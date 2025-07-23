"""
AEC File Manager - Lightweight Portable Version
Creates a minimal portable version without heavy AI dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_lightweight_spec():
    """Create PyInstaller spec for lightweight version"""
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
    excludes=[
        'torch',
        'transformers', 
        'sentence_transformers',
        'langchain',
        'numpy.random._pickle',
        'IPython',
        'matplotlib'
    ],
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
    name='AEC-File-Manager-Lite',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AEC-File-Manager-Lite'
)
"""
    
    with open('aec_manager_lite.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created lightweight spec file")

def modify_for_lightweight():
    """Create lightweight versions of the main files"""
    
    # Read original files and create lightweight versions
    lightweight_dir = Path('lightweight_temp')
    lightweight_dir.mkdir(exist_ok=True)
    
    # Copy and modify agentic_ai.py to disable heavy AI features
    with open('agentic_ai.py', 'r') as f:
        content = f.read()
    
    # Add lightweight mode check at the top
    lightweight_content = '''"""
AEC File Manager - Agentic AI Core (Lightweight Mode)
"""

import os
LIGHTWEIGHT_MODE = os.getenv('LIGHTWEIGHT_MODE', 'true').lower() == 'true'

''' + content
    
    with open(lightweight_dir / 'agentic_ai.py', 'w') as f:
        f.write(lightweight_content)
    
    # Copy other files
    files_to_copy = ['ui_app.py', 'llm_integration.py', 'run_app.py']
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, lightweight_dir)
    
    return lightweight_dir

def build_lightweight():
    """Build lightweight executable"""
    print("Building lightweight portable executable...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'aec_manager_lite.spec'
        ])
        
        print("✅ Lightweight executable built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Lightweight build failed: {e}")
        return False

def create_docker_container():
    """Create Docker container for true portability"""
    dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p models temp backups data

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start application
CMD ["python", "run_app.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    # Create docker-compose.yml
    compose_content = """
version: '3.8'

services:
  aec-file-manager:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./temp:/app/temp
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_HEADLESS=true
    restart: unless-stopped
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ Created Docker configuration")

def main():
    """Main lightweight build function"""
    print("🏗️  AEC File Manager - Lightweight Portable Build")
    print("=" * 60)
    
    # Create lightweight spec
    create_lightweight_spec()
    
    # Build lightweight version
    if build_lightweight():
        print("✅ Lightweight version built successfully")
    
    # Create Docker container option
    create_docker_container()
    
    print("\n" + "=" * 60)
    print("🎉 Lightweight Build Options Created!")
    print("=" * 60)
    print("Available options:")
    print("1. Lightweight executable in dist/AEC-File-Manager-Lite/")
    print("2. Docker container: docker-compose up")
    print("3. Regular portable version: python build_portable.py")

if __name__ == "__main__":
    main()