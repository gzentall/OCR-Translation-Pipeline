#!/usr/bin/env python3

"""
Setup script for Notion integration - Free Tier Version.
This version creates a simple page instead of databases, which works better with free tier limitations.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.notion_client import NotionClient


def create_simple_page(client, parent_page_id, title, content):
    """Create a simple page in Notion (works with free tier)."""
    try:
        data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]
        }
        
        result = client._make_request('POST', '/pages', data)
        return result
        
    except Exception as e:
        print(f"Error creating page: {e}")
        return None


def main():
    """Set up Notion integration for free tier."""
    print("🚀 Setting up Notion Integration (Free Tier Version)")
    print("=" * 55)
    
    try:
        # Initialize Notion client
        print("📡 Connecting to Notion...")
        client = NotionClient()
        print("✅ Connected to Notion successfully!")
        
        # Get parent page ID from user
        print("\n📄 This version creates simple pages instead of databases.")
        print("   This works better with Notion's free tier limitations.")
        
        page_id = input("\n🔑 Enter your Notion page ID: ").strip()
        
        if not page_id:
            print("❌ No page ID provided. Exiting.")
            return
        
        # Clean up the page ID
        page_id = page_id.split('?')[0].split('/')[-1]
        
        print(f"\n🏗️  Creating OCR pages in: {page_id}")
        
        # Create a main OCR page
        main_page = create_simple_page(
            client, 
            page_id, 
            "OCR Translation Pipeline", 
            "This is your OCR Translation Pipeline workspace. Processed documents will be stored here as individual pages."
        )
        
        if main_page:
            print(f"✅ Main OCR page created: {main_page['id']}")
            
            # Create a sample document page
            sample_page = create_simple_page(
                client,
                main_page['id'],
                "Sample Document - 2024-01-01",
                "This is a sample document page. When you process documents through the OCR pipeline, they will appear as pages like this with:\n\n• Original text\n• Translated text\n• Processing metadata\n• People mentioned\n• AI-generated summary"
            )
            
            if sample_page:
                print(f"✅ Sample document page created: {sample_page['id']}")
            
            # Save configuration
            config_file = Path('.notion_config')
            with open(config_file, 'w') as f:
                f.write(f"main_page_id={main_page['id']}\n")
                f.write(f"parent_page_id={page_id}\n")
                f.write(f"free_tier_mode=true\n")
            
            print(f"\n💾 Configuration saved to: {config_file}")
            print("\n✅ Free tier setup complete!")
            print("\n📝 How it works:")
            print("   • Each processed document becomes a new page")
            print("   • Pages are organized under the main OCR page")
            print("   • No complex databases needed")
            print("   • Works with Notion free tier")
            
        else:
            print("❌ Failed to create main page")
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure your Notion API key is correct")
        print("   2. Ensure the page is shared with your integration")
        print("   3. Check that the page ID is correct")
        print("   4. Verify you have permission to create pages")


if __name__ == "__main__":
    main()
