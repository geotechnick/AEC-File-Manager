"""
Configuration Manager

Handles loading and management of configuration settings from YAML files
with support for environment variable overrides and validation.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List


class ConfigManager:
    """
    Manages application configuration with support for YAML files,
    environment variable overrides, and configuration validation.
    """
    
    DEFAULT_CONFIG = {
        "database": {
            "type": "sqlite",
            "path": "aec_scanner.db",
            "host": "localhost",
            "port": 5432,
            "database": "aec_projects",
            "username": "aec_user",
            "password": ""
        },
        "scanning": {
            "max_workers": 4,
            "batch_size": 1000,
            "max_file_size_mb": 500,
            "generate_hashes": False,
            "excluded_extensions": [".tmp", ".log", ".bak", ".swp"],
            "excluded_directories": ["temp", ".git", "__pycache__", "node_modules"]
        },
        "metadata_extraction": {
            "pdf_processing": {
                "ocr_enabled": False,
                "ocr_language": "eng",
                "extract_images": False
            },
            "cad_processing": {
                "extract_layers": True,
                "extract_blocks": True,
                "max_entities": 10000
            },
            "office_documents": {
                "extract_embedded_objects": False,
                "process_formulas": True
            }
        },
        "file_naming": {
            "project_number_regex": r"PROJ\d+",
            "drawing_number_regex": r"[A-Z]-\d{3}",
            "revision_regex": r"R\d+",
            "discipline_codes": {
                "A": "Architectural",
                "M": "Mechanical", 
                "S": "Structural",
                "E": "Electrical",
                "R": "Civil"
            }
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/scanner.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "reporting": {
            "auto_generate": True,
            "output_formats": ["html", "json"],
            "include_thumbnails": False,
            "max_report_size_mb": 50
        },
        "performance": {
            "connection_timeout": 30,
            "query_timeout": 60,
            "cache_size_mb": 100,
            "enable_compression": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        # Load configuration
        self._load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        self.logger.info(f"Configuration loaded from: {self.config_path or 'default'}")
    
    def _load_config(self) -> None:
        """Load configuration from file or use defaults."""
        # Start with default configuration
        self.config = self._deep_copy_dict(self.DEFAULT_CONFIG)
        
        # If no config path provided, look for default locations
        if not self.config_path:
            default_paths = [
                "config/aec_scanner_config.yaml",
                "config/config.yaml", 
                "aec_scanner_config.yaml",
                "config.yaml"
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    self.config_path = path
                    break
        
        # Load from file if path exists
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    file_config = yaml.safe_load(file)
                    
                    if file_config:
                        # Merge file config with defaults
                        self.config = self._merge_dicts(self.config, file_config)
                        self.logger.info(f"Loaded configuration from {self.config_path}")
                    else:
                        self.logger.warning(f"Configuration file {self.config_path} is empty, using defaults")
                        
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing YAML config file {self.config_path}: {e}")
                self.logger.info("Using default configuration")
            except Exception as e:
                self.logger.error(f"Error loading config file {self.config_path}: {e}")
                self.logger.info("Using default configuration")
        else:
            self.logger.info("No configuration file found, using default configuration")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "AEC_DB_TYPE": "database.type",
            "AEC_DB_HOST": "database.host",
            "AEC_DB_PORT": "database.port",
            "AEC_DB_NAME": "database.database",
            "AEC_DB_USER": "database.username",
            "AEC_DB_PASSWORD": "database.password",
            "AEC_DB_PATH": "database.path",
            "AEC_MAX_WORKERS": "scanning.max_workers",
            "AEC_LOG_LEVEL": "logging.level",
            "AEC_LOG_FILE": "logging.file_path"
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(self.config, config_path, self._convert_env_value(env_value))
                self.logger.debug(f"Applied environment override: {env_var} -> {config_path}")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Handle comma-separated lists
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value
    
    def _set_nested_value(self, config_dict: Dict[str, Any], path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = path.split('.')
        current = config_dict
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _validate_config(self) -> None:
        """Validate configuration values and apply constraints."""
        # Validate database configuration
        db_type = self.config.get('database', {}).get('type', 'sqlite')
        if db_type not in ['sqlite', 'postgresql']:
            self.logger.warning(f"Invalid database type '{db_type}', defaulting to 'sqlite'")
            self.config['database']['type'] = 'sqlite'
        
        # Validate scanning configuration
        max_workers = self.config.get('scanning', {}).get('max_workers', 4)
        if not isinstance(max_workers, int) or max_workers < 1:
            self.logger.warning(f"Invalid max_workers '{max_workers}', defaulting to 4")
            self.config['scanning']['max_workers'] = 4
        
        # Validate file size limits
        max_file_size = self.config.get('scanning', {}).get('max_file_size_mb', 500)
        if not isinstance(max_file_size, (int, float)) or max_file_size <= 0:
            self.logger.warning(f"Invalid max_file_size_mb '{max_file_size}', defaulting to 500")
            self.config['scanning']['max_file_size_mb'] = 500
        
        # Validate logging level
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            self.logger.warning(f"Invalid log level '{log_level}', defaulting to 'INFO'")
            self.config['logging']['level'] = 'INFO'
        
        # Ensure log directory exists
        log_file = self.config.get('logging', {}).get('file_path', 'logs/scanner.log')
        log_dir = Path(log_file).parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created log directory: {log_dir}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.type')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        self._set_nested_value(self.config, key, value)
        self.logger.debug(f"Set configuration: {key} = {value}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration section."""
        return self.config.get('database', {})
    
    def get_scanning_config(self) -> Dict[str, Any]:
        """Get scanning configuration section."""
        return self.config.get('scanning', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration section."""
        return self.config.get('logging', {})
    
    def get_metadata_config(self) -> Dict[str, Any]:
        """Get metadata extraction configuration section."""
        return self.config.get('metadata_extraction', {})
    
    def save_config(self, output_path: Optional[str] = None) -> bool:
        """
        Save current configuration to YAML file.
        
        Args:
            output_path: Optional output path, defaults to current config path
            
        Returns:
            True if successful, False otherwise
        """
        output_path = output_path or self.config_path or "config/aec_scanner_config.yaml"
        
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                yaml.dump(
                    self.config, 
                    file, 
                    default_flow_style=False,
                    indent=2,
                    sort_keys=True
                )
            
            self.logger.info(f"Configuration saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._load_config()
            self._apply_env_overrides()
            self._validate_config()
            self.logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return self._deep_copy_dict(self.config)
    
    def validate_file_naming_patterns(self) -> bool:
        """
        Validate file naming regex patterns.
        
        Returns:
            True if all patterns are valid, False otherwise
        """
        import re
        
        patterns = self.config.get('file_naming', {})
        valid = True
        
        for pattern_name, pattern in patterns.items():
            if isinstance(pattern, str) and pattern_name.endswith('_regex'):
                try:
                    re.compile(pattern)
                    self.logger.debug(f"Valid regex pattern: {pattern_name}")
                except re.error as e:
                    self.logger.error(f"Invalid regex pattern '{pattern_name}': {pattern} - {e}")
                    valid = False
        
        return valid
    
    def get_environment_info(self) -> Dict[str, str]:
        """Get information about environment variables that affect configuration."""
        env_info = {}
        
        env_vars = [
            "AEC_DB_TYPE", "AEC_DB_HOST", "AEC_DB_PORT", "AEC_DB_NAME",
            "AEC_DB_USER", "AEC_DB_PASSWORD", "AEC_DB_PATH",
            "AEC_MAX_WORKERS", "AEC_LOG_LEVEL", "AEC_LOG_FILE"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            env_info[var] = value if value is not None else "not_set"
        
        return env_info
    
    @staticmethod
    def _deep_copy_dict(source: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary."""
        result = {}
        
        for key, value in source.items():
            if isinstance(value, dict):
                result[key] = ConfigManager._deep_copy_dict(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = ConfigManager._deep_copy_dict(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def create_sample_config(self, output_path: str = "config/aec_scanner_config.yaml") -> bool:
        """
        Create a sample configuration file with all available options.
        
        Args:
            output_path: Path where sample config will be created
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Add comments to the default configuration
            sample_config = self._add_config_comments(self.DEFAULT_CONFIG)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write("# AEC Directory Scanner Configuration File\n")
                file.write("# This file contains all available configuration options with default values\n")
                file.write("# Uncomment and modify values as needed\n\n")
                
                yaml.dump(
                    sample_config,
                    file,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=True
                )
            
            self.logger.info(f"Sample configuration created at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create sample configuration: {e}")
            return False
    
    def _add_config_comments(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add documentation comments to configuration sections."""
        # This is a simplified version - in a full implementation,
        # you might use a YAML library that preserves comments
        return config