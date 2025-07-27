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
from .core.async_file_scanner import AsyncFileSystemScanner
from .core.metadata_extractor import MetadataExtractor, ExtractorResult
from .database.database_manager import DatabaseManager
from .utils.config_manager import ConfigManager
from .utils.error_handler import ErrorHandler
from .utils.memory_manager import get_resource_manager, MemoryMonitor
from .utils.security_validator import SecurityManager
from .exceptions import (
    AECScannerException, DatabaseError, FileSystemError, ScanningError,
    MetadataExtractionError, ConfigurationError, ValidationError, 
    ProjectNotFoundError, ResourceLimitError, RetryableError
)


class AECDirectoryScanner:
    """
    Main application controller that orchestrates the complete scanning and
    metadata extraction process for AEC project directories.
    """
    
    def __init__(self, config_path: Optional[str] = None, enable_async: bool = True):
        """
        Initialize the AEC Directory Scanner with optimizations.
        
        Args:
            config_path: Optional path to configuration file
            enable_async: Enable async file operations for better performance
        """
        try:
            # Initialize configuration with hot-reload support
            self.config = ConfigManager(config_path, enable_hot_reload=True)
            
            # Initialize logging
            self.logger = logging.getLogger(__name__)
            
            # Validate configuration
            config_errors = self.config.validate_configuration_schema()
            if config_errors:
                for error in config_errors:
                    self.logger.warning(f"Configuration warning: {error}")
            
            # Initialize security manager
            allowed_paths = [self.config.get('scanning.allowed_base_paths', [])]
            if isinstance(allowed_paths[0], list):
                allowed_paths = allowed_paths[0]
            self.security_manager = SecurityManager(allowed_paths)
            
            # Initialize resource manager and memory monitoring
            self.resource_manager = get_resource_manager()
            self.memory_monitor = MemoryMonitor(
                warning_threshold=self.config.get('performance.memory_warning_threshold', 80.0),
                critical_threshold=self.config.get('performance.memory_critical_threshold', 90.0)
            )
            self.memory_monitor.start_monitoring()
            
            # Initialize error handler
            self.error_handler = ErrorHandler(self.logger)
            
            # Initialize core components
            self.directory_manager = AECDirectoryManager(self.logger)
            
            # Initialize file scanners (both sync and async)
            scanner_config = {
                'logger': self.logger,
                'max_workers': self.config.get('scanning.max_workers', 4),
                'hash_files': self.config.get('scanning.generate_hashes', False),
                'excluded_extensions': set(self.config.get('scanning.excluded_extensions', [])),
                'excluded_directories': set(self.config.get('scanning.excluded_directories', []))
            }
            
            self.file_scanner = FileSystemScanner(**scanner_config)
            
            if enable_async:
                async_config = scanner_config.copy()
                async_config['max_concurrent'] = async_config.pop('max_workers')
                self.async_file_scanner = AsyncFileSystemScanner(**async_config)
            else:
                self.async_file_scanner = None
            
            self.metadata_extractor = MetadataExtractor(self.logger)
            
            # Initialize database with connection pooling
            db_config = self.config.get('database', {})
            connection_string = self._build_connection_string(db_config)
            max_connections = self.config.get('performance.max_db_connections', 10)
            
            self.database = DatabaseManager(
                connection_string, 
                self.logger,
                connection_timeout=self.config.get('performance.connection_timeout', 30),
                max_connections=max_connections
            )
            
            # Initialize database schema
            if not self.database.initialize_database():
                raise DatabaseError("Failed to initialize database schema", "initialization")
            
            # Set up configuration change callback
            self.config.add_change_callback(self._handle_config_change)
            
            # Log system information
            system_info = self.resource_manager.get_system_info()
            self.logger.info(f"AEC Directory Scanner initialized successfully")
            self.logger.info(f"System info - Memory: {system_info['memory']['total_mb']:.1f}MB, "
                           f"CPU cores: {system_info['cpu']['count']}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AEC Directory Scanner: {e}")
            raise AECScannerException(f"Initialization failed: {e}") from e
    
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
        base_path: str,
        project_year: Optional[str] = None
    ) -> Dict[str, Union[bool, str, int]]:
        """
        Initialize a new AEC project with standard directory structure and security validation.
        
        Args:
            project_number: Unique project identifier
            project_name: Human-readable project name
            base_path: Root path where project will be created
            project_year: Optional project year (defaults to current year)
            
        Returns:
            Dictionary containing initialization results
        """
        try:
            self.logger.info(f"Initializing project: {project_number} - {project_name} ({project_year or 'current year'})")
            
            # Security validation
            validated_data = self.security_manager.validate_project_creation(
                project_number, project_name, base_path
            )
            
            # Check disk space requirements (estimate ~100MB for directory structure)
            self.resource_manager.check_disk_space(validated_data['base_path'], 100)
            
            # Create directory structure
            structure_result = self.directory_manager.create_project_structure(
                validated_data['project_number'], 
                validated_data['project_name'], 
                validated_data['base_path'], 
                project_year
            )
            
            if not structure_result["success"]:
                return {
                    "success": False,
                    "message": "Failed to create directory structure",
                    "errors": structure_result["errors"]
                }
            
            # Insert project into database
            project_data = {
                "project_number": validated_data['project_number'],
                "project_name": validated_data['project_name'],
                "base_path": structure_result["project_path"],
                "status": "active"
            }
            
            project_id = self.database.insert_project(project_data)
            
            if not project_id:
                raise DatabaseError("Failed to create database record", "insert", "projects")
            
            self.logger.info(f"Project initialized successfully with ID: {project_id}")
            
            return {
                "success": True,
                "message": f"Project {validated_data['project_number']} initialized successfully",
                "project_id": project_id,
                "project_path": structure_result["project_path"],
                "created_directories": len(structure_result.get("created_directories", []))
            }
            
        except (ValidationError, ResourceLimitError, DatabaseError) as e:
            error_msg = f"Project initialization failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
        except Exception as e:
            error_msg = f"Project initialization failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)]
            }
    
    async def scan_project_async(
        self, 
        project_id: int, 
        scan_type: str = 'full',
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Perform async scan of a project directory for improved performance.
        
        Args:
            project_id: Database ID of the project
            scan_type: Type of scan ('full', 'incremental', 'validation')
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing scan results and statistics
        """
        if not self.async_file_scanner:
            # Fall back to synchronous scanning
            return self.scan_project(project_id, scan_type, progress_callback)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get project path
            project_path = await self._get_project_path_async(project_id)
            
            if not os.path.exists(project_path):
                raise ProjectNotFoundError(project_id)
            
            self.logger.info(f"Starting async {scan_type} scan of project {project_id} at {project_path}")
            
            # Check memory before starting scan
            estimated_memory = self._estimate_scan_memory_usage(project_path)
            self.memory_monitor.check_memory_limit(estimated_memory, f"async scan of project {project_id}")
            
            # Perform async scan
            if scan_type == 'incremental':
                last_scan_time = await self._get_last_scan_time_async(project_id)
                scan_results = await self.async_file_scanner.incremental_scan_async(
                    project_path, last_scan_time, progress_callback
                )
            else:
                scan_results = await self.async_file_scanner.scan_directory_async(
                    project_path, recursive=True, progress_callback=progress_callback
                )
            
            # Process results using streaming to manage memory
            files_added, files_updated, errors = await self._process_scan_results_async(
                project_id, scan_results
            )
            
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
                "files_removed": self._detect_removed_files(project_id, scan_results),
                "errors_encountered": len(errors),
                "scan_status": "completed" if len(errors) == 0 else "completed_with_errors",
                "errors": errors
            }
            
            session_id = self.database.record_scan_session(scan_session_data)
            
            self.logger.info(
                f"Async scan completed: {len(scan_results)} files processed, "
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
                "message": f"Async scan completed successfully in {scan_duration:.2f} seconds"
            }
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            scan_duration = (end_time - start_time).total_seconds()
            
            error_msg = f"Async scan failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "message": error_msg,
                "scan_time": scan_duration,
                "errors": [error_msg]
            }
    
    async def _get_project_path_async(self, project_id: int) -> str:
        """Get project path async."""
        # This would be implemented with async database operations
        # For now, using sync version
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT base_path FROM projects WHERE id = ?", (project_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ProjectNotFoundError(project_id)
            
            return result[0]
    
    async def _get_last_scan_time_async(self, project_id: int) -> datetime:
        """Get last scan time async."""
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
                return datetime.fromisoformat(result[0].replace('Z', '+00:00'))
            else:
                return datetime.min.replace(tzinfo=timezone.utc)
    
    async def _process_scan_results_async(self, project_id: int, scan_results: List[FileInfo]) -> tuple:
        """Process scan results async with memory management."""
        from .utils.memory_manager import StreamingProcessor
        
        processor = StreamingProcessor(
            batch_size=self.config.get('scanning.batch_size', 1000),
            memory_limit_mb=self.config.get('performance.cache_size_mb', 100)
        )
        
        files_added = 0
        files_updated = 0
        errors = []
        
        def process_batch(batch):
            batch_added = 0
            batch_updated = 0
            batch_errors = []
            
            for file_info in batch:
                try:
                    # Validate file operation
                    validated_path = self.security_manager.validate_file_operation(
                        file_info.file_path, 'read', file_info.file_size
                    )
                    
                    # Check if file already exists in database
                    existing_file = self.database.get_file_by_path(validated_path)
                    
                    # Prepare file data for database
                    file_data = {
                        "project_id": project_id,
                        "directory_id": self._get_or_create_directory_id(project_id, file_info.parent_directory),
                        "file_name": file_info.file_name,
                        "file_path": validated_path,
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
                            batch_updated += 1
                        else:
                            batch_added += 1
                    
                except Exception as e:
                    error_msg = f"Error processing file {file_info.file_path}: {str(e)}"
                    batch_errors.append(error_msg)
            
            return batch_added, batch_updated, batch_errors
        
        # Process in batches
        async for result in processor.process_in_batches(iter(scan_results), process_batch):
            batch_added, batch_updated, batch_errors = result
            files_added += batch_added
            files_updated += batch_updated
            errors.extend(batch_errors)
        
        return files_added, files_updated, errors
    
    def _estimate_scan_memory_usage(self, project_path: str) -> float:
        """Estimate memory usage for scanning a directory."""
        try:
            # Quick count of files to estimate memory usage
            file_count = sum(1 for _ in Path(project_path).rglob('*') if _.is_file())
            
            # Estimate ~1KB per file info object
            estimated_mb = (file_count * 1024) / (1024 * 1024)
            
            # Add safety margin
            return estimated_mb * 1.5
            
        except Exception:
            # Conservative estimate if counting fails
            return 100.0
    
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
                # Validate against database records
                scan_results = self._validate_scan_results(project_id, scan_results)
            
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
                        "directory_id": self._get_or_create_directory_id(project_id, file_info.parent_directory),
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
                "files_removed": self._detect_removed_files(project_id, scan_results),
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
    
    def _validate_scan_results(self, project_id: int, scan_results: List[FileInfo]) -> List[FileInfo]:
        """
        Validate scan results against database records.
        
        Args:
            project_id: Project ID
            scan_results: List of FileInfo from scan
            
        Returns:
            Filtered list of files that need processing
        """
        validated_results = []
        
        for file_info in scan_results:
            try:
                # Check if file exists in database
                existing_file = self.database.get_file_by_path(file_info.file_path)
                
                if existing_file:
                    # Validate file integrity - check if modified
                    db_modified = datetime.fromisoformat(existing_file['modified_at'].replace('Z', '+00:00'))
                    if file_info.modified_time > db_modified:
                        validated_results.append(file_info)
                        self.logger.debug(f"File modified since last scan: {file_info.file_path}")
                    else:
                        self.logger.debug(f"File unchanged: {file_info.file_path}")
                else:
                    # New file
                    validated_results.append(file_info)
                    self.logger.debug(f"New file detected: {file_info.file_path}")
                    
            except Exception as e:
                self.logger.warning(f"Validation error for {file_info.file_path}: {e}")
                validated_results.append(file_info)  # Include file if validation fails
                
        return validated_results
    
    def _get_or_create_directory_id(self, project_id: int, directory_path: str) -> Optional[int]:
        """
        Get or create directory record and return its ID.
        
        Args:
            project_id: Project ID
            directory_path: Directory path
            
        Returns:
            Directory ID or None if failed
        """
        try:
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if directory exists
                cursor.execute(
                    "SELECT id FROM directories WHERE project_id = ? AND folder_path = ?",
                    (project_id, directory_path)
                )
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Create new directory record
                folder_name = Path(directory_path).name
                cursor.execute(
                    """
                    INSERT INTO directories (project_id, folder_path, folder_name, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (project_id, directory_path, folder_name, datetime.now(timezone.utc).isoformat())
                )
                
                directory_id = cursor.lastrowid
                self.logger.debug(f"Created directory record: {directory_path} (ID: {directory_id})")
                return directory_id
                
        except Exception as e:
            self.logger.error(f"Failed to get/create directory ID for {directory_path}: {e}")
            return None
    
    def _detect_removed_files(self, project_id: int, current_scan_results: List[FileInfo]) -> int:
        """
        Detect files that have been removed from the file system.
        
        Args:
            project_id: Project ID
            current_scan_results: Current scan results
            
        Returns:
            Number of files marked as removed
        """
        try:
            # Get all active files from database for this project
            db_files = self.database.get_files_by_project(project_id)
            
            # Create set of current file paths
            current_paths = {file_info.file_path for file_info in current_scan_results}
            
            # Find files in database that are not in current scan
            removed_count = 0
            
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                
                for db_file in db_files:
                    file_path = db_file['file_path']
                    
                    if file_path not in current_paths and not os.path.exists(file_path):
                        # Mark file as inactive
                        cursor.execute(
                            "UPDATE files SET is_active = false, last_scanned = ? WHERE id = ?",
                            (datetime.now(timezone.utc).isoformat(), db_file['id'])
                        )
                        removed_count += 1
                        self.logger.debug(f"Marked file as removed: {file_path}")
            
            if removed_count > 0:
                self.logger.info(f"Detected {removed_count} removed files")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to detect removed files: {e}")
            return 0

    def _handle_config_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Handle configuration changes during runtime."""
        self.logger.info("Configuration change detected, applying updates...")
        
        try:
            # Update scanner settings if changed
            if old_config.get('scanning', {}) != new_config.get('scanning', {}):
                self.logger.info("Updating scanner configuration")
                # Note: In a full implementation, you might recreate scanners with new settings
            
            # Update database settings if changed
            if old_config.get('database', {}) != new_config.get('database', {}):
                self.logger.warning("Database configuration changed - restart required for full effect")
            
            # Update memory monitoring thresholds
            old_perf = old_config.get('performance', {})
            new_perf = new_config.get('performance', {})
            
            if old_perf.get('memory_warning_threshold') != new_perf.get('memory_warning_threshold'):
                self.memory_monitor.warning_threshold = new_perf.get('memory_warning_threshold', 80.0)
                
            if old_perf.get('memory_critical_threshold') != new_perf.get('memory_critical_threshold'):
                self.memory_monitor.critical_threshold = new_perf.get('memory_critical_threshold', 90.0)
            
        except Exception as e:
            self.logger.error(f"Error applying configuration changes: {e}")

    def shutdown(self) -> None:
        """Gracefully shutdown the scanner and clean up resources."""
        try:
            self.logger.info("Shutting down AEC Directory Scanner")
            
            # Stop memory monitoring
            if hasattr(self, 'memory_monitor'):
                self.memory_monitor.stop_monitoring()
            
            # Stop any ongoing file monitoring
            self.file_scanner.stop_monitoring()
            
            # Stop configuration monitoring
            if hasattr(self, 'config'):
                self.config.shutdown()
            
            # Clean up resources
            if hasattr(self, 'resource_manager'):
                self.resource_manager.cleanup_resources()
            
            # Close database connections
            self.database.close_connection()
            
            self.logger.info("Shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")