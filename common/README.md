# Common SLCORP Assets

This folder is the proposed Git submodule root for files shared by SLCORP04 and SLCORP05.

## Layout

- `xml_example/`: shared DPSE/static-discovery XML examples.
- `fix_psl/`: Connext Micro PSL patch fetch/apply utilities, patch payloads, and rule-based code patch helpers.
- `fix_tools/`: local Connext tool patch helpers.
- `templates/`: shared MAG, AUTOSAR, C/C++, workaround, and script templates.
- `management/`: deployment, report, export, and marker update utilities.

Project-specific input files stay outside this folder under `projects/<project>/user_work`.