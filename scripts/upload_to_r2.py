"""
Upload all local data to Cloudflare R2.
Run this once to migrate documents, images, and metadata to R2.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.r2_storage import R2Storage


def upload_all_data():
    """Upload all documents, images, and metadata to R2."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         UPLOADING DATA TO CLOUDFLARE R2                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize R2
    print("Initializing R2 storage...")
    try:
        r2 = R2Storage()
        print("✅ R2 client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize R2: {e}")
        return False
    
    print()
    
    # Test connection first
    print("Testing R2 connection...")
    if not r2.test_connection():
        print("❌ R2 connection test failed. Please check credentials.")
        return False
    print("✅ Connection verified")
    print()
    
    print("═" * 66)
    print()
    
    # ========================================
    # PART 1: Upload Documents
    # ========================================
    
    print("📤 PART 1: Uploading Documents")
    print("─" * 66)
    
    documents_dir = Path('ocr_storage/documents')
    if not documents_dir.exists():
        print("❌ Documents directory not found!")
        return False
    
    doc_files = list(documents_dir.glob('*.json'))
    total_docs = len(doc_files)
    
    print(f"Found {total_docs} documents to upload...")
    print()
    
    uploaded_docs = 0
    failed_docs = 0
    
    for i, doc_file in enumerate(doc_files, 1):
        doc_id = doc_file.stem
        
        try:
            with open(doc_file) as f:
                doc_data = json.load(f)
            
            if r2.save_document(doc_id, doc_data):
                uploaded_docs += 1
                
                # Progress indicator every 10 documents
                if i % 10 == 0 or i == total_docs:
                    progress = (i / total_docs) * 100
                    print(f"   [{i:3d}/{total_docs}] {progress:5.1f}% - {doc_id}")
            else:
                failed_docs += 1
                print(f"   ❌ Failed: {doc_id}")
        
        except Exception as e:
            failed_docs += 1
            print(f"   ❌ Error uploading {doc_id}: {e}")
    
    print()
    print(f"✅ Documents uploaded: {uploaded_docs}/{total_docs}")
    if failed_docs > 0:
        print(f"⚠️  Failed: {failed_docs}")
    print()
    
    print("═" * 66)
    print()
    
    # ========================================
    # PART 2: Upload Images
    # ========================================
    
    print("📤 PART 2: Uploading Images")
    print("─" * 66)
    
    images_dir = Path('letters/work')
    if not images_dir.exists():
        print("❌ Images directory not found!")
        return False
    
    image_files = list(images_dir.glob('*.png'))
    total_images = len(image_files)
    
    print(f"Found {total_images} images to upload...")
    print(f"Estimated size: ~{total_images * 6.5:.0f} MB (~6.5 MB per image)")
    print(f"Estimated time: ~{total_images * 5 / 60:.1f} minutes (at ~5 sec per image)")
    print()
    
    # Check for --yes flag or AUTO_CONFIRM env var
    import sys
    auto_confirm = '--yes' in sys.argv or os.getenv('AUTO_CONFIRM', 'false').lower() == 'true'
    
    if not auto_confirm:
        confirm = input("This will upload all images to R2. Continue? [y/N]: ")
        if confirm.lower() != 'y':
            print("Upload cancelled.")
            return False
    else:
        print("✅ Auto-confirmed (--yes flag or AUTO_CONFIRM=true)")
    
    print()
    
    uploaded_images = 0
    failed_images = 0
    start_time = datetime.now()
    
    for i, image_file in enumerate(image_files, 1):
        try:
            if r2.upload_image_from_file(image_file):
                uploaded_images += 1
                
                # Progress indicator every 50 images
                if i % 50 == 0 or i == total_images:
                    progress = (i / total_images) * 100
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_images - i) / rate if rate > 0 else 0
                    eta_mins = eta_seconds / 60
                    
                    print(f"   [{i:4d}/{total_images}] {progress:5.1f}% - "
                          f"Rate: {rate:.1f} img/sec - ETA: {eta_mins:.1f} min")
            else:
                failed_images += 1
                if failed_images <= 10:  # Only show first 10 failures
                    print(f"   ❌ Failed: {image_file.name}")
        
        except Exception as e:
            failed_images += 1
            if failed_images <= 10:
                print(f"   ❌ Error uploading {image_file.name}: {e}")
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    
    print()
    print(f"✅ Images uploaded: {uploaded_images}/{total_images}")
    if failed_images > 0:
        print(f"⚠️  Failed: {failed_images}")
    print(f"⏱️  Total time: {elapsed_total / 60:.1f} minutes")
    print()
    
    print("═" * 66)
    print()
    
    # ========================================
    # PART 3: Upload Metadata
    # ========================================
    
    print("📤 PART 3: Uploading Metadata")
    print("─" * 66)
    
    metadata_file = Path('ocr_storage/metadata.json')
    if not metadata_file.exists():
        print("❌ Metadata file not found!")
        return False
    
    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        print(f"Metadata stats:")
        print(f"   • People: {len(metadata.get('people', {}))}")
        print(f"   • References: {sum(len(refs) for refs in metadata.get('references', {}).values())}")
        print(f"   • Documents: {len(metadata.get('documents', {}))}")
        print()
        
        if r2.save_metadata(metadata):
            print("✅ Metadata uploaded successfully")
        else:
            print("❌ Metadata upload failed")
            return False
    
    except Exception as e:
        print(f"❌ Error uploading metadata: {e}")
        return False
    
    print()
    print("═" * 66)
    print()
    
    # ========================================
    # FINAL STATS
    # ========================================
    
    print("📊 FINAL STATISTICS")
    print("─" * 66)
    
    stats = r2.get_storage_stats()
    print(f"   • Documents in R2: {stats['documents']}")
    print(f"   • Images in R2: {stats['images']}")
    print(f"   • Total storage used: {stats['total_size_mb']} MB")
    print(f"   • Free tier limit: 10,000 MB")
    print(f"   • Usage: {(stats['total_size_mb'] / 10000) * 100:.1f}%")
    print()
    
    print("═" * 66)
    print()
    print("🎉 DATA MIGRATION COMPLETE!")
    print()
    print("Next steps:")
    print("  1. Set USE_R2=true in Render environment variables")
    print("  2. Deploy your app to Render")
    print("  3. Test that everything works")
    print()
    
    return True


if __name__ == '__main__':
    success = upload_all_data()
    sys.exit(0 if success else 1)

