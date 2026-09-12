@echo off
REM RTI INTERNAL TEMPORARY WORKAROUND NOTICE
REM Temporary workaround until an official RTI patch is released.
REM Baseline version: Micro430er738.
REM Not officially supported by RTI Technical Support.
REM Must NOT be applied directly to controller mass-production development.

setlocal enabledelayedexpansion
call :print_notice

REM Run from this script's own directory so .\pdio_fl_system.xml resolves here.
cd /d "%~dp0"
set "WORKSPACE=%CD%"

REM ============================================================
REM  User-configurable variables - edit these for your project
REM ============================================================

REM Connext Micro 4.3.0 installation root. Keep aligned with ..\build_testapp.bat.
set "RTIMEHOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"

REM Java runtime root used by RTI build/generation tooling. Keep aligned with ..\build_testapp.bat.
set "JRE_HOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\resource\app\jre\x64Win64"

set "RTIME_TARGET_NAME=x86_64lePEvs2017-Win10"
set "SYSTEM_XML=gcs_test_system.xml"
set "OUTPUT_DIR=native_output"
set "DEPLOYMENT=GCS_LEFT_2_Domain_6_Deployment"
set "APPLICATION_DIR=native_output\MyDeploymentLib\MyDeploymentScenario\GCS_LEFT_2_Domain_6_Deployment\GCS_LEFT_2_Domain_6_Application"
set "COMMON_TEMPLATES_DIR=%~dp0..\..\..\..\common\templates"
set "MAG_TEMPLATE_PATH=%COMMON_TEMPLATES_DIR%\.workaround"
for %%F in ("%SYSTEM_XML%") do set "XML_NAME=%%~nF"

REM Prefer the tool locations used by the project scripts; fall back to the paths shown in the MD guide.
set "RTIDDSMAG_BAT=%RTIMEHOME%\bin\rtiddsmag.bat"
if not exist "%RTIDDSMAG_BAT%" set "RTIDDSMAG_BAT=%RTIMEHOME%\rtiddsmag\scripts\rtiddsmag.bat"

set "RTIDDSGEN_BAT=%RTIMEHOME%\bin\rtiddsgen.bat"
if not exist "%RTIDDSGEN_BAT%" set "RTIDDSGEN_BAT=%RTIMEHOME%\rtiddsgen\scripts\rtiddsgen.bat"

REM ============================================================
REM  Pre-checks
REM ============================================================
if not exist "%SYSTEM_XML%" (
    echo DDS System XML not found: "%CD%\%SYSTEM_XML%"
    exit /b 1
)

if not exist "%RTIDDSMAG_BAT%" (
    echo rtiddsmag.bat not found under RTIMEHOME: "%RTIMEHOME%"
    exit /b 1
)

if not exist "%RTIDDSGEN_BAT%" (
    echo rtiddsgen.bat not found under RTIMEHOME: "%RTIMEHOME%"
    exit /b 1
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM ============================================================
REM  Step 1: Generate the deployment-aware Micro C application
REM ============================================================
echo [1/3] Running rtiddsmag for "%DEPLOYMENT%"...
call "%RTIDDSMAG_BAT%" ^
    -inputXml "%SYSTEM_XML%" ^
    -language C ^
    -d "%OUTPUT_DIR%" ^
    -replace ^
    -deployment "%DEPLOYMENT%" ^
    -applicationType micro4 ^
    -verbosity 3
if errorlevel 1 (
    echo rtiddsmag failed.
    exit /b 1
)

if not exist "%APPLICATION_DIR%" (
    echo Expected generated application folder not found: "%APPLICATION_DIR%"
    exit /b 1
)

REM ============================================================
REM  Step 2: Generate type support beside the MAG-generated sources
REM ============================================================
echo [2/3] Running rtiddsgen type support generation...
pushd "%RTIMEHOME%\rtiddsmag"
call "%RTIDDSGEN_BAT%" ^
    -create typefiles ^
    -micro ^
    -language C ^
    -interpreted 0 ^
    "%WORKSPACE%\%SYSTEM_XML%" ^
    -d "%WORKSPACE%\%APPLICATION_DIR%" ^
    -replace
set "RTIDDSGEN_RESULT=%errorlevel%"
popd

if not "%RTIDDSGEN_RESULT%"=="0" (
    echo rtiddsgen failed.
    exit /b 1
)

REM ============================================================
REM  Step 3: DPSE Appgen patch
REM  Regenerate Appgen without -deployment/-applicationType so DPSE remote
REM  participants/endpoints are emitted, then overwrite only Appgen.h/.c.
REM ============================================================
echo [3/3] DPSE Appgen patch...
set "DPSE_TEMP_DIR=%APPLICATION_DIR%\dpse_appgen_temp"
if not exist "!DPSE_TEMP_DIR!" mkdir "!DPSE_TEMP_DIR!"

call "%RTIDDSMAG_BAT%" ^
    -inputXml "%SYSTEM_XML%" ^
    -language C ^
    -d "!DPSE_TEMP_DIR!" ^
    -replace
if errorlevel 1 (
    echo rtiddsmag DPSE Appgen generation failed.
    exit /b 1
)

python "%MAG_TEMPLATE_PATH%\patch_dpse_appgen.py" --xml-name %XML_NAME% --origin-dir "%APPLICATION_DIR%" --temp-dir "!DPSE_TEMP_DIR!" --takeall
if errorlevel 1 (
    echo DPSE Appgen patch failed.
    exit /b 1
)

rmdir /s /q "!DPSE_TEMP_DIR!"

echo Done. Generated application is under "%APPLICATION_DIR%".
endlocal
exit /b 0

:print_notice
echo [RTI NOTICE] INTERNAL TEMPORARY WORKAROUND
echo [RTI NOTICE] Temporary workaround until an official RTI patch is released.
echo [RTI NOTICE] Baseline version: Micro430er738.
echo [RTI NOTICE] Not officially supported by RTI Technical Support.
echo [RTI NOTICE] Must NOT be applied directly to controller mass-production development.
exit /b 0