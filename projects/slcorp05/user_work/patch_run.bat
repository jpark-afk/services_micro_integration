@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "COMMON_TEMPLATES_DIR=%SCRIPT_DIR%..\..\..\common\templates"
set "WORKAROUND_DIR=%COMMON_TEMPLATES_DIR%\.workaround"
set "INPUT_XML=%~1"
set "OUTPUT_XML=%~2"
set "AUTOSAR_PARTICIPANT=%~3"

if "%INPUT_XML%"=="" set "INPUT_XML=%SCRIPT_DIR%CODA Master Interface_domain_1_v5.6_DPSE_QoS.xml"
if "%OUTPUT_XML%"=="" set "OUTPUT_XML=%SCRIPT_DIR%wpc_system.xml"
if "%AUTOSAR_PARTICIPANT%"=="" set "AUTOSAR_PARTICIPANT=WPC::Domain_1"

if not exist "%INPUT_XML%" (
    echo ERROR: input XML not found: "%INPUT_XML%"
    exit /b 1
)

call "%WORKAROUND_DIR%\patch_missing_part_hkmc.bat" "%INPUT_XML%" "%OUTPUT_XML%" "%AUTOSAR_PARTICIPANT%"
if errorlevel 1 (
    echo ERROR: missing-part patch failed.
    exit /b 1
)

call "%WORKAROUND_DIR%\patch_arcgen_types.bat" "%OUTPUT_XML%" "%OUTPUT_XML%"
if errorlevel 1 (
    echo ERROR: arcgen type patch failed.
    exit /b 1
)

echo Patched XML saved: "%OUTPUT_XML%"
endlocal
exit /b 0