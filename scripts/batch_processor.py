#!/usr/bin/env python3

"""
Batch OCR Processor for OCR Translation Pipeline.
Process multiple documents through OCR enhancement pipeline.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import concurrent.futures

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_ocr_processor import EnhancedOCRProcessor


class BatchOCRProcessor:
    """Process multiple documents and track quality metrics."""
    
    def __init__(self, provider='openai', context_file='context/reference_data.json'):
        """
        Initialize batch processor.
        
        Args:
            provider: 'openai', 'claude', or 'both'
            context_file: Path to reference context JSON
        """
        self.processor = EnhancedOCRProcessor(provider=provider, context_file=context_file)
        self.provider = provider
        self.project_root = Path(__file__).parent.parent
    
    def run_ocr_on_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        Run Google Vision OCR on a PDF using existing script.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with 'text' and 'images' or None on error
        """
        # Generate doc ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get relative path from project root
        try:
            rel_path = pdf_path.relative_to(self.project_root)
        except ValueError:
            # If PDF is outside project root, use absolute path
            rel_path = pdf_path
        
        # Run OCR script
        script_path = self.project_root / "scripts" / "run_vision_ocr.sh"
        
        print(f"  Running Google Vision OCR on {pdf_path.name}...")
        
        try:
            result = subprocess.run(
                [str(script_path), str(rel_path), doc_id],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                print(f"  ❌ OCR failed: {result.stderr}")
                return None
            
            # Find the generated text file
            work_dir = self.project_root / "letters" / "work"
            pdf_stem = pdf_path.stem
            text_file = work_dir / f"{pdf_stem}.vision.txt"
            
            if not text_file.exists():
                print(f"  ❌ OCR text file not found: {text_file}")
                return None
            
            # Read OCR text
            with open(text_file, 'r') as f:
                ocr_text = f.read()
            
            print(f"  ✅ OCR complete: {len(ocr_text)} characters")
            
            return {
                'text': ocr_text,
                'doc_id': doc_id,
                'text_file': str(text_file)
            }
            
        except subprocess.TimeoutExpired:
            print(f"  ❌ OCR timed out after 5 minutes")
            return None
        except Exception as e:
            print(f"  ❌ OCR error: {e}")
            return None
    
    def run_translation(self, text_file: Path) -> Optional[str]:
        """
        Run Google Translate on a text file.
        
        Args:
            text_file: Path to text file to translate
            
        Returns:
            Translated text or None on error
        """
        script_path = self.project_root / "scripts" / "translate_google.py"
        
        # Determine output file path
        stem = text_file.stem
        if stem.endswith('.corrected'):
            stem = stem[:-10]  # Remove '.corrected'
        translated_file = text_file.parent / f"{stem}.translated.txt"
        
        print(f"  Translating to English...")
        
        try:
            # Specify explicit output path
            result = subprocess.run(
                ["python3", str(script_path), str(text_file), "--output", str(translated_file)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                print(f"  ⚠️  Translation failed: {result.stderr}")
                return None
            
            if not translated_file.exists():
                print(f"  ⚠️  Translated file not found: {translated_file}")
                return None
            
            with open(translated_file, 'r') as f:
                translated_text = f.read()
            
            print(f"  ✅ Translation complete: {len(translated_text)} characters")
            return translated_text
            
        except Exception as e:
            print(f"  ⚠️  Translation error: {e}")
            return None
    
    def process_document(self, pdf_path: Path, output_dir: Path) -> Optional[Dict]:
        """
        Process a single document through the enhancement pipeline.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save results
            
        Returns:
            Dict with processing results or None on error
        """
        print(f"\n{'='*80}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*80}")
        
        # Extract metadata from filename (e.g., 01-27-2003_eng_letter-001.pdf)
        metadata = self._extract_metadata(pdf_path)
        
        # Step 1: Run OCR
        ocr_result = self.run_ocr_on_pdf(pdf_path)
        if not ocr_result:
            return None
        
        raw_text = ocr_result['text']
        
        # Step 2: Apply LLM correction
        print(f"  Applying LLM correction with {self.provider}...")
        enhanced = self.processor.correct_with_context(raw_text, metadata)
        
        # Step 3: Extract entities (optional, can be done in Phase 5)
        # entities = self.processor.extract_entities(enhanced['corrected_text'], metadata)
        
        # Step 4: Save results
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save corrected text
        corrected_file = output_dir / f"{pdf_path.stem}.corrected.txt"
        with open(corrected_file, 'w') as f:
            f.write(enhanced['corrected_text'])
        
        # Step 5: Translate corrected text to English
        translated_text = self.run_translation(corrected_file)
        
        # Save detailed results as JSON
        result_data = {
            'pdf_file': pdf_path.name,
            'date_processed': datetime.now().isoformat(),
            'metadata': metadata,
            'raw_text': raw_text,
            'corrected_text': enhanced['corrected_text'],
            'translated_text': translated_text or '',
            'confidence': enhanced.get('confidence', 0),
            'corrections': enhanced.get('corrections', []),
            'uncertain_segments': enhanced.get('uncertain_segments', []),
            'provider_used': enhanced.get('provider_used'),
            'comparison': enhanced.get('comparison'),
            'raw_word_count': len(raw_text.split()),
            'corrected_word_count': len(enhanced['corrected_text'].split()),
            'corrections_count': len(enhanced.get('corrections', []))
        }
        
        result_file = output_dir / f"{pdf_path.stem}.result.json"
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"  ✅ Saved: {corrected_file.name}")
        print(f"  ✅ Saved: {result_file.name}")
        if translated_text:
            translated_file = output_dir / f"{pdf_path.stem}.translated.txt"
            print(f"  ✅ Saved: {translated_file.name}")
        print(f"  📊 Confidence: {enhanced.get('confidence')}%")
        print(f"  📝 Corrections: {len(enhanced.get('corrections', []))}")
        if translated_text:
            print(f"  🌍 Translated: {len(translated_text)} characters")
        
        return result_data
    
    def _extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extract metadata from PDF filename.
        
        Expected format: MM-DD-YYYY_lang_type-###.pdf
        Example: 01-27-2003_eng_letter-001.pdf
        """
        filename = pdf_path.stem
        parts = filename.split('_')
        
        metadata = {
            'document_type': 'letter',
            'expected_language': 'English',
            'date': 'unknown'
        }
        
        if len(parts) >= 3:
            # Parse date
            try:
                metadata['date'] = parts[0]
            except:
                pass
            
            # Parse language
            if parts[1] == 'eng':
                metadata['expected_language'] = 'English'
            elif parts[1] == 'ger':
                metadata['expected_language'] = 'German'
            
            # Parse type
            if 'letter' in parts[2]:
                metadata['document_type'] = 'letter'
        
        return metadata
    
    def process_directory(self, input_dir: Path, output_dir: Path, parallel: int = 1) -> List[Dict]:
        """
        Process all PDFs in a directory.
        
        Args:
            input_dir: Directory containing PDFs
            output_dir: Directory to save results
            parallel: Number of documents to process in parallel (default 1 for sequential)
            
        Returns:
            List of result dicts
        """
        pdf_files = list(input_dir.glob('*.pdf'))
        
        if not pdf_files:
            print(f"No PDF files found in {input_dir}")
            return []
        
        print(f"\n{'='*80}")
        print(f"Batch Processing: {len(pdf_files)} documents")
        print(f"Input:  {input_dir}")
        print(f"Output: {output_dir}")
        print(f"Provider: {self.provider}")
        print(f"Parallel: {parallel}")
        print(f"{'='*80}\n")
        
        results = []
        
        if parallel == 1:
            # Sequential processing
            for pdf_file in pdf_files:
                result = self.process_document(pdf_file, output_dir)
                if result:
                    results.append(result)
        else:
            # Parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = [executor.submit(self.process_document, pdf, output_dir) for pdf in pdf_files]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
        
        # Save summary
        summary = {
            'total_documents': len(pdf_files),
            'processed_successfully': len(results),
            'date_processed': datetime.now().isoformat(),
            'provider_used': self.provider,
            'results': results
        }
        
        summary_file = output_dir / 'batch_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"Batch Processing Complete")
        print(f"{'='*80}")
        print(f"Total documents: {len(pdf_files)}")
        print(f"Processed successfully: {len(results)}")
        print(f"Failed: {len(pdf_files) - len(results)}")
        print(f"\nSummary saved to: {summary_file}")
        print(f"{'='*80}\n")
        
        return results


def main():
    """Command-line interface for batch processor."""
    parser = argparse.ArgumentParser(
        description='Batch process PDFs through OCR enhancement pipeline'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input directory containing PDFs'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for results'
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'claude', 'both'],
        default='openai',
        help='LLM provider for corrections (default: openai)'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of documents to process in parallel (default: 1)'
    )
    parser.add_argument(
        '--context',
        default='context/reference_data.json',
        help='Path to reference context JSON file'
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Create batch processor
    processor = BatchOCRProcessor(
        provider=args.provider,
        context_file=args.context
    )
    
    # Process directory
    results = processor.process_directory(input_dir, output_dir, parallel=args.parallel)
    
    if not results:
        print("No documents were processed successfully.")
        sys.exit(1)
    
    print("✅ Batch processing complete!")


if __name__ == "__main__":
    main()

