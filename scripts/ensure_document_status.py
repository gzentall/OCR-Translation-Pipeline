#!/usr/bin/env python3

"""
Script to ensure all documents have a status field set to 'new'.
Updates documents that are missing the status field.
"""

import json
import sys
from pathlib import Path

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage


def ensure_document_status(storage_dir: Path):
    """Ensure all documents have a status field set to 'new'."""
    print("="*80)
    print("ENSURING ALL DOCUMENTS HAVE STATUS FIELD")
    print("="*80)
    
    storage = LocalOCRStorage(str(storage_dir))
    
    documents_dir = storage_dir / "documents"
    doc_files = list(documents_dir.glob("*.json"))
    
    print(f"\n📊 Found {len(doc_files)} documents")
    print("\n🔄 Checking and updating status fields...")
    
    updated_count = 0
    already_had_status = 0
    
    for i, doc_file in enumerate(doc_files, 1):
        try:
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            
            # Check if status field exists
            if 'status' not in doc_data or doc_data.get('status') is None or doc_data.get('status') == '':
                # Set status to 'new'
                doc_data['status'] = 'new'
                
                # Write back to file
                with open(doc_file, 'w') as f:
                    json.dump(doc_data, f, indent=2)
                
                updated_count += 1
                if i % 20 == 0:
                    print(f"  Updated {updated_count} documents so far...")
            else:
                already_had_status += 1
                
        except Exception as e:
            print(f"  ❌ Error processing {doc_file.name}: {e}")
    
    # Update metadata index to ensure status is reflected
    for doc_id, doc_meta in storage.metadata.get('documents', {}).items():
        if 'status' not in doc_meta or doc_meta.get('status') is None or doc_meta.get('status') == '':
            doc_meta['status'] = 'new'
    
    storage._save_metadata()
    
    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Total documents processed: {len(doc_files)}")
    print(f"Documents updated with status 'new': {updated_count}")
    print(f"Documents that already had status: {already_had_status}")
    print("================================================================================")
    print("\n✅ All documents now have a status field!")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    ensure_document_status(storage_path)

