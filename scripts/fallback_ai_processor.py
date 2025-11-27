
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
        lines = text.split('\n')
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
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
            r'\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b',  # First Middle Last
            r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',  # First M. Last
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
        name = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Rev|Sir|Lady)\b\.?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|III|IV|V)\b\.?$', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', '', name)
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
