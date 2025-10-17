@echo off
REM Aqua RTP Monitor - Quick Start Script
REM This script launches the RTP GUI application

echo ========================================
echo   Aqua RTP Stream Monitor
echo   Starting application...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg is not installed or not in PATH
    echo FFmpeg is required for RTP streaming and recording
    echo.
    echo Please install FFmpeg and add to PATH:
    echo 1. Download from https://ffmpeg.org/download.html
    echo 2. Extract to C:\ffmpeg
    echo 3. Add C:\ffmpeg\bin to PATH
    echo.
    pause
)

REM Check if config file exists
if not exist "config.yaml" (
    echo ERROR: config.yaml not found
    echo Please ensure you're running from the client_pc directory
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "records\videos" mkdir "records\videos"
if not exist "records\snapshots" mkdir "records\snapshots"
if not exist "logs" mkdir "logs"

echo.
echo Launching RTP GUI...
echo.

REM Run the application
python rtp_gui.py

REM If Python script exits with error
if errorlevel 1 (
    echo.
    echo ========================================
    echo   Application exited with error
    echo   Check logs\client.log for details
    echo ========================================
    pause
)
