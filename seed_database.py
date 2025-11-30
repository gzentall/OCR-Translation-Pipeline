#!/usr/bin/env python3

"""
Database seeding script.
Creates the initial Admin user if the database is empty.
Can be run safely multiple times (idempotent).
"""

import sys
from pathlib import Path
import bcrypt

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.database import init_db, DatabaseSession, User, UserRole


def seed_initial_admin():
    """Seed the database with the initial admin user"""
    
    print("Starting database seed...")
    
    # First, ensure database tables exist
    print("Initializing database tables...")
    if not init_db():
        print("✗ Failed to initialize database tables")
        return False
    
    with DatabaseSession() as db:
        # Check if any users exist
        user_count = db.query(User).count()
        
        if user_count > 0:
            print(f"Database already contains {user_count} user(s), skipping seed")
            return True
        
        print("Database is empty, creating initial admin user...")
        
        # Create initial admin user
        password = "mRKPKAWrLn3#VFB#Rsu"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = User(
            first_name="Gabe",
            last_name="Zentall",
            email="gabe@zentall.com",
            password_hash=password_hash,
            role=UserRole.ADMIN,
            is_active=True,
            last_sign_in=None,
            invite_token=None
        )
        
        try:
            db.add(admin_user)
            db.commit()
            print("✓ Database seeded with initial admin user")
            print(f"  Email: {admin_user.email}")
            print(f"  Role: {admin_user.role.value}")
            print(f"  Password: {password}")
            return True
        except Exception as e:
            db.rollback()
            print(f"✗ Error creating admin user: {e}")
            return False


if __name__ == '__main__':
    success = seed_initial_admin()
    sys.exit(0 if success else 1)





