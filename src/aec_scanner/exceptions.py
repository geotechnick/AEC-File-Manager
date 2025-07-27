"""
Custom exceptions for the AEC Directory Scanner system.

Provides specific exception types for better error handling and debugging.
"""


class AECScannerException(Exception):
    """Base exception for AEC Scanner errors."""
    pass


class DatabaseError(AECScannerException):
    """Database operation errors."""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(message)
        self.operation = operation
        self.table = table


class ConnectionPoolExhausted(DatabaseError):
    """Raised when database connection pool is exhausted."""
    pass


class FileSystemError(AECScannerException):
    """File system operation errors."""
    
    def __init__(self, message: str, file_path: str = None):
        super().__init__(message)
        self.file_path = file_path


class PermissionError(FileSystemError):
    """File/directory permission errors."""
    pass


class FileNotFoundError(FileSystemError):
    """File or directory not found errors."""
    pass


class ScanningError(AECScannerException):
    """Errors during directory scanning operations."""
    
    def __init__(self, message: str, scan_type: str = None, project_id: int = None):
        super().__init__(message)
        self.scan_type = scan_type
        self.project_id = project_id


class MetadataExtractionError(AECScannerException):
    """Errors during metadata extraction."""
    
    def __init__(self, message: str, file_path: str = None, extractor_type: str = None):
        super().__init__(message)
        self.file_path = file_path
        self.extractor_type = extractor_type


class ConfigurationError(AECScannerException):
    """Configuration related errors."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.config_key = config_key


class ValidationError(AECScannerException):
    """Data validation errors."""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        super().__init__(message)
        self.field = field
        self.value = value


class ProjectNotFoundError(AECScannerException):
    """Project not found in database."""
    
    def __init__(self, project_id: int = None, project_number: str = None):
        if project_id:
            message = f"Project with ID {project_id} not found"
        elif project_number:
            message = f"Project with number {project_number} not found"
        else:
            message = "Project not found"
        
        super().__init__(message)
        self.project_id = project_id
        self.project_number = project_number


class DirectoryStructureError(AECScannerException):
    """Directory structure validation errors."""
    
    def __init__(self, message: str, directory_path: str = None):
        super().__init__(message)
        self.directory_path = directory_path


class CacheError(AECScannerException):
    """Cache operation errors."""
    pass


class ThreadPoolError(AECScannerException):
    """Thread pool operation errors."""
    pass


class ResourceLimitError(AECScannerException):
    """Resource limit exceeded errors."""
    
    def __init__(self, message: str, resource_type: str = None, limit: int = None, current: int = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.limit = limit
        self.current = current


class RetryableError(AECScannerException):
    """Errors that can be retried."""
    
    def __init__(self, message: str, retry_count: int = 0, max_retries: int = 3):
        super().__init__(message)
        self.retry_count = retry_count
        self.max_retries = max_retries
    
    def can_retry(self) -> bool:
        """Check if operation can be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1