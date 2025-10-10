@echo off
REM Launcher script for Aqua Stream Monitor GUI

cd /d "%~dp0\.."

echo Starting Aqua Stream Monitor GUI...

REM Activate virtual environment
call venv\Scripts\activate

REM Launch GUI
python -m modules.gui_launcher

REM Deactivate virtual environment on exit
deactivate

pause
