#!/usr/bin/env python3

"""
Sync page_images from local storage to PostgreSQL database - simple version.
Only updates page_images and page_count columns without querying other fields.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database import DatabaseSession

def sync_images_to_database():
    """Sync page_images from local storage JSON files to PostgreSQL."""
    
    print("=" * 80)
    print("SYNCING PAGE IMAGES TO DATABASE")
    print("=" * 80)
    
    storage_dir = Path('ocr_storage/documents')
    
    if not storage_dir.exists():
        print(f"❌ Storage directory not found: {storage_dir}")
        return False
    
    updated_count = 0
    skipped_no_images = 0
    skipped_not_in_db = 0
    error_count = 0
    
    # Get all document JSON files
    doc_files = list(storage_dir.glob('*.json'))
    print(f"📊 Found {len(doc_files)} documents in local storage\n")
    
    for doc_file in doc_files:
        try:
            # Load document from local storage
            with open(doc_file) as f:
                doc_data = json.load(f)
            
            doc_id = doc_file.stem.replace('.json', '')
            page_images = doc_data.get('page_images', [])
            
            if not page_images:
                skipped_no_images += 1
                continue
            
            # Use a new session for each document to avoid transaction issues
            with DatabaseSession() as db:
                # Check if document exists using simple query
                result = db.execute(text("SELECT id FROM documents WHERE id = :doc_id"), {"doc_id": doc_id})
                doc_exists = result.fetchone()
                
                if not doc_exists:
                    # Document exists in local storage but not in database - skip it
                    skipped_not_in_db += 1
                    continue
                
                # Update page_images in database using raw SQL
                page_images_json = json.dumps(page_images)
                db.execute(
                    text("""
                        UPDATE documents 
                        SET page_images = :images, page_count = :count
                        WHERE id = :doc_id
                    """),
                    {
                        "images": page_images_json,
                        "count": len(page_images),
                        "doc_id": doc_id
                    }
                )
                
                # Commit this document
                db.commit()
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    print(f"  ✅ Synced {updated_count} documents...")
            
        except Exception as e:
            print(f"  ❌ Error processing {doc_file.name}: {str(e)[:100]}")
            error_count += 1
            continue
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Documents updated: {updated_count}")
    print(f"Documents skipped (no images): {skipped_no_images}")
    print(f"Documents skipped (not in DB): {skipped_not_in_db}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(doc_files)}")
    print("=" * 80)
    
    return error_count == 0

def main():
    """Run the sync."""
    load_dotenv()
    
    # Check database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else 'local'}\n")
    
    # Run sync
    success = sync_images_to_database()
    
    if success:
        print("\n🎉 Sync completed successfully!")
    else:
        print("\n⚠️ Sync completed with some errors")

if __name__ == '__main__':
    main()

