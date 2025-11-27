#!/usr/bin/env python3

"""
Populate sender and recipient locations for all documents using envelope extraction.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.local_storage import LocalOCRStorage
from scripts.envelope_extractor import EnvelopeExtractor

def populate_locations():
    """Extract and populate location data for all documents."""
    
    load_dotenv()
    
    print("=" * 80)
    print("POPULATING DOCUMENT LOCATIONS FROM ENVELOPE TEXT")
    print("=" * 80)
    
    # Initialize storage and extractor
    storage = LocalOCRStorage()
    extractor = EnvelopeExtractor()
    
    # Get all documents
    documents = storage.list_documents()
    print(f"📊 Found {len(documents)} documents\n")
    
    updated_count = 0
    skipped_no_text = 0
    skipped_already_set = 0
    error_count = 0
    
    for doc_id, doc_metadata in documents:
        try:
            # Get full document
            doc = storage.get_document(doc_id)
            if not doc:
                print(f"  ⚠️ Could not load document: {doc_id}")
                error_count += 1
                continue
            
            title = doc.get('title', doc_id)[:60]
            
            # Skip if both locations already set
            if doc.get('sender_location') and doc.get('recipient_location'):
                skipped_already_set += 1
                continue
            
            # Get text from available fields (try multiple field names)
            original_text = doc.get('original_text') or doc.get('raw_text') or doc.get('corrected_text') or ''
            if not original_text or len(original_text.strip()) < 50:
                skipped_no_text += 1
                continue
            
            print(f"📄 Processing: {title}")
            
            # Extract envelope metadata using LLM
            envelope_data = extractor.extract_metadata(original_text, doc_id)
            
            # Check if envelope was found
            if not envelope_data.get('sender') or not envelope_data.get('receiver'):
                print(f"  ⚠️ No clear envelope data found")
                continue
            
            # Prepare updates
            updates = {}
            
            # Update sender location if not set
            if not doc.get('sender_location') and envelope_data.get('sender_location'):
                updates['sender_location'] = envelope_data['sender_location']
                print(f"  ✅ Sender location: {envelope_data['sender_location']}")
            
            # Update recipient location if not set
            if not doc.get('recipient_location') and envelope_data.get('receiver_location'):
                updates['recipient_location'] = envelope_data['receiver_location']
                print(f"  ✅ Recipient location: {envelope_data['receiver_location']}")
            
            # Update sender if not set
            if not doc.get('sender') and envelope_data.get('sender'):
                updates['sender'] = envelope_data['sender']
                print(f"  ✅ Sender: {envelope_data['sender']}")
            
            # Update recipient if not set
            if not doc.get('recipient') and envelope_data.get('receiver'):
                updates['recipient'] = envelope_data['receiver']
                print(f"  ✅ Recipient: {envelope_data['receiver']}")
            
            # Save updates if any
            if updates:
                success = storage.update_document(doc_id, updates)
                if success:
                    updated_count += 1
                    print(f"  ✅ Updated document")
                else:
                    print(f"  ❌ Failed to update document")
                    error_count += 1
            else:
                print(f"  ℹ️ No new data to update")
            
            print()  # Blank line between documents
            
        except Exception as e:
            print(f"  ❌ Error processing {doc_id}: {str(e)[:100]}")
            error_count += 1
            continue
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Documents updated: {updated_count}")
    print(f"Documents skipped (already set): {skipped_already_set}")
    print(f"Documents skipped (no text): {skipped_no_text}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(documents)}")
    print("=" * 80)
    
    return error_count == 0

def main():
    """Run the location population."""
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set in environment")
        print("Please set it in your .env file or export it:")
        print("  export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    success = populate_locations()
    
    if success:
        print("\n🎉 Location population completed successfully!")
        print("   Restart the Flask app to see the updated locations.")
    else:
        print("\n⚠️ Location population completed with some errors")

if __name__ == '__main__':
    main()

