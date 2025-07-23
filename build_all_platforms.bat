@echo off
echo AEC File Manager - Multi-Platform Build Script
echo ===============================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Installing build dependencies...
pip install -r requirements-build.txt

echo.
echo Building portable version...
python build_portable.py

echo.
echo Building lightweight version...
python create_lightweight_portable.py

echo.
echo Creating distribution package...
if exist "AEC-File-Manager-Distribution" rmdir /s /q "AEC-File-Manager-Distribution"
mkdir "AEC-File-Manager-Distribution"

REM Copy portable versions
if exist "AEC-File-Manager-Portable" (
    xcopy /e /i "AEC-File-Manager-Portable" "AEC-File-Manager-Distribution\Portable-Full"
)

if exist "dist\AEC-File-Manager-Lite" (
    xcopy /e /i "dist\AEC-File-Manager-Lite" "AEC-File-Manager-Distribution\Portable-Lite"
)

REM Create quick start guide
echo Creating Quick Start Guide... > "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo. >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo AEC File Manager - Quick Start >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo ================================ >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo. >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo Choose your version: >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo. >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo 1. Full Version (Portable-Full): >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Complete AI features >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Larger file size (~500MB+) >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Run: start_aec_manager.bat >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo. >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo 2. Lite Version (Portable-Lite): >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Basic file management >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Smaller file size (~50MB) >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo    - Run: AEC-File-Manager-Lite.exe >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo. >> "AEC-File-Manager-Distribution\QUICKSTART.txt"
echo No Python installation required for either version! >> "AEC-File-Manager-Distribution\QUICKSTART.txt"

echo.
echo ===============================================
echo Build Complete!
echo ===============================================
echo.
echo Distribution package created in:
echo AEC-File-Manager-Distribution\
echo.
echo To distribute:
echo 1. Zip the entire 'AEC-File-Manager-Distribution' folder
echo 2. Users can extract and run without installing anything
echo.
pause