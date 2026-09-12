@echo off
setlocal

cd /d "%~dp0"

if "%~1"=="" (
    python .\deploy_from_manifest.py --manifest .\deploy-manifest.yaml
) else (
    python .\deploy_from_manifest.py --manifest "%~1"
)

exit /b %ERRORLEVEL%
