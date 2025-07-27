"""
Memory Management Utilities

Provides memory monitoring, streaming operations, and resource management
for handling large file collections and memory-intensive operations.
"""

import os
import psutil
import gc
import logging
import threading
import time
from typing import Iterator, List, Any, Optional, Callable, Generator
from dataclasses import dataclass
from pathlib import Path
import warnings

from ..exceptions import ResourceLimitError


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_mb: float
    available_mb: float
    used_mb: float
    used_percent: float
    process_mb: float
    process_percent: float


class MemoryMonitor:
    """
    Monitor memory usage and provide warnings when limits are approached.
    """
    
    def __init__(
        self, 
        warning_threshold: float = 80.0,
        critical_threshold: float = 90.0,
        check_interval: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold: Memory usage percentage to trigger warning
            critical_threshold: Memory usage percentage to trigger critical alert
            check_interval: Check interval in seconds
            logger: Optional logger instance
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks = []
        self._last_warning_time = 0
        self._last_critical_time = 0
        
        # Get process for monitoring
        self.process = psutil.Process()
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        # System memory
        memory = psutil.virtual_memory()
        
        # Process memory
        process_memory = self.process.memory_info()
        
        return MemoryStats(
            total_mb=memory.total / (1024 * 1024),
            available_mb=memory.available / (1024 * 1024),
            used_mb=memory.used / (1024 * 1024),
            used_percent=memory.percent,
            process_mb=process_memory.rss / (1024 * 1024),
            process_percent=self.process.memory_percent()
        )
    
    def start_monitoring(self):
        """Start continuous memory monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                stats = self.get_memory_stats()
                current_time = time.time()
                
                # Check thresholds
                if stats.used_percent >= self.critical_threshold:
                    if current_time - self._last_critical_time > 60:  # Throttle alerts
                        self.logger.critical(
                            f"Critical memory usage: {stats.used_percent:.1f}% "
                            f"({stats.used_mb:.1f}MB used of {stats.total_mb:.1f}MB)"
                        )
                        self._notify_callbacks('critical', stats)
                        self._last_critical_time = current_time
                
                elif stats.used_percent >= self.warning_threshold:
                    if current_time - self._last_warning_time > 300:  # Throttle warnings
                        self.logger.warning(
                            f"High memory usage: {stats.used_percent:.1f}% "
                            f"({stats.used_mb:.1f}MB used of {stats.total_mb:.1f}MB)"
                        )
                        self._notify_callbacks('warning', stats)
                        self._last_warning_time = current_time
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in memory monitoring: {e}")
                time.sleep(self.check_interval)
    
    def add_callback(self, callback: Callable[[str, MemoryStats], None]):
        """Add callback for memory threshold events."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, event_type: str, stats: MemoryStats):
        """Notify registered callbacks of memory events."""
        for callback in self._callbacks:
            try:
                callback(event_type, stats)
            except Exception as e:
                self.logger.error(f"Error in memory callback: {e}")
    
    def check_memory_limit(self, required_mb: float, operation_name: str = "operation"):
        """
        Check if there's sufficient memory for an operation.
        
        Args:
            required_mb: Required memory in MB
            operation_name: Name of operation for error messages
            
        Raises:
            ResourceLimitError: If insufficient memory available
        """
        stats = self.get_memory_stats()
        
        if stats.available_mb < required_mb:
            raise ResourceLimitError(
                f"Insufficient memory for {operation_name}. "
                f"Required: {required_mb:.1f}MB, Available: {stats.available_mb:.1f}MB",
                resource_type="memory",
                limit=int(stats.available_mb),
                current=int(required_mb)
            )
    
    def force_garbage_collection(self):
        """Force garbage collection and log memory savings."""
        stats_before = self.get_memory_stats()
        
        # Force garbage collection
        gc.collect()
        
        stats_after = self.get_memory_stats()
        freed_mb = stats_before.process_mb - stats_after.process_mb
        
        if freed_mb > 1.0:  # Only log if significant memory was freed
            self.logger.info(f"Garbage collection freed {freed_mb:.1f}MB of memory")
        
        return freed_mb


class StreamingProcessor:
    """
    Process large datasets in streaming fashion to manage memory usage.
    """
    
    def __init__(
        self, 
        batch_size: int = 1000,
        memory_limit_mb: float = 500,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize streaming processor.
        
        Args:
            batch_size: Number of items to process in each batch
            memory_limit_mb: Memory limit for processing
            logger: Optional logger instance
        """
        self.batch_size = batch_size
        self.memory_limit_mb = memory_limit_mb
        self.logger = logger or logging.getLogger(__name__)
        self.memory_monitor = MemoryMonitor()
    
    def process_in_batches(
        self, 
        items: Iterator[Any], 
        processor_func: Callable[[List[Any]], Any],
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Generator[Any, None, None]:
        """
        Process items in memory-efficient batches.
        
        Args:
            items: Iterator of items to process
            processor_func: Function to process each batch
            progress_callback: Optional progress callback
            
        Yields:
            Results from processing each batch
        """
        batch = []
        processed_count = 0
        
        try:
            for item in items:
                batch.append(item)
                
                if len(batch) >= self.batch_size:
                    # Check memory before processing
                    self.memory_monitor.check_memory_limit(
                        self.memory_limit_mb, 
                        f"batch processing ({len(batch)} items)"
                    )
                    
                    # Process batch
                    result = processor_func(batch)
                    yield result
                    
                    # Update progress
                    processed_count += len(batch)
                    if progress_callback:
                        progress_callback(processed_count)
                    
                    # Clear batch and force garbage collection
                    batch.clear()
                    if processed_count % (self.batch_size * 10) == 0:
                        self.memory_monitor.force_garbage_collection()
            
            # Process remaining items
            if batch:
                result = processor_func(batch)
                yield result
                
                processed_count += len(batch)
                if progress_callback:
                    progress_callback(processed_count)
        
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            raise
    
    def stream_file_lines(
        self, 
        file_path: Path, 
        chunk_size: int = 8192,
        encoding: str = 'utf-8'
    ) -> Generator[str, None, None]:
        """
        Stream file lines without loading entire file into memory.
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read
            encoding: File encoding
            
        Yields:
            Individual lines from the file
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                buffer = ""
                
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    lines = buffer.split('\n')
                    
                    # Yield complete lines, keep incomplete line in buffer
                    for line in lines[:-1]:
                        yield line
                    
                    buffer = lines[-1]
                
                # Yield remaining buffer as final line
                if buffer:
                    yield buffer
                    
        except Exception as e:
            self.logger.error(f"Error streaming file {file_path}: {e}")
            raise
    
    def estimate_memory_usage(self, item_count: int, avg_item_size_bytes: int) -> float:
        """
        Estimate memory usage for processing items.
        
        Args:
            item_count: Number of items to process
            avg_item_size_bytes: Average size of each item in bytes
            
        Returns:
            Estimated memory usage in MB
        """
        # Base Python object overhead + data size + processing overhead
        overhead_factor = 2.5  # Empirical factor for Python object overhead
        
        total_bytes = item_count * avg_item_size_bytes * overhead_factor
        return total_bytes / (1024 * 1024)


class ResourceManager:
    """
    Manage system resources including memory, disk space, and file handles.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize resource manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.memory_monitor = MemoryMonitor()
        self._file_handles = set()
        self._max_file_handles = 1000
    
    def check_disk_space(self, path: str, required_mb: float):
        """
        Check available disk space.
        
        Args:
            path: Path to check
            required_mb: Required space in MB
            
        Raises:
            ResourceLimitError: If insufficient disk space
        """
        try:
            stat = os.statvfs(path) if hasattr(os, 'statvfs') else None
            
            if stat:
                available_bytes = stat.f_bavail * stat.f_frsize
                available_mb = available_bytes / (1024 * 1024)
            else:
                # Fallback for Windows
                import shutil
                total, used, free = shutil.disk_usage(path)
                available_mb = free / (1024 * 1024)
            
            if available_mb < required_mb:
                raise ResourceLimitError(
                    f"Insufficient disk space at {path}. "
                    f"Required: {required_mb:.1f}MB, Available: {available_mb:.1f}MB",
                    resource_type="disk_space",
                    limit=int(available_mb),
                    current=int(required_mb)
                )
                
        except ResourceLimitError:
            raise
        except Exception as e:
            self.logger.warning(f"Unable to check disk space: {e}")
    
    def monitor_file_handles(self, file_handle):
        """Track open file handles."""
        self._file_handles.add(file_handle)
        
        if len(self._file_handles) > self._max_file_handles:
            self.logger.warning(f"High number of open file handles: {len(self._file_handles)}")
    
    def close_file_handle(self, file_handle):
        """Remove file handle from tracking."""
        self._file_handles.discard(file_handle)
    
    def get_system_info(self) -> dict:
        """Get comprehensive system resource information."""
        memory_stats = self.memory_monitor.get_memory_stats()
        
        # CPU information
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage for current directory
        disk_usage = psutil.disk_usage('.')
        
        return {
            'memory': {
                'total_mb': memory_stats.total_mb,
                'available_mb': memory_stats.available_mb,
                'used_percent': memory_stats.used_percent,
                'process_mb': memory_stats.process_mb
            },
            'cpu': {
                'count': cpu_count,
                'usage_percent': cpu_percent
            },
            'disk': {
                'total_mb': disk_usage.total / (1024 * 1024),
                'free_mb': disk_usage.free / (1024 * 1024),
                'used_percent': (disk_usage.used / disk_usage.total) * 100
            },
            'file_handles': {
                'open_count': len(self._file_handles),
                'max_limit': self._max_file_handles
            }
        }
    
    def cleanup_resources(self):
        """Clean up tracked resources."""
        # Close any remaining file handles
        for handle in list(self._file_handles):
            try:
                handle.close()
            except Exception as e:
                self.logger.warning(f"Error closing file handle: {e}")
        
        self._file_handles.clear()
        
        # Force garbage collection
        self.memory_monitor.force_garbage_collection()
        
        self.logger.info("Resource cleanup completed")


# Global resource manager instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager