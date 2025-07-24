"""
AEC Directory Scanner - Main Controller

The main application controller that orchestrates the complete scanning and
metadata extraction process for AEC project directories.
"""

import os
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable

from .core.directory_manager import AECDirectoryManager
from .core.file_scanner import FileSystemScanner, FileInfo
from .core.metadata_extractor import MetadataExtractor, ExtractorResult
from .database.database_manager import DatabaseManager
from .utils.config_manager import ConfigManager
from .utils.error_handler import ErrorHandler


class AECDirectoryScanner:
    """
    Main application controller that orchestrates the complete scanning and
    metadata extraction process for AEC project directories.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AEC Directory Scanner.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Initialize configuration
        self.config = ConfigManager(config_path)
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self.logger)
        
        # Initialize core components
        self.directory_manager = AECDirectoryManager(self.logger)
        
        self.file_scanner = FileSystemScanner(
            logger=self.logger,
            max_workers=self.config.get('scanning.max_workers', 4),
            hash_files=self.config.get('scanning.generate_hashes', False),
            excluded_extensions=set(self.config.get('scanning.excluded_extensions', [])),
            excluded_directories=set(self.config.get('scanning.excluded_directories', []))
        )
        
        self.metadata_extractor = MetadataExtractor(self.logger)
        
        # Initialize database
        db_config = self.config.get('database', {})
        connection_string = self._build_connection_string(db_config)
        self.database = DatabaseManager(connection_string, self.logger)
        
        # Initialize database schema
        if not self.database.initialize_database():
            raise RuntimeError("Failed to initialize database")
        
        self.logger.info("AEC Directory Scanner initialized successfully")
    
    def _build_connection_string(self, db_config: Dict[str, Any]) -> str:
        """Build database connection string from configuration."""
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = db_config.get('path', 'aec_scanner.db')
            # Ensure absolute path
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.getcwd(), db_path)
            return db_path
        
        elif db_type == 'postgresql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('database', 'aec_projects')
            username = db_config.get('username', 'aec_user')
            password = db_config.get('password', '')
            
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def initialize_project(
        self, 
        project_number: str, 
        project_name: str, 
        base_path: str
    ) -> Dict[str, Union[bool, str, int]]:
        """
        Initialize a new AEC project with standard directory structure.
        
        Args:
            project_number: Unique project identifier
            project_name: Human-readable project name
            base_path: Root path where project will be created
            
        Returns:
            Dictionary containing initialization results
        """
        try:
            self.logger.info(f"Initializing project: {project_number} - {project_name}")
            
            # Create directory structure
            structure_result = self.directory_manager.create_project_structure(
                project_number, project_name, base_path
            )
            
            if not structure_result["success"]:
                return {
                    "success": False,
                    "message": "Failed to create directory structure",
                    "errors": structure_result["errors"]
                }
            
            # Insert project into database
            project_data = {
                "project_number": project_number,
                "project_name": project_name,
                "base_path": structure_result["project_path"],
                "status": "active"
            }
            
            project_id = self.database.insert_project(project_data)
            
            if not project_id:
                return {
                    "success": False,
                    "message": "Failed to create database record",
                    "errors": ["Database insertion failed"]
                }
            
            self.logger.info(f"Project initialized successfully with ID: {project_id}")
            
            return {
                "success": True,
                "message": f"Project {project_number} initialized successfully",
                "project_id": project_id,
                "project_path": structure_result["project_path"],
                "created_directories": len(structure_result["created_directories"])
            }
            
        except Exception as e:
            error_msg = f"Project initialization failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
    
    def scan_project(
        self, 
        project_id: int, 
        scan_type: str = 'full',
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Perform a comprehensive scan of a project directory.
        
        Args:
            project_id: Database ID of the project
            scan_type: Type of scan ('full', 'incremental', 'validation')
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing scan results and statistics
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get project information
            project_info = self.database.get_files_by_project(project_id, limit=1)
            if not project_info:
                # Try to get project from projects table
                with self.database.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                    project_row = cursor.fetchone()
                    
                    if not project_row:
                        return {
                            "success": False,
                            "message": f"Project {project_id} not found",
                            "scan_time": 0
                        }
                    
                    project_path = project_row[3] if hasattr(project_row, '__getitem__') else project_row['base_path']
            else:
                # Extract project path from first file
                first_file = project_info[0]
                project_path = str(Path(first_file['file_path']).parents[2])  # Go up to project root
            
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "message": f"Project path does not exist: {project_path}",
                    "scan_time": 0
                }
            
            self.logger.info(f"Starting {scan_type} scan of project {project_id} at {project_path}")
            
            # Perform scan based on type
            scan_results = []
            
            if scan_type == 'full':
                scan_results = self.file_scanner.scan_directory(
                    project_path, 
                    recursive=True,
                    progress_callback=progress_callback
                )
            
            elif scan_type == 'incremental':
                # Get last scan time
                with self.database.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT MAX(end_time) FROM scan_history 
                        WHERE project_id = ? AND scan_status = 'completed'
                        """,
                        (project_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        last_scan_time = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                    else:
                        last_scan_time = datetime.min.replace(tzinfo=timezone.utc)
                
                scan_results = self.file_scanner.incremental_scan(
                    project_path, 
                    last_scan_time,
                    progress_callback=progress_callback
                )
            
            elif scan_type == 'validation':
                # Validation scan - check file integrity
                scan_results = self.file_scanner.scan_directory(project_path, recursive=True)
                # TODO: Add validation logic to check against database records
            
            # Process scan results
            files_added = 0
            files_updated = 0
            errors = []
            
            for file_info in scan_results:
                try:
                    # Check if file already exists in database
                    existing_file = self.database.get_file_by_path(file_info.file_path)
                    
                    # Prepare file data for database
                    file_data = {
                        "project_id": project_id,
                        "directory_id": None,  # TODO: Implement directory tracking
                        "file_name": file_info.file_name,
                        "file_path": file_info.file_path,
                        "file_extension": file_info.file_extension,
                        "file_size": file_info.file_size,
                        "file_hash": file_info.file_hash,
                        "created_at": file_info.created_time.isoformat(),
                        "modified_at": file_info.modified_time.isoformat(),
                        "last_accessed": file_info.accessed_time.isoformat()
                    }
                    
                    # Insert or update file record
                    file_id = self.database.insert_file_record(file_data)
                    
                    if file_id:
                        if existing_file:
                            files_updated += 1
                        else:
                            files_added += 1
                    
                except Exception as e:
                        error_msg = f"Error processing file {file_info.file_path}: {str(e)}"
                        self.logger.warning(error_msg)
                        errors.append(error_msg)
            
            end_time = datetime.now(timezone.utc)
            scan_duration = (end_time - start_time).total_seconds()
            
            # Record scan session
            scan_session_data = {
                "project_id": project_id,
                "scan_type": scan_type,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "files_scanned": len(scan_results),
                "files_added": files_added,
                "files_updated": files_updated,
                "files_removed": 0,  # TODO: Implement file removal detection
                "errors_encountered": len(errors),
                "scan_status": "completed" if len(errors) == 0 else "completed_with_errors",
                "errors": errors
            }
            
            session_id = self.database.record_scan_session(scan_session_data)
            
            self.logger.info(
                f"Scan completed: {len(scan_results)} files processed, "
                f"{files_added} added, {files_updated} updated, "
                f"{len(errors)} errors in {scan_duration:.2f}s"
            )
            
            return {
                "success": True,
                "scan_session_id": session_id,
                "scan_type": scan_type,
                "files_scanned": len(scan_results),
                "files_added": files_added,
                "files_updated": files_updated,
                "errors_encountered": len(errors),
                "errors": errors,
                "scan_time": scan_duration,
                "message": f"Scan completed successfully in {scan_duration:.2f} seconds"
            }
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            scan_duration = (end_time - start_time).total_seconds()
            
            error_msg = f"Scan failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Try to record failed scan session
            try:
                scan_session_data = {
                    "project_id": project_id,
                    "scan_type": scan_type,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "files_scanned": 0,
                    "files_added": 0,
                    "files_updated": 0,
                    "files_removed": 0,
                    "errors_encountered": 1,
                    "scan_status": "failed",
                    "errors": [error_msg]
                }
                self.database.record_scan_session(scan_session_data)
            except Exception:
                pass  # Don't fail if we can't record the failed session
            
            return {
                "success": False,
                "message": error_msg,
                "scan_time": scan_duration,
                "errors": [error_msg]
            }
    
    def extract_all_metadata(
        self, 
        project_id: int, 
        force_refresh: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from all files in a project.
        
        Args:
            project_id: Database ID of the project
            force_refresh: Whether to re-extract metadata for all files
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing metadata extraction results
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Starting metadata extraction for project {project_id}")
            
            # Get all files for the project
            files = self.database.get_files_by_project(project_id)
            
            if not files:
                return {
                    "success": False,
                    "message": f"No files found for project {project_id}",
                    "extraction_time": 0
                }
            
            total_files = len(files)
            processed_files = 0
            metadata_extracted = 0
            errors = []
            
            for i, file_record in enumerate(files):
                try:
                    file_path = file_record['file_path']
                    file_id = file_record['id']
                    
                    # Check if metadata already exists (unless force refresh)
                    if not force_refresh:
                        with self.database.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT COUNT(*) FROM file_metadata WHERE file_id = ?",
                                (file_id,)
                            )
                            existing_metadata = cursor.fetchone()[0]
                            
                            if existing_metadata > 0:
                                processed_files += 1
                                if progress_callback:
                                    progress_callback(i + 1, total_files)
                                continue
                    
                    # Extract metadata
                    extraction_result = self.metadata_extractor.extract_metadata(file_path)
                    
                    if extraction_result.success:
                        # Extract AEC-specific metadata
                        aec_metadata = self.metadata_extractor.extract_aec_metadata(file_path)
                        extraction_result.metadata["aec_metadata"] = aec_metadata
                        
                        # Generate content summary
                        content_summary = self.metadata_extractor.extract_content_summary(file_path)
                        extraction_result.metadata["content_summary"] = content_summary
                        
                        # Update database with metadata
                        if self.database.update_file_metadata(file_id, extraction_result.metadata):
                            metadata_extracted += 1
                        else:
                            errors.append(f"Failed to save metadata for {file_path}")
                    else:
                        errors.extend(extraction_result.errors)
                    
                    processed_files += 1
                    
                    if progress_callback:
                        progress_callback(i + 1, total_files)
                    
                except Exception as e:
                    error_msg = f"Error extracting metadata from {file_record.get('file_path', 'unknown')}: {str(e)}"
                    self.logger.warning(error_msg)
                    errors.append(error_msg)
                    processed_files += 1
            
            end_time = datetime.now(timezone.utc)
            extraction_duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"Metadata extraction completed: {processed_files} files processed, "
                f"{metadata_extracted} metadata records created, "
                f"{len(errors)} errors in {extraction_duration:.2f}s"
            )
            
            return {
                "success": True,
                "total_files": total_files,
                "processed_files": processed_files,
                "metadata_extracted": metadata_extracted,
                "errors_encountered": len(errors),
                "errors": errors,
                "extraction_time": extraction_duration,
                "message": f"Metadata extraction completed in {extraction_duration:.2f} seconds"
            }
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            extraction_duration = (end_time - start_time).total_seconds()
            
            error_msg = f"Metadata extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "message": error_msg,
                "extraction_time": extraction_duration,
                "errors": [error_msg]
            }
    
    def generate_project_report(self, project_id: int) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a project.
        
        Args:
            project_id: Database ID of the project
            
        Returns:
            Dictionary containing comprehensive project report
        """
        try:
            self.logger.info(f"Generating report for project {project_id}")
            
            # Get project statistics from database
            stats = self.database.get_project_statistics(project_id)
            
            if not stats:
                return {
                    "success": False,
                    "message": f"No data found for project {project_id}"
                }
            
            # Get project information
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                project_row = cursor.fetchone()
                
                if not project_row:
                    return {
                        "success": False,
                        "message": f"Project {project_id} not found"
                    }
            
            # Build comprehensive report
            report = {
                "success": True,
                "project_info": {
                    "project_id": project_id,
                    "project_number": project_row[1] if hasattr(project_row, '__getitem__') else project_row['project_number'],
                    "project_name": project_row[2] if hasattr(project_row, '__getitem__') else project_row['project_name'],
                    "base_path": project_row[3] if hasattr(project_row, '__getitem__') else project_row['base_path'],
                    "created_at": project_row[4] if hasattr(project_row, '__getitem__') else project_row['created_at'],
                    "status": project_row[6] if hasattr(project_row, '__getitem__') else project_row['status']
                },
                "file_statistics": {
                    "total_files": stats.get("total_files", 0),
                    "total_size_bytes": stats.get("total_size_bytes", 0),
                    "total_size_mb": round(stats.get("total_size_bytes", 0) / (1024 * 1024), 2),
                    "file_types": stats.get("file_types", []),
                    "disciplines": stats.get("disciplines", [])
                },
                "scan_history": stats.get("recent_scans", []),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Report generated successfully for project {project_id}")
            return report
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
    
    def validate_project_integrity(self, project_id: int) -> Dict[str, Any]:
        """
        Validate the integrity of a project's files and directory structure.
        
        Args:
            project_id: Database ID of the project
            
        Returns:
            Dictionary containing validation results
        """
        try:
            self.logger.info(f"Validating integrity of project {project_id}")
            
            # Get project base path
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT base_path FROM projects WHERE id = ?", (project_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {
                        "success": False,
                        "message": f"Project {project_id} not found"
                    }
                
                project_path = result[0]
            
            # Validate directory structure
            structure_validation = self.directory_manager.validate_structure(project_path)
            
            # Get database files and check if they exist on disk
            files = self.database.get_files_by_project(project_id)
            
            missing_files = []
            orphaned_records = []
            size_mismatches = []
            
            for file_record in files:
                file_path = file_record['file_path']
                
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
                else:
                    # Check file size
                    actual_size = os.path.getsize(file_path)
                    recorded_size = file_record.get('file_size', 0)
                    
                    if actual_size != recorded_size:
                        size_mismatches.append({
                            "file_path": file_path,
                            "recorded_size": recorded_size,
                            "actual_size": actual_size
                        })
            
            # Check for files on disk not in database
            if os.path.exists(project_path):
                disk_files = set()
                for root, dirs, files_list in os.walk(project_path):
                    for file_name in files_list:
                        disk_files.add(os.path.join(root, file_name))
                
                db_files = {f['file_path'] for f in files}
                orphaned_files = disk_files - db_files
                orphaned_records = list(orphaned_files)
            
            validation_results = {
                "success": True,
                "project_id": project_id,
                "project_path": project_path,
                "directory_structure": structure_validation,
                "file_validation": {
                    "total_files_in_db": len(files),
                    "missing_files": missing_files,
                    "missing_files_count": len(missing_files),
                    "orphaned_files": orphaned_records,
                    "orphaned_files_count": len(orphaned_records),
                    "size_mismatches": size_mismatches,
                    "size_mismatches_count": len(size_mismatches)
                },
                "overall_status": "healthy" if (
                    structure_validation["valid"] and 
                    len(missing_files) == 0 and 
                    len(size_mismatches) == 0
                ) else "issues_found",
                "validated_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Project validation completed: {validation_results['overall_status']}")
            return validation_results
            
        except Exception as e:
            error_msg = f"Project validation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
    
    def cleanup_orphaned_records(self, project_id: int) -> Dict[str, Any]:
        """
        Clean up orphaned database records for a project.
        
        Args:
            project_id: Database ID of the project
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            self.logger.info(f"Cleaning up orphaned records for project {project_id}")
            
            # Use database manager's cleanup method
            records_cleaned = self.database.cleanup_orphaned_records(project_id)
            
            return {
                "success": True,
                "project_id": project_id,
                "records_cleaned": records_cleaned,
                "message": f"Cleaned up {records_cleaned} orphaned records"
            }
            
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status information.
        
        Returns:
            Dictionary containing system status
        """
        try:
            # Get database info
            db_info = self.database.get_database_info()
            
            # Get configuration info
            config_info = {
                "config_loaded": self.config.config is not None,
                "config_path": self.config.config_path,
                "database_type": self.config.get('database.type', 'sqlite'),
                "max_workers": self.config.get('scanning.max_workers', 4)
            }
            
            return {
                "success": True,
                "system_info": {
                    "version": "1.0.0",
                    "started_at": datetime.now(timezone.utc).isoformat()
                },
                "database_info": db_info,
                "configuration": config_info,
                "components": {
                    "directory_manager": "initialized",
                    "file_scanner": "initialized", 
                    "metadata_extractor": "initialized",
                    "database_manager": "initialized"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get system status: {str(e)}",
                "errors": [str(e)]
            }
    
    def shutdown(self) -> None:
        """Gracefully shutdown the scanner and clean up resources."""
        try:
            self.logger.info("Shutting down AEC Directory Scanner")
            
            # Stop any ongoing file monitoring
            self.file_scanner.stop_monitoring()
            
            # Close database connections
            self.database.close_connection()
            
            self.logger.info("Shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")