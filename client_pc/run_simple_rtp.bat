@echo off
REM Simple RTP GUI Launcher
echo ========================================
echo   Simple RTP Stream Viewer
echo   Starting application...
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Check FFplay
ffplay -version >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFplay not found
    echo Please install FFmpeg: https://ffmpeg.org/download.html
    echo.
    pause
)

REM Create directories
if not exist "logs" mkdir "logs"

echo Launching Simple RTP Viewer...
echo.

python simple_rtp_gui.py

if errorlevel 1 (
    echo.
    echo Application exited with error
    pause
)
