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
        "00_PROJECT_MANAGEMENT": {
            "description": "Project administration, contracts, correspondence",
            "subdirs": {
                "Project_Charter": [],
                "Proposals": ["Technical", "Commercial", "Marketing"],
                "Contracts": ["Prime_Contract", "Subcontracts", "Amendments"],
                "Project_Schedule": ["Master_Schedule", "Milestone_Schedule", "Look_Ahead"],
                "Budget_Cost_Control": ["Budget_Tracking", "Cost_Reports", "Invoicing"],
                "Meeting_Minutes": ["Kickoff", "Design_Reviews", "Progress_Meetings", "Coordination"],
                "Project_Team": ["Contact_Lists", "Org_Charts", "Roles_Responsibilities"],
                "Risk_Management": [],
                "Quality_Assurance": []
            }
        },
        "01_CORRESPONDENCE": {
            "description": "Project correspondence and communication",
            "subdirs": {
                "RFIs": ["Incoming", "Outgoing", "Logs"],
                "Submittals": ["Incoming", "Outgoing", "Logs", "Review_Status"],
                "Change_Orders": ["Requests", "Approved", "Logs"],
                "Transmittals": [],
                "Notice_Letters": [],
                "Progress_Reports": [],
                "Email_Archives": []
            }
        },
        "02_DRAWINGS": {
            "description": "Design drawings and documentation",
            "subdirs": {
                "Current_Issue": [
                    "Architectural", "Structural", "Civil", "Geotechnical", "Mechanical",
                    "Electrical", "Plumbing", "Fire_Protection", "Landscape", "Interiors", "Specialty"
                ],
                "Superseded": ["By_Date", "By_Revision"],
                "Markups": ["Review_Comments", "Field_Sketches"],
                "Record_Drawings": [],
                "Shop_Drawings": ["Submitted", "Under_Review", "Approved"]
            }
        },
        "03_SPECIFICATIONS": {
            "description": "Technical specifications following CSI MasterFormat",
            "subdirs": {
                "Division_00_Bidding_Requirements": [
                    "00_01_Instructions_to_Bidders", "00_02_Information_Available_to_Bidders",
                    "00_41_Bid_Forms", "00_43_Subcontractor_List", "00_45_Quantities", "00_52_Agreement_Forms"
                ],
                "Division_01_General_Requirements": [
                    "01_01_Summary_of_Work", "01_05_Coordination_Procedures", "01_07_Abbreviations_Definitions",
                    "01_10_Reference_Standards", "01_25_Measurement_Payment", "01_29_Progress_Schedule",
                    "01_30_Submittals", "01_31_Project_Management", "01_32_Construction_Progress",
                    "01_33_Submittal_Procedures", "01_35_Special_Procedures", "01_40_Quality_Requirements",
                    "01_45_Quality_Control", "01_50_Temporary_Facilities", "01_55_Traffic_Regulation",
                    "01_57_Temporary_Controls", "01_60_Products_Materials", "01_70_Contract_Closeout",
                    "01_73_Execution", "01_74_Cleaning", "01_77_Record_Documents", "01_78_Closeout_Submittals"
                ],
                "Division_02_Site_Preparation": [
                    "02_05_Common_Work_Results", "02_10_Subsurface_Investigation", "02_20_Demolition",
                    "02_30_Site_Clearing", "02_40_Demolition_Modifications", "02_50_Site_Remediation"
                ],
                "Division_03_Concrete": [
                    "03_05_Common_Work_Results", "03_10_Concrete_Forming", "03_20_Concrete_Reinforcing",
                    "03_30_Cast_in_Place_Concrete", "03_40_Precast_Concrete", "03_50_Cast_Decks", "03_60_Grouting"
                ],
                "Division_04_Masonry": [
                    "04_05_Common_Work_Results", "04_20_Unit_Masonry", "04_40_Stone",
                    "04_50_Refractory_Masonry", "04_70_Manufactured_Masonry"
                ],
                "Division_05_Metals": [
                    "05_05_Common_Work_Results", "05_10_Structural_Steel", "05_20_Steel_Joist_Decking",
                    "05_30_Steel_Decking", "05_40_Cold_Formed_Steel", "05_50_Metal_Fabrications"
                ],
                "Division_06_Wood_Plastics": [
                    "06_05_Common_Work_Results", "06_10_Rough_Carpentry", "06_20_Finish_Carpentry",
                    "06_40_Architectural_Woodwork", "06_50_Structural_Plastics"
                ],
                "Division_07_Thermal_Moisture": [
                    "07_05_Common_Work_Results", "07_10_Dampproofing_Waterproofing", "07_20_Thermal_Protection",
                    "07_30_Steep_Slope_Roofing", "07_40_Roofing_Siding_Panels", "07_50_Membrane_Roofing",
                    "07_60_Flashing_Sheet_Metal", "07_70_Roofing_Specialties", "07_80_Fire_Smoke_Protection",
                    "07_90_Joint_Protection"
                ],
                "Division_08_Openings": [
                    "08_05_Common_Work_Results", "08_10_Doors_Frames", "08_20_Wood_Plastic_Doors",
                    "08_30_Specialty_Doors", "08_40_Entrances_Storefronts", "08_50_Windows",
                    "08_60_Roof_Windows_Skylights", "08_70_Hardware", "08_80_Glazing"
                ],
                "Division_09_Finishes": [
                    "09_05_Common_Work_Results", "09_10_Lath_Plaster", "09_20_Gypsum_Board", "09_30_Tiling",
                    "09_40_Terrazzo", "09_50_Ceilings", "09_60_Flooring", "09_70_Wall_Finishes", "09_80_Acoustic_Treatment"
                ],
                "Division_10_Specialties": [
                    "10_05_Common_Work_Results", "10_10_Information_Specialties", "10_20_Interior_Specialties",
                    "10_30_Fireplaces_Stoves", "10_40_Safety_Specialties", "10_50_Storage_Specialties", "10_70_Exterior_Specialties"
                ],
                "Division_11_Equipment": [
                    "11_05_Common_Work_Results", "11_10_Vehicle_Pedestrian_Equipment", "11_20_Office_Equipment",
                    "11_30_Residential_Equipment", "11_40_Foodservice_Equipment", "11_50_Educational_Scientific_Equipment",
                    "11_60_Entertainment_Recreation_Equipment", "11_70_Healthcare_Equipment", "11_80_Collection_Storage_Equipment"
                ],
                "Division_12_Furnishings": [
                    "12_05_Common_Work_Results", "12_10_Art", "12_20_Window_Treatments", "12_30_Casework",
                    "12_40_Furnishings_Accessories", "12_50_Furniture", "12_60_Multiple_Seating"
                ],
                "Division_13_Special_Construction": [
                    "13_05_Common_Work_Results", "13_10_Special_Facility_Components", "13_20_Special_Purpose_Rooms",
                    "13_30_Special_Structures", "13_40_Integrated_Construction", "13_50_Special_Instrumentation"
                ],
                "Division_14_Conveying_Equipment": [
                    "14_05_Common_Work_Results", "14_10_Dumbwaiters", "14_20_Elevators",
                    "14_30_Escalators_Moving_Walks", "14_40_Lifts", "14_70_Turntables", "14_80_Scaffolding"
                ],
                "Division_15_Mechanical": [
                    "15_05_Common_Work_Results", "15_10_General_Provisions", "15_20_Process_Piping",
                    "15_30_Fire_Protection_Piping", "15_40_Plumbing_Systems", "15_50_Heating_Systems",
                    "15_60_Cooling_Systems", "15_70_Air_Handling_Systems", "15_80_Air_Distribution_Systems",
                    "15_90_Controls_Instrumentation"
                ],
                "Division_16_Electrical": [
                    "16_05_Common_Work_Results", "16_10_General_Provisions", "16_20_Low_Voltage_Distribution",
                    "16_30_Medium_Voltage_Distribution", "16_40_Service_Distribution", "16_50_Lighting",
                    "16_60_Special_Systems", "16_70_Communications", "16_80_Sound_Video", "16_90_Controls_Instrumentation"
                ],
                "Division_31_Earthwork": [
                    "31_05_Common_Work_Results", "31_10_Site_Clearing", "31_20_Earth_Moving", "31_30_Earthwork_Methods",
                    "31_40_Shoring_Underpinning", "31_50_Excavation_Support", "31_60_Special_Foundations", "31_70_Tunneling"
                ],
                "Division_32_Exterior_Improvements": [
                    "32_05_Common_Work_Results", "32_10_Bases_Ballasts_Pavements", "32_20_Concrete_Paving",
                    "32_30_Site_Improvements", "32_40_Planting", "32_50_Ponds_Reservoirs", "32_60_Piped_Utilities",
                    "32_70_Wetlands", "32_80_Irrigation", "32_90_Planting"
                ],
                "Division_33_Utilities": [
                    "33_05_Common_Work_Results", "33_10_Water_Utilities", "33_20_Wells", "33_30_Sanitary_Sewerage_Utilities",
                    "33_40_Storm_Drainage_Utilities", "33_50_Fuel_Distribution", "33_60_Hydro_Utilities",
                    "33_70_Electrical_Utilities", "33_80_Communications_Utilities"
                ],
                "Division_34_Transportation": [
                    "34_05_Common_Work_Results", "34_10_Guideways", "34_20_Traction_Power", "34_30_Transportation_Signals",
                    "34_40_Transportation_Control", "34_50_Transportation_Fare_Collection", "34_60_Automobile_Service_Equipment",
                    "34_70_Vehicle_Barriers", "34_80_Bridges"
                ],
                "Division_35_Waterway_Marine": [
                    "35_05_Common_Work_Results", "35_10_Waterway_Construction", "35_20_Waterway_Equipment",
                    "35_30_Coastal_Construction", "35_40_Waterway_Structures", "35_50_Marine_Construction", "35_70_Dam_Construction"
                ],
                "Division_40_Process_Integration": [
                    "40_05_Common_Work_Results", "40_10_Gas_Liquid_Handling", "40_20_Process_Heating_Cooling",
                    "40_30_Process_Gas_Liquid_Treatment", "40_40_Process_Integration", "40_90_Instrumentation_Control"
                ],
                "Division_41_Material_Processing": [
                    "41_05_Common_Work_Results", "41_10_Bulk_Material_Processing", "41_20_Material_Preparation",
                    "41_30_Manufacturing", "41_40_Container_Processing"
                ],
                "Division_43_Process_Gas_Liquid": [
                    "43_05_Common_Work_Results", "43_10_Gas_Generation", "43_20_Gas_Cleaning_Separation",
                    "43_30_Gas_Mixing_Blending", "43_40_Liquid_Processing", "43_50_Liquid_Storage"
                ],
                "Division_44_Pollution_Control": [
                    "44_05_Common_Work_Results", "44_10_Air_Pollution_Control", "44_20_Noise_Control",
                    "44_30_Water_Pollution_Control", "44_40_Solid_Waste_Control", "44_50_Remediation"
                ],
                "Division_46_Water_Wastewater": [
                    "46_05_Common_Work_Results", "46_10_Water_Treatment", "46_20_Potable_Water_Treatment",
                    "46_30_Wastewater_Treatment", "46_40_Ozone_Treatment", "46_50_Pool_Fountain_Equipment",
                    "46_60_Chemical_Material_Feed", "46_70_Water_Wastewater_Equipment", "46_80_Water_Utility_Transmission"
                ],
                "Division_48_Electrical_Power": [
                    "48_05_Common_Work_Results", "48_10_Electrical_Power_Generation", "48_20_Electrical_Power_Transmission",
                    "48_30_Electrical_Power_Distribution", "48_40_Electrical_Power_Control", "48_50_Electrical_Power_Equipment",
                    "48_80_Electrical_Power_Monitoring"
                ],
                "Master_Specification": ["Section_Templates", "Standard_Language", "Specification_Guidelines", "Quality_Control_Checklists"]
            }
        },
        "04_CALCULATIONS": {
            "description": "Engineering calculations and analysis documents",
            "subdirs": {
                "Structural": [],
                "Geotechnical": [],
                "Civil": [],
                "Environmental": [],
                "Hydraulics": [],
                "Mechanical": [],
                "Electrical": [],
                "Plumbing": [],
                "Fire_Protection": [],
                "Transportation": []
            }
        },
        "05_REPORTS": {
            "description": "Technical reports and studies",
            "subdirs": {
                "Geotechnical": ["Boring_Logs", "Lab_Results", "Recommendations"],
                "Environmental": ["Phase_I_ESA", "Phase_II_ESA", "Wetland_Delineation", "Contamination_Assessment"],
                "Survey": ["Boundary", "Topographic", "ALTA", "Construction_Layout"],
                "Testing_Inspection": ["Materials_Testing", "Special_Inspection", "Commissioning", "Quality_Control"],
                "Traffic_Studies": [],
                "Utility_Studies": [],
                "Feasibility_Studies": [],
                "Code_Analysis": [],
                "Peer_Review": []
            }
        },
        "06_PERMITS_APPROVALS": {
            "description": "Permits and regulatory approvals",
            "subdirs": {
                "Building_Permits": ["Applications", "Approved", "Correspondence"],
                "Zoning": ["Variance_Requests", "Special_Use", "Site_Plan_Approval"],
                "Environmental": ["NPDES", "Wetland_Permits", "Air_Quality", "Waste_Permits"],
                "Utility_Permits": ["Water_Sewer", "Electric", "Gas", "Telecommunications"],
                "Transportation": ["Access_Permits", "Traffic_Signal", "Right_of_Way"],
                "Fire_Department": [],
                "Health_Department": []
            }
        },
        "07_SITE_DOCUMENTATION": {
            "description": "Site documentation and field records",
            "subdirs": {
                "Photos": ["Existing_Conditions", "Progress_Photos", "Site_Safety", "Quality_Issues", "Final_Completion"],
                "Site_Visits": ["Observation_Reports", "Punch_Lists", "Field_Notes"],
                "Surveys": ["Pre_Construction", "Construction_Layout", "As_Built_Survey"],
                "Video_Documentation": []
            }
        },
        "08_MODELS_CAD": {
            "description": "Digital models and CAD files",
            "subdirs": {
                "BIM_Models": ["Architectural", "Structural", "MEP", "Civil", "Federated", "Clash_Detection"],
                "CAD_Files": ["Native_Files", "DWG_Exchange", "Standards"],
                "3D_Models": ["Visualization", "Renderings", "Animations"],
                "GIS_Data": [],
                "Point_Clouds": []
            }
        },
        "09_CONSTRUCTION_ADMIN": {
            "description": "Construction administration and oversight",
            "subdirs": {
                "Pre_Construction": ["Pre_Bid_Meeting", "Bid_Documents", "Addenda"],
                "Bidding": ["Bid_Submissions", "Bid_Analysis", "Award_Recommendation"],
                "Construction_Phase": ["Construction_Observation", "Payment_Applications", "Change_Order_Management", "Schedule_Updates", "Safety_Reports"],
                "Testing_Commissioning": ["System_Testing", "Commissioning_Reports", "Performance_Testing"],
                "Substantial_Completion": ["Punch_Lists", "Certificate_Occupancy", "Final_Inspection"]
            }
        },
        "10_CLOSEOUT": {
            "description": "Project closeout documentation",
            "subdirs": {
                "As_Built_Drawings": ["Record_Drawings", "Red_Line_Markups", "Final_As_Builts"],
                "Operation_Maintenance": ["O&M_Manuals", "Training_Materials", "Maintenance_Schedules"],
                "Warranties_Guarantees": ["Equipment_Warranties", "System_Warranties", "Warranty_Tracking"],
                "Certificates_Approvals": ["Certificate_Occupancy", "Fire_Department_Approval", "Health_Department", "Utility_Approvals"],
                "Final_Documentation": ["Project_Summary", "Lessons_Learned", "Client_Feedback"],
                "Lien_Releases": []
            }
        },
        "11_SPECIALTY_CONSULTANTS": {
            "description": "Specialty consultant deliverables",
            "subdirs": {
                "Acoustical": [],
                "Security": [],
                "Audio_Visual": [],
                "Kitchen_Equipment": [],
                "Code_Consultant": [],
                "Envelope_Consultant": [],
                "Sustainability_LEED": [],
                "Historic_Preservation": [],
                "Lighting_Design": [],
                "Cost_Estimating": []
            }
        },
        "12_STANDARDS_TEMPLATES": {
            "description": "Project standards and templates",
            "subdirs": {
                "CAD_Standards": ["Layer_Standards", "Text_Standards", "Title_Blocks"],
                "BIM_Standards": ["Modeling_Standards", "Family_Library", "Naming_Conventions"],
                "Drawing_Templates": [],
                "Specification_Templates": [],
                "Calculation_Templates": [],
                "Report_Templates": []
            }
        },
        "13_ARCHIVE": {
            "description": "Archived project materials and superseded documents",
            "subdirs": {
                "Superseded_Drawings": ["By_Date", "By_Revision"],
                "Previous_Versions": ["Specifications", "Calculations", "Reports"],
                "Old_Correspondence": ["By_Date", "By_Topic"],
                "Inactive_Files": [],
                "Project_History": []
            }
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
        base_path: str,
        project_year: Optional[str] = None
    ) -> Dict[str, Union[bool, str, List[str]]]:
        """
        Create the complete AEC directory structure for a new project.
        
        Args:
            project_number: Unique project identifier
            project_name: Human-readable project name
            base_path: Root path where project structure will be created
            project_year: Optional project year (defaults to current year)
            
        Returns:
            Dictionary containing success status, project path, and any errors
        """
        try:
            # Use current year if not provided
            if not project_year:
                project_year = str(datetime.now().year)
            
            # Create project root directory with year
            project_folder_name = f"{project_name.replace(' ', '_').upper()}_{project_year}"
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
                    
                    # Create subdirectories (now nested structure)
                    subdirs = config.get("subdirs", {})
                    if isinstance(subdirs, dict):
                        # New nested structure
                        for subdir_name, sub_subdirs in subdirs.items():
                            sub_path = main_path / subdir_name
                            sub_path.mkdir(exist_ok=True)
                            created_dirs.append(str(sub_path))
                            
                            # Create sub-subdirectories
                            for sub_subdir in sub_subdirs:
                                sub_sub_path = sub_path / sub_subdir
                                sub_sub_path.mkdir(exist_ok=True)
                                created_dirs.append(str(sub_sub_path))
                    else:
                        # Legacy flat structure (fallback)
                        for subdir in subdirs:
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
                "project_year": project_year,
                "created_date": datetime.now().isoformat(),
                "structure_version": self.structure_version,
                "base_path": str(project_path),
                "created_directories": created_dirs,
                "total_directories": len(created_dirs)
            }
            
            metadata_path = project_path / ".aec_project_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Created project structure at {project_path} with {len(created_dirs)} directories")
            
            return {
                "success": len(errors) == 0,
                "project_path": str(project_path),
                "created_directories": created_dirs,
                "errors": errors,
                "metadata_file": str(metadata_path),
                "total_directories": len(created_dirs)
            }
            
        except Exception as e:
            error_msg = f"Failed to create project structure: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "project_path": "",
                "created_directories": [],
                "errors": [error_msg],
                "metadata_file": "",
                "total_directories": 0
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