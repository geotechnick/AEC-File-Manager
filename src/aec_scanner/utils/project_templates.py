"""
Project Templates and Intelligent File Detection

Smart project templates, file type detection, and automated project setup
based on industry standards and best practices.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re


@dataclass
class FileTypeInfo:
    """Information about a detected file type."""
    extension: str
    category: str
    discipline: str
    confidence: float
    metadata_extractors: List[str] = field(default_factory=list)
    typical_locations: List[str] = field(default_factory=list)


@dataclass
class ProjectTemplate:
    """Project template definition."""
    name: str
    description: str
    directory_structure: Dict[str, List[str]]
    file_naming_patterns: Dict[str, str]
    disciplines: List[str]
    typical_file_types: Set[str]
    metadata_requirements: Dict[str, List[str]]


class IntelligentFileDetector:
    """
    Intelligent file type detection and classification system
    for AEC projects.
    """
    
    def __init__(self):
        # Comprehensive file type database
        self.file_types = self._initialize_file_types()
        
        # Discipline detection patterns
        self.discipline_patterns = self._initialize_discipline_patterns()
        
        # Document type patterns
        self.document_patterns = self._initialize_document_patterns()
        
        # File naming conventions
        self.naming_conventions = self._initialize_naming_conventions()
    
    def _initialize_file_types(self) -> Dict[str, FileTypeInfo]:
        """Initialize comprehensive file type database."""
        return {
            # CAD and Design Files
            '.dwg': FileTypeInfo(
                extension='.dwg',
                category='cad',
                discipline='architectural',
                confidence=0.9,
                metadata_extractors=['autocad', 'dwg_reader'],
                typical_locations=['drawings', 'cad', 'design']
            ),
            '.dxf': FileTypeInfo(
                extension='.dxf',
                category='cad',
                discipline='architectural',
                confidence=0.85,
                metadata_extractors=['autocad', 'dxf_reader'],
                typical_locations=['drawings', 'cad', 'exchange']
            ),
            '.rvt': FileTypeInfo(
                extension='.rvt',
                category='bim',
                discipline='architectural',
                confidence=0.95,
                metadata_extractors=['revit', 'bim_reader'],
                typical_locations=['models', 'revit', 'bim']
            ),
            '.rfa': FileTypeInfo(
                extension='.rfa',
                category='bim_family',
                discipline='architectural',
                confidence=0.9,
                metadata_extractors=['revit', 'family_reader'],
                typical_locations=['families', 'components', 'library']
            ),
            '.skp': FileTypeInfo(
                extension='.skp',
                category='3d_model',
                discipline='architectural',
                confidence=0.8,
                metadata_extractors=['sketchup'],
                typical_locations=['models', 'sketchup', '3d']
            ),
            '.ifc': FileTypeInfo(
                extension='.ifc',
                category='bim_exchange',
                discipline='multidisciplinary',
                confidence=0.95,
                metadata_extractors=['ifc_reader', 'bim_reader'],
                typical_locations=['exchange', 'coordination', 'bim']
            ),
            
            # Engineering Files
            '.dgn': FileTypeInfo(
                extension='.dgn',
                category='cad',
                discipline='civil',
                confidence=0.85,
                metadata_extractors=['microstation'],
                typical_locations=['civil', 'survey', 'infrastructure']
            ),
            '.3dm': FileTypeInfo(
                extension='.3dm',
                category='3d_model',
                discipline='architectural',
                confidence=0.8,
                metadata_extractors=['rhino'],
                typical_locations=['models', 'rhino', 'parametric']
            ),
            '.step': FileTypeInfo(
                extension='.step',
                category='3d_exchange',
                discipline='mechanical',
                confidence=0.8,
                metadata_extractors=['step_reader'],
                typical_locations=['models', 'exchange', 'mechanical']
            ),
            '.stp': FileTypeInfo(
                extension='.stp',
                category='3d_exchange',
                discipline='mechanical',
                confidence=0.8,
                metadata_extractors=['step_reader'],
                typical_locations=['models', 'exchange', 'mechanical']
            ),
            
            # Documents
            '.pdf': FileTypeInfo(
                extension='.pdf',
                category='document',
                discipline='general',
                confidence=0.7,
                metadata_extractors=['pdf_reader', 'text_extractor'],
                typical_locations=['documents', 'drawings', 'specifications']
            ),
            '.docx': FileTypeInfo(
                extension='.docx',
                category='document',
                discipline='general',
                confidence=0.8,
                metadata_extractors=['office_reader', 'text_extractor'],
                typical_locations=['documents', 'specifications', 'reports']
            ),
            '.xlsx': FileTypeInfo(
                extension='.xlsx',
                category='spreadsheet',
                discipline='general',
                confidence=0.8,
                metadata_extractors=['office_reader', 'excel_reader'],
                typical_locations=['calculations', 'schedules', 'data']
            ),
            
            # Images and Visualizations
            '.jpg': FileTypeInfo(
                extension='.jpg',
                category='image',
                discipline='general',
                confidence=0.6,
                metadata_extractors=['image_reader', 'exif_reader'],
                typical_locations=['images', 'photos', 'renderings']
            ),
            '.png': FileTypeInfo(
                extension='.png',
                category='image',
                discipline='general',
                confidence=0.6,
                metadata_extractors=['image_reader'],
                typical_locations=['images', 'renderings', 'diagrams']
            ),
            '.tiff': FileTypeInfo(
                extension='.tiff',
                category='image',
                discipline='survey',
                confidence=0.7,
                metadata_extractors=['image_reader', 'geotiff_reader'],
                typical_locations=['survey', 'mapping', 'images']
            ),
            
            # Specialized Engineering
            '.las': FileTypeInfo(
                extension='.las',
                category='point_cloud',
                discipline='survey',
                confidence=0.9,
                metadata_extractors=['lidar_reader'],
                typical_locations=['survey', 'pointcloud', 'scanning']
            ),
            '.e57': FileTypeInfo(
                extension='.e57',
                category='point_cloud',
                discipline='survey',
                confidence=0.9,
                metadata_extractors=['pointcloud_reader'],
                typical_locations=['survey', 'scanning', '3d_data']
            ),
            '.pts': FileTypeInfo(
                extension='.pts',
                category='point_cloud',
                discipline='survey',
                confidence=0.8,
                metadata_extractors=['pointcloud_reader'],
                typical_locations=['survey', 'pointcloud', 'scanning']
            )
        }
    
    def _initialize_discipline_patterns(self) -> Dict[str, List[str]]:
        """Initialize discipline detection patterns."""
        return {
            'architectural': [
                'arch', 'architectural', 'building', 'facade', 'interior',
                'floor plan', 'elevation', 'section', 'detail'
            ],
            'structural': [
                'struct', 'structural', 'foundation', 'beam', 'column',
                'framing', 'reinforcement', 'concrete', 'steel'
            ],
            'mechanical': [
                'mech', 'mechanical', 'hvac', 'heating', 'cooling',
                'ventilation', 'ductwork', 'equipment'
            ],
            'electrical': [
                'elec', 'electrical', 'power', 'lighting', 'panel',
                'conduit', 'wiring', 'circuit'
            ],
            'plumbing': [
                'plumb', 'plumbing', 'water', 'sewer', 'drainage',
                'piping', 'fixtures', 'sanitary'
            ],
            'civil': [
                'civil', 'site', 'grading', 'utilities', 'roads',
                'infrastructure', 'survey', 'topography'
            ],
            'landscape': [
                'landscape', 'landscaping', 'planting', 'irrigation',
                'hardscape', 'site design'
            ],
            'fire_protection': [
                'fire', 'sprinkler', 'fire protection', 'alarm',
                'suppression', 'safety'
            ]
        }
    
    def _initialize_document_patterns(self) -> Dict[str, List[str]]:
        """Initialize document type detection patterns."""
        return {
            'drawing': [
                'plan', 'elevation', 'section', 'detail', 'schedule',
                'drawing', 'dwg', 'sheet'
            ],
            'specification': [
                'spec', 'specification', 'standard', 'requirement',
                'technical', 'material'
            ],
            'calculation': [
                'calc', 'calculation', 'analysis', 'design',
                'structural', 'load', 'sizing'
            ],
            'report': [
                'report', 'analysis', 'study', 'assessment',
                'evaluation', 'summary'
            ],
            'correspondence': [
                'letter', 'email', 'memo', 'correspondence',
                'communication', 'meeting'
            ],
            'submittal': [
                'submittal', 'shop drawing', 'product data',
                'sample', 'approval', 'review'
            ],
            'contract': [
                'contract', 'agreement', 'proposal', 'bid',
                'tender', 'purchase order'
            ]
        }
    
    def _initialize_naming_conventions(self) -> Dict[str, str]:
        """Initialize file naming convention patterns."""
        return {
            'aec_standard': r'^([A-Z]{1,3})-(\d{3})-([A-Z]{2})-(\d{2})',  # A-001-AR-01
            'project_based': r'^([A-Z0-9]+)-([A-Z]+)-(\d+)',  # PROJ2024-ARCH-001
            'discipline_first': r'^([A-Z]{1,3})(\d{3,4})',  # A001, S1001
            'phase_based': r'^([A-Z]{2})(\d{2})-([A-Z]{2})-(\d{3})',  # DD01-AR-001
            'iso_standard': r'^([A-Z]{2,4})-([A-Z]{2})-(\d{4})',  # PROJ-AR-0001
        }
    
    def detect_file_type(self, file_path: str) -> Optional[FileTypeInfo]:
        """
        Detect and classify a file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileTypeInfo object if detected, None otherwise
        """
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        # Direct extension match
        if extension in self.file_types:
            file_info = self.file_types[extension]
            
            # Enhance confidence based on location and naming
            enhanced_confidence = self._enhance_confidence(file_path, file_info)
            
            return FileTypeInfo(
                extension=file_info.extension,
                category=file_info.category,
                discipline=self._detect_discipline_from_path(file_path) or file_info.discipline,
                confidence=enhanced_confidence,
                metadata_extractors=file_info.metadata_extractors,
                typical_locations=file_info.typical_locations
            )
        
        # Unknown file type
        return None
    
    def _enhance_confidence(self, file_path: str, file_info: FileTypeInfo) -> float:
        """Enhance confidence based on file location and naming."""
        confidence = file_info.confidence
        path_lower = file_path.lower()
        
        # Check if file is in typical location
        for location in file_info.typical_locations:
            if location in path_lower:
                confidence = min(confidence + 0.1, 1.0)
                break
        
        # Check discipline match
        detected_discipline = self._detect_discipline_from_path(file_path)
        if detected_discipline == file_info.discipline:
            confidence = min(confidence + 0.05, 1.0)
        
        return confidence
    
    def _detect_discipline_from_path(self, file_path: str) -> Optional[str]:
        """Detect discipline from file path and name."""
        path_lower = file_path.lower()
        filename_lower = Path(file_path).name.lower()
        
        # Check path components and filename
        text_to_check = f"{path_lower} {filename_lower}"
        
        best_match = None
        highest_score = 0
        
        for discipline, patterns in self.discipline_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_to_check)
            if score > highest_score:
                highest_score = score
                best_match = discipline
        
        return best_match if highest_score > 0 else None
    
    def detect_document_type(self, file_path: str, content_hint: str = "") -> Optional[str]:
        """Detect document type from path and content hints."""
        path_lower = file_path.lower()
        content_lower = content_hint.lower()
        
        text_to_check = f"{path_lower} {content_lower}"
        
        best_match = None
        highest_score = 0
        
        for doc_type, patterns in self.document_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_to_check)
            if score > highest_score:
                highest_score = score
                best_match = doc_type
        
        return best_match
    
    def analyze_naming_convention(self, file_path: str) -> Dict[str, Any]:
        """Analyze file naming convention."""
        filename = Path(file_path).stem
        
        results = {
            'filename': filename,
            'convention': None,
            'components': {},
            'confidence': 0.0,
            'suggestions': []
        }
        
        for convention_name, pattern in self.naming_conventions.items():
            match = re.match(pattern, filename)
            if match:
                results['convention'] = convention_name
                results['confidence'] = 0.8
                
                # Extract components based on convention
                if convention_name == 'aec_standard':
                    results['components'] = {
                        'discipline': match.group(1),
                        'number': match.group(2),
                        'phase': match.group(3),
                        'revision': match.group(4)
                    }
                elif convention_name == 'project_based':
                    results['components'] = {
                        'project': match.group(1),
                        'discipline': match.group(2),
                        'number': match.group(3)
                    }
                # Add more convention parsing as needed
                
                break
        
        if not results['convention']:
            results['suggestions'] = self._suggest_naming_improvements(filename)
        
        return results


class ProjectTemplateManager:
    """
    Manages project templates and provides intelligent project setup.
    """
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.file_detector = IntelligentFileDetector()
    
    def _initialize_templates(self) -> Dict[str, ProjectTemplate]:
        """Initialize project templates."""
        return {
            'architectural': ProjectTemplate(
                name='Architectural Project',
                description='Standard architectural project structure',
                directory_structure={
                    'root': [
                        '00_Project_Management',
                        '01_Design_Development',
                        '02_Construction_Documents',
                        '03_Specifications',
                        '04_3D_Models',
                        '05_Renderings',
                        '06_Reference',
                        '07_Coordination',
                        '08_Submittals',
                        '09_As_Built'
                    ],
                    'design_development': [
                        'Architectural',
                        'Structural', 
                        'MEP',
                        'Landscape',
                        'Interiors'
                    ],
                    'construction_docs': [
                        'Drawings',
                        'Details',
                        'Schedules',
                        'Specifications'
                    ]
                },
                file_naming_patterns={
                    'drawings': 'A-{number}-{description}',
                    'details': 'A-{number}-D{detail_number}',
                    'schedules': 'A-{number}-SCH'
                },
                disciplines=['architectural', 'structural', 'mechanical', 'electrical', 'plumbing'],
                typical_file_types={'.dwg', '.rvt', '.skp', '.pdf', '.jpg', '.png'},
                metadata_requirements={
                    'drawings': ['discipline', 'sheet_number', 'revision', 'date'],
                    'models': ['discipline', 'phase', 'lod', 'date'],
                    'documents': ['type', 'discipline', 'revision', 'date']
                }
            ),
            
            'engineering': ProjectTemplate(
                name='Engineering Project',
                description='Multi-discipline engineering project structure',
                directory_structure={
                    'root': [
                        '00_Project_Management',
                        '01_Civil',
                        '02_Structural',
                        '03_Mechanical',
                        '04_Electrical',
                        '05_Calculations',
                        '06_Models',
                        '07_Specifications',
                        '08_Reports',
                        '09_Coordination'
                    ],
                    'calculations': [
                        'Structural',
                        'Mechanical',
                        'Electrical',
                        'Civil'
                    ]
                },
                file_naming_patterns={
                    'structural': 'S-{number}-{description}',
                    'mechanical': 'M-{number}-{description}',
                    'electrical': 'E-{number}-{description}',
                    'civil': 'C-{number}-{description}'
                },
                disciplines=['civil', 'structural', 'mechanical', 'electrical'],
                typical_file_types={'.dwg', '.dgn', '.xlsx', '.pdf', '.rvt'},
                metadata_requirements={
                    'calculations': ['discipline', 'type', 'engineer', 'date'],
                    'drawings': ['discipline', 'sheet_number', 'revision', 'date'],
                    'reports': ['type', 'author', 'revision', 'date']
                }
            ),
            
            'infrastructure': ProjectTemplate(
                name='Infrastructure Project',
                description='Civil infrastructure project structure',
                directory_structure={
                    'root': [
                        '00_Project_Management',
                        '01_Survey',
                        '02_Civil_Design',
                        '03_Utilities',
                        '04_Environmental',
                        '05_Geotechnical',
                        '06_Traffic',
                        '07_Construction',
                        '08_As_Built'
                    ],
                    'survey': [
                        'Field_Data',
                        'Point_Clouds',
                        'CAD_Files',
                        'Reports'
                    ]
                },
                file_naming_patterns={
                    'civil': 'C-{number}-{description}',
                    'utility': 'U-{number}-{description}',
                    'survey': 'SV-{number}-{description}'
                },
                disciplines=['civil', 'survey', 'environmental', 'geotechnical'],
                typical_file_types={'.dgn', '.dwg', '.las', '.pdf', '.xlsx'},
                metadata_requirements={
                    'survey': ['coordinate_system', 'date', 'surveyor'],
                    'design': ['discipline', 'phase', 'designer', 'date']
                }
            ),
            
            'bim': ProjectTemplate(
                name='BIM Project',
                description='Building Information Modeling project structure',
                directory_structure={
                    'root': [
                        '00_Project_Management',
                        '01_BIM_Models',
                        '02_Coordination',
                        '03_Clash_Detection',
                        '04_4D_5D',
                        '05_Families_Library',
                        '06_Standards',
                        '07_Exchange',
                        '08_Archive'
                    ],
                    'bim_models': [
                        'Architectural',
                        'Structural',
                        'MEP',
                        'Federated'
                    ],
                    'coordination': [
                        'BCF_Issues',
                        'Clash_Reports',
                        'Meeting_Minutes'
                    ]
                },
                file_naming_patterns={
                    'models': '{project}_{discipline}_{phase}_{lod}',
                    'families': '{category}_{type}_{size}',
                    'coordination': '{project}_COORD_{date}'
                },
                disciplines=['architectural', 'structural', 'mechanical', 'electrical', 'plumbing'],
                typical_file_types={'.rvt', '.rfa', '.ifc', '.nwf', '.nwd'},
                metadata_requirements={
                    'models': ['discipline', 'lod', 'phase', 'author', 'version'],
                    'families': ['category', 'type', 'author', 'version'],
                    'coordination': ['participants', 'date', 'issues_count']
                }
            )
        }
    
    def detect_project_type(self, project_path: str) -> Tuple[str, float]:
        """
        Detect the most likely project type based on existing files and structure.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Tuple of (template_name, confidence_score)
        """
        path_obj = Path(project_path)
        if not path_obj.exists():
            return 'architectural', 0.0  # Default template
        
        # Analyze existing files
        file_analysis = self._analyze_existing_files(path_obj)
        
        # Score templates based on file analysis
        template_scores = {}
        
        for template_name, template in self.templates.items():
            score = 0.0
            
            # Score based on file types
            for file_ext in file_analysis['file_types']:
                if file_ext in template.typical_file_types:
                    score += 0.2
            
            # Score based on disciplines detected
            for discipline in file_analysis['disciplines']:
                if discipline in template.disciplines:
                    score += 0.3
            
            # Score based on existing directory structure
            for existing_dir in file_analysis['directories']:
                for template_dirs in template.directory_structure.values():
                    if any(existing_dir.lower() in template_dir.lower() for template_dir in template_dirs):
                        score += 0.1
            
            template_scores[template_name] = min(score, 1.0)
        
        # Return template with highest score
        if template_scores:
            best_template = max(template_scores.items(), key=lambda x: x[1])
            return best_template[0], best_template[1]
        
        return 'architectural', 0.0
    
    def _analyze_existing_files(self, path: Path) -> Dict[str, Any]:
        """Analyze existing files in a project directory."""
        analysis = {
            'file_types': set(),
            'disciplines': set(),
            'directories': [],
            'file_count': 0,
            'naming_patterns': []
        }
        
        try:
            # Sample files for analysis (limit to avoid performance issues)
            sample_files = []
            for file_path in path.rglob('*'):
                if file_path.is_file() and len(sample_files) < 100:
                    sample_files.append(file_path)
                elif file_path.is_dir():
                    analysis['directories'].append(file_path.name)
            
            analysis['file_count'] = len(sample_files)
            
            # Analyze file types and disciplines
            for file_path in sample_files:
                file_info = self.file_detector.detect_file_type(str(file_path))
                if file_info:
                    analysis['file_types'].add(file_info.extension)
                    analysis['disciplines'].add(file_info.discipline)
                
                # Analyze naming patterns
                naming_analysis = self.file_detector.analyze_naming_convention(str(file_path))
                if naming_analysis['convention']:
                    analysis['naming_patterns'].append(naming_analysis['convention'])
        
        except Exception as e:
            # If analysis fails, return empty analysis
            pass
        
        return analysis
    
    def create_project_structure(
        self, 
        project_path: str, 
        template_name: str = None,
        custom_structure: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create project directory structure based on template.
        
        Args:
            project_path: Base path for the project
            template_name: Name of template to use (auto-detect if None)
            custom_structure: Custom directory structure override
            
        Returns:
            Dictionary with creation results
        """
        path_obj = Path(project_path)
        
        # Auto-detect template if not specified
        if not template_name:
            template_name, confidence = self.detect_project_type(project_path)
        
        template = self.templates.get(template_name)
        if not template:
            return {
                'success': False,
                'message': f'Unknown template: {template_name}',
                'directories_created': []
            }
        
        # Use custom structure if provided, otherwise use template
        structure = custom_structure or template.directory_structure
        
        created_directories = []
        
        try:
            # Create root directories
            for dir_name in structure.get('root', []):
                dir_path = path_obj / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_directories.append(str(dir_path))
            
            # Create subdirectories
            for parent_key, subdirs in structure.items():
                if parent_key == 'root':
                    continue
                
                # Find parent directory
                parent_dir = None
                for root_dir in structure.get('root', []):
                    if parent_key.lower() in root_dir.lower().replace('_', ' '):
                        parent_dir = path_obj / root_dir
                        break
                
                if parent_dir and parent_dir.exists():
                    for subdir_name in subdirs:
                        subdir_path = parent_dir / subdir_name
                        if not subdir_path.exists():
                            subdir_path.mkdir(parents=True, exist_ok=True)
                            created_directories.append(str(subdir_path))
            
            # Create template-specific files
            self._create_template_files(path_obj, template)
            
            return {
                'success': True,
                'message': f'Created {template.name} structure',
                'template_used': template_name,
                'directories_created': created_directories,
                'total_directories': len(created_directories)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to create structure: {e}',
                'directories_created': created_directories
            }
    
    def _create_template_files(self, project_path: Path, template: ProjectTemplate) -> None:
        """Create template-specific configuration files."""
        try:
            # Create project metadata file
            metadata_file = project_path / '.aec_project_metadata.json'
            if not metadata_file.exists():
                metadata = {
                    'template': template.name,
                    'created_date': datetime.now().isoformat(),
                    'disciplines': template.disciplines,
                    'naming_patterns': template.file_naming_patterns,
                    'metadata_requirements': template.metadata_requirements
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Create README file with template information
            readme_file = project_path / 'README.md'
            if not readme_file.exists():
                readme_content = f"""# {template.name}

{template.description}

## Directory Structure

This project follows the {template.name} template with the following structure:

"""
                for dir_name in template.directory_structure.get('root', []):
                    readme_content += f"- `{dir_name}/`\n"
                
                readme_content += f"""
## File Naming Conventions

"""
                for pattern_type, pattern in template.file_naming_patterns.items():
                    readme_content += f"- {pattern_type.title()}: `{pattern}`\n"
                
                readme_content += f"""
## Supported Disciplines

{', '.join(template.disciplines)}

## Typical File Types

{', '.join(sorted(template.typical_file_types))}

Generated by AEC Directory Scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                with open(readme_file, 'w') as f:
                    f.write(readme_content)
                    
        except Exception as e:
            # If file creation fails, continue silently
            pass
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        template = self.templates.get(template_name)
        if not template:
            return None
        
        return {
            'name': template.name,
            'description': template.description,
            'directory_structure': template.directory_structure,
            'file_naming_patterns': template.file_naming_patterns,
            'disciplines': template.disciplines,
            'typical_file_types': list(template.typical_file_types),
            'metadata_requirements': template.metadata_requirements
        }
    
    def list_available_templates(self) -> List[Dict[str, str]]:
        """List all available project templates."""
        return [
            {
                'name': name,
                'title': template.name,
                'description': template.description,
                'disciplines': ', '.join(template.disciplines)
            }
            for name, template in self.templates.items()
        ]


# Global instances for easy access
_file_detector = None
_template_manager = None

def get_file_detector() -> IntelligentFileDetector:
    """Get global file detector instance."""
    global _file_detector
    if _file_detector is None:
        _file_detector = IntelligentFileDetector()
    return _file_detector

def get_template_manager() -> ProjectTemplateManager:
    """Get global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = ProjectTemplateManager()
    return _template_manager