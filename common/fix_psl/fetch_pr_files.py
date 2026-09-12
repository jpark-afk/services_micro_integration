#!/usr/bin/env python3
"""Fetch changed PSL files from a Bitbucket Server pull request or branch."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PREFIX = "rti/ndds_lite/rti_me_psl.2.0"
DEFAULT_REPO_URL = "https://bitbucket.rti.com/scm/connext/connextmicro.git"


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_pr(value: str) -> tuple[str | None, str | None, str]:
    if value.isdigit():
        return None, None, value

    parsed = urlparse(value)
    match = re.search(r"/projects/([^/]+)/repos/([^/]+)/pull-requests/(\d+)", parsed.path)
    if not match:
        raise ValueError(f"Unsupported pull request value: {value}")

    project, repo, pr_id = match.groups()
    return project, repo, pr_id


def default_repo_url(pr_url: str, project: str | None, repo: str | None) -> str | None:
    if not project or not repo:
        return None

    parsed = urlparse(pr_url)
    if not parsed.scheme or not parsed.netloc:
        return None


    return f"{parsed.scheme}://{parsed.netloc}/scm/{project.lower()}/{repo}.git"


def is_pr_source(value: str) -> bool:
    if value.isdigit():
        return True
    parsed = urlparse(value)
    return bool(re.search(r"/projects/[^/]+/repos/[^/]+/pull-requests/\d+", parsed.path))


def ensure_cache(cache_dir: Path, repo_url: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not (cache_dir / ".git").exists():
        run_git(["init"], cache_dir)
        run_git(["remote", "add", "origin", repo_url], cache_dir)
        return

    current = run_git(["remote", "get-url", "origin"], cache_dir, check=False)
    if current.returncode != 0:
        run_git(["remote", "add", "origin", repo_url], cache_dir)
    elif current.stdout.strip() != repo_url:
        run_git(["remote", "set-url", "origin", repo_url], cache_dir)


def fetch_ref(cache_dir: Path, remote_ref: str, local_ref: str) -> bool:
    result = run_git(["fetch", "--force", "origin", f"{remote_ref}:{local_ref}"], cache_dir, check=False)
    if result.returncode != 0:
        return False
    return True


def fetch_base_ref(cache_dir: Path, base_ref: str) -> str:
    remote_ref = base_ref
    if not remote_ref.startswith("refs/"):
        remote_ref = f"refs/heads/{remote_ref}"

    local_ref = "refs/remotes/origin/pr-base"
    if not fetch_ref(cache_dir, remote_ref, local_ref):
        raise RuntimeError(f"Failed to fetch base ref '{base_ref}' from origin")
    return local_ref


def fetch_source_ref(cache_dir: Path, source_ref: str) -> str:
    remote_ref = source_ref
    if not remote_ref.startswith("refs/"):
        remote_ref = f"refs/heads/{remote_ref}"

    local_ref = "refs/remotes/origin/source"
    if not fetch_ref(cache_dir, remote_ref, local_ref):
        raise RuntimeError(f"Failed to fetch source ref '{source_ref}' from origin")
    return local_ref


def changed_paths_from_status(output: str) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        status = parts[0]
        if status.startswith("D"):
            continue

        if status.startswith("R") or status.startswith("C"):
            path = parts[-1]
        else:
            path = parts[1]

        files.append({"status": status, "path": path.replace("\\", "/")})
    return files


def get_changed_files(cache_dir: Path, pr_id: str, base_ref: str | None) -> tuple[str, str, list[dict[str, str]]]:
    pr_head = f"refs/remotes/origin/pr/{pr_id}"
    if not fetch_ref(cache_dir, f"refs/pull-requests/{pr_id}/from", pr_head):
        raise RuntimeError(f"Failed to fetch pull request head ref for PR {pr_id}")

    pr_merge = f"refs/remotes/origin/pr/{pr_id}-merge"
    if fetch_ref(cache_dir, f"refs/pull-requests/{pr_id}/merge", pr_merge):
        status = run_git(["diff", "--name-status", "-M", f"{pr_merge}^1", pr_merge], cache_dir)
        return pr_head, pr_merge, changed_paths_from_status(status.stdout)

    if not base_ref:
        raise RuntimeError("PR merge ref was not available. Re-run with --base-ref <target-branch>.")

    local_base = fetch_base_ref(cache_dir, base_ref)
    status = run_git(["diff", "--name-status", "-M", f"{local_base}...{pr_head}"], cache_dir)
    return pr_head, local_base, changed_paths_from_status(status.stdout)


def get_changed_files_from_ref(cache_dir: Path, source_ref: str, base_ref: str | None) -> tuple[str, str, list[dict[str, str]]]:
    if not base_ref:
        raise RuntimeError("--base-ref is required when fetching from a branch/ref")

    local_source = fetch_source_ref(cache_dir, source_ref)
    local_base = fetch_base_ref(cache_dir, base_ref)
    status = run_git(["diff", "--name-status", "-M", f"{local_base}...{local_source}"], cache_dir)
    return local_source, local_base, changed_paths_from_status(status.stdout)


def normalize_prefix(prefix: str) -> str:
    return prefix.replace("\\", "/").strip("/")


def path_under_prefix(path: str, prefix: str) -> str | None:
    path = path.replace("\\", "/").strip("/")
    prefix = normalize_prefix(prefix)
    if path == prefix:
        return ""
    if path.startswith(prefix + "/"):
        return path[len(prefix) + 1 :]
    return None


def write_file_from_git(cache_dir: Path, commit_ref: str, repo_path: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "show", f"{commit_ref}:{repo_path}"],
        cwd=str(cache_dir),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    destination.write_bytes(result.stdout)


def clean_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onerror=make_writable_and_retry)
    path.mkdir(parents=True, exist_ok=True)


def make_writable_and_retry(function, path: str, _exc_info) -> None:
    Path(path).chmod(stat.S_IWRITE)
    function(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Bitbucket PR URL, numeric PR id, or source branch/ref")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Git clone URL. Default: {DEFAULT_REPO_URL}")
    parser.add_argument("--source-prefix", default=DEFAULT_PREFIX, help="Repo folder to copy from. Default: rti_me_psl2.0")
    parser.add_argument("--download-root", type=Path, default=SCRIPT_DIR / "repository", help="Output folder for fetched files")
    parser.add_argument("--cache-dir", type=Path, default=SCRIPT_DIR / "_git_cache", help="Local git cache folder")
    parser.add_argument("--base-ref", help="Target branch/ref fallback when Bitbucket merge ref is unavailable")
    parser.add_argument("--keep-prefix", action="store_true", help="Keep source-prefix as the first output folder")
    parser.add_argument("--keep-existing", action="store_true", help="Do not clean download-root before writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_url = args.repo_url

    source_kind = "branch"
    pr_id = None
    if is_pr_source(args.source):
        project, repo, pr_id = parse_pr(args.source)
        repo_url = args.repo_url or default_repo_url(args.source, project, repo)
        if not repo_url:
            raise SystemExit("--repo-url is required when source is not a full Bitbucket PR URL")
        source_kind = "pull_request"

    ensure_cache(args.cache_dir, repo_url)
    if source_kind == "pull_request":
        source_ref, compare_ref, changed_files = get_changed_files(args.cache_dir, pr_id or "", args.base_ref)
    else:
        source_ref, compare_ref, changed_files = get_changed_files_from_ref(args.cache_dir, args.source, args.base_ref)

    if not args.keep_existing:
        clean_directory(args.download_root)
    else:
        args.download_root.mkdir(parents=True, exist_ok=True)

    prefix = normalize_prefix(args.source_prefix)
    manifest_files: list[dict[str, str]] = []
    for item in changed_files:
        relative = path_under_prefix(item["path"], prefix)
        if relative is None or not relative:
            continue

        output_relative = f"{prefix}/{relative}" if args.keep_prefix else relative
        destination = args.download_root / Path(output_relative)
        write_file_from_git(args.cache_dir, source_ref, item["path"], destination)
        manifest_files.append(
            {
                "status": item["status"],
                "repo_path": item["path"],
                "relative_path": output_relative.replace("\\", "/"),
            }
        )

    source_commit = run_git(["rev-parse", source_ref], args.cache_dir).stdout.strip()
    manifest = {
        "source": args.source,
        "source_kind": source_kind,
        "repo_url": repo_url,
        "pr_id": pr_id,
        "source_commit": source_commit,
        "compare_ref": compare_ref,
        "source_prefix": prefix,
        "download_root": str(args.download_root),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": manifest_files,
    }
    (args.download_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Fetched {len(manifest_files)} file(s) into {args.download_root}")
    for item in manifest_files:
        print(f"{item['status']} {item['relative_path']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        sys.stderr.write(error.stderr or error.stdout or str(error))
        raise SystemExit(error.returncode)