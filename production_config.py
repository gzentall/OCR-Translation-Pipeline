#!/usr/bin/env python3

"""
Production configuration updates for app.py
This script updates sensitive settings for production deployment.
"""

import os
import secrets
from pathlib import Path


def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_hex(32)


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'DATABASE_URL',
        'RESEND_API_KEY',
        'APP_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_api_keys():
    """Check if API key files exist."""
    api_keys = {
        '.gcp_api_key': 'Google Cloud (REQUIRED)',
        '.openai_api_key': 'OpenAI (Optional)',
        '.notion_api_key': 'Notion (Optional)'
    }
    
    print("\n📋 API Key Files Status:")
    for key_file, description in api_keys.items():
        path = Path(key_file)
        if path.exists():
            print(f"   ✅ {key_file} - {description}")
        else:
            if 'REQUIRED' in description:
                print(f"   ❌ {key_file} - {description} - NOT FOUND")
            else:
                print(f"   ⚠️  {key_file} - {description} - Not configured")


def check_directories():
    """Check if all required directories exist."""
    required_dirs = [
        'letters/inbox',
        'letters/work',
        'letters/out/en',
        'ocr_storage/documents',
        'ocr_storage/people',
        'static/css'
    ]
    
    print("\n📁 Directory Structure:")
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} - Creating...")
            path.mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    if all_exist:
        print("   All directories exist")
    else:
        print("   Created missing directories")


def check_database_connection():
    """Test database connection."""
    print("\n🗄️  Database Connection:")
    try:
        from scripts.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            if result:
                print("   ✅ Database connection successful")
                return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False


def production_checklist():
    """Run through production deployment checklist."""
    print("=" * 60)
    print("🚀 Production Deployment Checklist")
    print("=" * 60)
    
    # Load .env if it exists
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment variables
    env_ok = check_environment()
    
    # Check API keys
    check_api_keys()
    
    # Check directories
    check_directories()
    
    # Check database
    db_ok = check_database_connection()
    
    # Security recommendations
    print("\n🔒 Security Recommendations:")
    secret_key = os.getenv('SECRET_KEY', '')
    if secret_key == 'dev-secret-key-12345-change-in-production':
        print("   ❌ SECRET_KEY is using default value - CHANGE IT!")
        print(f"   💡 Use this: {generate_secret_key()}")
    elif len(secret_key) < 32:
        print("   ⚠️  SECRET_KEY is too short (should be 32+ characters)")
    else:
        print("   ✅ SECRET_KEY looks secure")
    
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        print("   ✅ FLASK_ENV set to production")
    else:
        print(f"   ⚠️  FLASK_ENV is '{flask_env}' - should be 'production'")
    
    app_url = os.getenv('APP_URL', '')
    if app_url.startswith('https://'):
        print("   ✅ APP_URL uses HTTPS")
    else:
        print(f"   ⚠️  APP_URL should use HTTPS in production: {app_url}")
    
    # Final summary
    print("\n" + "=" * 60)
    if env_ok and db_ok:
        print("✅ System is ready for production deployment!")
        print("\nNext steps:")
        print("1. Review security settings above")
        print("2. Initialize database: python3 -c 'from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)'")
        print("3. Create admin user: python3 seed_database.py")
        print("4. Start application: gunicorn -w 4 -b 0.0.0.0:5001 app:app")
    else:
        print("❌ System is NOT ready for deployment")
        print("\nPlease fix the issues above before deploying.")
    print("=" * 60)


def update_app_config():
    """
    Suggest production configuration changes for app.py
    """
    print("\n📝 Recommended app.py Configuration Changes:")
    print("\n1. Replace line 41 (SECRET_KEY) with:")
    print("   app.secret_key = os.getenv('SECRET_KEY')")
    print("   if not app.secret_key:")
    print("       raise ValueError('SECRET_KEY environment variable not set')")
    
    print("\n2. Update line 42 (SESSION_COOKIE_SECURE) to:")
    print("   app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'")
    
    print("\n3. Update line 1769 (app.run) to:")
    print("   debug_mode = os.getenv('FLASK_ENV') != 'production'")
    print("   app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5001)))")
    
    print("\n4. Add error logging:")
    print("   import logging")
    print("   if not app.debug:")
    print("       file_handler = logging.FileHandler('flask.log')")
    print("       file_handler.setLevel(logging.WARNING)")
    print("       app.logger.addHandler(file_handler)")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--config-help':
        update_app_config()
    else:
        production_checklist()


