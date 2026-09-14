@echo off
setlocal
call :print_notice

cd /d "%~dp0"

set "RTIMEHOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"
set "XML_DIR=user_work"
set "RTIME_MAG_FILES=test_system.xml"
set "JRE_HOME=C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1\resource\app\jre\x64Win64"
set "TARGET_NAME=x86_64lePEvs2017-Win10"
set "BUILD_CONFIG=Debug"
set "MSVC_ARCH=x64"
set "SRC_DIR=.\testapp"

if not exist "%SRC_DIR%" exit /b 1
if not exist "%XML_DIR%\%RTIME_MAG_FILES%" exit /b 1

echo(%RTIME_MAG_FILES%| findstr /R "[\\/]" >nul
if not errorlevel 1 exit /b 1

set "STAGED_XML=0"
if not exist "%SRC_DIR%\%RTIME_MAG_FILES%" set "STAGED_XML=1"
copy /Y "%XML_DIR%\%RTIME_MAG_FILES%" "%SRC_DIR%\%RTIME_MAG_FILES%" >nul
if errorlevel 1 exit /b 1

for %%F in ("%RTIME_MAG_FILES%") do set "APP_BASE=%%~nF"
if not exist "%SRC_DIR%\%APP_BASE%Appgen.c" exit /b 1
if not exist "%SRC_DIR%\%APP_BASE%Appgen.h" exit /b 1

set "BUILD_DRIVE="
for %%D in (Z Y X W V U T S R Q P O N M L K J I H G F E D) do if not defined BUILD_DRIVE if not exist "%%D:\" set "BUILD_DRIVE=%%D:"
if not defined BUILD_DRIVE (
    echo ERROR: No free drive letter is available for the short build path.
    exit /b 1
)

subst %BUILD_DRIVE% "%CD%"
if errorlevel 1 exit /b 1

pushd "%BUILD_DRIVE%\testapp"
call "%RTIMEHOME%\resource\scripts\rtime-make.bat" ^
    --config %BUILD_CONFIG% ^
    -A %MSVC_ARCH% ^
    --target self ^
    --name %TARGET_NAME% ^
    --build ^
    --source-dir . ^
    --delete ^
    -DRTIME_MAG_FILES_eq_%RTIME_MAG_FILES%
set "BUILD_RESULT=%errorlevel%"
popd
subst %BUILD_DRIVE% /d

if not "%BUILD_RESULT%"=="0" exit /b 1
if "%STAGED_XML%"=="1" del /q "%SRC_DIR%\%RTIME_MAG_FILES%"

echo Done. Build output is under "%SRC_DIR%\objs".
endlocal
exit /b 0

:print_notice
echo [RTI NOTICE] INTERNAL TEMPORARY WORKAROUND
echo [RTI NOTICE] Temporary workaround until an official RTI patch is released.
echo [RTI NOTICE] Baseline version: Micro430er738.
echo [RTI NOTICE] Not officially supported by RTI Technical Support.
echo [RTI NOTICE] Must NOT be applied directly to controller mass-production development.
echo [RTI NOTICE] See README.md for details.
exit /b 0