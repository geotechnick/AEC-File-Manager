#!/usr/bin/env python3
"""
Build script to create standalone executable versions of AEC File Manager
that require no Python installation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is available."""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def build_executable():
    """Build the standalone executable."""
    print("🔨 Building standalone AEC File Manager...")
    
    # Ensure PyInstaller is available
    check_pyinstaller()
    
    # Build command
    build_cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window (for GUI apps)
        '--add-data', 'src;src',        # Include source files
        '--add-data', 'config;config',  # Include config files
        '--name', 'AEC-File-Manager',   # Executable name
        '--icon', 'icon.ico',           # Icon (if exists)
        '--clean',                      # Clean build
        'aec_streamlined_cli.py'        # Main script
    ]
    
    # Remove --icon if no icon file exists
    if not os.path.exists('icon.ico'):
        build_cmd = [cmd for cmd in build_cmd if cmd != '--icon' and cmd != 'icon.ico']
    
    try:
        subprocess.check_call(build_cmd)
        print("✅ Executable built successfully!")
        print("📁 Find it in: dist/AEC-File-Manager.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_portable_package():
    """Create a complete portable package."""
    print("📦 Creating portable package...")
    
    # Create package directory
    package_dir = Path("AEC-File-Manager-Portable")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    exe_path = Path("dist/AEC-File-Manager.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, package_dir / "AEC-File-Manager.exe")
        print("✅ Executable copied")
    
    # Copy documentation
    docs_to_copy = [
        "EASY_INSTALL_GUIDE.md",
        "QUICK_START.md", 
        "README.md",
        "LICENSE"
    ]
    
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, package_dir / doc)
    
    # Create batch scripts for easy access
    create_batch_scripts(package_dir)
    
    # Create installer batch file
    create_installer_batch(package_dir)
    
    print(f"✅ Portable package created: {package_dir}")
    return True

def create_batch_scripts(package_dir):
    """Create simple batch scripts for common operations."""
    
    # Setup Project batch script
    setup_script = """@echo off
echo ===============================================
echo      AEC File Manager - Setup Project
echo ===============================================
echo.
set /p project_path="Enter your project folder path: "
if "%project_path%"=="" (
    echo Using current directory...
    set project_path=%cd%
)

cd /d "%project_path%"
AEC-File-Manager.exe init
echo.
echo Project setup complete!
pause
"""
    
    with open(package_dir / "Setup-Project.bat", 'w') as f:
        f.write(setup_script)
    
    # Scan Files batch script
    scan_script = """@echo off
echo ===============================================
echo       AEC File Manager - Scan Files
echo ===============================================
echo.
set /p project_path="Enter your project folder path (or press Enter for current): "
if "%project_path%"=="" (
    set project_path=%cd%
)

cd /d "%project_path%"
AEC-File-Manager.exe scan
echo.
echo Scan complete!
pause
"""
    
    with open(package_dir / "Scan-Files.bat", 'w') as f:
        f.write(scan_script)
    
    # Generate Report batch script
    report_script = """@echo off
echo ===============================================
echo     AEC File Manager - Generate Report
echo ===============================================
echo.
set /p project_path="Enter your project folder path (or press Enter for current): "
if "%project_path%"=="" (
    set project_path=%cd%
)

cd /d "%project_path%"
AEC-File-Manager.exe report
echo.
echo Report generated!
echo Check for .html file in your project folder
pause
"""
    
    with open(package_dir / "Generate-Report.bat", 'w') as f:
        f.write(report_script)

def create_installer_batch(package_dir):
    """Create a simple installer that just copies files."""
    installer_script = """@echo off
echo ===============================================
echo    AEC File Manager - Easy Installation
echo ===============================================
echo.
echo This will copy AEC File Manager to your system.
echo You can run it from anywhere after installation.
echo.
pause

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\\AEC-File-Manager
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
copy "AEC-File-Manager.exe" "%INSTALL_DIR%\\"
copy "*.bat" "%INSTALL_DIR%\\"
copy "*.md" "%INSTALL_DIR%\\"

echo.
echo ✅ Installation complete!
echo.
echo You can now run AEC File Manager from:
echo %INSTALL_DIR%
echo.
echo Or use the batch files for easy access:
echo - Setup-Project.bat
echo - Scan-Files.bat  
echo - Generate-Report.bat
echo.
pause
"""
    
    with open(package_dir / "INSTALL.bat", 'w') as f:
        f.write(installer_script)

def main():
    """Main build process."""
    print("🏗️ AEC File Manager - Standalone Build Process")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('aec_streamlined_cli.py'):
        print("❌ Error: Run this script from the AEC-File-Manager directory")
        sys.exit(1)
    
    # Build executable
    if build_executable():
        create_portable_package()
        print("\n🎉 Build complete!")
        print("\nWhat you now have:")
        print("📁 AEC-File-Manager-Portable/ - Complete portable package")
        print("   ├── AEC-File-Manager.exe - Main program (no Python needed!)")
        print("   ├── Setup-Project.bat - Easy project setup")
        print("   ├── Scan-Files.bat - Easy file scanning")
        print("   ├── Generate-Report.bat - Easy report generation")
        print("   ├── INSTALL.bat - System installer")
        print("   └── Documentation files")
        print("\nUsers can now:")
        print("1. Download the portable folder")
        print("2. Double-click any .bat file to get started")
        print("3. No Python installation required!")
    else:
        print("❌ Build failed. Check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main()