#!/usr/bin/env python3

"""
Batch process all documents to detect untranslated text.
Uses LLM to identify words/phrases that weren't properly translated.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.local_storage import LocalOCRStorage
from scripts.detect_untranslated import UntranslatedTextDetector


def batch_detect_untranslated(
    storage: LocalOCRStorage,
    limit: int = None,
    force: bool = False,
    dry_run: bool = False,
    delay: float = 1.0
):
    """
    Process all documents to detect untranslated text.
    
    Args:
        storage: LocalOCRStorage instance
        limit: Max documents to process (None = all)
        force: Reprocess even if already has markers
        dry_run: Don't save changes, just report
        delay: Delay between API calls (seconds)
    """
    print("=" * 80)
    print("DETECTING UNTRANSLATED TEXT IN DOCUMENTS")
    print("=" * 80)
    print()
    
    # Initialize detector
    print("🔧 Initializing untranslated text detector...")
    try:
        detector = UntranslatedTextDetector()
        print("   ✅ Detector initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize detector: {e}")
        return
    
    print()
    
    # Get all documents
    print("📚 Loading documents...")
    all_docs = storage.list_documents()
    
    # Sort by document number for consistent ordering
    all_docs.sort(key=lambda d: d.get('title', d.get('id', '')))
    
    total_docs = len(all_docs)
    print(f"   Found {total_docs} documents")
    print()
    
    # Filter documents to process
    docs_to_process = []
    for i, doc_meta in enumerate(all_docs):
        doc_id = doc_meta.get('id')
        
        # Get full document
        doc = storage.get_document(doc_id)
        if not doc:
            continue
        
        # Check if already processed
        has_markers = 'untranslated_markers' in doc and doc['untranslated_markers'] is not None
        
        if has_markers and not force:
            continue
        
        # Check if has translated text
        translated_text = doc.get('translated_text', '')
        if not translated_text or len(translated_text.strip()) < 20:
            continue
        
        doc_num = i + 1
        title = doc.get('title', doc_id)
        docs_to_process.append((doc_num, doc_id, title, doc))
    
    print(f"📋 Documents to process: {len(docs_to_process)}")
    if force:
        print("   (--force enabled, reprocessing all)")
    print()
    
    if limit:
        docs_to_process = docs_to_process[:limit]
        print(f"   Limited to first {limit} documents")
        print()
    
    if not docs_to_process:
        print("✅ No documents need processing!")
        return
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be saved")
        print()
    
    print("-" * 80)
    print()
    
    # Process documents
    success_count = 0
    error_count = 0
    markers_found = 0
    
    for i, (doc_num, doc_id, title, doc) in enumerate(docs_to_process, 1):
        print(f"[{i}/{len(docs_to_process)}] #{doc_num:03d} - {title[:50]}")
        
        translated_text = doc.get('translated_text', '')
        original_text = doc.get('original_text', '') or doc.get('raw_text', '')
        source_lang = doc.get('language', doc.get('source_language', 'unknown'))
        
        print(f"    Language: {source_lang}, Text length: {len(translated_text)} chars")
        
        try:
            # Detect untranslated text
            markers = detector.detect_untranslated_text(
                translated_text=translated_text,
                original_text=original_text,
                source_language=source_lang
            )
            
            if markers:
                markers_found += len(markers)
                print(f"    ⚠️  Found {len(markers)} untranslated word(s):")
                for marker in markers[:3]:  # Show first 3
                    suggestion = f" → {marker['suggestion']}" if marker.get('suggestion') else ""
                    print(f"       • \"{marker['text']}\"{suggestion}")
                if len(markers) > 3:
                    print(f"       ... and {len(markers) - 3} more")
            else:
                print(f"    ✅ No untranslated text found")
            
            # Save markers (even if empty list)
            if not dry_run:
                storage.update_document(doc_id, {'untranslated_markers': markers})
            
            success_count += 1
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            error_count += 1
        
        # Rate limiting
        if i < len(docs_to_process) and delay > 0:
            time.sleep(delay)
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  ✅ Processed: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  🔍 Untranslated markers found: {markers_found}")
    if dry_run:
        print()
        print("  (DRY RUN - no changes saved)")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Detect untranslated text in all documents'
    )
    parser.add_argument(
        '--limit', type=int, default=None,
        help='Maximum number of documents to process'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Reprocess documents even if they already have markers'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--delay', type=float, default=1.0,
        help='Delay between API calls in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--use-r2', action='store_true',
        help='Use R2 storage instead of local'
    )
    
    args = parser.parse_args()
    
    # Configure storage
    if args.use_r2:
        os.environ['USE_R2'] = 'true'
    
    # Initialize storage
    storage = LocalOCRStorage()
    
    # Run batch processing
    batch_detect_untranslated(
        storage=storage,
        limit=args.limit,
        force=args.force,
        dry_run=args.dry_run,
        delay=args.delay
    )


if __name__ == '__main__':
    main()

