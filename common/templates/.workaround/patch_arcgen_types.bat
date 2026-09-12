@echo off
setlocal

REM Creates a patched DDS XML copy for rtiarcgen type-name compatibility.
REM Usage:
REM   patch_arcgen_types.bat [input_xml] [output_xml]

set "INPUT_XML=%~1"
set "OUTPUT_XML=%~2"

if "%INPUT_XML%"=="" set "INPUT_XML=%~dp0..\..\slcorp04\test_system.xml"
if "%OUTPUT_XML%"=="" set "OUTPUT_XML=%~dp0..\..\slcorp04\test_system.xml"

if not exist "%INPUT_XML%" (
    echo ERROR: input XML not found: "%INPUT_XML%"
    exit /b 1
)

if "%OUTPUT_XML%"=="" (
    python "%~dp0patch_arcgen_types.py" --xml "%INPUT_XML%"
) else (
    python "%~dp0patch_arcgen_types.py" --xml "%INPUT_XML%" --out "%OUTPUT_XML%"
)

if errorlevel 1 (
    echo ERROR: arcgen type patch failed.
    exit /b 1
)

endlocal
exit /b 0