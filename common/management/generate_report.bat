@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "TEMPLATES_DIR=%SCRIPT_DIR%..\templates"
set "PYTHON_EXE=python"

"%PYTHON_EXE%" "%TEMPLATES_DIR%\generate_workaround_report.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo Failed to generate workaround report. Exit code: %EXIT_CODE%
    exit /b %EXIT_CODE%
)

echo Workaround report generated successfully.
exit /b 0
