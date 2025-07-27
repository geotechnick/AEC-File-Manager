"""
Smart Defaults and Auto-Detection

Intelligent system for automatically detecting project settings, 
providing smart defaults, and reducing user input requirements.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging


class SmartDefaults:
    """
    Smart defaults system that automatically detects project settings
    and provides intelligent defaults to minimize user input.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Common AEC project naming patterns
        self.project_patterns = {
            'year_first': r'^(\d{4})-?(.+)',  # 2024-Office Building
            'year_last': r'^(.+)-?(\d{4})$',  # Office Building-2024
            'project_code': r'^([A-Z]{2,6}\d{2,6})',  # PROJ2024, ABC123
            'discipline_code': r'[A-Z]{1,3}-\d+',  # A-001, MEP-101
        }
        
        # File type categorization
        self.file_categories = {
            'drawings': {'.dwg', '.dxf', '.dgn', '.rvt', '.rfa', '.ifc', '.skp'},
            'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
            'spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
            'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'},
            'models': {'.3dm', '.step', '.stp', '.iges', '.igs', '.obj', '.fbx'},
            'presentations': {'.ppt', '.pptx', '.odp'},
            'specifications': {'.spec', '.docx', '.pdf'},
            'calculations': {'.xls', '.xlsx', '.csv', '.pdf'}
        }
    
    def detect_project_info(self, path: str) -> Dict[str, Any]:
        """
        Auto-detect project information from directory path and contents.
        
        Args:
            path: Project directory path
            
        Returns:
            Dictionary with detected project information
        """
        path_obj = Path(path)
        directory_name = path_obj.name
        
        detected_info = {
            'project_number': None,
            'project_name': None,
            'project_year': None,
            'confidence_score': 0.0,
            'suggestions': [],
            'auto_detected': True
        }
        
        # Try to extract year
        year = self._extract_year(directory_name)
        if year:
            detected_info['project_year'] = year
            detected_info['confidence_score'] += 0.3
        
        # Try to extract project number/code
        project_code = self._extract_project_code(directory_name)
        if project_code:
            detected_info['project_number'] = project_code
            detected_info['confidence_score'] += 0.4
        
        # Extract/clean project name
        project_name = self._extract_project_name(directory_name, project_code, year)
        if project_name:
            detected_info['project_name'] = project_name
            detected_info['confidence_score'] += 0.3
        
        # Add suggestions based on detection confidence
        if detected_info['confidence_score'] < 0.5:
            detected_info['suggestions'] = self._generate_naming_suggestions(directory_name)
        
        self.logger.info(f"Auto-detected project info with {detected_info['confidence_score']:.1%} confidence")
        return detected_info
    
    def get_smart_defaults(self, detected_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate smart defaults based on detected information and current context.
        
        Args:
            detected_info: Previously detected project information
            
        Returns:
            Dictionary with smart default values
        """
        current_year = datetime.now().year
        
        defaults = {
            'project_year': detected_info.get('project_year') or current_year,
            'project_number': detected_info.get('project_number') or f"PROJ{current_year}",
            'project_name': detected_info.get('project_name') or "New AEC Project",
            'scan_settings': {
                'include_hidden_files': False,
                'max_file_size_mb': 100,
                'enable_metadata_extraction': True,
                'async_processing': True,
                'batch_size': 50
            },
            'database_settings': {
                'use_connection_pooling': True,
                'enable_query_caching': True,
                'backup_frequency': 'daily'
            },
            'output_preferences': {
                'format': 'summary',
                'show_progress': True,
                'verbose_errors': False
            }
        }
        
        return defaults
    
    def auto_configure_scan_settings(self, project_path: str) -> Dict[str, Any]:
        """
        Automatically configure scan settings based on project size and content.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Optimized scan configuration
        """
        path_obj = Path(project_path)
        
        if not path_obj.exists():
            return self._get_default_scan_settings()
        
        # Analyze directory structure
        analysis = self._analyze_directory_structure(path_obj)
        
        config = {
            'async_processing': analysis['total_files'] > 100,
            'batch_size': min(max(analysis['total_files'] // 10, 10), 100),
            'max_concurrent': min(analysis['directory_depth'] * 2, 10),
            'enable_hashing': analysis['total_size_mb'] < 1000,  # Only for smaller projects
            'memory_limit_mb': 512 if analysis['total_size_mb'] > 5000 else 256,
            'progress_updates': analysis['total_files'] > 50,
            'estimated_duration_minutes': self._estimate_scan_duration(analysis)
        }
        
        self.logger.info(f"Auto-configured scan for {analysis['total_files']} files "
                        f"({analysis['total_size_mb']:.1f}MB)")
        
        return config
    
    def suggest_directory_structure(self, project_type: str = 'general') -> Dict[str, List[str]]:
        """
        Suggest directory structure based on project type.
        
        Args:
            project_type: Type of AEC project
            
        Returns:
            Suggested directory structure
        """
        base_structure = {
            'root': [
                '00_Project_Management',
                '01_Design_Development', 
                '02_Construction_Documents',
                '03_Specifications',
                '04_Calculations',
                '05_Models_3D',
                '06_Presentations',
                '07_Reference_Materials',
                '08_Correspondence',
                '09_Submittals',
                '10_As_Built'
            ]
        }
        
        # Customize based on project type
        if project_type == 'architectural':
            base_structure['specialized'] = [
                '01_Design_Development/Architectural',
                '01_Design_Development/Structural', 
                '01_Design_Development/MEP',
                '05_Models_3D/Revit',
                '05_Models_3D/SketchUp'
            ]
        elif project_type == 'engineering':
            base_structure['specialized'] = [
                '01_Design_Development/Civil',
                '01_Design_Development/Structural',
                '01_Design_Development/Mechanical',
                '01_Design_Development/Electrical',
                '04_Calculations/Structural',
                '04_Calculations/MEP'
            ]
        
        return base_structure
    
    def detect_existing_projects(self, search_path: str) -> List[Dict[str, Any]]:
        """
        Detect existing AEC projects in a directory tree.
        
        Args:
            search_path: Root path to search for projects
            
        Returns:
            List of detected project information
        """
        detected_projects = []
        search_path_obj = Path(search_path)
        
        if not search_path_obj.exists():
            return detected_projects
        
        # Look for project indicators
        for item in search_path_obj.rglob('*'):
            if item.is_dir():
                # Check for AEC project patterns
                if self._looks_like_aec_project(item):
                    project_info = self.detect_project_info(str(item))
                    project_info['path'] = str(item)
                    project_info['size_analysis'] = self._get_quick_size_analysis(item)
                    detected_projects.append(project_info)
        
        # Sort by confidence score
        detected_projects.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        self.logger.info(f"Detected {len(detected_projects)} potential AEC projects")
        return detected_projects
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text."""
        year_match = re.search(r'(20\d{2})', text)
        if year_match:
            year = int(year_match.group(1))
            current_year = datetime.now().year
            if 2020 <= year <= current_year + 5:  # Reasonable year range
                return year
        return None
    
    def _extract_project_code(self, text: str) -> Optional[str]:
        """Extract project code from text."""
        # Look for patterns like PROJ2024, ABC123, etc.
        for pattern_name, pattern in self.project_patterns.items():
            if pattern_name == 'project_code':
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
        return None
    
    def _extract_project_name(self, text: str, project_code: Optional[str], year: Optional[int]) -> str:
        """Extract and clean project name."""
        cleaned_text = text
        
        # Remove project code if found
        if project_code:
            cleaned_text = cleaned_text.replace(project_code, '').strip()
        
        # Remove year if found
        if year:
            cleaned_text = re.sub(rf'\b{year}\b', '', cleaned_text).strip()
        
        # Remove common separators and clean up
        cleaned_text = re.sub(r'[-_]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Capitalize properly
        if cleaned_text:
            return ' '.join(word.capitalize() for word in cleaned_text.split())
        
        return text  # Return original if cleaning failed
    
    def _generate_naming_suggestions(self, directory_name: str) -> List[str]:
        """Generate naming suggestions for unclear project names."""
        current_year = datetime.now().year
        
        suggestions = [
            f"Consider using format: PROJ{current_year}-{directory_name}",
            f"Try: {directory_name.replace('_', ' ').replace('-', ' ').title()}",
            f"Format example: {current_year}-{directory_name.replace('_', '-')}"
        ]
        
        return suggestions
    
    def _analyze_directory_structure(self, path: Path) -> Dict[str, Any]:
        """Analyze directory structure for optimization."""
        analysis = {
            'total_files': 0,
            'total_size_mb': 0,
            'directory_depth': 0,
            'file_types': {},
            'largest_files': []
        }
        
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                        analysis['total_files'] += 1
                        analysis['total_size_mb'] += size / (1024 * 1024)
                        
                        # Track file types
                        ext = item.suffix.lower()
                        analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                        
                        # Track depth
                        depth = len(item.relative_to(path).parts)
                        analysis['directory_depth'] = max(analysis['directory_depth'], depth)
                        
                    except (OSError, PermissionError):
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Error analyzing directory structure: {e}")
        
        return analysis
    
    def _estimate_scan_duration(self, analysis: Dict[str, Any]) -> float:
        """Estimate scan duration in minutes based on analysis."""
        # Base estimate: 100 files per minute for small files
        base_rate = 100
        
        # Adjust for file size
        if analysis['total_size_mb'] > 1000:
            base_rate = 50  # Slower for large files
        elif analysis['total_size_mb'] > 5000:
            base_rate = 20  # Much slower for very large files
        
        # Adjust for directory depth
        depth_penalty = max(0, analysis['directory_depth'] - 5) * 0.1
        
        estimated_minutes = (analysis['total_files'] / base_rate) * (1 + depth_penalty)
        return max(0.1, estimated_minutes)  # Minimum 0.1 minutes
    
    def _looks_like_aec_project(self, path: Path) -> bool:
        """Check if directory looks like an AEC project."""
        # Check for AEC-related files
        aec_indicators = 0
        
        try:
            files = list(path.iterdir())[:50]  # Sample first 50 items
            
            for item in files:
                if item.is_file():
                    ext = item.suffix.lower()
                    
                    # Check for AEC file types
                    for category, extensions in self.file_categories.items():
                        if ext in extensions:
                            aec_indicators += 1
                            break
                
                elif item.is_dir():
                    # Check for AEC-related directory names
                    dir_name = item.name.lower()
                    aec_keywords = ['design', 'drawing', 'model', 'spec', 'calc', 'arch', 'struct', 'mep']
                    if any(keyword in dir_name for keyword in aec_keywords):
                        aec_indicators += 2
        
        except (OSError, PermissionError):
            return False
        
        return aec_indicators >= 3  # Threshold for considering it an AEC project
    
    def _get_quick_size_analysis(self, path: Path) -> Dict[str, Any]:
        """Get quick size analysis without deep traversal."""
        try:
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            file_count = sum(1 for f in path.rglob('*') if f.is_file())
            
            return {
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count,
                'estimated_scan_time': file_count / 100  # rough estimate
            }
        except Exception:
            return {'total_size_mb': 0, 'file_count': 0, 'estimated_scan_time': 0}
    
    def _get_default_scan_settings(self) -> Dict[str, Any]:
        """Get default scan settings when analysis fails."""
        return {
            'async_processing': True,
            'batch_size': 50,
            'max_concurrent': 5,
            'enable_hashing': True,
            'memory_limit_mb': 256,
            'progress_updates': True,
            'estimated_duration_minutes': 1.0
        }