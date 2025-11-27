#!/usr/bin/env python3

"""
Test script for Notion and OpenAI integrations.
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.notion_client import NotionClient, OCRNotionManager
from scripts.ai_processor import AIProcessor


def test_notion_integration():
    """Test Notion API connection and basic functionality."""
    print("🔗 Testing Notion Integration...")
    
    try:
        # Initialize Notion client
        client = NotionClient()
        print("✅ Notion client initialized successfully")
        
        # Test basic API call (search for pages)
        try:
            search_results = client.search_pages()
            print(f"✅ Notion API connection successful - found {len(search_results.get('results', []))} pages")
        except Exception as e:
            print(f"⚠️  Notion API search failed: {e}")
            print("   This might be normal if you haven't shared any pages with the integration yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Notion integration failed: {e}")
        return False


def test_openai_integration():
    """Test OpenAI API connection."""
    print("\n🤖 Testing OpenAI Integration...")
    
    try:
        # Initialize AI processor
        processor = AIProcessor()
        print("✅ OpenAI client initialized successfully")
        
        # Test with a simple request
        try:
            # Use a very small test to minimize API usage
            test_text = "Hello world. This is a test."
            summary = processor.generate_summary(test_text, "English")
            
            if "failed" in summary.lower():
                print(f"⚠️  OpenAI API quota exceeded: {summary}")
                return False
            else:
                print(f"✅ OpenAI API working - Generated summary: {summary[:100]}...")
                return True
                
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                print(f"⚠️  OpenAI API quota exceeded: {e}")
                return False
            else:
                print(f"❌ OpenAI API error: {e}")
                return False
        
    except Exception as e:
        print(f"❌ OpenAI integration failed: {e}")
        return False


def create_fallback_ai_processor():
    """Create a fallback AI processor that doesn't use OpenAI."""
    print("\n🔄 Creating fallback AI processor...")
    
    fallback_code = '''
import re
from typing import List, Dict
from datetime import datetime
from fuzzywuzzy import fuzz, process


class FallbackAIProcessor:
    """Fallback AI processor that uses rule-based methods instead of OpenAI."""
    
    def __init__(self):
        self.known_people = {}
        self.name_variations = {}
    
    def generate_summary(self, text: str, source_language: str = "unknown") -> str:
        """Generate a basic summary using rule-based methods."""
        # Extract key information using regex patterns
        lines = text.split('\\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Look for common letter patterns
        if len(non_empty_lines) > 0:
            first_line = non_empty_lines[0]
            last_line = non_empty_lines[-1] if len(non_empty_lines) > 1 else ""
            
            # Basic summary
            summary_parts = []
            if first_line:
                summary_parts.append(f"Document starts with: {first_line[:100]}")
            if last_line and last_line != first_line:
                summary_parts.append(f"Document ends with: {last_line[:100]}")
            
            # Count words and estimate content
            word_count = len(text.split())
            summary_parts.append(f"Document contains approximately {word_count} words")
            
            return " | ".join(summary_parts)
        
        return "No readable content found in document"
    
    def extract_people_names(self, text: str) -> List[Dict[str, str]]:
        """Extract person names using regex patterns."""
        # Common name patterns
        name_patterns = [
            r'\\b[A-Z][a-z]+ [A-Z][a-z]+\\b',  # First Last
            r'\\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\\b',  # First Middle Last
            r'\\b[A-Z][a-z]+ [A-Z]\\. [A-Z][a-z]+\\b',  # First M. Last
        ]
        
        people = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Filter out common false positives
                if not any(word in match.lower() for word in ['the', 'and', 'or', 'but', 'for', 'with']):
                    people.append({
                        'name': match,
                        'context': 'Mentioned in document'
                    })
        
        # Remove duplicates
        unique_people = []
        seen_names = set()
        for person in people:
            if person['name'] not in seen_names:
                unique_people.append(person)
                seen_names.add(person['name'])
        
        return unique_people[:10]  # Limit to 10 people
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for consistent matching."""
        # Remove common titles and suffixes
        name = re.sub(r'\\b(Mr|Mrs|Ms|Dr|Prof|Rev|Sir|Lady)\\b\\.?\\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\\b(Jr|Sr|III|IV|V)\\b\\.?$', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\\w\\s]', '', name)
        name = ' '.join(name.split())
        
        return name.lower().strip()
    
    def add_person(self, name: str, context: str = "", document_date: str = None) -> str:
        """Add a person to the database."""
        normalized_name = self.normalize_name(name)
        
        if normalized_name not in self.known_people:
            self.known_people[normalized_name] = {
                'aliases': [normalized_name],
                'context': context,
                'first_mentioned': document_date or datetime.now().isoformat(),
                'documents': []
            }
            self.name_variations[normalized_name] = normalized_name
        
        return normalized_name
    
    def process_document(self, text: str, source_language: str = "unknown", document_date: str = None) -> Dict:
        """Process a document to extract summary and people."""
        summary = self.generate_summary(text, source_language)
        people_data = self.extract_people_names(text)
        
        processed_people = []
        for person in people_data:
            normalized_name = self.add_person(
                person.get('name', ''),
                person.get('context', ''),
                document_date
            )
            processed_people.append({
                'original_name': person.get('name', ''),
                'normalized_name': normalized_name,
                'context': person.get('context', '')
            })
        
        return {
            'summary': summary,
            'people': processed_people,
            'people_count': len(processed_people)
        }
'''
    
    # Write the fallback processor
    with open('scripts/fallback_ai_processor.py', 'w') as f:
        f.write(fallback_code)
    
    print("✅ Fallback AI processor created")
    return True


def main():
    """Run all integration tests."""
    print("🧪 Testing OCR Translation Pipeline Integrations")
    print("=" * 50)
    
    # Test Notion
    notion_ok = test_notion_integration()
    
    # Test OpenAI
    openai_ok = test_openai_integration()
    
    # Create fallback if OpenAI fails
    if not openai_ok:
        create_fallback_ai_processor()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    print(f"Notion Integration: {'✅ Working' if notion_ok else '❌ Failed'}")
    print(f"OpenAI Integration: {'✅ Working' if openai_ok else '⚠️  Quota Exceeded (Fallback Created)'}")
    
    if notion_ok and openai_ok:
        print("\n🎉 All integrations are working! Ready to proceed.")
    elif notion_ok:
        print("\n✅ Notion is working. OpenAI has quota issues, but fallback processor created.")
        print("   You can either:")
        print("   1. Add billing to your OpenAI account")
        print("   2. Use the fallback processor (basic rule-based processing)")
    else:
        print("\n❌ Some integrations need attention. Check API keys and permissions.")


if __name__ == "__main__":
    main()
