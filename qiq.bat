@echo off

:: ---------------------------------------
:: A comprehensive Python management tool.
:: https://github.com/the-code-monk/qiq
:: ---------------------------------------

setlocal enabledelayedexpansion

:: Set current directory as QiQ path
set "QIQ_DIR=%~dp0"

set "arch=win32"
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" set "arch=amd64"
if defined PROCESSOR_ARCHITEW6432 set "arch=amd64"

:: REM Define the ESC character using a FOR loop and prompt command trick
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$E# & echo on & for %%b in (1) do rem"') do (
    set "ESC=%%a"
)

:: List installed python versions
if /I "%1"=="-envs" goto :ShowPythonEnvs
if /I "%1"=="--environments" goto :ShowPythonEnvs

:: Install python version
if /I "%1"=="-ipy" goto :InstallPython
if /I "%1"=="--install-python" goto :InstallPython

:: Uninstall python
if /I "%1"=="-upy" goto :UninstallPython
if /I "%1"=="--uninstall-python" goto :UninstallPython

:: Create virtual environment
if /I "%1"=="-venv" goto :CreateVirtualEnv
if /I "%1"=="--virtual-environment" goto :CreateVirtualEnv

:: Display help.
if "%1"=="-h" goto :Help
if "%1"=="--help" goto :Help

:: List explicitly install packages in current environment.
if "%1"=="-a" goto :ExecPython
if "%1"=="--about" goto :ExecPython

:: List explicitly install packages in current environment.
if "%1"=="-l" goto :ExecPython
if "%1"=="--list" goto :ExecPython

:: List explicitly install packages along with their dependencies in a tree format.
if "%1"=="-t" goto :ExecPython
if "%1"=="--tree" goto :ExecPython

:: List latest version of pckages.
if "%1"=="-d" goto :ExecPython
if "%1"=="--detail" goto :ExecPython

:: List all the projects using qiq
if "%1"=="-p" goto :ExecPython
if "%1"=="--projects" goto :ExecPython

:: Purge unwanted packages
if "%1"=="-c" goto :ExecPython
if "%1"=="--clean" goto :ExecPython

:: Create package importer from requirements.txt
if "%1"=="-r" goto :ExecPython
if "%1"=="--require" goto :ExecPython

:: Install packages in current environment.
if "%1"=="-i" goto :ExecPython
if "%1"=="--install" goto :ExecPython

:: UnInstall packages in current environment.
if "%1"=="-u" goto :ExecPython
if "%1"=="--uninstall" goto :ExecPython

:: Output requirements.txt
if "%1"=="-o" goto :ExecPython
if "%1"=="--output" goto :ExecPython

:: Display qiq version.
if "%1"=="-v" goto :ShowVersion
if "%1"=="--version" goto :ShowVersion

call :Display 31  "Error: No command found. %1"
echo Use -h or --help for help.
exit /b 1

:ShowPythonEnvs
echo.
echo Python Environments...
echo.
dir "%QIQ_DIR%python\python-win\python*.*" /ad /b
exit /b

:InstallPython
::net session >nul 2>&1
::if %errorlevel% neq 0 (
::    echo Requesting admin privileges...
::    powershell -Command "Start-Process cmd -ArgumentList '/c %~s0' -Verb RunAs"
::)

if defined QIQ_PYTHON_DIR (
    CALL :Display 31 "Please exit from the current virtual environment prompt in order to install python."
    goto :end
)

if "%2"=="" (
    echo Error: You must provide a python version to install.
    echo Example: qiq -ipy 3.13.5
    goto :end
)

set "folder=!QIQ_DIR!python\python-win\python-%2"
rem Check if python version is already installed
if exist "!folder!" (
    dir /b "!folder!" 2>nul | findstr . >nul
    if not errorlevel 1 (
        echo Notice: Python %2 is already installed.
        echo Uninstall it first using:
        echo qiq -upy %2
        exit /b
    ) else (
        rmdir /s /q "!folder!"
    )
)

:: Create python file name from 2nd argument.
set "pyexe=python-%2-%arch%.exe"
:: Example https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
set "url=https://www.python.org/ftp/python/%2/!pyexe!"

:: Check if python exe exists on the python server for the version
for /f %%A in ('curl -s -o NUL -w "%%{http_code}" "!url!"') do set "status=%%A"

if NOT "!status!"=="200" (
    echo Installer for Python %2 does not exists on python server.
    echo Here is the list of all available python versions.
    echo https://www.python.org/ftp/python/
    exit /b 1
)

:: Create python installation folder
mkdir "!folder!"

CALL :Display 32 "Downloading !pyexe!..."
curl -L "!url!" -o "%folder%\!pyexe!"

CALL :Display 32 "Installing !folder!\!pyexe!"
CALL :Display 32 "Please wait..."

::Perform silent installation of python
"!folder!\!pyexe!" /quiet InstallAllUsers=0 Include_launcher=0 Include_test=0 TargetDir="!folder!" PrependPath=0

:: Don't Delete python installer file,
:: It's required for uninstallation.

:: Upgrading pip
CALL :Display 32 "Upgrading pip..."
!folder!\python.exe -m pip install --upgrade pip --no-warn-script-location

:: Install minimal packages required for qiq
CALL :Display 32 "Installing minimal packages required for qiq..."
!folder!\python.exe -m pip install -r %QIQ_DIR%\requirements.txt --no-warn-script-location

:: Create qiqpy console executable that can be used as python
!folder!\python.exe %QIQ_DIR%\src\qiq_console.py

:: Create required qiq directories in python installation
CALL :Display 32 "Configuring qiq..."
mkdir "!folder!\qiq\qiq-cache"
mkdir "!folder!\qiq\qiq-packages"
mkdir "!folder!\qiq\qiq-config"

rem Create qiq.pth file and copy to Lib/site-packages.
rem This will automatically imports all the packages
rem in .qiq/qiq.json file 
set "qiq_pth_file=!folder!\Lib\site-packages\qiq.pth"
(
    echo !QIQ_DIR!src
) > "%qiq_pth_file%"

CALL :Display 32 "Python %2 successfully installed."
exit /b

:UninstallPython
if defined QIQ_PYTHON_DIR (
    CALL :Display 31 "Please exit from the current virtual environment prompt in order to install python."
    goto :end
)
if "%2"=="" (
    echo Error: You must provide a python version to Uninstall.
    echo Example: qiq -upy 3.13.5
    goto :end
)
:: Create python file name from 2nd argument.
set "pyexe=python-%2-%arch%.exe"
set "folder=!QIQ_DIR!python\python-win\python-%2"
rem Check if python version is already installed
if exist "!folder!" (
    echo Found Python %2
    rem Ask for confirmation
    set /p "choice=Are you sure you want to uninstall Python %2? (y/n)"
    if /I "!choice!"=="n" goto :end
    rem Check if the Python installer exists
    if exist "!folder!\!pyexe!" (
        echo Uninstalling. Please wait...
        "!folder!\!pyexe!" /quiet /uninstall
        rmdir /s /q "!folder!"
    ) else (
        CALL :Display 31 "Error: Unable to uninstall. Missing python installer !pyexe!"
        exit /b 1
    )
    echo Done
)
exit /b

:CreateVirtualEnv
if "%2"=="" (
    echo Error: You must provide an installed python version for the virtual environment creation.
    echo Example: qiq -venv 3.13.5
    goto :end
)

if defined QIQ_PYTHON_DIR (
    CALL :Display 31 "Please exit from the current virtual environment prompt in order to create a new one."
    goto :end
)

rem Check if python version is already installed
set "folder=%QIQ_DIR%\python\python-win\python-%2"
if not exist "!folder!" (
    CALL :Display 31 "Error: Python %2 is not installed."
    goto :end
)

:: Check if there is already a qiq venv present in the current directory
if exist ".qiq\activate.bat" (
    echo It seems there is already a qiq virtual environment installed in the current directory.
    set /p "choice=Are you sure you want to overwrite the existing environment? (y/n)"
    if /I "!choice!"=="n" goto :end
)

:: Copy virtual environment scripts
goto :CopyScripts

exit /b

:ExecPython
call :CheckPrompt
if errorlevel 1 exit /b 1
call python %~dp0src\qiq_main.py %*
exit /b 0

:: Copy virtual environment scripts in .qiq directory in current folder
:CopyScripts
set "qiq_venv_dir=%cd%\.qiq"
if not exist "%qiq_venv_dir%" mkdir "%qiq_venv_dir%"

set "activate_batch=%QIQ_DIR%\scripts\activate.bat"
set "deactivate_batch=%QIQ_DIR%\scripts\deactivate.bat"
set "activate_ps=%QIQ_DIR%\scripts\activate.ps1"
set "deactivate_ps=%QIQ_DIR%\scripts\deactivate.ps1"
set "qiq_ini=%QIQ_DIR%\scripts\qiq.ini"

copy /Y "%activate_batch%" "%qiq_venv_dir%" >nul
copy /Y "%deactivate_batch%" "%qiq_venv_dir%" >nul
copy /Y "%activate_ps%" "%qiq_venv_dir%" >nul
copy /Y "%deactivate_ps%" "%qiq_venv_dir%" >nul
rem Copy if doesn't exists. Keep existing settings.
IF NOT EXIST "!qiq_venv_dir!\qiq.ini" (
    copy /Y "%qiq_ini%" "%qiq_venv_dir%" >nul
)

:: Replace current environment path in activation script
powershell -Command "(Get-Content '%qiq_venv_dir%\activate.bat') -replace 'XXXXX','%folder%' | Set-Content '%qiq_venv_dir%\activate.bat'"
powershell -Command "(Get-Content '%qiq_venv_dir%\activate.ps1') -replace 'XXXXX','%folder%' | Set-Content '%qiq_venv_dir%\activate.ps1'"

CALL :Display 32 "Virtual environment scripts copied."

rem execute virtual environment based on user's choice
set /p "execenv=Would you like to enter in the virtual environment? (y/n)"
if /I "!execenv!"=="y" (
    endlocal
    call "%qiq_venv_dir%\activate.bat"
)

exit /b

:: Check if virtual environment prompt is active
:CheckPrompt
if not defined QIQ_PYTHON_DIR (
    call :Display 31 "Error: Virtual Environment is not active."
    exit /b 1
)
exit /b

:: A simple function that displays text with given color
:: Usage: CALL :Display 32 "Your message"
:Display
echo %ESC%[%~1m%~2%ESC%[0m
exit /b

:ShowVersion
:: Get qiq version
set /p qiqversion=<%~dp0VERSION
echo.
echo Version : %qiqversion%
echo.
exit /b

:Help
if defined WT_SESSION (
    chcp 65001 >nul
    powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; (Get-Content '%~dp0help\help-utf8.txt' -Raw -Encoding UTF8) -replace '\\033', [char]27"
) else (
    powershell -NoProfile -Command "(Get-Content '%~dp0help\help.txt' -Raw -Encoding UTF8)"
)
:end