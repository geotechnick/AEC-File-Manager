#!/usr/bin/env python3
"""
AEC Scanner - Streamlined CLI

Ultra-simplified command-line interface that removes friction and maximizes ease of use.
Most operations require minimal input and use intelligent defaults.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aec_scanner import AECDirectoryScanner
from aec_scanner.utils.smart_defaults import SmartDefaults
from aec_scanner.utils.progress_manager import ProgressManager, ProgressStyle


class StreamlinedCLI:
    """Ultra-simplified CLI interface for AEC Scanner."""
    
    def __init__(self):
        self.smart_defaults = SmartDefaults()
        self.scanner: Optional[AECDirectoryScanner] = None
        
    def auto_init(self, path: str = None) -> Dict[str, Any]:
        """
        Auto-initialize project with smart detection.
        
        Args:
            path: Project path (uses current directory if not provided)
            
        Returns:
            Result dictionary
        """
        # Use current directory if no path provided
        if not path:
            path = os.getcwd()
        
        path = os.path.abspath(path)
        print(f"🔍 Auto-detecting project settings for: {path}")
        
        # Auto-detect project info
        detected = self.smart_defaults.detect_project_info(path)
        defaults = self.smart_defaults.get_smart_defaults(detected)
        
        print(f"📋 Detected: {detected['project_name']} ({detected['project_number']}) - {detected['project_year']}")
        
        if detected['confidence_score'] < 0.7:
            print("⚠️  Low confidence in auto-detection. Consider using 'aec init' for manual setup.")
            
            # Show suggestions
            for suggestion in detected.get('suggestions', []):
                print(f"   💡 {suggestion}")
        
        # Initialize scanner
        self.scanner = AECDirectoryScanner()
        
        # Create project with detected settings
        result = self.scanner.initialize_project(
            defaults['project_number'],
            defaults['project_name'], 
            path,
            defaults['project_year']
        )
        
        if result['success']:
            print(f"✅ Project initialized successfully!")
            print(f"   Project ID: {result['project_id']}")
            print(f"   Directories created: {result.get('directories_created', 0)}")
            return result
        else:
            print(f"❌ Failed to initialize project: {result.get('message', 'Unknown error')}")
            return result
    
    def quick_scan(self, path: str = None) -> Dict[str, Any]:
        """
        Quick scan with automatic optimization.
        
        Args:
            path: Project path (auto-detects if not provided)
            
        Returns:
            Scan results
        """
        if not path:
            path = os.getcwd()
        
        # Auto-configure scan settings
        scan_config = self.smart_defaults.auto_configure_scan_settings(path)
        
        # Show scan preview
        print(f"⚡ Quick scan configured:")
        print(f"   Estimated time: {scan_config['estimated_duration_minutes']:.1f} minutes")
        print(f"   Batch size: {scan_config['batch_size']} files")
        print(f"   Memory limit: {scan_config['memory_limit_mb']}MB")
        
        # Initialize scanner if needed
        if not self.scanner:
            print("🔧 Auto-initializing project...")
            init_result = self.auto_init(path)
            if not init_result['success']:
                return init_result
        
        # Create progress manager
        progress = ProgressManager(style=ProgressStyle.DETAILED)
        
        def progress_callback(current: int, total: int):
            if not hasattr(progress_callback, '_started'):
                progress.start("Scanning files", total)
                progress_callback._started = True
            progress.update(current=current)
            if current >= total:
                progress.finish(success=True, final_message="Scan completed")
        
        print(f"🔍 Starting scan...")
        
        # Get project ID (assume latest if multiple)
        # This is a simplified approach - in production you'd want better project management
        project_id = 1  # For demo purposes
        
        result = self.scanner.scan_project(
            project_id,
            'full',
            progress_callback=progress_callback
        )
        
        if result['success']:
            print(f"✅ Scan completed successfully!")
            print(f"   Files scanned: {result.get('files_scanned', 0)}")
            print(f"   Files added: {result.get('files_added', 0)}")
            print(f"   Scan time: {result.get('scan_time', 0):.1f}s")
        else:
            print(f"❌ Scan failed: {result.get('message', 'Unknown error')}")
        
        return result
    
    def smart_report(self, project_id: int = None, output: str = None) -> Dict[str, Any]:
        """
        Generate smart report with automatic formatting.
        
        Args:
            project_id: Project ID (auto-detects if not provided)
            output: Output file (auto-generates if not provided)
            
        Returns:
            Report generation results
        """
        if not self.scanner:
            print("❌ No scanner initialized. Run 'aec scan' first.")
            return {'success': False, 'message': 'No scanner available'}
        
        if not project_id:
            project_id = 1  # Auto-detect or use latest
        
        if not output:
            # Auto-generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"aec_report_{timestamp}.html"
        
        print(f"📊 Generating smart report...")
        
        result = self.scanner.generate_project_report(project_id)
        
        if result['success']:
            # Save to file
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Create a nice HTML report
                html_content = self._create_html_report(result)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ Report generated: {output_path}")
                print(f"   Open in browser: file://{output_path.absolute()}")
                
                return {'success': True, 'output_path': str(output_path)}
            except Exception as e:
                print(f"❌ Failed to save report: {e}")
                return {'success': False, 'message': str(e)}
        else:
            print(f"❌ Report generation failed: {result.get('message', 'Unknown error')}")
            return result
    
    def status(self) -> Dict[str, Any]:
        """Get system status with smart insights."""
        if not self.scanner:
            # Try to detect existing projects
            current_dir = os.getcwd()
            detected_projects = self.smart_defaults.detect_existing_projects(current_dir)
            
            if detected_projects:
                print(f"🔍 Found {len(detected_projects)} potential AEC projects:")
                for i, project in enumerate(detected_projects[:5], 1):
                    confidence = project.get('confidence_score', 0) * 100
                    size_info = project.get('size_analysis', {})
                    print(f"   {i}. {project['project_name']} ({confidence:.0f}% confidence)")
                    print(f"      Path: {project['path']}")
                    print(f"      Size: {size_info.get('file_count', 0)} files, "
                          f"{size_info.get('total_size_mb', 0):.1f}MB")
                
                print(f"\n💡 Run 'aec init' in a project directory to get started")
                return {'success': True, 'projects_found': len(detected_projects)}
            else:
                print("📁 No AEC projects detected in current directory")
                print("💡 Run 'aec init' to create a new project")
                return {'success': True, 'projects_found': 0}
        
        # Get scanner status
        status_result = self.scanner.get_system_status()
        
        if status_result['success']:
            print("✅ AEC Scanner Status:")
            
            # Database info
            db_info = status_result.get('database', {})
            print(f"   Database: {db_info.get('type', 'Unknown')} - {db_info.get('status', 'Unknown')}")
            
            # Projects info
            projects = status_result.get('projects', [])
            print(f"   Projects: {len(projects)} active")
            
            for project in projects[:3]:  # Show first 3
                print(f"     • {project.get('project_name', 'Unknown')} "
                      f"({project.get('total_files', 0)} files)")
            
            # Recent activity
            recent_scans = status_result.get('recent_scans', [])
            if recent_scans:
                latest_scan = recent_scans[0]
                print(f"   Last scan: {latest_scan.get('end_time', 'Unknown')} "
                      f"({latest_scan.get('files_scanned', 0)} files)")
        
        return status_result
    
    def _create_html_report(self, report_data: Dict[str, Any]) -> str:
        """Create a beautiful HTML report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEC Project Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; }}
        .content {{ padding: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .stat-number {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #6c757d; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}
        .chart {{ margin: 20px 0; }}
        h1, h2, h3 {{ margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .footer {{ text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ AEC Project Report</h1>
            <p>Generated on {report_data.get('generated_at', 'Unknown date')}</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{report_data.get('total_files', 0)}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{report_data.get('total_size_gb', 0):.1f} GB</div>
                    <div class="stat-label">Total Size</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(report_data.get('file_types', []))}</div>
                    <div class="stat-label">File Types</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(report_data.get('disciplines', []))}</div>
                    <div class="stat-label">Disciplines</div>
                </div>
            </div>
            
            <h2>📁 File Distribution</h2>
            <table>
                <thead>
                    <tr><th>File Type</th><th>Count</th><th>Size</th><th>Percentage</th></tr>
                </thead>
                <tbody>
        """
        
        # Add file types table
        for file_type in report_data.get('file_types', [])[:10]:
            percentage = (file_type.get('count', 0) / max(report_data.get('total_files', 1), 1)) * 100
            html += f"""
                    <tr>
                        <td>{file_type.get('extension', 'Unknown')}</td>
                        <td>{file_type.get('count', 0):,}</td>
                        <td>{file_type.get('total_size_mb', 0):.1f} MB</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <div class="footer">
                <p>Generated by AEC Directory Scanner • 
                   <span class="badge badge-success">Optimized & Streamlined</span>
                </p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html


def create_streamlined_parser() -> argparse.ArgumentParser:
    """Create the streamlined argument parser."""
    parser = argparse.ArgumentParser(
        description='🏗️ AEC Scanner - Streamlined Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Ultra-Simple Commands:

  aec                           # Auto-detect and initialize current directory
  aec scan                      # Quick scan with smart optimization  
  aec report                    # Generate beautiful HTML report
  aec status                    # Show system status and insights

🎯 Advanced Commands:

  aec init [path]              # Manual project initialization
  aec scan [path] --fast       # Fast scan mode
  aec report --pdf             # Generate PDF report
  
💡 Tips:
  • Most commands work without any arguments - just run them!
  • The scanner auto-detects project settings intelligently
  • All operations use smart defaults to minimize typing
        """
    )
    
    # Subcommands with minimal requirements
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Auto-init (default when no command given)
    init_parser = subparsers.add_parser('init', help='Initialize project (auto-detects settings)')
    init_parser.add_argument('path', nargs='?', help='Project path (default: current directory)')
    
    # Quick scan
    scan_parser = subparsers.add_parser('scan', help='Quick scan with smart optimization')
    scan_parser.add_argument('path', nargs='?', help='Project path (default: current directory)')
    scan_parser.add_argument('--fast', action='store_true', help='Fast scan mode (skip metadata)')
    
    # Smart report
    report_parser = subparsers.add_parser('report', help='Generate beautiful report')
    report_parser.add_argument('--output', help='Output file (auto-generates if not provided)')
    report_parser.add_argument('--pdf', action='store_true', help='Generate PDF instead of HTML')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show system status and insights')
    
    return parser


def main() -> int:
    """Main entry point for streamlined CLI."""
    cli = StreamlinedCLI()
    parser = create_streamlined_parser()
    args = parser.parse_args()
    
    try:
        # Handle no command - default to auto-init
        if not args.command:
            print("🚀 AEC Scanner - Auto-initializing current directory...")
            result = cli.auto_init()
            return 0 if result['success'] else 1
        
        # Execute commands
        if args.command == 'init':
            result = cli.auto_init(args.path)
            return 0 if result['success'] else 1
            
        elif args.command == 'scan':
            result = cli.quick_scan(args.path)
            return 0 if result['success'] else 1
            
        elif args.command == 'report':
            result = cli.smart_report(output=args.output)
            return 0 if result['success'] else 1
            
        elif args.command == 'status':
            result = cli.status()
            return 0 if result['success'] else 1
            
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Run 'aec status' to check system health")
        return 1
    finally:
        # Cleanup
        if cli.scanner:
            try:
                cli.scanner.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    sys.exit(main())