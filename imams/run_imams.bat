@echo off
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error starting IMAMS. Make sure Python and dependencies are installed.
    echo Run install.bat first.
    pause
)
