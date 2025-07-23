# AEC File Manager - Portable Deployment Guide

This guide explains how to create and distribute portable versions of the AEC File Manager that can run on any computer without requiring Python installation.

## Quick Build Commands

### Windows
```cmd
# Run the automated build script
build_all_platforms.bat

# Or build individual versions
python build_portable.py          # Full version with AI
python create_lightweight_portable.py  # Lite version
```

### Linux/Mac
```bash
# Run the automated build script
./build_all_platforms.sh

# Or build individual versions
python3 build_portable.py          # Full version with AI
python3 create_lightweight_portable.py  # Lite version
```

## What Gets Created

After running the build scripts, you'll have:

```
AEC-File-Manager-Distribution/
├── Portable-Full/              # Complete version (~500MB)
│   ├── app/                    # Executable and dependencies
│   ├── start_aec_manager.bat   # Windows launcher
│   ├── start_aec_manager.sh    # Linux/Mac launcher
│   ├── config/                 # Configuration files
│   ├── data/                   # User data directory
│   ├── models/                 # AI models directory
│   └── README-Portable.txt     # Usage instructions
│
├── Portable-Lite/              # Lightweight version (~50MB)
│   ├── AEC-File-Manager-Lite   # Executable (Linux/Mac)
│   ├── AEC-File-Manager-Lite.exe  # Executable (Windows)
│   └── _internal/              # Required libraries
│
└── QUICKSTART.txt              # User guide
```

## Distribution Options

### 1. Full Portable Version
- **Size**: ~500MB
- **Features**: Complete AI functionality, document analysis, LLM integration
- **Best for**: Users who need full AI capabilities
- **Startup**: Double-click launcher script

### 2. Lightweight Version  
- **Size**: ~50MB
- **Features**: Basic file management, no AI dependencies
- **Best for**: Quick deployments, basic file operations
- **Startup**: Run executable directly

### 3. Docker Container
```bash
# Build and run with Docker
docker-compose up

# Access at http://localhost:8501
```

## User Instructions

### Windows Users
1. Extract the distribution package
2. Navigate to desired version folder
3. Double-click `start_aec_manager.bat`
4. Application opens in browser automatically

### Linux/Mac Users
1. Extract the distribution package
2. Navigate to desired version folder
3. Run `./start_aec_manager.sh` in terminal
4. Application opens in browser automatically

### Direct Executable (Lite Version)
1. Navigate to `Portable-Lite` folder
2. Run the executable directly:
   - Windows: `AEC-File-Manager-Lite.exe`
   - Linux/Mac: `./AEC-File-Manager-Lite`

## Technical Details

### Dependencies Bundled
- Python 3.9+ runtime
- Streamlit web framework
- Pandas for data processing
- Plotly for visualizations
- File processing libraries (PDF, DOCX, Excel)
- AI libraries (full version only)

### System Requirements
- **RAM**: 2GB minimum, 4GB recommended (full version)
- **Storage**: 1GB free space
- **OS**: Windows 10+, macOS 10.14+, Linux (most distributions)
- **Browser**: Any modern browser (Chrome, Firefox, Safari, Edge)

### Configuration
- Settings stored in `config/.env`
- Data files stored in `data/` directory
- Models cached in `models/` directory
- All paths are relative to executable location

## Troubleshooting

### Common Issues

**Application won't start**
- Check available disk space (>1GB)
- Run as administrator (Windows) or with sudo (Linux/Mac)
- Temporarily disable antivirus software

**Browser doesn't open**
- Manually navigate to http://localhost:8501
- Check if port 8501 is already in use
- Try different port in config/.env

**Large file size**
- Use Lightweight version for basic functionality
- AI models can be removed from `models/` directory if not needed

### Build Issues

**PyInstaller errors**
```bash
# Clean build
python -m PyInstaller --clean aec_manager.spec

# Update PyInstaller
pip install --upgrade pyinstaller
```

**Missing dependencies**
```bash
# Install all build requirements
pip install -r requirements-build.txt
```

## Customization

### Excluding AI Components
Edit `create_lightweight_portable.py` and add to excludes:
```python
excludes=[
    'torch',
    'transformers', 
    'sentence_transformers',
    'langchain'
]
```

### Custom Icon
Add icon to PyInstaller spec:
```python
exe = EXE(
    # ... other parameters ...
    icon='path/to/icon.ico',
)
```

### Environment Variables
Customize default settings in portable config:
```bash
# config/.env
STREAMLIT_PORT=8080        # Custom port
STREAMLIT_HOST=0.0.0.0    # Allow external access
DEBUG_MODE=true           # Enable debug logging
```

## Security Notes

- All processing happens locally - no data sent to external servers
- AI models run locally (if enabled)
- No network access required for core functionality
- User data stays in the portable directory

## Support

For issues with portable deployment:
1. Check the troubleshooting section above
2. Review build logs for specific errors
3. Create an issue at: [GitHub Repository]

---

**Note**: The portable version is ideal for:
- Air-gapped systems
- Quick demonstrations
- Users without Python knowledge
- Consistent deployment across multiple machines