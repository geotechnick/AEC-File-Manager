# 🏗️ AEC File Manager

**Local Agentic AI for Architecture, Engineering & Construction Project Directory Management**

A locally-runnable, open-source AI system that provides intelligent project directory management, file classification, revision tracking, and quality control logging for AEC projects. Features a user-friendly Streamlit interface and supports various local LLM backends for contextual document analysis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-Active-green.svg)

## 🚀 Features

### 🏗️ **Project Structure Management**
- **Automated Directory Creation**: Generates standardized AEC project folders following industry best practices
- **Smart File Classification**: AI-powered file categorization and placement
- **Naming Convention Enforcement**: Maintains consistent file naming across disciplines
- **Template Customization**: Editable directory structures and naming conventions

### 🤖 **Agentic AI Capabilities**
- **Contextual Directory Awareness**: Understands and navigates project hierarchies semantically
- **Natural Language Queries**: Ask questions like "What were the last three change orders?"
- **Document Intelligence**: Automatically summarizes and classifies AEC documents
- **Version Tracking**: Monitors file changes with automated revision logging

### 🔍 **File Intelligence System**
- **Multi-Format Support**: PDF, DOCX, XLSX, CSV, TXT, DWG, DXF, IFC, RVT
- **Content Analysis**: Extracts and analyzes document content
- **Semantic Search**: Find documents by meaning, not just keywords
- **Auto-Classification**: Suggests appropriate folders for uploaded files

### 📋 **Quality Control (QC) Tracking**
- **Review Management**: Track QC status across all project documents
- **Discipline-Based Reviews**: Separate workflows for Architectural, Structural, MEP, etc.
- **Deadline Monitoring**: Automated alerts for overdue reviews
- **Approval Workflows**: Standardized QC processes with comments and status tracking

### 🔄 **Revision Control**
- **Automated Version Tracking**: Monitors file changes with MD5 hash comparison
- **Change Summaries**: AI-generated descriptions of document modifications
- **History Preservation**: Complete revision timeline for all project files
- **Rollback Capability**: Access to previous file versions

### 🖥️ **User Interface**
- **Modern Streamlit UI**: Clean, responsive web interface
- **Visual File Explorer**: Browse project files with AI status indicators
- **Interactive Dashboards**: QC status, revision history, and project metrics
- **Real-time Search**: Natural language query interface

## 🛠️ Installation

### Quick Start (Automated)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/AEC-File-Manager.git
   cd AEC-File-Manager
   ```

2. **Run the installation script**:
   ```bash
   python install.py
   ```

3. **Launch the application**:
   ```bash
   python run_app.py
   ```

### Manual Installation

1. **Prerequisites**:
   - Python 3.8 or higher
   - Git

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env file with your preferences
   ```

4. **Launch application**:
   ```bash
   streamlit run ui_app.py
   ```

## 🤖 Local LLM Setup

### Option 1: Ollama (Recommended)

Ollama is the easiest way to run local LLMs:

1. **Install Ollama**:
   - Windows/Mac: Download from [ollama.ai](https://ollama.ai)
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Download a model**:
   ```bash
   ollama pull llama2
   ```

3. **Update configuration**:
   ```env
   USE_LOCAL_LLM=true
   LLM_MODEL_TYPE=ollama
   OLLAMA_MODEL=llama2
   ```

### Option 2: llama-cpp-python

For direct model file usage:

1. **Install llama-cpp-python**:
   ```bash
   pip install llama-cpp-python
   ```

2. **Download a GGML/GGUF model** from [Hugging Face](https://huggingface.co/models?search=ggml)

3. **Place model in `models/` directory**

4. **Update configuration**:
   ```env
   USE_LOCAL_LLM=true
   LLM_MODEL_TYPE=llama-cpp
   LLM_MODEL_PATH=./models/your-model.ggml
   ```

### Option 3: No LLM (Fallback)

The system works without LLM using pattern matching:

```env
USE_LOCAL_LLM=false
```

## 📁 Project Structure

When creating a new project, the system generates this standardized directory structure:

```
PROJECT_NAME_YYYY/
├── 00_PROJECT_MANAGEMENT/
│   ├── Proposals/
│   ├── Contracts/
│   ├── Project_Charter/
│   ├── Meeting_Minutes/
│   ├── Schedules/
│   └── Budget/
├── 01_CORRESPONDENCE/
│   ├── RFIs/
│   │   ├── Incoming/
│   │   └── Outgoing/
│   ├── Submittals/
│   │   ├── Incoming/
│   │   └── Outgoing/
│   ├── Change_Orders/
│   └── Email/
├── 02_DRAWINGS/
│   ├── Architectural/
│   ├── Structural/
│   ├── Civil/
│   ├── Mechanical/
│   ├── Electrical/
│   ├── Landscape/
│   ├── Current/
│   └── Superseded/
├── 03_SPECIFICATIONS/
│   ├── Division_00_Procurement/
│   ├── Division_01_General/
│   ├── ... (CSI MasterFormat)
│   └── Division_14_Conveying/
├── 04_CALCULATIONS/
│   ├── Structural/
│   ├── Civil/
│   ├── Mechanical/
│   ├── Electrical/
│   └── Energy/
├── 05_REPORTS/
│   ├── Geotechnical/
│   ├── Environmental/
│   ├── Survey/
│   ├── Testing/
│   └── Inspection/
├── 06_PERMITS/
│   ├── Building/
│   ├── Zoning/
│   ├── Environmental/
│   └── Utility/
├── 07_PHOTOS/
│   ├── Site/
│   ├── Progress/
│   ├── Existing_Conditions/
│   └── Completion/
├── 08_MODELS/
│   ├── BIM/
│   ├── CAD/
│   └── 3D/
├── 09_CLOSEOUT/
│   ├── As_Built/
│   ├── Operation_Manuals/
│   ├── Warranties/
│   └── Certificates/
└── 10_ARCHIVE/
    ├── Superseded_Drawings/
    ├── Old_Correspondence/
    └── Previous_Versions/
```

## 📋 File Naming Conventions

The system enforces standardized naming conventions:

**Format**: `ProjectNumber_DisciplineCode_SheetNumber_RevisionNumber_Date.ext`

**Examples**:
- `PROJ123_A_001_R0_2024-01-15.pdf` (Architectural drawing)
- `PROJ123_S_C01_R2_2024-02-20.docx` (Structural calculation)
- `PROJ123_M_RFI-001_R0_2024-03-10.pdf` (Mechanical RFI)

**Discipline Codes**:
- `A` - Architectural
- `S` - Structural
- `C` - Civil
- `M` - Mechanical
- `E` - Electrical
- `L` - Landscape

## 🎯 Usage Guide

### Creating a New Project

1. Navigate to the **Create Project** page
2. Enter project name (e.g., "OFFICE_BUILDING")
3. Select project year
4. Add any custom folders if needed
5. Click **Create Project**

### Uploading and Managing Files

1. Go to **File Explorer**
2. Use the file uploader to add documents
3. Files are automatically classified and placed in appropriate folders
4. Review and approve AI suggestions for file placement

### AI Assistant Queries

The AI Assistant can help with:

- **"What were the last three change orders?"**
- **"Show me the latest structural calculations"**
- **"When was the last RFI received?"**
- **"Which files need QC review?"**

### Quality Control Management

1. **QC Dashboard**: View all QC items and their status
2. **Create QC Entry**: Assign files for review
3. **Update Status**: Mark items as approved, rejected, or needs revision
4. **Overdue Tracking**: Monitor items past their due date

### Revision Tracking

- All file changes are automatically tracked
- View revision history for any file
- Compare versions and see change summaries
- Access previous versions when needed

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Core Settings
USE_LOCAL_LLM=true
DEBUG_MODE=false

# LLM Configuration
LLM_MODEL_TYPE=ollama
OLLAMA_MODEL=llama2
LLM_CONTEXT_SIZE=2048
LLM_MAX_TOKENS=512

# UI Settings
STREAMLIT_PORT=8501
STREAMLIT_HOST=localhost

# File Processing
MAX_FILE_SIZE_MB=100
SUPPORTED_EXTENSIONS=.pdf,.docx,.xlsx,.csv,.txt,.dwg,.dxf,.ifc,.rvt

# QC Settings
DEFAULT_QC_DUE_DAYS=7
QC_REMINDER_DAYS=2

# Security (Optional)
REQUIRE_AUTH=false
```

## 🔧 Architecture

### Core Components

- **`agentic_ai.py`**: Main AI controller and business logic
- **`ui_app.py`**: Streamlit web interface
- **`llm_integration.py`**: Local LLM backends and document processing
- **`run_app.py`**: Application launcher with environment setup
- **`install.py`**: Automated installation script

### Database Schema

**Revisions Table**:
```sql
CREATE TABLE revisions (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    version TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user TEXT,
    change_summary TEXT,
    file_size INTEGER,
    is_current BOOLEAN DEFAULT TRUE
);
```

**QC Log Table**:
```sql
CREATE TABLE qc_log (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,
    filename TEXT NOT NULL,
    discipline TEXT NOT NULL,
    reviewer TEXT,
    review_date TEXT,
    qc_status TEXT NOT NULL,
    comments TEXT,
    due_date TEXT,
    created_date TEXT NOT NULL,
    last_updated TEXT NOT NULL
);
```

## 🔒 Security & Privacy

- **Fully Local Operation**: All data stays on your machine
- **No Cloud Dependencies**: Works completely offline
- **Open Source**: Transparent, auditable code
- **Optional Authentication**: Can be enabled for multi-user environments
- **File Access Control**: Respects local file system permissions

## 🚧 Roadmap

### Planned Features

- [ ] **OCR Integration**: Extract text from scanned documents
- [ ] **BIM Viewer Integration**: Direct model viewing and markup
- [ ] **Email Notifications**: QC reminders and status updates
- [ ] **Voice Assistant**: Natural language voice queries
- [ ] **Advanced Search**: Full-text search across all documents
- [ ] **Collaboration Tools**: Multi-user workflows and comments
- [ ] **Mobile Interface**: Responsive design for tablets/phones
- [ ] **Export Tools**: Generate project reports and summaries
- [ ] **API Integration**: Connect with external AEC software
- [ ] **Cloud Sync**: Optional backup to cloud storage

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Local LLM support via [Ollama](https://ollama.ai/) and [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- Document processing with [PyPDF2](https://pypdf2.readthedocs.io/) and [python-docx](https://python-docx.readthedocs.io/)
- Data visualization with [Plotly](https://plotly.com/)

## 💬 Support

- 📧 **Email**: [Your Email]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/AEC-File-Manager/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/AEC-File-Manager/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/your-username/AEC-File-Manager/wiki)

---

**Built with ❤️ for the AEC Community**