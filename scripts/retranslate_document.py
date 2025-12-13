#!/usr/bin/env python3

"""
Re-translate a specific document using Google Translate.
Usage: python scripts/retranslate_document.py doc_20251201_134055
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
load_dotenv()

from scripts.translate_google import translate_text


def retranslate_document(doc_id: str):
    """Re-translate a document."""
    
    # Load document
    doc_path = Path(f'ocr_storage/documents/{doc_id}.json')
    if not doc_path.exists():
        print(f"❌ Document not found: {doc_path}")
        return False
    
    with open(doc_path) as f:
        doc = json.load(f)
    
    print(f"Document: {doc.get('title')}")
    print(f"Language: {doc.get('language', 'unknown')}")
    
    # Get the raw OCR text (this is what should be translated)
    raw_text = doc.get('raw_text', '')
    if not raw_text:
        print("❌ No raw_text found in document")
        return False
    
    print(f"\nRaw text length: {len(raw_text)} chars")
    print(f"Raw text preview:\n{raw_text[:300]}...\n")
    
    # Determine source language
    lang = doc.get('language', 'fre')
    lang_map = {
        'fre': 'fr',
        'ger': 'de',
        'spa': 'es',
        'ita': 'it',
        'pol': 'pl',
        'rus': 'ru',
    }
    source_lang = lang_map.get(lang, lang)
    
    # Translate
    print(f"🌐 Translating from {source_lang} to English...")
    
    try:
        result = translate_text(raw_text, target_language='en', source_language=source_lang)
        
        # Handle tuple/list return
        if isinstance(result, (list, tuple)):
            translated = result[0] if result else ''
        else:
            translated = result
        
        if translated:
            print(f"✅ Translation complete!")
            print(f"   Translated length: {len(translated)} chars")
            print(f"\n--- Translation preview ---")
            print(translated[:600])
            print("...\n")
            
            # Update document
            doc['translated_text'] = translated
            doc['original_text'] = raw_text  # Set original to the actual raw text
            
            # Save
            with open(doc_path, 'w') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            print(f"✅ Document saved: {doc_path}")
            return True
        else:
            print("❌ Translation returned empty")
            return False
            
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/retranslate_document.py <doc_id>")
        print("Example: python scripts/retranslate_document.py doc_20251201_134055")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    success = retranslate_document(doc_id)
    sys.exit(0 if success else 1)

