"""
AEC Directory Scanner and Metadata Database System

A comprehensive Python-based software system that automatically builds and manages
the standardized AEC project directory structure, scans all files within the directory
tree, extracts detailed metadata from each file, and stores this information in a
structured database.
"""

__version__ = "1.0.0"
__author__ = "AEC Development Team"

from .core.directory_manager import AECDirectoryManager
from .core.file_scanner import FileSystemScanner
from .core.metadata_extractor import MetadataExtractor
from .database.database_manager import DatabaseManager
from .main import AECDirectoryScanner

__all__ = [
    "AECDirectoryManager",
    "FileSystemScanner", 
    "MetadataExtractor",
    "DatabaseManager",
    "AECDirectoryScanner"
]