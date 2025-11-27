#!/usr/bin/env python3

"""
Import enhanced OCR results into local storage for UI viewing.
Merges corrected text and translations into the existing document records.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_batch_results(results_dir: Path) -> Dict[str, Dict]:
    """Load all batch processing results indexed by PDF filename."""
    summary_file = results_dir / 'batch_summary.json'
    
    if not summary_file.exists():
        print(f"Error: {summary_file} not found")
        return {}
    
    with open(summary_file) as f:
        data = json.load(f)
    
    # Index by PDF filename for easy lookup
    results_by_pdf = {}
    for result in data.get('results', []):
        pdf_name = result.get('pdf_file', '')
        results_by_pdf[pdf_name] = result
    
    return results_by_pdf


def load_local_metadata(storage_dir: Path) -> Dict:
    """Load local OCR storage metadata."""
    metadata_file = storage_dir / 'metadata.json'
    
    if not metadata_file.exists():
        print(f"Warning: {metadata_file} not found, creating new one")
        return {'documents': [], 'version': '1.0'}
    
    with open(metadata_file) as f:
        return json.load(f)


def load_document_file(storage_dir: Path, doc_id: str) -> Dict:
    """Load full document JSON file."""
    doc_file = storage_dir / 'documents' / f'{doc_id}.json'
    if doc_file.exists():
        with open(doc_file) as f:
            return json.load(f)
    return {}


def find_document_by_filename(storage_dir: Path, metadata: Dict, pdf_filename: str) -> tuple:
    """Find a document in metadata by matching filename patterns.
    
    Returns: (doc_id, doc_data) or (None, None)
    """
    pdf_stem = Path(pdf_filename).stem.lower()
    
    # Search through document metadata
    documents = metadata.get('documents', {})
    if isinstance(documents, list):
        # Old list format
        for doc in documents:
            if doc.get('source_pdf', '').lower().find(pdf_stem) >= 0:
                return (None, doc)
    else:
        # Dict format (current)
        for doc_id, doc_meta in documents.items():
            title = doc_meta.get('title', '').lower()
            if pdf_stem in title:
                # Load full document data
                doc_data = load_document_file(storage_dir, doc_id)
                return (doc_id, doc_data)
    
    return (None, None)


def update_document_with_corrections(doc: Dict, result: Dict) -> Dict:
    """Update document record with enhanced OCR results."""
    # Add corrected text
    if result.get('corrected_text'):
        doc['corrected_text'] = result['corrected_text']
        doc['correction_confidence'] = result.get('confidence', 0)
    
    # Add translated text
    if result.get('translated_text'):
        doc['translated_text'] = result['translated_text']
    
    # Add correction metadata
    doc['corrections_made'] = result.get('corrections_count', len(result.get('corrections', [])))
    doc['ocr_provider'] = result.get('provider_used', 'unknown')
    
    # Mark as enhanced
    doc['enhanced_ocr'] = True
    doc['enhancement_date'] = datetime.now().isoformat()
    
    # Preserve original text
    if 'ocr_text' in doc and 'original_text' not in doc:
        doc['original_text'] = doc['ocr_text']
    
    return doc


def import_enhanced_results(storage_dir: Path, results_dir: Path, reprocessed_dir: Path = None):
    """Import enhanced OCR results into local storage."""
    
    print("="*70)
    print("IMPORTING ENHANCED OCR TO LOCAL STORAGE")
    print("="*70)
    
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
    
    # Load local metadata
    print(f"\n📂 Loading local metadata from: {storage_dir}")
    metadata = load_local_metadata(storage_dir)
    docs_dict = metadata.get('documents', {})
    doc_count = len(docs_dict) if isinstance(docs_dict, dict) else len(docs_dict)
    print(f"   Found {doc_count} existing documents")
    
    # Update documents
    updated_count = 0
    not_found = []
    
    documents_dir = storage_dir / 'documents'
    documents_dir.mkdir(exist_ok=True)
    
    for pdf_name, result in batch_results.items():
        doc_id, doc_data = find_document_by_filename(storage_dir, metadata, pdf_name)
        
        if doc_id and doc_data:
            # Update document data
            update_document_with_corrections(doc_data, result)
            
            # Save updated document file
            doc_file = documents_dir / f'{doc_id}.json'
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            updated_count += 1
            print(f"  ✓ Updated: {pdf_name} ({doc_id})")
        else:
            not_found.append(pdf_name)
    
    # Update metadata timestamp
    metadata['last_updated'] = datetime.now().isoformat()
    
    # Save updated metadata
    metadata_file = storage_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*70)
    print("IMPORT SUMMARY")
    print("="*70)
    print(f"Documents updated: {updated_count}")
    print(f"Documents not found in storage: {len(not_found)}")
    
    if not_found:
        print(f"\nNot found (may need to upload PDFs to UI first):")
        for pdf in not_found[:10]:
            print(f"  - {pdf}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found) - 10} more")
    
    print(f"\n💾 Updated metadata saved to: {metadata_file}")
    print("="*70)
    
    return updated_count, not_found


def main():
    """Command-line interface."""
    storage_dir = Path('ocr_storage')
    results_dir = Path('letters/full_batch_results')
    reprocessed_dir = Path('letters/reprocessed_results')
    
    if not storage_dir.exists():
        print(f"Error: Storage directory not found: {storage_dir}")
        sys.exit(1)
    
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)
    
    updated, not_found = import_enhanced_results(storage_dir, results_dir, reprocessed_dir)
    
    if len(not_found) > 0:
        print("\n💡 TIP: Upload the missing PDFs through the UI first, then run this script again.")


if __name__ == '__main__':
    main()

