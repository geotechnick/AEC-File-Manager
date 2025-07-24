"""
Setup script for AEC Directory Scanner

A comprehensive Python-based software system that automatically builds and manages
the standardized AEC project directory structure, scans all files within the directory
tree, extracts detailed metadata from each file, and stores this information in a
structured database.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)

setup(
    name="aec-directory-scanner",
    version="1.0.0",
    author="AEC Development Team",
    author_email="dev@aec-scanner.com",
    description="Comprehensive AEC project directory scanning and metadata extraction system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aec-team/aec-directory-scanner",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Include package data
    include_package_data=True,
    package_data={
        "aec_scanner": ["*.yaml", "*.json"],
        "": ["*.md", "*.txt", "*.yaml", "*.json"]
    },
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "postgresql": ["psycopg2-binary>=2.9.0"],
        "performance": ["psutil>=5.8.0"],
        "enhanced": [
            "Pillow>=9.0.0",
            "PyPDF2>=3.0.0", 
            "python-magic>=0.4.24"
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0"
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0"
        ]
    },
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command-line tools
    entry_points={
        "console_scripts": [
            "aec-scanner=aec_scanner_cli:main",
        ],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    
    # Keywords for PyPI
    keywords=[
        "aec", "architecture", "engineering", "construction",
        "file-scanning", "metadata-extraction", "directory-management",
        "project-management", "database", "file-organization"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/aec-team/aec-directory-scanner/issues",
        "Source": "https://github.com/aec-team/aec-directory-scanner",
        "Documentation": "https://aec-directory-scanner.readthedocs.io/",
    },
    
    # License
    license="MIT",
    
    # Additional metadata
    zip_safe=False,
)