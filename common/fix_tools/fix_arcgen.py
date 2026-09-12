#!/usr/bin/env python3
"""Apply arcgen fix files into a Connext Professional installation."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = SCRIPT_DIR / "arcgen_fix_499"
DEFAULT_TARGET_HOME = Path(r"C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1")


def reject_unsafe_relative(path: Path) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe relative path: {path}")


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("files"), list) or not data["files"]:
        raise ValueError(f"Manifest has no files: {path}")
    return data


def backup_existing_file(source: Path, timestamp: str, dry_run: bool) -> Path:
    backup_path = source.with_name(f"{source.name}.{timestamp}.bak")
    print(f"BACKUP {source} -> {backup_path}")
    if not dry_run:
        shutil.copy2(source, backup_path)
    return backup_path


def apply_file(source: Path, destination: Path, dry_run: bool) -> None:
    print(f"PATCH {source} -> {destination}")
    if dry_run:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Folder containing fix files")
    parser.add_argument("--manifest", type=Path, help="Manifest path. Default: <source-dir>/manifest.json")
    parser.add_argument("--target-home", type=Path, default=DEFAULT_TARGET_HOME, help="Connext Professional installation root")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_dir = args.source_dir.resolve()
    target_home = args.target_home.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else source_dir / "manifest.json"

    manifest = load_manifest(manifest_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not source_dir.is_dir():
        raise SystemExit(f"Source folder does not exist: {source_dir}")
    if not target_home.is_dir():
        raise SystemExit(f"Target home folder does not exist: {target_home}")

    patched = 0
    backed_up = 0
    for item in manifest["files"]:
        source_relative = Path(item["source"])
        target_relative = Path(item["target"])
        reject_unsafe_relative(source_relative)
        reject_unsafe_relative(target_relative)

        source = source_dir / source_relative
        destination = target_home / target_relative
        if not source.is_file():
            raise SystemExit(f"Patch source file not found: {source}")

        if destination.exists():
            backup_existing_file(destination, timestamp, args.dry_run)
            backed_up += 1

        apply_file(source, destination, args.dry_run)
        patched += 1

    print(f"Patched {patched} file(s) into {target_home}")
    print(f"Backed up {backed_up} existing file(s) next to their target files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
