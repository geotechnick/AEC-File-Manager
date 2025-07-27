"""
Enhanced Output Formatter

Beautiful, user-friendly output formatting with multiple styles,
smart summaries, and visual elements for improved readability.
"""

import json
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re


class OutputFormat(Enum):
    """Available output formats."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"
    MINIMAL = "minimal"


@dataclass
class FormatTheme:
    """Visual theme for output formatting."""
    primary_color: str
    secondary_color: str
    success_color: str
    warning_color: str
    error_color: str
    info_color: str
    accent_color: str


class OutputFormatter:
    """
    Enhanced output formatter with beautiful, user-friendly formatting
    and smart summaries tailored for different use cases.
    """
    
    def __init__(self, default_format: OutputFormat = OutputFormat.SUMMARY):
        self.default_format = default_format
        
        # Color themes
        self.themes = {
            'default': FormatTheme(
                primary_color='#667eea',
                secondary_color='#764ba2',
                success_color='#10b981',
                warning_color='#f59e0b',
                error_color='#ef4444',
                info_color='#3b82f6',
                accent_color='#8b5cf6'
            ),
            'professional': FormatTheme(
                primary_color='#1f2937',
                secondary_color='#374151',
                success_color='#059669',
                warning_color='#d97706',
                error_color='#dc2626',
                info_color='#2563eb',
                accent_color='#7c3aed'
            )
        }
        
        # Terminal colors (ANSI codes)
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'underline': '\033[4m',
            'green': '\033[92m',
            'blue': '\033[94m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'cyan': '\033[96m',
            'magenta': '\033[95m',
            'white': '\033[97m'
        }
        
        # Unicode symbols for visual enhancement
        self.symbols = {
            'check': '✅',
            'cross': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'rocket': '🚀',
            'folder': '📁',
            'file': '📄',
            'chart': '📊',
            'clock': '⏱️',
            'gear': '⚙️',
            'star': '⭐',
            'lightning': '⚡',
            'magnify': '🔍',
            'hammer': '🔨',
            'box': '📦',
            'arrow_right': '→',
            'bullet': '•'
        }
    
    def format_output(
        self, 
        data: Dict[str, Any], 
        format_type: OutputFormat = None,
        theme: str = 'default',
        title: str = None
    ) -> str:
        """
        Format data according to the specified format type.
        
        Args:
            data: Data to format
            format_type: Output format (uses default if None)
            theme: Theme to use for formatting
            title: Optional title for the output
            
        Returns:
            Formatted string
        """
        if format_type is None:
            format_type = self.default_format
        
        if format_type == OutputFormat.SUMMARY:
            return self._format_summary(data, theme, title)
        elif format_type == OutputFormat.DETAILED:
            return self._format_detailed(data, theme, title)
        elif format_type == OutputFormat.JSON:
            return self._format_json(data)
        elif format_type == OutputFormat.HTML:
            return self._format_html(data, theme, title)
        elif format_type == OutputFormat.MARKDOWN:
            return self._format_markdown(data, title)
        elif format_type == OutputFormat.CSV:
            return self._format_csv(data)
        elif format_type == OutputFormat.MINIMAL:
            return self._format_minimal(data)
        else:
            return self._format_summary(data, theme, title)
    
    def _format_summary(self, data: Dict[str, Any], theme: str, title: str) -> str:
        """Format data as a clean, readable summary."""
        lines = []
        
        # Add title if provided
        if title:
            lines.append(f"{self.colors['bold']}{self.colors['blue']}{title}{self.colors['reset']}")
            lines.append("─" * len(title))
            lines.append("")
        
        # Handle different data types
        if 'success' in data:
            status_icon = self.symbols['check'] if data['success'] else self.symbols['cross']
            status_color = self.colors['green'] if data['success'] else self.colors['red']
            status_text = "Success" if data['success'] else "Failed"
            
            lines.append(f"{status_icon} {status_color}{status_text}{self.colors['reset']}")
            
            if 'message' in data:
                lines.append(f"   {data['message']}")
            lines.append("")
        
        # Project information
        if 'project_id' in data:
            lines.append(f"{self.symbols['folder']} Project ID: {self.colors['cyan']}{data['project_id']}{self.colors['reset']}")
        
        if 'project_name' in data:
            lines.append(f"{self.symbols['folder']} Project: {self.colors['cyan']}{data['project_name']}{self.colors['reset']}")
        
        # File statistics
        if 'files_scanned' in data:
            lines.append(f"{self.symbols['file']} Files scanned: {self.colors['yellow']}{data['files_scanned']:,}{self.colors['reset']}")
        
        if 'files_added' in data:
            lines.append(f"{self.symbols['file']} Files added: {self.colors['green']}{data['files_added']:,}{self.colors['reset']}")
        
        if 'files_updated' in data:
            lines.append(f"{self.symbols['file']} Files updated: {self.colors['blue']}{data['files_updated']:,}{self.colors['reset']}")
        
        if 'total_files' in data:
            lines.append(f"{self.symbols['file']} Total files: {self.colors['yellow']}{data['total_files']:,}{self.colors['reset']}")
        
        # Size information
        if 'total_size_gb' in data:
            lines.append(f"{self.symbols['box']} Total size: {self.colors['magenta']}{data['total_size_gb']:.2f} GB{self.colors['reset']}")
        
        # Time information
        if 'scan_time' in data:
            lines.append(f"{self.symbols['clock']} Scan time: {self.colors['cyan']}{data['scan_time']:.1f}s{self.colors['reset']}")
        
        if 'generated_at' in data:
            timestamp = data['generated_at']
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = timestamp
            else:
                formatted_time = str(timestamp)
            lines.append(f"{self.symbols['clock']} Generated: {self.colors['dim']}{formatted_time}{self.colors['reset']}")
        
        # Directory information
        if 'directories_created' in data:
            lines.append(f"{self.symbols['folder']} Directories created: {self.colors['green']}{data['directories_created']}{self.colors['reset']}")
        
        # Error information
        if 'errors_encountered' in data and data['errors_encountered'] > 0:
            lines.append(f"{self.symbols['warning']} Errors: {self.colors['red']}{data['errors_encountered']}{self.colors['reset']}")
        
        # Performance metrics
        if 'performance' in data:
            perf = data['performance']
            if 'files_per_second' in perf:
                lines.append(f"{self.symbols['lightning']} Speed: {self.colors['yellow']}{perf['files_per_second']:.1f} files/sec{self.colors['reset']}")
        
        # Add spacing if we have content
        if len(lines) > 0:
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_detailed(self, data: Dict[str, Any], theme: str, title: str) -> str:
        """Format data with detailed information and visual elements."""
        lines = []
        
        # Detailed header
        if title:
            lines.append(f"{self.colors['bold']}{self.colors['blue']}")
            lines.append("╔" + "═" * (len(title) + 2) + "╗")
            lines.append(f"║ {title} ║")
            lines.append("╚" + "═" * (len(title) + 2) + "╝")
            lines.append(f"{self.colors['reset']}")
            lines.append("")
        
        # Start with summary
        summary = self._format_summary(data, theme, None)
        lines.append(summary)
        
        # Add detailed sections
        if 'file_types' in data:
            lines.append(f"{self.colors['bold']}📊 File Type Distribution{self.colors['reset']}")
            lines.append("─" * 25)
            
            file_types = data['file_types'][:10]  # Show top 10
            for i, file_type in enumerate(file_types, 1):
                ext = file_type.get('extension', 'Unknown')
                count = file_type.get('count', 0)
                size_mb = file_type.get('total_size_mb', 0)
                
                # Create a simple bar visualization
                max_count = max(ft.get('count', 0) for ft in file_types) if file_types else 1
                bar_length = min(20, int((count / max_count) * 20)) if max_count > 0 else 0
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                lines.append(f"{i:2}. {ext:8} │{bar}│ {count:>6,} files ({size_mb:>8.1f} MB)")
            
            lines.append("")
        
        # Discipline breakdown
        if 'disciplines' in data:
            lines.append(f"{self.colors['bold']}🏗️ Discipline Breakdown{self.colors['reset']}")
            lines.append("─" * 22)
            
            for discipline in data['disciplines']:
                name = discipline.get('discipline', 'Unknown').title()
                count = discipline.get('count', 0)
                lines.append(f"   {self.symbols['bullet']} {name}: {count:,} files")
            
            lines.append("")
        
        # Recent activity
        if 'recent_scans' in data:
            lines.append(f"{self.colors['bold']}⏱️ Recent Activity{self.colors['reset']}")
            lines.append("─" * 17)
            
            for scan in data['recent_scans'][:5]:
                scan_type = scan.get('scan_type', 'Unknown')
                end_time = scan.get('end_time', 'Unknown')
                files_scanned = scan.get('files_scanned', 0)
                status = scan.get('status', 'Unknown')
                
                status_icon = self.symbols['check'] if status == 'completed' else self.symbols['warning']
                lines.append(f"   {status_icon} {scan_type}: {files_scanned:,} files ({end_time})")
            
            lines.append("")
        
        # System health
        if 'database' in data:
            db_info = data['database']
            lines.append(f"{self.colors['bold']}🗄️ Database Status{self.colors['reset']}")
            lines.append("─" * 17)
            
            db_type = db_info.get('type', 'Unknown')
            db_status = db_info.get('status', 'Unknown')
            status_color = self.colors['green'] if db_status == 'healthy' else self.colors['yellow']
            
            lines.append(f"   Type: {db_type}")
            lines.append(f"   Status: {status_color}{db_status}{self.colors['reset']}")
            
            if 'table_counts' in db_info:
                table_counts = db_info['table_counts']
                total_records = sum(table_counts.values()) if table_counts else 0
                lines.append(f"   Total records: {total_records:,}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format data as pretty JSON."""
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    
    def _format_html(self, data: Dict[str, Any], theme: str, title: str) -> str:
        """Format data as HTML with modern styling."""
        theme_config = self.themes.get(theme, self.themes['default'])
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title or 'AEC Scanner Report')}</title>
    <style>
        :root {{
            --primary-color: {theme_config.primary_color};
            --secondary-color: {theme_config.secondary_color};
            --success-color: {theme_config.success_color};
            --warning-color: {theme_config.warning_color};
            --error-color: {theme_config.error_color};
            --info-color: {theme_config.info_color};
            --accent-color: {theme_config.accent_color};
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        .status-card {{
            display: flex;
            align-items: center;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            font-weight: 500;
        }}
        
        .status-success {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid var(--success-color);
            color: var(--success-color);
        }}
        
        .status-error {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid var(--error-color);
            color: var(--error-color);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: #f8fafc;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #64748b;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .section {{
            margin: 2rem 0;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent-color);
        }}
        
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .table th,
        .table td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .table th {{
            background: var(--primary-color);
            color: white;
            font-weight: 600;
        }}
        
        .table tr:hover {{
            background: #f8fafc;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--success-color), var(--info-color));
            transition: width 0.3s ease;
        }}
        
        .footer {{
            background: #f8fafc;
            padding: 1.5rem;
            text-align: center;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge-success {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--success-color);
        }}
        
        .badge-info {{
            background: rgba(59, 130, 246, 0.1);
            color: var(--info-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ {html.escape(title or 'AEC Scanner Report')}</h1>
            <div class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>
        
        <div class="content">
        """
        
        # Status section
        if 'success' in data:
            status_class = 'status-success' if data['success'] else 'status-error'
            status_icon = '✅' if data['success'] else '❌'
            status_text = 'Operation Successful' if data['success'] else 'Operation Failed'
            
            html_content += f"""
            <div class="status-card {status_class}">
                <span style="font-size: 1.5rem; margin-right: 1rem;">{status_icon}</span>
                <div>
                    <div style="font-size: 1.2rem;">{status_text}</div>
                    {f'<div style="opacity: 0.8; margin-top: 0.25rem;">{html.escape(data["message"])}</div>' if data.get('message') else ''}
                </div>
            </div>
            """
        
        # Statistics grid
        stats = []
        if 'total_files' in data:
            stats.append(('Total Files', f"{data['total_files']:,}"))
        if 'files_scanned' in data:
            stats.append(('Files Scanned', f"{data['files_scanned']:,}"))
        if 'total_size_gb' in data:
            stats.append(('Total Size', f"{data['total_size_gb']:.2f} GB"))
        if 'scan_time' in data:
            stats.append(('Scan Time', f"{data['scan_time']:.1f}s"))
        
        if stats:
            html_content += '<div class="stats-grid">'
            for label, value in stats:
                html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{value}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """
            html_content += '</div>'
        
        # File types table
        if 'file_types' in data and data['file_types']:
            html_content += """
            <div class="section">
                <h2 class="section-title">📊 File Type Distribution</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>File Type</th>
                            <th>Count</th>
                            <th>Size (MB)</th>
                            <th>Distribution</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            total_files = sum(ft.get('count', 0) for ft in data['file_types'])
            for file_type in data['file_types'][:15]:  # Top 15
                ext = file_type.get('extension', 'Unknown')
                count = file_type.get('count', 0)
                size_mb = file_type.get('total_size_mb', 0)
                percentage = (count / total_files * 100) if total_files > 0 else 0
                
                html_content += f"""
                        <tr>
                            <td><code>{html.escape(ext)}</code></td>
                            <td>{count:,}</td>
                            <td>{size_mb:.1f}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {percentage:.1f}%"></div>
                                </div>
                                <small>{percentage:.1f}%</small>
                            </td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            </div>
            """
        
        html_content += """
        </div>
        
        <div class="footer">
            <p>Generated by <strong>AEC Directory Scanner</strong> • 
               <span class="badge badge-success">Optimized & Streamlined</span>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _format_markdown(self, data: Dict[str, Any], title: str) -> str:
        """Format data as Markdown."""
        lines = []
        
        # Title
        if title:
            lines.append(f"# {title}")
            lines.append("")
        
        # Status
        if 'success' in data:
            status_icon = "✅" if data['success'] else "❌"
            status_text = "Success" if data['success'] else "Failed"
            lines.append(f"{status_icon} **Status:** {status_text}")
            
            if 'message' in data:
                lines.append(f"**Message:** {data['message']}")
            lines.append("")
        
        # Summary statistics
        if any(key in data for key in ['total_files', 'files_scanned', 'total_size_gb']):
            lines.append("## 📊 Summary")
            lines.append("")
            
            if 'total_files' in data:
                lines.append(f"- **Total Files:** {data['total_files']:,}")
            if 'files_scanned' in data:
                lines.append(f"- **Files Scanned:** {data['files_scanned']:,}")
            if 'total_size_gb' in data:
                lines.append(f"- **Total Size:** {data['total_size_gb']:.2f} GB")
            if 'scan_time' in data:
                lines.append(f"- **Scan Time:** {data['scan_time']:.1f} seconds")
            
            lines.append("")
        
        # File types
        if 'file_types' in data and data['file_types']:
            lines.append("## 📁 File Types")
            lines.append("")
            lines.append("| File Type | Count | Size (MB) |")
            lines.append("|-----------|-------|-----------|")
            
            for file_type in data['file_types'][:10]:
                ext = file_type.get('extension', 'Unknown')
                count = file_type.get('count', 0)
                size_mb = file_type.get('total_size_mb', 0)
                lines.append(f"| `{ext}` | {count:,} | {size_mb:.1f} |")
            
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Generated by AEC Directory Scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)
    
    def _format_csv(self, data: Dict[str, Any]) -> str:
        """Format data as CSV (simplified)."""
        if 'file_types' in data and data['file_types']:
            lines = ["File Type,Count,Size (MB)"]
            for file_type in data['file_types']:
                ext = file_type.get('extension', 'Unknown')
                count = file_type.get('count', 0)
                size_mb = file_type.get('total_size_mb', 0)
                lines.append(f'"{ext}",{count},{size_mb:.1f}')
            return '\n'.join(lines)
        else:
            # Flatten data for CSV
            lines = ["Key,Value"]
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    lines.append(f'"{key}","{value}"')
            return '\n'.join(lines)
    
    def _format_minimal(self, data: Dict[str, Any]) -> str:
        """Format data with minimal output."""
        if 'success' in data:
            if data['success']:
                message = data.get('message', 'OK')
                return f"✅ {message}"
            else:
                message = data.get('message', 'FAILED')
                return f"❌ {message}"
        
        # Extract key information
        key_info = []
        if 'total_files' in data:
            key_info.append(f"{data['total_files']:,} files")
        if 'total_size_gb' in data:
            key_info.append(f"{data['total_size_gb']:.1f}GB")
        if 'scan_time' in data:
            key_info.append(f"{data['scan_time']:.1f}s")
        
        return " | ".join(key_info) if key_info else str(data)
    
    def create_progress_summary(
        self, 
        current: int, 
        total: int, 
        operation: str = "Processing",
        additional_info: Dict[str, Any] = None
    ) -> str:
        """Create a formatted progress summary."""
        percentage = (current / total * 100) if total > 0 else 0
        
        # Progress bar
        bar_length = 40
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        summary = f"{self.colors['blue']}{operation}{self.colors['reset']}: {bar} {percentage:.1f}% ({current:,}/{total:,})"
        
        if additional_info:
            info_parts = []
            if 'speed' in additional_info:
                info_parts.append(f"{additional_info['speed']:.1f}/s")
            if 'eta' in additional_info:
                info_parts.append(f"ETA: {additional_info['eta']}")
            if 'errors' in additional_info and additional_info['errors'] > 0:
                info_parts.append(f"{self.colors['red']}{additional_info['errors']} errors{self.colors['reset']}")
            
            if info_parts:
                summary += f" [{', '.join(info_parts)}]"
        
        return summary


# Global formatter instance
_global_formatter = None

def get_formatter(default_format: OutputFormat = OutputFormat.SUMMARY) -> OutputFormatter:
    """Get global output formatter instance."""
    global _global_formatter
    if _global_formatter is None:
        _global_formatter = OutputFormatter(default_format)
    return _global_formatter

def format_data(
    data: Dict[str, Any], 
    format_type: OutputFormat = OutputFormat.SUMMARY,
    title: str = None
) -> str:
    """Quick function to format data."""
    formatter = get_formatter()
    return formatter.format_output(data, format_type, title=title)