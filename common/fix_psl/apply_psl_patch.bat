@echo off
setlocal
if "%~1"=="" (
	python "%~dp0apply_psl_patch.py" --repository "%~dp0repository" --psl-home "%~dp0psl_fix_6094"
	exit /b %ERRORLEVEL%
)
python "%~dp0apply_psl_patch.py" %*
exit /b %ERRORLEVEL%