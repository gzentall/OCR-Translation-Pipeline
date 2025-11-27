#!/usr/bin/env python3

"""
AI processing module for OCR Translation Pipeline.
Handles document summarization, person name extraction, and cross-document analysis.
"""

import re
import os
from typing import List, Dict, Set, Tuple
from datetime import datetime
from fuzzywuzzy import fuzz, process
import openai
from pathlib import Path


class AIProcessor:
    """AI-powered document processing for OCR results."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize AI processor with OpenAI API key."""
        self.api_key = openai_api_key or self._get_api_key()
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Person name tracking
        self.known_people = {}  # normalized_name -> {aliases, first_mentioned, context}
        self.name_variations = {}  # variation -> normalized_name
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from environment or file."""
        # Try environment variable first
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # Try to read from file
        key_file = Path('.openai_api_key')
        if key_file.exists():
            return key_file.read_text().strip()
        
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or create .openai_api_key file")
    
    def generate_summary(self, text: str, source_language: str = "unknown") -> str:
        """Generate a descriptive summary of the document content."""
        try:
            prompt = f"""
            Please provide a detailed summary of the following text. The text appears to be from a {source_language} document that has been translated to English.
            
            Your summary should include:
            1. WHO: Who is writing to whom (sender and recipient)
            2. NATURE: What type of document this is (personal letter, business correspondence, official document, etc.)
            3. TOPICS: What specific topics, subjects, or themes are discussed
            4. CONTEXT: Any important dates, locations, events, or circumstances mentioned
            5. RELATIONSHIP: The relationship between the people involved (family, friends, business associates, etc.)
            
            Format your response as a clear, descriptive paragraph that would help someone quickly understand the document's content and significance.
            
            Text to summarize:
            {text[:3000]}  # Limit to avoid token limits
            
            Summary:
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates detailed, informative summaries of historical documents. Focus on providing context about who is communicating with whom, the nature of their relationship, and what they are discussing."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def extract_people_names(self, text: str) -> List[Dict[str, str]]:
        """Extract person names from text using AI."""
        try:
            prompt = f"""
            Extract all person names from the following text. Return them as a JSON list where each person has:
            - "name": the full name as it appears in the text
            - "context": brief context about who they are or their role
            
            Text:
            {text[:2000]}
            
            Return only valid JSON, no other text.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts person names from text. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse JSON response
            import json
            people_data = json.loads(response.choices[0].message.content.strip())
            return people_data if isinstance(people_data, list) else []
            
        except Exception as e:
            print(f"Error extracting people names: {e}")
            return []
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for consistent matching."""
        # Remove common titles and suffixes
        name = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Rev|Sir|Lady)\b\.?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|III|IV|V)\b\.?$', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        
        return name.lower().strip()
    
    def find_similar_names(self, name: str, threshold: int = 80) -> List[Tuple[str, int]]:
        """Find similar names in the known people database."""
        normalized_name = self.normalize_name(name)
        
        # Check exact matches first
        if normalized_name in self.known_people:
            return [(normalized_name, 100)]
        
        # Check aliases
        for known_name, data in self.known_people.items():
            for alias in data.get('aliases', []):
                if fuzz.ratio(normalized_name, alias) >= threshold:
                    return [(known_name, fuzz.ratio(normalized_name, alias))]
        
        # Fuzzy match against all known names
        matches = []
        for known_name in self.known_people.keys():
            similarity = fuzz.ratio(normalized_name, known_name)
            if similarity >= threshold:
                matches.append((known_name, similarity))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)
    
    def add_person(self, name: str, context: str = "", document_date: str = None) -> str:
        """Add a person to the database, handling name variations."""
        normalized_name = self.normalize_name(name)
        
        # Check if this is a variation of an existing person
        similar_names = self.find_similar_names(name, threshold=85)
        
        if similar_names:
            # This is likely the same person
            existing_name = similar_names[0][0]
            person_data = self.known_people[existing_name]
            
            # Add as alias if not already present
            if normalized_name not in person_data.get('aliases', []):
                person_data.setdefault('aliases', []).append(normalized_name)
            
            # Update context if provided
            if context:
                existing_context = person_data.get('context', '')
                if context not in existing_context:
                    person_data['context'] = f"{existing_context}\n{context}".strip()
            
            # Update first mentioned date if this is earlier
            if document_date:
                current_first = person_data.get('first_mentioned')
                if not current_first or document_date < current_first:
                    person_data['first_mentioned'] = document_date
            
            self.name_variations[normalized_name] = existing_name
            return existing_name
        
        else:
            # New person
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
        # Generate summary
        summary = self.generate_summary(text, source_language)
        
        # Extract people names
        people_data = self.extract_people_names(text)
        
        # Process and normalize people
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
    
    def get_people_database(self) -> Dict:
        """Get the complete people database."""
        return self.known_people
    
    def get_person_timeline(self, person_name: str) -> List[Dict]:
        """Get timeline of documents mentioning a specific person."""
        normalized_name = self.normalize_name(person_name)
        
        if normalized_name not in self.known_people:
            return []
        
        person_data = self.known_people[normalized_name]
        return person_data.get('documents', [])
    
    def search_people(self, query: str, threshold: int = 70) -> List[Tuple[str, int]]:
        """Search for people by name with fuzzy matching."""
        query_normalized = self.normalize_name(query)
        
        matches = []
        for name, data in self.known_people.items():
            # Check main name
            similarity = fuzz.ratio(query_normalized, name)
            if similarity >= threshold:
                matches.append((name, similarity))
            
            # Check aliases
            for alias in data.get('aliases', []):
                similarity = fuzz.ratio(query_normalized, alias)
                if similarity >= threshold:
                    matches.append((name, similarity))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)


def main():
    """Test the AI processor functionality."""
    try:
        processor = AIProcessor()
        print("AI Processor initialized successfully!")
        
        # Test with sample text
        sample_text = """
        Dear John,
        I hope this letter finds you well. I am writing to inform you about the recent developments 
        regarding the family business. Your brother Robert has been handling the accounts, and 
        your sister Mary has been managing the correspondence.
        
        Best regards,
        Elizabeth
        """
        
        result = processor.process_document(sample_text, "English")
        print(f"Summary: {result['summary']}")
        print(f"People found: {result['people']}")
        
    except Exception as e:
        print(f"Error initializing AI Processor: {e}")
        print("\nMake sure you have:")
        print("1. Set the OPENAI_API_KEY environment variable or created .openai_api_key file")
        print("2. Have sufficient OpenAI API credits")


if __name__ == "__main__":
    main()
