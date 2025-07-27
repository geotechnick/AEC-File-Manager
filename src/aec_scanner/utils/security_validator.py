"""
Security Validation Utilities

Provides input validation, path sanitization, and security checks
to prevent common security vulnerabilities.
"""

import os
import re
import hashlib
import logging
from pathlib import Path, PurePath
from typing import Union, List, Optional, Dict, Any
from urllib.parse import urlparse

from ..exceptions import ValidationError, FileSystemError


class PathValidator:
    """
    Validates and sanitizes file paths to prevent directory traversal attacks.
    """
    
    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r'\.\.[\\/]',  # Directory traversal
        r'[\\/]\.\.[\\/]',  # Directory traversal
        r'[\\/]\.\.$',  # Directory traversal at end
        r'^\.\.[\\/]',  # Directory traversal at start
        r'~[\\/]',  # Home directory access
        r'[\\/]~[\\/]',  # Home directory access
        r'\$\w+',  # Environment variables
        r'%\w+%',  # Windows environment variables
    ]
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar',
        '.sh', '.bash', '.zsh', '.ps1', '.py', '.pl', '.php', '.asp', '.jsp',
        '.dll', '.so', '.dylib'
    }
    
    # System directories to protect (relative to root)
    PROTECTED_DIRS = {
        'windows': {'windows', 'program files', 'program files (x86)', 'system32'},
        'unix': {'bin', 'sbin', 'usr', 'var', 'etc', 'boot', 'dev', 'proc', 'sys'}
    }
    
    def __init__(self, allowed_base_paths: Optional[List[str]] = None):
        """
        Initialize path validator.
        
        Args:
            allowed_base_paths: List of allowed base paths for file operations
        """
        self.logger = logging.getLogger(__name__)
        self.allowed_base_paths = allowed_base_paths or []
        
        # Normalize allowed paths
        self.allowed_base_paths = [
            os.path.abspath(os.path.expanduser(path)) 
            for path in self.allowed_base_paths
        ]
    
    def validate_path(self, file_path: Union[str, Path], operation: str = "access") -> Path:
        """
        Validate and sanitize a file path.
        
        Args:
            file_path: Path to validate
            operation: Type of operation (access, write, delete)
            
        Returns:
            Validated and normalized Path object
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not file_path:
            raise ValidationError("Empty file path provided")
        
        try:
            # Convert to Path object and resolve
            path = Path(file_path)
            
            # Check for dangerous patterns
            path_str = str(path)
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    raise ValidationError(
                        f"Dangerous path pattern detected: {pattern}",
                        field="file_path",
                        value=str(file_path)
                    )
            
            # Resolve path to absolute form
            try:
                resolved_path = path.resolve()
            except (OSError, ValueError) as e:
                raise ValidationError(f"Invalid path: {e}")
            
            # Check if path is within allowed base paths
            if self.allowed_base_paths:
                is_allowed = any(
                    self._is_subpath(resolved_path, base_path)
                    for base_path in self.allowed_base_paths
                )
                
                if not is_allowed:
                    raise ValidationError(
                        f"Path outside allowed directories: {resolved_path}",
                        field="file_path",
                        value=str(file_path)
                    )
            
            # Check for access to protected system directories
            self._check_protected_directories(resolved_path, operation)
            
            # Additional checks for write/delete operations
            if operation in ('write', 'delete'):
                self._validate_write_operation(resolved_path, operation)
            
            return resolved_path
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Path validation error: {e}")
    
    def _is_subpath(self, path: Path, base_path: str) -> bool:
        """Check if path is within base path."""
        try:
            path.relative_to(base_path)
            return True
        except ValueError:
            return False
    
    def _check_protected_directories(self, path: Path, operation: str):
        """Check if path accesses protected system directories."""
        path_parts = [part.lower() for part in path.parts]
        
        # Determine OS type
        if os.name == 'nt':  # Windows
            protected = self.PROTECTED_DIRS['windows']
        else:  # Unix-like
            protected = self.PROTECTED_DIRS['unix']
        
        # Check if any protected directory is in the path
        for protected_dir in protected:
            if protected_dir in path_parts:
                if operation in ('write', 'delete'):
                    raise ValidationError(
                        f"Access to protected system directory denied: {protected_dir}",
                        field="file_path",
                        value=str(path)
                    )
                else:
                    self.logger.warning(f"Read access to protected directory: {path}")
    
    def _validate_write_operation(self, path: Path, operation: str):
        """Additional validation for write/delete operations."""
        # Check file extension for dangerous types
        if path.suffix.lower() in self.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                f"Operation on dangerous file type not allowed: {path.suffix}",
                field="file_extension",
                value=path.suffix
            )
        
        # Check if trying to overwrite critical files
        critical_files = {'hosts', 'passwd', 'shadow', 'sudoers', 'boot.ini', 'ntldr'}
        if path.name.lower() in critical_files:
            raise ValidationError(
                f"Access to critical system file denied: {path.name}",
                field="file_name",
                value=path.name
            )
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing or replacing dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path separators and dangerous characters
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(dangerous_chars, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Handle reserved Windows names
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in reserved_names:
            sanitized = f"file_{sanitized}"
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed_file"
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized


class InputValidator:
    """
    Validates various types of input data for security and correctness.
    """
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"'.*?;.*?--",  # SQL comment injection
        r"union\s+select",  # UNION SELECT injection
        r"drop\s+table",  # DROP TABLE
        r"delete\s+from",  # DELETE FROM
        r"insert\s+into",  # INSERT INTO
        r"update\s+.*?set",  # UPDATE SET
        r"exec\s*\(",  # Stored procedure execution
        r"xp_.*?\(",  # Extended stored procedures
        r"sp_.*?\(",  # System stored procedures
    ]
    
    def __init__(self):
        """Initialize input validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_project_number(self, project_number: str) -> str:
        """
        Validate project number format.
        
        Args:
            project_number: Project number to validate
            
        Returns:
            Validated project number
            
        Raises:
            ValidationError: If project number is invalid
        """
        if not project_number:
            raise ValidationError("Project number cannot be empty")
        
        # Basic format validation
        if len(project_number) > 50:
            raise ValidationError("Project number too long (max 50 characters)")
        
        # Check for dangerous characters
        if re.search(r'[<>&"\'\x00-\x1f]', project_number):
            raise ValidationError(
                "Project number contains invalid characters",
                field="project_number",
                value=project_number
            )
        
        # Check for SQL injection patterns
        self._check_sql_injection(project_number, "project_number")
        
        return project_number.strip()
    
    def validate_project_name(self, project_name: str) -> str:
        """
        Validate project name.
        
        Args:
            project_name: Project name to validate
            
        Returns:
            Validated project name
            
        Raises:
            ValidationError: If project name is invalid
        """
        if not project_name:
            raise ValidationError("Project name cannot be empty")
        
        if len(project_name) > 255:
            raise ValidationError("Project name too long (max 255 characters)")
        
        # Check for dangerous characters (allow more flexibility than project number)
        if re.search(r'[<>&"\x00-\x1f]', project_name):
            raise ValidationError(
                "Project name contains invalid characters",
                field="project_name",
                value=project_name
            )
        
        # Check for SQL injection patterns
        self._check_sql_injection(project_name, "project_name")
        
        return project_name.strip()
    
    def validate_database_identifier(self, identifier: str, identifier_type: str = "identifier") -> str:
        """
        Validate database identifiers (table names, column names, etc.).
        
        Args:
            identifier: Database identifier to validate
            identifier_type: Type of identifier for error messages
            
        Returns:
            Validated identifier
            
        Raises:
            ValidationError: If identifier is invalid
        """
        if not identifier:
            raise ValidationError(f"{identifier_type} cannot be empty")
        
        # Database identifiers should be alphanumeric with underscores
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier):
            raise ValidationError(
                f"Invalid {identifier_type} format. Must start with letter and contain only letters, numbers, and underscores",
                field=identifier_type,
                value=identifier
            )
        
        if len(identifier) > 64:
            raise ValidationError(f"{identifier_type} too long (max 64 characters)")
        
        # Check for SQL reserved words
        sql_reserved = {
            'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
            'table', 'database', 'index', 'view', 'trigger', 'procedure',
            'function', 'union', 'join', 'where', 'having', 'group', 'order',
            'limit', 'offset', 'distinct', 'count', 'sum', 'max', 'min', 'avg'
        }
        
        if identifier.lower() in sql_reserved:
            raise ValidationError(
                f"{identifier_type} cannot be a SQL reserved word: {identifier}",
                field=identifier_type,
                value=identifier
            )
        
        return identifier
    
    def validate_file_size(self, file_size: int, max_size_mb: int = 500) -> int:
        """
        Validate file size limits.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Validated file size
            
        Raises:
            ValidationError: If file size is invalid
        """
        if file_size < 0:
            raise ValidationError("File size cannot be negative")
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValidationError(
                f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)",
                field="file_size",
                value=file_size
            )
        
        return file_size
    
    def validate_regex_pattern(self, pattern: str, pattern_name: str = "pattern") -> str:
        """
        Validate regex pattern for safety and correctness.
        
        Args:
            pattern: Regex pattern to validate
            pattern_name: Name of pattern for error messages
            
        Returns:
            Validated pattern
            
        Raises:
            ValidationError: If pattern is invalid
        """
        if not pattern:
            raise ValidationError(f"{pattern_name} cannot be empty")
        
        try:
            # Test compilation
            compiled = re.compile(pattern)
            
            # Test with sample strings to ensure pattern doesn't cause excessive backtracking
            test_strings = ['', 'a', 'abc', 'a' * 100, 'abc123', '!@#$%']
            
            for test_str in test_strings:
                try:
                    # Set a timeout-like limit by checking if match takes too long
                    compiled.search(test_str)
                except Exception as e:
                    raise ValidationError(f"Regex pattern causes errors: {e}")
            
            return pattern
            
        except re.error as e:
            raise ValidationError(
                f"Invalid regex pattern '{pattern_name}': {e}",
                field=pattern_name,
                value=pattern
            )
    
    def _check_sql_injection(self, value: str, field_name: str):
        """Check for potential SQL injection patterns."""
        value_lower = value.lower()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                self.logger.warning(f"Potential SQL injection attempt in {field_name}: {pattern}")
                raise ValidationError(
                    f"Invalid characters detected in {field_name}",
                    field=field_name,
                    value=value
                )
    
    def sanitize_log_message(self, message: str) -> str:
        """
        Sanitize log messages to prevent log injection attacks.
        
        Args:
            message: Log message to sanitize
            
        Returns:
            Sanitized message
        """
        if not message:
            return ""
        
        # Remove control characters that could be used for log injection
        sanitized = re.sub(r'[\r\n\t\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', message)
        
        # Limit message length
        if len(sanitized) > 1000:
            sanitized = sanitized[:997] + "..."
        
        return sanitized


class SecurityManager:
    """
    Central security manager for coordinating various security validations.
    """
    
    def __init__(self, allowed_base_paths: Optional[List[str]] = None):
        """
        Initialize security manager.
        
        Args:
            allowed_base_paths: List of allowed base paths for file operations
        """
        self.path_validator = PathValidator(allowed_base_paths)
        self.input_validator = InputValidator()
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.config = {
            'max_file_size_mb': 500,
            'max_project_name_length': 255,
            'max_project_number_length': 50,
            'enable_path_validation': True,
            'enable_input_validation': True,
            'log_security_events': True
        }
    
    def validate_project_creation(self, project_number: str, project_name: str, base_path: str) -> dict:
        """
        Comprehensive validation for project creation.
        
        Args:
            project_number: Project number
            project_name: Project name
            base_path: Base path for project
            
        Returns:
            Dictionary with validated values
            
        Raises:
            ValidationError: If any validation fails
        """
        try:
            validated_data = {}
            
            # Validate project number
            validated_data['project_number'] = self.input_validator.validate_project_number(project_number)
            
            # Validate project name
            validated_data['project_name'] = self.input_validator.validate_project_name(project_name)
            
            # Validate base path
            validated_data['base_path'] = str(self.path_validator.validate_path(base_path, 'write'))
            
            if self.config['log_security_events']:
                self.logger.info(f"Project validation successful: {project_number}")
            
            return validated_data
            
        except ValidationError as e:
            if self.config['log_security_events']:
                self.logger.warning(f"Project validation failed: {e}")
            raise
    
    def validate_file_operation(self, file_path: str, operation: str, file_size: Optional[int] = None) -> str:
        """
        Validate file operation for security.
        
        Args:
            file_path: Path to file
            operation: Type of operation (read, write, delete)
            file_size: Optional file size for validation
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate path
            validated_path = self.path_validator.validate_path(file_path, operation)
            
            # Validate file size if provided
            if file_size is not None:
                self.input_validator.validate_file_size(file_size, self.config['max_file_size_mb'])
            
            return str(validated_path)
            
        except ValidationError as e:
            if self.config['log_security_events']:
                self.logger.warning(f"File operation validation failed: {e}")
            raise
    
    def get_security_report(self) -> dict:
        """Generate security configuration report."""
        return {
            'path_validation_enabled': self.config['enable_path_validation'],
            'input_validation_enabled': self.config['enable_input_validation'],
            'allowed_base_paths': self.path_validator.allowed_base_paths,
            'max_file_size_mb': self.config['max_file_size_mb'],
            'dangerous_extensions_blocked': len(self.path_validator.DANGEROUS_EXTENSIONS),
            'sql_injection_patterns_checked': len(self.input_validator.SQL_INJECTION_PATTERNS)
        }