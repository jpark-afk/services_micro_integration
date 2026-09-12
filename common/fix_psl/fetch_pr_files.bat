@echo off
setlocal
if "%~1"=="" (
	python "%~dp0fetch_pr_files.py" task/PLATFORMS-6094 --base-ref develop/connextmicro
	exit /b %ERRORLEVEL%
)
python "%~dp0fetch_pr_files.py" %*
exit /b %ERRORLEVEL%