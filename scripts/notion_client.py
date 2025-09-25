#!/usr/bin/env python3

"""
Notion API client for OCR Translation Pipeline integration.
Handles creating databases, pages, and managing document storage in Notion.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class NotionClient:
    """Client for interacting with Notion API."""
    
    def __init__(self, api_key: str = None):
        """Initialize Notion client with API key."""
        self.api_key = api_key or self._get_api_key()
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def _get_api_key(self) -> str:
        """Get Notion API key from environment or file."""
        # Try environment variable first
        api_key = os.getenv('NOTION_API_KEY')
        if api_key:
            return api_key
        
        # Try to read from file
        key_file = Path('.notion_api_key')
        if key_file.exists():
            return key_file.read_text().strip()
        
        raise ValueError("Notion API key not found. Set NOTION_API_KEY environment variable or create .notion_api_key file")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to Notion API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Notion API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def create_database(self, parent_page_id: str, title: str, properties: Dict) -> Dict:
        """Create a new database in Notion."""
        data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        
        return self._make_request('POST', '/databases', data)
    
    def create_page(self, parent_id: str, properties: Dict, content_blocks: List[Dict] = None) -> Dict:
        """Create a new page in Notion."""
        data = {
            "parent": {"database_id": parent_id},
            "properties": properties
        }
        
        if content_blocks:
            data["children"] = content_blocks
        
        return self._make_request('POST', '/pages', data)
    
    def add_content_blocks(self, page_id: str, blocks: List[Dict]) -> Dict:
        """Add content blocks to an existing page."""
        data = {"children": blocks}
        return self._make_request('PATCH', f'/blocks/{page_id}/children', data)
    
    def search_pages(self, query: str = "") -> Dict:
        """Search for pages in Notion."""
        data = {"query": query} if query else {}
        return self._make_request('POST', '/search', data)
    
    def get_database(self, database_id: str) -> Dict:
        """Get database information."""
        return self._make_request('GET', f'/databases/{database_id}')
    
    def query_database(self, database_id: str, filter_data: Dict = None, sorts: List[Dict] = None) -> Dict:
        """Query a database with filters and sorting."""
        data = {}
        if filter_data:
            data["filter"] = filter_data
        if sorts:
            data["sorts"] = sorts
        
        return self._make_request('POST', f'/databases/{database_id}/query', data)


class OCRNotionManager:
    """Manager for OCR document storage in Notion."""
    
    def __init__(self, notion_client: NotionClient):
        self.client = notion_client
        self.documents_db_id = None
        self.people_db_id = None
    
    def setup_databases(self, parent_page_id: str) -> Dict[str, str]:
        """Create the OCR Documents and People databases."""
        
        # Define OCR Documents database properties
        documents_properties = {
            "Title": {"title": {}},
            "Date Processed": {"date": {}},
            "Source Language": {
                "select": {
                    "options": [
                        {"name": "German", "color": "blue"},
                        {"name": "English", "color": "green"},
                        {"name": "French", "color": "purple"},
                        {"name": "Spanish", "color": "orange"},
                        {"name": "Italian", "color": "pink"},
                        {"name": "Other", "color": "gray"}
                    ]
                }
            },
            "Target Language": {
                "select": {
                    "options": [
                        {"name": "English", "color": "green"}
                    ]
                }
            },
            "Original Text": {"rich_text": {}},
            "Translated Text": {"rich_text": {}},
            "File Size": {"number": {"format": "byte"}},
            "Processing Status": {
                "select": {
                    "options": [
                        {"name": "Complete", "color": "green"},
                        {"name": "Error", "color": "red"},
                        {"name": "Processing", "color": "yellow"}
                    ]
                }
            },
            "People Mentioned": {"relation": {"database_id": "PLACEHOLDER"}},  # Will be updated after People DB is created
            "Summary": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}}
        }
        
        # Define People database properties
        people_properties = {
            "Name": {"title": {}},
            "Aliases": {"rich_text": {}},
            "First Mentioned": {"date": {}},
            "Documents": {"relation": {"database_id": "PLACEHOLDER"}},  # Will be updated after Documents DB is created
            "Context Notes": {"rich_text": {}}
        }
        
        try:
            # Create People database first
            print("Creating People database...")
            people_db = self.client.create_database(
                parent_page_id=parent_page_id,
                title="People",
                properties=people_properties
            )
            self.people_db_id = people_db["id"]
            print(f"People database created: {self.people_db_id}")
            
            # Create Documents database with reference to People database
            documents_properties["People Mentioned"]["relation"]["database_id"] = self.people_db_id
            people_properties["Documents"]["relation"]["database_id"] = "PLACEHOLDER"  # Will be updated
            
            print("Creating OCR Documents database...")
            documents_db = self.client.create_database(
                parent_page_id=parent_page_id,
                title="OCR Documents",
                properties=documents_properties
            )
            self.documents_db_id = documents_db["id"]
            print(f"OCR Documents database created: {self.documents_db_id}")
            
            # Update People database with reference to Documents database
            people_properties["Documents"]["relation"]["database_id"] = self.documents_db_id
            self.client._make_request('PATCH', f'/databases/{self.people_db_id}', {
                "properties": people_properties
            })
            
            return {
                "documents_db_id": self.documents_db_id,
                "people_db_id": self.people_db_id
            }
            
        except Exception as e:
            print(f"Error creating databases: {e}")
            raise
    
    def add_document(self, document_data: Dict) -> str:
        """Add a processed document to the OCR Documents database."""
        if not self.documents_db_id:
            raise ValueError("Databases not set up. Call setup_databases() first.")
        
        # Prepare properties for the document
        properties = {
            "Title": {
                "title": [{"text": {"content": document_data.get("title", "Untitled Document")}}]
            },
            "Date Processed": {
                "date": {"start": document_data.get("date_processed", datetime.now().isoformat())}
            },
            "Source Language": {
                "select": {"name": document_data.get("source_language", "Unknown")}
            },
            "Target Language": {
                "select": {"name": document_data.get("target_language", "English")}
            },
            "Original Text": {
                "rich_text": [{"text": {"content": document_data.get("original_text", "")[:2000]}}]  # Notion limit
            },
            "Translated Text": {
                "rich_text": [{"text": {"content": document_data.get("translated_text", "")[:2000]}}]  # Notion limit
            },
            "File Size": {
                "number": document_data.get("file_size", 0)
            },
            "Processing Status": {
                "select": {"name": document_data.get("status", "Complete")}
            },
            "Summary": {
                "rich_text": [{"text": {"content": document_data.get("summary", "")}}]
            }
        }
        
        # Add tags if provided
        if document_data.get("tags"):
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in document_data["tags"]]
            }
        
        # Create content blocks for full text (since properties have length limits)
        content_blocks = []
        
        if document_data.get("original_text"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Original Text"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": document_data["original_text"]}}]}
                }
            ])
        
        if document_data.get("translated_text"):
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Translated Text"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": document_data["translated_text"]}}]}
                }
            ])
        
        try:
            # Create the page
            page = self.client.create_page(
                parent_id=self.documents_db_id,
                properties=properties,
                content_blocks=content_blocks
            )
            
            print(f"Document added to Notion: {page['id']}")
            return page['id']
            
        except Exception as e:
            print(f"Error adding document to Notion: {e}")
            raise
    
    def search_documents(self, query: str = "") -> List[Dict]:
        """Search documents in the database."""
        if not self.documents_db_id:
            raise ValueError("Databases not set up. Call setup_databases() first.")
        
        try:
            results = self.client.query_database(self.documents_db_id)
            return results.get("results", [])
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []


def main():
    """Test the Notion client functionality."""
    try:
        # Initialize client
        client = NotionClient()
        manager = OCRNotionManager(client)
        
        print("Notion client initialized successfully!")
        print("To set up databases, you'll need to provide a parent page ID.")
        print("Example usage:")
        print("  manager.setup_databases('your-page-id-here')")
        
    except Exception as e:
        print(f"Error initializing Notion client: {e}")
        print("\nMake sure you have:")
        print("1. Created a Notion integration at https://notion.so/my-integrations")
        print("2. Set the NOTION_API_KEY environment variable or created .notion_api_key file")
        print("3. Shared a Notion page with your integration")


if __name__ == "__main__":
    main()
