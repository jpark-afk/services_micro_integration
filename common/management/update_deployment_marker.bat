@echo off
setlocal

cd /d "%~dp0"
python .\update_deployment_marker.py --manifest .\deploy-manifest.yaml

exit /b %ERRORLEVEL%
