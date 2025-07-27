"""
Metadata Extraction Engine

Comprehensive metadata extraction from various file types with support for
AEC-specific file naming conventions and content analysis.
"""

import os
import re
import json
import logging
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass
class ExtractorResult:
    """Result from metadata extraction."""
    success: bool
    metadata: Dict[str, Any]
    errors: List[str]
    extractor_version: str
    extraction_time: datetime


class BaseExtractor:
    """Base class for all metadata extractors."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.version = "1.0"
    
    def can_extract(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file."""
        raise NotImplementedError
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from the file."""
        raise NotImplementedError


class GeneralFileExtractor(BaseExtractor):
    """Extract general file system metadata from any file."""
    
    def can_extract(self, file_path: str) -> bool:
        return os.path.exists(file_path)
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract basic file system metadata."""
        try:
            path = Path(file_path)
            stat_info = path.stat()
            
            # Get MIME type
            mime_type, encoding = mimetypes.guess_type(file_path)
            
            return {
                "file_name": path.name,
                "file_extension": path.suffix.lower(),
                "file_size_bytes": stat_info.st_size,
                "file_size_mb": round(stat_info.st_size / (1024 * 1024), 4),
                "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "mime_type": mime_type,
                "encoding": encoding,
                "parent_directory": str(path.parent),
                "is_hidden": path.name.startswith('.'),
                "permissions": oct(stat_info.st_mode)[-3:]
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting general metadata from {file_path}: {e}")
            return {"error": str(e)}


class PDFExtractor(BaseExtractor):
    """Extract metadata from PDF files."""
    
    def can_extract(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata using basic file reading."""
        try:
            metadata = {
                "document_type": "PDF",
                "page_count": None,
                "title": None,
                "author": None,
                "creator": None,
                "producer": None,
                "creation_date": None,
                "modification_date": None,
                "keywords": [],
                "subject": None,
                "pdf_version": None
            }
            
            # Basic PDF header analysis
            with open(file_path, 'rb') as file:
                header = file.read(1024).decode('latin-1', errors='ignore')
                
                # Extract PDF version
                version_match = re.search(r'%PDF-(\d+\.\d+)', header)
                if version_match:
                    metadata["pdf_version"] = version_match.group(1)
                
                # Try to find basic metadata in the header
                if '/Title' in header:
                    title_match = re.search(r'/Title\s*\((.*?)\)', header)
                    if title_match:
                        metadata["title"] = title_match.group(1)
                
                if '/Author' in header:
                    author_match = re.search(r'/Author\s*\((.*?)\)', header)
                    if author_match:
                        metadata["author"] = author_match.group(1)
            
            # Try to count pages by searching for page objects
            try:
                with open(file_path, 'rb') as file:
                    content = file.read()
                    page_objects = content.count(b'/Type /Page')
                    if page_objects > 0:
                        metadata["page_count"] = page_objects
            except Exception:
                pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF metadata from {file_path}: {e}")
            return {"error": str(e), "document_type": "PDF"}


class CADExtractor(BaseExtractor):
    """Extract metadata from CAD files (DWG/DXF)."""
    
    def can_extract(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.dwg', '.dxf'))
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract CAD file metadata."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            metadata = {
                "document_type": "CAD",
                "cad_format": file_ext[1:].upper(),  # Remove the dot
                "version": None,
                "units": None,
                "layers": [],
                "blocks": [],
                "entities_count": None,
                "drawing_limits": None,
                "last_saved_by": None
            }
            
            if file_ext == '.dxf':
                # DXF files are text-based, we can parse basic information
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read(5000)  # Read first 5KB
                        
                        # Look for version information
                        version_match = re.search(r'AC\d{4}', content)
                        if version_match:
                            metadata["version"] = version_match.group(0)
                        
                        # Count basic entities (simplified)
                        lines = content.split('\n')
                        entity_count = 0
                        for line in lines:
                            if line.strip() in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'TEXT']:
                                entity_count += 1
                        
                        if entity_count > 0:
                            metadata["entities_count"] = entity_count
                            
                except Exception:
                    pass
            
            elif file_ext == '.dwg':
                # DWG files are binary, limited metadata extraction
                try:
                    with open(file_path, 'rb') as file:
                        header = file.read(100)
                        
                        # Try to identify DWG version from header
                        if header.startswith(b'AC'):
                            version_bytes = header[0:6]
                            metadata["version"] = version_bytes.decode('ascii', errors='ignore')
                            
                except Exception:
                    pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting CAD metadata from {file_path}: {e}")
            return {"error": str(e), "document_type": "CAD"}


class OfficeDocumentExtractor(BaseExtractor):
    """Extract metadata from Office documents."""
    
    def can_extract(self, file_path: str) -> bool:
        extensions = {'.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt'}
        return Path(file_path).suffix.lower() in extensions
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract Office document metadata."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            metadata = {
                "document_type": "Office Document",
                "office_format": file_ext[1:].upper(),
                "title": None,
                "author": None,
                "last_modified_by": None,
                "creation_date": None,
                "last_modified": None,
                "revision": None,
                "application": None,
                "company": None,
                "keywords": [],
                "comments": None
            }
            
            # For newer Office formats (.docx, .xlsx, .pptx), try to read XML metadata
            if file_ext in {'.docx', '.xlsx', '.pptx'}:
                try:
                    import zipfile
                    
                    with zipfile.ZipFile(file_path, 'r') as zip_file:
                        # Try to read core properties
                        try:
                            core_xml = zip_file.read('docProps/core.xml')
                            root = ET.fromstring(core_xml)
                            
                            # Define namespaces
                            ns = {
                                'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                                'dc': 'http://purl.org/dc/elements/1.1/',
                                'dcterms': 'http://purl.org/dc/terms/'
                            }
                            
                            # Extract metadata
                            title_elem = root.find('.//dc:title', ns)
                            if title_elem is not None:
                                metadata["title"] = title_elem.text
                            
                            creator_elem = root.find('.//dc:creator', ns)
                            if creator_elem is not None:
                                metadata["author"] = creator_elem.text
                            
                            modified_elem = root.find('.//cp:lastModifiedBy', ns)
                            if modified_elem is not None:
                                metadata["last_modified_by"] = modified_elem.text
                            
                            created_elem = root.find('.//dcterms:created', ns)
                            if created_elem is not None:
                                metadata["creation_date"] = created_elem.text
                            
                            modified_date_elem = root.find('.//dcterms:modified', ns)
                            if modified_date_elem is not None:
                                metadata["last_modified"] = modified_date_elem.text
                            
                            keywords_elem = root.find('.//cp:keywords', ns)
                            if keywords_elem is not None and keywords_elem.text:
                                metadata["keywords"] = [k.strip() for k in keywords_elem.text.split(',')]
                            
                        except Exception:
                            pass  # Core properties might not exist
                        
                        # Try to read app properties
                        try:
                            app_xml = zip_file.read('docProps/app.xml')
                            app_root = ET.fromstring(app_xml)
                            
                            app_ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}
                            
                            app_elem = app_root.find('.//ep:Application', app_ns)
                            if app_elem is not None:
                                metadata["application"] = app_elem.text
                            
                            company_elem = app_root.find('.//ep:Company', app_ns)
                            if company_elem is not None:
                                metadata["company"] = company_elem.text
                            
                        except Exception:
                            pass  # App properties might not exist
                            
                except Exception:
                    pass  # File might not be a valid zip or Office file
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting Office document metadata from {file_path}: {e}")
            return {"error": str(e), "document_type": "Office Document"}


class ImageExtractor(BaseExtractor):
    """Extract metadata from image files."""
    
    def can_extract(self, file_path: str) -> bool:
        extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'}
        return Path(file_path).suffix.lower() in extensions
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract image metadata."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            metadata = {
                "document_type": "Image",
                "image_format": file_ext[1:].upper(),
                "width": None,
                "height": None,
                "color_depth": None,
                "compression": None,
                "camera_make": None,
                "camera_model": None,
                "date_taken": None,
                "gps_coordinates": None,
                "orientation": None
            }
            
            # Try to get basic image information by reading file headers
            try:
                with open(file_path, 'rb') as file:
                    header = file.read(1024)
                    
                    if file_ext in {'.jpg', '.jpeg'}:
                        # JPEG header analysis
                        if header.startswith(b'\xff\xd8\xff'):
                            # Look for EXIF data marker
                            if b'Exif' in header:
                                metadata["has_exif"] = True
                            
                            # Try to find image dimensions in JPEG
                            try:
                                file.seek(0)
                                data = file.read(10000)  # Read more data for dimension search
                                
                                # Look for SOF (Start of Frame) markers
                                sof_markers = [b'\xff\xc0', b'\xff\xc1', b'\xff\xc2']
                                for marker in sof_markers:
                                    pos = data.find(marker)
                                    if pos != -1 and pos + 9 < len(data):
                                        # Height and width are at specific offsets
                                        height = int.from_bytes(data[pos+5:pos+7], 'big')
                                        width = int.from_bytes(data[pos+7:pos+9], 'big')
                                        metadata["height"] = height
                                        metadata["width"] = width
                                        break
                            except Exception:
                                pass
                    
                    elif file_ext == '.png':
                        # PNG header analysis
                        if header.startswith(b'\x89PNG\r\n\x1a\n'):
                            # PNG dimensions are in the IHDR chunk
                            try:
                                if len(header) >= 24:
                                    width = int.from_bytes(header[16:20], 'big')
                                    height = int.from_bytes(header[20:24], 'big')
                                    metadata["width"] = width
                                    metadata["height"] = height
                            except Exception:
                                pass
                    
                    elif file_ext in {'.tiff', '.tif'}:
                        # TIFF header analysis
                        if header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
                            metadata["tiff_format"] = "Little Endian" if header.startswith(b'II') else "Big Endian"
            
            except Exception:
                pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting image metadata from {file_path}: {e}")
            return {"error": str(e), "document_type": "Image"}


class TextFileExtractor(BaseExtractor):
    """Extract metadata from text files."""
    
    def can_extract(self, file_path: str) -> bool:
        extensions = {'.txt', '.md', '.rtf', '.csv', '.log'}
        return Path(file_path).suffix.lower() in extensions
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text file metadata."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            metadata = {
                "document_type": "Text File",
                "text_format": file_ext[1:].upper(),
                "encoding": None,
                "line_count": 0,
                "word_count": 0,
                "character_count": 0,
                "language": None,
                "has_bom": False
            }
            
            # Detect encoding and read file
            try:
                # Try common encodings
                encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
                content = None
                detected_encoding = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            content = file.read()
                            detected_encoding = encoding
                            break
                    except UnicodeDecodeError:
                        continue
                
                if content is not None:
                    metadata["encoding"] = detected_encoding
                    
                    # Check for BOM
                    with open(file_path, 'rb') as file:
                        first_bytes = file.read(4)
                        if first_bytes.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
                            metadata["has_bom"] = True
                        elif first_bytes.startswith(b'\xff\xfe') or first_bytes.startswith(b'\xfe\xff'):  # UTF-16 BOM
                            metadata["has_bom"] = True
                    
                    # Count lines, words, characters
                    lines = content.split('\n')
                    metadata["line_count"] = len(lines)
                    metadata["character_count"] = len(content)
                    
                    words = content.split()
                    metadata["word_count"] = len(words)
                    
                    # For CSV files, try to detect structure
                    if file_ext == '.csv':
                        try:
                            import csv
                            from io import StringIO
                            
                            # Detect CSV dialect
                            sample = content[:1024]
                            sniffer = csv.Sniffer()
                            dialect = sniffer.sniff(sample)
                            
                            # Count columns and rows
                            csv_reader = csv.reader(StringIO(content), dialect=dialect)
                            rows = list(csv_reader)
                            
                            metadata["csv_rows"] = len(rows)
                            metadata["csv_columns"] = len(rows[0]) if rows else 0
                            metadata["csv_delimiter"] = dialect.delimiter
                            
                        except Exception:
                            pass
            
            except Exception:
                pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting text file metadata from {file_path}: {e}")
            return {"error": str(e), "document_type": "Text File"}


class MetadataExtractor:
    """
    Main metadata extraction engine that coordinates multiple extractors
    and handles AEC-specific metadata extraction.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the metadata extractor with all available extractors.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.version = "1.0"
        
        # Register all extractors
        self.extractors: List[BaseExtractor] = [
            GeneralFileExtractor(logger),
            PDFExtractor(logger),
            CADExtractor(logger),
            OfficeDocumentExtractor(logger),
            ImageExtractor(logger),
            TextFileExtractor(logger)
        ]
        
        # Custom extractors registry
        self.custom_extractors: Dict[str, BaseExtractor] = {}
        
        # AEC file naming patterns - Comprehensive system supporting full specification
        self.aec_patterns = {
            # Primary format: Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext
            "primary_format": r"([A-Z]{2})_([A-Z]{1,2}|EN|SU|PM|GE)_([A-Z0-9]{2,6})_([A-Z0-9]{1,8})_([CR]\d{1,2}|[A-Z]{2,6})_([0-9]{6})\.([a-z0-9]{2,4})",
            
            # Basic project identification (legacy support)
            "project_number": r"[A-Z0-9]{3,8}",  # e.g., PROJ123, ABC123456 (for legacy files)
            "project_year": r"20\d{2}",  # 2020-2099 (for legacy files)
            "date_format": r"[0-9]{6}",  # MMDDYY format
            
            # Document identification
            "document_number": r"[A-Z]\d{2}-\d{3}",  # e.g., A01-001, S02-005
            "sheet_number": r"[A-Z0-9]{1,4}",  # e.g., 001, A1, S201, M401
            "drawing_number": r"[A-Z]-\d{3}",  # Legacy format
            
            # Revision tracking - Check Print and Clean Document System
            "revision": r"R\d{1,2}",  # Clean revisions: R0, R1, R15
            "check_print": r"C\d{1,2}",  # Check print revisions: C01, C02, C15
            "revision_letter": r"[A-Z]",  # A, B, C for preliminary revisions
            "issue_code": r"(IFC|IFB|IFP|AB|RFI|PCO|FOR|CONST|RECORD)",  # All issue types
            
            # Discipline codes - Full comprehensive list
            "discipline_code": r"(A|S|G|C|M|E|P|H|F|L|I|T|EN|SU|PM|GE)",
            "discipline_full": {
                "A": "Architectural",
                "S": "Structural",
                "G": "Geotechnical", 
                "C": "Civil",
                "M": "Mechanical",
                "E": "Electrical",
                "P": "Plumbing",
                "H": "Hydraulic",
                "F": "Fire Protection",
                "L": "Landscape",
                "I": "Interiors",
                "T": "Transportation",
                "EN": "Environmental",
                "SU": "Survey",
                "PM": "Project Management",
                "GE": "General/Multi-Discipline"
            },
            
            # Phase codes
            "phase_code": r"(PD|SD|DD|CD|CA|CO)",
            "phase_full": {
                "PD": "Pre-Design/Programming",
                "SD": "Schematic Design",
                "DD": "Design Development", 
                "CD": "Construction Documents",
                "CA": "Construction Administration",
                "CO": "Closeout"
            },
            
            # Document types - Comprehensive list
            "document_type": r"(DWG|PLN|SEC|DTL|SCH|CALC|LOAD|SIZE|PAR|RPT|MEMO|STUDY|EVAL|SPEC|DIV|RFI|SUB|CO|TXM|LTR|BIM|3D|CAD|PHO|IMG|PER|APP|MTG|SHOP|AB)",
            "document_type_full": {
                # Drawings
                "DWG": "Drawing",
                "PLN": "Plan",
                "SEC": "Section",
                "DTL": "Detail",
                "SCH": "Schedule",
                # Calculations
                "CALC": "Calculation",
                "LOAD": "Load Calculation",
                "SIZE": "Sizing Calculation",
                "PAR": "Parameter Calculation",
                # Reports
                "RPT": "Report",
                "MEMO": "Memorandum",
                "STUDY": "Study",
                "EVAL": "Evaluation",
                # Specifications
                "SPEC": "Specification",
                "DIV": "Division",
                # Correspondence
                "RFI": "Request for Information",
                "SUB": "Submittal",
                "CO": "Change Order",
                "TXM": "Transmittal",
                "LTR": "Letter",
                # Models
                "BIM": "Building Information Model",
                "3D": "3D Model",
                "CAD": "CAD File",
                # Photos
                "PHO": "Photograph",
                "IMG": "Image",
                # Permits
                "PER": "Permit",
                "APP": "Application",
                # Special formats
                "MTG": "Meeting",
                "SHOP": "Shop Drawing",
                "AB": "As-Built"
            },
            
            # CSI MasterFormat
            "csi_division": r"(0[0-9]|1[0-6]|2[0-9]|3[0-9]|4[0-9])",  # 00-49
            "csi_section": r"\d{2}\s?\d{2}\s?\d{2}",  # 03 30 00 format
            
            # Special naming patterns (without project number, MMDDYY date format)
            "meeting_format": r"MTG_([0-9]{6})_([A-Za-z]+)\.([a-z]{3,4})",
            "transmittal_format": r"TXM_([A-Z]{2,4})_([0-9]{3})_([0-9]{6})\.([a-z]{3})",
            "shop_drawing_format": r"SHOP_([A-Z]{1,2})_([A-Z]+)_([A-Z]+)_([CR]\d{1,2})_([0-9]{6})\.([a-z]{3})",
            "as_built_format": r"AB_([A-Z]{1,2})_([A-Z0-9]{1,4})_([0-9]{6})\.([a-z]{3})",
            
            # Special identifiers
            "submittal_number": r"SUB-\d{3}",  # SUB-001
            "rfi_number": r"RFI-\d{3}",  # RFI-001
            "change_order": r"CO-\d{3}",  # CO-001
            "sku_number": r"SKU-\d{3}",  # Sketch number
            
            # Size and format codes
            "sheet_size": r"(11X17|24X36|30X42|ARCH[ABCDE]|ANSI[ABCDE])",
            "scale": r"(NTS|VARIES|\d+\"=\d+'?-?\d*\"?)",
            
            # Status indicators
            "status": r"(DRAFT|PRELIM|FINAL|VOID|SUPERSEDED)",
            "confidential": r"(CONFIDENTIAL|PROPRIETARY|NOT FOR CONSTRUCTION)"
        }
    
    def extract_metadata(self, file_path: str) -> ExtractorResult:
        """
        Extract comprehensive metadata from a file using all applicable extractors.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            ExtractorResult containing all extracted metadata
        """
        start_time = datetime.now()
        all_metadata = {}
        errors = []
        
        try:
            # Run all applicable extractors
            for extractor in self.extractors:
                try:
                    if extractor.can_extract(file_path):
                        extractor_name = extractor.__class__.__name__
                        result = extractor.extract(file_path)
                        
                        if result:
                            all_metadata[extractor_name] = result
                            
                except Exception as e:
                    error_msg = f"Error in {extractor.__class__.__name__}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            
            # Check custom extractors
            file_ext = Path(file_path).suffix.lower()
            if file_ext in self.custom_extractors:
                try:
                    custom_result = self.custom_extractors[file_ext].extract(file_path)
                    all_metadata["CustomExtractor"] = custom_result
                except Exception as e:
                    errors.append(f"Custom extractor error: {str(e)}")
            
            return ExtractorResult(
                success=len(all_metadata) > 0,
                metadata=all_metadata,
                errors=errors,
                extractor_version=self.version,
                extraction_time=start_time
            )
            
        except Exception as e:
            error_msg = f"Critical error in metadata extraction: {str(e)}"
            self.logger.error(error_msg)
            
            return ExtractorResult(
                success=False,
                metadata={},
                errors=[error_msg],
                extractor_version=self.version,
                extraction_time=start_time
            )
    
    def extract_aec_metadata(self, file_path: str, naming_convention: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract AEC-specific metadata from comprehensive file naming conventions.
        
        Args:
            file_path: Path to the file
            naming_convention: Optional custom naming convention patterns
            
        Returns:
            Dictionary containing AEC-specific metadata
        """
        patterns = naming_convention or self.aec_patterns
        file_path_obj = Path(file_path)
        filename = file_path_obj.name  # Full filename with extension
        
        aec_metadata = {
            "is_aec_standard": False,
            "naming_format": None,
            "project_number": None,
            "phase_code": None,
            "phase_name": None,
            "discipline_code": None,
            "discipline_name": None,
            "document_type": None,
            "document_type_name": None,
            "sheet_number": None,
            "revision": None,
            "revision_type": None,  # "check_print", "clean", "issue_code"
            "date_issued": None,
            "issue_code": None,
            "drawing_number": None,
            "csi_division": None,
            "csi_section": None,
            "special_identifiers": [],
            "extracted_elements": [],
            "keywords": []
        }
        
        try:
            # Try primary format first: Phase_DisciplineCode_DocumentType_SheetNumber_RevisionNumber_Date.ext
            primary_match = re.search(patterns["primary_format"], filename, re.IGNORECASE)
            if primary_match:
                aec_metadata["naming_format"] = "primary"
                aec_metadata["is_aec_standard"] = True
                aec_metadata["phase_code"] = primary_match.group(1)
                aec_metadata["discipline_code"] = primary_match.group(2)
                aec_metadata["document_type"] = primary_match.group(3).upper()
                aec_metadata["sheet_number"] = primary_match.group(4)
                aec_metadata["revision"] = primary_match.group(5)
                aec_metadata["date_issued"] = primary_match.group(6)
                
                # Determine revision type
                if aec_metadata["revision"].startswith('C'):
                    aec_metadata["revision_type"] = "check_print"
                elif aec_metadata["revision"].startswith('R'):
                    aec_metadata["revision_type"] = "clean"
                else:
                    aec_metadata["revision_type"] = "issue_code"
                
                # Get full names
                aec_metadata["phase_name"] = patterns["phase_full"].get(aec_metadata["phase_code"], "Unknown")
                aec_metadata["discipline_name"] = patterns["discipline_full"].get(aec_metadata["discipline_code"], "Unknown")
                aec_metadata["document_type_name"] = patterns["document_type_full"].get(aec_metadata["document_type"], "Unknown")
                
                aec_metadata["extracted_elements"] = ["phase_code", "discipline_code", "document_type", "sheet_number", "revision", "date_issued"]
                return aec_metadata
            
            # Try special formats
            special_formats = {
                "meeting": patterns["meeting_format"],
                "transmittal": patterns["transmittal_format"],
                "shop_drawing": patterns["shop_drawing_format"],
                "as_built": patterns["as_built_format"]
            }
            
            for format_name, pattern in special_formats.items():
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    aec_metadata["naming_format"] = format_name
                    aec_metadata["is_aec_standard"] = True
                    
                    if format_name == "meeting":
                        aec_metadata["date_issued"] = match.group(1)
                        aec_metadata["document_type"] = "MTG"
                        aec_metadata["document_type_name"] = "Meeting"
                        aec_metadata["extracted_elements"] = ["date_issued", "document_type"]
                    
                    elif format_name == "transmittal":
                        aec_metadata["date_issued"] = match.group(3)
                        aec_metadata["document_type"] = "TXM"
                        aec_metadata["document_type_name"] = "Transmittal"
                        aec_metadata["extracted_elements"] = ["date_issued", "document_type"]
                    
                    elif format_name == "shop_drawing":
                        aec_metadata["discipline_code"] = match.group(1)
                        aec_metadata["revision"] = match.group(4)
                        aec_metadata["date_issued"] = match.group(5)
                        aec_metadata["document_type"] = "SHOP"
                        aec_metadata["document_type_name"] = "Shop Drawing"
                        aec_metadata["discipline_name"] = patterns["discipline_full"].get(aec_metadata["discipline_code"], "Unknown")
                        aec_metadata["extracted_elements"] = ["discipline_code", "revision", "date_issued", "document_type"]
                    
                    elif format_name == "as_built":
                        aec_metadata["discipline_code"] = match.group(1)
                        aec_metadata["sheet_number"] = match.group(2)
                        aec_metadata["date_issued"] = match.group(3)
                        aec_metadata["document_type"] = "AB"
                        aec_metadata["document_type_name"] = "As-Built"
                        aec_metadata["discipline_name"] = patterns["discipline_full"].get(aec_metadata["discipline_code"], "Unknown")
                        aec_metadata["extracted_elements"] = ["discipline_code", "sheet_number", "date_issued", "document_type"]
                    
                    return aec_metadata
            
            # Fallback to individual pattern matching for legacy formats
            aec_metadata["naming_format"] = "legacy"
            filename_no_ext = file_path_obj.stem  # Filename without extension
            
            # Extract project number
            project_match = re.search(patterns["project_number"], filename_no_ext, re.IGNORECASE)
            if project_match:
                aec_metadata["project_number"] = project_match.group(0)
                aec_metadata["is_aec_standard"] = True
                aec_metadata["extracted_elements"].append("project_number")
            
            # Extract discipline code
            discipline_match = re.search(patterns["discipline_code"], filename_no_ext)
            if discipline_match:
                disc_code = discipline_match.group(0)
                aec_metadata["discipline_code"] = disc_code
                aec_metadata["discipline_name"] = patterns["discipline_full"].get(disc_code, "Unknown")
                aec_metadata["extracted_elements"].append("discipline_code")
            
            # Extract document type
            doc_match = re.search(patterns["document_type"], filename_no_ext, re.IGNORECASE)
            if doc_match:
                doc_type = doc_match.group(0).upper()
                aec_metadata["document_type"] = doc_type
                aec_metadata["document_type_name"] = patterns["document_type_full"].get(doc_type, "Unknown")
                aec_metadata["extracted_elements"].append("document_type")
            
            # Extract phase code
            phase_match = re.search(patterns["phase_code"], filename_no_ext)
            if phase_match:
                phase_code = phase_match.group(0)
                aec_metadata["phase_code"] = phase_code
                aec_metadata["phase_name"] = patterns["phase_full"].get(phase_code, "Unknown")
                aec_metadata["extracted_elements"].append("phase_code")
            
            # Extract revision - check for check prints first
            check_print_match = re.search(patterns["check_print"], filename_no_ext, re.IGNORECASE)
            if check_print_match:
                aec_metadata["revision"] = check_print_match.group(0).upper()
                aec_metadata["revision_type"] = "check_print"
                aec_metadata["extracted_elements"].append("revision")
            else:
                rev_match = re.search(patterns["revision"], filename_no_ext, re.IGNORECASE)
                if rev_match:
                    aec_metadata["revision"] = rev_match.group(0).upper()
                    aec_metadata["revision_type"] = "clean"
                    aec_metadata["extracted_elements"].append("revision")
            
            # Extract issue code
            issue_match = re.search(patterns["issue_code"], filename_no_ext)
            if issue_match:
                aec_metadata["issue_code"] = issue_match.group(0)
                aec_metadata["revision_type"] = "issue_code"
                aec_metadata["extracted_elements"].append("issue_code")
            
            # Extract sheet number
            sheet_match = re.search(patterns["sheet_number"], filename_no_ext)
            if sheet_match:
                aec_metadata["sheet_number"] = sheet_match.group(0)
                aec_metadata["extracted_elements"].append("sheet_number")
            
            # Extract date
            date_match = re.search(patterns["date_format"], filename_no_ext)
            if date_match:
                aec_metadata["date_issued"] = date_match.group(0)
                aec_metadata["extracted_elements"].append("date_issued")
            
            # Extract CSI information
            csi_div_match = re.search(patterns["csi_division"], filename_no_ext)
            if csi_div_match:
                aec_metadata["csi_division"] = csi_div_match.group(0)
                aec_metadata["extracted_elements"].append("csi_division")
            
            csi_sec_match = re.search(patterns["csi_section"], filename_no_ext)
            if csi_sec_match:
                aec_metadata["csi_section"] = csi_sec_match.group(0)
                aec_metadata["extracted_elements"].append("csi_section")
            
            # Extract special identifiers
            special_patterns = ["submittal_number", "rfi_number", "change_order", "sku_number"]
            for pattern_name in special_patterns:
                special_match = re.search(patterns[pattern_name], filename_no_ext, re.IGNORECASE)
                if special_match:
                    aec_metadata["special_identifiers"].append({
                        "type": pattern_name,
                        "value": special_match.group(0)
                    })
                    aec_metadata["extracted_elements"].append(pattern_name)
            
            # Extract keywords from filename
            keyword_patterns = [
                r"plan", r"elevation", r"section", r"detail", r"schedule",
                r"spec", r"drawing", r"sheet", r"layout", r"diagram", r"calc",
                r"report", r"memo", r"study", r"evaluation", r"permit", r"photo"
            ]
            
            for pattern in keyword_patterns:
                if re.search(pattern, filename_no_ext.lower()):
                    aec_metadata["keywords"].append(pattern)
            
            # Determine if this follows AEC standards based on extracted elements
            if len(aec_metadata["extracted_elements"]) >= 2:
                aec_metadata["is_aec_standard"] = True
            
            # Determine parent folder type for additional context
            parent_folder = file_path_obj.parent.name
            aec_metadata["folder_context"] = parent_folder
            
        except Exception as e:
            self.logger.error(f"Error extracting AEC metadata: {e}")
            aec_metadata["extraction_error"] = str(e)
        
        return aec_metadata
    
    def extract_content_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Generate a content summary for supported file types.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing content summary information
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            summary = {
                "has_summary": False,
                "content_type": None,
                "summary_text": None,
                "key_elements": [],
                "complexity_score": 0
            }
            
            # Text-based content summary
            if file_ext in {'.txt', '.md', '.rtf'}:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read(5000)  # Read first 5KB
                        
                        if content:
                            summary["has_summary"] = True
                            summary["content_type"] = "Text Document"
                            
                            # Extract first few sentences as summary
                            sentences = re.split(r'[.!?]+', content)
                            summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
                            summary["summary_text"] = '. '.join(summary_sentences)
                            
                            # Find key elements (capitalized words, numbers)
                            key_elements = re.findall(r'\b[A-Z][A-Za-z]{2,}\b|\b\d+(?:\.\d+)?\b', content)
                            summary["key_elements"] = list(set(key_elements[:20]))  # Limit to 20 unique elements
                            
                            # Simple complexity score based on vocabulary diversity
                            words = content.lower().split()
                            unique_words = set(words)
                            if len(words) > 0:
                                summary["complexity_score"] = min(len(unique_words) / len(words), 1.0)
                
                except Exception:
                    pass
            
            # PDF content summary (basic)
            elif file_ext == '.pdf':
                summary["content_type"] = "PDF Document"
                # Note: Advanced PDF text extraction would require additional libraries
                summary["summary_text"] = "PDF document - text extraction not available in basic mode"
            
            # CAD file summary
            elif file_ext in {'.dwg', '.dxf'}:
                summary["content_type"] = "CAD Drawing"
                summary["summary_text"] = f"CAD drawing file in {file_ext.upper()} format"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating content summary: {e}")
            return {"error": str(e)}
    
    def generate_content_hash(self, file_path: str) -> str:
        """
        Generate a SHA-256 hash of the file content for change detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal string of the file hash
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating content hash: {e}")
            return ""
    
    def register_custom_extractor(self, file_type: str, extractor: BaseExtractor) -> None:
        """
        Register a custom metadata extractor for specific file types.
        
        Args:
            file_type: File extension (e.g., '.xyz')
            extractor: Custom extractor instance
        """
        self.custom_extractors[file_type.lower()] = extractor
        self.logger.info(f"Registered custom extractor for {file_type} files")
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get list of all supported file types.
        
        Returns:
            List of supported file extensions
        """
        supported_types = []
        
        # Get types from built-in extractors
        type_map = {
            'PDFExtractor': ['.pdf'],
            'CADExtractor': ['.dwg', '.dxf'],
            'OfficeDocumentExtractor': ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt'],
            'ImageExtractor': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'],
            'TextFileExtractor': ['.txt', '.md', '.rtf', '.csv', '.log']
        }
        
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            if extractor_name in type_map:
                supported_types.extend(type_map[extractor_name])
        
        # Add custom extractor types
        supported_types.extend(self.custom_extractors.keys())
        
        return sorted(list(set(supported_types)))