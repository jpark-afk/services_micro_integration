@echo off
setlocal EnableDelayedExpansion
call :print_notice

cd /d "%~dp0"

set "RTIMEHOME=@RTIMEHOME@"
set "SYSTEM_XML_PATH=%~dp0\@SYSTEM_XML_REL_PATH@"
set "JRE_HOME=@JRE_HOME@"

set "OUTPUT_DIR=.\"
set "DEPLOYMENT_NAME=@DEPLOYMENT_NAME@"
set "APPLICATION_TYPE=AUTOSAR_CDD"
set "LANGUAGE=C"
set "IS_CERT=@IS_CERT@"
set "IS_DPSE=@IS_DPSE@"

set "COMMON_TEMPLATES_DIR=%~dp0@COMMON_TEMPLATES_DIR@"
set "AUTOSAR_TEMPLATE_PATH=%COMMON_TEMPLATES_DIR%\autosar"
set "MAG_TEMPLATE_PATH=%COMMON_TEMPLATES_DIR%\.workaround"
set "ARCGEN_TARGET=AUTOSAR"

set "DEPLOYMENT_LIBRARY_NAME=@DEPLOYMENT_LIBRARY_NAME@"
set "DEPLOYMENT_SCENARIO_NAME=@DEPLOYMENT_SCENARIO_NAME@"
set "APPLICATION_NAME=@APPLICATION_NAME@"
set "DOMAIN_PARTICIPANT_NAME=@DOMAIN_PARTICIPANT_NAME@"

for %%F in ("%SYSTEM_XML_PATH%") do set "XML_NAME=%%~nF"

echo [1/5] Running rtiddsmag...
call "%RTIMEHOME%\bin\rtiddsmag.bat" ^
    -inputXml "%SYSTEM_XML_PATH%" ^
    -deployment %DEPLOYMENT_NAME% ^
    -applicationType %APPLICATION_TYPE% ^
    -language %LANGUAGE% ^
    -d %OUTPUT_DIR% ^
    -autosarTemplatePath "%AUTOSAR_TEMPLATE_PATH%" ^
    -replace
if errorlevel 1 exit /b 1

set "PARTICIPANT_DIR=%OUTPUT_DIR%\%DEPLOYMENT_LIBRARY_NAME%\%DEPLOYMENT_SCENARIO_NAME%\%DEPLOYMENT_NAME%\%APPLICATION_NAME%\%DOMAIN_PARTICIPANT_NAME%"
set "DDS_GEN_DIR=%PARTICIPANT_DIR%\dds_gen"

echo [2/5] Running rtiarcgen...
if not exist "%DDS_GEN_DIR%" mkdir "%DDS_GEN_DIR%"
pushd "%DDS_GEN_DIR%"
set "RTIDDSGEN_PATH=%RTIMEHOME%\rtiddsgen\scripts\rtiddsgen.bat"
set "RTIDDSGEN_PARAMS=-create typefiles -micro -language C -ppDisable -interpreted 0"
call "%RTIMEHOME%\..\bin\rtiarcgen" -arxmlTypes "%SYSTEM_XML_PATH%" -arxmlPath . -singleFile -target %ARCGEN_TARGET% -ddsTypeSupport -conversions
set "RTIARCGEN_RESULT=%errorlevel%"
popd
if not "%RTIARCGEN_RESULT%"=="0" exit /b 1

echo [3/5] Creating dds_cdd_userstub.h...
type nul > "%PARTICIPANT_DIR%\dds_cdd_userstub.h"
if errorlevel 1 exit /b 1

if /I "%IS_DPSE%"=="YES" (
    echo [4/5] DPSE Appgen patch...
    set "DPSE_TEMP_DIR=%PARTICIPANT_DIR%\dpse_appgen_temp"
    if not exist "!DPSE_TEMP_DIR!" mkdir "!DPSE_TEMP_DIR!"
    call "%RTIMEHOME%\bin\rtiddsmag.bat" ^
        -inputXml "%SYSTEM_XML_PATH%" ^
        -language %LANGUAGE% ^
        -d "!DPSE_TEMP_DIR!" ^
        -autosarTemplatePath "%AUTOSAR_TEMPLATE_PATH%" ^
        -replace
    if errorlevel 1 exit /b 1
    python "%MAG_TEMPLATE_PATH%\patch_dpse_appgen.py" --xml-name %XML_NAME% --origin-dir "%PARTICIPANT_DIR%\dds_impl" --temp-dir "!DPSE_TEMP_DIR!"
    if errorlevel 1 exit /b 1
    rmdir /s /q "!DPSE_TEMP_DIR!"
)

echo [5/5] Patching unused conversion blocks...
python "%MAG_TEMPLATE_PATH%\patch_unused_conversions.py" ^
    --system-xml "%SYSTEM_XML_PATH%" ^
    --deployment "%DEPLOYMENT_NAME%" ^
    --c "%DDS_GEN_DIR%\%XML_NAME%_conversions.c" ^
    --h "%DDS_GEN_DIR%\%XML_NAME%_conversions.h"
if errorlevel 1 exit /b 1

echo Done. Generated files are under "%PARTICIPANT_DIR%".
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