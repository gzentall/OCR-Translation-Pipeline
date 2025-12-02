#!/usr/bin/env python3
"""
Promote Document to Production (R2 Storage)

This script promotes individual documents from local storage to the production
R2 storage. Use this when documents are processed locally and need to be
uploaded to production.

Usage:
    # Promote a single document by ID
    python scripts/promote_document.py doc_20251201_134055
    
    # Promote multiple documents
    python scripts/promote_document.py doc_20251201_134055 doc_20251201_140000
    
    # Promote all documents from the last N days
    python scripts/promote_document.py --recent 7
    
    # Promote all documents (full sync)
    python scripts/promote_document.py --all
    
    # Dry run (show what would be promoted without uploading)
    python scripts/promote_document.py --dry-run doc_20251201_134055
    
    # Include images (slower, uploads page images too)
    python scripts/promote_document.py --with-images doc_20251201_134055
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from scripts.r2_storage import R2Storage
from scripts.local_storage import LocalOCRStorage


class DocumentPromoter:
    """Promote documents from local storage to R2 production storage."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the promoter.
        
        Args:
            dry_run: If True, only simulate promotion without uploading
        """
        self.dry_run = dry_run
        self.local_storage = LocalOCRStorage()
        self.r2_storage = None
        
        if not dry_run:
            try:
                self.r2_storage = R2Storage()
                print("✅ Connected to R2 storage")
            except Exception as e:
                print(f"❌ Failed to connect to R2: {e}")
                print("   Make sure R2 credentials are set in .env")
                sys.exit(1)
        else:
            print("🔍 Dry run mode - no changes will be made")
    
    def get_local_documents(self) -> List[str]:
        """Get list of all local document IDs."""
        docs_dir = Path("ocr_storage/documents")
        if not docs_dir.exists():
            return []
        return [f.stem for f in docs_dir.glob("*.json")]
    
    def get_recent_documents(self, days: int) -> List[str]:
        """Get documents modified in the last N days."""
        docs_dir = Path("ocr_storage/documents")
        if not docs_dir.exists():
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        
        for f in docs_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime >= cutoff:
                recent.append(f.stem)
        
        return sorted(recent, key=lambda x: Path(f"ocr_storage/documents/{x}.json").stat().st_mtime, reverse=True)
    
    def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """Get document metadata from local storage."""
        doc_path = Path(f"ocr_storage/documents/{doc_id}.json")
        if not doc_path.exists():
            return None
        
        with open(doc_path) as f:
            return json.load(f)
    
    def promote_document(self, doc_id: str, with_images: bool = False) -> bool:
        """
        Promote a single document to R2.
        
        Args:
            doc_id: Document ID to promote
            with_images: If True, also upload page images
            
        Returns:
            True if successful, False otherwise
        """
        doc = self.get_document_info(doc_id)
        if not doc:
            print(f"  ❌ Document {doc_id} not found in local storage")
            return False
        
        title = doc.get('title', doc_id)
        sender = doc.get('sender', 'Unknown')
        recipient = doc.get('recipient', 'Unknown')
        
        print(f"  📄 {title}")
        print(f"     From: {sender} → To: {recipient}")
        
        if self.dry_run:
            print(f"     [DRY RUN] Would upload document")
            if with_images:
                images = doc.get('page_images', [])
                print(f"     [DRY RUN] Would upload {len(images)} images")
            return True
        
        try:
            # Upload document JSON
            success = self.r2_storage.save_document(doc, doc_id)
            if not success:
                print(f"  ❌ Failed to upload document")
                return False
            
            print(f"     ✅ Document uploaded")
            
            # Upload images if requested
            if with_images:
                images = doc.get('page_images', [])
                if images:
                    uploaded = 0
                    for img_path in images:
                        img_file = Path(img_path)
                        if img_file.exists():
                            # Extract page number from filename
                            # Format: letters/work/179-1942-08-15-fre-1.png
                            page_num = img_file.stem.split('-')[-1]
                            r2_key = f"images/{doc_id}/page_{page_num}.png"
                            
                            with open(img_file, 'rb') as f:
                                self.r2_storage.client.put_object(
                                    Bucket=self.r2_storage.bucket,
                                    Key=r2_key,
                                    Body=f.read(),
                                    ContentType='image/png'
                                )
                            uploaded += 1
                    
                    print(f"     ✅ Uploaded {uploaded}/{len(images)} images")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def promote_documents(self, doc_ids: List[str], with_images: bool = False) -> Dict:
        """
        Promote multiple documents to R2.
        
        Args:
            doc_ids: List of document IDs to promote
            with_images: If True, also upload page images
            
        Returns:
            Dict with promotion statistics
        """
        stats = {
            'total': len(doc_ids),
            'success': 0,
            'failed': 0,
            'failed_ids': []
        }
        
        print(f"\n{'='*60}")
        print(f"Promoting {len(doc_ids)} document(s) to production")
        print(f"{'='*60}\n")
        
        for i, doc_id in enumerate(doc_ids, 1):
            print(f"[{i}/{len(doc_ids)}] {doc_id}")
            
            if self.promote_document(doc_id, with_images):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['failed_ids'].append(doc_id)
            
            print()
        
        # Print summary
        print(f"{'='*60}")
        print(f"Promotion Complete")
        print(f"{'='*60}")
        print(f"  ✅ Success: {stats['success']}")
        print(f"  ❌ Failed:  {stats['failed']}")
        
        if stats['failed_ids']:
            print(f"\nFailed documents:")
            for doc_id in stats['failed_ids']:
                print(f"  - {doc_id}")
        
        return stats
    
    def check_r2_status(self, doc_id: str) -> bool:
        """Check if a document exists in R2."""
        if self.dry_run:
            return False
        
        try:
            doc = self.r2_storage.get_document(doc_id)
            return doc is not None
        except:
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Promote documents from local storage to R2 production',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s doc_20251201_134055              # Promote single document
  %(prog)s doc_1 doc_2 doc_3                # Promote multiple documents
  %(prog)s --recent 7                       # Promote docs from last 7 days
  %(prog)s --all                            # Promote all documents
  %(prog)s --dry-run doc_20251201_134055    # Preview without uploading
  %(prog)s --with-images doc_20251201_134055  # Include page images
  %(prog)s --list                           # List local documents
  %(prog)s --list --recent 3                # List recent documents
        """
    )
    
    parser.add_argument('doc_ids', nargs='*', help='Document IDs to promote')
    parser.add_argument('--all', action='store_true', help='Promote all local documents')
    parser.add_argument('--recent', type=int, metavar='DAYS', help='Promote documents from the last N days')
    parser.add_argument('--dry-run', action='store_true', help='Simulate promotion without uploading')
    parser.add_argument('--with-images', action='store_true', help='Also upload page images')
    parser.add_argument('--list', action='store_true', help='List documents instead of promoting')
    
    args = parser.parse_args()
    
    # Initialize promoter
    promoter = DocumentPromoter(dry_run=args.dry_run)
    
    # Determine which documents to process
    doc_ids = []
    
    if args.all:
        doc_ids = promoter.get_local_documents()
        print(f"Found {len(doc_ids)} documents in local storage")
    elif args.recent:
        doc_ids = promoter.get_recent_documents(args.recent)
        print(f"Found {len(doc_ids)} documents from the last {args.recent} days")
    elif args.doc_ids:
        doc_ids = args.doc_ids
    else:
        # No documents specified - show help
        if args.list:
            # List mode without filters - show all
            doc_ids = promoter.get_local_documents()
        else:
            parser.print_help()
            print("\n❌ Error: No documents specified. Use --all, --recent N, or provide document IDs.")
            sys.exit(1)
    
    # List mode
    if args.list:
        print(f"\n{'='*60}")
        print(f"Local Documents ({len(doc_ids)})")
        print(f"{'='*60}\n")
        
        for doc_id in doc_ids:
            doc = promoter.get_document_info(doc_id)
            if doc:
                title = doc.get('title', doc_id)
                sender = doc.get('sender', 'Unknown')
                date = doc.get('date', 'Unknown')
                in_r2 = "✅" if promoter.check_r2_status(doc_id) else "❌"
                print(f"  {in_r2} {doc_id}")
                print(f"     {title} | {sender} | {date}")
        
        print(f"\n✅ = In R2, ❌ = Not in R2")
        return
    
    # Promote documents
    if not doc_ids:
        print("No documents to promote.")
        sys.exit(0)
    
    stats = promoter.promote_documents(doc_ids, with_images=args.with_images)
    
    # Exit with error code if any failed
    if stats['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

