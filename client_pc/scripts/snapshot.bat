@echo off
REM Windows batch script to capture a snapshot

SETLOCAL

SET SCRIPT_DIR=%~dp0
SET CLIENT_DIR=%SCRIPT_DIR%..

cd /d "%CLIENT_DIR%"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Capture snapshot
python modules\cli.py snapshot

ENDLOCAL
