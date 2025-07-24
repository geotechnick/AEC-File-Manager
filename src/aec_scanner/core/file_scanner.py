"""
File System Scanner

Handles recursive scanning of directories, file system monitoring, and change detection
for the AEC Directory Scanner system.
"""

import os
import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class FileInfo:
    """Data class for storing file information."""
    file_path: str
    file_name: str
    file_extension: str
    file_size: int
    created_time: datetime
    modified_time: datetime
    accessed_time: datetime
    is_directory: bool
    parent_directory: str
    depth_level: int
    file_hash: Optional[str] = None


class FileSystemScanner:
    """
    Handles recursive directory scanning, file monitoring, and change detection
    with support for large directory structures and incremental scanning.
    """
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None,
        max_workers: int = 4,
        hash_files: bool = False,
        excluded_extensions: Optional[Set[str]] = None,
        excluded_directories: Optional[Set[str]] = None
    ):
        """
        Initialize the File System Scanner.
        
        Args:
            logger: Optional logger instance
            max_workers: Number of threads for parallel processing
            hash_files: Whether to generate file hashes (resource intensive)
            excluded_extensions: Set of file extensions to skip (e.g., {'.tmp', '.log'})
            excluded_directories: Set of directory names to skip (e.g., {'temp', '.git'})
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_workers = max_workers
        self.hash_files = hash_files
        self.excluded_extensions = excluded_extensions or {'.tmp', '.log', '.bak', '.swp'}
        self.excluded_directories = excluded_directories or {'temp', '.git', '__pycache__', 'node_modules'}
        
        # Progress tracking
        self._scan_progress = 0
        self._total_files = 0
        self._progress_callback: Optional[Callable] = None
        self._stop_scanning = False
        
        # File system monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_scan_cache: Dict[str, FileInfo] = {}
    
    def scan_directory(
        self, 
        root_path: str, 
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FileInfo]:
        """
        Recursively scan a directory and return detailed file information.
        
        Args:
            root_path: Root directory path to scan
            recursive: Whether to scan subdirectories recursively
            progress_callback: Optional callback function for progress updates (current, total)
            
        Returns:
            List of FileInfo objects containing detailed file information
        """
        root_path = Path(root_path)
        
        if not root_path.exists():
            self.logger.error(f"Root path does not exist: {root_path}")
            return []
        
        self.logger.info(f"Starting directory scan: {root_path}")
        self._progress_callback = progress_callback
        self._stop_scanning = False
        
        # First pass: count total files for progress tracking
        if progress_callback:
            self._total_files = self._count_files(root_path, recursive)
            self._scan_progress = 0
        
        files_info = []
        
        try:
            if recursive:
                files_info = self._scan_recursive(root_path, 0)
            else:
                files_info = self._scan_single_level(root_path, 0)
                
            self.logger.info(f"Scan completed. Found {len(files_info)} files")
            return files_info
            
        except Exception as e:
            self.logger.error(f"Error during directory scan: {e}")
            return files_info
    
    def _scan_recursive(self, directory: Path, depth: int) -> List[FileInfo]:
        """Recursively scan directory structure."""
        files_info = []
        
        try:
            # Use ThreadPoolExecutor for parallel processing of large directories
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for item in directory.iterdir():
                    if self._stop_scanning:
                        break
                        
                    if item.is_file():
                        future = executor.submit(self._process_file, item, depth)
                        futures.append(future)
                    elif item.is_dir() and not self._should_exclude_directory(item.name):
                        # Process subdirectory recursively
                        subdirectory_files = self._scan_recursive(item, depth + 1)
                        files_info.extend(subdirectory_files)
                
                # Collect results from file processing
                for future in as_completed(futures):
                    if self._stop_scanning:
                        break
                    try:
                        file_info = future.result()
                        if file_info:
                            files_info.append(file_info)
                            self._update_progress()
                    except Exception as e:
                        self.logger.warning(f"Error processing file: {e}")
                        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing directory: {directory}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return files_info
    
    def _scan_single_level(self, directory: Path, depth: int) -> List[FileInfo]:
        """Scan only the immediate directory level."""
        files_info = []
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for item in directory.iterdir():
                    if self._stop_scanning:
                        break
                        
                    if item.is_file():
                        future = executor.submit(self._process_file, item, depth)
                        futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    if self._stop_scanning:
                        break
                    try:
                        file_info = future.result()
                        if file_info:
                            files_info.append(file_info)
                            self._update_progress()
                    except Exception as e:
                        self.logger.warning(f"Error processing file: {e}")
                        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing directory: {directory}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return files_info
    
    def _process_file(self, file_path: Path, depth: int) -> Optional[FileInfo]:
        """Process a single file and extract its information."""
        try:
            # Check if file should be excluded
            if self._should_exclude_file(file_path):
                return None
            
            stat_info = file_path.stat()
            
            # Generate file hash if requested
            file_hash = None
            if self.hash_files:
                file_hash = self._calculate_file_hash(file_path)
            
            return FileInfo(
                file_path=str(file_path),
                file_name=file_path.name,
                file_extension=file_path.suffix.lower(),
                file_size=stat_info.st_size,
                created_time=datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc),
                modified_time=datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc),
                accessed_time=datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc),
                is_directory=False,
                parent_directory=str(file_path.parent),
                depth_level=depth,
                file_hash=file_hash
            )
            
        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot access file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded from scanning."""
        # Check file extension
        if file_path.suffix.lower() in self.excluded_extensions:
            return True
        
        # Check if file is hidden (starts with .)
        if file_path.name.startswith('.') and file_path.name != '.aec_project_metadata.json':
            return True
        
        return False
    
    def _should_exclude_directory(self, dir_name: str) -> bool:
        """Check if a directory should be excluded from scanning."""
        return dir_name.lower() in {d.lower() for d in self.excluded_directories}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Cannot calculate hash for {file_path}: {e}")
            return ""
    
    def _count_files(self, root_path: Path, recursive: bool) -> int:
        """Count total number of files for progress tracking."""
        count = 0
        try:
            if recursive:
                for item in root_path.rglob("*"):
                    if item.is_file() and not self._should_exclude_file(item):
                        count += 1
            else:
                for item in root_path.iterdir():
                    if item.is_file() and not self._should_exclude_file(item):
                        count += 1
        except Exception:
            pass  # If counting fails, progress tracking will be disabled
        return count
    
    def _update_progress(self):
        """Update scan progress and call callback if provided."""
        self._scan_progress += 1
        if self._progress_callback and self._total_files > 0:
            self._progress_callback(self._scan_progress, self._total_files)
    
    def get_file_tree(self, root_path: str) -> Dict:
        """
        Generate a hierarchical tree structure of the directory.
        
        Args:
            root_path: Root directory path
            
        Returns:
            Dictionary representing the directory tree structure
        """
        root_path = Path(root_path)
        
        if not root_path.exists():
            return {"error": "Path does not exist"}
        
        def build_tree(path: Path) -> Dict:
            tree = {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": 0,
                "modified": None
            }
            
            try:
                stat_info = path.stat()
                tree["size"] = stat_info.st_size
                tree["modified"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                if path.is_dir():
                    tree["children"] = []
                    try:
                        for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                            if not self._should_exclude_file(child) and not self._should_exclude_directory(child.name):
                                tree["children"].append(build_tree(child))
                    except PermissionError:
                        tree["error"] = "Permission denied"
                        
            except Exception as e:
                tree["error"] = str(e)
            
            return tree
        
        return build_tree(root_path)
    
    def incremental_scan(
        self, 
        root_path: str, 
        last_scan_time: datetime,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FileInfo]:
        """
        Perform incremental scan to find only files changed since last scan.
        
        Args:
            root_path: Root directory path to scan
            last_scan_time: Timestamp of the last scan
            progress_callback: Optional progress callback
            
        Returns:
            List of FileInfo objects for changed/new files
        """
        self.logger.info(f"Starting incremental scan since {last_scan_time}")
        
        all_files = self.scan_directory(root_path, recursive=True, progress_callback=progress_callback)
        
        # Filter files modified after last scan time
        changed_files = [
            file_info for file_info in all_files
            if file_info.modified_time > last_scan_time or file_info.created_time > last_scan_time
        ]
        
        self.logger.info(f"Incremental scan found {len(changed_files)} changed files")
        return changed_files
    
    def monitor_changes(
        self, 
        root_path: str, 
        callback: Callable[[List[FileInfo]], None],
        interval: int = 30
    ) -> None:
        """
        Monitor directory for file system changes in real-time.
        
        Args:
            root_path: Directory path to monitor
            callback: Function to call when changes are detected
            interval: Check interval in seconds
        """
        if self._monitoring:
            self.logger.warning("Already monitoring directory changes")
            return
        
        self._monitoring = True
        self.logger.info(f"Starting file system monitoring for {root_path}")
        
        def monitor_loop():
            last_scan = datetime.now(timezone.utc)
            
            while self._monitoring:
                try:
                    time.sleep(interval)
                    
                    if not self._monitoring:
                        break
                    
                    # Perform incremental scan
                    changes = self.incremental_scan(root_path, last_scan)
                    
                    if changes:
                        self.logger.info(f"Detected {len(changes)} file changes")
                        callback(changes)
                    
                    last_scan = datetime.now(timezone.utc)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop file system monitoring."""
        if self._monitoring:
            self._monitoring = False
            self.logger.info("Stopping file system monitoring")
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)
    
    def stop_scanning(self) -> None:
        """Stop the current scanning operation."""
        self._stop_scanning = True
        self.logger.info("Stopping directory scan")
    
    def generate_scan_report(self, scan_results: List[FileInfo]) -> Dict:
        """
        Generate a comprehensive report from scan results.
        
        Args:
            scan_results: List of FileInfo objects from a scan
            
        Returns:
            Dictionary containing scan statistics and analysis
        """
        if not scan_results:
            return {"error": "No scan results provided"}
        
        # Calculate statistics
        total_files = len(scan_results)
        total_size = sum(f.file_size for f in scan_results)
        
        # Group by extension
        extensions = {}
        for file_info in scan_results:
            ext = file_info.file_extension or "no_extension"
            if ext not in extensions:
                extensions[ext] = {"count": 0, "total_size": 0}
            extensions[ext]["count"] += 1
            extensions[ext]["total_size"] += file_info.file_size
        
        # Group by directory depth
        depth_distribution = {}
        for file_info in scan_results:
            depth = file_info.depth_level
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        # Find largest files
        largest_files = sorted(scan_results, key=lambda x: x.file_size, reverse=True)[:10]
        
        # Find newest files
        newest_files = sorted(scan_results, key=lambda x: x.modified_time, reverse=True)[:10]
        
        return {
            "scan_summary": {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "scan_timestamp": datetime.now(timezone.utc).isoformat()
            },
            "file_extensions": dict(sorted(extensions.items(), key=lambda x: x[1]["count"], reverse=True)),
            "depth_distribution": depth_distribution,
            "largest_files": [
                {
                    "path": f.file_path,
                    "size_bytes": f.file_size,
                    "size_mb": round(f.file_size / (1024 * 1024), 2)
                }
                for f in largest_files
            ],
            "newest_files": [
                {
                    "path": f.file_path,
                    "modified": f.modified_time.isoformat(),
                    "size_bytes": f.file_size
                }
                for f in newest_files
            ]
        }