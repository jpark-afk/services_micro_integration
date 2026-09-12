@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    echo Usage: %~nx0 ^<project-template-values.yaml^>
    exit /b 1
)

python "%SCRIPT_DIR%render_project_scripts.py" %* --force
exit /b %ERRORLEVEL%