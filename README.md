# AEC File Processor

A local-first AEC (Architecture, Engineering, Construction) file processing system that intelligently organizes and processes project files according to industry standards.

## Current Status

**Phase 0: Local Foundation - COMPLETED**

The system has been completely rebuilt from the ground up following a systematic development approach. We now have a solid foundation with proper AEC industry standards implementation.

### What's Working Now

- **Complete .NET Solution**: Core library, CLI application, API, and test projects
- **AEC Directory Standards**: Supports standard `PROJECT_NAME_PROJECT_NUMBER/` structure
- **Industry File Naming**: Handles `Phase_DocumentType_Description_Revision_Date.ext` format
- **Real-time File Monitoring**: Watches directories for changes and processes files automatically
- **Intelligent Classification**: Automatically categorizes files by phase, discipline, and document type
- **CLI Interface**: Complete command-line tool with watch, process, and query commands

### Supported Standards

#### Phase Codes
- **PD** - Pre-Design/Programming
- **SD** - Schematic Design  
- **DD** - Design Development
- **CD** - Construction Documents
- **CA** - Construction Administration
- **CO** - Closeout

#### Document Types
- **DWG** - Drawings/Plans
- **CALC** - Calculations
- **RPT** - Reports
- **SPEC** - Specifications
- **RFI** - Request for Information
- **SUB** - Submittal
- **CHG** - Change Order
- **PHO** - Photos
- **BIM** - BIM Models

#### Revision System
- **C01, C02, C03...** - Internal coordination and review
- **R0, R1, R2...** - External revisions
- **IFC** - Issued for Construction
- **IFB** - Issued for Bidding
- **IFP** - Issued for Permit

#### File Types
- `.dwg` - AutoCAD files
- `.pdf` - Final issued documents
- `.rvt` - Revit files
- `.docx` - Word documents
- `.xlsx` - Excel spreadsheets
- `.ifc` - BIM exchange files

## Getting Started

### Installation from GitHub

1. **Clone the repository:**
   ```bash
   git clone https://github.com/geotechnick/AEC-File-Manager.git
   cd AEC-File-Manager
   ```

2. **Prerequisites:**
   - .NET 9.0 SDK or later
   - Git

3. **Build the solution:**
   ```bash
   dotnet restore
   dotnet build
   ```

4. **Run the CLI application:**
   ```bash
   cd AECFileProcessor.CLI
   dotnet run help
   ```

## Usage

### CLI Commands

```bash
# Watch a directory for file changes
dotnet run --project AECFileProcessor.CLI watch --path "C:\Projects\MyProject_12345"

# Process files in a directory once
dotnet run --project AECFileProcessor.CLI process --path "C:\Projects\MyProject_12345"

# Query processed files
dotnet run --project AECFileProcessor.CLI query
dotnet run --project AECFileProcessor.CLI query --project 12345

# Show help
dotnet run --project AECFileProcessor.CLI help
```

### Example File Structure

```
MyProject_12345/
├── 02_DRAWINGS/
│   ├── Current/
│   │   ├── Architectural/
│   │   │   ├── CD_DWG_FloorPlan_Level1_R2_031524.pdf
│   │   │   └── DD_DWG_SiteLayout_R1_022824.dwg
│   │   ├── Structural/
│   │   └── Mechanical/
│   └── Superseded/
├── 03_SPECIFICATIONS/
│   ├── CD_SPEC_Division08_Openings_R1_033024.docx
│   └── CD_SPEC_Division15_HVAC_R2_041224.pdf
└── 04_CALCULATIONS/
    └── DD_CALC_StructuralBeams_R2_022024.pdf
```

## Development

### Running Tests
```bash
dotnet test
```

### Building for Release
```bash
dotnet build --configuration Release
```

## Roadmap

### Phase 1: Enhanced Processing (Next)
- SQLite database integration
- Advanced CAD metadata extraction
- PDF content processing with OCR
- Coordination analysis between disciplines

### Phase 2: Advanced Features
- Web API for remote access
- Real-time project health dashboards
- Automated quality checks
- Integration with common AEC tools

### Phase 3: Enterprise Features
- Multi-project management
- Team collaboration features
- Advanced reporting and analytics
- Cloud deployment options

## Architecture

The system follows a clean architecture pattern with:

- **Core Domain**: Business logic and domain models
- **Services**: File processing, classification, and monitoring
- **CLI Interface**: Command-line user interface
- **API**: RESTful web API (planned)
- **Tests**: Comprehensive unit and integration tests

## File Naming Examples

```
CD_DWG_FloorPlan_Level1_R2_031524.pdf
│  │   │        │      │  │
│  │   │        │      │  └── Date (MMDDYY)
│  │   │        │      └──── Revision (R2)
│  │   │        └─────────── Description
│  │   └────────────────────── Document Type
│  └────────────────────────── Phase
└───────────────────────────── Project handled by directory structure
```

## Contributing

This project follows a systematic development approach. Please see the `references/` folder for detailed architecture and development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.