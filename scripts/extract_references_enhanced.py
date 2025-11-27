#!/usr/bin/env python3

"""
Enhanced script to extract comprehensive references from documents using full context.
Extracts: People, Places (from addresses and text), Events, Themes, and Emotions.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage
from scripts.ai_processor import AIProcessor

# Load environment variables
load_dotenv()

def load_context() -> str:
    """Load the reference context data to provide to the LLM."""
    context_file = Path(__file__).resolve().parent.parent / 'context' / 'reference_data.json'
    if context_file.exists():
        with open(context_file, 'r') as f:
            context_data = json.load(f)
        return json.dumps(context_data, indent=2)
    return ""

def extract_references_with_context(ai_processor: AIProcessor, text: str, 
                                    document_date: str = None,
                                    sender: str = None,
                                    recipient: str = None,
                                    sender_location: str = None,
                                    recipient_location: str = None) -> Dict[str, List[tuple]]:
    """
    Enhanced extraction that uses full context and metadata to identify references.
    """
    context = load_context()
    
    # Build metadata context
    metadata_context = ""
    if document_date:
        metadata_context += f"Document Date: {document_date}\n"
    if sender:
        metadata_context += f"Sender: {sender}\n"
    if recipient:
        metadata_context += f"Recipient: {recipient}\n"
    if sender_location:
        metadata_context += f"Sender Location: {sender_location}\n"
    if recipient_location:
        metadata_context += f"Recipient Location: {recipient_location}\n"
    
    prompt = f"""
You are analyzing historical WWII-era correspondence between Robert and Betty Zentall (originally Zweigenthal).

CONTEXT ABOUT THE COLLECTION:
{context}

CURRENT DOCUMENT METADATA:
{metadata_context}

From the following document text, extract and categorize ALL important references with maximum detail and context:

EXTRACTION CATEGORIES:

1. **People**: Anyone mentioned by name or relationship
   - Include nicknames, formal names, relationships
   - Note if they are family, friends, military contacts, officials, etc.
   - Context should indicate their relationship/significance

2. **Places**: VERY IMPORTANT - Extract ALL locations including:
   - Cities, towns, villages, regions, countries
   - Street addresses (from envelopes and letter content)
   - Specific locations mentioned (cafes, hotels, camps, buildings)
   - Military locations, camps, stations
   - Context should indicate significance (home, military base, meeting place, etc.)

3. **Events**: Historical and personal events
   - WWII events (invasions, battles, mobilizations, etc.)
   - Personal milestones (meetings, pregnancy, travel, etc.)
   - Specific dates or time periods mentioned
   - Context should explain what happened

4. **Themes**: Major recurring topics or concepts
   - War anxiety, separation, hope, daily life, finances, health, pregnancy, family, military service
   - Context should capture the essence of the theme

5. **Emotions**: Dominant feelings expressed
   - Love, longing, fear, worry, hope, joy, sadness, frustration, etc.
   - Context should note intensity and what triggered it

SPECIAL ATTENTION:
- Extract BOTH sender and recipient locations if addresses are visible
- Look for street addresses, house numbers, city names in any language
- Identify military camps, barracks, or station names
- Note when people reference "here" or "there" - infer location from context
- Capture event dates precisely when mentioned
- Consider the historical period (1932-1942, WWII era)

Return ONLY valid JSON in this exact format:
{{
  "people": [
    {{"name": "Full Name", "context": "relationship/role, 1-5 words"}}
  ],
  "places": [
    {{"name": "Location Name", "context": "significance/type, address if available"}}
  ],
  "events": [
    {{"name": "Event Name", "context": "what happened, date if known"}}
  ],
  "themes": [
    {{"name": "Theme Name", "context": "brief description"}}
  ],
  "emotions": [
    {{"name": "Emotion Name", "context": "trigger/intensity"}}
  ]
}}

DOCUMENT TEXT:
{text[:6000]}

Return only valid JSON, no other text.
"""
    
    try:
        response = ai_processor.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert historical document analyst specializing in WWII correspondence. Extract ALL references with detailed context. Pay special attention to addresses and locations. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        parsed_json = json.loads(content)
        
        # Convert to tuple format with robust error handling
        result = {
            "people": [],
            "places": [],
            "events": [],
            "themes": [],
            "emotions": []
        }
        
        for category in result.keys():
            if category in parsed_json and isinstance(parsed_json[category], list):
                result[category] = [
                    (item.get("name", "Unknown"), item.get("context", ""))
                    for item in parsed_json[category]
                    if isinstance(item, dict) and item.get("name")
                ]
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"      ❌ Error decoding JSON from LLM: {e}")
        print(f"      Raw response: {content[:200]}...")
        return {"people": [], "places": [], "events": [], "themes": [], "emotions": []}
    except Exception as e:
        print(f"      ❌ Error extracting references: {e}")
        return {"people": [], "places": [], "events": [], "themes": [], "emotions": []}


def extract_and_categorize_references_enhanced(storage_dir: Path, limit: int = None, 
                                               force_reprocess: bool = False):
    """
    Enhanced extraction that uses document metadata and full context.
    """
    print("="*80)
    print("ENHANCED REFERENCE EXTRACTION WITH FULL CONTEXT")
    print("="*80)

    storage = LocalOCRStorage(str(storage_dir))
    ai_processor = AIProcessor()

    local_doc_ids = list(storage.metadata.get('documents', {}).keys())
    print(f"\n📊 Found {len(local_doc_ids)} documents")

    if limit:
        local_doc_ids = local_doc_ids[:limit]
        print(f"   Processing first {limit} documents (test mode)")

    updated_count = 0
    failed_count = 0
    
    # Global reference tracking
    global_references = {
        "person": {},
        "place": {},
        "event": {},
        "theme": {},
        "emotion": {}
    }

    print("\n🔄 Processing documents with enhanced context...")

    for i, doc_id in enumerate(local_doc_ids):
        doc_data = storage.get_document(doc_id)
        if not doc_data:
            print(f"  ⚠️ Document {doc_id} not found, skipping.")
            failed_count += 1
            continue

        title = doc_data.get('title', doc_id)
        print(f"\n  [{i+1}/{len(local_doc_ids)}] 📄 {title}")

        document_text = doc_data.get('original_text') or doc_data.get('raw_text')
        
        if not document_text:
            print(f"     ⚠️ No text content, skipping.")
            failed_count += 1
            continue

        try:
            # Extract with full context and metadata
            extracted_refs = extract_references_with_context(
                ai_processor,
                document_text,
                document_date=doc_data.get('date'),
                sender=doc_data.get('sender'),
                recipient=doc_data.get('recipient'),
                sender_location=doc_data.get('sender_location'),
                recipient_location=doc_data.get('recipient_location')
            )
            
            doc_references_for_update = []
            ref_counts = {
                "person": 0, "place": 0, "event": 0, "theme": 0, "emotion": 0
            }
            
            # Map plural keys from LLM to singular type names
            type_mapping = {
                "people": "person",
                "places": "place",
                "events": "event",
                "themes": "theme",
                "emotions": "emotion"
            }

            for ref_key, refs in extracted_refs.items():
                ref_type = type_mapping.get(ref_key, ref_key.rstrip('s'))  # Convert plural to singular
                
                for ref_name, ref_context in refs:
                    normalized_name = storage.normalize_name(ref_name)
                    
                    # Add to global references
                    if normalized_name not in global_references[ref_type]:
                        global_references[ref_type][normalized_name] = {
                            "name": ref_name,
                            "type": ref_type,
                            "context": ref_context,
                            "aliases": [ref_name],
                            "documents": [],
                            "first_mentioned": datetime.now().isoformat()
                        }
                    
                    # Add document to reference's document list
                    if doc_id not in global_references[ref_type][normalized_name]["documents"]:
                        global_references[ref_type][normalized_name]["documents"].append(doc_id)
                    
                    # Add to document's reference list
                    doc_references_for_update.append({
                        "original_name": ref_name,
                        "normalized_name": normalized_name,
                        "type": ref_type
                    })
                    ref_counts[ref_type] += 1

            # Update document
            storage.update_document(doc_id, {"people": doc_references_for_update})
            updated_count += 1
            
            print(f"     ✅ 👥 People: {ref_counts['person']}, 📍 Places: {ref_counts['place']}, "
                  f"📅 Events: {ref_counts['event']}, 💭 Themes: {ref_counts['theme']}, "
                  f"❤️ Emotions: {ref_counts['emotion']}")

        except Exception as e:
            print(f"     ❌ Error: {e}")
            failed_count += 1

    print("\n🔄 Saving enhanced references to metadata...")
    
    # Merge with existing 'people' metadata
    flat_references = {}
    for ref_type, refs_by_type in global_references.items():
        for normalized_name, ref_data in refs_by_type.items():
            # Check if this reference already exists in 'people' metadata
            if normalized_name in storage.metadata.get("people", {}):
                # Merge with existing people data
                existing = storage.metadata["people"][normalized_name]
                # Keep existing aliases and add new ones
                all_aliases = list(set(existing.get("aliases", []) + ref_data["aliases"]))
                ref_data["aliases"] = all_aliases
                # Merge document lists
                all_docs = list(set(existing.get("documents", []) + ref_data["documents"]))
                ref_data["documents"] = all_docs
                # Keep existing context if present
                if existing.get("context"):
                    ref_data["context"] = existing["context"]
            
            flat_references[normalized_name] = ref_data
    
    # Update references metadata
    storage.metadata["references"] = flat_references
    storage._save_metadata()

    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Documents processed: {updated_count}")
    print(f"Documents failed: {failed_count}")

    print("\nEnhanced references extracted:")
    total_unique_refs = 0
    total_mentions = 0
    ref_type_icons = {
        "person": "👥",
        "place": "📍",
        "event": "📅",
        "theme": "💭",
        "emotion": "❤️"
    }
    for ref_type, refs_by_type in global_references.items():
        unique_count = len(refs_by_type)
        mentions_count = sum(len(ref_data["documents"]) for ref_data in refs_by_type.values())
        print(f"  {ref_type_icons.get(ref_type, '  ')} {ref_type.capitalize()}s: "
              f"{unique_count} unique ({mentions_count} total mentions)")
        total_unique_refs += unique_count
        total_mentions += mentions_count
    
    print(f"\nTotal unique references: {total_unique_refs}")
    print(f"Total mentions: {total_mentions}")
    print("================================================================================")

    print("\n🎉 Enhanced reference extraction complete!")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    # Set limit=5 for testing, or None to process all
    extract_and_categorize_references_enhanced(storage_path, limit=None)

