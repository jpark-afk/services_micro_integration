@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

REM User inputs
set "RTIMEHOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"
set "INPUT_XML=%~1"
set "OUTPUT_XML=%~2"
set "AUTOSAR_PARTICIPANT=%~3"
if "%INPUT_XML%"=="" set "INPUT_XML=%SCRIPT_DIR%CODA Master Interface_domain_1_v5.6_DPSE_QoS.xml"
if "%OUTPUT_XML%"=="" set "OUTPUT_XML=%SCRIPT_DIR%wpc_system.xml"
if "%AUTOSAR_PARTICIPANT%"=="" set "AUTOSAR_PARTICIPANT=WPC::Domain_1"

REM Internal paths
set "COMMON_TEMPLATES_DIR=%SCRIPT_DIR%..\..\..\common\templates"
set "WORKAROUND_DIR=%COMMON_TEMPLATES_DIR%\.workaround"
set "SCHEMA_PATH=%RTIMEHOME%\rtiddsmag\resource\schema\dds-xml_system_definitions.xsd"

if not exist "%INPUT_XML%" (
    echo ERROR: input XML not found: "%INPUT_XML%"
    exit /b 1
)
if not exist "%SCHEMA_PATH%" (
    echo ERROR: DDS System XML schema not found: "%SCHEMA_PATH%"
    exit /b 1
)

call "%WORKAROUND_DIR%\patch_missing_part_hkmc.bat" "%INPUT_XML%" "%OUTPUT_XML%" "%AUTOSAR_PARTICIPANT%" "%SCHEMA_PATH%"
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