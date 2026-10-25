@echo off
chcp 65001 >nul
title MS Media Player

echo ============================================
echo MS Media Player - Launcher
echo ============================================
echo.

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.9+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if VLC is installed
set "VLC_FOUND=0"
if exist "C:\Program Files\VideoLAN\VLC\vlc.exe" (
    set "VLC_FOUND=1"
    set "PATH=C:\Program Files\VideoLAN\VLC;%PATH%"
) else if exist "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" (
    set "VLC_FOUND=1"
    set "PATH=C:\Program Files (x86)\VideoLAN\VLC;%PATH%"
) else (
    vlc --version >nul 2>&1
    if not errorlevel 1 set "VLC_FOUND=1"
)

if "%VLC_FOUND%"=="0" (
    echo WARNING: VLC Media Player not found!
    echo Please install VLC from https://www.videolan.org/vlc/
    echo The application may not work without VLC.
    echo.
)

REM Check and install dependencies if needed
python -c "import PySide6, vlc, platformdirs" >nul 2>&1
if errorlevel 1 (
    echo Installing/updating dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting MS Media Player...
echo --------------------------------------------

REM Run the application
python run.py

REM Pause on error so user can see the message
if errorlevel 1 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    pause
)