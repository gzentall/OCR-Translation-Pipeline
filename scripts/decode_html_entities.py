#!/usr/bin/env python3

"""
Script to decode HTML entities in document texts to actual characters.
Replaces &#39; with ', &amp; with &, etc.
"""

import json
import os
import sys
import html
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load environment variables
load_dotenv()


def decode_html_in_text(text: str) -> str:
    """Decode HTML entities in text."""
    if not text:
        return text
    return html.unescape(text)


def decode_html_entities_in_documents(storage_dir: Path):
    """
    Decode HTML entities in all document JSON files.
    """
    print("="*80)
    print("DECODING HTML ENTITIES IN DOCUMENTS")
    print("="*80)

    documents_dir = storage_dir / "documents"
    
    if not documents_dir.exists():
        print(f"Error: Documents directory not found at {documents_dir}")
        return

    doc_files = list(documents_dir.glob("*.json"))
    print(f"\n📊 Found {len(doc_files)} document files")

    updated_count = 0
    unchanged_count = 0
    
    # Fields to check for HTML entities
    text_fields = [
        'original_text',
        'raw_text', 
        'translated_text',
        'summary',
        'title'
    ]

    print("\n🔄 Processing documents...")

    for i, doc_file in enumerate(doc_files, 1):
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            changed = False
            
            # Decode HTML entities in text fields
            for field in text_fields:
                if field in doc_data and doc_data[field]:
                    original = doc_data[field]
                    decoded = decode_html_in_text(original)
                    
                    if decoded != original:
                        doc_data[field] = decoded
                        changed = True
            
            # Also check people references if they have HTML entities
            if 'people' in doc_data and isinstance(doc_data['people'], list):
                for person in doc_data['people']:
                    if isinstance(person, dict):
                        if 'original_name' in person:
                            original = person['original_name']
                            decoded = decode_html_in_text(original)
                            if decoded != original:
                                person['original_name'] = decoded
                                changed = True
                    elif isinstance(person, str):
                        # Handle string format (legacy)
                        idx = doc_data['people'].index(person)
                        decoded = decode_html_in_text(person)
                        if decoded != person:
                            doc_data['people'][idx] = decoded
                            changed = True
            
            if changed:
                # Save updated document
                with open(doc_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, indent=2, ensure_ascii=False)
                updated_count += 1
                
                if updated_count <= 10:  # Show first 10 updates
                    title = doc_data.get('title', doc_file.name)
                    print(f"  [{i}/{len(doc_files)}] ✅ {title}")
            else:
                unchanged_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing {doc_file.name}: {e}")

    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Documents updated: {updated_count}")
    print(f"Documents unchanged: {unchanged_count}")
    print(f"Total processed: {len(doc_files)}")
    print("================================================================================")

    print("\n🎉 HTML entity decoding complete!")
    print("\nCommon replacements made:")
    print("  &#39; → ' (apostrophe)")
    print("  &amp; → & (ampersand)")
    print("  &quot; → \" (quote)")
    print("  &lt; → < (less than)")
    print("  &gt; → > (greater than)")
    print("  &#[number]; → corresponding character")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    decode_html_entities_in_documents(storage_path)

