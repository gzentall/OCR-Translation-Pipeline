#!/usr/bin/env python3

"""
Setup script for Notion integration.
Creates the OCR Documents and People databases in your Notion workspace.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.notion_client import NotionClient, OCRNotionManager


def main():
    """Set up Notion databases for the OCR pipeline."""
    print("🚀 Setting up Notion Integration for OCR Translation Pipeline")
    print("=" * 60)
    
    try:
        # Initialize Notion client
        print("📡 Connecting to Notion...")
        client = NotionClient()
        manager = OCRNotionManager(client)
        print("✅ Connected to Notion successfully!")
        
        # Get parent page ID from user
        print("\n📄 To create the databases, I need a Notion page ID.")
        print("   This should be a page where you want the databases to be created.")
        print("\n   To get a page ID:")
        print("   1. Open the page in Notion")
        print("   2. Copy the URL")
        print("   3. The page ID is the long string after the last '/' in the URL")
        print("   4. Remove any query parameters (everything after '?')")
        print("\n   Example: https://notion.so/your-workspace/Page-Title-abc123def456")
        print("            Page ID: abc123def456")
        
        page_id = input("\n🔑 Enter the Notion page ID: ").strip()
        
        if not page_id:
            print("❌ No page ID provided. Exiting.")
            return
        
        # Clean up the page ID (remove any extra characters)
        page_id = page_id.split('?')[0].split('/')[-1]
        
        print(f"\n🏗️  Creating databases in page: {page_id}")
        print("   This will create:")
        print("   - OCR Documents database (for storing processed documents)")
        print("   - People database (for tracking people mentioned across documents)")
        
        # Create the databases
        result = manager.setup_databases(page_id)
        
        print("\n🎉 Databases created successfully!")
        print(f"   📊 OCR Documents Database ID: {result['documents_db_id']}")
        print(f"   👥 People Database ID: {result['people_db_id']}")
        
        # Save the database IDs for later use
        config_file = Path('.notion_config')
        with open(config_file, 'w') as f:
            f.write(f"documents_db_id={result['documents_db_id']}\n")
            f.write(f"people_db_id={result['people_db_id']}\n")
            f.write(f"parent_page_id={page_id}\n")
        
        print(f"\n💾 Configuration saved to: {config_file}")
        print("\n✅ Setup complete! Your OCR pipeline is now ready to use Notion.")
        print("\n📝 Next steps:")
        print("   1. Test the integration by processing a document")
        print("   2. Check your Notion page to see the new databases")
        print("   3. The databases will be populated automatically when you process documents")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure your Notion API key is correct")
        print("   2. Ensure the page is shared with your integration")
        print("   3. Check that the page ID is correct")
        print("   4. Verify you have permission to create databases in that page")


if __name__ == "__main__":
    main()
