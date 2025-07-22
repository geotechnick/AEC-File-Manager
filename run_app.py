"""
AEC File Manager - Application Launcher
Simple launcher script with environment setup and error handling
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Please run: pip install -r requirements.txt")
        return False
    
    return True


def setup_environment():
    """Setup environment variables and configuration"""
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        example_env = Path('.env.example')
        if example_env.exists():
            logger.info("Creating .env file from template")
            env_file.write_text(example_env.read_text())
        else:
            logger.info("Creating basic .env file")
            env_file.write_text("""
# Basic AEC File Manager Configuration
USE_LOCAL_LLM=false
STREAMLIT_PORT=8501
DEBUG_MODE=false
""".strip())
    
    # Create models directory for local LLM files
    models_dir = Path('models')
    if not models_dir.exists():
        models_dir.mkdir()
        logger.info("Created models directory for LLM files")


def launch_streamlit():
    """Launch the Streamlit application"""
    try:
        # Get port from environment or use default
        port = os.getenv('STREAMLIT_PORT', '8501')
        host = os.getenv('STREAMLIT_HOST', 'localhost')
        
        logger.info(f"Starting AEC File Manager on http://{host}:{port}")
        
        # Launch Streamlit
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 
            'ui_app.py',
            '--server.port', port,
            '--server.address', host,
            '--server.headless', 'true' if os.getenv('STREAMLIT_HEADLESS') == 'true' else 'false'
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error launching application: {e}")
        sys.exit(1)


def main():
    """Main launcher function"""
    print("🏗️  AEC File Manager - Starting...")
    print("=" * 50)
    
    # Check system requirements
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Launch application
    launch_streamlit()


if __name__ == "__main__":
    main()