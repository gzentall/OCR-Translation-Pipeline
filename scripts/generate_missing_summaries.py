#!/usr/bin/env python3

"""
Generate summaries for documents that are missing them.
Uses AI processor with full context to create comprehensive summaries.
"""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.local_storage import LocalOCRStorage
from scripts.ai_processor import AIProcessor


def load_context():
    """Load reference data for context."""
    context_file = Path(__file__).parent.parent / 'reference_data.json'
    if context_file.exists():
        with open(context_file) as f:
            return json.load(f)
    return {}


def generate_summary_with_context(ai_processor, doc, context):
    """Generate a comprehensive summary using context."""
    # Get text to summarize
    text = doc.get('translated_text') or doc.get('original_text', '')
    if not text:
        return "No text available for summary."
    
    # Build context for the prompt
    people_names = [p.get('name', '') for p in context.get('people', [])][:20]
    places = [p.get('location', '') for p in context.get('places', [])][:15]
    historical_context = context.get('historical_context', [])[:10]
    
    # Create enhanced prompt with context
    prompt = f"""Please write a concise summary (2-3 sentences) of this letter.

Historical Context:
- Key people in this collection: {', '.join(people_names) if people_names else 'Robert and Betty Zentall'}
- Key places: {', '.join(places) if places else 'Prague, Paris, various European cities'}
- Period: {', '.join(str(h) for h in historical_context) if historical_context else '1930s-1950s correspondence'}

Document Information:
- Date: {doc.get('document_date', 'Unknown')}
- Sender: {doc.get('sender', 'Unknown')}
- Recipient: {doc.get('recipient', 'Unknown')}

Letter Text:
{text}

Summary:"""
    
    try:
        summary = ai_processor.generate_summary(prompt)
        if summary and len(summary.strip()) > 10:
            return summary.strip()
        else:
            return f"Summary generation returned empty result."
    except Exception as e:
        return f"Summary generation failed: {str(e)}"


def generate_missing_summaries(storage: LocalOCRStorage):
    """Generate summaries for all documents missing them."""
    print("="*80)
    print("GENERATING MISSING SUMMARIES")
    print("="*80)
    
    # Initialize AI processor and load context
    print("\n🔧 Initializing AI processor and loading context...")
    ai_processor = AIProcessor()
    context = load_context()
    print(f"   Loaded context: {len(context.get('people', []))} people, {len(context.get('places', []))} places")
    
    # Get all documents
    all_docs = storage.list_documents()
    
    # Find documents without summaries
    docs_to_process = []
    for doc_id, metadata in all_docs:
        doc = storage.get_document(doc_id)
        if not doc:
            continue
        
        summary = doc.get('summary', '').strip()
        if not summary:
            title = doc.get('title', '')
            if title:
                parts = title.split('-')
                doc_num = int(parts[0]) if parts[0].isdigit() else 999
            else:
                doc_num = 999
            docs_to_process.append((doc_num, doc_id, title, doc))
    
    # Sort by document number
    docs_to_process.sort(key=lambda x: x[0])
    
    print(f"\n📊 Found {len(docs_to_process)} documents without summaries")
    print()
    
    success_count = 0
    error_count = 0
    
    for i, (doc_num, doc_id, title, doc) in enumerate(docs_to_process, 1):
        print(f"[{i}/{len(docs_to_process)}] #{doc_num:03d} - {title}")
        
        # Check if there's text to summarize
        text = doc.get('translated_text') or doc.get('original_text', '')
        if not text or len(text.strip()) < 20:
            print(f"    ⚠️  Skipping - no text available")
            error_count += 1
            continue
        
        # Generate summary
        try:
            summary = generate_summary_with_context(ai_processor, doc, context)
            
            # Update document
            storage.update_document(doc_id, {'summary': summary})
            
            # Show preview
            preview = summary[:100] + "..." if len(summary) > 100 else summary
            print(f"    ✅ {preview}")
            success_count += 1
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            error_count += 1
    
    print("\n" + "="*80)
    print(f"✅ COMPLETE")
    print(f"   Generated: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total: {len(docs_to_process)}")
    print("="*80)


if __name__ == '__main__':
    storage = LocalOCRStorage()
    generate_missing_summaries(storage)

