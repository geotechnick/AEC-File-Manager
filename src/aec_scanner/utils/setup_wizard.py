"""
Interactive Setup Wizard

User-friendly interactive wizard for first-time setup and configuration
with smart suggestions and validation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json

from .smart_defaults import SmartDefaults


class SetupWizard:
    """
    Interactive setup wizard that guides users through initial configuration
    with intelligent suggestions and validation.
    """
    
    def __init__(self):
        self.smart_defaults = SmartDefaults()
        self.config = {}
        
        # Color codes for terminal output
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m', 
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'reset': '\033[0m'
        }
    
    def run_wizard(self) -> Dict[str, Any]:
        """
        Run the complete setup wizard.
        
        Returns:
            Configuration dictionary
        """
        self._show_welcome()
        
        try:
            # Step 1: Project detection and setup
            project_config = self._setup_project()
            
            # Step 2: Scan preferences
            scan_config = self._setup_scan_preferences()
            
            # Step 3: Output preferences  
            output_config = self._setup_output_preferences()
            
            # Step 4: Advanced options (optional)
            advanced_config = self._setup_advanced_options()
            
            # Combine all configurations
            self.config = {
                'project': project_config,
                'scanning': scan_config,
                'output': output_config,
                'advanced': advanced_config,
                'wizard_completed': True,
                'wizard_version': '1.0',
                'created_at': datetime.now().isoformat()
            }
            
            # Step 5: Summary and confirmation
            if self._show_summary():
                self._save_configuration()
                self._show_completion()
                return self.config
            else:
                print(f"{self.colors['yellow']}Setup cancelled by user.{self.colors['reset']}")
                return {}
                
        except KeyboardInterrupt:
            print(f"\n{self.colors['yellow']}Setup wizard interrupted. You can run it again anytime.{self.colors['reset']}")
            return {}
        except Exception as e:
            print(f"\n{self.colors['red']}Error during setup: {e}{self.colors['reset']}")
            return {}
    
    def _show_welcome(self) -> None:
        """Show welcome message and introduction."""
        print(f"""
{self.colors['bold']}{self.colors['blue']}
╔═══════════════════════════════════════════════╗
║           🏗️  AEC Scanner Setup Wizard        ║  
║                                               ║
║     Welcome! Let's get you set up quickly    ║
║     with intelligent defaults and guidance   ║
╚═══════════════════════════════════════════════╝
{self.colors['reset']}

This wizard will help you:
  ✅ Detect and configure your AEC project
  ✅ Set up scanning preferences  
  ✅ Configure output options
  ✅ Optimize for your workflow

{self.colors['green']}💡 Tip: Press Enter to accept suggested defaults (shown in brackets){self.colors['reset']}
""")
        
        input("Press Enter to continue...")
        print()
    
    def _setup_project(self) -> Dict[str, Any]:
        """Setup project configuration."""
        print(f"{self.colors['bold']}📋 Step 1: Project Configuration{self.colors['reset']}")
        print()
        
        # Detect current directory
        current_dir = os.getcwd()
        print(f"Current directory: {self.colors['blue']}{current_dir}{self.colors['reset']}")
        
        # Auto-detect project info
        detected = self.smart_defaults.detect_project_info(current_dir)
        confidence = detected.get('confidence_score', 0)
        
        if confidence > 0.5:
            print(f"{self.colors['green']}✅ Auto-detected project settings (confidence: {confidence:.1%}){self.colors['reset']}")
            print(f"   Project: {detected['project_name']}")
            print(f"   Number: {detected['project_number']}")
            print(f"   Year: {detected['project_year']}")
            print()
            
            use_detected = self._ask_yes_no("Use auto-detected settings?", default=True)
            if use_detected:
                return {
                    'path': current_dir,
                    'project_number': detected['project_number'],
                    'project_name': detected['project_name'],
                    'project_year': detected['project_year'],
                    'auto_detected': True
                }
        
        # Manual configuration
        print(f"{self.colors['yellow']}⚙️  Manual project configuration{self.colors['reset']}")
        
        # Project path
        default_path = current_dir
        project_path = self._ask_input(
            "Project directory path",
            default=default_path,
            validator=self._validate_path
        )
        
        # Re-detect with chosen path if different
        if project_path != current_dir:
            detected = self.smart_defaults.detect_project_info(project_path)
        
        # Project number
        project_number = self._ask_input(
            "Project number/code",
            default=detected.get('project_number') or f"PROJ{datetime.now().year}",
            validator=self._validate_project_number
        )
        
        # Project name
        project_name = self._ask_input(
            "Project name",
            default=detected.get('project_name') or "AEC Project",
            validator=self._validate_project_name
        )
        
        # Project year
        project_year = self._ask_input(
            "Project year",
            default=str(detected.get('project_year') or datetime.now().year),
            validator=self._validate_year
        )
        
        return {
            'path': project_path,
            'project_number': project_number,
            'project_name': project_name,
            'project_year': int(project_year),
            'auto_detected': False
        }
    
    def _setup_scan_preferences(self) -> Dict[str, Any]:
        """Setup scanning preferences."""
        print(f"\n{self.colors['bold']}🔍 Step 2: Scanning Preferences{self.colors['reset']}")
        print()
        
        # Auto-configure based on project
        project_path = self.config.get('project', {}).get('path', os.getcwd())
        auto_config = self.smart_defaults.auto_configure_scan_settings(project_path)
        
        print(f"Auto-detected scan settings for your project:")
        print(f"  • Estimated files: ~{auto_config.get('estimated_files', 'unknown')}")
        print(f"  • Recommended batch size: {auto_config.get('batch_size', 50)}")
        print(f"  • Estimated scan time: {auto_config.get('estimated_duration_minutes', 1):.1f} minutes")
        print()
        
        use_auto = self._ask_yes_no("Use recommended scan settings?", default=True)
        if use_auto:
            return {
                'use_async': auto_config.get('async_processing', True),
                'batch_size': auto_config.get('batch_size', 50),
                'max_concurrent': auto_config.get('max_concurrent', 5),
                'enable_hashing': auto_config.get('enable_hashing', True),
                'include_hidden': False,
                'max_file_size_mb': 100,
                'auto_optimized': True
            }
        
        # Manual configuration
        print(f"{self.colors['yellow']}⚙️  Custom scan configuration{self.colors['reset']}")
        
        # Performance mode
        performance_modes = {
            '1': ('Fast', 'Quick scan, minimal metadata'),
            '2': ('Balanced', 'Good speed with essential metadata'),
            '3': ('Thorough', 'Complete scan with full metadata'),
            '4': ('Custom', 'Configure individual settings')
        }
        
        print("Performance mode:")
        for key, (name, desc) in performance_modes.items():
            print(f"  {key}. {name} - {desc}")
        
        mode = self._ask_choice("Select mode", list(performance_modes.keys()), default='2')
        
        if mode == '1':  # Fast
            return {
                'use_async': True,
                'batch_size': 100,
                'max_concurrent': 10,
                'enable_hashing': False,
                'include_hidden': False,
                'max_file_size_mb': 50,
                'performance_mode': 'fast'
            }
        elif mode == '2':  # Balanced
            return {
                'use_async': True,
                'batch_size': 50,
                'max_concurrent': 5,
                'enable_hashing': True,
                'include_hidden': False,
                'max_file_size_mb': 100,
                'performance_mode': 'balanced'
            }
        elif mode == '3':  # Thorough
            return {
                'use_async': True,
                'batch_size': 25,
                'max_concurrent': 3,
                'enable_hashing': True,
                'include_hidden': True,
                'max_file_size_mb': 500,
                'performance_mode': 'thorough'
            }
        else:  # Custom
            return self._setup_custom_scan_settings()
    
    def _setup_custom_scan_settings(self) -> Dict[str, Any]:
        """Setup custom scan settings."""
        print(f"\n{self.colors['blue']}Custom scan settings:{self.colors['reset']}")
        
        batch_size = int(self._ask_input(
            "Batch size (files processed at once)",
            default="50",
            validator=lambda x: x.isdigit() and 1 <= int(x) <= 500
        ))
        
        max_concurrent = int(self._ask_input(
            "Max concurrent operations",
            default="5", 
            validator=lambda x: x.isdigit() and 1 <= int(x) <= 20
        ))
        
        enable_hashing = self._ask_yes_no("Generate file hashes?", default=True)
        include_hidden = self._ask_yes_no("Include hidden files?", default=False)
        
        max_file_size = int(self._ask_input(
            "Maximum file size to process (MB)",
            default="100",
            validator=lambda x: x.isdigit() and 1 <= int(x) <= 5000
        ))
        
        return {
            'use_async': True,
            'batch_size': batch_size,
            'max_concurrent': max_concurrent,
            'enable_hashing': enable_hashing,
            'include_hidden': include_hidden,
            'max_file_size_mb': max_file_size,
            'performance_mode': 'custom'
        }
    
    def _setup_output_preferences(self) -> Dict[str, Any]:
        """Setup output preferences."""
        print(f"\n{self.colors['bold']}📊 Step 3: Output Preferences{self.colors['reset']}")
        print()
        
        # Default format
        formats = {
            '1': ('Summary', 'Clean, easy-to-read summaries'),
            '2': ('Detailed', 'Comprehensive information with progress bars'),
            '3': ('JSON', 'Machine-readable structured data'),
            '4': ('Minimal', 'Essential information only')
        }
        
        print("Default output format:")
        for key, (name, desc) in formats.items():
            print(f"  {key}. {name} - {desc}")
        
        format_choice = self._ask_choice("Select format", list(formats.keys()), default='1')
        format_map = {'1': 'summary', '2': 'detailed', '3': 'json', '4': 'minimal'}
        
        # Progress display
        show_progress = self._ask_yes_no("Show progress bars during operations?", default=True)
        
        # Error handling
        verbose_errors = self._ask_yes_no("Show detailed error information?", default=False)
        
        # Auto-open reports
        auto_open_reports = self._ask_yes_no("Automatically open HTML reports in browser?", default=True)
        
        return {
            'default_format': format_map[format_choice],
            'show_progress': show_progress,
            'verbose_errors': verbose_errors,
            'auto_open_reports': auto_open_reports,
            'use_colors': True
        }
    
    def _setup_advanced_options(self) -> Dict[str, Any]:
        """Setup advanced options."""
        print(f"\n{self.colors['bold']}⚙️  Step 4: Advanced Options (Optional){self.colors['reset']}")
        print()
        
        setup_advanced = self._ask_yes_no("Configure advanced options?", default=False)
        if not setup_advanced:
            return {'use_defaults': True}
        
        # Database preferences
        print(f"\n{self.colors['blue']}Database settings:{self.colors['reset']}")
        
        use_connection_pooling = self._ask_yes_no("Enable database connection pooling?", default=True)
        enable_query_caching = self._ask_yes_no("Enable query caching?", default=True)
        
        # Memory management
        print(f"\n{self.colors['blue']}Memory management:{self.colors['reset']}")
        
        memory_limit = int(self._ask_input(
            "Memory limit (MB)",
            default="512",
            validator=lambda x: x.isdigit() and 64 <= int(x) <= 8192
        ))
        
        enable_memory_monitoring = self._ask_yes_no("Enable memory monitoring?", default=True)
        
        # Backup settings
        print(f"\n{self.colors['blue']}Backup settings:{self.colors['reset']}")
        
        auto_backup = self._ask_yes_no("Enable automatic database backups?", default=True)
        backup_frequency = 'daily'
        
        if auto_backup:
            freq_options = {
                '1': 'hourly',
                '2': 'daily', 
                '3': 'weekly',
                '4': 'manual'
            }
            print("Backup frequency:")
            for key, freq in freq_options.items():
                print(f"  {key}. {freq.capitalize()}")
            
            freq_choice = self._ask_choice("Select frequency", list(freq_options.keys()), default='2')
            backup_frequency = freq_options[freq_choice]
        
        return {
            'database': {
                'use_connection_pooling': use_connection_pooling,
                'enable_query_caching': enable_query_caching
            },
            'memory': {
                'limit_mb': memory_limit,
                'enable_monitoring': enable_memory_monitoring
            },
            'backup': {
                'auto_backup': auto_backup,
                'frequency': backup_frequency
            },
            'use_defaults': False
        }
    
    def _show_summary(self) -> bool:
        """Show configuration summary and ask for confirmation."""
        print(f"\n{self.colors['bold']}📋 Configuration Summary{self.colors['reset']}")
        print("=" * 50)
        
        # Project summary
        project = self.config['project']
        print(f"\n{self.colors['green']}Project:{self.colors['reset']}")
        print(f"  Name: {project['project_name']}")
        print(f"  Number: {project['project_number']}")
        print(f"  Year: {project['project_year']}")
        print(f"  Path: {project['path']}")
        
        # Scanning summary
        scanning = self.config['scanning']
        print(f"\n{self.colors['blue']}Scanning:{self.colors['reset']}")
        if 'performance_mode' in scanning:
            print(f"  Mode: {scanning['performance_mode'].title()}")
        print(f"  Batch size: {scanning['batch_size']}")
        print(f"  Concurrent ops: {scanning['max_concurrent']}")
        print(f"  File hashing: {'Enabled' if scanning['enable_hashing'] else 'Disabled'}")
        
        # Output summary
        output = self.config['output']
        print(f"\n{self.colors['yellow']}Output:{self.colors['reset']}")
        print(f"  Format: {output['default_format'].title()}")
        print(f"  Progress bars: {'Enabled' if output['show_progress'] else 'Disabled'}")
        print(f"  Auto-open reports: {'Enabled' if output['auto_open_reports'] else 'Disabled'}")
        
        print("\n" + "=" * 50)
        
        return self._ask_yes_no(f"\n{self.colors['bold']}Save this configuration?{self.colors['reset']}", default=True)
    
    def _save_configuration(self) -> None:
        """Save configuration to file."""
        config_dir = Path.home() / '.aec_scanner'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'wizard_config.json'
        
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"\n{self.colors['green']}✅ Configuration saved to: {config_file}{self.colors['reset']}")
    
    def _show_completion(self) -> None:
        """Show completion message with next steps."""
        print(f"""
{self.colors['bold']}{self.colors['green']}
╔═══════════════════════════════════════════════╗
║          🎉 Setup Complete! 🎉                ║
║                                               ║
║     Your AEC Scanner is ready to use!        ║
╚═══════════════════════════════════════════════╝
{self.colors['reset']}

{self.colors['bold']}Next steps:{self.colors['reset']}

1. 🔍 Run your first scan:
   {self.colors['blue']}aec scan{self.colors['reset']}

2. 📊 Generate a report:
   {self.colors['blue']}aec report{self.colors['reset']}

3. 📋 Check status anytime:
   {self.colors['blue']}aec status{self.colors['reset']}

{self.colors['green']}💡 Tip: All commands now use your saved preferences!{self.colors['reset']}

{self.colors['yellow']}Need help? Run 'aec --help' for more options.{self.colors['reset']}
""")
    
    def _ask_input(self, prompt: str, default: str = "", validator=None) -> str:
        """Ask for user input with validation."""
        while True:
            if default:
                full_prompt = f"{prompt} [{default}]: "
            else:
                full_prompt = f"{prompt}: "
            
            response = input(full_prompt).strip()
            
            if not response and default:
                response = default
            
            if not response:
                print(f"{self.colors['red']}Please provide a value.{self.colors['reset']}")
                continue
            
            if validator and not validator(response):
                print(f"{self.colors['red']}Invalid input. Please try again.{self.colors['reset']}")
                continue
            
            return response
    
    def _ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Ask for yes/no input."""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def _ask_choice(self, prompt: str, choices: List[str], default: str = "") -> str:
        """Ask for choice from list."""
        while True:
            if default:
                response = input(f"{prompt} [{default}]: ").strip()
            else:
                response = input(f"{prompt}: ").strip()
            
            if not response and default:
                response = default
            
            if response in choices:
                return response
            
            print(f"{self.colors['red']}Please choose from: {', '.join(choices)}{self.colors['reset']}")
    
    def _validate_path(self, path: str) -> bool:
        """Validate directory path."""
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_dir()
    
    def _validate_project_number(self, number: str) -> bool:
        """Validate project number."""
        return len(number.strip()) >= 3 and not number.isspace()
    
    def _validate_project_name(self, name: str) -> bool:
        """Validate project name."""
        return len(name.strip()) >= 2 and not name.isspace()
    
    def _validate_year(self, year: str) -> bool:
        """Validate year."""
        try:
            y = int(year)
            return 2020 <= y <= datetime.now().year + 10
        except ValueError:
            return False


def run_setup_wizard() -> Dict[str, Any]:
    """
    Run the interactive setup wizard.
    
    Returns:
        Configuration dictionary
    """
    wizard = SetupWizard()
    return wizard.run_wizard()