#!/usr/bin/env python3

"""
Batch Processing Validation Tool.
Verify that all documents were processed successfully.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict


def validate_batch_results(results_dir: str) -> bool:
    """
    Validate batch processing results.
    
    Args:
        results_dir: Directory containing processing results
        
    Returns:
        True if validation passes, False otherwise
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return False
    
    print(f"\n{'='*80}")
    print(f"Validating Batch Results: {results_dir}")
    print(f"{'='*80}\n")
    
    # Check for summary file
    summary_file = results_path / 'batch_summary.json'
    if not summary_file.exists():
        print(f"❌ Summary file not found: {summary_file}")
        return False
    
    # Load summary
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    total = summary.get('total_documents', 0)
    processed = summary.get('processed_successfully', 0)
    
    print(f"Total documents: {total}")
    print(f"Processed successfully: {processed}")
    print(f"Failed: {total - processed}")
    
    if processed == 0:
        print("\n❌ No documents were processed successfully")
        return False
    
    # Validate each result file
    result_files = list(results_path.glob('*.result.json'))
    
    print(f"\nValidating {len(result_files)} result files...\n")
    
    errors = []
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            # Check required fields
            required_fields = ['pdf_file', 'corrected_text', 'confidence', 'corrections']
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                errors.append(f"{result_file.name}: Missing fields {missing_fields}")
                print(f"  ❌ {result_file.name}: Missing {missing_fields}")
                continue
            
            # Check confidence
            confidence = result.get('confidence', 0)
            if confidence < 50:
                print(f"  ⚠️  {result_file.name}: Low confidence ({confidence}%)")
            else:
                print(f"  ✅ {result_file.name}: OK (confidence: {confidence}%)")
            
            # Check for corrected text file
            corrected_file = results_path / f"{result_file.stem.replace('.result', '')}.corrected.txt"
            if not corrected_file.exists():
                errors.append(f"{result_file.name}: Corrected text file missing")
                print(f"  ❌ {result_file.name}: Corrected text file missing")
        
        except Exception as e:
            errors.append(f"{result_file.name}: {e}")
            print(f"  ❌ {result_file.name}: Error - {e}")
    
    # Print summary
    print(f"\n{'='*80}")
    if errors:
        print(f"❌ Validation failed with {len(errors)} errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        print(f"{'='*80}\n")
        return False
    else:
        print(f"✅ All validations passed!")
        print(f"{'='*80}\n")
        return True


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate batch processing results'
    )
    parser.add_argument(
        'results_dir',
        help='Directory containing batch processing results'
    )
    
    args = parser.parse_args()
    
    success = validate_batch_results(args.results_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

