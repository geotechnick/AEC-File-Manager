#!/usr/bin/env python3
"""
Test the new naming format: Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext
With MMDDYY date format and no project number.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aec_scanner.core.metadata_extractor import MetadataExtractor

def test_new_primary_format():
    """Test the new primary format without project number and with MMDDYY dates."""
    print("Testing New Primary Format: Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext")
    print("="*90)
    
    extractor = MetadataExtractor()
    
    # Test files with new format (MMDDYY dates, no project number)
    test_files = [
        # Drawings
        "CD_A_DWG_001_R3_031524.pdf",  # Architectural floor plan
        "DD_S_DWG_S201_R1_022824.dwg",  # Structural framing plan
        "CD_M_SCH_M401_R0_041024.pdf",  # Mechanical equipment schedule
        
        # Calculations
        "DD_S_CALC_BEAM_R2_022024.pdf",  # Structural beam calculations
        "CD_M_SIZE_DUCT_R1_032524.xlsx",  # Mechanical duct sizing
        "CD_E_LOAD_PANEL_R0_040524.pdf",  # Electrical load calculations
        
        # Reports
        "PD_G_RPT_GEOTECH_R0_011024.pdf",  # Geotechnical report
        "SD_EN_STUDY_ENVIR_R1_012524.pdf",  # Environmental study
        "CA_GE_MEMO_SAFETY_R0_051524.docx",  # Safety memo
        
        # Check print revisions
        "DD_A_DWG_001_C05_031024.pdf",  # 5th internal check print
        "CD_S_DWG_S201_C12_042024.pdf",  # 12th internal check print
        
        # Issue codes
        "CD_S_DWG_S201_IFC_050124.pdf",  # Final issued for construction
    ]
    
    print("Primary Format Tests:")
    success_count = 0
    
    for filename in test_files:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard") and metadata.get("naming_format") == "primary":
            print(f"  [OK] Format: {metadata.get('naming_format')}")
            print(f"  [OK] Phase: {metadata.get('phase_code')} ({metadata.get('phase_name')})")
            print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
            print(f"  [OK] Document Type: {metadata.get('document_type')} ({metadata.get('document_type_name')})")
            print(f"  [OK] Sheet: {metadata.get('sheet_number')}")
            print(f"  [OK] Revision: {metadata.get('revision')} ({metadata.get('revision_type')})")
            print(f"  [OK] Date: {metadata.get('date_issued')}")
            success_count += 1
        else:
            print(f"  [FAIL] Not recognized as new primary format")
            if "error" in metadata:
                print(f"    Error: {metadata['error']}")
    
    print(f"\nPrimary Format Results: {success_count}/{len(test_files)} files parsed successfully")
    return success_count == len(test_files)

def test_new_special_formats():
    """Test special formats with new naming (no project number, MMDDYY dates)."""
    print("\n\nTesting New Special Formats")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    # Test special formats with new naming
    test_files = [
        # Meeting Minutes
        "MTG_031524_DesignReview.docx",
        "MTG_052024_ProgressMeeting.docx",
        
        # Transmittals
        "TXM_CONT_001_051024.pdf",
        "TXM_ARCH_002_060124.pdf",
        
        # Shop Drawings
        "SHOP_S_ACME_STEEL_R1_061524.pdf",
        "SHOP_M_HVAC_UNITS_R0_070124.pdf",
        
        # As-Built Drawings
        "AB_A_001_083024.pdf",
        "AB_E_E101_091524.pdf",
    ]
    
    print("Special Format Tests:")
    success_count = 0
    
    for filename in test_files:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if metadata.get("is_aec_standard"):
            format_type = metadata.get('naming_format')
            print(f"  [OK] Special Format: {format_type}")
            print(f"  [OK] Document Type: {metadata.get('document_type')} ({metadata.get('document_type_name')})")
            
            if format_type == "shop_drawing":
                print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
                print(f"  [OK] Revision: {metadata.get('revision')}")
            elif format_type == "as_built":
                print(f"  [OK] Discipline: {metadata.get('discipline_code')} ({metadata.get('discipline_name')})")
                print(f"  [OK] Sheet: {metadata.get('sheet_number')}")
            
            print(f"  [OK] Date: {metadata.get('date_issued')}")
            success_count += 1
        else:
            print(f"  [FAIL] Not recognized as AEC standard")
    
    print(f"\nSpecial Format Results: {success_count}/{len(test_files)} files parsed successfully")
    return success_count == len(test_files)

def test_date_format_validation():
    """Test that MMDDYY date format is properly validated."""
    print("\n\nTesting MMDDYY Date Format Validation")
    print("="*50)
    
    extractor = MetadataExtractor()
    
    # Test various date formats
    date_tests = [
        ("CD_A_DWG_001_R0_031524.pdf", "031524", True),  # Valid: March 15, 2024
        ("CD_A_DWG_001_R0_123124.pdf", "123124", True),  # Valid: December 31, 2024
        ("CD_A_DWG_001_R0_010124.pdf", "010124", True),  # Valid: January 1, 2024
        ("CD_A_DWG_001_R0_2024-03-15.pdf", None, False),  # Invalid: Old format
        ("CD_A_DWG_001_R0_20240315.pdf", None, False),  # Invalid: YYYYMMDD
    ]
    
    print("Date Format Tests:")
    success_count = 0
    
    for filename, expected_date, should_work in date_tests:
        print(f"\nFile: {filename}")
        metadata = extractor.extract_aec_metadata(f"/temp/{filename}")
        
        if should_work:
            if metadata.get("is_aec_standard") and metadata.get("date_issued") == expected_date:
                print(f"  [OK] Date format recognized: {expected_date}")
                success_count += 1
            else:
                print(f"  [FAIL] Date format not recognized or incorrect")
        else:
            if not metadata.get("is_aec_standard") or metadata.get("naming_format") != "primary":
                print(f"  [OK] Correctly rejected invalid date format")
                success_count += 1
            else:
                print(f"  [FAIL] Incorrectly accepted invalid date format")
    
    print(f"\nDate Format Results: {success_count}/{len(date_tests)} tests passed")
    return success_count == len(date_tests)

def main():
    """Run all tests for the new naming format."""
    print("AEC Directory Scanner - New Naming Format Test")
    print("="*90)
    print("Testing format: Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext")
    print("Date format: MMDDYY (no project number)")
    print()
    
    try:
        # Run all tests
        primary_passed = test_new_primary_format()
        special_passed = test_new_special_formats()
        date_passed = test_date_format_validation()
        
        print("\n" + "="*90)
        print("TEST SUMMARY:")
        print(f"Primary Format Tests: {'PASSED' if primary_passed else 'FAILED'}")
        print(f"Special Format Tests: {'PASSED' if special_passed else 'FAILED'}")
        print(f"Date Format Tests: {'PASSED' if date_passed else 'FAILED'}")
        
        if primary_passed and special_passed and date_passed:
            print("\n[SUCCESS] All new naming convention tests PASSED!")
            print("The updated file naming system is working correctly.")
        else:
            print("\n[ERROR] Some tests FAILED!")
            return 1
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())