#!/bin/bash

echo "AEC File Manager - Multi-Platform Build Script"
echo "==============================================="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "ERROR: Python $required_version or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "Installing build dependencies..."
python3 -m pip install -r requirements-build.txt

echo ""
echo "Building portable version..."
python3 build_portable.py

echo ""
echo "Building lightweight version..."
python3 create_lightweight_portable.py

echo ""
echo "Creating distribution package..."
rm -rf "AEC-File-Manager-Distribution"
mkdir -p "AEC-File-Manager-Distribution"

# Copy portable versions
if [ -d "AEC-File-Manager-Portable" ]; then
    cp -r "AEC-File-Manager-Portable" "AEC-File-Manager-Distribution/Portable-Full"
fi

if [ -d "dist/AEC-File-Manager-Lite" ]; then
    cp -r "dist/AEC-File-Manager-Lite" "AEC-File-Manager-Distribution/Portable-Lite"
fi

# Create quick start guide
cat > "AEC-File-Manager-Distribution/QUICKSTART.txt" << EOF
AEC File Manager - Quick Start
================================

Choose your version:

1. Full Version (Portable-Full):
   - Complete AI features
   - Larger file size (~500MB+)
   - Run: ./start_aec_manager.sh

2. Lite Version (Portable-Lite):
   - Basic file management
   - Smaller file size (~50MB)
   - Run: ./AEC-File-Manager-Lite

No Python installation required for either version!

For support: https://github.com/your-repo/AEC-File-Manager
EOF

# Make shell scripts executable
find "AEC-File-Manager-Distribution" -name "*.sh" -exec chmod +x {} \;

echo ""
echo "==============================================="
echo "Build Complete!"
echo "==============================================="
echo ""
echo "Distribution package created in:"
echo "AEC-File-Manager-Distribution/"
echo ""
echo "To distribute:"
echo "1. Compress the entire 'AEC-File-Manager-Distribution' folder"
echo "2. Users can extract and run without installing anything"
echo ""