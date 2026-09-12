# fix_psl/code_patch

Utility folder for rule-based source patching.

## Files
- `code_patch.py`: Patch engine
- `code_patch_rules.toml`: Rule/config file
- `run_code_patch.bat`: Windows launcher

## Quick Start
Run from anywhere:

```bat
fix_psl\code_patch\run_code_patch.bat
```

Default behavior:
- Reads `fix_psl/code_patch/code_patch_rules.toml`
- Scans `source_root`
- Writes only changed files to `output_root` (temporary output tree)
- Does not overwrite original files

Overwrite originals:

```bat
fix_psl\code_patch\run_code_patch.bat --in-place
```

Keep previous temporary output files:

```bat
fix_psl\code_patch\run_code_patch.bat --keep-output
```

Use another rules file:

```bat
fix_psl\code_patch\run_code_patch.bat --rules C:\path\to\other_rules.toml
```

## Backups and Rollback
Every time a file is actually modified, the original content is saved next
to it as `filename.ext.bak` before the patched content is written:
- `--in-place`: backup is written next to the original in `source_root`.
- Default (no `--in-place`): backup is written next to the patched copy in
  `output_root` (`_patched_tmp`).

An existing `.bak` is never overwritten, so the earliest known-good original
is preserved across repeated runs.

Restore from backups and delete the `.bak` files:

```bat
REM restore output_root (_patched_tmp) from its .bak files
fix_psl\code_patch\run_code_patch.bat --rollback

REM restore source_root originals from their .bak files
fix_psl\code_patch\run_code_patch.bat --rollback --in-place
```

`--rollback` only restores files that currently have a matching `.bak`; it
does not apply or re-evaluate any rules.

## TOML Writing Guide
Top-level keys:
- `source_root` (required): source tree root
- `output_root` (required unless `--in-place`): temp output folder
- `marker` (optional): patch marker string (default `PATCHED_BY_code_patch.py`)

Path notes:
- `source_root` accepts DOS-style Windows paths like `C:\RTI\...`.
- Relative `output_root` is resolved from the rules file directory.
- `source_root` can be absolute or workspace-relative.

Rule block format:

```toml
[[rules]]
id = "unique-rule-id"
path_glob = "**/someFile.c"
operation = "replace_line"
line_hint = 100
search_window = 10
note = "short reason"
match = "exact original line"
replacement = "exact replacement line with optional {marker}"
```

Supported operations:
- `replace_line`
  - Replaces one exact line near `line_hint`
  - Required: `match`, `replacement`
- `disable_block`
  - Wraps matched preprocessor block with `#if 0 ...` and `#endif ...`
  - Required: `start`, `end`

`disable_block` example:

```toml
[[rules]]
id = "disable-sample"
path_glob = "**/sample.h"
operation = "disable_block"
line_hint = 200
search_window = 20
note = "temporarily disable block"
start = "#ifndef FEATURE_X"
end = "#endif /* !FEATURE_X */"
```

## Safety/Matching Behavior
- Matching is exact text (whitespace and comments must match).
- Target line is selected by nearest match to `line_hint`.
- If nearest match is outside `search_window`, execution stops with error.
- If a nearby line already contains `PATCHED_BY_`, the rule is skipped as already patched.

## Recommended Workflow
1. Edit `code_patch_rules.toml`
2. Run without `--in-place`
3. Inspect output in `_patched_tmp`
4. Run with `--in-place` only after validation
