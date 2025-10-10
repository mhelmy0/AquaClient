@echo off
REM Windows batch script to start the RTMP client and recorder

SETLOCAL

SET SCRIPT_DIR=%~dp0
SET CLIENT_DIR=%SCRIPT_DIR%..

echo Starting RTMP client...

cd /d "%CLIENT_DIR%"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the client
python modules\cli.py start

ENDLOCAL
