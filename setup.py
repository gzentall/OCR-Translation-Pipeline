#!/usr/bin/env python3

"""
Setup script for the OCR Translation Pipeline web application.
This script helps set up the environment and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Docker is installed")
            return True
        else:
            print("✗ Docker is not installed")
            return False
    except FileNotFoundError:
        print("✗ Docker is not installed")
        return False

def install_python_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✓ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Python dependencies: {e}")
        return False

def check_api_key():
    """Check if Google Cloud API key is configured."""
    api_key_file = Path('.gcp_api_key')
    if api_key_file.exists():
        with open(api_key_file, 'r') as f:
            key = f.read().strip()
        if key:
            print("✓ Google Cloud API key is configured")
            return True
        else:
            print("✗ Google Cloud API key file is empty")
            return False
    else:
        print("✗ Google Cloud API key file (.gcp_api_key) not found")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        'letters/inbox',
        'letters/work', 
        'letters/out/en',
        'letters/out/pdf',
        'letters/out/qa',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directory structure created")

def make_scripts_executable():
    """Make shell scripts executable."""
    scripts = [
        'scripts/run_vision_ocr.sh',
        'scripts/run_all_vision_ocr.sh'
    ]
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            os.chmod(script_path, 0o755)
    
    print("✓ Scripts made executable")

def main():
    """Main setup function."""
    print("OCR Translation Pipeline Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Check Docker
    docker_ok = check_docker()
    
    # Create directories
    create_directories()
    
    # Make scripts executable
    make_scripts_executable()
    
    # Install Python dependencies
    deps_ok = install_python_dependencies()
    
    # Check API key
    api_key_ok = check_api_key()
    
    print("\nSetup Summary:")
    print("=" * 40)
    print(f"Python Dependencies: {'✓' if deps_ok else '✗'}")
    print(f"Docker: {'✓' if docker_ok else '✗'}")
    print(f"API Key: {'✓' if api_key_ok else '✗'}")
    print(f"Directory Structure: ✓")
    print(f"Scripts: ✓")
    
    if not api_key_ok:
        print("\n⚠️  IMPORTANT: You need to set up your Google Cloud API key:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Vision API and Translation API")
        print("4. Create an API key in APIs & Services → Credentials")
        print("5. Save the API key to .gcp_api_key file")
    
    if not docker_ok:
        print("\n⚠️  IMPORTANT: You need to install Docker:")
        print("Visit https://www.docker.com/get-started to download and install Docker")
    
    if deps_ok and docker_ok and api_key_ok:
        print("\n🎉 Setup complete! You can now run the web application:")
        print("python3 app.py")
        print("\nThen open http://localhost:5000 in your browser")
    else:
        print("\n⚠️  Setup incomplete. Please address the issues above before running the application.")

if __name__ == "__main__":
    main()

