#!/usr/bin/env python3

"""
Extract and categorize references from all documents using LLM.
Extracts: People, Places, Events, Themes, and Emotions.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import openai
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage

# Load environment variables
load_dotenv()


class ReferenceExtractor:
    """Extract and categorize references from documents using LLM."""
    
    def __init__(self):
        """Initialize the reference extractor with OpenAI API."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            # Try reading from file
            key_file = Path('.openai_api_key')
            if key_file.exists():
                self.api_key = key_file.read_text().strip()
            else:
                raise ValueError("OpenAI API key not found")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def extract_references_from_text(self, text: str, doc_context: Dict = None) -> Dict[str, List[Dict]]:
        """
        Extract all references from text and categorize them.
        
        Returns:
            Dict with keys: people, places, events, themes, emotions
        """
        context_info = ""
        if doc_context:
            date = doc_context.get('document_date', 'unknown')
            sender = doc_context.get('sender', 'unknown')
            recipient = doc_context.get('recipient', 'unknown')
            context_info = f"\nDocument context: Date: {date}, From: {sender}, To: {recipient}"
        
        prompt = f"""
You are analyzing a historical document from the World War II era (1930s-1940s).
Extract and categorize ALL significant references from this document.{context_info}

**EXTRACTION RULES:**

**PEOPLE** - Extract:
- Full names of individuals mentioned
- Both formal names (e.g., "Robert Wesenthal") and nicknames/informal names (e.g., "Bob")
- Family relationships (e.g., "Mother", "Uncle Hans")
- Professional titles with names (e.g., "Dr. Schmidt")
- Note: Include BOTH the formal name AND any nicknames/variations as separate entries

**PLACES** - Extract:
- Cities, countries, regions (e.g., "Paris", "France", "Alsace")
- Specific addresses or locations (e.g., "123 Main Street")
- Landmarks or buildings (e.g., "Hotel de Ville")
- Geographic features (e.g., "Rhine River")

**EVENTS** - Extract:
- Historical events mentioned (e.g., "War", "Occupation", "Liberation")
- Personal events (e.g., "Wedding", "Birthday", "Move to America")
- Specific dated occurrences (e.g., "July 1940 evacuation")

**THEMES** - Extract:
- Main topics or subjects discussed (e.g., "Family separation", "Immigration", "Financial hardship")
- Recurring concepts (e.g., "Hope", "Safety", "Reunion")
- Document types (e.g., "Letter to family", "Legal document", "Travel papers")

**EMOTIONS** - Extract:
- Dominant emotional tones (e.g., "Worry", "Relief", "Longing", "Fear")
- Emotional states of people mentioned
- Overall sentiment of the document

Return ONLY valid JSON in this exact format:
{{
  "people": [
    {{"name": "Full Name", "context": "brief context about role or relationship"}},
    {{"name": "Nickname", "context": "informal name for [Full Name]"}}
  ],
  "places": [
    {{"name": "Place Name", "context": "why this place is mentioned"}}
  ],
  "events": [
    {{"name": "Event Name", "context": "what happened"}}
  ],
  "themes": [
    {{"name": "Theme Name", "context": "why this theme is significant"}}
  ],
  "emotions": [
    {{"name": "Emotion Name", "context": "how this emotion is expressed"}}
  ]
}}

Document text:
{text[:4000]}

Extract references as JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a historical document analyst specializing in extracting structured information from WWII-era correspondence. You extract people, places, events, themes, and emotions with historical accuracy. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            # Ensure all keys exist
            for key in ['people', 'places', 'events', 'themes', 'emotions']:
                if key not in result:
                    result[key] = []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️ JSON decode error: {e}")
            return {
                'people': [],
                'places': [],
                'events': [],
                'themes': [],
                'emotions': []
            }
        except Exception as e:
            print(f"  ❌ Error extracting references: {e}")
            return {
                'people': [],
                'places': [],
                'events': [],
                'themes': [],
                'emotions': []
            }


def process_all_documents(storage_dir: Path, limit: int = None):
    """
    Process all documents and extract references.
    
    Args:
        storage_dir: Path to ocr_storage directory
        limit: Optional limit on number of documents to process (for testing)
    """
    print("="*80)
    print("EXTRACTING REFERENCES FROM DOCUMENTS")
    print("="*80)
    
    storage = LocalOCRStorage(str(storage_dir))
    extractor = ReferenceExtractor()
    
    # Get all documents
    all_doc_ids = list(storage.metadata.get('documents', {}).keys())
    print(f"\n📊 Found {len(all_doc_ids)} documents")
    
    if limit:
        all_doc_ids = all_doc_ids[:limit]
        print(f"   Processing first {limit} documents (test mode)")
    
    # Statistics
    stats = {
        'documents_processed': 0,
        'documents_failed': 0,
        'people_extracted': 0,
        'places_extracted': 0,
        'events_extracted': 0,
        'themes_extracted': 0,
        'emotions_extracted': 0
    }
    
    # Track all unique references
    all_references = {
        'people': {},      # name -> {aliases, context, type, documents}
        'places': {},
        'events': {},
        'themes': {},
        'emotions': {}
    }
    
    print(f"\n🔄 Processing documents...")
    
    for idx, doc_id in enumerate(all_doc_ids, 1):
        try:
            # Load document
            doc_data = storage.get_document(doc_id)
            if not doc_data:
                print(f"  [{idx}/{len(all_doc_ids)}] ⚠️ Document {doc_id} not found")
                stats['documents_failed'] += 1
                continue
            
            title = doc_data.get('title', doc_id)[:50]
            print(f"\n  [{idx}/{len(all_doc_ids)}] 📄 {title}")
            
            # Get text (prefer corrected, fallback to original, then raw)
            text = (doc_data.get('corrected_text') or 
                   doc_data.get('original_text') or 
                   doc_data.get('raw_text') or '')
            
            if not text:
                print(f"     ⚠️ No text content found")
                stats['documents_failed'] += 1
                continue
            
            # Extract references
            doc_context = {
                'document_date': doc_data.get('document_date'),
                'sender': doc_data.get('sender'),
                'recipient': doc_data.get('recipient')
            }
            
            references = extractor.extract_references_from_text(text, doc_context)
            
            # Track extracted references
            ref_counts = {
                'people': len(references.get('people', [])),
                'places': len(references.get('places', [])),
                'events': len(references.get('events', [])),
                'themes': len(references.get('themes', [])),
                'emotions': len(references.get('emotions', []))
            }
            
            print(f"     ✅ People: {ref_counts['people']}, Places: {ref_counts['places']}, " +
                  f"Events: {ref_counts['events']}, Themes: {ref_counts['themes']}, " +
                  f"Emotions: {ref_counts['emotions']}")
            
            # Update document with people references (for backward compatibility)
            people_for_doc = []
            for person in references.get('people', []):
                person_name = person.get('name', '').strip()
                if person_name:
                    people_for_doc.append(person_name)
                    stats['people_extracted'] += 1
            
            # Add people to document
            doc_file = storage.documents_dir / f"{doc_id}.json"
            if doc_file.exists():
                with open(doc_file, 'r') as f:
                    doc_json = json.load(f)
                
                doc_json['people'] = people_for_doc
                
                with open(doc_file, 'w') as f:
                    json.dump(doc_json, f, indent=2)
            
            # Aggregate all references
            for ref_type, refs in references.items():
                for ref in refs:
                    ref_name = ref.get('name', '').strip()
                    if not ref_name:
                        continue
                    
                    normalized_name = storage.normalize_name(ref_name)
                    
                    if normalized_name not in all_references[ref_type]:
                        all_references[ref_type][normalized_name] = {
                            'name': ref_name,
                            'aliases': [ref_name],
                            'context': ref.get('context', ''),
                            'type': ref_type,
                            'documents': []
                        }
                    
                    # Add document to reference
                    if doc_id not in all_references[ref_type][normalized_name]['documents']:
                        all_references[ref_type][normalized_name]['documents'].append(doc_id)
                    
                    # Update stats
                    if ref_type != 'people':  # Already counted people above
                        stats[f'{ref_type}_extracted'] += 1
            
            stats['documents_processed'] += 1
            
        except Exception as e:
            print(f"     ❌ Error processing document: {e}")
            stats['documents_failed'] += 1
            continue
    
    print(f"\n🔄 Saving references to metadata...")
    
    # Save people references to metadata (for backward compatibility)
    for person_name, person_data in all_references['people'].items():
        storage.metadata['people'][person_name] = {
            'aliases': person_data['aliases'],
            'context': person_data['context'],
            'type': 'person',
            'documents': person_data['documents'],
            'first_mentioned': datetime.now().isoformat()
        }
        
        # Update document metadata people counts
        for doc_id in person_data['documents']:
            if doc_id in storage.metadata['documents']:
                storage.metadata['documents'][doc_id]['people_count'] = len(
                    storage.get_document(doc_id).get('people', [])
                )
    
    # Save all references (including places, events, themes, emotions)
    storage.metadata['references'] = {
        'places': all_references['places'],
        'events': all_references['events'],
        'themes': all_references['themes'],
        'emotions': all_references['emotions']
    }
    
    storage._save_metadata()
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Documents failed: {stats['documents_failed']}")
    print(f"\nReferences extracted:")
    print(f"  👥 People: {len(all_references['people'])} unique ({stats['people_extracted']} total mentions)")
    print(f"  📍 Places: {len(all_references['places'])} unique ({stats['places_extracted']} total mentions)")
    print(f"  📅 Events: {len(all_references['events'])} unique ({stats['events_extracted']} total mentions)")
    print(f"  💭 Themes: {len(all_references['themes'])} unique ({stats['themes_extracted']} total mentions)")
    print(f"  ❤️ Emotions: {len(all_references['emotions'])} unique ({stats['emotions_extracted']} total mentions)")
    print("="*80)
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract references from documents')
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
        stats = process_all_documents(storage_path, limit=limit)
        print("\n🎉 Reference extraction complete!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

