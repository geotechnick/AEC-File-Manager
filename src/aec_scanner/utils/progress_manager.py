"""
Progress Manager

Enhanced progress tracking with beautiful progress bars, real-time updates,
ETA calculations, and user-friendly feedback.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging


class ProgressStyle(Enum):
    """Progress bar styles."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    MINIMAL = "minimal"
    VERBOSE = "verbose"


@dataclass
class ProgressState:
    """Progress tracking state."""
    current: int = 0
    total: int = 0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    operation: str = ""
    sub_operation: str = ""
    errors_count: int = 0
    warnings_count: int = 0
    custom_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_data is None:
            self.custom_data = {}


class ProgressManager:
    """
    Advanced progress manager with beautiful progress bars and real-time feedback.
    """
    
    def __init__(
        self, 
        style: ProgressStyle = ProgressStyle.DETAILED,
        update_interval: float = 0.1,
        logger: Optional[logging.Logger] = None
    ):
        self.style = style
        self.update_interval = update_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self.state = ProgressState()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._update_thread: Optional[threading.Thread] = None
        self._last_display = ""
        
        # Progress bar characters
        self.progress_chars = {
            'filled': '█',
            'partial': ['▏', '▎', '▍', '▌', '▋', '▊', '▉'],
            'empty': '░',
            'left_border': '▌',
            'right_border': '▐'
        }
        
        # Color codes (ANSI)
        self.colors = {
            'green': '\033[92m',
            'blue': '\033[94m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'cyan': '\033[96m',
            'magenta': '\033[95m',
            'white': '\033[97m',
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m'
        }
    
    def start(self, operation: str, total: int = 0, auto_update: bool = True) -> None:
        """
        Start progress tracking.
        
        Args:
            operation: Description of the operation
            total: Total number of items to process
            auto_update: Whether to automatically update display
        """
        with self._lock:
            self.state = ProgressState(
                current=0,
                total=total,
                start_time=datetime.now(),
                last_update=datetime.now(),
                operation=operation
            )
        
        if auto_update and self.style != ProgressStyle.MINIMAL:
            self._start_auto_update()
        
        self.logger.info(f"Started progress tracking: {operation}")
    
    def update(
        self, 
        current: Optional[int] = None, 
        increment: int = 1,
        sub_operation: str = "",
        custom_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update progress.
        
        Args:
            current: Current position (if None, increments by increment)
            increment: Amount to increment if current is None
            sub_operation: Current sub-operation description
            custom_data: Additional data to track
        """
        with self._lock:
            if current is not None:
                self.state.current = current
            else:
                self.state.current += increment
            
            self.state.last_update = datetime.now()
            self.state.sub_operation = sub_operation
            
            if custom_data:
                self.state.custom_data.update(custom_data)
        
        # Manual update if not auto-updating
        if not self._update_thread or not self._update_thread.is_alive():
            self._display_progress()
    
    def add_error(self, error_msg: str = "") -> None:
        """Record an error."""
        with self._lock:
            self.state.errors_count += 1
            if error_msg:
                self.logger.error(f"Progress tracking error: {error_msg}")
    
    def add_warning(self, warning_msg: str = "") -> None:
        """Record a warning."""
        with self._lock:
            self.state.warnings_count += 1
            if warning_msg:
                self.logger.warning(f"Progress tracking warning: {warning_msg}")
    
    def finish(self, success: bool = True, final_message: str = "") -> None:
        """
        Finish progress tracking.
        
        Args:
            success: Whether the operation completed successfully
            final_message: Final message to display
        """
        self._stop_auto_update()
        
        with self._lock:
            if self.state.total > 0:
                self.state.current = self.state.total
        
        # Final display
        self._display_final_summary(success, final_message)
        
        self.logger.info(f"Finished progress tracking: {self.state.operation}")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        with self._lock:
            elapsed = self._get_elapsed_time()
            eta = self._calculate_eta()
            speed = self._calculate_speed()
            
            return {
                'current': self.state.current,
                'total': self.state.total,
                'percentage': self._get_percentage(),
                'elapsed_seconds': elapsed.total_seconds() if elapsed else 0,
                'eta_seconds': eta.total_seconds() if eta else None,
                'speed_per_second': speed,
                'operation': self.state.operation,
                'sub_operation': self.state.sub_operation,
                'errors': self.state.errors_count,
                'warnings': self.state.warnings_count,
                'custom_data': self.state.custom_data.copy()
            }
    
    def _start_auto_update(self) -> None:
        """Start automatic progress display updates."""
        if self._update_thread and self._update_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self._update_thread.start()
    
    def _stop_auto_update(self) -> None:
        """Stop automatic progress updates."""
        self._stop_event.set()
        if self._update_thread:
            self._update_thread.join(timeout=1.0)
    
    def _auto_update_loop(self) -> None:
        """Auto-update loop for progress display."""
        while not self._stop_event.is_set():
            self._display_progress()
            time.sleep(self.update_interval)
    
    def _display_progress(self) -> None:
        """Display current progress."""
        try:
            if self.style == ProgressStyle.MINIMAL:
                return
            
            display_text = self._build_progress_display()
            
            # Only update if display changed (reduces flicker)
            if display_text != self._last_display:
                print(f"\r{display_text}", end='', flush=True)
                self._last_display = display_text
                
        except Exception as e:
            self.logger.debug(f"Error displaying progress: {e}")
    
    def _build_progress_display(self) -> str:
        """Build the progress display string."""
        with self._lock:
            if self.style == ProgressStyle.SIMPLE:
                return self._build_simple_display()
            elif self.style == ProgressStyle.DETAILED:
                return self._build_detailed_display()
            elif self.style == ProgressStyle.VERBOSE:
                return self._build_verbose_display()
            else:
                return self._build_simple_display()
    
    def _build_simple_display(self) -> str:
        """Build simple progress display."""
        percentage = self._get_percentage()
        bar = self._create_progress_bar(30)
        
        return f"{self.state.operation}: {bar} {percentage:.1f}%"
    
    def _build_detailed_display(self) -> str:
        """Build detailed progress display."""
        percentage = self._get_percentage()
        bar = self._create_progress_bar(40)
        elapsed = self._get_elapsed_time()
        eta = self._calculate_eta()
        speed = self._calculate_speed()
        
        # Build components
        parts = []
        
        # Operation name
        if self.state.operation:
            parts.append(f"{self.colors['bold']}{self.state.operation}{self.colors['reset']}")
        
        # Progress bar with percentage
        parts.append(f"{bar} {self.colors['cyan']}{percentage:.1f}%{self.colors['reset']}")
        
        # Current/Total
        if self.state.total > 0:
            parts.append(f"({self.state.current:,}/{self.state.total:,})")
        else:
            parts.append(f"({self.state.current:,})")
        
        # Speed
        if speed > 0:
            parts.append(f"{self.colors['green']}{speed:.1f}/s{self.colors['reset']}")
        
        # Time info
        if elapsed:
            elapsed_str = self._format_duration(elapsed)
            if eta and self.state.total > 0:
                eta_str = self._format_duration(eta)
                parts.append(f"[{elapsed_str} < {eta_str}]")
            else:
                parts.append(f"[{elapsed_str}]")
        
        # Errors/Warnings
        if self.state.errors_count > 0 or self.state.warnings_count > 0:
            status_parts = []
            if self.state.errors_count > 0:
                status_parts.append(f"{self.colors['red']}{self.state.errors_count} errors{self.colors['reset']}")
            if self.state.warnings_count > 0:
                status_parts.append(f"{self.colors['yellow']}{self.state.warnings_count} warnings{self.colors['reset']}")
            parts.append(f"({', '.join(status_parts)})")
        
        # Sub-operation
        if self.state.sub_operation:
            parts.append(f"{self.colors['dim']}- {self.state.sub_operation}{self.colors['reset']}")
        
        return " ".join(parts)
    
    def _build_verbose_display(self) -> str:
        """Build verbose progress display with multiple lines."""
        lines = []
        
        # Main progress line
        lines.append(self._build_detailed_display())
        
        # Additional custom data
        if self.state.custom_data:
            for key, value in self.state.custom_data.items():
                if key.startswith('_'):  # Skip internal data
                    continue
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def _create_progress_bar(self, width: int) -> str:
        """Create a visual progress bar."""
        if self.state.total <= 0:
            # Indeterminate progress
            pos = int(time.time() * 2) % width
            bar = [self.progress_chars['empty']] * width
            bar[pos] = self.progress_chars['filled']
            return f"{self.colors['blue']}{''.join(bar)}{self.colors['reset']}"
        
        # Determinate progress
        percentage = self._get_percentage() / 100
        filled_width = percentage * width
        full_blocks = int(filled_width)
        
        # Build bar
        bar_parts = []
        
        # Filled portion
        if full_blocks > 0:
            bar_parts.append(self.colors['green'] + self.progress_chars['filled'] * full_blocks)
        
        # Partial block
        remainder = filled_width - full_blocks
        if remainder > 0 and full_blocks < width:
            partial_index = min(int(remainder * len(self.progress_chars['partial'])), 
                              len(self.progress_chars['partial']) - 1)
            bar_parts.append(self.colors['green'] + self.progress_chars['partial'][partial_index])
            full_blocks += 1
        
        # Empty portion
        empty_blocks = width - full_blocks
        if empty_blocks > 0:
            bar_parts.append(self.colors['dim'] + self.progress_chars['empty'] * empty_blocks)
        
        bar_parts.append(self.colors['reset'])
        
        return ''.join(bar_parts)
    
    def _get_percentage(self) -> float:
        """Get completion percentage."""
        if self.state.total <= 0:
            return 0.0
        return min((self.state.current / self.state.total) * 100, 100.0)
    
    def _get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since start."""
        if not self.state.start_time:
            return None
        return datetime.now() - self.state.start_time
    
    def _calculate_eta(self) -> Optional[timedelta]:
        """Calculate estimated time to completion."""
        if not self.state.start_time or self.state.total <= 0 or self.state.current <= 0:
            return None
        
        elapsed = self._get_elapsed_time()
        if not elapsed:
            return None
        
        remaining_items = self.state.total - self.state.current
        if remaining_items <= 0:
            return timedelta(0)
        
        rate = self.state.current / elapsed.total_seconds()
        if rate <= 0:
            return None
        
        eta_seconds = remaining_items / rate
        return timedelta(seconds=eta_seconds)
    
    def _calculate_speed(self) -> float:
        """Calculate processing speed (items per second)."""
        if not self.state.start_time or self.state.current <= 0:
            return 0.0
        
        elapsed = self._get_elapsed_time()
        if not elapsed or elapsed.total_seconds() <= 0:
            return 0.0
        
        return self.state.current / elapsed.total_seconds()
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _display_final_summary(self, success: bool, final_message: str) -> None:
        """Display final summary."""
        # Clear current line
        print("\r" + " " * 100 + "\r", end='')
        
        elapsed = self._get_elapsed_time()
        speed = self._calculate_speed()
        
        # Status icon and color
        if success:
            status_icon = "✅"
            status_color = self.colors['green']
        else:
            status_icon = "❌"
            status_color = self.colors['red']
        
        # Build summary
        summary_parts = [
            f"{status_icon} {status_color}{self.state.operation}{self.colors['reset']}"
        ]
        
        if final_message:
            summary_parts.append(f"- {final_message}")
        
        # Stats
        if self.state.total > 0:
            summary_parts.append(f"({self.state.current:,}/{self.state.total:,} items)")
        else:
            summary_parts.append(f"({self.state.current:,} items)")
        
        if elapsed:
            summary_parts.append(f"in {self._format_duration(elapsed)}")
        
        if speed > 0:
            summary_parts.append(f"({speed:.1f}/s)")
        
        # Errors/Warnings summary
        if self.state.errors_count > 0 or self.state.warnings_count > 0:
            issues = []
            if self.state.errors_count > 0:
                issues.append(f"{self.colors['red']}{self.state.errors_count} errors{self.colors['reset']}")
            if self.state.warnings_count > 0:
                issues.append(f"{self.colors['yellow']}{self.state.warnings_count} warnings{self.colors['reset']}")
            summary_parts.append(f"[{', '.join(issues)}]")
        
        print(" ".join(summary_parts))


class SimpleProgressCallback:
    """Simple progress callback wrapper for legacy code."""
    
    def __init__(self, manager: ProgressManager):
        self.manager = manager
    
    def __call__(self, current: int, total: int) -> None:
        """Legacy callback interface."""
        if hasattr(self.manager.state, 'total') and self.manager.state.total != total:
            self.manager.state.total = total
        self.manager.update(current=current)


def create_progress_callback(
    operation: str,
    style: ProgressStyle = ProgressStyle.DETAILED
) -> Callable[[int, int], None]:
    """
    Create a simple progress callback function.
    
    Args:
        operation: Operation description
        style: Progress bar style
        
    Returns:
        Progress callback function
    """
    manager = ProgressManager(style=style)
    
    def callback(current: int, total: int) -> None:
        if not hasattr(callback, '_started'):
            manager.start(operation, total)
            callback._started = True
        
        manager.update(current=current)
        
        if current >= total:
            manager.finish(success=True)
    
    return callback