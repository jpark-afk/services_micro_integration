# Project-Specific Assets

`projects/` keeps project-specific input files outside the shared `common/` submodule.

## Clone and Update Shared Assets

Clone this repository with its pinned shared-workaround release:

```powershell
git clone --recurse-submodules git@github.com:jpark-afk/services_micro_integration.git
```

For an existing clone, initialize the shared assets and enable recursive updates for later Git operations:

```powershell
git submodule update --init --recursive
git config submodule.recurse true
```

`common/` is pinned to a release tag from `git@github.com:jpark-afk/micro_workaround.git`. To adopt a newer shared release, check out its tag in `common/`, stage the resulting gitlink in this repository, and commit that pointer update.

## Git Hooks

Enable the version-controlled hooks once after cloning:

```bat
.\.githooks\install.bat
```

After each parent-repository checkout, the `post-checkout` hook initializes and updates submodules to the commit pinned by the parent repository. It deliberately does not use `--remote`, so a checkout remains reproducible and does not silently advance `common/`.

## New Project Layout

Create one folder per project:

```text
projects/
  <your_project>/
    project-template-values.yaml
    user_work/
      <system xml files>
```

Put the original system XML or CODA XML files under `<your_project>/user_work/`. The file names used there must be written explicitly in `<your_project>/project-template-values.yaml`.

Generate runnable scripts after writing the YAML file:

```bat
..\..\common\management\render_project_scripts.bat .\project-template-values.yaml --force
```

Run the command from `projects\<your_project>`. It generates scripts such as `generate_ddscdd.bat`, `generate_testapp_native.bat`, `generate_testapp_native.sh`, `build_testapp_native.bat`, `build_testapp_native.sh`, and `user_work\patch_run.bat`.

## Generation Workflow

Run the following commands from `projects\<your_project>` after setting the values in `project-template-values.yaml`:

```bat
..\..\common\management\render_project_scripts.bat .\project-template-values.yaml --force
.\user_work\patch_run.bat
.\generate_ddscdd.bat
```

`patch_run.bat` applies the required workarounds to `PATCH_INPUT_XML_FILE` and writes `PATCH_OUTPUT_XML_FILE` under `user_work\`. `generate_ddscdd.bat` then uses that patched XML and `DEPLOYMENT_NAME` to generate the AUTOSAR CDD development code.

Create a separate XML input for the native TestApp by copying the patched XML to the `RTIME_MAG_FILES` name, normally `test_system.xml`. Do not replace the CDD input XML.

```bat
copy /Y ".\user_work\<PATCH_OUTPUT_XML_FILE>" ".\user_work\test_system.xml"
.\generate_testapp_native.bat
.\build_testapp_native.bat
```

Before generating the TestApp, set `NATIVE_MAG_DEPLOYMENT` to a deployment that exists in `test_system.xml`. `generate_testapp_native.bat` creates the TestApp source under `testapp\`; `build_testapp_native.bat` builds it for `WINDOWS_TARGET_NAME`.

## project-template-values.yaml Guide

Use this structure:

```yaml
project: <your_project>

tokens:
  RTIMEHOME: C:\RTI\...\rti_connext_dds_micro-4.3.0_ER738
  JRE_HOME: C:\RTI\...\resource\app\jre\x64Win64
  PROJECT_WORK_DIR: user_work
  PATCH_INPUT_XML_FILE: <original CODA XML file name>
  PATCH_OUTPUT_XML_FILE: <patched system XML file name>
  PATCH_AUTOSAR_PARTICIPANT: <AUTOSAR participant selector>
  PATCH_WORKAROUND_DIR: ..\..\..\common\templates\.workaround
  SYSTEM_XML_REL_PATH: '@PROJECT_WORK_DIR@\@PATCH_OUTPUT_XML_FILE@'
  DEPLOYMENT_NAME: <deployment name in system XML>
  NATIVE_MAG_DEPLOYMENT: <native test app deployment name>
  DEPLOYMENT_LIBRARY_NAME: MyDeploymentLib
  DEPLOYMENT_SCENARIO_NAME: MyDeploymentScenario
  APPLICATION_NAME: <application name in deployment path>
  DOMAIN_PARTICIPANT_NAME: <domain participant name in deployment path>
  IS_CERT: YES
  IS_DPSE: YES
  RTIME_MAG_FILES: test_system.xml
  NATIVE_SYSTEM_XML_REL_PATH: '@TEST_XML_DIR@\@RTIME_MAG_FILES@'
  TEST_XML_DIR: '@PROJECT_WORK_DIR@'
  WINDOWS_TARGET_NAME: x86_64lePEvs2017-Win10
  RTIMEHOME_LINUX: /path/to/rti_connext_dds_micro-4.3.0
  JRE_HOME_LINUX: /usr/lib/jvm/default-java
  TEST_XML_DIR_POSIX: './@PROJECT_WORK_DIR@'
  LINUX_TARGET_NAME: x86_64leElfgcc13.3.0-Linux6
```

Field notes:

- `project`: Project folder name. Usually the same as `projects/<your_project>`.
- `RTIMEHOME`: Windows Connext Micro installation root.
- `JRE_HOME`: Windows Java runtime used by `rtime-make.bat`.
- `PROJECT_WORK_DIR`: Project-local work folder. Keep this as `user_work` unless the folder name changes.
- `PATCH_INPUT_XML_FILE`: Original CODA XML file placed under `PROJECT_WORK_DIR`.
- `PATCH_OUTPUT_XML_FILE`: Patched DDS system XML file produced by `user_work\patch_run.bat`; this is the main system XML used by `generate_ddscdd.bat`.
- `PATCH_AUTOSAR_PARTICIPANT`: AUTOSAR participant selector passed to the missing-part workaround.
- `PATCH_WORKAROUND_DIR`: Relative path from `PROJECT_WORK_DIR` to `common\templates\.workaround`.
- `SYSTEM_XML_REL_PATH`: Relative path from project root to the patched system XML. Prefer `@PROJECT_WORK_DIR@\@PATCH_OUTPUT_XML_FILE@`.
- `DEPLOYMENT_NAME`: Deployment name passed to `rtiddsmag` for AUTOSAR CDD generation.
- `NATIVE_MAG_DEPLOYMENT`: Deployment name passed to `rtiddsmag` for native test app generation.
- `DEPLOYMENT_LIBRARY_NAME`: Deployment library folder name generated by MAG.
- `DEPLOYMENT_SCENARIO_NAME`: Deployment scenario folder name generated by MAG.
- `APPLICATION_NAME`: Application folder name generated by MAG.
- `DOMAIN_PARTICIPANT_NAME`: Domain participant folder name generated by MAG.
- `IS_CERT`: `YES` for CERT-flag-enabled flow, otherwise `NO`.
- `IS_DPSE`: `YES` when DPSE appgen patching is required.
- `RTIME_MAG_FILES`: Native test app XML file name. Use a project-neutral name such as `test_system.xml`.
- `NATIVE_SYSTEM_XML_REL_PATH`: Relative path from project root to the native test app XML. Prefer `@TEST_XML_DIR@\@RTIME_MAG_FILES@`.
- `TEST_XML_DIR`: Folder containing the native test app XML. Usually `@PROJECT_WORK_DIR@`.
- `WINDOWS_TARGET_NAME`: Target name passed to Windows `rtime-make.bat`.
- `RTIMEHOME_LINUX`: Linux Connext Micro installation root for `build_testapp_native.sh`.
- `JRE_HOME_LINUX`: Linux Java runtime for native test app builds.
- `TEST_XML_DIR_POSIX`: POSIX path to the native test app XML folder. Usually `./@PROJECT_WORK_DIR@`.
- `LINUX_TARGET_NAME`: Target name passed to Linux `rtime-make`.

Token values may reference other token values with `@TOKEN_NAME@`. The renderer expands those references before writing scripts.
