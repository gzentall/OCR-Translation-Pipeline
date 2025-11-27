#!/usr/bin/env python3

"""
Extract page images from PDFs and link them to documents in storage.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List
import subprocess


def extract_pdf_pages(pdf_path: Path, output_dir: Path, doc_id: str) -> List[str]:
    """
    Extract pages from PDF as PNG images.
    
    Returns list of image paths relative to project root.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use pdftoppm to extract pages (part of poppler-utils)
    # Output format: {doc_id}_page_001.png, {doc_id}_page_002.png, etc.
    output_prefix = output_dir / doc_id
    
    try:
        # Extract all pages as PNG
        result = subprocess.run(
            ['pdftoppm', '-png', str(pdf_path), str(output_prefix)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"  ⚠️ pdftoppm failed: {result.stderr}")
            return []
        
        # Find the generated images
        images = sorted(output_dir.glob(f"{doc_id}-*.png"))
        
        # Return paths relative to project root
        # Convert to absolute paths first to handle any relative path issues
        abs_paths = [img.resolve() for img in images]
        project_root = Path.cwd().resolve()
        relative_paths = [str(img.relative_to(project_root)) for img in abs_paths]
        
        return relative_paths
        
    except FileNotFoundError:
        print(f"  ⚠️ pdftoppm not found. Install with: brew install poppler")
        return []
    except Exception as e:
        print(f"  ❌ Error extracting pages: {e}")
        return []


def add_images_to_documents(storage_dir: Path, pdf_dir: Path, images_dir: Path):
    """Add page images to all document records."""
    
    print("="*80)
    print("EXTRACTING IMAGES FROM PDFs AND LINKING TO DOCUMENTS")
    print("="*80)
    
    # Load metadata
    metadata_file = storage_dir / 'metadata.json'
    if not metadata_file.exists():
        print(f"Error: {metadata_file} not found")
        return
    
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    documents_dir = storage_dir / 'documents'
    
    updated_count = 0
    failed_count = 0
    
    # Process each document
    for doc_id, doc_meta in metadata['documents'].items():
        title = doc_meta.get('title', '')
        
        # Extract PDF name from title (e.g., "003-1941-07-20-fre" from "003-1941-07-20-fre - 2025-11-10")
        pdf_stem = title.split(' - ')[0] if ' - ' in title else title
        pdf_file = pdf_dir / f"{pdf_stem}.pdf"
        
        if not pdf_file.exists():
            print(f"  ⚠️ PDF not found: {pdf_file.name}")
            failed_count += 1
            continue
        
        print(f"\n📄 Processing: {pdf_file.name} ({doc_id})")
        
        # Extract images
        image_paths = extract_pdf_pages(pdf_file, images_dir, doc_id)
        
        if not image_paths:
            print(f"  ⚠️ No images extracted")
            failed_count += 1
            continue
        
        # Load document data
        doc_file = documents_dir / f'{doc_id}.json'
        if not doc_file.exists():
            print(f"  ⚠️ Document file not found: {doc_file}")
            failed_count += 1
            continue
        
        with open(doc_file) as f:
            doc = json.load(f)
        
        # Add images to document
        doc['page_images'] = image_paths
        doc['page_count'] = len(image_paths)
        
        # Save updated document
        with open(doc_file, 'w') as f:
            json.dump(doc, f, indent=2)
        
        # Update metadata
        doc_meta['page_count'] = len(image_paths)
        
        updated_count += 1
        print(f"  ✅ Added {len(image_paths)} images")
    
    # Save updated metadata
    metadata['last_updated'] = datetime.now().isoformat()
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Documents updated: {updated_count}")
    print(f"Documents failed: {failed_count}")
    print(f"Total: {len(metadata['documents'])}")
    print("="*80)
    
    return updated_count, failed_count


def main():
    """Command-line interface."""
    storage_dir = Path('ocr_storage')
    pdf_dir = Path('letters/inbox')
    images_dir = Path('letters/work')
    
    if not storage_dir.exists():
        print(f"Error: Storage directory not found: {storage_dir}")
        sys.exit(1)
    
    if not pdf_dir.exists():
        print(f"Error: PDF directory not found: {pdf_dir}")
        sys.exit(1)
    
    updated, failed = add_images_to_documents(storage_dir, pdf_dir, images_dir)
    
    if updated > 0:
        print(f"\n🎉 Successfully added images to {updated} documents!")
        print(f"   Restart the Flask app to see the images.")
    
    if failed > 0:
        print(f"\n⚠️  {failed} documents couldn't be processed (PDFs may need to be uploaded)")


if __name__ == '__main__':
    main()


