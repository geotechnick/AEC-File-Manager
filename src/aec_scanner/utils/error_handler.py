"""
Error Handler

Comprehensive error handling and logging system for the AEC Directory Scanner
with performance monitoring and user-friendly error messages.
"""

import logging
import traceback
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    FILE_ACCESS = "file_access"
    DATABASE = "database"
    METADATA_EXTRACTION = "metadata_extraction"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    SYSTEM = "system"


@dataclass
class ErrorRecord:
    """Data class for storing error information."""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    suggested_solutions: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetric:
    """Data class for storing performance metrics."""
    operation: str
    duration: float
    files_processed: int
    timestamp: datetime
    memory_usage_mb: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


class ErrorHandler:
    """
    Comprehensive error handling system with logging, performance monitoring,
    and user-friendly error messages with suggested solutions.
    """
    
    def __init__(self, logger: logging.Logger, max_error_history: int = 1000):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger instance to use for error reporting
            max_error_history: Maximum number of errors to keep in memory
        """
        self.logger = logger
        self.max_error_history = max_error_history
        
        # Error tracking
        self.error_history: List[ErrorRecord] = []
        self.error_count_by_category: Dict[ErrorCategory, int] = {}
        self.error_count_by_severity: Dict[ErrorSeverity, int] = {}
        
        # Performance tracking
        self.performance_metrics: List[PerformanceMetric] = []
        self.operation_start_times: Dict[str, float] = {}
        
        # Error patterns and solutions
        self.error_solutions = self._initialize_error_solutions()
        
        self.logger.info("Error handler initialized")
    
    def _initialize_error_solutions(self) -> Dict[str, List[str]]:
        """Initialize common error patterns and their suggested solutions."""
        return {
            "Permission denied": [
                "Check if the file or directory has proper read/write permissions",
                "Run the application with elevated privileges if necessary",
                "Ensure the file is not locked by another application"
            ],
            "File not found": [
                "Verify the file path is correct and the file exists",
                "Check if the file has been moved or deleted",
                "Ensure the drive or network location is accessible"
            ],
            "Database connection": [
                "Verify database server is running and accessible",
                "Check database connection parameters in configuration",
                "Ensure network connectivity to database server",
                "Verify database credentials are correct"
            ],
            "Out of memory": [
                "Reduce the number of parallel workers in configuration",
                "Process files in smaller batches",
                "Increase system memory or virtual memory",
                "Close other memory-intensive applications"
            ],
            "Disk full": [
                "Free up disk space on the target drive",
                "Move files to a different location with more space",
                "Clean up temporary files and logs",
                "Check if disk quotas are restricting space"
            ],
            "Metadata extraction": [
                "Verify the file is not corrupted",
                "Check if the file format is supported",
                "Update metadata extraction libraries",
                "Try processing the file with a different tool first"
            ],
            "Network timeout": [
                "Check network connectivity",
                "Increase timeout values in configuration",
                "Verify firewall settings allow the connection",
                "Try the operation again later"
            ]
        }
    
    def handle_file_error(
        self, 
        error: Exception, 
        file_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle file-related errors with appropriate logging and recovery suggestions.
        
        Args:
            error: The exception that occurred
            file_path: Path to the file that caused the error
            context: Optional additional context information
            
        Returns:
            True if error was handled gracefully, False if critical
        """
        error_id = self._generate_error_id()
        
        # Determine error severity and category
        severity = self._determine_severity(error, ErrorCategory.FILE_ACCESS)
        
        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            category=ErrorCategory.FILE_ACCESS,
            severity=severity,
            message=str(error),
            details=f"Error processing file: {file_path}",
            file_path=file_path,
            function_name=self._get_calling_function(),
            stack_trace=traceback.format_exc(),
            context=context or {},
            suggested_solutions=self._get_suggested_solutions(str(error))
        )
        
        # Log the error
        self._log_error(error_record)
        
        # Store error record
        self._store_error_record(error_record)
        
        # Return whether the error is recoverable
        return severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
    
    def handle_database_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle database-related errors.
        
        Args:
            error: The exception that occurred
            operation: Database operation that failed
            context: Optional additional context information
            
        Returns:
            True if error was handled gracefully, False if critical
        """
        error_id = self._generate_error_id()
        severity = self._determine_severity(error, ErrorCategory.DATABASE)
        
        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            category=ErrorCategory.DATABASE,
            severity=severity,
            message=str(error),
            details=f"Database operation failed: {operation}",
            function_name=self._get_calling_function(),
            stack_trace=traceback.format_exc(),
            context=context or {},
            suggested_solutions=self._get_suggested_solutions(str(error))
        )
        
        self._log_error(error_record)
        self._store_error_record(error_record)
        
        return severity != ErrorSeverity.CRITICAL
    
    def handle_metadata_error(
        self,
        error: Exception,
        file_path: str,
        extractor_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle metadata extraction errors.
        
        Args:
            error: The exception that occurred
            file_path: Path to the file that caused the error
            extractor_name: Name of the metadata extractor
            context: Optional additional context information
            
        Returns:
            True if error was handled gracefully, False if critical
        """
        error_id = self._generate_error_id()
        severity = self._determine_severity(error, ErrorCategory.METADATA_EXTRACTION)
        
        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            category=ErrorCategory.METADATA_EXTRACTION,
            severity=severity,
            message=str(error),
            details=f"Metadata extraction failed using {extractor_name}",
            file_path=file_path,
            function_name=self._get_calling_function(),
            stack_trace=traceback.format_exc(),
            context=context or {"extractor": extractor_name},
            suggested_solutions=self._get_suggested_solutions("Metadata extraction")
        )
        
        self._log_error(error_record)
        self._store_error_record(error_record)
        
        return True  # Metadata extraction errors are usually recoverable
    
    def log_performance_metrics(
        self,
        operation: str,
        duration: float,
        files_processed: int,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log performance metrics for monitoring and optimization.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            files_processed: Number of files processed
            context: Optional additional context
        """
        try:
            import psutil
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            memory_usage = None
        
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            files_processed=files_processed,
            timestamp=datetime.now(timezone.utc),
            memory_usage_mb=memory_usage,
            context=context or {}
        )
        
        self.performance_metrics.append(metric)
        
        # Log performance information
        files_per_second = files_processed / duration if duration > 0 else 0
        self.logger.info(
            f"Performance: {operation} - {files_processed} files in {duration:.2f}s "
            f"({files_per_second:.1f} files/sec)"
        )
        
        # Check for performance issues
        if files_per_second < 10 and files_processed > 100:
            self.logger.warning(
                f"Slow performance detected: {operation} processing only "
                f"{files_per_second:.1f} files/second"
            )
        
        # Limit metrics history
        if len(self.performance_metrics) > 500:
            self.performance_metrics = self.performance_metrics[-400:]
    
    def start_operation_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.operation_start_times[operation] = time.time()
    
    def end_operation_timer(
        self,
        operation: str,
        files_processed: int,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        End timing an operation and log metrics.
        
        Args:
            operation: Name of the operation
            files_processed: Number of files processed
            context: Optional additional context
            
        Returns:
            Duration in seconds
        """
        if operation not in self.operation_start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        duration = time.time() - self.operation_start_times[operation]
        del self.operation_start_times[operation]
        
        self.log_performance_metrics(operation, duration, files_processed, context)
        return duration
    
    def generate_error_report(self, scan_session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive error report.
        
        Args:
            scan_session_id: Optional scan session ID to filter errors
            
        Returns:
            Dictionary containing error report data
        """
        # Filter errors by scan session if provided
        if scan_session_id:
            errors = [
                e for e in self.error_history 
                if e.context.get('scan_session_id') == scan_session_id
            ]
        else:
            errors = self.error_history.copy()
        
        # Calculate statistics
        total_errors = len(errors)
        errors_by_category = {}
        errors_by_severity = {}
        errors_by_hour = {}
        
        for error in errors:
            # Count by category
            category = error.category.value
            errors_by_category[category] = errors_by_category.get(category, 0) + 1
            
            # Count by severity
            severity = error.severity.value
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1
            
            # Count by hour
            hour_key = error.timestamp.strftime('%Y-%m-%d %H:00')
            errors_by_hour[hour_key] = errors_by_hour.get(hour_key, 0) + 1
        
        # Find most common errors
        error_messages = {}
        for error in errors:
            msg = error.message[:100]  # Truncate long messages
            error_messages[msg] = error_messages.get(msg, 0) + 1
        
        most_common_errors = sorted(
            error_messages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Recent critical errors
        critical_errors = [
            {
                "error_id": e.error_id,
                "timestamp": e.timestamp.isoformat(),
                "message": e.message,
                "file_path": e.file_path,
                "suggested_solutions": e.suggested_solutions
            }
            for e in errors
            if e.severity == ErrorSeverity.CRITICAL
        ][-10:]  # Last 10 critical errors
        
        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "scan_session_id": scan_session_id,
            "summary": {
                "total_errors": total_errors,
                "critical_errors": len([e for e in errors if e.severity == ErrorSeverity.CRITICAL]),
                "high_severity_errors": len([e for e in errors if e.severity == ErrorSeverity.HIGH]),
                "error_rate_per_hour": len(errors_by_hour) / max(len(errors_by_hour), 1)
            },
            "errors_by_category": errors_by_category,
            "errors_by_severity": errors_by_severity,
            "errors_by_hour": errors_by_hour,
            "most_common_errors": most_common_errors,
            "recent_critical_errors": critical_errors,
            "recommendations": self._generate_recommendations(errors)
        }
    
    def suggest_solutions(self, error_type: str) -> List[str]:
        """
        Get suggested solutions for a specific error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            List of suggested solutions
        """
        return self._get_suggested_solutions(error_type)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary statistics.
        
        Returns:
            Dictionary containing performance summary
        """
        if not self.performance_metrics:
            return {"message": "No performance data available"}
        
        # Calculate averages by operation
        operation_stats = {}
        for metric in self.performance_metrics:
            if metric.operation not in operation_stats:
                operation_stats[metric.operation] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_files": 0,
                    "durations": [],
                    "files_per_second": []
                }
            
            stats = operation_stats[metric.operation]
            stats["count"] += 1
            stats["total_duration"] += metric.duration
            stats["total_files"] += metric.files_processed
            stats["durations"].append(metric.duration)
            
            if metric.duration > 0:
                fps = metric.files_processed / metric.duration
                stats["files_per_second"].append(fps)
        
        # Calculate summary statistics
        summary = {}
        for operation, stats in operation_stats.items():
            avg_duration = stats["total_duration"] / stats["count"]
            avg_files_per_second = sum(stats["files_per_second"]) / len(stats["files_per_second"]) if stats["files_per_second"] else 0
            
            summary[operation] = {
                "executions": stats["count"],
                "total_files_processed": stats["total_files"],
                "average_duration": round(avg_duration, 2),
                "average_files_per_second": round(avg_files_per_second, 2),
                "total_duration": round(stats["total_duration"], 2)
            }
        
        return {
            "summary_generated_at": datetime.now(timezone.utc).isoformat(),
            "total_operations": len(self.performance_metrics),
            "operation_statistics": summary
        }
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()
        self.error_count_by_category.clear()
        self.error_count_by_severity.clear()
        self.logger.info("Error history cleared")
    
    def clear_performance_metrics(self) -> None:
        """Clear the performance metrics."""
        self.performance_metrics.clear()
        self.logger.info("Performance metrics cleared")
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID."""
        from uuid import uuid4
        return str(uuid4())[:8]
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine the severity of an error based on its type and category."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if any(keyword in error_str for keyword in ['database', 'connection', 'timeout']):
            if category == ErrorCategory.DATABASE:
                return ErrorSeverity.CRITICAL
        
        if 'out of memory' in error_str or 'memory' in error_str:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_str for keyword in ['permission denied', 'access denied', 'disk full']):
            return ErrorSeverity.HIGH
        
        if error_type in ['connectionerror', 'timeouterror']:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_str for keyword in ['file not found', 'no such file']):
            return ErrorSeverity.MEDIUM
        
        if category == ErrorCategory.METADATA_EXTRACTION:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _get_calling_function(self) -> Optional[str]:
        """Get the name of the calling function."""
        try:
            import inspect
            frame = inspect.currentframe()
            # Go up the stack to find the calling function
            for _ in range(3):  # Skip error handler frames
                frame = frame.f_back
                if frame is None:
                    return None
            return frame.f_code.co_name
        except Exception:
            return None
    
    def _get_suggested_solutions(self, error_message: str) -> List[str]:
        """Get suggested solutions based on error message."""
        error_lower = error_message.lower()
        
        for pattern, solutions in self.error_solutions.items():
            if pattern.lower() in error_lower:
                return solutions
        
        # Generic suggestions
        return [
            "Check the application logs for more detailed error information",
            "Verify that all required files and directories are accessible",
            "Ensure the system has sufficient resources (memory, disk space)",
            "Try running the operation again with different parameters"
        ]
    
    def _log_error(self, error_record: ErrorRecord) -> None:
        """Log an error record using the appropriate log level."""
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"[{error_record.error_id}] {error_record.message} - {error_record.details}"
            )
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"[{error_record.error_id}] {error_record.message} - {error_record.details}"
            )
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"[{error_record.error_id}] {error_record.message} - {error_record.details}"
            )
        else:
            self.logger.info(
                f"[{error_record.error_id}] {error_record.message} - {error_record.details}"
            )
    
    def _store_error_record(self, error_record: ErrorRecord) -> None:
        """Store an error record in the history."""
        self.error_history.append(error_record)
        
        # Update counters
        category = error_record.category
        severity = error_record.severity
        
        self.error_count_by_category[category] = self.error_count_by_category.get(category, 0) + 1
        self.error_count_by_severity[severity] = self.error_count_by_severity.get(severity, 0) + 1
        
        # Limit history size
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history//2:]
    
    def _generate_recommendations(self, errors: List[ErrorRecord]) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []
        
        # Check for common patterns
        file_errors = len([e for e in errors if e.category == ErrorCategory.FILE_ACCESS])
        db_errors = len([e for e in errors if e.category == ErrorCategory.DATABASE])
        critical_errors = len([e for e in errors if e.severity == ErrorSeverity.CRITICAL])
        
        if file_errors > 10:
            recommendations.append(
                "High number of file access errors detected. "
                "Check file permissions and ensure all paths are accessible."
            )
        
        if db_errors > 5:
            recommendations.append(
                "Multiple database errors detected. "
                "Verify database connection and consider checking database logs."
            )
        
        if critical_errors > 0:
            recommendations.append(
                "Critical errors detected. "
                "Review system resources and configuration settings."
            )
        
        # Performance recommendations
        recent_metrics = self.performance_metrics[-50:] if len(self.performance_metrics) > 50 else self.performance_metrics
        if recent_metrics:
            avg_speed = sum(
                m.files_processed / m.duration for m in recent_metrics if m.duration > 0
            ) / len(recent_metrics)
            
            if avg_speed < 5:
                recommendations.append(
                    "Low processing speed detected. "
                    "Consider reducing parallel workers or increasing system resources."
                )
        
        return recommendations if recommendations else ["No specific recommendations at this time."]