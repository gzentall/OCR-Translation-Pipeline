#!/usr/bin/env python3

"""
Script to reset all documents to 'new' status.
Updates both local storage and optionally the database.
"""

import json
import sys
from pathlib import Path

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage


def reset_all_document_status(storage_dir: Path):
    """Reset all documents to 'new' status."""
    print("="*80)
    print("RESETTING ALL DOCUMENTS TO 'NEW' STATUS")
    print("="*80)
    
    storage = LocalOCRStorage(str(storage_dir))
    
    documents_dir = storage_dir / "documents"
    doc_files = list(documents_dir.glob("*.json"))
    
    print(f"\n📊 Found {len(doc_files)} documents")
    print("\n🔄 Resetting status to 'new'...")
    
    updated_count = 0
    
    for i, doc_file in enumerate(doc_files, 1):
        try:
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            
            # Update status to 'new'
            old_status = doc_data.get('status', 'unknown')
            doc_data['status'] = 'new'
            
            # Write back to file
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            updated_count += 1
            
            if i % 20 == 0:
                print(f"  Processed {i}/{len(doc_files)} documents...")
                
        except Exception as e:
            print(f"  ❌ Error processing {doc_file.name}: {e}")
    
    # Update metadata index
    for doc_id, doc_meta in storage.metadata.get('documents', {}).items():
        doc_meta['status'] = 'new'
    
    storage._save_metadata()
    
    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Total documents reset: {updated_count}/{len(doc_files)}")
    print("All documents now have status: 'new'")
    print("================================================================================")
    print("\n✅ Document status reset complete!")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    reset_all_document_status(storage_path)

