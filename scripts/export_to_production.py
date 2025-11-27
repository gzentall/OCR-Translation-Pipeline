#!/usr/bin/env python3

"""
Export to Production Database Tool.
Migrate enhanced OCR data from local JSON storage to PostgreSQL production database.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseSession, Document, Reference, ReferenceType
from local_storage import LocalOCRStorage


class ProductionExporter:
    """Export local OCR data to production PostgreSQL database."""
    
    def __init__(self, storage_dir='ocr_storage'):
        """
        Initialize exporter.
        
        Args:
            storage_dir: Path to local storage directory
        """
        self.storage = LocalOCRStorage(storage_dir)
        self.stats = {
            'total_documents': 0,
            'exported_documents': 0,
            'skipped_documents': 0,
            'total_references': 0,
            'exported_references': 0,
            'errors': []
        }
    
    def export_all(self, dry_run=True) -> Dict:
        """
        Export all documents from local storage to production database.
        
        Args:
            dry_run: If True, only simulate export without committing
            
        Returns:
            Dict with export statistics
        """
        print(f"\n{'='*80}")
        print(f"{'DRY RUN - ' if dry_run else ''}Exporting to Production Database")
        print(f"{'='*80}\n")
        
        # Get all documents from local storage
        doc_ids = self.storage.list_documents()
        self.stats['total_documents'] = len(doc_ids)
        
        print(f"Found {len(doc_ids)} documents in local storage")
        
        if not doc_ids:
            print("No documents to export.")
            return self.stats
        
        # Process each document
        with DatabaseSession() as db:
            for i, doc_id in enumerate(doc_ids, 1):
                print(f"\n[{i}/{len(doc_ids)}] Processing {doc_id}...")
                
                try:
                    self._export_document(db, doc_id, dry_run)
                    self.stats['exported_documents'] += 1
                except Exception as e:
                    error_msg = f"Error exporting {doc_id}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
                    self.stats['skipped_documents'] += 1
            
            if not dry_run:
                db.commit()
                print("\n✅ Changes committed to database")
            else:
                print("\n🔍 Dry run complete - no changes made to database")
        
        # Print summary
        self._print_summary()
        
        return self.stats
    
    def _export_document(self, db, doc_id: str, dry_run: bool):
        """
        Export a single document to the database.
        
        Args:
            db: Database session
            doc_id: Document ID
            dry_run: If True, don't commit changes
        """
        # Load document from local storage
        doc_data = self.storage.get_document(doc_id)
        
        if not doc_data:
            raise ValueError(f"Document {doc_id} not found in local storage")
        
        # Check if document already exists
        existing = db.query(Document).filter_by(id=doc_id).first()
        
        if existing:
            print(f"  ⚠️  Document already exists in database - skipping")
            self.stats['skipped_documents'] += 1
            return
        
        # Create document record
        doc = Document(
            id=doc_id,
            title=doc_data.get('title', f"Document {doc_id}"),
            date_processed=datetime.fromisoformat(doc_data.get('date_processed', datetime.now().isoformat())),
            document_date=doc_data.get('document_date'),
            source_language=doc_data.get('source_language', 'unknown'),
            target_language=doc_data.get('target_language', 'en'),
            original_text=doc_data.get('original_text'),
            translated_text=doc_data.get('translated_text'),
            summary=doc_data.get('summary', 'No summary available'),
            page_count=doc_data.get('page_count', 0),
            file_size=doc_data.get('file_size', 0),
            status='Processed'
        )
        
        # Add enhanced OCR fields if available
        if 'corrected_text' in doc_data:
            # Note: This requires schema migration (see Phase 7)
            # For now, we'll store in comments or metadata
            if hasattr(doc, 'corrected_text'):
                doc.corrected_text = doc_data['corrected_text']
            if hasattr(doc, 'correction_confidence'):
                doc.correction_confidence = doc_data.get('correction_confidence')
            if hasattr(doc, 'correction_metadata'):
                doc.correction_metadata = json.dumps({
                    'corrections': doc_data.get('corrections_applied', []),
                    'uncertain_segments': doc_data.get('uncertain_segments', [])
                })
        
        # Extract sender/recipient if available
        doc.sender = doc_data.get('sender', '')
        doc.recipient = doc_data.get('recipient', '')
        doc.sender_location = doc_data.get('sender_location', '')
        doc.recipient_location = doc_data.get('recipient_location', '')
        doc.comments = doc_data.get('comments', '')
        
        if dry_run:
            print(f"  🔍 Would create: Document(id='{doc.id}', title='{doc.title}')")
        else:
            db.add(doc)
            print(f"  ✅ Created: Document(id='{doc.id}', title='{doc.title}')")
        
        # Process people references
        people = doc_data.get('people', [])
        for person in people:
            self._add_reference(
                db,
                doc,
                person.get('original_name'),
                ReferenceType.PERSON,
                person.get('context', ''),
                dry_run
            )
    
    def _add_reference(self, db, doc: Document, name: str, ref_type: ReferenceType, 
                       description: str, dry_run: bool):
        """
        Add or link a reference to a document.
        
        Args:
            db: Database session
            doc: Document object
            name: Reference name
            ref_type: Type of reference
            description: Reference description
            dry_run: If True, don't commit changes
        """
        if not name:
            return
        
        # Check if reference already exists
        ref = db.query(Reference).filter_by(name=name, type=ref_type).first()
        
        if not ref:
            # Create new reference
            ref = Reference(
                name=name,
                type=ref_type,
                description=description
            )
            
            if dry_run:
                print(f"    🔍 Would create: Reference(name='{name}', type='{ref_type.value}')")
            else:
                db.add(ref)
                self.stats['exported_references'] += 1
                print(f"    ✅ Created: Reference(name='{name}', type='{ref_type.value}')")
        
        # Link reference to document
        if ref not in doc.references:
            doc.references.append(ref)
            if not dry_run:
                print(f"    🔗 Linked: {name} -> {doc.id}")
    
    def _print_summary(self):
        """Print export summary statistics."""
        print(f"\n{'='*80}")
        print("Export Summary")
        print(f"{'='*80}")
        print(f"Total documents:      {self.stats['total_documents']}")
        print(f"Exported:             {self.stats['exported_documents']}")
        print(f"Skipped:              {self.stats['skipped_documents']}")
        print(f"References created:   {self.stats['exported_references']}")
        
        if self.stats['errors']:
            print(f"\nErrors encountered:   {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")
        
        print(f"{'='*80}\n")
    
    def validate_export(self) -> bool:
        """
        Validate that export was successful.
        
        Returns:
            True if validation passes, False otherwise
        """
        print(f"\n{'='*80}")
        print("Validating Export")
        print(f"{'='*80}\n")
        
        doc_ids = self.storage.list_documents()
        
        with DatabaseSession() as db:
            for doc_id in doc_ids:
                doc = db.query(Document).filter_by(id=doc_id).first()
                
                if not doc:
                    print(f"❌ Document {doc_id} not found in database")
                    return False
                
                print(f"✅ Document {doc_id} verified in database")
        
        print(f"\n✅ All {len(doc_ids)} documents validated successfully\n")
        return True


def main():
    """Command-line interface for export tool."""
    parser = argparse.ArgumentParser(
        description='Export enhanced OCR data to production database'
    )
    parser.add_argument(
        '--storage-dir',
        default='ocr_storage',
        help='Local storage directory (default: ocr_storage)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate export without making changes'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually perform export (disables dry-run)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate export after completion'
    )
    
    args = parser.parse_args()
    
    # Safety check
    if args.confirm and args.dry_run:
        print("Error: Cannot use both --confirm and --dry-run")
        sys.exit(1)
    
    dry_run = not args.confirm
    
    if not dry_run:
        print("\n⚠️  WARNING: This will export data to production database!")
        print("   Make sure you have:")
        print("   1. Backed up your production database")
        print("   2. Tested with --dry-run first")
        print("   3. Set the correct DATABASE_URL")
        
        confirm = input("\nType 'yes' to proceed: ")
        if confirm.lower() != 'yes':
            print("Export cancelled.")
            sys.exit(0)
    
    # Check database connection
    try:
        with DatabaseSession() as db:
            db.execute("SELECT 1")
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure DATABASE_URL is set correctly:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        sys.exit(1)
    
    # Create exporter
    exporter = ProductionExporter(storage_dir=args.storage_dir)
    
    # Run export
    stats = exporter.export_all(dry_run=dry_run)
    
    # Validate if requested
    if args.validate and not dry_run:
        if not exporter.validate_export():
            print("❌ Validation failed")
            sys.exit(1)
    
    # Final status
    if stats['errors']:
        print(f"⚠️  Export completed with {len(stats['errors'])} errors")
        sys.exit(1)
    else:
        if dry_run:
            print("✅ Dry run completed successfully")
            print("\nTo actually export, run with --confirm:")
            print("  python scripts/export_to_production.py --confirm")
        else:
            print("✅ Export completed successfully")


if __name__ == "__main__":
    main()

