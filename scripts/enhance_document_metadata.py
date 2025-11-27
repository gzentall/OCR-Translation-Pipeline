#!/usr/bin/env python3

"""
Enhance document metadata using LLM with full context.
- Extract/refine references using context
- Identify sender/recipient with context
- Extract locations from envelope addresses
- Regenerate summaries with enhanced context
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load environment variables
load_dotenv()

from scripts.local_storage import LocalOCRStorage
from scripts.envelope_extractor import EnvelopeExtractor
from scripts.geoapify_client import GeoapifyClient
from scripts.ai_processor import AIProcessor
from scripts.extract_references import ReferenceExtractor


class DocumentMetadataEnhancer:
    """Enhance document metadata using LLM with context."""
    
    def __init__(self):
        self.storage = LocalOCRStorage()
        self.envelope_extractor = EnvelopeExtractor()
        self.geoapify = GeoapifyClient()
        self.ai_processor = AIProcessor()
        self.reference_extractor = ReferenceExtractor()
        
        # Load context
        context_file = Path(__file__).parent.parent / 'context' / 'reference_data.json'
        with open(context_file, 'r') as f:
            self.context = json.load(f)
    
    def enhance_document(self, doc_id: str) -> bool:
        """
        Enhance a single document's metadata.
        Returns True if successful, False otherwise.
        """
        try:
            # Get document
            doc = self.storage.get_document(doc_id)
            if not doc:
                print(f"  ❌ Document not found: {doc_id}")
                return False
            
            title = doc.get('title', doc_id)
            print(f"\n📄 {title}")
            
            # Use translated text for analysis (it's in English)
            text = doc.get('translated_text', '')
            original_text = doc.get('corrected_text', doc.get('original_text', ''))
            
            if not text:
                print(f"  ⚠️  No translated text available")
                return False
            
            # Prepare metadata for context
            metadata = {
                'document_date': doc.get('document_date'),
                'source_language': doc.get('source_language', 'de'),
                'current_sender': doc.get('sender'),
                'current_recipient': doc.get('recipient')
            }
            
            changes_made = []
            
            # 1. Extract/refine sender and recipient from envelope
            print(f"  🔍 Identifying sender/recipient...")
            envelope_data = self.envelope_extractor.extract_metadata(original_text, metadata)
            
            if envelope_data.get('sender') and envelope_data['sender'] != 'Unknown':
                if doc.get('sender') != envelope_data['sender']:
                    doc['sender'] = envelope_data['sender']
                    changes_made.append(f"sender: {envelope_data['sender']}")
                    print(f"    ✓ Sender: {envelope_data['sender']}")
            
            # FIX: envelope_extractor returns 'receiver' not 'recipient'
            if envelope_data.get('receiver') and envelope_data['receiver'] != 'Unknown':
                if doc.get('recipient') != envelope_data['receiver']:
                    doc['recipient'] = envelope_data['receiver']
                    changes_made.append(f"recipient: {envelope_data['receiver']}")
                    print(f"    ✓ Recipient: {envelope_data['receiver']}")
            
            # 2. Extract locations from envelope addresses with European bias for pre-1945 documents
            print(f"  📍 Extracting locations...")
            
            # Determine if document is pre-1945 (European correspondence)
            doc_date = doc.get('document_date', '')
            is_pre_1945 = False
            
            # Try to extract year from document_date field
            if doc_date:
                try:
                    year = int(doc_date.split('-')[0]) if '-' in doc_date else int(doc_date[:4])
                    is_pre_1945 = year < 1945
                except:
                    pass
            
            # Fallback: Extract year from filename (e.g., "125-1935-05-27-ger" -> 1935)
            if not is_pre_1945 and not doc_date:
                title = doc.get('title', '')
                try:
                    # Title format: number-YYYY-MM-DD-lang
                    parts = title.split('-')
                    if len(parts) >= 4 and parts[1].isdigit() and len(parts[1]) == 4:
                        year = int(parts[1])
                        is_pre_1945 = year < 1945
                        print(f"    ℹ️  Extracted year {year} from filename (pre-1945: {is_pre_1945})")
                except:
                    pass
            
            # Additional fallback: German/French source suggests pre-1945 European context
            if not is_pre_1945 and doc.get('source_language') in ['de', 'fr', 'ger', 'fre']:
                is_pre_1945 = True
                print(f"    ℹ️  Using European bias based on source language: {doc.get('source_language')}")
            
            if envelope_data.get('sender_location') and envelope_data['sender_location'] != 'Unknown':
                # Use European bias for pre-1945 documents
                location_result = self.geoapify.geocode_address(
                    envelope_data['sender_location'], 
                    prefer_european=is_pre_1945
                )
                
                if location_result:
                    doc['sender_location'] = location_result
                    changes_made.append(f"sender_location: {location_result.get('formatted', 'N/A')}")
                    print(f"    ✓ Sender location: {location_result.get('formatted', 'N/A')}")
            
            # FIX: envelope_extractor returns 'receiver_location' not 'recipient_location'
            if envelope_data.get('receiver_location') and envelope_data['receiver_location'] != 'Unknown':
                # Use European bias for pre-1945 documents
                location_result = self.geoapify.geocode_address(
                    envelope_data['receiver_location'],
                    prefer_european=is_pre_1945
                )
                
                if location_result:
                    doc['recipient_location'] = location_result
                    changes_made.append(f"recipient_location: {location_result.get('formatted', 'N/A')}")
                    print(f"    ✓ Recipient location: {location_result.get('formatted', 'N/A')}")
            
            # 3. Extract references with context
            print(f"  🏷️  Extracting references...")
            references_result = self.reference_extractor.extract_references_from_text(text, metadata)
            
            # Clear existing references for this document
            existing_refs = doc.get('people', [])
            
            # Remove this document from all existing references
            for ref_name in existing_refs:
                ref_data = self.storage.get_reference(ref_name)
                if ref_data and doc_id in ref_data.get('document_ids', []):
                    ref_data['document_ids'].remove(doc_id)
                    self.storage._save_metadata()
            
            # Add new references
            new_refs = []
            for ref_type, refs in references_result.items():
                for ref_data in refs:
                    ref_name = ref_data.get('name')
                    if ref_name:
                        # Add to global references if not exists
                        existing_ref = self.storage.get_reference(ref_name)
                        if not existing_ref:
                            self.storage.add_reference(
                                ref_type, 
                                ref_name, 
                                aliases=ref_data.get('aliases'),
                                notes=ref_data.get('context')
                            )
                        
                        # Link to document
                        self.storage.add_reference_to_document(doc_id, ref_name, role=ref_type)
                        new_refs.append(ref_name)
            
            doc['people'] = new_refs
            if new_refs:
                changes_made.append(f"references: {len(new_refs)} added")
                print(f"    ✓ References: {len(new_refs)} identified")
            
            # 4. Regenerate summary with enhanced context
            print(f"  📝 Regenerating summary...")
            
            # Extract names from context (handle dict format)
            people_names = []
            people_list = self.context.get('people', [])
            if isinstance(people_list, list):
                for p in people_list[:20]:
                    if isinstance(p, dict):
                        people_names.append(p.get('name', ''))
                    elif isinstance(p, str):
                        people_names.append(p)
            
            places_names = []
            places_list = self.context.get('places', [])
            if isinstance(places_list, list):
                for pl in places_list[:20]:
                    if isinstance(pl, dict):
                        places_names.append(pl.get('name', ''))
                    elif isinstance(pl, str):
                        places_names.append(pl)
            
            historical_context = []
            hist_list = self.context.get('historical_context', [])
            if isinstance(hist_list, list) and len(hist_list) > 0:
                for h in hist_list[:5]:
                    if isinstance(h, dict):
                        historical_context.append(h.get('description', ''))
                    elif isinstance(h, str):
                        historical_context.append(h)
            
            summary_prompt = f"""Analyze this letter and provide a comprehensive summary.

CONTEXT (for reference):
- Known People: {', '.join(people_names)}
- Known Places: {', '.join(places_names)}
- Historical Context: {', '.join(historical_context)}

DOCUMENT METADATA:
- Date: {doc.get('document_date', 'Unknown')}
- From: {doc.get('sender', 'Unknown')}
- To: {doc.get('recipient', 'Unknown')}
- Language: {doc.get('source_language', 'Unknown')}

TRANSLATED TEXT:
{text[:3000]}

Provide a summary covering:
1. WHO: Sender and recipient (use canonical names from context if available)
2. NATURE: Type of correspondence (personal letter, business, etc.)
3. TOPICS: Main themes and subjects discussed
4. CONTEXT: Relevant historical or personal context
5. RELATIONSHIP: Nature of relationship between sender and recipient

Keep the summary concise but informative (3-5 sentences)."""

            try:
                new_summary = self.ai_processor.generate_summary(text[:4000], doc.get('source_language', 'de'))
                if new_summary and new_summary != doc.get('summary'):
                    doc['summary'] = new_summary.strip()
                    changes_made.append("summary: regenerated")
                    print(f"    ✓ Summary regenerated")
            except Exception as e:
                print(f"    ⚠️  Summary generation failed: {e}")
            
            # Save document using update_document
            if changes_made:
                # Prepare updates dict
                updates = {}
                if 'sender' in doc:
                    updates['sender'] = doc['sender']
                if 'recipient' in doc:
                    updates['recipient'] = doc['recipient']
                if 'sender_location' in doc:
                    updates['sender_location'] = doc['sender_location']
                if 'recipient_location' in doc:
                    updates['recipient_location'] = doc['recipient_location']
                if 'summary' in doc:
                    updates['summary'] = doc['summary']
                if 'people' in doc:
                    updates['people'] = doc['people']
                
                self.storage.update_document(doc_id, updates)
                print(f"  ✅ Updated: {', '.join(changes_made)}")
                return True
            else:
                print(f"  ℹ️  No changes needed")
                return False
                
        except Exception as e:
            print(f"  ❌ Error enhancing document: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def enhance_batch(self, start_doc: int, end_doc: int):
        """Enhance a batch of documents by their numeric identifiers."""
        print("="*80)
        print(f"ENHANCING DOCUMENTS {start_doc}-{end_doc}")
        print("="*80)
        
        # Get all documents
        all_docs = self.storage.list_documents()
        
        # Filter to documents in the range
        target_docs = []
        for doc_id, metadata in all_docs:
            title = metadata.get('title', '')
            # Extract numeric part from title (e.g., "150-1934-11-19-ger" -> 150)
            if title:
                parts = title.split('-')
                if parts[0].isdigit():
                    doc_num = int(parts[0])
                    if start_doc <= doc_num <= end_doc:
                        target_docs.append((doc_num, doc_id, title))
        
        # Sort by document number
        target_docs.sort(key=lambda x: x[0])
        
        print(f"\n📊 Found {len(target_docs)} documents to enhance")
        print(f"Range: {target_docs[0][2]} to {target_docs[-1][2]}")
        print()
        
        success_count = 0
        for i, (doc_num, doc_id, title) in enumerate(target_docs, 1):
            print(f"\n[{i}/{len(target_docs)}] Processing {title}...")
            if self.enhance_document(doc_id):
                success_count += 1
        
        print("\n" + "="*80)
        print("ENHANCEMENT COMPLETE")
        print("="*80)
        print(f"✅ Successfully enhanced: {success_count}/{len(target_docs)} documents")
        print(f"📊 Total documents in system: {len(all_docs)}")
        print("="*80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance document metadata using LLM')
    parser.add_argument('--start', type=int, default=108, help='Start document number')
    parser.add_argument('--end', type=int, default=177, help='End document number')
    parser.add_argument('--doc', type=str, help='Single document ID to enhance')
    
    args = parser.parse_args()
    
    enhancer = DocumentMetadataEnhancer()
    
    if args.doc:
        # Enhance single document
        print(f"Enhancing single document: {args.doc}")
        enhancer.enhance_document(args.doc)
    else:
        # Enhance batch
        enhancer.enhance_batch(args.start, args.end)

