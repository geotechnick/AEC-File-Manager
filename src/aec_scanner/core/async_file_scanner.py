"""
Async File System Scanner

Async implementation of file system scanning with improved performance
for I/O bound operations using asyncio.
"""

import asyncio
import aiofiles
import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable, Union, Set, AsyncGenerator
from dataclasses import dataclass
import os
import stat

from .file_scanner import FileInfo


class AsyncFileSystemScanner:
    """
    Async file system scanner optimized for I/O bound operations.
    Provides significant performance improvements for large directory structures.
    """
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None,
        max_concurrent: int = 100,
        hash_files: bool = False,
        excluded_extensions: Optional[Set[str]] = None,
        excluded_directories: Optional[Set[str]] = None
    ):
        """
        Initialize the Async File System Scanner.
        
        Args:
            logger: Optional logger instance
            max_concurrent: Maximum concurrent file operations
            hash_files: Whether to generate file hashes (resource intensive)
            excluded_extensions: Set of file extensions to skip
            excluded_directories: Set of directory names to skip
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_concurrent = max_concurrent
        self.hash_files = hash_files
        self.excluded_extensions = excluded_extensions or {'.tmp', '.log', '.bak', '.swp'}
        self.excluded_directories = excluded_directories or {'temp', '.git', '__pycache__', 'node_modules'}
        
        # Semaphore to limit concurrent operations
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Progress tracking
        self._scan_progress = 0
        self._total_files = 0
        self._progress_callback: Optional[Callable] = None
        self._stop_scanning = False
    
    async def scan_directory_async(
        self, 
        root_path: str, 
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FileInfo]:
        """
        Async recursive directory scan with concurrent file processing.
        
        Args:
            root_path: Root directory path to scan
            recursive: Whether to scan subdirectories recursively
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of FileInfo objects containing detailed file information
        """
        root_path = Path(root_path)
        
        if not root_path.exists():
            self.logger.error(f"Root path does not exist: {root_path}")
            return []
        
        self.logger.info(f"Starting async directory scan: {root_path}")
        self._progress_callback = progress_callback
        self._stop_scanning = False
        
        # First pass: count total files for progress tracking
        if progress_callback:
            self._total_files = await self._count_files_async(root_path, recursive)
            self._scan_progress = 0
        
        files_info = []
        
        try:
            if recursive:
                async for file_info in self._scan_recursive_async(root_path, 0):
                    if self._stop_scanning:
                        break
                    if file_info:
                        files_info.append(file_info)
                        self._update_progress()
            else:
                async for file_info in self._scan_single_level_async(root_path, 0):
                    if self._stop_scanning:
                        break
                    if file_info:
                        files_info.append(file_info)
                        self._update_progress()
                
            self.logger.info(f"Async scan completed. Found {len(files_info)} files")
            return files_info
            
        except Exception as e:
            self.logger.error(f"Error during async directory scan: {e}")
            return files_info
    
    async def _scan_recursive_async(self, directory: Path, depth: int) -> AsyncGenerator[Optional[FileInfo], None]:
        """Async recursive directory scanning with concurrent processing."""
        try:
            # Get directory entries
            entries = []
            try:
                # Use asyncio.to_thread for blocking I/O operations
                entries = await asyncio.to_thread(list, directory.iterdir())
            except PermissionError:
                self.logger.warning(f"Permission denied accessing directory: {directory}")
                return
            
            # Separate files and directories
            files = [entry for entry in entries if entry.is_file()]
            directories = [entry for entry in entries if entry.is_dir() and not self._should_exclude_directory(entry.name)]
            
            # Process files concurrently
            file_tasks = [self._process_file_async(file_path, depth) for file_path in files]
            
            # Process files in batches to avoid overwhelming the system
            batch_size = min(self.max_concurrent, len(file_tasks))
            for i in range(0, len(file_tasks), batch_size):
                if self._stop_scanning:
                    break
                    
                batch = file_tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error processing file: {result}")
                    elif result is not None:
                        yield result
            
            # Process subdirectories recursively
            for subdir in directories:
                if self._stop_scanning:
                    break
                async for file_info in self._scan_recursive_async(subdir, depth + 1):
                    yield file_info
                    
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
    
    async def _scan_single_level_async(self, directory: Path, depth: int) -> AsyncGenerator[Optional[FileInfo], None]:
        """Async single-level directory scanning."""
        try:
            entries = await asyncio.to_thread(list, directory.iterdir())
            files = [entry for entry in entries if entry.is_file()]
            
            # Process files concurrently
            file_tasks = [self._process_file_async(file_path, depth) for file_path in files]
            
            batch_size = min(self.max_concurrent, len(file_tasks))
            for i in range(0, len(file_tasks), batch_size):
                if self._stop_scanning:
                    break
                    
                batch = file_tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error processing file: {result}")
                    elif result is not None:
                        yield result
                        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing directory: {directory}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
    
    async def _process_file_async(self, file_path: Path, depth: int) -> Optional[FileInfo]:
        """Async file processing with semaphore-controlled concurrency."""
        async with self._semaphore:
            try:
                # Check if file should be excluded
                if self._should_exclude_file(file_path):
                    return None
                
                # Get file stats using thread pool for blocking I/O
                stat_info = await asyncio.to_thread(file_path.stat)
                
                # Generate file hash if requested
                file_hash = None
                if self.hash_files:
                    file_hash = await self._calculate_file_hash_async(file_path)
                
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
    
    async def _calculate_file_hash_async(self, file_path: Path) -> str:
        """Async file hash calculation."""
        try:
            hash_sha256 = hashlib.sha256()
            
            async with aiofiles.open(file_path, "rb") as f:
                while chunk := await f.read(4096):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Cannot calculate hash for {file_path}: {e}")
            return ""
    
    async def _count_files_async(self, root_path: Path, recursive: bool) -> int:
        """Async file counting for progress tracking."""
        count = 0
        try:
            if recursive:
                async for entry in self._walk_directory_async(root_path):
                    if entry.is_file() and not self._should_exclude_file(entry):
                        count += 1
            else:
                entries = await asyncio.to_thread(list, root_path.iterdir())
                for entry in entries:
                    if entry.is_file() and not self._should_exclude_file(entry):
                        count += 1
        except Exception:
            pass  # If counting fails, progress tracking will be disabled
        return count
    
    async def _walk_directory_async(self, root_path: Path) -> AsyncGenerator[Path, None]:
        """Async directory walking generator."""
        try:
            entries = await asyncio.to_thread(list, root_path.iterdir())
            
            for entry in entries:
                if entry.is_file():
                    yield entry
                elif entry.is_dir() and not self._should_exclude_directory(entry.name):
                    async for sub_entry in self._walk_directory_async(entry):
                        yield sub_entry
                        
        except PermissionError:
            pass  # Skip directories we can't access
        except Exception as e:
            self.logger.warning(f"Error walking directory {root_path}: {e}")
    
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
    
    def _update_progress(self):
        """Update scan progress and call callback if provided."""
        self._scan_progress += 1
        if self._progress_callback and self._total_files > 0:
            self._progress_callback(self._scan_progress, self._total_files)
    
    async def incremental_scan_async(
        self, 
        root_path: str, 
        last_scan_time: datetime,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FileInfo]:
        """
        Async incremental scan to find only files changed since last scan.
        
        Args:
            root_path: Root directory path to scan
            last_scan_time: Timestamp of the last scan
            progress_callback: Optional progress callback
            
        Returns:
            List of FileInfo objects for changed/new files
        """
        self.logger.info(f"Starting async incremental scan since {last_scan_time}")
        
        all_files = await self.scan_directory_async(root_path, recursive=True, progress_callback=progress_callback)
        
        # Filter files modified after last scan time
        changed_files = [
            file_info for file_info in all_files
            if file_info.modified_time > last_scan_time or file_info.created_time > last_scan_time
        ]
        
        self.logger.info(f"Async incremental scan found {len(changed_files)} changed files")
        return changed_files
    
    def stop_scanning(self) -> None:
        """Stop the current scanning operation."""
        self._stop_scanning = True
        self.logger.info("Stopping async directory scan")
    
    async def batch_process_files(
        self,
        file_paths: List[str],
        processor_func: Callable,
        batch_size: int = 100
    ) -> List[any]:
        """
        Process files in batches with controlled concurrency.
        
        Args:
            file_paths: List of file paths to process
            processor_func: Function to process each file
            batch_size: Size of each processing batch
            
        Returns:
            List of processing results
        """
        results = []
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            batch_tasks = [processor_func(file_path) for file_path in batch]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results