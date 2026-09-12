@echo off
REM RTI INTERNAL TEMPORARY WORKAROUND NOTICE
REM Temporary workaround until an official RTI patch is released.
REM Baseline version: Micro430er738.
REM Not officially supported by RTI Technical Support.
REM Must NOT be applied directly to controller mass-production development.
REM See README.md for details.

setlocal
call :print_notice

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%code_patch.py"

if not exist "%PY_SCRIPT%" (
    echo ERROR: code_patch.py not found: "%PY_SCRIPT%"
    exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%PY_SCRIPT%" %*
    exit /b %ERRORLEVEL%
)

python "%PY_SCRIPT%" %*
exit /b %ERRORLEVEL%

[RTI NOTICE] INTERNAL TEMPORARY WORKAROUND
[RTI NOTICE] Temporary workaround until an official RTI patch is released.
[RTI NOTICE] Baseline version: Micro430er738.
[RTI NOTICE] Not officially supported by RTI Technical Support.
[RTI NOTICE] Must NOT be applied directly to controller mass-production development.
[RTI NOTICE] See README.md for details.
