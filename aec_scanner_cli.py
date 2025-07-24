#!/usr/bin/env python3
"""
AEC Directory Scanner - Command Line Interface

Comprehensive command-line interface for the AEC Directory Scanner system
with support for all major operations including project initialization,
scanning, metadata extraction, reporting, and system management.
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aec_scanner import AECDirectoryScanner
from aec_scanner.utils.config_manager import ConfigManager
from aec_scanner.utils.error_handler import ErrorHandler


def setup_logging(config: ConfigManager) -> logging.Logger:
    """
    Set up logging configuration based on config settings.
    
    Args:
        config: Configuration manager instance
        
    Returns:
        Configured logger instance
    """
    log_config = config.get_logging_config()
    
    # Create log directory if it doesn't exist
    log_file = Path(log_config.get('file_path', 'logs/scanner.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO').upper()),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('aec_scanner_cli')
    return logger


def progress_callback(current: int, total: int) -> None:
    """Progress callback for long-running operations."""
    if total > 0:
        percent = (current / total) * 100
        print(f"\rProgress: {current}/{total} ({percent:.1f}%)", end='', flush=True)
        if current == total:
            print()  # New line when complete


def format_output(data: dict, format_type: str = 'json') -> str:
    """
    Format output data for display.
    
    Args:
        data: Data to format
        format_type: Output format ('json', 'table', 'summary')
        
    Returns:
        Formatted string
    """
    if format_type == 'json':
        return json.dumps(data, indent=2, default=str)
    
    elif format_type == 'summary':
        if not data.get('success', False):
            return f"Error: {data.get('message', 'Unknown error')}"
        
        # Extract key information for summary
        summary_lines = []
        
        if 'project_id' in data:
            summary_lines.append(f"Project ID: {data['project_id']}")
        
        if 'files_scanned' in data:
            summary_lines.append(f"Files scanned: {data['files_scanned']}")
        
        if 'files_added' in data:
            summary_lines.append(f"Files added: {data['files_added']}")
        
        if 'files_updated' in data:
            summary_lines.append(f"Files updated: {data['files_updated']}")
        
        if 'scan_time' in data:
            summary_lines.append(f"Scan time: {data['scan_time']:.2f}s")
        
        if 'message' in data:
            summary_lines.append(f"Status: {data['message']}")
        
        return '\n'.join(summary_lines) if summary_lines else str(data)
    
    else:  # table format - simplified
        return json.dumps(data, indent=2, default=str)


def cmd_init(args, scanner: AECDirectoryScanner) -> int:
    """Initialize a new project."""
    print(f"Initializing project: {args.project_number} - {args.project_name}")
    
    result = scanner.initialize_project(
        args.project_number,
        args.project_name,
        args.path
    )
    
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_scan(args, scanner: AECDirectoryScanner) -> int:
    """Scan a project directory."""
    print(f"Starting {args.type} scan of project {args.project_id}")
    
    callback = progress_callback if args.verbose else None
    
    result = scanner.scan_project(
        args.project_id,
        args.type,
        progress_callback=callback
    )
    
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_extract(args, scanner: AECDirectoryScanner) -> int:
    """Extract metadata from project files."""
    print(f"Extracting metadata for project {args.project_id}")
    
    callback = progress_callback if args.verbose else None
    
    result = scanner.extract_all_metadata(
        args.project_id,
        args.force_refresh,
        progress_callback=callback
    )
    
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_report(args, scanner: AECDirectoryScanner) -> int:
    """Generate project report."""
    print(f"Generating report for project {args.project_id}")
    
    result = scanner.generate_project_report(args.project_id)
    
    if args.output:
        # Save report to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if args.format == 'json':
                json.dump(result, f, indent=2, default=str)
            else:
                f.write(format_output(result, args.format))
        
        print(f"Report saved to: {output_path}")
    else:
        print(format_output(result, args.format))
    
    return 0 if result['success'] else 1


def cmd_validate(args, scanner: AECDirectoryScanner) -> int:
    """Validate project integrity."""
    print(f"Validating project {args.project_id}")
    
    result = scanner.validate_project_integrity(args.project_id)
    
    if args.repair_missing and not result.get('directory_structure', {}).get('valid', True):
        print("Repairing missing directories...")
        # Get project path and repair
        project_path = result.get('project_path')
        if project_path:
            repaired = scanner.directory_manager.repair_structure(project_path)
            if repaired:
                print(f"Repaired {len(repaired)} missing directories")
                # Re-validate after repair
                result = scanner.validate_project_integrity(args.project_id)
    
    print(format_output(result, args.format))
    return 0 if result.get('overall_status') == 'healthy' else 1


def cmd_db(args, scanner: AECDirectoryScanner) -> int:
    """Database management operations."""
    if args.action == 'backup':
        print(f"Creating database backup: {args.output}")
        success = scanner.database.backup_database(args.output)
        result = {
            'success': success,
            'message': f"Backup {'completed' if success else 'failed'}",
            'backup_path': args.output if success else None
        }
        
    elif args.action == 'migrate':
        print(f"Migrating database to version: {args.target_version}")
        success = scanner.database.migrate_schema(args.target_version)
        result = {
            'success': success,
            'message': f"Migration {'completed' if success else 'failed'}",
            'target_version': args.target_version
        }
        
    elif args.action == 'info':
        print("Getting database information...")
        result = scanner.database.get_database_info()
        result['success'] = 'error' not in result
        
    else:
        result = {
            'success': False,
            'message': f"Unknown database action: {args.action}"
        }
    
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_monitor(args, scanner: AECDirectoryScanner) -> int:
    """Monitor file system changes."""
    # Get project path
    with scanner.database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT base_path FROM projects WHERE id = ?", (args.project_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"Project {args.project_id} not found")
            return 1
        
        project_path = result[0]
    
    print(f"Monitoring project {args.project_id} at {project_path}")
    print(f"Check interval: {args.watch_interval} seconds")
    print("Press Ctrl+C to stop monitoring")
    
    def change_callback(changes):
        if changes:
            print(f"\n{datetime.now()}: Detected {len(changes)} file changes")
            for change in changes[:5]:  # Show first 5 changes
                print(f"  - {change.file_path}")
            if len(changes) > 5:
                print(f"  ... and {len(changes) - 5} more")
    
    try:
        scanner.file_scanner.monitor_changes(
            project_path,
            change_callback,
            args.watch_interval
        )
        
        # Keep the script running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping file system monitoring...")
        scanner.file_scanner.stop_monitoring()
        return 0


def cmd_export(args, scanner: AECDirectoryScanner) -> int:
    """Export project data."""
    print(f"Exporting project {args.project_id} data")
    
    # Get project files and metadata
    files = scanner.database.get_files_by_project(args.project_id)
    project_stats = scanner.database.get_project_statistics(args.project_id)
    
    export_data = {
        'export_info': {
            'project_id': args.project_id,
            'exported_at': datetime.now().isoformat(),
            'format': args.format,
            'total_files': len(files)
        },
        'project_statistics': project_stats,
        'files': files
    }
    
    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            if args.format == 'json':
                json.dump(export_data, f, indent=2, default=str)
            else:
                # CSV export would require pandas or csv module
                json.dump(export_data, f, indent=2, default=str)
        
        result = {
            'success': True,
            'message': f"Data exported successfully to {output_path}",
            'output_path': str(output_path),
            'records_exported': len(files)
        }
        
    except Exception as e:
        result = {
            'success': False,
            'message': f"Export failed: {str(e)}"
        }
    
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_status(args, scanner: AECDirectoryScanner) -> int:
    """Get system status."""
    print("Getting system status...")
    
    result = scanner.get_system_status()
    print(format_output(result, args.format))
    return 0 if result['success'] else 1


def cmd_config(args, scanner: AECDirectoryScanner) -> int:
    """Configuration management."""
    if args.action == 'show':
        config_data = {
            'success': True,
            'configuration': scanner.config.get_all_config()
        }
        
    elif args.action == 'sample':
        output_path = args.output or 'config/aec_scanner_config.yaml'
        success = scanner.config.create_sample_config(output_path)
        config_data = {
            'success': success,
            'message': f"Sample configuration {'created' if success else 'creation failed'}",
            'output_path': output_path if success else None
        }
        
    elif args.action == 'validate':
        valid_patterns = scanner.config.validate_file_naming_patterns()
        config_data = {
            'success': valid_patterns,
            'message': f"Configuration {'is valid' if valid_patterns else 'has invalid patterns'}",
            'environment_variables': scanner.config.get_environment_info()
        }
        
    else:
        config_data = {
            'success': False,
            'message': f"Unknown config action: {args.action}"
        }
    
    print(format_output(config_data, args.format))
    return 0 if config_data['success'] else 1


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='AEC Directory Scanner - Comprehensive file scanning and metadata extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize new project
  aec-scanner init --project-number PROJ2024 --project-name "Office Building" --path "/projects/office_building"
  
  # Full project scan
  aec-scanner scan --project-id 1 --type full --verbose
  
  # Extract metadata
  aec-scanner extract --project-id 1 --force-refresh
  
  # Generate report
  aec-scanner report --project-id 1 --format html --output reports/project_report.html
  
  # Validate project
  aec-scanner validate --project-id 1 --repair-missing
        """
    )
    
    # Global options
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--format', choices=['json', 'summary', 'table'], default='summary',
                       help='Output format (default: summary)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize project
    init_parser = subparsers.add_parser('init', help='Initialize new project')
    init_parser.add_argument('--project-number', required=True, help='Project number')
    init_parser.add_argument('--project-name', required=True, help='Project name')
    init_parser.add_argument('--path', required=True, help='Base path for project')
    
    # Scan project
    scan_parser = subparsers.add_parser('scan', help='Scan project directory')
    scan_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    scan_parser.add_argument('--type', choices=['full', 'incremental', 'validation'], 
                            default='full', help='Scan type')
    
    # Extract metadata
    extract_parser = subparsers.add_parser('extract', help='Extract metadata from files')
    extract_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    extract_parser.add_argument('--force-refresh', action='store_true', 
                               help='Re-extract metadata for all files')
    
    # Generate report
    report_parser = subparsers.add_parser('report', help='Generate project report')
    report_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    report_parser.add_argument('--output', type=str, help='Output file path')
    
    # Validate project
    validate_parser = subparsers.add_parser('validate', help='Validate project integrity')
    validate_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    validate_parser.add_argument('--repair-missing', action='store_true', 
                                help='Repair missing directories')
    
    # Database management
    db_parser = subparsers.add_parser('db', help='Database management')
    db_parser.add_argument('--action', choices=['backup', 'migrate', 'info'], 
                          required=True, help='Database action')
    db_parser.add_argument('--output', type=str, help='Output file path (for backup)')
    db_parser.add_argument('--target-version', type=str, help='Target version (for migrate)')
    
    # Monitor changes
    monitor_parser = subparsers.add_parser('monitor', help='Monitor file system changes')
    monitor_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    monitor_parser.add_argument('--watch-interval', type=int, default=30, 
                               help='Watch interval in seconds')
    
    # Export data
    export_parser = subparsers.add_parser('export', help='Export project data')
    export_parser.add_argument('--project-id', type=int, required=True, help='Project ID')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', 
                              help='Export format')
    export_parser.add_argument('--output', type=str, required=True, help='Output file path')
    
    # System status
    status_parser = subparsers.add_parser('status', help='Get system status')
    
    # Configuration management
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--action', choices=['show', 'sample', 'validate'], 
                              required=True, help='Configuration action')
    config_parser.add_argument('--output', type=str, help='Output file path')
    
    return parser


def main() -> int:
    """Main entry point for the CLI application."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize configuration
        config = ConfigManager(args.config)
        
        # Setup logging
        logger = setup_logging(config)
        
        # Initialize scanner
        logger.info("Initializing AEC Directory Scanner")
        scanner = AECDirectoryScanner(args.config)
        
        # Execute command
        command_map = {
            'init': cmd_init,
            'scan': cmd_scan,
            'extract': cmd_extract,
            'report': cmd_report,
            'validate': cmd_validate,
            'db': cmd_db,
            'monitor': cmd_monitor,
            'export': cmd_export,
            'status': cmd_status,
            'config': cmd_config
        }
        
        if args.command in command_map:
            return command_map[args.command](args, scanner)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        # Cleanup
        try:
            if 'scanner' in locals():
                scanner.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main())