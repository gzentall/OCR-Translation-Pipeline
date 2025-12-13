#!/usr/bin/env python3

"""
Comprehensive batch processing script for new documents.

This script processes a batch of PDF documents through the complete pipeline:
1. Extract images from PDFs
2. Run handwriting OCR
3. Translate to English
4. Extract metadata (sender, recipient, locations)
5. Extract and categorize references
6. Associate images with documents
"""

import json
import sys
import subprocess
import html
from pathlib import Path
from datetime import datetime
from typing import Optional
import time

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage
from scripts.ai_processor import AIProcessor
from scripts.envelope_extractor import EnvelopeExtractor
from scripts.translate_google import translate_text
from scripts.extract_references import ReferenceExtractor
from scripts.batch_processor import BatchOCRProcessor
from scripts.detect_untranslated import detect_untranslated_text


def extract_pdf_images(pdf_path: Path, output_dir: Path) -> list:
    """Extract images from PDF using pdftoppm."""
    print(f"  📄 Extracting images from {pdf_path.name}...")
    
    # Create unique prefix for this PDF
    pdf_id = pdf_path.stem
    output_prefix = output_dir / pdf_id
    
    try:
        # Run pdftoppm to extract pages as PNG images
        subprocess.run([
            'pdftoppm',
            '-png',
            '-r', '300',  # 300 DPI for good quality
            str(pdf_path),
            str(output_prefix)
        ], check=True, capture_output=True)
        
        # Find generated images
        images = sorted(output_dir.glob(f"{pdf_id}-*.png"))
        print(f"    ✅ Extracted {len(images)} page(s)")
        return [str(img.relative_to(Path.cwd())) for img in images]
        
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Error extracting images: {e}")
        return []


def run_enhanced_ocr(pdf_path: Path, batch_processor: BatchOCRProcessor, 
                     context: dict, source_lang: str) -> Optional[tuple]:
    """Run enhanced OCR with context-aware correction."""
    print(f"  🔍 Running Google Vision OCR with context enhancement...")
    
    # Prepare metadata for context-aware processing
    metadata = {
        'language': source_lang,
        'context': context,
        'filename': pdf_path.name
    }
    
    try:
        # Run OCR
        ocr_result = batch_processor.run_ocr_on_pdf(pdf_path)
        if not ocr_result:
            return None
        
        raw_text = ocr_result['text']
        print(f"    ✅ OCR complete ({len(raw_text)} chars)")
        
        # Apply LLM correction with context
        print(f"    🔧 Applying context-aware correction...")
        enhanced = batch_processor.processor.correct_with_context(raw_text, metadata)
        
        corrected_text = enhanced.get('corrected_text', raw_text)
        print(f"    ✅ Text corrected ({len(corrected_text)} chars)")
        
        return (raw_text, corrected_text)
        
    except Exception as e:
        print(f"    ❌ Enhanced OCR error: {e}")
        return None


def decode_html_entities(text: str) -> str:
    """Decode HTML entities in text (&#39; → ', &amp; → &, etc.)."""
    if not text or not isinstance(text, str):
        return text
    return html.unescape(text)


def translate_document(text: str, source_lang: str) -> str:
    """Translate document text to English."""
    if source_lang == 'eng' or not text:
        return text
    
    # Map ISO 639-2 (3-letter) to ISO 639-1 (2-letter) codes
    lang_map = {
        'ger': 'de',   # German
        'fre': 'fr',   # French
        'spa': 'es',   # Spanish
        'ita': 'it',   # Italian
        'pol': 'pl',   # Polish
        'rus': 'ru',   # Russian
        'eng': 'en'    # English
    }
    
    google_lang = lang_map.get(source_lang, source_lang)
    
    print(f"  🌐 Translating from {source_lang} ({google_lang}) to English...")
    try:
        translated = translate_text(text, target_language='en', source_language=google_lang)
        
        # Google Translate returns array/tuple (text, detected_lang) - extract just text
        if isinstance(translated, (list, tuple)):
            translated = translated[0]
        
        print(f"    ✅ Translation complete")
        return translated
    except Exception as e:
        print(f"    ⚠️  Translation error: {e}")
        return text


def extract_document_metadata(text: str, envelope_extractor: EnvelopeExtractor) -> dict:
    """Extract sender, recipient, and locations from document."""
    print(f"  📋 Extracting metadata...")
    try:
        metadata = envelope_extractor.extract_metadata(text)
        print(f"    ✅ Metadata extracted")
        print(f"       Sender: {metadata.get('sender', 'Unknown')}")
        print(f"       Recipient: {metadata.get('recipient', 'Unknown')}")
        return metadata
    except Exception as e:
        print(f"    ⚠️  Metadata extraction error: {e}")
        return {}


def extract_document_references(text: str, context: dict, ref_extractor: ReferenceExtractor) -> dict:
    """Extract and categorize references using LLM.
    
    Returns dict with two formats:
    - 'detailed': Original format with context (for metadata)
    - 'simple': Just names (for document display)
    """
    print(f"  🏷️  Extracting references...")
    try:
        references = ref_extractor.extract_references_from_text(text, context)
        
        # Normalize references - handle both dict and string formats
        detailed_refs = {}
        simple_refs = {}
        
        for ref_type in ['people', 'places', 'events', 'themes', 'emotions']:
            ref_list = references.get(ref_type, [])
            
            if ref_list:
                # Ensure consistent dict format for detailed
                detailed_refs[ref_type] = []
                simple_refs[ref_type] = []
                
                for item in ref_list:
                    if isinstance(item, dict):
                        # Already in dict format
                        detailed_refs[ref_type].append(item)
                        simple_refs[ref_type].append(item.get('name', str(item)))
                    elif isinstance(item, str):
                        # Convert string to dict format
                        detailed_refs[ref_type].append({'name': item, 'context': ''})
                        simple_refs[ref_type].append(item)
                    else:
                        # Fallback for unknown types
                        name = str(item)
                        detailed_refs[ref_type].append({'name': name, 'context': ''})
                        simple_refs[ref_type].append(name)
        
        counts = {k: len(v) for k, v in simple_refs.items() if v}
        print(f"    ✅ References extracted: {counts}")
        
        return {
            'detailed': detailed_refs,
            'simple': simple_refs
        }
    except Exception as e:
        print(f"    ⚠️  Reference extraction error: {e}")
        return {
            'detailed': {},
            'simple': {}
        }


def parse_filename(filename: str) -> dict:
    """Parse document filename to extract metadata.
    
    Expected format: NNN-YYYY-MM-DD-lang.pdf
    Example: 002-1938-01-05-ger.pdf
    """
    stem = Path(filename).stem
    parts = stem.split('-')
    
    metadata = {
        'number': parts[0] if len(parts) > 0 else None,
        'date': None,
        'language': parts[-1] if len(parts) > 0 else 'unknown'
    }
    
    # Try to parse date from middle parts
    if len(parts) >= 4:
        try:
            year = parts[1]
            month = parts[2] if len(parts[2]) == 2 else '01'
            day = parts[3] if len(parts[3]) == 2 else '01'
            metadata['date'] = f"{year}-{month}-{day}"
        except:
            pass
    
    return metadata


def process_single_document(pdf_path: Path, storage: LocalOCRStorage, 
                           ai_processor: AIProcessor, envelope_extractor: EnvelopeExtractor,
                           ref_extractor: ReferenceExtractor, batch_processor: BatchOCRProcessor,
                           context: dict, work_dir: Path, project_root: Path) -> bool:
    """Process a single PDF document through the complete pipeline."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*80}")
    
    try:
        # Parse filename for metadata
        file_metadata = parse_filename(pdf_path.name)
        source_lang = file_metadata['language']
        
        # Step 1: Run Enhanced OCR with context-aware correction
        ocr_result = run_enhanced_ocr(pdf_path, batch_processor, context, source_lang)
        if not ocr_result:
            print("  ❌ Enhanced OCR failed")
            return False
        
        raw_text, original_text = ocr_result
        if not original_text or len(original_text) < 50:
            print("  ❌ OCR produced insufficient text")
            return False
        
        # Step 2: Extract images for display (using pdftoppm)
        print(f"  📄 Extracting images for display...")
        image_paths = extract_pdf_images(pdf_path, work_dir)
        if not image_paths:
            print("    ⚠️  No images extracted for display")
            image_paths = []
        
        # Step 3: Translate
        translated_text = translate_document(original_text, source_lang)
        
        # Ensure translation is a string (Google Translate returns tuple/list [text, lang])
        if isinstance(translated_text, (list, tuple)):
            translated_text = translated_text[0] if translated_text else ''
        
        # Step 3b: Decode HTML entities in all text fields
        print(f"  🔧 Decoding HTML entities...")
        original_text = decode_html_entities(original_text)
        translated_text = decode_html_entities(translated_text)
        raw_text = decode_html_entities(raw_text)
        print(f"    ✅ HTML entities decoded")
        
        # Step 3c: Detect untranslated text
        print(f"  🔍 Detecting untranslated text...")
        try:
            untranslated_markers = detect_untranslated_text(
                translated_text=translated_text,
                original_text=original_text,
                source_language=source_lang
            )
            if untranslated_markers:
                print(f"    ⚠️  Found {len(untranslated_markers)} untranslated word(s)")
            else:
                print(f"    ✅ No untranslated text detected")
        except Exception as e:
            print(f"    ⚠️  Detection error: {e}")
            untranslated_markers = []
        
        # Step 4: Extract metadata
        metadata = extract_document_metadata(original_text, envelope_extractor)
        
        # Step 5: Extract references
        references = extract_document_references(original_text, context, ref_extractor)
        
        # Step 6: Generate summary
        print(f"  📝 Generating summary...")
        try:
            summary = ai_processor.generate_summary(original_text, source_lang)
            # Decode HTML entities in summary
            summary = decode_html_entities(summary)
            print(f"    ✅ Summary generated")
        except Exception as e:
            print(f"    ⚠️  Summary error: {e}")
            summary = "No summary available"
        
        # Always use filename as title
        title = pdf_path.stem
        # Decode HTML entities in title too
        title = decode_html_entities(title)
        print(f"       Title: {title}")
        
        # Step 7: Create document
        print(f"  💾 Saving document...")
        
        # Generate doc_id first
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get references in simple format
        simple_refs = references.get('simple', {})
        
        doc_data = {
            'id': doc_id,
            'filename': pdf_path.name,  # Store original filename
            'title': title,
            'raw_text': raw_text,  # Original OCR output
            'original_text': original_text,  # Context-corrected text
            'translated_text': translated_text,
            'untranslated_markers': untranslated_markers,  # Words/phrases that weren't translated
            'summary': summary,
            'language': source_lang,
            'date': file_metadata['date'],
            'sender': metadata.get('sender'),
            'recipient': metadata.get('recipient'),
            'sender_location': metadata.get('sender_location'),
            'recipient_location': metadata.get('recipient_location'),
            'references': simple_refs,  # New categorized format
            'people': simple_refs.get('people', []),  # Legacy format for UI compatibility
            'page_images': image_paths,
            'page_count': len(image_paths),  # Number of pages
            'source_file': str(pdf_path),
            'status': 'new',
            'reviews': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save document with explicit doc_id
        storage.add_document(doc_data, doc_id=doc_id)
        
        # Step 8: Add references to global metadata
        print(f"  🏷️  Adding references to metadata...")
        ref_count = 0
        
        # Use detailed format for global metadata (has context)
        detailed_refs = references.get('detailed', {})
        
        for ref_type, ref_list in detailed_refs.items():
            # Convert plural to singular for type
            singular_type = ref_type.rstrip('s') if ref_type != 'themes' else 'theme'
            
            for ref_data in ref_list:
                # ref_data is guaranteed to be dict with 'name' and 'context'
                ref_name = ref_data.get('name', '')
                if ref_name:
                    try:
                        # Add reference to global metadata (if it doesn't exist)
                        storage.add_reference(
                            ref_type=singular_type,
                            name=ref_name,
                            aliases=[],
                            notes=ref_data.get('context', '')
                        )
                        
                        # Link reference to document (uses just the name)
                        storage.add_reference_to_document(doc_id, ref_name)
                        ref_count += 1
                    except Exception as e:
                        # Log but continue if one reference fails
                        print(f"    ⚠️  Could not add reference '{ref_name}': {e}")
        
        print(f"    ✅ Added {ref_count} references to metadata")
        
        print(f"  ✅ Document {doc_id} saved successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return False


def main(start_num=None, end_num=None):
    """Main batch processing function.
    
    Args:
        start_num: Start file number (e.g., 108)
        end_num: End file number (e.g., 177)
    """
    print("="*80)
    print("BATCH DOCUMENT PROCESSING")
    print("="*80)
    if start_num and end_num:
        print(f"Processing files {start_num}-{end_num}")
    print()
    
    # Setup paths
    project_root = Path(__file__).resolve().parent.parent
    inbox_dir = project_root / "letters" / "inbox"
    work_dir = project_root / "letters" / "work"
    storage_dir = project_root / "ocr_storage"
    context_file = project_root / "context" / "reference_data.json"
    
    # Create work directory if needed
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize services
    print("\n🔧 Initializing services...")
    storage = LocalOCRStorage(str(storage_dir))
    ai_processor = AIProcessor()
    envelope_extractor = EnvelopeExtractor()
    ref_extractor = ReferenceExtractor()
    batch_processor = BatchOCRProcessor(provider='openai', context_file=str(context_file))
    
    # Load context
    context = {}
    if context_file.exists():
        with open(context_file) as f:
            context = json.load(f)
        print(f"✅ Loaded context file with {len(context)} entries")
    
    # Get list of PDFs to process
    all_pdfs = sorted(inbox_dir.glob("*.pdf"))
    
    # Identify already processed files
    processed_sources = set()
    for doc_file in (storage_dir / "documents").glob("*.json"):
        try:
            with open(doc_file) as f:
                data = json.load(f)
                if data.get('source_file'):
                    processed_sources.add(Path(data['source_file']).name)
        except:
            pass
    
    # Filter to unprocessed files
    pdfs_to_process = [p for p in all_pdfs if p.name not in processed_sources]
    
    # Further filter by file number range if specified
    if start_num and end_num:
        pdfs_to_process = [
            p for p in pdfs_to_process 
            if p.stem.split('-')[0].isdigit() and start_num <= int(p.stem.split('-')[0]) <= end_num
        ]
    
    print(f"\n📊 Processing Status:")
    print(f"   Total PDFs in inbox: {len(all_pdfs)}")
    print(f"   Already processed: {len(processed_sources)}")
    print(f"   To process: {len(pdfs_to_process)}")
    
    if not pdfs_to_process:
        print("\n✅ No new documents to process!")
        return
    
    # Process each document
    print(f"\n🚀 Starting batch processing of {len(pdfs_to_process)} documents...")
    start_time = time.time()
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(pdfs_to_process, 1):
        print(f"\n[{i}/{len(pdfs_to_process)}]")
        
        if process_single_document(pdf_path, storage, ai_processor, envelope_extractor, ref_extractor, batch_processor, context, work_dir, project_root):
            successful += 1
        else:
            failed += 1
        
        # Brief pause between documents to avoid rate limiting
        if i < len(pdfs_to_process):
            time.sleep(2)
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Time elapsed: {elapsed/60:.1f} minutes")
    print(f"📊 Average: {elapsed/len(pdfs_to_process):.1f} seconds per document")
    print(f"{'='*80}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process PDF documents through OCR pipeline')
    parser.add_argument('--start', type=int, help='Start file number (e.g., 108)')
    parser.add_argument('--end', type=int, help='End file number (e.g., 177)')
    
    args = parser.parse_args()
    main(start_num=args.start, end_num=args.end)

