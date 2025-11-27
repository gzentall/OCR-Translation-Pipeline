#!/usr/bin/env python3
"""
Interactive API Key Setup Script
Helps you configure all required API keys for the OCR Translation Pipeline
"""

import os
import sys
from pathlib import Path
from getpass import getpass

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

PROJECT_ROOT = Path(__file__).parent

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓{RESET} {text}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠{RESET}  {text}")

def print_error(text):
    """Print error message"""
    print(f"{RED}✗{RESET} {text}")

def check_key_file(filename):
    """Check if a key file exists and is not empty"""
    filepath = PROJECT_ROOT / filename
    if filepath.exists():
        content = filepath.read_text().strip()
        if content:
            return True, content[:20] + "..." if len(content) > 20 else content
    return False, None

def save_key_file(filename, content):
    """Save API key to a file"""
    filepath = PROJECT_ROOT / filename
    filepath.write_text(content.strip() + '\n')
    # Set restrictive permissions (owner read/write only)
    os.chmod(filepath, 0o600)
    return filepath

def setup_google_cloud():
    """Setup Google Cloud API key"""
    print_header("Google Cloud API Setup")
    
    print("Google Cloud is required for:")
    print("  • Cloud Vision API (OCR)")
    print("  • Cloud Translation API (Translation)")
    print()
    
    exists, preview = check_key_file('.gcp_api_key')
    
    if exists:
        print_success(f"Found existing API key: {preview}")
        response = input(f"\n{YELLOW}Do you want to replace it? (y/N):{RESET} ").strip().lower()
        if response != 'y':
            return True
    
    print("\n" + BOLD + "To get your Google Cloud API key:" + RESET)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create or select a project")
    print("3. Enable 'Cloud Vision API' and 'Cloud Translation API'")
    print("4. Go to: APIs & Services → Credentials")
    print("5. Click 'Create credentials' → 'API key'")
    print("6. Copy the API key\n")
    
    api_key = getpass(f"{BOLD}Enter your Google Cloud API key (hidden): {RESET}").strip()
    
    if not api_key:
        print_error("No API key entered. Skipping...")
        return False
    
    # Validate basic format
    if len(api_key) < 20:
        print_error("API key seems too short. Please check and try again.")
        return False
    
    filepath = save_key_file('.gcp_api_key', api_key)
    print_success(f"Saved API key to {filepath}")
    return True

def setup_openai():
    """Setup OpenAI API key"""
    print_header("OpenAI API Setup")
    
    print("OpenAI is required for:")
    print("  • AI-powered document analysis")
    print("  • Entity extraction")
    print("  • Relationship detection")
    print()
    
    exists, preview = check_key_file('.openai_api_key')
    
    if exists:
        print_success(f"Found existing API key: {preview}")
        response = input(f"\n{YELLOW}Do you want to replace it? (y/N):{RESET} ").strip().lower()
        if response != 'y':
            return True
    
    print("\n" + BOLD + "To get your OpenAI API key:" + RESET)
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Sign in or create an account")
    print("3. Click 'Create new secret key'")
    print("4. Name it (e.g., 'OCR Pipeline')")
    print("5. Copy the key (starts with 'sk-')\n")
    
    api_key = getpass(f"{BOLD}Enter your OpenAI API key (hidden): {RESET}").strip()
    
    if not api_key:
        print_error("No API key entered. Skipping...")
        return False
    
    # Validate basic format
    if not api_key.startswith('sk-'):
        print_warning("OpenAI keys usually start with 'sk-'. Your key might be invalid.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            return False
    
    filepath = save_key_file('.openai_api_key', api_key)
    print_success(f"Saved API key to {filepath}")
    return True

def setup_notion():
    """Setup Notion API key (optional)"""
    print_header("Notion API Setup (Optional)")
    
    print("Notion integration is OPTIONAL.")
    print("Only set this up if you want to sync documents to Notion.")
    print()
    
    response = input(f"{YELLOW}Do you want to set up Notion integration? (y/N):{RESET} ").strip().lower()
    if response != 'y':
        print("Skipping Notion setup...")
        return True
    
    exists, preview = check_key_file('.notion_api_key')
    
    if exists:
        print_success(f"Found existing API key: {preview}")
        response = input(f"\n{YELLOW}Do you want to replace it? (y/N):{RESET} ").strip().lower()
        if response != 'y':
            return True
    
    print("\n" + BOLD + "To get your Notion API key:" + RESET)
    print("1. Go to: https://www.notion.so/my-integrations")
    print("2. Click 'New integration'")
    print("3. Name it (e.g., 'OCR Pipeline')")
    print("4. Select your workspace")
    print("5. Copy the 'Internal Integration Token' (starts with 'secret_')")
    print("6. Share your database with the integration\n")
    
    api_key = getpass(f"{BOLD}Enter your Notion API token (hidden): {RESET}").strip()
    
    if not api_key:
        print_warning("No API key entered. Notion integration will not be available.")
        return True
    
    # Validate basic format
    if not api_key.startswith('secret_'):
        print_warning("Notion tokens usually start with 'secret_'. Your token might be invalid.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            return True
    
    filepath = save_key_file('.notion_api_key', api_key)
    print_success(f"Saved API token to {filepath}")
    return True

def check_setup():
    """Check current setup status"""
    print_header("Current Setup Status")
    
    checks = [
        ('.gcp_api_key', 'Google Cloud API', True),
        ('.openai_api_key', 'OpenAI API', True),
        ('.notion_api_key', 'Notion API', False),
    ]
    
    all_required_ok = True
    
    for filename, name, required in checks:
        exists, preview = check_key_file(filename)
        if exists:
            print_success(f"{name}: Configured ({preview})")
        else:
            if required:
                print_error(f"{name}: NOT configured (REQUIRED)")
                all_required_ok = False
            else:
                print_warning(f"{name}: NOT configured (optional)")
    
    return all_required_ok

def test_apis():
    """Offer to test API connections"""
    print_header("Test API Connections")
    
    print("You can now test if your API keys are working correctly.")
    response = input(f"\n{YELLOW}Run API tests now? (Y/n):{RESET} ").strip().lower()
    
    if response == 'n':
        print("\nYou can test later by running:")
        print(f"  {BOLD}python3 test_integrations.py{RESET}")
        return
    
    print("\nRunning API tests...\n")
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, 'test_integrations.py'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print_warning("Warnings/Errors:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print_error("Tests timed out. You can run them manually later.")
    except Exception as e:
        print_error(f"Could not run tests: {e}")
        print("You can run them manually:")
        print(f"  {BOLD}python3 test_integrations.py{RESET}")

def main():
    """Main setup flow"""
    print(f"\n{BOLD}{BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║           OCR Translation Pipeline Setup                 ║")
    print("║               API Key Configuration                      ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{RESET}\n")
    
    print("This script will help you set up API keys for:")
    print("  • Google Cloud (Vision & Translation)")
    print("  • OpenAI (AI Processing)")
    print("  • Notion (Optional - Document sync)")
    print()
    
    # Check current status
    all_ok = check_setup()
    
    if all_ok:
        print(f"\n{GREEN}{BOLD}All required API keys are already configured!{RESET}")
        response = input(f"\n{YELLOW}Do you want to reconfigure any keys? (y/N):{RESET} ").strip().lower()
        if response != 'y':
            print("\nSetup complete! You can start using the application.")
            return
    
    # Setup each API
    print("\n" + BOLD + "Let's set up your API keys..." + RESET)
    
    gcp_ok = setup_google_cloud()
    openai_ok = setup_openai()
    notion_ok = setup_notion()
    
    # Final status
    print_header("Setup Complete!")
    
    if gcp_ok and openai_ok:
        print_success("All required API keys are configured!")
        print("\nYou can now:")
        print(f"  1. Start Flask: {BOLD}python3 app.py{RESET}")
        print(f"  2. Start Next.js: {BOLD}cd ocr-auth && npm run dev{RESET}")
        print(f"  3. Access the app: {BOLD}http://localhost:3000{RESET}")
        
        test_apis()
    else:
        print_error("Some required API keys are missing.")
        print("\nPlease run this script again to complete setup:")
        print(f"  {BOLD}python3 setup_api_keys.py{RESET}")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup cancelled by user.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)






