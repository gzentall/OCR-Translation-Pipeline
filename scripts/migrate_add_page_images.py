#!/usr/bin/env python3

"""
Migration script to add page_images column to documents table.
"""

import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database import engine, DatabaseSession

def check_column_exists():
    """Check if page_images column already exists."""
    try:
        with DatabaseSession() as db:
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='page_images'
            """))
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking column: {e}")
        return False

def add_page_images_column():
    """Add page_images column to documents table."""
    print("🔄 Adding page_images column to documents table...")
    
    # Check if column already exists
    if check_column_exists():
        print("✅ page_images column already exists!")
        return True
    
    try:
        with DatabaseSession() as db:
            # Add the column
            db.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN page_images TEXT
            """))
            db.commit()
            print("✅ Successfully added page_images column")
            
            # Verify
            if check_column_exists():
                print("✅ Verification passed")
                return True
            else:
                print("❌ Verification failed")
                return False
                
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False

def main():
    """Run the migration."""
    load_dotenv()
    
    print("=" * 80)
    print("DATABASE MIGRATION: Add page_images Column")
    print("=" * 80)
    
    # Check database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    # Run migration
    success = add_page_images_column()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed")
        sys.exit(1)

if __name__ == '__main__':
    main()

