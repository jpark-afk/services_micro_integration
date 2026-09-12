#!/usr/bin/env python3
# RTI INTERNAL TEMPORARY WORKAROUND NOTICE
# Temporary workaround until an official RTI patch is released.
# Baseline version: Micro430er738.
# Not officially supported by RTI Technical Support.
# Must NOT be applied directly to controller mass-production development.
# See README.md for details.

"""Apply configurable source patches under a directory tree.

Default behavior writes only modified files into a temporary output tree.
Use --in-place to overwrite the original files instead.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit(
            "ERROR: tomllib is unavailable. Use Python 3.11+ or install tomli."
        ) from exc


DEFAULT_MARKER = "PATCHED_BY_code_patch.py"
PATCH_MARKER_PREFIX = "PATCHED_BY_"


class PatchError(Exception):
    """Raised when a rule cannot be applied safely."""


@dataclass(frozen=True)
class Rule:
    rule_id: str
    path_glob: str
    operation: str
    line_hint: int
    search_window: int
    note: str
    match: str | None = None
    replacement: str | None = None
    start: str | None = None
    end: str | None = None


@dataclass(frozen=True)
class RuleResult:
    rule: Rule
    status: str
    detail: str


def render_rule_text(template: str, rule: Rule, marker: str) -> str:
    return template.format(marker=marker, note=rule.note, rule_id=rule.rule_id)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        help="Root directory to scan recursively for patch targets.",
    )
    parser.add_argument(
        "--rules",
        default=str(script_dir / "code_patch_rules.toml"),
        help="Path to the TOML patch rules file.",
    )
    parser.add_argument(
        "--output-root",
        help="Directory that receives only modified files when not using --in-place.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the original files instead of writing to a temp output tree.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Do not clear the temp output directory before writing patched files.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore *.bak files over their patched counterparts and delete the .bak files.",
    )
    return parser.parse_args()


def load_config(rules_path: Path) -> dict[str, Any]:
    text = rules_path.read_text(encoding="utf-8")
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        normalized_text = normalize_windows_root_assignments(text)
        return tomllib.loads(normalized_text)


ROOT_ASSIGNMENT_RE = re.compile(
    r'^(?P<key>\s*[A-Za-z0-9_]*root\s*=\s*)"(?P<value>.*)"\s*$',
    re.MULTILINE,
)


def normalize_windows_root_assignments(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group("key")
        value = match.group("value")
        if "\\" not in value:
            return match.group(0)
        escaped_value = value.replace("\\", "\\\\")
        return f'{key}"{escaped_value}"'

    return ROOT_ASSIGNMENT_RE.sub(repl, text)


def build_rules(config: dict[str, Any]) -> list[Rule]:
    raw_rules = config.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise PatchError("Rules file must contain at least one [[rules]] entry.")

    rules: list[Rule] = []
    for entry in raw_rules:
        if not isinstance(entry, dict):
            raise PatchError("Each [[rules]] entry must be a table.")
        rule = Rule(
            rule_id=require_string(entry, "id"),
            path_glob=require_string(entry, "path_glob"),
            operation=require_string(entry, "operation"),
            line_hint=require_int(entry, "line_hint"),
            search_window=int(entry.get("search_window", 40)),
            note=require_string(entry, "note"),
            match=optional_string(entry, "match"),
            replacement=optional_string(entry, "replacement"),
            start=optional_string(entry, "start"),
            end=optional_string(entry, "end"),
        )
        validate_rule(rule)
        rules.append(rule)
    return rules


def require_string(entry: dict[str, Any], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise PatchError(f"Rule field '{key}' must be a non-empty string.")
    return value


def optional_string(entry: dict[str, Any], key: str) -> str | None:
    value = entry.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise PatchError(f"Rule field '{key}' must be a non-empty string when set.")
    return value


def require_int(entry: dict[str, Any], key: str) -> int:
    value = entry.get(key)
    if not isinstance(value, int) or value < 1:
        raise PatchError(f"Rule field '{key}' must be a positive integer.")
    return value


def validate_rule(rule: Rule) -> None:
    if rule.operation == "replace_line":
        if rule.match is None or rule.replacement is None:
            raise PatchError(
                f"Rule '{rule.rule_id}' requires 'match' and 'replacement'."
            )
        return
    if rule.operation == "disable_block":
        if rule.start is None or rule.end is None:
            raise PatchError(f"Rule '{rule.rule_id}' requires 'start' and 'end'.")
        return
    raise PatchError(
        f"Rule '{rule.rule_id}' uses unsupported operation '{rule.operation}'."
    )


def resolve_roots(args: argparse.Namespace, config: dict[str, Any]) -> tuple[Path, Path, str]:
    rules_path = Path(args.rules).resolve()
    workspace_dir = rules_path.parent.parent
    rules_dir = rules_path.parent

    source_root_value = args.source_root or config.get("source_root")
    if not isinstance(source_root_value, str) or not source_root_value:
        raise PatchError("source_root must be provided via CLI or TOML config.")
    source_root = (workspace_dir / source_root_value).resolve()
    if not source_root.is_dir():
        raise PatchError(f"Source root does not exist: {source_root}")

    output_root_value = args.output_root or config.get("output_root")
    if not args.in_place:
        if not isinstance(output_root_value, str) or not output_root_value:
            raise PatchError("output_root must be provided when not using --in-place.")
        output_root = (rules_dir / output_root_value).resolve()
    else:
        output_root = Path()

    marker = config.get("marker", DEFAULT_MARKER)
    if not isinstance(marker, str) or not marker:
        raise PatchError("marker must be a non-empty string.")

    return source_root, output_root, marker


def matches_glob(relative_path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(relative_path, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatch(relative_path, pattern[3:])
    )


def detect_newline(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    return "\n"


def pick_index(indices: list[int], line_hint: int, search_window: int, label: str) -> int:
    if not indices:
        raise PatchError(f"Could not find {label}.")
    chosen = min(indices, key=lambda idx: (abs((idx + 1) - line_hint), idx))
    distance = abs((chosen + 1) - line_hint)
    if distance > search_window:
        raise PatchError(
            f"Closest {label} is {distance} lines away from hint line {line_hint}."
        )
    return chosen


def find_nearby_patch_marker(
    stripped_lines: list[str],
    line_hint: int,
    search_window: int,
) -> int | None:
    start = max(0, line_hint - 1 - search_window)
    end = min(len(stripped_lines), line_hint + search_window)
    for idx in range(start, end):
        if PATCH_MARKER_PREFIX in stripped_lines[idx]:
            return idx
    return None


def legacy_wrapper_start(marker: str, note: str) -> str:
    return f"#if 0 /* {marker}: {note} */"


def legacy_wrapper_end(marker: str) -> str:
    return f"#endif /* {marker} */"


def apply_replace_line(text: str, rule: Rule, marker: str) -> tuple[str, RuleResult]:
    assert rule.match is not None
    assert rule.replacement is not None

    rendered_replacement = render_rule_text(rule.replacement, rule, marker)
    newline = detect_newline(text)
    lines = text.splitlines(keepends=True)
    stripped_lines = [line.rstrip("\r\n") for line in lines]

    nearby_marker = find_nearby_patch_marker(
        stripped_lines,
        rule.line_hint,
        rule.search_window,
    )
    if nearby_marker is not None:
        return text, RuleResult(rule, "already_patched", f"line {nearby_marker + 1}")

    replacement_indices = [
        idx for idx, line in enumerate(stripped_lines) if line == rendered_replacement
    ]
    if replacement_indices:
        chosen_replacement = pick_index(
            replacement_indices,
            rule.line_hint,
            rule.search_window,
            f"replacement line for rule '{rule.rule_id}'",
        )
        return text, RuleResult(rule, "already_patched", f"line {chosen_replacement + 1}")

    match_indices = [idx for idx, line in enumerate(stripped_lines) if line == rule.match]
    chosen_match = pick_index(
        match_indices,
        rule.line_hint,
        rule.search_window,
        f"match line for rule '{rule.rule_id}'",
    )
    lines[chosen_match] = rendered_replacement + newline
    return "".join(lines), RuleResult(rule, "patched", f"line {chosen_match + 1}")


def apply_disable_block(text: str, rule: Rule, marker: str) -> tuple[str, RuleResult]:
    assert rule.start is not None
    assert rule.end is not None

    newline = detect_newline(text)
    lines = text.splitlines(keepends=True)
    stripped_lines = [line.rstrip("\r\n") for line in lines]

    start_indices = [idx for idx, line in enumerate(stripped_lines) if line == rule.start]
    start_index = pick_index(
        start_indices,
        rule.line_hint,
        rule.search_window,
        f"block start for rule '{rule.rule_id}'",
    )

    end_index = None
    for idx in range(start_index, len(stripped_lines)):
        if stripped_lines[idx] == rule.end:
            end_index = idx
            break
    if end_index is None:
        raise PatchError(f"Could not find block end for rule '{rule.rule_id}'.")

    nearby_marker = find_nearby_patch_marker(
        stripped_lines,
        rule.line_hint,
        rule.search_window,
    )
    if nearby_marker is not None:
        return text, RuleResult(rule, "already_patched", f"line {nearby_marker + 1}")

    wrapper_start = legacy_wrapper_start(marker, rule.note) + newline
    wrapper_end = legacy_wrapper_end(marker) + newline
    lines.insert(start_index, wrapper_start)
    lines.insert(end_index + 2, wrapper_end)
    return "".join(lines), RuleResult(rule, "patched", f"lines {start_index + 1}-{end_index + 1}")


def apply_rule(text: str, rule: Rule, marker: str) -> tuple[str, RuleResult]:
    if rule.operation == "replace_line":
        return apply_replace_line(text, rule, marker)
    if rule.operation == "disable_block":
        return apply_disable_block(text, rule, marker)
    raise PatchError(f"Unsupported operation: {rule.operation}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def backup_path(path: Path) -> Path:
    return path.with_name(path.name + ".bak")


def write_backup_if_absent(backup_target: Path, original_text: str) -> None:
    # Keep the earliest known-good original; do not clobber an existing backup.
    if backup_target.exists():
        return
    write_text(backup_target, original_text)


def restore_backups(root: Path) -> int:
    restored = 0
    for bak_path in sorted(root.rglob("*.bak")):
        if not bak_path.is_file():
            continue
        original_path = bak_path.with_name(bak_path.name[: -len(".bak")])
        original_path.write_bytes(bak_path.read_bytes())
        bak_path.unlink()
        print(f"ROLLBACK {original_path}")
        restored += 1
    return restored


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def clear_output_root(output_root: Path) -> None:
    for path in sorted(output_root.rglob("*"), reverse=True):
        try:
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        except FileNotFoundError:
            continue
        except PermissionError:
            if path.is_file() or path.is_symlink():
                raise PatchError(f"Could not delete output file: {path}")
            continue


def patch_tree(
    source_root: Path,
    output_root: Path,
    rules: list[Rule],
    marker: str,
    in_place: bool,
    keep_output: bool,
) -> int:
    source_files = [path for path in source_root.rglob("*") if path.is_file()]
    changed_files = 0
    applied_results: list[str] = []

    if not in_place and output_root.exists() and not keep_output:
        clear_output_root(output_root)

    for source_path in source_files:
        rel_path = source_path.relative_to(source_root)
        rel_posix = rel_path.as_posix()
        file_rules = [rule for rule in rules if matches_glob(rel_posix, rule.path_glob)]
        if not file_rules:
            continue

        text = read_text(source_path)
        original_text = text
        rule_results: list[RuleResult] = []

        for rule in sorted(file_rules, key=lambda item: item.line_hint, reverse=True):
            text, result = apply_rule(text, rule, marker)
            rule_results.append(result)

        if text == original_text:
            for result in reversed(rule_results):
                applied_results.append(
                    f"SKIP {rel_posix}: {result.rule.rule_id} ({result.status}, {result.detail})"
                )
            continue

        destination = source_path if in_place else output_root / rel_path
        write_backup_if_absent(backup_path(destination), original_text)
        write_text(destination, text)
        changed_files += 1

        for result in reversed(rule_results):
            applied_results.append(
                f"PATCH {rel_posix}: {result.rule.rule_id} ({result.status}, {result.detail})"
            )

    for message in applied_results:
        print(message)

    print(f"Modified files: {changed_files}")
    if not in_place:
        print(f"Patched file tree: {output_root}")
    return 0


def main() -> int:
    args = parse_args()
    rules_path = Path(args.rules).resolve()
    if not rules_path.is_file():
        print(f"ERROR: rules file not found: {rules_path}", file=sys.stderr)
        return 1

    try:
        config = load_config(rules_path)
        source_root, output_root, marker = resolve_roots(args, config)

        if args.rollback:
            rollback_root = source_root if args.in_place else output_root
            if not rollback_root.is_dir():
                raise PatchError(f"Rollback target does not exist: {rollback_root}")
            restored = restore_backups(rollback_root)
            print(f"Restored files: {restored}")
            return 0

        rules = build_rules(config)
        return patch_tree(
            source_root=source_root,
            output_root=output_root,
            rules=rules,
            marker=marker,
            in_place=args.in_place,
            keep_output=args.keep_output,
        )
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())