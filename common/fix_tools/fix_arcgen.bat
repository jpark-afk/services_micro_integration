@echo off
setlocal
if "%~1"=="" (
    python "%~dp0fix_arcgen.py" --source-dir "%~dp0arcgen_fix_499" --target-home "C:\RTI\rti_connext_drive-4.0.0\rti_connext_dds-7.3.1"
    exit /b %ERRORLEVEL%
)
python "%~dp0fix_arcgen.py" %*
exit /b %ERRORLEVEL%
