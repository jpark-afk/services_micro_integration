#!/usr/bin/env python3
"""Generate workaround report from .vm files under a folder.

The report scans for workaround tags in the form `workaround#CLASS` (case-insensitive),
extracts nearby context lines, and writes a Markdown report.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

WORKAROUND_PATTERN = re.compile(r"workaround#(?:\s*([A-Za-z0-9_]+))?", re.IGNORECASE)
REPORT_VERSION = "1.0.0"

CATEGORY_DEFINITIONS = {
    "COMMON": "Mandatory patch.",
    "HAE": "For Autoever only; not a mandatory patch.",
    "VTT": "For virtual target (internal only); not a mandatory patch.",
}


class Occurrence:
    def __init__(
        self,
        file_path: Path,
        line_no: int,
        category: str,
        context_start: int,
        context_end: int,
        lines: list[str],
    ) -> None:
        self.file_path = file_path
        self.line_no = line_no
        self.category = category
        self.context_start = context_start
        self.context_end = context_end
        self.lines = lines


def read_text_with_fallback(path: Path) -> str:
    """Read text with a few common encodings used in mixed Windows projects."""
    for encoding in ("utf-8-sig", "utf-8", "cp949", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_category(raw_category: str | None) -> str:
    if not raw_category:
        return "COMMON"
    category = raw_category.strip().upper()
    return category if category else "COMMON"


def find_xml_comment_end(lines: list[str], start_line: int) -> int:
    """Return the line number where an XML comment ends, or start_line if not a block."""
    line_text = lines[start_line - 1]
    if "<!--" not in line_text:
        return start_line
    if "-->" in line_text:
        return start_line

    for line_no in range(start_line + 1, len(lines) + 1):
        if "-->" in lines[line_no - 1]:
            return line_no

    return start_line


def collect_occurrences(source_dir: Path, context_lines: int) -> list[Occurrence]:
    occurrences: list[Occurrence] = []

    for vm_file in sorted(source_dir.rglob("*.vm"), key=lambda p: str(p).lower()):
        content = read_text_with_fallback(vm_file)
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            if "workaround#" not in line.lower():
                continue

            for match in WORKAROUND_PATTERN.finditer(line):
                category = normalize_category(match.group(1))
                start = max(1, idx - context_lines)
                xml_comment_end = find_xml_comment_end(lines, idx)
                end = min(len(lines), max(idx + context_lines, xml_comment_end + context_lines))
                snippet = lines[start - 1 : end]
                occurrences.append(
                    Occurrence(
                        file_path=vm_file,
                        line_no=idx,
                        category=category,
                        context_start=start,
                        context_end=end,
                        lines=snippet,
                    )
                )

    return occurrences


def build_category_summary(counts: Counter) -> str:
    if not counts:
        return "None"

    preferred_order = ["COMMON", "HAE", "VTT"]
    seen = set()
    parts: list[str] = []

    for category in preferred_order:
        if category in counts:
            parts.append(f"{category} ({counts[category]})")
            seen.add(category)

    for category in sorted(counts):
        if category not in seen:
            parts.append(f"{category} ({counts[category]})")

    return ", ".join(parts)


def build_report(
    source_dir: Path,
    occurrences: Iterable[Occurrence],
    workspace_root: Path,
    generated_at: datetime,
) -> str:
    items = list(occurrences)
    counts = Counter(item.category for item in items)

    lines: list[str] = []
    lines.append(f"**Report Version: {REPORT_VERSION}**")
    lines.append(f"- Generated date: {generated_at.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("**Workaround Report -- snippets with context and line numbers**")
    lines.append("")
    lines.append(f"- Scope: collected `workaround#` occurrences from all `.vm` files under `{source_dir.as_posix()}`.")
    lines.append(f"- Total items found: {len(items)}")
    lines.append(f"- Categories: {build_category_summary(counts)}")
    lines.append("")
    lines.append("Category definitions:")

    definition_order = ["COMMON", "HAE", "VTT"]
    for category in definition_order:
        definition = CATEGORY_DEFINITIONS[category]
        lines.append(f"- **{category}**: {definition}")

    unknown_categories = [category for category in sorted(counts) if category not in CATEGORY_DEFINITIONS]
    for category in unknown_categories:
        lines.append(f"- **{category}**: Unclassified category found in source comments.")

    lines.append("")
    lines.append("Below are code snippets (about +/-5 lines) around each `workaround#` occurrence. Items are grouped by category in this order: COMMON, HAE, VTT.")
    lines.append("")

    grouped: dict[str, list[Occurrence]] = {}
    for item in items:
        grouped.setdefault(item.category, []).append(item)

    ordered_categories: list[str] = ["COMMON", "HAE", "VTT"]
    ordered_categories.extend(category for category in sorted(grouped) if category not in {"COMMON", "HAE", "VTT"})

    section_index = 1
    for category in ordered_categories:
        category_items = grouped.get(category, [])
        lines.append(f"### {category} ({len(category_items)})")
        lines.append("")

        if not category_items:
            lines.append("- No items")
            lines.append("")
            continue

        for item in category_items:
            relative_path = item.file_path.relative_to(workspace_root).as_posix()
            lines.append(f"{section_index}) File: {relative_path} (L{item.line_no})")
            lines.append("```text")

            current_line = item.context_start
            for text in item.lines:
                lines.append(f"L{current_line}: {text}")
                current_line += 1

            lines.append("```")
            lines.append("")
            section_index += 1

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate workaround report from .vm templates")
    parser.add_argument(
        "--source",
        help="Folder to scan recursively for .vm files (default: this script's directory)",
    )
    parser.add_argument(
        "--output",
        help="Output markdown file path (default: <source>/workaround_report.md)",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=5,
        help="Number of context lines before/after each match (default: 5)",
    )
    return parser.parse_args()


def resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def main() -> int:
    args = parse_args()

    if args.context < 0:
        raise ValueError("--context must be >= 0")

    script_dir = Path(__file__).resolve().parent
    source_dir = resolve_path(args.source, script_dir) if args.source else script_dir
    output_file = resolve_path(args.output, script_dir) if args.output else source_dir / "workaround_report.md"
    workspace_root = source_dir.parent

    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    occurrences = collect_occurrences(source_dir=source_dir, context_lines=args.context)
    source_label = source_dir.relative_to(workspace_root)
    report = build_report(
        source_dir=source_label,
        occurrences=occurrences,
        workspace_root=workspace_root,
        generated_at=datetime.now(),
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")

    print(f"Generated: {output_file}")
    print(f"Matches: {len(occurrences)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
