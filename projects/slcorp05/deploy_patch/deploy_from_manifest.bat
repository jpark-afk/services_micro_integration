@echo off
setlocal

cd /d "%~dp0"

if "%~1"=="" (
    python ..\..\..\common\management\deploy_from_manifest.py --manifest .\deploy-manifest.yaml
) else (
    python ..\..\..\common\management\deploy_from_manifest.py --manifest "%~1"
)

exit /b %ERRORLEVEL%
