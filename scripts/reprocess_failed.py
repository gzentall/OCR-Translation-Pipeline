#!/usr/bin/env python3

"""
Reprocess failed documents with improved error handling.
"""

import json
import sys
from pathlib import Path
from batch_processor import BatchOCRProcessor


def main():
    """Reprocess documents that had LLM errors."""
    
    # Read the batch summary to find failed documents
    summary_file = Path("letters/full_batch_results/batch_summary.json")
    
    if not summary_file.exists():
        print(f"Error: {summary_file} not found")
        sys.exit(1)
    
    with open(summary_file) as f:
        data = json.load(f)
    
    # Find documents with 0% confidence (LLM errors)
    failed_docs = [
        result for result in data['results']
        if result.get('confidence', 0) == 0
    ]
    
    if not failed_docs:
        print("No failed documents found!")
        return
    
    print(f"Found {len(failed_docs)} documents with errors to reprocess")
    print("="*70)
    
    # Create a list of PDF files to reprocess
    failed_pdfs = [doc['pdf_file'] for doc in failed_docs]
    
    print("\nDocuments to reprocess:")
    for pdf in failed_pdfs:
        print(f"  - {pdf}")
    
    # Create temporary directory with just these PDFs
    inbox_dir = Path("letters/inbox")
    output_dir = Path("letters/reprocessed_results")
    output_dir.mkdir(exist_ok=True)
    
    # Process each failed document individually
    processor = BatchOCRProcessor(
        provider='openai',
        context_file='context/reference_data.json'
    )
    
    results = []
    success_count = 0
    
    for pdf_name in failed_pdfs:
        pdf_path = inbox_dir / pdf_name
        
        if not pdf_path.exists():
            print(f"\n⚠️ PDF not found: {pdf_path}")
            continue
        
        print(f"\n{'='*70}")
        print(f"Reprocessing: {pdf_name}")
        print(f"{'='*70}")
        
        result = processor.process_document(pdf_path, output_dir)
        
        if result and result.get('confidence', 0) > 0:
            success_count += 1
            print(f"  ✅ SUCCESS! Confidence: {result['confidence']}%")
        else:
            print(f"  ❌ Still failed")
        
        results.append(result)
    
    # Save reprocessing summary
    summary = {
        'total_documents': len(failed_pdfs),
        'successful': success_count,
        'failed_again': len(failed_pdfs) - success_count,
        'results': results
    }
    
    summary_output = output_dir / 'reprocessing_summary.json'
    with open(summary_output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*70)
    print("REPROCESSING SUMMARY")
    print("="*70)
    print(f"Total documents: {len(failed_pdfs)}")
    print(f"Now successful: {success_count}")
    print(f"Still failing: {len(failed_pdfs) - success_count}")
    print(f"\nResults saved to: {summary_output}")
    print("="*70)


if __name__ == '__main__':
    main()

