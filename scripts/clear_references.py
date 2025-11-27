#!/usr/bin/env python3

"""
Clear all existing references from the database.
This script removes all people references from metadata and documents.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage


def clear_references(storage_dir: Path):
    """
    Clear all references from metadata and all documents.
    """
    print("="*80)
    print("CLEARING ALL REFERENCES")
    print("="*80)
    
    storage = LocalOCRStorage(str(storage_dir))
    
    # Get counts before clearing
    people_count = len(storage.metadata.get('people', {}))
    doc_count = len(storage.metadata.get('documents', {}))
    
    print(f"\n📊 Current state:")
    print(f"   People references: {people_count}")
    print(f"   Documents: {doc_count}")
    
    if people_count == 0:
        print("\n✅ No references to clear!")
        return
    
    # Confirm action
    print(f"\n⚠️  This will remove {people_count} people references from {doc_count} documents.")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print("\n🔄 Clearing references...")
    
    # Clear people from metadata
    print("   Clearing metadata...")
    storage.metadata['people'] = {}
    
    # Clear people from all documents
    documents_dir = storage.documents_dir
    cleared_count = 0
    
    print("   Clearing documents...")
    for doc_file in documents_dir.glob("*.json"):
        try:
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            
            # Clear people array
            if 'people' in doc_data and len(doc_data['people']) > 0:
                doc_data['people'] = []
                
                with open(doc_file, 'w') as f:
                    json.dump(doc_data, f, indent=2)
                
                cleared_count += 1
        
        except Exception as e:
            print(f"   ⚠️ Error clearing {doc_file.name}: {e}")
    
    # Update document metadata people counts
    for doc_id in storage.metadata['documents']:
        storage.metadata['documents'][doc_id]['people_count'] = 0
    
    # Save metadata
    storage._save_metadata()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Removed {people_count} people references")
    print(f"✅ Cleared references from {cleared_count} documents")
    print(f"✅ Metadata updated")
    print("="*80)


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"❌ Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    clear_references(storage_path)
    print("\n🎉 References cleared successfully!")

