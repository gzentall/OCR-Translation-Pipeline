#!/usr/bin/env python3

"""
Populate local storage with all batch-processed documents.
Creates new document records directly from batch results without needing UI upload.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def generate_doc_id() -> str:
    """Generate a document ID based on timestamp."""
    return datetime.now().strftime("doc_%Y%m%d_%H%M%S")


def load_batch_results(results_dir: Path) -> Dict[str, Dict]:
    """Load all batch processing results."""
    summary_file = results_dir / 'batch_summary.json'
    
    if not summary_file.exists():
        print(f"Error: {summary_file} not found")
        return {}
    
    with open(summary_file) as f:
        data = json.load(f)
    
    results_by_pdf = {}
    for result in data.get('results', []):
        pdf_name = result.get('pdf_file', '')
        results_by_pdf[pdf_name] = result
    
    return results_by_pdf


def extract_metadata_from_filename(pdf_name: str) -> Dict:
    """Extract date and language from PDF filename."""
    stem = Path(pdf_name).stem
    
    # Parse filename like "065-1940-04-26-fre" or "089-1936-01-23-ger"
    parts = stem.split('-')
    
    metadata = {
        'date': 'unknown',
        'language': 'unknown'
    }
    
    # Try to extract date
    if len(parts) >= 4:
        try:
            year = parts[1]
            month = parts[2] if parts[2] != 'XX' and parts[2] != 'xxx' else '01'
            day = parts[3] if parts[3] != 'xx' else '01'
            metadata['date'] = f"{year}-{month}-{day}"
        except:
            pass
    
    # Extract language from last part
    if parts:
        last_part = parts[-1].lower()
        if 'fre' in last_part:
            metadata['language'] = 'French'
        elif 'ger' in last_part:
            metadata['language'] = 'German'
        elif 'eng' in last_part:
            metadata['language'] = 'English'
    
    return metadata


def create_document_record(pdf_name: str, result: Dict, doc_id: str) -> Dict:
    """Create a complete document record from batch result."""
    
    file_metadata = extract_metadata_from_filename(pdf_name)
    
    # Create document record
    doc = {
        'id': doc_id,
        'title': Path(pdf_name).stem,
        'source_pdf': pdf_name,
        'date_processed': datetime.now().isoformat(),
        'date_created': file_metadata['date'],
        'source_language': file_metadata['language'],
        'target_language': 'English',
        'status': 'Final',
        
        # OCR data
        'raw_text': result.get('raw_text', ''),
        'corrected_text': result.get('corrected_text', ''),
        'translated_text': result.get('translated_text', ''),
        
        # Quality metrics
        'correction_confidence': result.get('confidence', 0),
        'corrections_made': result.get('corrections_count', len(result.get('corrections', []))),
        'ocr_provider': result.get('provider_used', 'openai'),
        
        # Metadata
        'enhanced_ocr': True,
        'enhancement_date': datetime.now().isoformat(),
        
        # Statistics
        'raw_word_count': result.get('raw_word_count', 0),
        'corrected_word_count': result.get('corrected_word_count', 0),
        
        # Processing details
        'corrections': result.get('corrections', []),
        'uncertain_segments': result.get('uncertain_segments', []),
    }
    
    return doc


def populate_local_storage(storage_dir: Path, results_dir: Path, reprocessed_dir: Path = None):
    """Populate local storage with all batch results."""
    
    print("="*80)
    print("POPULATING LOCAL STORAGE WITH ALL BATCH RESULTS")
    print("="*80)
    
    # Load results
    print(f"\n📂 Loading batch results from: {results_dir}")
    batch_results = load_batch_results(results_dir)
    print(f"   Found {len(batch_results)} batch results")
    
    # Also load reprocessed results if available
    if reprocessed_dir and reprocessed_dir.exists():
        print(f"\n📂 Loading reprocessed results from: {reprocessed_dir}")
        reprocessed = load_batch_results(reprocessed_dir)
        print(f"   Found {len(reprocessed)} reprocessed results")
        # Merge (reprocessed overrides batch)
        batch_results.update(reprocessed)
        print(f"   Total results after merge: {len(batch_results)}")
    
    # Load or create metadata
    metadata_file = storage_dir / 'metadata.json'
    if metadata_file.exists():
        print(f"\n📂 Loading existing metadata from: {storage_dir}")
        with open(metadata_file) as f:
            metadata = json.load(f)
    else:
        print(f"\n📂 Creating new metadata file")
        metadata = {
            'documents': {},
            'people': {},
            'last_updated': datetime.now().isoformat()
        }
    
    # Ensure documents dict exists
    if not isinstance(metadata.get('documents'), dict):
        metadata['documents'] = {}
    
    # Create documents directory
    documents_dir = storage_dir / 'documents'
    documents_dir.mkdir(exist_ok=True)
    
    # Process each result
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for pdf_name, result in sorted(batch_results.items()):
        # Check if document already exists by title
        pdf_stem = Path(pdf_name).stem
        existing_doc_id = None
        
        for doc_id, doc_meta in metadata['documents'].items():
            if pdf_stem in doc_meta.get('title', ''):
                existing_doc_id = doc_id
                break
        
        if existing_doc_id:
            # Update existing document
            doc_file = documents_dir / f'{existing_doc_id}.json'
            if doc_file.exists():
                with open(doc_file) as f:
                    doc = json.load(f)
                
                # Update with new data
                doc['corrected_text'] = result.get('corrected_text', '')
                doc['translated_text'] = result.get('translated_text', '')
                doc['correction_confidence'] = result.get('confidence', 0)
                doc['corrections_made'] = result.get('corrections_count', 0)
                doc['enhanced_ocr'] = True
                doc['enhancement_date'] = datetime.now().isoformat()
                
                # Save updated document
                with open(doc_file, 'w') as f:
                    json.dump(doc, f, indent=2)
                
                updated_count += 1
                print(f"  ✓ Updated: {pdf_name} ({existing_doc_id})")
            else:
                skipped_count += 1
                print(f"  ⚠️ Skipped: {pdf_name} (metadata exists but file missing)")
        else:
            # Create new document
            doc_id = generate_doc_id()
            
            # Avoid duplicate IDs
            import time
            while doc_id in metadata['documents']:
                time.sleep(0.01)
                doc_id = generate_doc_id()
            
            # Create document record
            doc = create_document_record(pdf_name, result, doc_id)
            
            # Save document file
            doc_file = documents_dir / f'{doc_id}.json'
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)
            
            # Add to metadata
            metadata['documents'][doc_id] = {
                'title': f"{Path(pdf_name).stem}",
                'date_processed': datetime.now().isoformat(),
                'source_language': doc['source_language'],
                'target_language': 'English',
                'status': 'Final'
            }
            
            created_count += 1
            print(f"  ✓ Created: {pdf_name} ({doc_id})")
    
    # Update metadata timestamp
    metadata['last_updated'] = datetime.now().isoformat()
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*80)
    print("IMPORT SUMMARY")
    print("="*80)
    print(f"Documents created: {created_count}")
    print(f"Documents updated: {updated_count}")
    print(f"Documents skipped: {skipped_count}")
    print(f"Total in storage: {len(metadata['documents'])}")
    print(f"\n💾 Metadata saved to: {metadata_file}")
    print("="*80)
    
    return created_count, updated_count, skipped_count


def main():
    """Command-line interface."""
    storage_dir = Path('ocr_storage')
    results_dir = Path('letters/full_batch_results')
    reprocessed_dir = Path('letters/reprocessed_results')
    
    if not storage_dir.exists():
        print(f"Creating storage directory: {storage_dir}")
        storage_dir.mkdir(parents=True)
    
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)
    
    created, updated, skipped = populate_local_storage(storage_dir, results_dir, reprocessed_dir)
    
    print(f"\n🎉 Successfully populated local storage!")
    print(f"   You can now view all {created + updated} documents at http://localhost:5001")


if __name__ == '__main__':
    main()

