#!/usr/bin/env python3

"""
Script to fix sender/recipient names in documents to match canonical names in people database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage

# Load environment variables
load_dotenv()

# Name mappings: Map all variations to canonical names
# Monsieur Zweigenthal/Elisabeth Zentall → Robert Zentall/Betty Zentall
NAME_MAPPINGS = {
    "Monsieur Zweigenthal": "Robert Zentall",
    "Robert Zweigenthal": "Robert Zentall",
    "robert zweigenthal": "Robert Zentall",
    "Elisabeth Zentall": "Betty Zentall",
    "Elizabeth Zentall": "Betty Zentall",
    "elisabeth zentall": "Betty Zentall",
    "Betty Aigner": "Betty Zentall",
    "Elizabeth Aigner": "Betty Zentall",
    "Elisabeth Aigner": "Betty Zentall",
}

def fix_sender_recipient_names(storage_dir: Path):
    """
    Updates sender/recipient fields in all documents to use canonical names.
    """
    print("="*80)
    print("FIXING SENDER/RECIPIENT NAMES")
    print("="*80)

    storage = LocalOCRStorage(str(storage_dir))

    local_doc_ids = list(storage.metadata.get('documents', {}).keys())
    print(f"\n📊 Found {len(local_doc_ids)} documents")

    updated_count = 0
    skipped_count = 0

    print("\n🔄 Processing documents...")

    for i, doc_id in enumerate(local_doc_ids):
        doc_data = storage.get_document(doc_id)
        if not doc_data:
            print(f"  ⚠️ Document {doc_id} not found in local storage, skipping.")
            skipped_count += 1
            continue

        title = doc_data.get('title', doc_id)
        sender = doc_data.get('sender', '')
        recipient = doc_data.get('recipient', '')

        # Check if we need to update
        new_sender = NAME_MAPPINGS.get(sender, sender)
        new_recipient = NAME_MAPPINGS.get(recipient, recipient)

        if new_sender != sender or new_recipient != recipient:
            print(f"  [{i+1}/{len(local_doc_ids)}] 📄 {title}")
            if new_sender != sender:
                print(f"     🔄 Sender: '{sender}' → '{new_sender}'")
            if new_recipient != recipient:
                print(f"     🔄 Recipient: '{recipient}' → '{new_recipient}'")

            updates = {}
            if new_sender != sender:
                updates['sender'] = new_sender
            if new_recipient != recipient:
                updates['recipient'] = new_recipient

            storage.update_document(doc_id, updates)
            updated_count += 1
        else:
            skipped_count += 1

    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Documents updated: {updated_count}")
    print(f"Documents unchanged: {skipped_count}")
    print("================================================================================")

    print("\n🎉 Sender/recipient names fixed!")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    fix_sender_recipient_names(storage_path)

