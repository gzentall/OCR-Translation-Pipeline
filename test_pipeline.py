#!/usr/bin/env python3

"""
Test script for the OCR Translation Pipeline.
This script validates that all components are working correctly.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_api_key():
    """Test if API key is configured."""
    api_key_file = Path('.gcp_api_key')
    if not api_key_file.exists():
        return False, "API key file not found"
    
    with open(api_key_file, 'r') as f:
        key = f.read().strip()
    
    if not key:
        return False, "API key is empty"
    
    return True, "API key configured"

def test_docker():
    """Test if Docker is available."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Docker is available"
        else:
            return False, "Docker not working"
    except FileNotFoundError:
        return False, "Docker not installed"

def test_scripts():
    """Test if all required scripts exist and are executable."""
    scripts = [
        'scripts/run_vision_ocr.sh',
        'scripts/run_all_vision_ocr.sh',
        'scripts/translate_google.py'
    ]
    
    missing = []
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            missing.append(script)
        elif not os.access(script_path, os.X_OK) and script.endswith('.sh'):
            missing.append(f"{script} (not executable)")
    
    if missing:
        return False, f"Missing or non-executable scripts: {', '.join(missing)}"
    
    return True, "All scripts available"

def test_directories():
    """Test if all required directories exist."""
    directories = [
        'letters/inbox',
        'letters/work',
        'letters/out/en',
        'templates'
    ]
    
    missing = []
    for directory in directories:
        if not Path(directory).exists():
            missing.append(directory)
    
    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    
    return True, "All directories exist"

def test_python_dependencies():
    """Test if Python dependencies are installed."""
    required_packages = [
        ('flask', 'flask'),
        ('google.cloud.translate', 'google.cloud.translate_v2'),
        ('google.cloud.vision', 'google.cloud.vision')
    ]
    
    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        return False, f"Missing Python packages: {', '.join(missing)}"
    
    return True, "All Python dependencies installed"

def test_web_app():
    """Test if the web application can start."""
    try:
        # Try to import the Flask app
        sys.path.insert(0, str(Path.cwd()))
        import app
        return True, "Web application can be imported"
    except Exception as e:
        return False, f"Web application import failed: {e}"

def main():
    """Run all tests."""
    print("OCR Translation Pipeline - System Test")
    print("=" * 50)
    
    tests = [
        ("API Key", test_api_key),
        ("Docker", test_docker),
        ("Scripts", test_scripts),
        ("Directories", test_directories),
        ("Python Dependencies", test_python_dependencies),
        ("Web Application", test_web_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            status = "✓" if success else "✗"
            print(f"{status} {test_name}: {message}")
            results.append(success)
        except Exception as e:
            print(f"✗ {test_name}: Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\nYour OCR Translation Pipeline is ready to use!")
        print("Run 'python3 app.py' to start the web interface.")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("\nPlease fix the failing tests before using the pipeline.")
        
        if not results[0]:  # API key test
            print("\nTo fix API key issues:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Enable Vision API and Translation API")
            print("3. Create an API key")
            print("4. Save it to .gcp_api_key file")
        
        if not results[1]:  # Docker test
            print("\nTo fix Docker issues:")
            print("1. Install Docker from https://www.docker.com/get-started")
            print("2. Make sure Docker is running")

if __name__ == "__main__":
    main()
