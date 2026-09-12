#!/usr/bin/env python3
"""Copy fetched PSL files into a PSL home directory."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def load_files(repository: Path, manifest: Path | None) -> list[Path]:
    if manifest and manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return [Path(item["relative_path"]) for item in data.get("files", [])]

    return [path.relative_to(repository) for path in repository.rglob("*") if path.is_file() and path.name != "manifest.json"]


def reject_unsafe_relative(path: Path) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe relative path: {path}")


def target_relative_path(source_relative: Path) -> Path:
    parts = source_relative.parts
    if parts and parts[0] == "include":
        return Path("include", "rti_me", *parts[1:])
    if parts and parts[0] == "srcC":
        return Path("src", "rti_me_psl", *parts[1:])
    return source_relative


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=SCRIPT_DIR / "repository", help="Fetched file repository")
    parser.add_argument("--manifest", type=Path, help="Manifest from fetch_pr_files.py. Default: <repository>/manifest.json")
    parser.add_argument("--psl-home", type=Path, default=SCRIPT_DIR / "psl_target", help="PSL home directory to overwrite")
    parser.add_argument("--dry-run", action="store_true", help="Print copies without writing files")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repository = args.repository.resolve()
    manifest = args.manifest or repository / "manifest.json"
    psl_home = args.psl_home.resolve()

    if not repository.exists():
        raise SystemExit(f"Repository folder does not exist: {repository}")

    files = load_files(repository, manifest)
    if not files:
        print("No files to copy")
        return 0

    for relative in files:
        reject_unsafe_relative(relative)
        source = repository / relative
        destination_relative = target_relative_path(relative)
        reject_unsafe_relative(destination_relative)
        destination = psl_home / destination_relative
        if not source.is_file():
            raise SystemExit(f"Missing fetched file: {source}")

        print(f"COPY {relative} -> {destination_relative}")
        if args.dry_run:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    print(f"Copied {len(files)} file(s) into {psl_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())