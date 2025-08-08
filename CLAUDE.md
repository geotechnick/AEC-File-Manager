# AEC File Manager - Claude AI Assistant Information

## Project Overview

The **AEC File Manager** is a local-first file processing system specifically designed for Architecture, Engineering, and Construction (AEC) project files. It intelligently organizes, processes, and manages project files according to industry standards, with automated file classification, metadata extraction, and real-time monitoring capabilities.

## Technology Stack

- **.NET 9.0** - Core framework
- **C#** - Primary programming language  
- **CLI Application** - Command-line interface for project management
- **Web API** - RESTful API for integration (planned)
- **In-memory storage** - Current data storage (SQLite planned for Phase 1)
- **Real-time file monitoring** - Automatic file change detection

## Project Structure

```
AECFileProcessor.sln                 # Main solution file
├── AECFileProcessor.Core/           # Core business logic and domain models
│   ├── Interfaces/                  # Service contracts and abstractions
│   ├── Models/                      # Domain models and data structures
│   └── Services/                    # Business logic implementations
├── AECFileProcessor.CLI/            # Command-line interface application
├── AECFileProcessor.API/            # Web API project (for future web interface)
├── AECFileProcessor.Tests/          # Unit and integration tests
└── references/                     # Architecture and design documentation
```

## Current Status: Phase 0 Complete

The system has been completely rebuilt following systematic development approach with these working features:

### ✅ Core Features
- **Project Structure Creation** - Creates 87 standard AEC directories with CSI MasterFormat divisions
- **File Classification** - Automatically categorizes files by phase, discipline, document type
- **Real-time Monitoring** - Watches directories for changes and processes files automatically  
- **Industry Standards** - Supports AEC naming conventions and file organization
- **CLI Interface** - Complete command-line tool with multiple commands

### ✅ Supported Standards

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

#### File Types
- `.dwg` - AutoCAD files
- `.pdf` - Final issued documents
- `.rvt` - Revit files
- `.docx` - Word documents
- `.xlsx` - Excel spreadsheets
- `.ifc` - BIM exchange files

## CLI Commands

### Basic Commands
```bash
# Build and run the application
dotnet build
cd AECFileProcessor.CLI
dotnet run help

# Create a new project with standard AEC structure
dotnet run create-project --path "C:\Projects" --name "OfficeBuilding" --number "12345"

# Validate existing project structure  
dotnet run validate-project --path "C:\Projects\OfficeBuilding_12345"

# Watch a directory for file changes (real-time processing)
dotnet run watch --path "C:\Projects\OfficeBuilding_12345"

# Process files in a directory once
dotnet run process --path "C:\Projects\OfficeBuilding_12345"

# Query processed files
dotnet run query
dotnet run query --project 12345
```

## Key Classes and Components

### Core Models
- **FileRecord** (`AECFileProcessor.Core.Models.FileRecord`): Represents a processed file with AEC metadata
  - Contains classification fields (Phase, Discipline, DocumentType)
  - Tracks processing status and extracted metadata
  - Supports revision management and project association

### Services
- **ProjectStructureService** (`AECFileProcessor.Core.Services.ProjectStructureService`): 
  - Creates standard 87-directory AEC project structure
  - Validates existing project compliance (80% threshold)
  - Generates PROJECT_INFO.md and README files with naming conventions

- **BasicFileProcessor** (`AECFileProcessor.Core.Services.BasicFileProcessor`):
  - Processes individual files and extracts metadata
  - Classifies files according to AEC naming conventions
  - Updates file records with processing status

- **LocalFileWatcher** (`AECFileProcessor.Core.Services.LocalFileWatcher`):
  - Monitors directories for file system changes
  - Automatically processes new/modified files
  - Filters out temporary and system files

### Interfaces
- **IFileProcessor** - Contract for file processing operations
- **IFileRepository** - Data access abstraction (currently in-memory)
- **IProjectStructureService** - Project structure management contract

## File Naming Convention

Files should follow the format: `Phase_DocumentType_Description_Revision_Date.ext`

**Example:** `CD_DWG_FloorPlan_Level1_R2_031524.pdf`

This convention allows automatic classification of:
- Project phase (PD, SD, DD, CD, CA, CO)
- Document type (DWG, CALC, RPT, SPEC, etc.)
- Descriptive content
- Revision level (C01, R1, IFC, etc.)
- Creation/modification date

## Development Approach

The project follows a systematic development approach with clear phases:

1. **Phase 0** (Complete) - Local foundation with core file processing
2. **Phase 1** (Next) - SQLite integration and advanced metadata extraction  
3. **Phase 2** - Web API and real-time dashboards
4. **Phase 3** - Enterprise features and cloud deployment

## Testing and Quality

- **Unit tests** in `AECFileProcessor.Tests`
- **Integration tests** for file processing workflows
- **Logging** with Microsoft.Extensions.Logging throughout
- **Error handling** with graceful degradation

## Development Commands

```bash
# Build the solution
dotnet build

# Run tests
dotnet test

# Build for release
dotnet build --configuration Release

# Run specific project
dotnet run --project AECFileProcessor.CLI [command] [options]
```

## Architecture Notes

The system uses a clean architecture approach:
- **Domain models** in Core project
- **Business logic** separated into services
- **Infrastructure concerns** isolated in appropriate projects
- **Dependency injection** for loose coupling
- **Interface-based design** for testability

## Future Roadmap

### Phase 1: Enhanced Processing
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

## Working with This Codebase

When making changes to this project:

1. **Understand the domain** - This is AEC-specific with industry terminology
2. **Follow naming conventions** - Both code and file naming standards matter
3. **Maintain clean architecture** - Keep business logic in Core, infrastructure separate
4. **Add logging** - Use ILogger for debugging and monitoring
5. **Write tests** - Especially for file processing logic
6. **Consider performance** - File processing can be resource intensive

## Getting Started for Development

1. **Prerequisites**: .NET 9.0 SDK
2. **Clone repository**: `git clone [repository-url]`
3. **Restore packages**: `dotnet restore`
4. **Build solution**: `dotnet build`
5. **Run tests**: `dotnet test`
6. **Try CLI**: `cd AECFileProcessor.CLI && dotnet run help`

The project is ready for development and extension, with a solid foundation for AEC file management workflows.