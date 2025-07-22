"""
AEC File Manager - Installation Script
Automated setup script for first-time installation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header():
    """Print installation header"""
    print("🏗️  AEC File Manager - Installation Script")
    print("=" * 50)
    print("This script will help you set up the AEC File Manager")
    print("for local project directory management with AI assistance.")
    print()


def check_python_version():
    """Check Python version compatibility"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install required Python packages"""
    print("\nInstalling dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def setup_configuration():
    """Setup configuration files"""
    print("\nSetting up configuration...")
    
    # Create .env file
    env_file = Path('.env')
    if env_file.exists():
        print("ℹ️  Configuration file already exists")
    else:
        # Copy from example
        example_env = Path('.env.example')
        if example_env.exists():
            env_file.write_text(example_env.read_text())
            print("✅ Configuration file created from template")
        else:
            print("❌ Warning: No configuration template found")
    
    # Create directories
    directories = ['models', 'temp', 'backups']
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"✅ Created directory: {directory}/")
    
    return True


def prompt_llm_setup():
    """Prompt user for LLM setup preferences"""
    print("\n" + "=" * 50)
    print("🤖 Local LLM Setup")
    print("=" * 50)
    
    print("AEC File Manager supports several local LLM options:")
    print("1. Ollama (Recommended - Easy to install and use)")
    print("2. llama-cpp-python (Manual model download required)")
    print("3. Skip LLM setup (Use basic text processing only)")
    print()
    
    while True:
        choice = input("Select option (1-3): ").strip()
        
        if choice == '1':
            setup_ollama()
            break
        elif choice == '2':
            setup_llama_cpp()
            break
        elif choice == '3':
            print("ℹ️  LLM setup skipped. You can enable it later in .env")
            break
        else:
            print("Please enter 1, 2, or 3")


def setup_ollama():
    """Setup Ollama LLM"""
    print("\n🦙 Setting up Ollama...")
    
    # Check if Ollama is installed
    try:
        subprocess.run(['ollama', '--version'], capture_output=True, check=True)
        print("✅ Ollama is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama is not installed")
        print("\nTo install Ollama:")
        
        system = platform.system().lower()
        if system == 'windows':
            print("1. Download from: https://ollama.ai/download")
            print("2. Run the installer")
        elif system == 'darwin':  # macOS
            print("1. Download from: https://ollama.ai/download")
            print("2. Or use Homebrew: brew install ollama")
        elif system == 'linux':
            print("1. Run: curl -fsSL https://ollama.ai/install.sh | sh")
        
        print("\nAfter installing Ollama:")
        print("1. Run: ollama pull llama2")
        print("2. Start the service: ollama serve")
        
        return
    
    # Try to pull a model
    print("Downloading a lightweight model (this may take several minutes)...")
    try:
        subprocess.run(['ollama', 'pull', 'llama2'], check=True)
        print("✅ Llama2 model downloaded successfully")
        
        # Update .env file
        update_env_file({
            'USE_LOCAL_LLM': 'true',
            'LLM_MODEL_TYPE': 'ollama',
            'OLLAMA_MODEL': 'llama2'
        })
        
    except subprocess.CalledProcessError:
        print("❌ Failed to download model. Please run 'ollama pull llama2' manually")


def setup_llama_cpp():
    """Setup llama-cpp-python"""
    print("\n🦙 Setting up llama-cpp-python...")
    
    try:
        # Install llama-cpp-python
        print("Installing llama-cpp-python (this may take a while)...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'llama-cpp-python'])
        
        print("✅ llama-cpp-python installed")
        print("\nTo use llama-cpp, you need to download a model file:")
        print("1. Visit: https://huggingface.co/models?search=ggml")
        print("2. Download a .ggml or .gguf model file")
        print("3. Place it in the 'models/' directory")
        print("4. Update LLM_MODEL_PATH in .env to point to your model")
        
        # Update .env file
        update_env_file({
            'USE_LOCAL_LLM': 'true',
            'LLM_MODEL_TYPE': 'llama-cpp'
        })
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install llama-cpp-python")


def update_env_file(updates: dict):
    """Update .env file with new values"""
    env_file = Path('.env')
    
    if env_file.exists():
        content = env_file.read_text()
        
        for key, value in updates.items():
            # Replace existing line or add new one
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'{key}={value}')
            
            content = '\n'.join(lines)
        
        env_file.write_text(content)
        print(f"✅ Updated configuration: {', '.join(updates.keys())}")


def test_installation():
    """Test the installation"""
    print("\n" + "=" * 50)
    print("🧪 Testing Installation")
    print("=" * 50)
    
    try:
        # Test imports
        print("Testing core imports...")
        
        import streamlit
        print("✅ Streamlit")
        
        import pandas
        print("✅ Pandas")
        
        import plotly
        print("✅ Plotly")
        
        # Test our modules
        from agentic_ai import AgenticAI
        print("✅ Agentic AI core")
        
        from llm_integration import LocalLLMManager
        print("✅ LLM integration")
        
        print("\n✅ All core components working!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 50)
    print("🎉 Installation Complete!")
    print("=" * 50)
    
    print("To start the AEC File Manager:")
    print("1. Run: python run_app.py")
    print("2. Open your browser to: http://localhost:8501")
    print()
    
    print("Quick start guide:")
    print("• Create a new project from the 'Create Project' page")
    print("• Upload files using the 'File Explorer'")
    print("• Use the AI Assistant for natural language queries")
    print("• Track revisions and QC in their respective dashboards")
    print()
    
    print("For more information, see the README.md file")
    print()


def main():
    """Main installation function"""
    print_header()
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Installation failed during dependency installation")
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        print("❌ Installation failed during configuration setup")
        sys.exit(1)
    
    # Prompt for LLM setup
    prompt_llm_setup()
    
    # Test installation
    if not test_installation():
        print("❌ Installation validation failed")
        sys.exit(1)
    
    # Show next steps
    print_next_steps()


if __name__ == "__main__":
    main()