# Project Script Templates

These templates are shared by SLCORP04 and SLCORP05. Replace `@TOKEN@` values per project before writing runnable scripts into a project folder.

Generate runnable scripts from a project token file:

```bat
common\management\render_project_scripts.bat projects\slcorp04\project-template-values.yaml --force
```

This reads `common\templates\.project_scripts\**\*.template.*` and writes files such as `generate_ddscdd.bat` and `@PROJECT_WORK_DIR@\patch_run.bat` into the directory containing `project-template-values.yaml`.

Common tokens:

Token values may reference other tokens. For example, `SYSTEM_XML_REL_PATH` can be `@PROJECT_WORK_DIR@\@PATCH_OUTPUT_XML_FILE@`.

- `@RTIMEHOME@`
- `@JRE_HOME@`
- `@PROJECT_WORK_DIR@`
- `@COMMON_TEMPLATES_DIR@`
- `@SYSTEM_XML_REL_PATH@`
- `@NATIVE_SYSTEM_XML_REL_PATH@`
- `@TEST_XML_DIR@`
- `@RTIME_MAG_FILES@`
- `@DEPLOYMENT_NAME@`
- `@APPLICATION_NAME@`
- `@DOMAIN_PARTICIPANT_NAME@`
- `@IS_CERT@`
- `@IS_DPSE@`
- `@PATCH_INPUT_XML_FILE@`
- `@PATCH_OUTPUT_XML_FILE@`
- `@PATCH_AUTOSAR_PARTICIPANT@`
- `@TEST_XML_DIR_POSIX@`
