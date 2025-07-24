"""
AEC Directory Manager

Handles creation, validation, and management of the standardized AEC project 
directory structure.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union


class AECDirectoryManager:
    """
    Manages the standardized AEC project directory structure including creation,
    validation, repair, and version management.
    """
    
    # Standard AEC directory structure template
    STANDARD_STRUCTURE = {
        "01_Project_Management": {
            "description": "Project administration, contracts, correspondence",
            "subdirs": ["Contracts", "Correspondence", "Meetings", "Reports"]
        },
        "02_Programming": {
            "description": "Project programming, space planning, feasibility studies",
            "subdirs": ["Feasibility", "Space_Planning", "Programming_Reports"]
        },
        "03_Schematic_Design": {
            "description": "Conceptual design documents and drawings",
            "subdirs": ["Drawings", "3D_Models", "Renderings", "Reports"]
        },
        "04_Design_Development": {
            "description": "Developed design documents and coordination",
            "subdirs": ["Architectural", "Structural", "MEP", "Civil", "Landscape"]
        },
        "05_Construction_Documents": {
            "description": "Final construction drawings and specifications",
            "subdirs": ["Drawings", "Specifications", "Details", "Schedules"]
        },
        "06_Bidding_Procurement": {
            "description": "Bidding documents and contractor procurement",
            "subdirs": ["Bid_Documents", "Addenda", "Contractor_Submissions"]
        },
        "07_Construction_Administration": {
            "description": "Construction phase administration and oversight",
            "subdirs": ["RFIs", "Submittals", "Change_Orders", "Field_Reports"]
        },
        "08_Post_Construction": {
            "description": "Closeout documents and post-occupancy materials",
            "subdirs": ["As_Built", "O&M_Manuals", "Warranties", "Commissioning"]
        },
        "09_Consultants": {
            "description": "External consultant deliverables and coordination",
            "subdirs": ["Structural", "MEP", "Civil", "Landscape", "Specialty"]
        },
        "10_References": {
            "description": "Reference materials, codes, standards, and research",
            "subdirs": ["Codes_Standards", "Product_Information", "Research"]
        },
        "11_Presentations": {
            "description": "Client presentations and public meeting materials",
            "subdirs": ["Client_Meetings", "Public_Presentations", "Board_Meetings"]
        },
        "12_Marketing": {
            "description": "Marketing materials and award submissions",
            "subdirs": ["Photography", "Renderings", "Awards", "Publications"]
        },
        "13_Archive": {
            "description": "Archived project materials and superseded documents",
            "subdirs": ["Superseded", "Old_Versions", "Reference_Only"]
        },
        "14_Software_Data": {
            "description": "Native software files and project databases",
            "subdirs": ["CAD_Files", "BIM_Models", "Databases", "Analysis_Files"]
        }
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the AEC Directory Manager.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger or logging.getLogger(__name__)
        self.structure_version = "1.0"
    
    def create_project_structure(
        self, 
        project_number: str, 
        project_name: str, 
        base_path: str
    ) -> Dict[str, Union[bool, str, List[str]]]:
        """
        Create the complete AEC directory structure for a new project.
        
        Args:
            project_number: Unique project identifier
            project_name: Human-readable project name
            base_path: Root path where project structure will be created
            
        Returns:
            Dictionary containing success status, project path, and any errors
        """
        try:
            # Create project root directory
            project_folder_name = f"{project_number}_{project_name.replace(' ', '_')}"
            project_path = Path(base_path) / project_folder_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            created_dirs = []
            errors = []
            
            # Create all standard directories and subdirectories
            for main_dir, config in self.STANDARD_STRUCTURE.items():
                main_path = project_path / main_dir
                
                try:
                    main_path.mkdir(exist_ok=True)
                    created_dirs.append(str(main_path))
                    
                    # Create subdirectories
                    for subdir in config.get("subdirs", []):
                        sub_path = main_path / subdir
                        sub_path.mkdir(exist_ok=True)
                        created_dirs.append(str(sub_path))
                        
                except Exception as e:
                    error_msg = f"Failed to create {main_path}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Create project metadata file
            metadata = {
                "project_number": project_number,
                "project_name": project_name,
                "created_date": datetime.now().isoformat(),
                "structure_version": self.structure_version,
                "base_path": str(project_path),
                "created_directories": created_dirs
            }
            
            metadata_path = project_path / ".aec_project_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Created project structure at {project_path}")
            
            return {
                "success": len(errors) == 0,
                "project_path": str(project_path),
                "created_directories": created_dirs,
                "errors": errors,
                "metadata_file": str(metadata_path)
            }
            
        except Exception as e:
            error_msg = f"Failed to create project structure: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "project_path": "",
                "created_directories": [],
                "errors": [error_msg],
                "metadata_file": ""
            }
    
    def validate_structure(self, project_path: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate the integrity of an existing project directory structure.
        
        Args:
            project_path: Path to the project root directory
            
        Returns:
            Dictionary containing validation results and missing/extra directories
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            return {
                "valid": False,
                "missing_dirs": ["Project path does not exist"],
                "extra_dirs": [],
                "structure_version": None
            }
        
        missing_dirs = []
        extra_dirs = []
        existing_dirs = set()
        
        # Check for all required directories
        for main_dir, config in self.STANDARD_STRUCTURE.items():
            main_path = project_path / main_dir
            
            if not main_path.exists():
                missing_dirs.append(main_dir)
            else:
                existing_dirs.add(main_dir)
                
                # Check subdirectories
                for subdir in config.get("subdirs", []):
                    sub_path = main_path / subdir
                    if not sub_path.exists():
                        missing_dirs.append(f"{main_dir}/{subdir}")
        
        # Check for extra directories
        for item in project_path.iterdir():
            if item.is_dir() and item.name not in self.STANDARD_STRUCTURE:
                if not item.name.startswith('.'):  # Ignore hidden directories
                    extra_dirs.append(item.name)
        
        # Get structure version from metadata
        structure_version = None
        metadata_path = project_path / ".aec_project_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    structure_version = metadata.get("structure_version")
            except Exception as e:
                self.logger.warning(f"Could not read metadata file: {e}")
        
        is_valid = len(missing_dirs) == 0
        
        return {
            "valid": is_valid,
            "missing_dirs": missing_dirs,
            "extra_dirs": extra_dirs,
            "structure_version": structure_version,
            "existing_dirs": list(existing_dirs)
        }
    
    def repair_structure(self, project_path: str) -> List[str]:
        """
        Repair missing directories in an existing project structure.
        
        Args:
            project_path: Path to the project root directory
            
        Returns:
            List of directories that were created during repair
        """
        project_path = Path(project_path)
        created_dirs = []
        
        if not project_path.exists():
            self.logger.error(f"Project path does not exist: {project_path}")
            return created_dirs
        
        validation = self.validate_structure(str(project_path))
        
        for missing_dir in validation["missing_dirs"]:
            try:
                if "/" in missing_dir:
                    # It's a subdirectory
                    dir_path = project_path / missing_dir
                else:
                    # It's a main directory
                    dir_path = project_path / missing_dir
                
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))
                self.logger.info(f"Created missing directory: {dir_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to create directory {missing_dir}: {e}")
        
        return created_dirs
    
    def get_folder_metadata(self, folder_path: str) -> Dict[str, Union[str, int, datetime]]:
        """
        Extract metadata information about a specific folder.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Dictionary containing folder metadata
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            return {"error": "Folder does not exist"}
        
        try:
            stat_info = folder_path.stat()
            
            # Count files and subdirectories
            file_count = 0
            dir_count = 0
            total_size = 0
            
            if folder_path.is_dir():
                for item in folder_path.rglob("*"):
                    if item.is_file():
                        file_count += 1
                        try:
                            total_size += item.stat().st_size
                        except (OSError, FileNotFoundError):
                            pass  # Skip files that can't be accessed
                    elif item.is_dir():
                        dir_count += 1
            
            return {
                "folder_name": folder_path.name,
                "folder_path": str(folder_path),
                "created_time": datetime.fromtimestamp(stat_info.st_ctime),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime),
                "file_count": file_count,
                "directory_count": dir_count,
                "total_size_bytes": total_size,
                "is_aec_standard": folder_path.name in self.STANDARD_STRUCTURE
            }
            
        except Exception as e:
            self.logger.error(f"Error getting folder metadata: {e}")
            return {"error": str(e)}
    
    def update_structure_version(self, project_path: str, new_version: str) -> bool:
        """
        Update the structure version in project metadata.
        
        Args:
            project_path: Path to the project root directory
            new_version: New version string
            
        Returns:
            True if successful, False otherwise
        """
        metadata_path = Path(project_path) / ".aec_project_metadata.json"
        
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata["structure_version"] = new_version
                metadata["last_updated"] = datetime.now().isoformat()
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Updated structure version to {new_version}")
                return True
            else:
                self.logger.error("Metadata file does not exist")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update structure version: {e}")
            return False
    
    def get_structure_info(self) -> Dict[str, Union[str, Dict]]:
        """
        Get information about the standard AEC directory structure.
        
        Returns:
            Dictionary containing structure version and directory information
        """
        return {
            "version": self.structure_version,
            "total_directories": len(self.STANDARD_STRUCTURE),
            "structure": self.STANDARD_STRUCTURE
        }