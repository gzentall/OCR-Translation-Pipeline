"""
Test Cloudflare R2 connection.
Run this to verify your R2 credentials work before uploading data.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.r2_storage import R2Storage


def test_r2_connection():
    """Test R2 connection and basic operations."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            CLOUDFLARE R2 CONNECTION TEST                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Check environment variables
    print("1️⃣  Checking environment variables...")
    env_vars = {
        'R2_ENDPOINT_URL': os.getenv('R2_ENDPOINT_URL'),
        'R2_ACCESS_KEY_ID': os.getenv('R2_ACCESS_KEY_ID'),
        'R2_SECRET_ACCESS_KEY': os.getenv('R2_SECRET_ACCESS_KEY'),
        'R2_BUCKET_NAME': os.getenv('R2_BUCKET_NAME', 'documents')
    }
    
    for key, value in env_vars.items():
        if value:
            masked = value if key == 'R2_BUCKET_NAME' else (value[:10] + '...' if len(value) > 10 else value)
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: MISSING")
            print()
            print("ERROR: Missing R2 credentials in .env file!")
            print("Please add all required R2 environment variables.")
            return False
    
    print()
    
    # Initialize R2 storage
    print("2️⃣  Initializing R2 storage client...")
    try:
        r2 = R2Storage()
        print("   ✅ R2 client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize R2 client: {e}")
        return False
    
    print()
    
    # Test connection
    print("3️⃣  Testing R2 connection...")
    if r2.test_connection():
        print("   ✅ Connection successful!")
    else:
        print("   ❌ Connection failed!")
        return False
    
    print()
    
    # Test write operation
    print("4️⃣  Testing write operation (small test file)...")
    test_data = {
        'test': True,
        'message': 'R2 connection test',
        'timestamp': '2025-11-27'
    }
    
    try:
        success = r2.save_document('_test_connection', test_data)
        if success:
            print("   ✅ Write operation successful!")
        else:
            print("   ❌ Write operation failed!")
            return False
    except Exception as e:
        print(f"   ❌ Write operation error: {e}")
        return False
    
    print()
    
    # Test read operation
    print("5️⃣  Testing read operation...")
    try:
        retrieved = r2.get_document('_test_connection')
        if retrieved and retrieved.get('test') == True:
            print("   ✅ Read operation successful!")
            print(f"   Retrieved data: {retrieved}")
        else:
            print("   ❌ Read operation failed!")
            return False
    except Exception as e:
        print(f"   ❌ Read operation error: {e}")
        return False
    
    print()
    
    # Clean up test file
    print("6️⃣  Cleaning up test file...")
    try:
        r2.delete_document('_test_connection')
        print("   ✅ Test file deleted")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not delete test file: {e}")
    
    print()
    
    # Get storage stats
    print("7️⃣  Checking current R2 storage...")
    stats = r2.get_storage_stats()
    print(f"   • Documents: {stats['documents']}")
    print(f"   • Images: {stats['images']}")
    print(f"   • Total size: {stats['total_size_mb']} MB")
    
    print()
    print("═" * 66)
    print()
    print("🎉 ALL TESTS PASSED!")
    print()
    print("✅ Your R2 storage is ready to use.")
    print("✅ You can now upload your data with: python3 scripts/upload_to_r2.py")
    print()
    print("═" * 66)
    
    return True


if __name__ == '__main__':
    success = test_r2_connection()
    sys.exit(0 if success else 1)

