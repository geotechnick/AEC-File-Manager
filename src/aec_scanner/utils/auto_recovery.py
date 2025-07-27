"""
Auto-Recovery and Self-Healing System

Intelligent system that automatically detects and fixes common issues,
recovers from errors, and maintains system health without user intervention.
"""

import os
import shutil
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import traceback


class RecoveryAction(Enum):
    """Types of recovery actions."""
    REPAIR = "repair"
    RECREATE = "recreate"
    RESTART = "restart"
    ROLLBACK = "rollback"
    CLEANUP = "cleanup"
    SKIP = "skip"


@dataclass
class RecoveryResult:
    """Result of a recovery action."""
    success: bool
    action: RecoveryAction
    description: str
    details: str = ""
    auto_applied: bool = True


class AutoRecovery:
    """
    Auto-recovery system that detects and fixes common issues automatically.
    """
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None,
        auto_fix: bool = True,
        backup_enabled: bool = True
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.auto_fix = auto_fix
        self.backup_enabled = backup_enabled
        
        # Recovery statistics
        self.recovery_stats = {
            'total_issues': 0,
            'auto_fixed': 0,
            'manual_required': 0,
            'last_check': None
        }
        
        # Issue patterns and their recovery actions
        self.recovery_patterns = self._initialize_recovery_patterns()
        
        # Health monitoring
        self._health_checks: List[Callable] = []
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def _initialize_recovery_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize recovery patterns for common issues."""
        return {
            'database_locked': {
                'pattern': ['database is locked', 'sqlite3.OperationalError'],
                'action': RecoveryAction.RESTART,
                'handler': self._recover_database_lock,
                'auto_fix': True,
                'severity': 'medium'
            },
            'missing_database': {
                'pattern': ['no such file or directory', 'database'],
                'action': RecoveryAction.RECREATE,
                'handler': self._recover_missing_database,
                'auto_fix': True,
                'severity': 'high'
            },
            'corrupted_database': {
                'pattern': ['database disk image is malformed', 'corruption'],
                'action': RecoveryAction.ROLLBACK,
                'handler': self._recover_corrupted_database,
                'auto_fix': True,
                'severity': 'critical'
            },
            'permission_denied': {
                'pattern': ['permission denied', 'access denied'],
                'action': RecoveryAction.REPAIR,
                'handler': self._recover_permissions,
                'auto_fix': False,  # Requires user attention
                'severity': 'high'
            },
            'disk_full': {
                'pattern': ['no space left on device', 'disk full'],
                'action': RecoveryAction.CLEANUP,
                'handler': self._recover_disk_space,
                'auto_fix': True,
                'severity': 'critical'
            },
            'memory_error': {
                'pattern': ['memory error', 'out of memory'],
                'action': RecoveryAction.RESTART,
                'handler': self._recover_memory_error,
                'auto_fix': True,
                'severity': 'high'
            },
            'missing_directories': {
                'pattern': ['no such file or directory', 'folder'],
                'action': RecoveryAction.RECREATE,
                'handler': self._recover_missing_directories,
                'auto_fix': True,
                'severity': 'medium'
            },
            'config_error': {
                'pattern': ['configuration error', 'config invalid'],
                'action': RecoveryAction.REPAIR,
                'handler': self._recover_config_error,
                'auto_fix': True,
                'severity': 'medium'
            }
        }
    
    def analyze_error(self, error: Exception, context: Dict[str, Any] = None) -> Optional[RecoveryResult]:
        """
        Analyze an error and attempt automatic recovery.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            Recovery result if recovery was attempted, None otherwise
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        self.recovery_stats['total_issues'] += 1
        
        # Find matching recovery pattern
        for pattern_name, pattern_info in self.recovery_patterns.items():
            patterns = pattern_info['pattern']
            
            if any(pattern in error_str or pattern in error_type for pattern in patterns):
                self.logger.info(f"Detected issue pattern: {pattern_name}")
                
                if self.auto_fix and pattern_info['auto_fix']:
                    return self._attempt_recovery(pattern_name, pattern_info, error, context)
                else:
                    self.logger.warning(f"Issue detected but auto-fix disabled: {pattern_name}")
                    return RecoveryResult(
                        success=False,
                        action=pattern_info['action'],
                        description=f"Manual intervention required for: {pattern_name}",
                        auto_applied=False
                    )
        
        # No matching pattern found
        self.logger.debug(f"No recovery pattern found for error: {error}")
        return None
    
    def _attempt_recovery(
        self, 
        pattern_name: str, 
        pattern_info: Dict[str, Any], 
        error: Exception,
        context: Dict[str, Any] = None
    ) -> RecoveryResult:
        """Attempt to recover from an identified issue."""
        self.logger.info(f"Attempting auto-recovery for: {pattern_name}")
        
        try:
            # Create backup if enabled
            if self.backup_enabled and pattern_info['severity'] in ['high', 'critical']:
                self._create_emergency_backup(context)
            
            # Execute recovery handler
            handler = pattern_info['handler']
            result = handler(error, context or {})
            
            if result.success:
                self.recovery_stats['auto_fixed'] += 1
                self.logger.info(f"Auto-recovery successful: {result.description}")
            else:
                self.recovery_stats['manual_required'] += 1
                self.logger.warning(f"Auto-recovery failed: {result.description}")
            
            return result
            
        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
            self.recovery_stats['manual_required'] += 1
            
            return RecoveryResult(
                success=False,
                action=pattern_info['action'],
                description=f"Recovery failed for {pattern_name}",
                details=str(recovery_error),
                auto_applied=True
            )
    
    def _recover_database_lock(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from database lock issues."""
        db_path = context.get('database_path')
        if not db_path:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RESTART,
                description="Database path not provided in context"
            )
        
        try:
            # Wait for lock to release
            max_wait = 30  # seconds
            wait_interval = 1
            
            for attempt in range(max_wait):
                try:
                    # Try to connect briefly
                    conn = sqlite3.connect(db_path, timeout=1)
                    conn.execute("SELECT 1")
                    conn.close()
                    
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.RESTART,
                        description=f"Database lock cleared after {attempt + 1} seconds"
                    )
                    
                except sqlite3.OperationalError:
                    time.sleep(wait_interval)
                    continue
            
            # If still locked, try to remove lock file
            lock_files = [f"{db_path}-wal", f"{db_path}-shm"]
            removed_files = []
            
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        removed_files.append(lock_file)
                    except OSError:
                        pass
            
            if removed_files:
                return RecoveryResult(
                    success=True,
                    action=RecoveryAction.REPAIR,
                    description=f"Removed lock files: {', '.join(removed_files)}"
                )
            
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RESTART,
                description="Could not clear database lock"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RESTART,
                description=f"Database lock recovery failed: {e}"
            )
    
    def _recover_missing_database(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from missing database."""
        try:
            # Try to recreate database from backup
            db_path = context.get('database_path')
            if not db_path:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.RECREATE,
                    description="Database path not provided"
                )
            
            # Look for recent backup
            backup_path = self._find_recent_backup(db_path)
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, db_path)
                return RecoveryResult(
                    success=True,
                    action=RecoveryAction.ROLLBACK,
                    description=f"Restored database from backup: {backup_path}"
                )
            
            # Create new database if no backup
            database_manager = context.get('database_manager')
            if database_manager:
                success = database_manager.initialize_database()
                if success:
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.RECREATE,
                        description="Created new database with schema"
                    )
            
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RECREATE,
                description="Could not recreate database"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RECREATE,
                description=f"Database recreation failed: {e}"
            )
    
    def _recover_corrupted_database(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from corrupted database."""
        try:
            db_path = context.get('database_path')
            if not db_path:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.ROLLBACK,
                    description="Database path not provided"
                )
            
            # Try to repair using SQLite's built-in recovery
            backup_db = f"{db_path}.corrupt_backup"
            
            # Backup corrupted database
            shutil.copy2(db_path, backup_db)
            
            # Attempt to dump and recreate
            try:
                # Export data using .dump
                dump_file = f"{db_path}.dump"
                os.system(f'sqlite3 "{db_path}" ".dump" > "{dump_file}"')
                
                # Remove corrupted database
                os.remove(db_path)
                
                # Recreate from dump
                os.system(f'sqlite3 "{db_path}" ".read {dump_file}"')
                
                # Clean up
                os.remove(dump_file)
                
                return RecoveryResult(
                    success=True,
                    action=RecoveryAction.REPAIR,
                    description=f"Repaired corrupted database, backup saved as {backup_db}"
                )
                
            except Exception:
                # If repair fails, restore from backup
                backup_path = self._find_recent_backup(db_path)
                if backup_path and os.path.exists(backup_path):
                    shutil.copy2(backup_path, db_path)
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.ROLLBACK,
                        description=f"Restored from backup due to corruption"
                    )
                
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.ROLLBACK,
                    description="Could not recover corrupted database"
                )
                
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.ROLLBACK,
                description=f"Corruption recovery failed: {e}"
            )
    
    def _recover_permissions(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from permission issues."""
        try:
            file_path = context.get('file_path') or context.get('database_path')
            if not file_path:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.REPAIR,
                    description="No file path provided for permission recovery"
                )
            
            # Try to fix permissions
            path_obj = Path(file_path)
            
            # For directories
            if path_obj.is_dir():
                try:
                    path_obj.chmod(0o755)
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.REPAIR,
                        description=f"Fixed directory permissions: {file_path}"
                    )
                except OSError:
                    pass
            
            # For files
            elif path_obj.is_file():
                try:
                    path_obj.chmod(0o644)
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.REPAIR,
                        description=f"Fixed file permissions: {file_path}"
                    )
                except OSError:
                    pass
            
            return RecoveryResult(
                success=False,
                action=RecoveryAction.REPAIR,
                description="Permission recovery requires manual intervention"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.REPAIR,
                description=f"Permission recovery failed: {e}"
            )
    
    def _recover_disk_space(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from disk space issues."""
        try:
            cleanup_actions = []
            freed_space = 0
            
            # Clean temporary files
            temp_dirs = ['/tmp', os.path.expanduser('~/tmp'), 'temp']
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    freed = self._cleanup_temp_files(temp_dir)
                    if freed > 0:
                        cleanup_actions.append(f"Cleaned {temp_dir}: {freed}MB")
                        freed_space += freed
            
            # Clean old log files
            log_dirs = ['logs', os.path.expanduser('~/.aec_scanner/logs')]
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    freed = self._cleanup_old_logs(log_dir)
                    if freed > 0:
                        cleanup_actions.append(f"Cleaned logs: {freed}MB")
                        freed_space += freed
            
            # Clean old backups (keep only recent ones)
            backup_dirs = ['backups', os.path.expanduser('~/.aec_scanner/backups')]
            for backup_dir in backup_dirs:
                if os.path.exists(backup_dir):
                    freed = self._cleanup_old_backups(backup_dir)
                    if freed > 0:
                        cleanup_actions.append(f"Cleaned old backups: {freed}MB")
                        freed_space += freed
            
            if freed_space > 0:
                return RecoveryResult(
                    success=True,
                    action=RecoveryAction.CLEANUP,
                    description=f"Freed {freed_space}MB disk space",
                    details="; ".join(cleanup_actions)
                )
            else:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.CLEANUP,
                    description="No disk space could be automatically freed"
                )
                
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.CLEANUP,
                description=f"Disk cleanup failed: {e}"
            )
    
    def _recover_memory_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from memory issues."""
        try:
            # Suggest memory optimization
            suggestions = [
                "Reduce batch size in scanning configuration",
                "Disable file hashing for large files",
                "Increase system virtual memory",
                "Close other memory-intensive applications"
            ]
            
            # Try to clear any caches
            if 'scanner' in context:
                scanner = context['scanner']
                if hasattr(scanner, 'clear_caches'):
                    scanner.clear_caches()
            
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RESTART,
                description="Memory optimization suggestions provided",
                details="; ".join(suggestions)
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RESTART,
                description=f"Memory recovery failed: {e}"
            )
    
    def _recover_missing_directories(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from missing directories."""
        try:
            missing_path = context.get('file_path') or context.get('directory_path')
            if not missing_path:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.RECREATE,
                    description="No directory path provided"
                )
            
            path_obj = Path(missing_path)
            
            # Create missing directory and parents
            path_obj.mkdir(parents=True, exist_ok=True)
            
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RECREATE,
                description=f"Created missing directory: {missing_path}"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.RECREATE,
                description=f"Directory creation failed: {e}"
            )
    
    def _recover_config_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from configuration errors."""
        try:
            config_path = context.get('config_path')
            if not config_path:
                return RecoveryResult(
                    success=False,
                    action=RecoveryAction.REPAIR,
                    description="No config path provided"
                )
            
            # Try to create default configuration
            config_manager = context.get('config_manager')
            if config_manager:
                success = config_manager.create_default_config()
                if success:
                    return RecoveryResult(
                        success=True,
                        action=RecoveryAction.REPAIR,
                        description="Created default configuration"
                    )
            
            return RecoveryResult(
                success=False,
                action=RecoveryAction.REPAIR,
                description="Could not repair configuration"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.REPAIR,
                description=f"Config recovery failed: {e}"
            )
    
    def _create_emergency_backup(self, context: Dict[str, Any]) -> None:
        """Create emergency backup before risky recovery operations."""
        try:
            db_path = context.get('database_path')
            if db_path and os.path.exists(db_path):
                backup_dir = Path(db_path).parent / 'emergency_backups'
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = backup_dir / f"emergency_backup_{timestamp}.db"
                
                shutil.copy2(db_path, backup_path)
                self.logger.info(f"Created emergency backup: {backup_path}")
                
        except Exception as e:
            self.logger.warning(f"Could not create emergency backup: {e}")
    
    def _find_recent_backup(self, db_path: str) -> Optional[str]:
        """Find the most recent backup of a database."""
        try:
            db_dir = Path(db_path).parent
            backup_patterns = [
                db_dir / 'backups' / '*.db',
                db_dir / 'emergency_backups' / '*.db',
                db_dir / f"{Path(db_path).stem}_backup_*.db"
            ]
            
            all_backups = []
            for pattern in backup_patterns:
                all_backups.extend(Path().glob(str(pattern)))
            
            if all_backups:
                # Sort by modification time
                latest_backup = max(all_backups, key=lambda p: p.stat().st_mtime)
                return str(latest_backup)
            
        except Exception as e:
            self.logger.debug(f"Error finding backup: {e}")
        
        return None
    
    def _cleanup_temp_files(self, temp_dir: str) -> int:
        """Clean temporary files and return freed space in MB."""
        try:
            freed_bytes = 0
            temp_path = Path(temp_dir)
            
            # Remove files older than 1 day
            cutoff_time = time.time() - 86400  # 24 hours
            
            for file_path in temp_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        freed_bytes += size
                    except OSError:
                        continue
            
            return freed_bytes // (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 0
    
    def _cleanup_old_logs(self, log_dir: str) -> int:
        """Clean old log files and return freed space in MB."""
        try:
            freed_bytes = 0
            log_path = Path(log_dir)
            
            # Remove log files older than 7 days
            cutoff_time = time.time() - (7 * 86400)
            
            for log_file in log_path.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_time:
                    try:
                        size = log_file.stat().st_size
                        log_file.unlink()
                        freed_bytes += size
                    except OSError:
                        continue
            
            return freed_bytes // (1024 * 1024)
            
        except Exception:
            return 0
    
    def _cleanup_old_backups(self, backup_dir: str) -> int:
        """Clean old backup files, keeping only recent ones."""
        try:
            freed_bytes = 0
            backup_path = Path(backup_dir)
            
            # Keep only last 5 backups
            backup_files = sorted(
                backup_path.glob('*.db*'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backup_files[5:]:  # Remove all but 5 most recent
                try:
                    size = old_backup.stat().st_size
                    old_backup.unlink()
                    freed_bytes += size
                except OSError:
                    continue
            
            return freed_bytes // (1024 * 1024)
            
        except Exception:
            return 0
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        self.recovery_stats['last_check'] = datetime.now().isoformat()
        return self.recovery_stats.copy()


# Global recovery instance for easy access
_global_recovery = None

def get_auto_recovery(
    logger: Optional[logging.Logger] = None,
    auto_fix: bool = True
) -> AutoRecovery:
    """Get or create global auto-recovery instance."""
    global _global_recovery
    if _global_recovery is None:
        _global_recovery = AutoRecovery(logger=logger, auto_fix=auto_fix)
    return _global_recovery


def handle_with_recovery(func: Callable) -> Callable:
    """Decorator to automatically handle errors with recovery."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            recovery = get_auto_recovery()
            context = kwargs.get('recovery_context', {})
            
            result = recovery.analyze_error(e, context)
            if result and result.success:
                # Retry the operation after successful recovery
                try:
                    return func(*args, **kwargs)
                except Exception as retry_error:
                    # If retry fails, raise the original error
                    raise e
            else:
                # No recovery possible or recovery failed
                raise e
    
    return wrapper