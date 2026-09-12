# fix_psl

PSL patch utilities for fetching upstream patch payloads, applying them to a PSL home directory, and running rule-based local source patches.

## Fetch Changed PR Files

```bat
fix_psl\fetch_pr_files.bat https://bitbucket.rti.com/projects/CONNEXT/repos/connextmicro/pull-requests/5416
```

Default behavior:
- Fetches `refs/pull-requests/<id>/from` from Git.
- Uses `refs/pull-requests/<id>/merge` to calculate the files changed by the PR.
- Downloads only changed files under `rti/ndds_lite/rti_me_psl.2.0/`.
- Writes them under `fix_psl/repository/`, preserving the path below `rti_me_psl.2.0/`.
- Writes `fix_psl/repository/manifest.json`.

If the Bitbucket merge ref is unavailable, provide the target branch:

```bat
fix_psl\fetch_pr_files.bat https://bitbucket.rti.com/projects/CONNEXT/repos/connextmicro/pull-requests/5416 --base-ref develop
```

Fetch changed files from a source branch compared to its base branch:

```bat
fix_psl\fetch_pr_files.bat task/PLATFORMS-6094 --base-ref develop/connextmicro
```

If only a PR id is provided, also provide the clone URL:

```bat
fix_psl\fetch_pr_files.bat 5416 --repo-url https://bitbucket.rti.com/scm/connext/connextmicro.git
```

Useful options:
- `--source-prefix rti/ndds_lite/rti_me_psl.2.0`: source folder to extract from the repository.
- `--repo-url https://bitbucket.rti.com/scm/connext/connextmicro.git`: repository URL; this is the default.
- `--download-root fix_psl\repository`: destination for fetched files.
- `--keep-prefix`: write files under `repository\rti_me_psl2.0\...` instead of stripping the prefix.
- `--keep-existing`: do not clean `repository` before fetching.

## Apply To PSL Home

Apply path mapping:
- `repository\include\...` -> `RTIMEHOME\include\rti_me\...`
- `repository\srcC\...` -> `RTIMEHOME\src\rti_me_psl\...`

Test with an empty local target folder:

```bat
mkdir fix_psl\psl_target
fix_psl\apply_psl_patch.bat --psl-home fix_psl\psl_target
```

Apply to a real PSL home directory:

```bat
fix_psl\apply_psl_patch.bat --psl-home C:\path\to\RTIMEHOME
```

Preview without writing:

```bat
fix_psl\apply_psl_patch.bat --psl-home C:\path\to\RTIMEHOME --dry-run
```

`apply_psl_patch.py` copies the files listed in `manifest.json`. If the manifest is missing, it copies every file under `repository` except `manifest.json`.

## Rule-Based Code Patch

Rule-based patch utilities are under `fix_psl\code_patch`.

Files:
- `code_patch\code_patch.py`: patch engine
- `code_patch\code_patch_rules.toml`: rule/config file
- `code_patch\run_code_patch.bat`: Windows launcher

Run in dry-output mode:

```bat
fix_psl\code_patch\run_code_patch.bat
```

Default behavior:
- Reads `fix_psl\code_patch\code_patch_rules.toml`
- Scans `source_root`
- Writes only changed files to `output_root` (`_patched_tmp` by default)
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

Restore from backups and delete the `.bak` files:

```bat
REM restore output_root (_patched_tmp) from its .bak files
fix_psl\code_patch\run_code_patch.bat --rollback

REM restore source_root originals from their .bak files
fix_psl\code_patch\run_code_patch.bat --rollback --in-place
```

Every modified file gets a `filename.ext.bak` backup. Existing `.bak` files are never overwritten.