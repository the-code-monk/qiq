@echo off
REM ====================================================
REM Deactivate Python environment
REM ====================================================

REM Check if ORIG_PATH exists
if "%ORIG_PATH%"=="" (
    echo No Python environment is active.
    exit /b 0
)

REM Restore original PATH
set "PATH=%ORIG_PATH%"

REM Restore original prompt
set "PROMPT=%ORIG_PROMPT%"

REM Unset Python-related variables
set "QIQ_PYTHON_DIR="
set "PYTHON_PROMPT="
set "ORIG_PATH="
set "ORIG_PROMPT="

echo Python environment deactivated.