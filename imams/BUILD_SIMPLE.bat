@echo off
echo.
echo ============================================================
echo   IMAMS - Quick Build (Portable EXE, no installer)
echo ============================================================
echo.

python --version >nul 2>&1 || (echo Python not found. Install from python.org && pause && exit /b 1)

echo Installing dependencies...
python -m pip install pyinstaller -r requirements.txt --quiet

echo.
echo Building EXE...
python -m PyInstaller --onedir --windowed --name IMAMS ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL.ImageDraw ^
    --hidden-import openpyxl ^
    --hidden-import reportlab ^
    --hidden-import reportlab.lib ^
    --hidden-import reportlab.lib.pagesizes ^
    --hidden-import reportlab.platypus ^
    --hidden-import dateutil ^
    --hidden-import dateutil.relativedelta ^
    --hidden-import babel ^
    --hidden-import babel.numbers ^
    --clean --noconfirm main.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================================
    echo   DONE!
    echo.
    echo   Your portable application is in:  dist\IMAMS\
    echo   Run it by double-clicking:        dist\IMAMS\IMAMS.exe
    echo.
    echo   To share with others: zip the entire dist\IMAMS\ folder.
    echo   The recipient just extracts and runs IMAMS.exe directly.
    echo   No Python needed on their machine.
    echo ============================================================
) else (
    echo.
    echo Build failed. Check the output above for errors.
)
echo.
pause
