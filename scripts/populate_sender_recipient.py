#!/usr/bin/env python3

"""
Populate sender and recipient fields for all documents using LLM.
Uses document text and historical context to identify correspondents.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage

# Load environment variables
load_dotenv()


class SenderRecipientIdentifier:
    """Identify sender and recipient from document content using LLM."""
    
    def __init__(self):
        """Initialize with OpenAI API."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            key_file = Path('.openai_api_key')
            if key_file.exists():
                self.api_key = key_file.read_text().strip()
            else:
                raise ValueError("OpenAI API key not found")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def identify_correspondents(self, text: str, doc_context: Dict = None) -> Dict[str, str]:
        """
        Identify sender and recipient from document text.
        
        Args:
            text: Document text content
            doc_context: Optional context (existing sender/recipient, date, etc.)
        
        Returns:
            Dict with 'sender' and 'recipient' keys
        """
        context_info = ""
        if doc_context:
            date = doc_context.get('document_date', 'unknown')
            existing_sender = doc_context.get('sender')
            existing_recipient = doc_context.get('recipient')
            context_info = f"\nDocument date: {date}"
            if existing_sender:
                context_info += f"\nExisting sender: {existing_sender}"
            if existing_recipient:
                context_info += f"\nExisting recipient: {existing_recipient}"
        
        prompt = f"""You are analyzing WWII-era family correspondence (1932-1950) to identify the sender and recipient.

**KNOWN CORRESPONDENTS:**

PRIMARY PEOPLE:
1. **Robert Zentall** (also known as: Robert Zweigenthal, Bob, Zentall)
   - Soldier in French army during WWII
   - Stationed in Agde, France
   - Later in USA
   - Husband of Betty

2. **Betty Zentall** (also known as: Elizabeth Zentall, Elizabeth Aigner, Betty Zweigenthal, Elizabeth Zweigenthal, Baba)
   - Wife of Robert
   - Lived in Paris, France
   - Later in USA
   - Maiden name: Aigner

OTHER FAMILY MEMBERS:
- Hans Aigner (Betty's father)
- Josef Aigner (Betty's relative)
- Various other family members and friends

**YOUR TASK:**
Analyze this document and identify:
1. **Who is writing** (sender)
2. **Who is receiving** (recipient)

**ANALYSIS RULES:**
- Look for salutations like "Dear Betty", "My Dear Bob", "Chère Baba"
- Look for closings/signatures like "Your loving husband", "Love, Betty", "Bob"
- Consider the tone and content (military updates → likely from Robert)
- Consider locations mentioned (if from military camp → Robert; if from Paris → Betty)
- Use the existing data if it looks correct
- Return the FULL NAME (prefer "Robert Zentall" or "Betty Zentall")
- If uncertain but can make an educated guess, do so with the most likely option
- Only return "Unknown" if truly impossible to determine{context_info}

**Document text:**
{text[:3000]}

Return ONLY valid JSON in this exact format:
{{
  "sender": "Full Name",
  "recipient": "Full Name",
  "confidence": "high|medium|low",
  "reasoning": "brief explanation of how you identified them"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a historical document analyst specializing in WWII-era correspondence. You identify document senders and recipients with high accuracy by analyzing salutations, closings, content, and context. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            return {
                'sender': result.get('sender', 'Unknown'),
                'recipient': result.get('recipient', 'Unknown'),
                'confidence': result.get('confidence', 'low'),
                'reasoning': result.get('reasoning', '')
            }
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️ JSON decode error: {e}")
            return {
                'sender': 'Unknown',
                'recipient': 'Unknown',
                'confidence': 'low',
                'reasoning': 'Error parsing LLM response'
            }
        except Exception as e:
            print(f"  ❌ Error identifying correspondents: {e}")
            return {
                'sender': 'Unknown',
                'recipient': 'Unknown',
                'confidence': 'low',
                'reasoning': f'Error: {str(e)}'
            }


def populate_all_documents(storage_dir: Path, force: bool = False, limit: int = None):
    """
    Populate sender and recipient for all documents.
    
    Args:
        storage_dir: Path to ocr_storage directory
        force: If True, re-process documents that already have sender/recipient
        limit: Optional limit on number of documents to process (for testing)
    """
    print("="*80)
    print("IDENTIFYING SENDER AND RECIPIENT FOR ALL DOCUMENTS")
    print("="*80)
    
    storage = LocalOCRStorage(str(storage_dir))
    identifier = SenderRecipientIdentifier()
    
    # Get all documents
    all_doc_ids = list(storage.metadata.get('documents', {}).keys())
    print(f"\n📊 Found {len(all_doc_ids)} documents")
    
    if limit:
        all_doc_ids = all_doc_ids[:limit]
        print(f"   Processing first {limit} documents (test mode)")
    
    # Statistics
    stats = {
        'documents_processed': 0,
        'documents_updated': 0,
        'documents_skipped': 0,
        'documents_failed': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0
    }
    
    print(f"\n🔄 Processing documents...")
    if not force:
        print("   (Skipping documents that already have sender and recipient)")
    
    for idx, doc_id in enumerate(all_doc_ids, 1):
        try:
            # Load document
            doc_data = storage.get_document(doc_id)
            if not doc_data:
                print(f"  [{idx}/{len(all_doc_ids)}] ⚠️ Document {doc_id} not found")
                stats['documents_failed'] += 1
                continue
            
            title = doc_data.get('title', doc_id)[:50]
            
            # Check if already has sender/recipient (unless force=True)
            has_sender = doc_data.get('sender') and doc_data.get('sender') != 'Unknown'
            has_recipient = doc_data.get('recipient') and doc_data.get('recipient') != 'Unknown'
            
            if has_sender and has_recipient and not force:
                print(f"  [{idx}/{len(all_doc_ids)}] ⏭️  {title} (already has sender/recipient)")
                stats['documents_skipped'] += 1
                continue
            
            print(f"\n  [{idx}/{len(all_doc_ids)}] 📄 {title}")
            
            # Get text (prefer corrected, fallback to original, then raw)
            text = (doc_data.get('corrected_text') or 
                   doc_data.get('original_text') or 
                   doc_data.get('raw_text') or '')
            
            if not text:
                print(f"     ⚠️ No text content found")
                stats['documents_failed'] += 1
                continue
            
            # Build context
            doc_context = {
                'document_date': doc_data.get('document_date'),
                'sender': doc_data.get('sender'),
                'recipient': doc_data.get('recipient')
            }
            
            # Identify correspondents
            result = identifier.identify_correspondents(text, doc_context)
            
            sender = result['sender']
            recipient = result['recipient']
            confidence = result['confidence']
            reasoning = result['reasoning']
            
            # Update stats
            stats[f'{confidence}_confidence'] += 1
            
            print(f"     ✅ Sender: {sender}")
            print(f"     ✅ Recipient: {recipient}")
            print(f"     📊 Confidence: {confidence}")
            if reasoning:
                print(f"     💭 Reasoning: {reasoning[:80]}...")
            
            # Update document
            updates = {
                'sender': sender,
                'recipient': recipient
            }
            
            success = storage.update_document(doc_id, updates)
            
            if success:
                stats['documents_updated'] += 1
            else:
                print(f"     ⚠️ Failed to update document")
                stats['documents_failed'] += 1
            
            stats['documents_processed'] += 1
            
        except Exception as e:
            print(f"     ❌ Error processing document: {e}")
            stats['documents_failed'] += 1
            continue
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Documents updated: {stats['documents_updated']}")
    print(f"Documents skipped: {stats['documents_skipped']}")
    print(f"Documents failed: {stats['documents_failed']}")
    print(f"\nConfidence levels:")
    print(f"  🟢 High confidence: {stats['high_confidence']}")
    print(f"  🟡 Medium confidence: {stats['medium_confidence']}")
    print(f"  🔴 Low confidence: {stats['low_confidence']}")
    print("="*80)
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate sender and recipient fields')
    parser.add_argument('--force', action='store_true',
                       help='Re-process documents that already have sender/recipient')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of documents to process (for testing)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only first 5 documents')
    
    args = parser.parse_args()
    
    limit = args.limit
    if args.test:
        limit = 5
    
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"❌ Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    try:
        stats = populate_all_documents(storage_path, force=args.force, limit=limit)
        print("\n🎉 Sender/recipient identification complete!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

