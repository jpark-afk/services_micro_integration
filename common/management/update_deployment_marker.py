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
import re
from pathlib import Path


NOTICE_TITLE = "RTI INTERNAL TEMPORARY WORKAROUND NOTICE"
XML_NOTICE_TITLE = "RTI EXAMPLE FILE NOTICE"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_manifest(manifest_path: Path) -> dict:
    data: dict = {"include": [], "exclude": []}
    section = None
    current_include = None

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    for line_no, raw in enumerate(lines, start=1):
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
                    current_include = {
                        "path": _strip_quotes(payload.split(":", 1)[1].strip()),
                        "recursive": False,
                    }
                else:
                    current_include = {"path": _strip_quotes(payload), "recursive": False}
                data["include"].append(current_include)
                continue

            if stripped.startswith("recursive:"):
                if current_include is None:
                    raise ValueError(f"'recursive' without include item at line {line_no}")
                value = _strip_quotes(stripped.split(":", 1)[1].strip()).lower()
                current_include["recursive"] = value in {"true", "yes", "1"}
                continue

            raise ValueError(f"Unsupported include syntax at line {line_no}: {raw}")

        if section == "exclude":
            if stripped.startswith("- "):
                data["exclude"].append(_strip_quotes(stripped[2:].strip()))
                continue
            raise ValueError(f"Unsupported exclude syntax at line {line_no}: {raw}")

    return data


def load_marker_format(manifest_path: Path) -> dict[str, list[str]]:
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    marker: dict[str, list[str]] = {}

    in_section = False
    current_key: str | None = None

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            continue

        if not in_section:
            if stripped == "deploymentMarkerFormat:":
                in_section = True
            continue

        # End marker section when we return to top-level keys.
        if not line.startswith(" "):
            break

        # Child key under deploymentMarkerFormat
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            marker[current_key] = []
            continue

        # List item under a child key
        if current_key and line.startswith("    - "):
            item = _strip_quotes(stripped[2:].strip())
            marker[current_key].append(item)
            continue

    return marker


def _to_posix(path: Path) -> str:
    return path.as_posix()


def is_excluded(rel_path: Path, patterns: list[str]) -> bool:
    posix = _to_posix(rel_path)
    if "__pycache__" in rel_path.parts:
        return True
    for pattern in patterns:
        if fnmatch.fnmatch(posix, pattern):
            return True
    return False


def collect_targets(root: Path, manifest: dict) -> list[Path]:
    targets: list[Path] = []
    includes = manifest.get("include", [])
    excludes = manifest.get("exclude", [])

    for item in includes:
        rel = Path(item["path"])
        src = root / rel
        if not src.exists():
            continue

        if src.is_file():
            if not is_excluded(rel, excludes) and src.suffix.lower() in {".py", ".bat", ".xml"}:
                targets.append(src)
            continue

        iterator = src.rglob("*") if item.get("recursive", False) else src.glob("*")
        for child in iterator:
            if not child.is_file():
                continue
            rel_child = child.relative_to(root)
            if is_excluded(rel_child, excludes):
                continue
            if child.suffix.lower() in {".py", ".bat", ".xml"}:
                targets.append(child)

    return sorted(set(targets))


def detect_baseline_from_readme(readme_path: Path) -> str:
    if not readme_path.exists():
        return "Micro430er738"
    text = readme_path.read_text(encoding="utf-8")
    match = re.search(r"Baseline version:\s*([^\.\n]+)", text)
    if match:
        return match.group(1).strip()
    return "Micro430er738"


def py_notice_lines(baseline: str) -> list[str]:
    return [
        f"# {NOTICE_TITLE}",
        "# Temporary workaround until an official RTI patch is released.",
        f"# Baseline version: {baseline}.",
        "# Not officially supported by RTI Technical Support.",
        "# Must NOT be applied directly to controller mass-production development.",
        "# See README.md for details.",
    ]


def bat_notice_lines(baseline: str) -> list[str]:
    return [
        f"REM {NOTICE_TITLE}",
        "REM Temporary workaround until an official RTI patch is released.",
        f"REM Baseline version: {baseline}.",
        "REM Not officially supported by RTI Technical Support.",
        "REM Must NOT be applied directly to controller mass-production development.",
        "REM See README.md for details.",
    ]


def bat_runtime_notice_block(baseline: str) -> list[str]:
    return [
        ":print_notice",
        "echo [RTI NOTICE] INTERNAL TEMPORARY WORKAROUND",
        "echo [RTI NOTICE] Temporary workaround until an official RTI patch is released.",
        f"echo [RTI NOTICE] Baseline version: {baseline}.",
        "echo [RTI NOTICE] Not officially supported by RTI Technical Support.",
        "echo [RTI NOTICE] Must NOT be applied directly to controller mass-production development.",
        "echo [RTI NOTICE] See README.md for details.",
        "echo.",
        "exit /b 0",
    ]


def xml_notice_lines() -> list[str]:
    return [
        f"<!-- {XML_NOTICE_TITLE} -->",
        "<!-- This file is provided as an example configuration and is not a workaround. -->",
        "<!-- Not intended for direct use in controller mass-production projects. -->",
        "<!-- RTI does not provide official support for this file content and assumes no responsibility for errors from its use. -->",
        "<!-- Users must review and modify this file for their own environment before use. -->",
        "<!-- Refer to the Connext Micro 4.3 online documentation for guidance. -->",
    ]


def resolve_notice_block(custom_block: list[str] | None, fallback_block: list[str]) -> list[str]:
    if custom_block:
        return custom_block
    return fallback_block


def remove_notice_block(lines: list[str], prefix: str) -> list[str]:
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == f"{prefix} {NOTICE_TITLE}":
            start = i
            break
    if start is None:
        return lines

    for j in range(start, min(start + 12, len(lines))):
        if "See README.md for details." in lines[j]:
            end = j
            break

    if end is None:
        return lines

    k = end + 1
    while k < len(lines) and not lines[k].strip():
        k += 1

    return lines[:start] + lines[k:]


def remove_xml_notice_block(lines: list[str]) -> list[str]:
    start = None
    end = None

    for i, line in enumerate(lines):
        if line.strip() == f"<!-- {XML_NOTICE_TITLE} -->":
            start = i
            break

    if start is None:
        return lines

    for j in range(start, min(start + 16, len(lines))):
        if "Connext Micro 4.3 online documentation" in lines[j]:
            end = j
            break

    if end is None:
        return lines

    k = end + 1
    while k < len(lines) and not lines[k].strip():
        k += 1

    return lines[:start] + lines[k:]


def update_python_file(path: Path, baseline: str, custom_block: list[str] | None = None) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    lines = remove_notice_block(lines, "#")

    insert_at = 1 if lines and lines[0].startswith("#!") else 0
    block = resolve_notice_block(custom_block, py_notice_lines(baseline)) + [""]
    new_lines = lines[:insert_at] + block + lines[insert_at:]

    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def update_batch_file(
    path: Path,
    baseline: str,
    custom_static_block: list[str] | None = None,
    custom_runtime_block: list[str] | None = None,
) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

    if not lines or lines[0].strip().lower() != "@echo off":
        lines.insert(0, "@echo off")

    lines = remove_notice_block(lines, "REM")

    notice = resolve_notice_block(custom_static_block, bat_notice_lines(baseline)) + [""]
    lines = [lines[0]] + notice + lines[1:]

    has_call = any(line.strip().lower() == "call :print_notice" for line in lines)
    if not has_call:
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("setlocal"):
                lines.insert(i + 1, "call :print_notice")
                break

    label_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == ":print_notice":
            label_idx = i
            break

    if label_idx is not None:
        lines = lines[:label_idx]
        while lines and not lines[-1].strip():
            lines.pop()

    lines.append("")
    lines.extend(resolve_notice_block(custom_runtime_block, bat_runtime_notice_block(baseline)))

    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def update_xml_file(path: Path, custom_block: list[str] | None = None) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    lines = remove_xml_notice_block(lines)

    insert_after = None
    for i, line in enumerate(lines):
        if "<dds" in line:
            for j in range(i, min(i + 4, len(lines))):
                if ">" in lines[j]:
                    insert_after = j
                    break
            break

    if insert_after is None:
        insert_after = 0

    block = [f"    {line}" for line in resolve_notice_block(custom_block, xml_notice_lines())] + [""]
    new_lines = lines[: insert_after + 1] + block + lines[insert_after + 1 :]

    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Update RTI deployment marker notices in include scope files")
    parser.add_argument("--manifest", required=True, help="Path to deployment manifest yaml")
    parser.add_argument("--baseline", help="Override baseline version string")
    parser.add_argument("--dry-run", action="store_true", help="Show targets only without writing")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 1

    root = manifest_path.parent
    manifest = parse_manifest(manifest_path)
    marker_format = load_marker_format(manifest_path)

    baseline = args.baseline or detect_baseline_from_readme(root / "customer" / "README.md")
    targets = collect_targets(root, manifest)

    updated = 0
    for path in targets:
        rel = path.relative_to(root).as_posix()
        if args.dry_run:
            print(f"TARGET: {rel}")
            continue

        if path.suffix.lower() == ".py":
            changed = update_python_file(
                path,
                baseline,
                marker_format.get("pythonStaticCommentBlock"),
            )
        elif path.suffix.lower() == ".xml":
            changed = update_xml_file(path, marker_format.get("xmlStaticCommentBlock"))
        else:
            changed = update_batch_file(
                path,
                baseline,
                marker_format.get("batchStaticCommentBlock"),
                marker_format.get("batchRuntimeOutputBlock"),
            )

        if changed:
            updated += 1
            print(f"UPDATED: {rel}")
        else:
            print(f"UNCHANGED: {rel}")

    if args.dry_run:
        print(f"Total targets: {len(targets)}")
    else:
        print(f"Done. Updated files: {updated} / {len(targets)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
