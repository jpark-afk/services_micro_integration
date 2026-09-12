#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TOKEN_RE = re.compile(r"@([A-Z0-9_]+)@")


def expand_token_values(tokens: dict[str, str]) -> dict[str, str]:
    expanded = dict(tokens)

    for _ in range(len(expanded) + 1):
        changed = False
        for key, value in list(expanded.items()):
            missing = sorted({match.group(1) for match in TOKEN_RE.finditer(value) if match.group(1) not in expanded})
            if missing:
                joined = ", ".join(missing)
                raise ValueError(f"Missing referenced token(s) in {key}: {joined}")

            resolved = TOKEN_RE.sub(lambda match: expanded[match.group(1)], value)
            if resolved != value:
                expanded[key] = resolved
                changed = True

        if not changed:
            unresolved = sorted(key for key, value in expanded.items() if TOKEN_RE.search(value))
            if unresolved:
                joined = ", ".join(unresolved)
                raise ValueError(f"Circular token reference(s): {joined}")
            return expanded

    raise ValueError("Circular token reference detected")


def parse_project_values(path: Path) -> dict[str, str]:
    tokens: dict[str, str] = {}
    in_tokens = False

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "tokens:":
            in_tokens = True
            continue

        if not in_tokens:
            continue

        if not raw.startswith((" ", "\t")):
            in_tokens = False
            continue

        if ":" not in stripped:
            raise ValueError(f"Invalid token entry at line {line_no}: {raw}")

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        tokens[key] = value

    if not tokens:
        raise ValueError(f"No tokens found in {path}")
    return expand_token_values(tokens)


def render_text(template_text: str, tokens: dict[str, str], template_path: Path) -> str:
    missing = sorted({match.group(1) for match in TOKEN_RE.finditer(template_text) if match.group(1) not in tokens})
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing token(s) for {template_path}: {joined}")

    return TOKEN_RE.sub(lambda match: tokens[match.group(1)], template_text)


def output_name(template_path: Path) -> str:
    name = template_path.name
    if ".template." not in name:
        raise ValueError(f"Template file name must contain .template.: {template_path}")
    return name.replace(".template.", ".", 1)


def output_path(template_path: Path, template_dir: Path, output_dir: Path, tokens: dict[str, str]) -> Path:
    relative_parent = template_path.parent.relative_to(template_dir)
    rendered_parent = render_text(relative_parent.as_posix(), tokens, template_path)
    return output_dir / Path(rendered_parent) / output_name(template_path)


def render_templates(values_path: Path, template_dir: Path, output_dir: Path, force: bool) -> list[Path]:
    tokens = parse_project_values(values_path)
    templates = sorted(template_dir.rglob("*.template.*"))
    if not templates:
        raise FileNotFoundError(f"No script templates found in {template_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for template_path in templates:
        destination = output_path(template_path, template_dir, output_dir, tokens)
        if destination.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file: {destination}. Use --force to overwrite.")

        rendered = render_text(template_path.read_text(encoding="utf-8"), tokens, template_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="")
        written.append(destination)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Render project runner scripts from project-template-values.yaml")
    parser.add_argument("values", type=Path, help="Path to projects/<project>/project-template-values.yaml")
    parser.add_argument("--template-dir", type=Path, default=Path(__file__).resolve().parents[1] / "templates" / ".project_scripts")
    parser.add_argument("--output-dir", type=Path, help="Output directory. Default: directory containing the values file")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated scripts")
    args = parser.parse_args()

    values_path = args.values.resolve()
    template_dir = args.template_dir.resolve()
    output_dir = (args.output_dir or values_path.parent).resolve()

    try:
        written = render_templates(values_path, template_dir, output_dir, args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())