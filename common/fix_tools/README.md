# fix_tools

Patch helper scripts for Connext Professional tools.

## Arcgen Fix 499

Default example:

```bat
fix_tools\fix_arcgen.bat
```

Equivalent command:

```bat
python fix_tools\fix_arcgen.py --source-dir fix_tools\arcgen_fix_499 --target-home C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1
```

Apply to another Connext Professional installation:

```bat
fix_tools\fix_arcgen.bat --source-dir fix_tools\arcgen_fix_499 --target-home C:\path\to\rti_connext_dds-7.3.1
```

Preview without writing:

```bat
fix_tools\fix_arcgen.bat --source-dir fix_tools\arcgen_fix_499 --target-home C:\path\to\rti_connext_dds-7.3.1 --dry-run
```

Target files are managed by `fix_tools\arcgen_fix_499\manifest.json`.
For arcgen, the files are installed under `resource\app\bin\x64Win64VS2017`.
If a target file already exists, it is copied next to the target as `<filename>.<timestamp>.bak` before patching.

Required patch binaries in `fix_tools\arcgen_fix_499`:
- `rtiarcgen.exe`
- `rtiaragen.exe`
