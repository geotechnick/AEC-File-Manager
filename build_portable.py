"""
AEC File Manager - Portable Build Script
Creates a standalone executable that runs without Python installation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def create_spec_file():
    """Create PyInstaller spec file for customized build"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui_app.py', '.'),
        ('agentic_ai.py', '.'),
        ('llm_integration.py', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'plotly',
        'PyPDF2',
        'docx',
        'openpyxl',
        'sentence_transformers',
        'langchain',
        'transformers',
        'torch',
        'dotenv',
        'sqlite3',
        'pathlib',
        'hashlib',
        'datetime',
        'json',
        'shutil',
        'typing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AEC-File-Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AEC-File-Manager'
)
"""
    
    with open('aec_manager.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def build_executable():
    """Build the standalone executable"""
    print("Building portable executable...")
    print("This may take several minutes...")
    
    try:
        # Build using spec file
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'aec_manager.spec'
        ])
        
        print("✅ Executable built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_portable_package():
    """Create complete portable package"""
    print("Creating portable package...")
    
    # Create portable directory
    portable_dir = Path('AEC-File-Manager-Portable')
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir()
    
    # Copy executable files
    dist_dir = Path('dist/AEC-File-Manager')
    if dist_dir.exists():
        shutil.copytree(dist_dir, portable_dir / 'app')
    
    # Create launcher scripts
    create_launcher_scripts(portable_dir)
    
    # Copy essential files
    essential_files = ['README.md', 'LICENSE']
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, portable_dir)
    
    # Create default configuration
    create_portable_config(portable_dir)
    
    print(f"✅ Portable package created in: {portable_dir}")

def create_launcher_scripts(portable_dir):
    """Create cross-platform launcher scripts"""
    
    # Windows batch file
    bat_content = """@echo off
echo Starting AEC File Manager...
cd /d "%~dp0app"
start "" "AEC-File-Manager.exe"
echo AEC File Manager is starting in your browser...
echo Press any key to close this window.
pause >nul
"""
    
    with open(portable_dir / 'start_aec_manager.bat', 'w') as f:
        f.write(bat_content)
    
    # Linux/Mac shell script
    sh_content = """#!/bin/bash
echo "Starting AEC File Manager..."
cd "$(dirname "$0")/app"
./AEC-File-Manager &
echo "AEC File Manager is starting in your browser..."
echo "Press Enter to continue..."
read
"""
    
    with open(portable_dir / 'start_aec_manager.sh', 'w') as f:
        f.write(sh_content)
    
    # Make shell script executable
    os.chmod(portable_dir / 'start_aec_manager.sh', 0o755)
    
    print("✅ Created launcher scripts")

def create_portable_config(portable_dir):
    """Create portable configuration files"""
    
    # Create config directory
    config_dir = portable_dir / 'config'
    config_dir.mkdir()
    
    # Create portable .env file
    env_content = """# AEC File Manager - Portable Configuration
USE_LOCAL_LLM=false
STREAMLIT_PORT=8501
STREAMLIT_HOST=localhost
STREAMLIT_HEADLESS=false
DEBUG_MODE=false

# Portable mode settings
PORTABLE_MODE=true
DATA_DIR=./data
MODELS_DIR=./models
TEMP_DIR=./temp
"""
    
    with open(config_dir / '.env', 'w') as f:
        f.write(env_content)
    
    # Create directories
    (portable_dir / 'data').mkdir()
    (portable_dir / 'models').mkdir()
    (portable_dir / 'temp').mkdir()
    
    # Create portable readme
    readme_content = """# AEC File Manager - Portable Version

This is a portable version of AEC File Manager that runs without installing Python or dependencies.

## Quick Start

### Windows:
Double-click `start_aec_manager.bat`

### Linux/Mac:
Run `./start_aec_manager.sh` in terminal

## Features

- Complete file management for AEC projects
- AI-powered document analysis
- No installation required
- All data stored locally in this folder

## Configuration

Edit `config/.env` to customize settings.

## Troubleshooting

If the application doesn't start:
1. Check that you have sufficient disk space
2. Temporarily disable antivirus software
3. Run as administrator (Windows) or with sudo (Linux/Mac)

For support, visit: https://github.com/your-repo/AEC-File-Manager
"""
    
    with open(portable_dir / 'README-Portable.txt', 'w') as f:
        f.write(readme_content)
    
    print("✅ Created portable configuration")

def cleanup_build_files():
    """Clean up build artifacts"""
    cleanup_dirs = ['build', 'dist', '__pycache__']
    cleanup_files = ['aec_manager.spec']
    
    for dir_name in cleanup_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
    
    for file_name in cleanup_files:
        if Path(file_name).exists():
            os.remove(file_name)
    
    print("✅ Cleaned up build files")

def main():
    """Main build function"""
    print("🏗️  AEC File Manager - Portable Build")
    print("=" * 50)
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("❌ Failed to install PyInstaller")
        return False
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        return False
    
    # Create portable package
    create_portable_package()
    
    # Cleanup
    cleanup_build_files()
    
    print("\n" + "=" * 50)
    print("🎉 Portable Build Complete!")
    print("=" * 50)
    print("Find your portable AEC File Manager in:")
    print("📁 AEC-File-Manager-Portable/")
    print("\nTo distribute:")
    print("1. Zip the entire 'AEC-File-Manager-Portable' folder")
    print("2. Users can extract and run without any installation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)