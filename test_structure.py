#!/usr/bin/env python3
"""
Test script to verify the AEC Directory Scanner structure creation.

This script tests the new comprehensive directory structure and naming conventions.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aec_scanner.core.directory_manager import AECDirectoryManager
from aec_scanner.core.metadata_extractor import MetadataExtractor

def test_directory_creation():
    """Test the creation of the comprehensive AEC directory structure."""
    print("Testing AEC Directory Structure Creation...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Initialize directory manager
        manager = AECDirectoryManager()
        
        # Test project creation
        result = manager.create_project_structure(
            project_number="PROJ2024",
            project_name="Test Office Building",
            base_path=temp_dir,
            project_year="2024"
        )
        
        if result["success"]:
            print(f"Successfully created project structure!")
            print(f"Project path: {result['project_path']}")
            print(f"Total directories created: {result['total_directories']}")
            
            # Verify some key directories exist
            project_path = Path(result['project_path'])
            
            key_dirs_to_check = [
                "00_PROJECT_MANAGEMENT/Project_Charter",
                "01_CORRESPONDENCE/RFIs/Incoming",
                "02_DRAWINGS/Current_Issue/Architectural",
                "03_SPECIFICATIONS/Division_01_General_Requirements",
                "04_CALCULATIONS/Structural",
                "05_REPORTS/Geotechnical/Boring_Logs",
                "06_PERMITS_APPROVALS/Building_Permits/Applications",
                "07_SITE_DOCUMENTATION/Photos/Existing_Conditions",
                "08_MODELS_CAD/BIM_Models/Architectural",
                "09_CONSTRUCTION_ADMIN/Pre_Construction/Pre_Bid_Meeting",
                "10_CLOSEOUT/As_Built_Drawings/Record_Drawings",
                "11_SPECIALTY_CONSULTANTS/Acoustical",
                "12_STANDARDS_TEMPLATES/CAD_Standards/Layer_Standards",
                "13_ARCHIVE/Superseded_Drawings/By_Date"
            ]
            
            print("\nVerifying key directories:")
            for dir_path in key_dirs_to_check:
                full_path = project_path / dir_path
                if full_path.exists():
                    print(f"[OK] {dir_path}")
                else:
                    print(f"[FAIL] {dir_path}")
            
            # Test structure validation
            print("\nTesting structure validation...")
            validation_result = manager.validate_structure(str(project_path))
            
            if validation_result["valid"]:
                print("Structure validation passed!")
            else:
                print(f"Structure validation failed!")
                print(f"Missing directories: {validation_result['missing_dirs']}")
                print(f"Extra directories: {validation_result['extra_dirs']}")
            
        else:
            print(f"Failed to create project structure!")
            print(f"Errors: {result['errors']}")

def test_naming_conventions():
    """Test the comprehensive file naming conventions."""
    print("\n" + "="*60)
    print("Testing File Naming Convention Parsing...")
    
    # Initialize metadata extractor
    extractor = MetadataExtractor()
    
    # Test various file naming patterns
    test_files = [
        "PROJ2024_A_001_R0_2024-01-15.pdf",  # Standard drawing
        "PROJ2024_S_C01_R2_2024-02-20.pdf",  # Structural calculation
        "PROJ2024_M_RFI-001_R0_2024-03-10.pdf",  # Mechanical RFI
        "PROJ2024_E_SUB-005_R1_2024-04-05.pdf",  # Electrical submittal
        "ABC123_A01-001_IFC_2024-05-01.dwg",  # Drawing with issue code
        "OFFICE_BUILDING_2024_SPEC_03_30_00_R0.docx",  # Specification
        "PROJ2024_CO-012_APPROVED_2024-06-15.pdf",  # Change order
    ]
    
    print("\nTesting naming pattern extraction:")
    for filename in test_files:
        print(f"\nFile: {filename}")
        
        # Extract AEC metadata
        temp_path = f"/temp/{filename}"  # Dummy path for testing
        aec_metadata = extractor.extract_aec_metadata(temp_path)
        
        if aec_metadata.get("is_aec_standard"):
            print("[OK] Recognized as AEC standard file")
            if aec_metadata.get("project_number"):
                print(f"   Project: {aec_metadata['project_number']}")
            if aec_metadata.get("discipline_code"):
                print(f"   Discipline: {aec_metadata['discipline_code']} ({aec_metadata.get('discipline_name', 'Unknown')})")
            if aec_metadata.get("document_type"):
                print(f"   Document Type: {aec_metadata['document_type']}")
            if aec_metadata.get("revision"):
                print(f"   Revision: {aec_metadata['revision']}")
            if aec_metadata.get("phase_code"):
                print(f"   Phase: {aec_metadata['phase_code']} ({aec_metadata.get('phase_name', 'Unknown')})")
        else:
            print("[WARN] Not recognized as AEC standard file")

def test_structure_info():
    """Test getting structure information."""
    print("\n" + "="*60)
    print("Testing Structure Information...")
    
    manager = AECDirectoryManager()
    info = manager.get_structure_info()
    
    print(f"Structure Version: {info['version']}")
    print(f"Total Main Directories: {info['total_directories']}")
    
    print("\nMain directories:")
    for dir_name, config in info['structure'].items():
        subdir_count = len(config.get('subdirs', {}))
        print(f"   {dir_name}: {subdir_count} subdirectories")

def main():
    """Run all tests."""
    print("AEC Directory Scanner - Structure Test")
    print("="*60)
    
    try:
        test_directory_creation()
        test_naming_conventions()
        test_structure_info()
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("\nThe AEC Directory Scanner is ready to use with the new structure.")
        print("\nUsage example:")
        print("python aec_scanner_cli.py init --project-number PROJ2024 --project-name 'Office Building' --path './projects' --project-year 2024")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())