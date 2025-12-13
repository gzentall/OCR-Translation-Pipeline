#!/usr/bin/env python3

"""
Reconstruct corrupted OCR and translate using GPT-4.
For documents where the OCR output is too corrupted for Google Translate.

Usage: python scripts/reconstruct_and_translate.py doc_20251201_134055
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import openai

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
load_dotenv()


def reconstruct_and_translate(doc_id: str):
    """Use GPT-4 to reconstruct and translate a document."""
    
    # Initialize OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    client = openai.OpenAI(api_key=api_key)
    
    # Load document
    doc_path = Path(f'ocr_storage/documents/{doc_id}.json')
    if not doc_path.exists():
        print(f"❌ Document not found: {doc_path}")
        return False
    
    with open(doc_path) as f:
        doc = json.load(f)
    
    raw_text = doc.get('raw_text', '')
    if not raw_text:
        print("❌ No raw_text found")
        return False
    
    title = doc.get('title', doc_id)
    language = doc.get('language', 'fre')
    
    # Map language codes
    lang_names = {
        'fre': 'French',
        'ger': 'German',
        'spa': 'Spanish',
        'ita': 'Italian',
        'pol': 'Polish',
        'rus': 'Russian',
    }
    lang_name = lang_names.get(language, 'French')
    
    print(f"Document: {title}")
    print(f"Language: {lang_name}")
    print(f"Raw text length: {len(raw_text)} chars")
    print(f"\nRaw text preview:\n{raw_text[:400]}...\n")
    
    # Build prompt
    prompt = f"""You are an expert at reading corrupted OCR output from handwritten {lang_name} letters from the 1940s.

Below is OCR output from a handwritten {lang_name} letter. The OCR is corrupted with:
- Garbled characters
- Mixed language fragments  
- Cyrillic/Russian characters that should be {lang_name}
- Line breaks in wrong places
- Misrecognized letters

Your task:
1. RECONSTRUCT the original {lang_name} text as it was likely written
2. TRANSLATE the reconstructed text to English

OCR OUTPUT:
\"\"\"
{raw_text}
\"\"\"

Respond with JSON:
{{
  "original_text": "The reconstructed original {lang_name} text, clean and readable with proper punctuation",
  "translated_text": "The complete English translation"
}}

Important:
- This is a personal letter from WWII era (1942)
- Common topics: health, daily life, family news, travel, wartime conditions
- Reconstruct logical {lang_name} sentences from the garbled OCR
- Translate EVERYTHING to proper English
- If a word is truly unclear, make your best guess based on context"""

    print("🤖 Using GPT-4 to reconstruct and translate...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an expert in {lang_name} handwriting from historical documents. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=6000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        original = result.get('original_text', '')
        translated = result.get('translated_text', '')
        
        if not original or not translated:
            print("❌ GPT-4 returned empty result")
            return False
        
        print(f"\n✅ Reconstruction complete!")
        print(f"\n{'='*60}")
        print(f"ORIGINAL {lang_name.upper()} ({len(original)} chars):")
        print(f"{'='*60}")
        print(original[:1000])
        if len(original) > 1000:
            print("\n[...truncated...]")
        
        print(f"\n{'='*60}")
        print(f"ENGLISH TRANSLATION ({len(translated)} chars):")
        print(f"{'='*60}")
        print(translated[:1000])
        if len(translated) > 1000:
            print("\n[...truncated...]")
        
        # Update document
        doc['original_text'] = original
        doc['translated_text'] = translated
        # Keep raw_text for reference
        
        with open(doc_path, 'w') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Document saved: {doc_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/reconstruct_and_translate.py <doc_id>")
        print("Example: python scripts/reconstruct_and_translate.py doc_20251201_134055")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    success = reconstruct_and_translate(doc_id)
    sys.exit(0 if success else 1)

