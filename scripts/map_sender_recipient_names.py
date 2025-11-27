#!/usr/bin/env python3

"""
Map extracted sender/recipient names to canonical reference names.
Many names extracted from envelopes are OCR errors or alternate names.
"""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.local_storage import LocalOCRStorage


# Mapping of extracted names to canonical names
NAME_MAPPING = {
    # Elisabeth Aigner is Betty Zentall's maiden name
    'Elisabeth Aigner': 'Betty Zentall',
    'Elizabeth Aigner': 'Betty Zentall',
    'Elisabeth Bigner': 'Betty Zentall',  # OCR error
    'Elisabeth Rigner': 'Betty Zentall',  # OCR error
    'Elisabeth Signer': 'Betty Zentall',  # OCR error
    'Elisabeth Aiguer': 'Betty Zentall',  # OCR error
    'Elisabeth Higner': 'Betty Zentall',  # OCR error
    'Elisabeth Zentall': 'Betty Zentall',
    'Elizabeth Zentall': 'Betty Zentall',
    'E. Aigner': 'Betty Zentall',
    'E. Aigner Zweigenthal': 'Betty Zentall',
    
    # Bob is Robert Zentall's nickname
    'Bob': 'Robert Zentall',
    'Bob Zweigenthal': 'Robert Zentall',
    'Bob Zentall': 'Robert Zentall',
    
    # Laci is a nickname (possibly Robert)
    'Laci': 'Robert Zentall',
    
    # Armin is a family member - keep as is but ensure it's in references
    'Armin Zweigenthal': 'Armin Zweigenthal',
    
    # Hein Bole - keep as is
    'Hein Bole': 'Hein Bole',
    
    # Mrs. variations
    'Mrs. Robert Zentall': 'Betty Zentall',
    'Mrs. Rob. Zentall': 'Betty Zentall',
}


def map_sender_recipient_names(storage: LocalOCRStorage, start_doc: int, end_doc: int):
    """Map sender/recipient names to canonical names."""
    print("="*80)
    print(f"MAPPING SENDER/RECIPIENT NAMES (Documents {start_doc}-{end_doc})")
    print("="*80)
    
    # Get all documents
    all_docs = storage.list_documents()
    
    # Filter to target range
    target_docs = []
    for doc_id, metadata in all_docs:
        title = metadata.get('title', '')
        if title:
            parts = title.split('-')
            if parts[0].isdigit():
                doc_num = int(parts[0])
                if start_doc <= doc_num <= end_doc:
                    target_docs.append((doc_num, doc_id, title))
    
    target_docs.sort(key=lambda x: x[0])
    
    print(f"\n📊 Found {len(target_docs)} documents to process")
    print()
    
    updated_count = 0
    
    for i, (doc_num, doc_id, title) in enumerate(target_docs, 1):
        doc = storage.get_document(doc_id)
        if not doc:
            continue
        
        changes = []
        
        # Map sender
        sender = doc.get('sender')
        if sender and sender in NAME_MAPPING:
            mapped_name = NAME_MAPPING[sender]
            if mapped_name != sender:
                doc['sender'] = mapped_name
                changes.append(f"sender: {sender} → {mapped_name}")
        
        # Map recipient
        recipient = doc.get('recipient')
        if recipient and recipient in NAME_MAPPING:
            mapped_name = NAME_MAPPING[recipient]
            if mapped_name != recipient:
                doc['recipient'] = mapped_name
                changes.append(f"recipient: {recipient} → {mapped_name}")
        
        # Clear "Unknown" values
        if doc.get('sender') == 'Unknown':
            doc['sender'] = None
            changes.append("sender: cleared 'Unknown'")
        
        if doc.get('recipient') == 'Unknown':
            doc['recipient'] = None
            changes.append("recipient: cleared 'Unknown'")
        
        # Save if changed
        if changes:
            storage.update_document(doc_id, {
                'sender': doc.get('sender'),
                'recipient': doc.get('recipient')
            })
            updated_count += 1
            print(f"[{i}/{len(target_docs)}] {title}")
            for change in changes:
                print(f"    • {change}")
    
    print("\n" + "="*80)
    print(f"✅ Updated {updated_count}/{len(target_docs)} documents")
    print("="*80)


if __name__ == '__main__':
    storage = LocalOCRStorage()
    map_sender_recipient_names(storage, 108, 177)

