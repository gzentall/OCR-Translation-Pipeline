#!/usr/bin/env python3

"""
Database Migration Script for OCR Quality Enhancement.
Adds new columns for corrected_text, confidence scores, and review status.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import text

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseSession, engine


def run_migration():
    """
    Add new columns to documents table for enhanced OCR features.
    
    New columns:
    - corrected_text: LLM-corrected OCR text
    - correction_confidence: 0-100 confidence score
    - correction_metadata: JSON string with correction details
    - is_reviewed: Boolean indicating if editor approved corrections
    """
    print("\n" + "="*80)
    print("Database Migration: Adding Enhanced OCR Columns")
    print("="*80 + "\n")
    
    migrations = [
        {
            'name': 'Add corrected_text column',
            'check': "SELECT column_name FROM information_schema.columns WHERE table_name='documents' AND column_name='corrected_text'",
            'sql': "ALTER TABLE documents ADD COLUMN corrected_text TEXT"
        },
        {
            'name': 'Add correction_confidence column',
            'check': "SELECT column_name FROM information_schema.columns WHERE table_name='documents' AND column_name='correction_confidence'",
            'sql': "ALTER TABLE documents ADD COLUMN correction_confidence INTEGER"
        },
        {
            'name': 'Add correction_metadata column',
            'check': "SELECT column_name FROM information_schema.columns WHERE table_name='documents' AND column_name='correction_metadata'",
            'sql': "ALTER TABLE documents ADD COLUMN correction_metadata TEXT"
        },
        {
            'name': 'Add is_reviewed column',
            'check': "SELECT column_name FROM information_schema.columns WHERE table_name='documents' AND column_name='is_reviewed'",
            'sql': "ALTER TABLE documents ADD COLUMN is_reviewed BOOLEAN DEFAULT FALSE NOT NULL"
        }
    ]
    
    with DatabaseSession() as db:
        for migration in migrations:
            print(f"Checking: {migration['name']}...")
            
            # Check if column already exists
            result = db.execute(text(migration['check']))
            if result.fetchone():
                print(f"  ✓ Column already exists, skipping")
                continue
            
            # Run migration
            try:
                db.execute(text(migration['sql']))
                db.commit()
                print(f"  ✅ Migration applied successfully")
            except Exception as e:
                print(f"  ❌ Migration failed: {e}")
                db.rollback()
                return False
    
    print("\n" + "="*80)
    print("✅ All migrations completed successfully!")
    print("="*80 + "\n")
    
    return True


def verify_migration():
    """Verify that all new columns exist in the database."""
    print("\n" + "="*80)
    print("Verifying Migration")
    print("="*80 + "\n")
    
    expected_columns = [
        'corrected_text',
        'correction_confidence',
        'correction_metadata',
        'is_reviewed'
    ]
    
    with DatabaseSession() as db:
        for column in expected_columns:
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name='documents' AND column_name='{column}'"
            result = db.execute(text(query))
            
            if result.fetchone():
                print(f"✅ Column exists: {column}")
            else:
                print(f"❌ Column missing: {column}")
                return False
    
    print("\n✅ All columns verified successfully!\n")
    return True


def main():
    """Run database migration."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate database for enhanced OCR features'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify that migration was applied'
    )
    
    args = parser.parse_args()
    
    # Check database connection
    try:
        with DatabaseSession() as db:
            db.execute(text("SELECT 1"))
            print("✅ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}\n")
        print("Make sure DATABASE_URL is set correctly:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'\n")
        sys.exit(1)
    
    if args.verify_only:
        success = verify_migration()
    else:
        success = run_migration()
        if success:
            verify_migration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

