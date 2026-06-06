@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   AAAIS - Windows Installer Builder
echo   AGV ASSESSMENT ADVANCE INTIMATION SYSTEM
echo ============================================================
echo.

:: ─── Step 0: Check Python ───────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.10+ from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo [OK] Found %PYVER%

:: ─── Step 1: Upgrade pip & install build tools ──────────────
echo.
echo [1/5] Installing build dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install pyinstaller --quiet
python -m pip install -r requirements.txt --quiet
echo [OK] Dependencies installed.

:: ─── Step 2: Create assets folder if missing ────────────────
if not exist assets mkdir assets

:: Create a minimal icon if none exists
if not exist assets\icon.ico (
    echo [INFO] No icon found. Creating placeholder icon...
    python -c "
from PIL import Image, ImageDraw
import os

img = Image.new('RGBA', (256, 256), (15, 52, 96, 255))
draw = ImageDraw.Draw(img)
draw.ellipse([20, 20, 236, 236], fill=(241, 196, 15, 255))
draw.text((128, 110), 'I', fill=(15, 52, 96, 255))

ico_path = os.path.join('assets', 'icon.ico')
img.save(ico_path, format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
print('Icon created.')
" 2>nul || echo [WARN] Could not create icon, continuing without it.
)

:: ─── Step 3: Build EXE with PyInstaller ─────────────────────
echo.
echo [2/5] Building standalone EXE (this takes 2-5 minutes)...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

python -m PyInstaller IMAMS.spec --clean --noconfirm

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed. See output above for details.
    pause
    exit /b 1
)
echo [OK] EXE built successfully in dist\IMAMS\

:: ─── Step 4: Copy database placeholder ─────────────────────
echo.
echo [3/5] Preparing application files...
if not exist dist\IMAMS\data mkdir dist\IMAMS\data
echo [OK] Files prepared.

:: ─── Step 5: Try Inno Setup (optional) ─────────────────────
echo.
echo [4/5] Checking for Inno Setup...

set INNO_PATH=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set INNO_PATH="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

if not %INNO_PATH%=="" (
    echo [OK] Inno Setup found. Building installer...
    if not exist output mkdir output
    %INNO_PATH% installer.iss
    if %ERRORLEVEL% equ 0 (
        echo.
        echo ============================================================
        echo   SUCCESS! Windows Installer created:
        echo   output\IMAMS_Setup.exe
        echo ============================================================
    ) else (
        echo [WARN] Inno Setup failed. Falling back to portable zip.
        goto :portable
    )
) else (
    echo [INFO] Inno Setup not found. Creating portable ZIP instead.
    echo        Download Inno Setup from https://jrsoftware.org/isdl.php
    echo        to build a proper .exe installer next time.
    goto :portable
)
goto :done

:: ─── Fallback: Portable ZIP ─────────────────────────────────
:portable
echo.
echo [5/5] Creating portable ZIP archive...
python -c "
import zipfile, os, sys

src = 'dist\\IMAMS'
if not os.path.isdir(src):
    print('ERROR: dist\\IMAMS not found')
    sys.exit(1)

os.makedirs('output', exist_ok=True)
zip_path = 'output\\IMAMS_Portable.zip'

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        for f in files:
            fp = os.path.join(root, f)
            arcname = os.path.relpath(fp, 'dist')
            zf.write(fp, arcname)

size_mb = os.path.getsize(zip_path) / 1024 / 1024
print(f'Created: {zip_path} ({size_mb:.1f} MB)')
"
echo.
echo ============================================================
echo   SUCCESS! Portable ZIP created:
echo   output\IMAMS_Portable.zip
echo.
echo   To distribute: extract the ZIP and run IMAMS\IMAMS.exe
echo   No Python installation required on the target machine.
echo ============================================================

:done
echo.
echo Build complete. Press any key to exit.
pause >nul
