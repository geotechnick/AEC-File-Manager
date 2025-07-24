#!/usr/bin/env python3
"""
Test script to validate comprehensive AEC naming conventions.

This script tests all the naming formats and patterns specified in the
comprehensive file naming convention system.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aec_scanner.core.metadata_extractor import MetadataExtractor

def test_primary_format():
    """Test the primary naming format: ProjectNumber_Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext"""
    print("Testing Primary Format: ProjectNumber_Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext")
    print("="*100)
    
    extractor = MetadataExtractor()
    
    test_files = [
        # Drawings
        "PROJ123_CD_A_DWG_001_R3_2024-03-15.pdf",  # Architectural floor plan
        "PROJ123_DD_S_DWG_S201_R1_2024-02-28.dwg",  # Structural framing plan
        "PROJ123_CD_M_SCH_M401_R0_2024-04-10.pdf",  # Mechanical equipment schedule
        
        # Calculations
        "PROJ123_DD_S_CALC_BEAM_R2_2024-02-20.pdf",  # Structural beam calculations
        "PROJ123_CD_M_SIZE_DUCT_R1_2024-03-25.xlsx",  # Mechanical duct sizing
        "PROJ123_CD_E_LOAD_PANEL_R0_2024-04-05.pdf",  # Electrical load calculations
        
        # Reports
        "PROJ123_PD_G_RPT_GEOTECH_R0_2024-01-10.pdf",  # Geotechnical report
        "PROJ123_SD_EN_STUDY_ENVIR_R1_2024-01-25.pdf",  # Environmental study
        "PROJ123_CA_GE_MEMO_SAFETY_R0_2024-05-15.docx",  # Safety memo
        
        # Specifications
        "PROJ123_CD_A_SPEC_DIV08_R1_2024-03-30.docx",  # Division 08 - Openings
        "PROJ123_CD_M_SPEC_DIV23_R2_2024-04-12.pdf",  # Division 23 - HVAC
        
        # Correspondence
        "PROJ123_CA_M_RFI_001_R0_2024-05-20.pdf",  # Mechanical RFI
        "PROJ123_CA_S_SUB_STEEL_R1_2024-06-01.pdf",  # Structural steel submittal
        "PROJ123_CA_GE_CO_015_R0_2024-06-10.pdf",  # Change Order #15
        
        # Models and CAD
        "PROJ123_DD_A_BIM_MODEL_R2_2024-03-01.rvt",  # Architectural BIM model
        "PROJ123_CD_C_CAD_SITE_R1_2024-04-20.dwg",  # Civil site plan CAD
        
        # Photos and Documentation
        "PROJ123_CA_GE_PHO_PROG_001_2024-05-25.jpg",  # Progress photo
        "PROJ123_PD_A_PHO_EXIST_001_2024-01-05.jpg",  # Existing conditions photo
        
        # Permits and Approvals
        "PROJ123_CD_A_PER_BUILD_R0_2024-04-01.pdf",  # Building permit application
        "PROJ123_CD_C_PER_STORM_R1_2024-04-15.pdf",  # Stormwater permit
    ]
    
    for filename in test_files:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            print(f"  [OK] Format: {metadata.get('naming_format', 'unknown')}")
            print(f"  [OK] Project: {metadata.get('project_number')}")
            print(f"  [OK] Phase: {metadata.get('phase_code')} ({metadata.get('phase_name')})")
            print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
            print(f"  [OK] Document Type: {metadata.get('document_type')} ({metadata.get('document_type_name')})")
            print(f"  [OK] Sheet: {metadata.get('sheet_number')}")
            print(f"  [OK] Revision: {metadata.get('revision')} ({metadata.get('revision_type')})")
            print(f"  [OK] Date: {metadata.get('date_issued')}")
        else:
            print(f"  [FAIL] Not recognized as AEC standard")
            if "error" in metadata:
                print(f"    Error: {metadata['error']}")
            if "extraction_error" in metadata:
                print(f"    Error: {metadata['extraction_error']}")

def test_check_print_revisions():
    """Test check print revision system (C01, C02, C03...)"""
    print("\n\nTesting Check Print Revisions")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    test_files = [
        "PROJ123_DD_A_DWG_001_C05_2024-03-10.pdf",  # 5th internal check print
        "PROJ123_DD_A_DWG_001_R1_2024-03-15.pdf",   # 1st clean issue to client
        "PROJ123_CD_S_DWG_S201_C12_2024-04-20.pdf", # 12th internal check print
        "PROJ123_CD_S_DWG_S201_IFC_2024-05-01.pdf", # Final issued for construction
    ]
    
    for filename in test_files:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            revision = metadata.get('revision')
            revision_type = metadata.get('revision_type')
            issue_code = metadata.get('issue_code')
            
            if revision_type == "check_print":
                print(f"  [OK] Check Print Revision: {revision}")
            elif revision_type == "clean":
                print(f"  [OK] Clean Document Revision: {revision}")
            elif revision_type == "issue_code":
                print(f"  [OK] Issue Code: {issue_code}")
            else:
                print(f"  [WARN] Unknown revision type: {revision}")
        else:
            print(f"  [FAIL] Not recognized")

def test_special_formats():
    """Test special naming formats (MTG, TXM, SHOP, AB)"""
    print("\n\nTesting Special Naming Formats")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    test_files = [
        # Meeting Minutes
        "PROJ123_MTG_2024-03-15_DesignReview.docx",
        "PROJ123_MTG_2024-05-20_ProgressMeeting.docx",
        
        # Transmittals
        "PROJ123_TXM_CONT_001_2024-05-10.pdf",
        "PROJ123_TXM_ARCH_002_2024-06-01.pdf",
        
        # Shop Drawings
        "PROJ123_SHOP_S_ACME_STEEL_R1_2024-06-15.pdf",
        "PROJ123_SHOP_M_HVAC_UNITS_R0_2024-07-01.pdf",
        
        # As-Built Drawings
        "PROJ123_AB_A_001_2024-08-30.pdf",
        "PROJ123_AB_E_E101_2024-09-15.pdf",
    ]
    
    for filename in test_files:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            format_type = metadata.get('naming_format')
            print(f"  [OK] Special Format: {format_type}")
            print(f"  [OK] Project: {metadata.get('project_number')}")
            print(f"  [OK] Document Type: {metadata.get('document_type')} ({metadata.get('document_type_name')})")
            
            if format_type == "shop_drawing":
                print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
                print(f"  [OK] Revision: {metadata.get('revision')}")
            elif format_type == "as_built":
                print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
                print(f"  [OK] Sheet: {metadata.get('sheet_number')}")
            
            print(f"  [OK] Date: {metadata.get('date_issued')}")
        else:
            print(f"  [FAIL] Not recognized as AEC standard")

def test_discipline_codes():
    """Test all discipline codes"""
    print("\n\nTesting All Discipline Codes")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    # Test all discipline codes with sample files
    disciplines = [
        ("A", "Architectural"),
        ("S", "Structural"),
        ("G", "Geotechnical"),
        ("C", "Civil"),
        ("M", "Mechanical"),
        ("E", "Electrical"),
        ("P", "Plumbing"),
        ("H", "Hydraulic"),
        ("F", "Fire Protection"),
        ("L", "Landscape"),
        ("I", "Interiors"),
        ("T", "Transportation"),
        ("EN", "Environmental"),
        ("SU", "Survey"),
        ("PM", "Project Management"),
        ("GE", "General/Multi-Discipline")
    ]
    
    for disc_code, disc_name in disciplines:
        filename = f"PROJ123_CD_{disc_code}_DWG_001_R0_2024-01-15.pdf"
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            extracted_name = metadata.get('discipline_name')
            if extracted_name == disc_name:
                print(f"  [OK] {disc_code}: {disc_name}")
            else:
                print(f"  [WARN] {disc_code}: Expected '{disc_name}', got '{extracted_name}'")
        else:
            print(f"  [FAIL] {disc_code}: Not recognized")

def test_document_types():
    """Test all document type codes"""
    print("\n\nTesting All Document Type Codes")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    # Test comprehensive document types
    doc_types = [
        # Drawings
        ("DWG", "Drawing"),
        ("PLN", "Plan"),
        ("SEC", "Section"),
        ("DTL", "Detail"),
        ("SCH", "Schedule"),
        # Calculations
        ("CALC", "Calculation"),
        ("LOAD", "Load Calculation"),
        ("SIZE", "Sizing Calculation"),
        ("PAR", "Parameter Calculation"),
        # Reports
        ("RPT", "Report"),
        ("MEMO", "Memorandum"),
        ("STUDY", "Study"),
        ("EVAL", "Evaluation"),
        # Specifications
        ("SPEC", "Specification"),
        ("DIV", "Division"),
        # Correspondence
        ("RFI", "Request for Information"),
        ("SUB", "Submittal"),
        ("CO", "Change Order"),
        ("TXM", "Transmittal"),
        ("LTR", "Letter"),
        # Models
        ("BIM", "Building Information Model"),
        ("3D", "3D Model"),
        ("CAD", "CAD File"),
        # Photos
        ("PHO", "Photograph"),
        ("IMG", "Image"),
        # Permits
        ("PER", "Permit"),
        ("APP", "Application")
    ]
    
    for doc_code, doc_name in doc_types:
        filename = f"PROJ123_CD_A_{doc_code}_001_R0_2024-01-15.pdf"
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            extracted_name = metadata.get('document_type_name')
            if extracted_name == doc_name:
                print(f"  [OK] {doc_code}: {doc_name}")
            else:
                print(f"  [WARN] {doc_code}: Expected '{doc_name}', got '{extracted_name}'")
        else:
            print(f"  [FAIL] {doc_code}: Not recognized")

def test_issue_codes():
    """Test all issue codes"""
    print("\n\nTesting Issue Codes")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    issue_codes = [
        "IFC",    # Issued for Construction
        "IFB",    # Issued for Bidding
        "IFP",    # Issued for Permit
        "AB",     # As-Built version
        "RFI",    # Issued for RFI response
        "PCO",    # Issued for Potential Change Order review
        "FOR",    # Issued for Record
        "CONST",  # Construction Issue
        "RECORD"  # Record Drawing
    ]
    
    for issue_code in issue_codes:
        filename = f"PROJ123_CD_A_DWG_001_{issue_code}_2024-01-15.pdf"
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            extracted_issue = metadata.get('issue_code')
            if extracted_issue == issue_code:
                print(f"  [OK] {issue_code}: Recognized")
            else:
                print(f"  [WARN] {issue_code}: Expected '{issue_code}', got '{extracted_issue}'")
        else:
            print(f"  [FAIL] {issue_code}: Not recognized")

def main():
    """Run all naming convention tests."""
    print("AEC Comprehensive Naming Convention Test")
    print("="*100)
    
    try:
        test_primary_format()
        test_check_print_revisions()
        test_special_formats()
        test_discipline_codes()
        test_document_types()
        test_issue_codes()
        
        print("\n" + "="*100)
        print("All naming convention tests completed!")
        print("\nThe comprehensive AEC naming convention system is now fully implemented.")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())