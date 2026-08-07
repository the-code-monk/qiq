@echo off
:: QiQ install.bat
:: Install script for Windows 10 or higher

:: Get qiq version
set /p qiqversion=<%~dp0VERSION

:: Install QiQ
echo "Installing QiQ %qiqversion%..."

:: Add this path to system/user path
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\qiqtopath.ps1" -AddPath %~dp0

echo Done
