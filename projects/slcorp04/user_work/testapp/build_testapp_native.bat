@echo off
REM RTI INTERNAL TEMPORARY WORKAROUND NOTICE
REM Temporary workaround until an official RTI patch is released.
REM Baseline version: Micro430er738.
REM Not officially supported by RTI Technical Support.
REM Must NOT be applied directly to controller mass-production development.

setlocal
call :print_notice

REM Run from this script's own directory so generated paths stay local to slcorp04.
cd /d "%~dp0"

REM ============================================================
REM  User-configurable variables - edit these for your project
REM ============================================================

REM Connext Micro 4.3.0 installation root. Keep aligned with ..\build_testapp.bat.
set "RTIMEHOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"

REM Java runtime root used by RTI build/generation tooling. Keep aligned with ..\build_testapp.bat.
set "JRE_HOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\resource\app\jre\x64Win64"

set "RTIME_TARGET_NAME=x86_64lePEvs2017-Win10"
set "BUILD_CONFIG=Debug"
set "MSVC_ARCH=x64"
set "BUILD_DIR=%CD%\native_build"
set "APPLICATION_DIR=%CD%\native_output\MyDeploymentLib\MyDeploymentScenario\GCS_LEFT_2_Domain_6_Deployment\GCS_LEFT_2_Domain_6_Application"
set "APPLICATION_EXE=%APPLICATION_DIR%\objs\%RTIME_TARGET_NAME%\%BUILD_CONFIG%\GCS_LEFT_2_Domain_6_Application.exe"

REM ============================================================
REM  Pre-checks
REM ============================================================
if not exist "%APPLICATION_DIR%\CMakeLists.txt" (
    echo Generated application CMakeLists.txt not found: "%APPLICATION_DIR%\CMakeLists.txt"
    echo Run generate_testapp_native.bat first.
    exit /b 1
)

where cmake >nul 2>&1
if errorlevel 1 (
    echo cmake was not found on PATH.
    exit /b 1
)

if exist "%BUILD_DIR%\CMakeCache.txt" (
    findstr /C:"CMAKE_GENERATOR_PLATFORM:INTERNAL=%MSVC_ARCH%" "%BUILD_DIR%\CMakeCache.txt" >nul 2>&1
    if errorlevel 1 (
        echo Existing build directory was configured for a different platform. Removing "%BUILD_DIR%"...
        rmdir /s /q "%BUILD_DIR%"
    )
)

REM ============================================================
REM  Build with CMake
REM ============================================================
echo Configuring "%APPLICATION_DIR%"...
cmake -S "%APPLICATION_DIR%" -B "%BUILD_DIR%" -A %MSVC_ARCH% -DCMAKE_BUILD_TYPE=%BUILD_CONFIG%
if errorlevel 1 (
    echo cmake configure failed.
    exit /b 1
)

echo Building "%BUILD_CONFIG%"...
cmake --build "%BUILD_DIR%" --config "%BUILD_CONFIG%" --parallel
if errorlevel 1 (
    echo cmake build failed.
    exit /b 1
)

echo Done. Executable should be under:
echo "%APPLICATION_EXE%"
endlocal
exit /b 0

:print_notice
echo [RTI NOTICE] INTERNAL TEMPORARY WORKAROUND
echo [RTI NOTICE] Temporary workaround until an official RTI patch is released.
echo [RTI NOTICE] Baseline version: Micro430er738.
echo [RTI NOTICE] Not officially supported by RTI Technical Support.
echo [RTI NOTICE] Must NOT be applied directly to controller mass-production development.
exit /b 0