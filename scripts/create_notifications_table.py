#!/usr/bin/env python3
"""
Create notifications table in database.
Run this script to add the notifications table to your database.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.database import init_db, Base, engine

if __name__ == '__main__':
    print("Creating notifications table...")
    try:
        # Create all tables (will only create new ones)
        Base.metadata.create_all(bind=engine)
        print("✓ Notifications table created successfully!")
        print("\nTo verify, check your database for the 'notifications' table.")
    except Exception as e:
        print(f"✗ Error creating notifications table: {e}")
        sys.exit(1)


