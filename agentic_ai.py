"""
AEC Project Directory Management - Core Agentic AI Logic
"""

import os
import json
import sqlite3
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


class AECDirectoryStructure:
    """Manages AEC project directory structure and naming conventions"""
    
    DEFAULT_STRUCTURE = {
        "00_PROJECT_MANAGEMENT": {
            "Proposals": [],
            "Contracts": [],
            "Project_Charter": [],
            "Meeting_Minutes": [],
            "Schedules": [],
            "Budget": []
        },
        "01_CORRESPONDENCE": {
            "RFIs": ["Incoming", "Outgoing"],
            "Submittals": ["Incoming", "Outgoing"],
            "Change_Orders": [],
            "Email": []
        },
        "02_DRAWINGS": {
            "Architectural": [],
            "Structural": [],
            "Civil": [],
            "Mechanical": [],
            "Electrical": [],
            "Landscape": [],
            "Current": [],
            "Superseded": []
        },
        "03_SPECIFICATIONS": {
            "Division_00_Procurement": [],
            "Division_01_General": [],
            "Division_02_Existing": [],
            "Division_03_Concrete": [],
            "Division_04_Masonry": [],
            "Division_05_Metals": [],
            "Division_06_Wood": [],
            "Division_07_Thermal": [],
            "Division_08_Openings": [],
            "Division_09_Finishes": [],
            "Division_10_Specialties": [],
            "Division_11_Equipment": [],
            "Division_12_Furnishings": [],
            "Division_13_Special": [],
            "Division_14_Conveying": []
        },
        "04_CALCULATIONS": {
            "Structural": [],
            "Civil": [],
            "Mechanical": [],
            "Electrical": [],
            "Energy": []
        },
        "05_REPORTS": {
            "Geotechnical": [],
            "Environmental": [],
            "Survey": [],
            "Testing": [],
            "Inspection": []
        },
        "06_PERMITS": {
            "Building": [],
            "Zoning": [],
            "Environmental": [],
            "Utility": []
        },
        "07_PHOTOS": {
            "Site": [],
            "Progress": [],
            "Existing_Conditions": [],
            "Completion": []
        },
        "08_MODELS": {
            "BIM": [],
            "CAD": [],
            "3D": []
        },
        "09_CLOSEOUT": {
            "As_Built": [],
            "Operation_Manuals": [],
            "Warranties": [],
            "Certificates": []
        },
        "10_ARCHIVE": {
            "Superseded_Drawings": [],
            "Old_Correspondence": [],
            "Previous_Versions": []
        }
    }
    
    DISCIPLINE_CODES = {
        "A": "Architectural",
        "S": "Structural", 
        "C": "Civil",
        "M": "Mechanical",
        "E": "Electrical",
        "L": "Landscape"
    }

    def __init__(self, project_name: str, year: int):
        self.project_name = project_name
        self.year = year
        self.project_dir = f"{project_name}_{year}"
        
    def create_directory_structure(self, base_path: str = ".") -> str:
        """Create the full AEC directory structure"""
        project_path = os.path.join(base_path, self.project_dir)
        
        if os.path.exists(project_path):
            raise ValueError(f"Project directory {project_path} already exists")
            
        os.makedirs(project_path)
        
        for main_folder, subfolders in self.DEFAULT_STRUCTURE.items():
            main_path = os.path.join(project_path, main_folder)
            os.makedirs(main_path)
            
            if isinstance(subfolders, dict):
                for subfolder, sub_subfolders in subfolders.items():
                    sub_path = os.path.join(main_path, subfolder)
                    os.makedirs(sub_path)
                    
                    for sub_subfolder in sub_subfolders:
                        os.makedirs(os.path.join(sub_path, sub_subfolder))
            elif isinstance(subfolders, list):
                for subfolder in subfolders:
                    os.makedirs(os.path.join(main_path, subfolder))
                    
        return project_path
    
    @staticmethod
    def validate_filename(filename: str) -> Dict[str, str]:
        """Validate and parse AEC filename convention"""
        # Expected format: ProjectNumber_DisciplineCode_SheetNumber_RevisionNumber_Date.ext
        parts = filename.split('_')
        
        if len(parts) < 5:
            return {"valid": False, "error": "Insufficient filename components"}
            
        return {
            "valid": True,
            "project_number": parts[0],
            "discipline_code": parts[1],
            "sheet_number": parts[2],
            "revision_number": parts[3],
            "date": parts[4].split('.')[0],
            "extension": filename.split('.')[-1] if '.' in filename else ""
        }
    
    @staticmethod
    def suggest_filename(project_number: str, discipline: str, sheet_number: str, 
                        revision: str = "R0", date: str = None) -> str:
        """Generate standardized filename"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        discipline_code = discipline.upper()[0] if discipline else "X"
        return f"{project_number}_{discipline_code}_{sheet_number}_{revision}_{date}"


class FileIntelligence:
    """Handles file parsing, classification, and contextual analysis"""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'PDF Document',
        '.docx': 'Word Document',
        '.xlsx': 'Excel Spreadsheet',
        '.csv': 'CSV Data',
        '.txt': 'Text File',
        '.dwg': 'AutoCAD Drawing',
        '.dxf': 'DXF Drawing',
        '.ifc': 'BIM Model',
        '.rvt': 'Revit Model',
        '.skp': 'SketchUp Model'
    }
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        
    def classify_file(self, filepath: str) -> Dict[str, str]:
        """Classify file based on name, extension, and content"""
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        # Basic classification by extension
        file_type = self.SUPPORTED_EXTENSIONS.get(ext, 'Unknown')
        
        # Enhanced classification by filename patterns
        suggested_folder = self._suggest_folder_by_filename(filename)
        
        return {
            "filename": filename,
            "file_type": file_type,
            "extension": ext,
            "suggested_folder": suggested_folder,
            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat() if os.path.exists(filepath) else None
        }
    
    def _suggest_folder_by_filename(self, filename: str) -> str:
        """Suggest appropriate folder based on filename patterns"""
        filename_lower = filename.lower()
        
        # Pattern matching for common AEC file types
        patterns = {
            "02_DRAWINGS": ["drawing", "plan", "elevation", "section", "detail", "dwg", "dxf"],
            "03_SPECIFICATIONS": ["spec", "specification", "division"],
            "04_CALCULATIONS": ["calc", "calculation", "analysis", "structural"],
            "01_CORRESPONDENCE": ["rfi", "submittal", "email", "letter", "memo"],
            "05_REPORTS": ["report", "geotech", "survey", "testing"],
            "06_PERMITS": ["permit", "approval", "zoning"],
            "07_PHOTOS": ["photo", "image", "jpg", "png", "site"],
            "08_MODELS": ["model", "bim", "revit", "rvt", "ifc"]
        }
        
        for folder, keywords in patterns.items():
            if any(keyword in filename_lower for keyword in keywords):
                return folder
                
        return "10_ARCHIVE"  # Default fallback
    
    def get_file_hash(self, filepath: str) -> str:
        """Generate MD5 hash for file version tracking"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"error_{str(e)}"


class RevisionsTracker:
    """Manages file revision tracking and change logs"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.db_path = os.path.join(project_path, "revisions.db")
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for revision tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                version TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user TEXT,
                change_summary TEXT,
                file_size INTEGER,
                is_current BOOLEAN DEFAULT TRUE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_filepath ON revisions(filepath);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_current ON revisions(is_current);
        ''')
        
        conn.commit()
        conn.close()
    
    def track_file(self, filepath: str, user: str = "system", 
                   change_summary: str = "File added/updated") -> bool:
        """Track a new file revision"""
        if not os.path.exists(filepath):
            return False
            
        filename = os.path.basename(filepath)
        file_hash = FileIntelligence(self.project_path).get_file_hash(filepath)
        file_size = os.path.getsize(filepath)
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if this exact version already exists
        cursor.execute('''
            SELECT id FROM revisions 
            WHERE filepath = ? AND file_hash = ?
        ''', (filepath, file_hash))
        
        if cursor.fetchone():
            conn.close()
            return False  # Identical version already tracked
        
        # Mark previous versions as not current
        cursor.execute('''
            UPDATE revisions 
            SET is_current = FALSE 
            WHERE filepath = ?
        ''', (filepath,))
        
        # Get next version number
        cursor.execute('''
            SELECT MAX(CAST(REPLACE(version, 'v', '') AS INTEGER)) 
            FROM revisions 
            WHERE filepath = ?
        ''', (filepath,))
        
        result = cursor.fetchone()
        next_version = f"v{(result[0] or 0) + 1}"
        
        # Insert new revision
        cursor.execute('''
            INSERT INTO revisions 
            (filepath, filename, file_hash, version, timestamp, user, change_summary, file_size, is_current)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
        ''', (filepath, filename, file_hash, next_version, timestamp, user, change_summary, file_size))
        
        conn.commit()
        conn.close()
        return True
    
    def get_file_history(self, filepath: str) -> List[Dict]:
        """Get revision history for a specific file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, timestamp, user, change_summary, file_size, is_current
            FROM revisions 
            WHERE filepath = ?
            ORDER BY timestamp DESC
        ''', (filepath,))
        
        revisions = []
        for row in cursor.fetchall():
            revisions.append({
                "version": row[0],
                "timestamp": row[1],
                "user": row[2],
                "change_summary": row[3],
                "file_size": row[4],
                "is_current": bool(row[5])
            })
        
        conn.close()
        return revisions


class QCLogger:
    """Quality Control logging and tracking system"""
    
    QC_STATUSES = ["Pending", "In Review", "Approved", "Rejected", "Revision Required"]
    DISCIPLINES = ["Architectural", "Structural", "Civil", "Mechanical", "Electrical", "General"]
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.db_path = os.path.join(project_path, "qc_log.db")
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for QC tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qc_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_qc_filepath ON qc_log(filepath);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_qc_status ON qc_log(qc_status);
        ''')
        
        conn.commit()
        conn.close()
    
    def create_qc_entry(self, filepath: str, discipline: str, 
                       reviewer: str = None, due_days: int = 7) -> int:
        """Create new QC entry for a file"""
        filename = os.path.basename(filepath)
        created_date = datetime.now().isoformat()
        due_date = (datetime.now().replace(day=datetime.now().day + due_days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qc_log 
            (filepath, filename, discipline, reviewer, qc_status, due_date, created_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filepath, filename, discipline, reviewer, "Pending", due_date, created_date, created_date))
        
        qc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return qc_id
    
    def update_qc_status(self, qc_id: int, status: str, reviewer: str, 
                        comments: str = None) -> bool:
        """Update QC entry status"""
        if status not in self.QC_STATUSES:
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_time = datetime.now().isoformat()
        review_date = update_time if status != "Pending" else None
        
        cursor.execute('''
            UPDATE qc_log 
            SET qc_status = ?, reviewer = ?, comments = ?, review_date = ?, last_updated = ?
            WHERE id = ?
        ''', (status, reviewer, comments, review_date, update_time, qc_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_overdue_qc(self) -> List[Dict]:
        """Get files with overdue QC reviews"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_date = datetime.now().isoformat()
        
        cursor.execute('''
            SELECT id, filepath, filename, discipline, due_date, qc_status
            FROM qc_log 
            WHERE due_date < ? AND qc_status = 'Pending'
            ORDER BY due_date ASC
        ''', (current_date,))
        
        overdue = []
        for row in cursor.fetchall():
            overdue.append({
                "id": row[0],
                "filepath": row[1],
                "filename": row[2],
                "discipline": row[3],
                "due_date": row[4],
                "status": row[5]
            })
        
        conn.close()
        return overdue
    
    def get_qc_summary(self) -> Dict:
        """Get QC status summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT qc_status, COUNT(*) as count
            FROM qc_log 
            GROUP BY qc_status
        ''')
        
        status_counts = {status: 0 for status in self.QC_STATUSES}
        for row in cursor.fetchall():
            status_counts[row[0]] = row[1]
        
        conn.close()
        return status_counts


class AgenticAI:
    """Main Agentic AI controller class"""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
        self.file_intelligence = FileIntelligence(project_path) if project_path else None
        self.revisions_tracker = RevisionsTracker(project_path) if project_path else None
        self.qc_logger = QCLogger(project_path) if project_path else None
    
    def initialize_project(self, project_name: str, year: int, base_path: str = ".") -> str:
        """Initialize a new AEC project"""
        structure = AECDirectoryStructure(project_name, year)
        project_path = structure.create_directory_structure(base_path)
        
        # Initialize components for new project
        self.project_path = project_path
        self.file_intelligence = FileIntelligence(project_path)
        self.revisions_tracker = RevisionsTracker(project_path)
        self.qc_logger = QCLogger(project_path)
        
        return project_path
    
    def scan_and_classify_files(self) -> Dict[str, List[Dict]]:
        """Scan project directory and classify all files"""
        if not self.project_path or not os.path.exists(self.project_path):
            return {}
        
        classified_files = {}
        
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.startswith('.') or file.endswith('.db'):
                    continue
                    
                filepath = os.path.join(root, file)
                classification = self.file_intelligence.classify_file(filepath)
                
                folder = os.path.relpath(root, self.project_path)
                if folder not in classified_files:
                    classified_files[folder] = []
                
                classified_files[folder].append({
                    **classification,
                    "full_path": filepath
                })
        
        return classified_files
    
    def process_query(self, query: str) -> str:
        """Process natural language queries about the project"""
        query_lower = query.lower()
        
        # Simple pattern matching for common queries
        if "change order" in query_lower:
            return self._find_change_orders()
        elif "structural calc" in query_lower:
            return self._find_structural_calculations()
        elif "latest rfi" in query_lower or "last rfi" in query_lower:
            return self._find_latest_rfis()
        elif "overdue qc" in query_lower or "overdue review" in query_lower:
            return self._get_overdue_qc_summary()
        else:
            return f"Query processing for '{query}' is not yet implemented. Available queries include: change orders, structural calculations, latest RFIs, overdue QC."
    
    def _find_change_orders(self) -> str:
        """Find change order documents"""
        co_path = os.path.join(self.project_path, "01_CORRESPONDENCE", "Change_Orders")
        if not os.path.exists(co_path):
            return "No change orders directory found."
        
        files = [f for f in os.listdir(co_path) if not f.startswith('.')]
        if not files:
            return "No change orders found."
        
        # Sort by modification time (most recent first)
        files_with_time = [(f, os.path.getmtime(os.path.join(co_path, f))) for f in files]
        files_sorted = sorted(files_with_time, key=lambda x: x[1], reverse=True)
        
        recent_cos = files_sorted[:3]
        result = "Latest change orders:\n"
        for co, _ in recent_cos:
            result += f"- {co}\n"
        
        return result
    
    def _find_structural_calculations(self) -> str:
        """Find structural calculation files"""
        calc_path = os.path.join(self.project_path, "04_CALCULATIONS", "Structural")
        if not os.path.exists(calc_path):
            return "No structural calculations directory found."
        
        files = [f for f in os.listdir(calc_path) if not f.startswith('.')]
        if not files:
            return "No structural calculations found."
        
        return f"Found {len(files)} structural calculation files:\n" + "\n".join([f"- {f}" for f in files[:5]])
    
    def _find_latest_rfis(self) -> str:
        """Find latest RFI documents"""
        rfi_path = os.path.join(self.project_path, "01_CORRESPONDENCE", "RFIs")
        if not os.path.exists(rfi_path):
            return "No RFIs directory found."
        
        all_files = []
        for subdir in ["Incoming", "Outgoing"]:
            subdir_path = os.path.join(rfi_path, subdir)
            if os.path.exists(subdir_path):
                files = [os.path.join(subdir_path, f) for f in os.listdir(subdir_path) if not f.startswith('.')]
                all_files.extend(files)
        
        if not all_files:
            return "No RFI files found."
        
        # Sort by modification time
        files_with_time = [(f, os.path.getmtime(f)) for f in all_files]
        files_sorted = sorted(files_with_time, key=lambda x: x[1], reverse=True)
        
        latest_rfi = files_sorted[0]
        mod_time = datetime.fromtimestamp(latest_rfi[1]).strftime("%Y-%m-%d %H:%M")
        
        return f"Latest RFI: {os.path.basename(latest_rfi[0])}\nModified: {mod_time}"
    
    def _get_overdue_qc_summary(self) -> str:
        """Get summary of overdue QC items"""
        if not self.qc_logger:
            return "QC system not initialized."
        
        overdue = self.qc_logger.get_overdue_qc()
        if not overdue:
            return "No overdue QC items found."
        
        result = f"Found {len(overdue)} overdue QC items:\n"
        for item in overdue[:5]:  # Show first 5
            result += f"- {item['filename']} ({item['discipline']}) - Due: {item['due_date'][:10]}\n"
        
        return result


if __name__ == "__main__":
    # Example usage
    ai = AgenticAI()
    
    # Initialize a new project
    project_path = ai.initialize_project("SAMPLE_PROJECT", 2024, ".")
    print(f"Created project at: {project_path}")
    
    # Scan and classify files
    classified = ai.scan_and_classify_files()
    print(f"Classified files in {len(classified)} directories")