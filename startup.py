#!/usr/bin/env python3
"""
Startup script for production deployment.
Initializes database and creates admin user if needed.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🚀 Starting OCR Translation Pipeline")
print("=" * 60)

# Step 1: Initialize database tables
print("\n1️⃣  Initializing database...")
try:
    from scripts.database import Base, engine, User, DatabaseSession
    Base.metadata.create_all(engine)
    print("   ✅ Database tables ready")
except Exception as e:
    print(f"   ⚠️  Database initialization warning: {e}")
    sys.exit(1)

# Step 2: Create admin user if doesn't exist
print("\n2️⃣  Checking for admin user...")
try:
    with DatabaseSession() as db:
        # Check if any users exist
        user_count = db.query(User).count()
        
        if user_count == 0:
            print("   📝 No users found. Creating admin user...")
            
            # Import required modules
            import bcrypt
            from scripts.database import UserRole
            
            # Get admin credentials from environment or use defaults
            admin_email = os.getenv('SEED_SUPERADMIN_EMAIL', 'gabe@zentall.com')
            admin_password = os.getenv('SEED_SUPERADMIN_PASSWORD', 'admin123')
            admin_first = os.getenv('SEED_SUPERADMIN_FIRSTNAME', 'Admin')
            admin_last = os.getenv('SEED_SUPERADMIN_LASTNAME', 'User')
            
            # Create admin user
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin_user = User(
                first_name=admin_first,
                last_name=admin_last,
                email=admin_email,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            
            print(f"   ✅ Admin user created: {admin_email}")
            print(f"   🔑 Password: {admin_password}")
            print("   ⚠️  IMPORTANT: Change this password immediately after first login!")
        else:
            print(f"   ✅ Found {user_count} existing user(s)")
            
except Exception as e:
    print(f"   ⚠️  Admin user creation warning: {e}")

print("\n" + "=" * 60)
print("✅ Initialization complete!")
print("=" * 60)
print()


