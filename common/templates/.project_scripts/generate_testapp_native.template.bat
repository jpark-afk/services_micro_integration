@echo off
setlocal enabledelayedexpansion
call :print_notice

cd /d "%~dp0"

set "RTIMEHOME=@RTIMEHOME@"
set "SYSTEM_XML_PATH=%~dp0\@NATIVE_SYSTEM_XML_REL_PATH@"
set "JRE_HOME=@JRE_HOME@"
set "IS_CERT=@IS_CERT@"
set "IS_DPSE=@IS_DPSE@"
set "MAG_APPLICATION_TYPE=micro4"
set "OUTPUT=testapp"
set "MAG_DEPLOYMENT=@NATIVE_MAG_DEPLOYMENT@"
set "COMMON_TEMPLATES_DIR=%~dp0@COMMON_TEMPLATES_DIR@"
set "MAG_TEMPLATE_PATH=%COMMON_TEMPLATES_DIR%\.workaround"

if not exist "%OUTPUT%" mkdir "%OUTPUT%"
dir /a /b "%OUTPUT%" 2>nul | findstr . >nul
if %errorlevel%==0 (
    attrib -h -s "%OUTPUT%\*" /s /d >nul 2>&1
    for /d %%D in ("%OUTPUT%\*") do rmdir /s /q "%%~fD"
    del /f /q "%OUTPUT%\*" >nul 2>&1
)

echo [1/5] Running rtiddsmag...
call "%RTIMEHOME%\bin\rtiddsmag.bat" ^
    -inputXml "%SYSTEM_XML_PATH%" ^
    -deployment "%MAG_DEPLOYMENT%" ^
    -applicationType %MAG_APPLICATION_TYPE% ^
    -language C ^
    -d "%OUTPUT%" ^
    -replace
if errorlevel 1 exit /b 1

echo [2/5] Running rtiddsgen...
call "%RTIMEHOME%\bin\rtiddsgen.bat" ^
    -language C ^
    -create typefiles -micro -ppDisable ^
    "%SYSTEM_XML_PATH%" ^
    -d "%OUTPUT%"
if errorlevel 1 exit /b 1

echo [3/5] Flattening "%OUTPUT%"...
for %%O in ("%OUTPUT%") do set "OUTPUT_ABS=%%~fO"
for /f "delims=" %%F in ('dir /a:-d /b /s "%OUTPUT%"') do (
    if /I not "%%~dpF"=="%OUTPUT_ABS%\" move /Y "%%F" "%OUTPUT_ABS%\" >nul
)
for /f "delims=" %%D in ('dir /a:d /b /s "%OUTPUT%" ^| sort /r') do rmdir "%%D" 2>nul

echo [4/5] Copying "%SYSTEM_XML_PATH%" into "%OUTPUT%"...
copy /Y "%SYSTEM_XML_PATH%" "%OUTPUT_ABS%\" >nul

for %%F in ("%SYSTEM_XML_PATH%") do set "XML_NAME=%%~nF"
if /I "%IS_DPSE%"=="YES" (
    echo [5/5] DPSE Appgen patch...
    set "DPSE_TEMP_DIR=%OUTPUT%\dpse_appgen_temp"
    if not exist "!DPSE_TEMP_DIR!" mkdir "!DPSE_TEMP_DIR!"
    call "%RTIMEHOME%\bin\rtiddsmag.bat" ^
        -inputXml "%SYSTEM_XML_PATH%" ^
        -language C ^
        -d "!DPSE_TEMP_DIR!" ^
        -replace
    if errorlevel 1 exit /b 1
    python "%MAG_TEMPLATE_PATH%\patch_dpse_appgen.py" --xml-name %XML_NAME% --origin-dir "%OUTPUT%" --temp-dir "!DPSE_TEMP_DIR!" --takeall
    if errorlevel 1 exit /b 1
    rmdir /s /q "!DPSE_TEMP_DIR!"
)

echo Done. Generated files are under "%OUTPUT%".
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