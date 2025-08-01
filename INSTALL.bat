@echo off
echo ===============================================
echo    AEC File Manager - One-Click Installation
echo ===============================================
echo.
echo This will install the AEC File Manager on your computer.
echo Please wait while we set everything up...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please follow these steps:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download and install Python
    echo 3. Make sure to check "Add Python to PATH" during installation
    echo 4. Restart your computer
    echo 5. Run this installer again
    echo.
    pause
    exit /b 1
)

echo ✓ Python is installed
echo.

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install required packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo ✓ Required packages installed
echo.

REM Install the AEC File Manager
echo Installing AEC File Manager...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install AEC File Manager
    pause
    exit /b 1
)

echo ✓ AEC File Manager installed
echo.

REM Test the installation
echo Testing installation...
aec status
if errorlevel 1 (
    echo WARNING: Installation may not be complete
    echo Try running 'python -m aec_streamlined_cli status' instead
) else (
    echo ✓ Installation successful!
)

echo.
echo ===============================================
echo           Installation Complete!
echo ===============================================
echo.
echo You can now use AEC File Manager with these commands:
echo.
echo   aec              - Set up a new project (auto-detects settings)
echo   aec scan         - Scan your project files
echo   aec report       - Generate a project report
echo   aec status       - Check system status
echo.
echo For detailed instructions, see EASY_INSTALL_GUIDE.md
echo.
echo Need help? Visit: https://github.com/geotechnick/AEC-File-Manager/issues
echo.
pause