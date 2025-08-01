# AEC File Manager

## Professional Project Organization System

AEC File Manager is a comprehensive file management solution designed specifically for Architecture, Engineering, and Construction professionals. The system automatically creates standardized project directory structures, organizes files according to industry best practices, and provides advanced reporting capabilities to streamline project workflows.

## Overview

This software addresses the critical need for consistent file organization in AEC projects by implementing industry-standard directory structures and automated file classification. The system supports both standalone operation requiring no technical setup and full-featured installation for advanced functionality.

## Getting Started

### Instant Setup (No Installation Required)

For immediate use without technical setup:

1. Download the repository as a ZIP file from GitHub
2. Extract the files to your local system
3. Execute `AEC-Setup-Standalone.bat` to create the project structure
4. Execute `AEC-Organize-Files.bat` to organize existing files

This approach works on any Windows system without requiring Python installation or configuration.

### Full Installation (Advanced Features)

For access to metadata extraction, HTML reporting, and database functionality:

Follow the [Technical Installation Guide](#installation) below.

## Documentation

| Resource | Target Audience | Content |
|----------|----------------|---------|
| [Standalone Guide](docs/STANDALONE_README.md) | All users | Basic functionality without installation |
| [Installation Guide](docs/EASY_INSTALL_GUIDE.md) | Non-technical users | Detailed setup instructions |
| [Quick Start Guide](docs/QUICK_START.md) | Technical users | Rapid deployment guide |

## Features

### Professional Directory Structure

The system creates a comprehensive 506-directory structure following AEC industry standards:

```
PROJECT_NAME_2024/
├── 00_PROJECT_MANAGEMENT/      # Contracts, schedules, budgets
├── 01_CORRESPONDENCE/          # RFIs, submittals, communications
├── 02_DRAWINGS/               # CAD files and technical drawings
├── 03_SPECIFICATIONS/         # CSI MasterFormat specifications
├── 04_CALCULATIONS/           # Engineering calculations
├── 05_REPORTS/                # Technical reports and studies
├── 06_PERMITS_APPROVALS/      # Regulatory documentation
├── 07_SITE_DOCUMENTATION/     # Field documentation and photos
├── 08_MODELS_CAD/             # BIM models and 3D files
├── 09_CONSTRUCTION_ADMIN/     # Construction phase documentation
├── 10_CLOSEOUT/               # Project completion documents
├── 11_SPECIALTY_CONSULTANTS/  # Specialty consultant deliverables
├── 12_STANDARDS_TEMPLATES/    # Project standards and templates
└── 13_ARCHIVE/                # Historical and superseded files
```

### Intelligent File Organization

- **Pattern Recognition**: Automatically identifies AEC file naming conventions
- **Multi-format Support**: Handles CAD files, PDFs, Office documents, images, and BIM files
- **Safe Operations**: Files are copied rather than moved to preserve originals
- **Industry Compliance**: Implements CSI MasterFormat standards

### Advanced Capabilities

**Full Version Features:**
- Metadata extraction from technical documents
- HTML report generation with project analytics
- Database tracking of file changes and revisions
- Performance monitoring and optimization
- Batch processing capabilities

## Installation

### System Requirements

- Windows 10/11 (standalone version)
- Python 3.8+ (full version)
- Internet connection for initial setup

### Technical Installation

```bash
# Clone the repository
git clone https://github.com/geotechnick/AEC-File-Manager
cd AEC-File-Manager

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Command Line Usage

```bash
# Initialize new project with automatic settings detection
aec

# Scan and organize project files
aec scan

# Generate comprehensive project report
aec report

# Display system status and project information
aec status
```

## File Format Support

### Supported File Types

- **CAD Files**: DWG, DXF with layer and block extraction
- **Document Files**: PDF with title block and revision extraction
- **Office Documents**: Word, Excel, PowerPoint with metadata parsing
- **Image Files**: JPG, PNG, TIFF with EXIF data extraction
- **BIM Files**: IFC, RVT with model property extraction
- **Text Files**: TXT, MD, RTF, CSV with encoding detection

### AEC-Specific Processing

- Drawing number and sheet identification
- Revision tracking and history management
- Phase code recognition and classification
- Discipline assignment based on naming conventions
- CSI MasterFormat section identification

## Use Cases

### Target Applications

- **Architecture Firms**: Project file organization and drawing management
- **Engineering Companies**: Calculation and technical document organization
- **Construction Companies**: Submittal tracking and field documentation
- **Project Management**: Document control and compliance monitoring
- **Facility Management**: As-built documentation and maintenance records

### Performance Metrics

- Directory creation: 500+ directories in under 10 seconds
- File processing: 10,000+ files per minute scanning capability
- Pattern recognition: Automatic classification of standard AEC naming conventions
- Database performance: Sub-second query response times for large projects

## Architecture

### System Components

- **Core Engine**: Directory management and file processing
- **Metadata Extractors**: Specialized parsers for different file types
- **Database Layer**: SQLite/PostgreSQL support for project tracking
- **CLI Interface**: Command-line tools for automated workflows
- **Reporting Engine**: HTML and data export capabilities

### Security Model

- Read-only file operations by default
- No modification of original files
- Complete audit trail of all operations
- Input validation and sanitization
- Defensive security implementation

## Support

### Documentation

Complete documentation is available in the `docs/` directory, including:

- Installation guides for different user levels
- API documentation for developers
- Configuration reference
- Troubleshooting guides

### Community Support

- **Issues**: [GitHub Issues](https://github.com/geotechnick/AEC-File-Manager/issues)
- **Feature Requests**: Submit via GitHub Issues
- **Contributing**: Community contributions welcome

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for complete terms.

## Professional Benefits

### Industry Compliance
- Implements AEC industry best practices
- CSI MasterFormat integration
- Scalable from small projects to enterprise deployments
- Compatible with existing AEC workflows

### Operational Efficiency  
- Eliminates manual file organization overhead
- Reduces time spent searching for project documents
- Standardizes file naming and organization across teams
- Provides immediate project structure without training requirements

### Risk Mitigation
- Preserves all original files during organization
- Maintains complete audit trail of operations
- Implements defensive security practices
- Provides backup and recovery capabilities

---

*AEC File Manager: Professional project organization for the modern AEC industry.*