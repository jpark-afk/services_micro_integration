#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

from __future__ import annotations

import argparse
import fnmatch
import os
import stat
import shutil
import sys
from pathlib import Path


OVERVIEW_START = "<!-- AUTO-GENERATED OVERVIEW START -->"
OVERVIEW_END = "<!-- AUTO-GENERATED OVERVIEW END -->"
TREE_MAX_DEPTH = 2


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_manifest(manifest_path: Path) -> dict:
    data: dict = {
        "targetDir": "",
        "sourceRoot": ".",
        "include": [],
        "exclude": [],
    }

    section = None
    current_include = None

    for line_no, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        stripped = line.strip()

        if line == stripped and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()

            if not value and key in {"include", "exclude"}:
                section = key
                current_include = None
                continue

            data[key] = _strip_quotes(value)
            section = None
            current_include = None
            continue

        if section == "include":
            if stripped.startswith("- "):
                payload = stripped[2:].strip()
                if payload.startswith("path:"):
                    path_value = _strip_quotes(payload.split(":", 1)[1].strip())
                    current_include = {"path": path_value, "recursive": False}
                    data["include"].append(current_include)
                elif payload:
                    current_include = {"path": _strip_quotes(payload), "recursive": False}
                    data["include"].append(current_include)
                else:
                    raise ValueError(f"Invalid include item at line {line_no}")
                continue

            if stripped.startswith("recursive:"):
                if current_include is None:
                    raise ValueError(f"'recursive' without include item at line {line_no}")
                recursive_value = _strip_quotes(stripped.split(":", 1)[1].strip()).lower()
                current_include["recursive"] = recursive_value in {"true", "yes", "1"}
                continue

            if stripped.startswith("sourceRoot:"):
                if current_include is None:
                    raise ValueError(f"'sourceRoot' without include item at line {line_no}")
                current_include["sourceRoot"] = _strip_quotes(stripped.split(":", 1)[1].strip())
                continue

            if stripped.startswith("target:"):
                if current_include is None:
                    raise ValueError(f"'target' without include item at line {line_no}")
                current_include["target"] = _strip_quotes(stripped.split(":", 1)[1].strip())
                continue

            raise ValueError(f"Unsupported include syntax at line {line_no}: {raw}")

        if section == "exclude":
            if stripped.startswith("- "):
                data["exclude"].append(_strip_quotes(stripped[2:].strip()))
                continue
            raise ValueError(f"Unsupported exclude syntax at line {line_no}: {raw}")

    if not data.get("targetDir"):
        raise ValueError("Missing required key: targetDir")

    return data


def _to_posix(path: Path) -> str:
    return path.as_posix()


def is_excluded(rel_path: Path, patterns: list[str]) -> bool:
    posix = _to_posix(rel_path)

    if "__pycache__" in rel_path.parts:
        return True
    if "_patched_tmp" in rel_path.parts:
        return True

    for pattern in patterns:
        if fnmatch.fnmatch(posix, pattern):
            return True
    return False


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def resolve_target_path(rel_path: Path) -> Path:
    if rel_path.as_posix() == "customer/README.md":
        return Path("README.md")
    return rel_path


def remove_tree(path: Path) -> None:
    def _onerror(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            raise exc_info[1]

    shutil.rmtree(path, onerror=_onerror)


def copy_includes(manifest_dir: Path, default_root: Path, target: Path, includes: list[dict], excludes: list[str]) -> int:
    copied = 0

    for item in includes:
        root = (manifest_dir / item.get("sourceRoot", default_root)).resolve()
        rel = Path(item["path"])
        src = root / rel
        dst_rel = Path(item.get("target", rel.as_posix()))

        if not src.exists():
            raise FileNotFoundError(f"Include path not found: {item['path']}")

        if src.is_file():
            child_rel = resolve_target_path(dst_rel if "target" in item else rel)
            if is_excluded(child_rel, excludes):
                continue
            copy_file(src, target / child_rel)
            copied += 1
            continue

        recursive = bool(item.get("recursive", False))
        if recursive:
            iterator = src.rglob("*")
        else:
            iterator = src.glob("*")

        for child in iterator:
            if not child.is_file():
                continue

            if "target" in item:
                child_rel = dst_rel / child.relative_to(src)
            else:
                child_rel = child.relative_to(root)

            child_rel = resolve_target_path(child_rel)
            if is_excluded(child_rel, excludes):
                continue

            copy_file(child, target / child_rel)
            copied += 1

    return copied


def ensure_readme_copy(root: Path, target: Path) -> None:
    src_readme = root / "customer" / "README.md"
    if src_readme.exists():
        copy_file(src_readme, target / "README.md")


def summarize_include_item(manifest_dir: Path, default_root: Path, item: dict, excludes: list[str]) -> str:
    root = (manifest_dir / item.get("sourceRoot", default_root)).resolve()
    rel = Path(item["path"])
    src = root / rel
    display_path = item.get("target", item["path"])

    if src.is_dir() or item.get("path", "").endswith("/"):
        folder_name = display_path.rstrip("/")
        purpose_map = {
            "templates": "Template resources for code generation and workaround flows",
            "xml_example": "DPSE/static-discovery XML configuration files",
            "fix_psl": "PSL patch payloads, fetch/apply utilities, and rule-based patch helpers",
        }
        purpose = purpose_map.get(folder_name, "Folder-level resources used by this package")

        top_entries: list[str] = []
        if src.exists() and src.is_dir():
            for child in sorted(src.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                rel_child = Path(display_path.rstrip("/")) / child.name
                if is_excluded(rel_child, excludes):
                    continue
                top_entries.append(child.name + ("/" if child.is_dir() else ""))
                if len(top_entries) >= 8:
                    break

        if top_entries:
            return f"- `{display_path}`: {purpose}. Top-level contents: {', '.join(top_entries)}"
        return f"- `{display_path}`: {purpose}."

    run_map = {
        "generate_ddscdd.bat": "Run: `.\\generate_ddscdd.bat`",
        "generate_testapp.bat": "Run: `.\\generate_testapp.bat`",
        "build_testapp.bat": "Run: `.\\build_testapp.bat`",
    }
    quick = run_map.get(rel.name, "")
    suffix = f" {quick}" if quick else ""
    return f"- `{display_path}`: Included file in deployment package.{suffix}"


def build_tree_lines(base_dir: Path, max_depth: int) -> list[str]:
    lines = [f"{base_dir.name}/"]

    def walk(current: Path, prefix: str, depth: int) -> None:
        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for idx, entry in enumerate(entries):
            is_last = idx == len(entries) - 1
            connector = "└─ " if is_last else "├─ "
            name = entry.name + ("/" if entry.is_dir() else "")
            lines.append(prefix + connector + name)

            if entry.is_dir():
                if depth < max_depth:
                    child_prefix = prefix + ("   " if is_last else "│  ")
                    walk(entry, child_prefix, depth + 1)

    walk(base_dir, "", 1)
    return lines


def build_overview_section(manifest_dir: Path, default_root: Path, target: Path, includes: list[dict], excludes: list[str]) -> str:
    include_lines = [summarize_include_item(manifest_dir, default_root, item, excludes) for item in includes]
    tree_lines = build_tree_lines(target, TREE_MAX_DEPTH)

    section: list[str] = [
        "Overview of Files",
        "",
        "This section is auto-generated during deployment.",
        "",
        "Included from deploy-manifest.yaml:",
        *include_lines,
        "",
        f"Target folder tree (depth: {TREE_MAX_DEPTH}):",
        "```text",
        *tree_lines,
        "```",
        "",
    ]
    return "\n".join(section)


def update_deployed_readme(manifest_dir: Path, default_root: Path, target: Path, includes: list[dict], excludes: list[str]) -> None:
    readme_path = target / "README.md"
    if not readme_path.exists():
        return

    text = readme_path.read_text(encoding="utf-8")

    # Remove previously generated block if present.
    start_idx = text.find(OVERVIEW_START)
    end_idx = text.find(OVERVIEW_END)
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        end_pos = end_idx + len(OVERVIEW_END)
        text = (text[:start_idx] + text[end_pos:]).lstrip("\n")

    generated = (
        f"{OVERVIEW_START}\n"
        + build_overview_section(manifest_dir, default_root, target, includes, excludes)
        + f"{OVERVIEW_END}\n\n"
    )

    marker = "IMPORTANT NOTICE"
    marker_idx = text.find(marker)
    if marker_idx != -1:
        updated = text[:marker_idx] + generated + text[marker_idx:]
    else:
        updated = generated + text

    readme_path.write_text(updated, encoding="utf-8")


def zip_target_folder(target_dir: Path) -> Path:
    zip_path = target_dir.parent / f"{target_dir.name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    archive_path = shutil.make_archive(
        base_name=str(target_dir.parent / target_dir.name),
        format="zip",
        root_dir=str(target_dir.parent),
        base_dir=target_dir.name,
    )
    return Path(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy files from deploy-manifest.yaml")
    parser.add_argument(
        "--manifest",
        default="deploy-manifest.yaml",
        help="Path to deployment manifest YAML (default: deploy-manifest.yaml)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        return 1

    try:
        manifest = parse_manifest(manifest_path)
    except Exception as exc:
        print(f"ERROR: Failed to parse manifest: {exc}")
        return 1

    manifest_dir = manifest_path.parent
    source_root = (manifest_dir / manifest.get("sourceRoot", ".")).resolve()
    target_dir = (manifest_dir / manifest["targetDir"]).resolve()
    if target_dir == source_root:
        print("ERROR: targetDir cannot be the source root")
        return 1

    if target_dir.exists():
        remove_tree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    includes: list[dict] = manifest.get("include", [])
    excludes: list[str] = manifest.get("exclude", [])

    try:
        copied_count = copy_includes(manifest_dir, source_root, target_dir, includes, excludes)
        ensure_readme_copy(source_root, target_dir)
        update_deployed_readme(manifest_dir, source_root, target_dir, includes, excludes)
        zip_path = zip_target_folder(target_dir)
    except Exception as exc:
        print(f"ERROR: Deployment failed: {exc}")
        return 1

    print(f"Deployment completed: {target_dir}")
    print(f"Files copied: {copied_count}")
    print(f"Archive created: {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
