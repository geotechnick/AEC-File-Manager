# 📁 AEC File Manager - Project Structure

This document outlines the clean, organized structure of the AEC File Manager project.

---

## 🏗️ Project Layout

```
AEC-File-Manager/
├── 📄 README.md                          # Main project documentation
├── 📄 LICENSE                            # MIT License
├── 📄 CHANGELOG.md                       # Version history and changes
├── 📄 requirements.txt                   # Python dependencies
├── 📄 setup.py                          # Python package setup
│
├── 🚀 AEC-Setup-Standalone.bat          # Zero-install project creator
├── 🔧 AEC-Organize-Files.bat            # Zero-install file organizer
│
├── 🐍 aec_scanner_cli.py                # Advanced CLI interface
├── 🐍 aec_streamlined_cli.py            # Simplified CLI interface
│
├── 📁 docs/                             # All documentation
│   ├── STANDALONE_README.md             # Zero-installation guide
│   ├── EASY_INSTALL_GUIDE.md            # Step-by-step for non-programmers
│   └── QUICK_START.md                   # 5-minute setup guide
│
├── 📁 scripts/                          # Build and utility scripts
│   └── build_standalone.py              # Creates executable version
│
├── 📁 config/                           # Configuration files
│   └── aec_scanner_config.yaml          # Default system configuration
│
└── 📁 src/                              # Python source code
    └── aec_scanner/                     # Main package
        ├── core/                        # Core functionality
        ├── database/                    # Database management
        ├── extractors/                  # Metadata extractors
        └── utils/                       # Utility modules
```

---

## 🎯 Usage Paths

### For Non-Programmers (Zero Installation):
1. **Download** the repository as ZIP
2. **Extract** files
3. **Double-click** `AEC-Setup-Standalone.bat` or `AEC-Organize-Files.bat`

### For Technical Users (Full Features):
1. **Install** Python dependencies: `pip install -r requirements.txt`
2. **Install** package: `pip install -e .`
3. **Use** advanced commands: `aec`, `aec scan`, `aec report`

---

## 📚 Documentation Guide

| File | Purpose | Target Audience |
|------|---------|----------------|
| `README.md` | Main project overview | Everyone |
| `docs/STANDALONE_README.md` | Zero-installation guide | Non-programmers |
| `docs/EASY_INSTALL_GUIDE.md` | Step-by-step installation | Beginners |
| `docs/QUICK_START.md` | Fast setup guide | Experienced users |
| `PROJECT_STRUCTURE.md` | This file - project layout | Developers |

---

## 🔧 Core Components

### Standalone Scripts (No Installation):
- **`AEC-Setup-Standalone.bat`**: Creates complete AEC project structure (506 directories)
- **`AEC-Organize-Files.bat`**: Organizes existing files using smart pattern recognition

### Python CLI Tools:
- **`aec_streamlined_cli.py`**: Simplified interface with smart defaults
- **`aec_scanner_cli.py`**: Advanced interface with full feature access

### Build Tools:
- **`scripts/build_standalone.py`**: Creates Windows executable with PyInstaller
- **`setup.py`**: Standard Python package installation

### Configuration:
- **`config/aec_scanner_config.yaml`**: Default system settings
- **`requirements.txt`**: Python package dependencies

---

## 🧹 What Was Cleaned Up

### Removed Files:
- ❌ `test_*.py` - Test files moved to proper testing framework
- ❌ `demo_*.py` - Demo files consolidated into documentation
- ❌ `test_projects/` - Large test directory removed
- ❌ `logs/` - Runtime logs directory removed
- ❌ `aec_scanner.db` - Database files removed from repo
- ❌ `INSTALL.bat` - Redundant installer removed

### Organized Structure:
- ✅ All documentation moved to `docs/` folder
- ✅ Build scripts moved to `scripts/` folder
- ✅ Clear separation between standalone and full versions
- ✅ Logical file naming and organization

---

## 🚀 Getting Started

**Choose your path:**

1. **🟢 Easiest**: Use standalone `.bat` files (no installation)
2. **🟡 Full Features**: Follow technical installation for Python version

**All documentation is now organized in the `docs/` folder with clear guidance for each user type.**

---

*Clean, organized, and ready for professional AEC workflows!* 🏗️