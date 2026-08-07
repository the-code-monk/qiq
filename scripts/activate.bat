@echo off
REM ====================================================
REM Activate Python environment
REM ====================================================

REM Check if virtual env is already active
if defined QIQ_PYTHON_DIR if not "%QIQ_PYTHON_DIR%"=="" (
    echo Virtual environment is already active.
    exit /b 1
)

REM Directory where Python is installed
set QIQ_PYTHON_DIR=XXXXX

if not exist "%QIQ_PYTHON_DIR%\python.exe" (
    echo python.exe not found in %QIQ_PYTHON_DIR%
    exit /b 1
)

REM Save original environment variables if not already saved
if "%ORIG_PATH%"=="" set "ORIG_PATH=%PATH%"
if "%ORIG_PROMPT%"=="" set "ORIG_PROMPT=%PROMPT%"

REM Update PATH
set "PATH=%QIQ_PYTHON_DIR%;%QIQ_PYTHON_DIR%\Scripts;%PATH%"

REM Extract last folder name from QIQ_PYTHON_DIR for prompt
for %%I in ("%QIQ_PYTHON_DIR%") do set "PYTHON_PROMPT=%%~nI"

set "USE_COLOR="
if defined WT_SESSION set "USE_COLOR=1"
if defined TERM set "USE_COLOR=1"

rem capture real escape character
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

if defined USE_COLOR (
    rem print with ANSI colors
    prompt %ESC%[1;32m^(QiQ^)%ESC%[0m%ESC%[1;34m^(%PYTHON_PROMPT%^)%ESC%[0m $P$G
) else (
    prompt ^(QiQ^)^(%PYTHON_PROMPT%^) $P$G
)

echo Python environment configured
echo Python location: %QIQ_PYTHON_DIR%

python --version