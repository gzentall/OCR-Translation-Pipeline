
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
        """Generate a descriptive summary using rule-based methods."""
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if len(non_empty_lines) == 0:
            return "No readable content found in document"
        
        # Extract key information
        first_line = non_empty_lines[0]
        last_line = non_empty_lines[-1] if len(non_empty_lines) > 1 else ""
        
        # Look for letter patterns (Dear, To, From, etc.)
        letter_indicators = []
        if re.search(r'\b(dear|to|from|my dear|dearest)\b', first_line.lower()):
            letter_indicators.append("appears to be a personal letter")
        
        # Look for names in the first few lines
        names = self.extract_people_names(text)
        name_info = ""
        if names:
            # Filter out common letter openings
            filtered_names = []
            for person in names[:3]:
                name = person['name']
                if not any(word in name.lower() for word in ['dear', 'to', 'from', 'my dear', 'dearest']):
                    filtered_names.append(name)
            if filtered_names:
                name_info = f" involving {', '.join(filtered_names)}"
        
        # Look for common topics/keywords
        topics = []
        text_lower = text.lower()
        
        # Family topics
        if any(word in text_lower for word in ['family', 'mother', 'father', 'brother', 'sister', 'son', 'daughter']):
            topics.append("family matters")
        
        # Business topics
        if any(word in text_lower for word in ['business', 'money', 'payment', 'account', 'work', 'job']):
            topics.append("business/financial matters")
        
        # Health topics
        if any(word in text_lower for word in ['health', 'sick', 'ill', 'doctor', 'medicine', 'hospital']):
            topics.append("health concerns")
        
        # Travel topics
        if any(word in text_lower for word in ['travel', 'trip', 'journey', 'visit', 'arrive', 'depart']):
            topics.append("travel plans")
        
        # Dates and locations
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, text_lower)
        
        location_pattern = r'\b(in|at|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        locations = re.findall(location_pattern, text)
        
        # Build descriptive summary
        summary_parts = []
        
        # Document type and participants
        if letter_indicators:
            summary_parts.append(f"This {letter_indicators[0]}{name_info}")
        elif name_info:
            summary_parts.append(f"Document{name_info}")
        else:
            summary_parts.append("Document")
        
        # Topics discussed
        if topics:
            summary_parts.append(f"discusses {', '.join(topics)}")
        
        # Dates mentioned
        if dates:
            summary_parts.append(f"mentions dates: {', '.join(dates[:2])}")  # First 2 dates
        
        # Locations mentioned
        if locations:
            location_names = [loc[1] for loc in locations[:2]]  # First 2 locations
            summary_parts.append(f"references locations: {', '.join(location_names)}")
        
        # Document length
        word_count = len(text.split())
        if word_count > 0:
            summary_parts.append(f"({word_count} words)")
        
        return ". ".join(summary_parts) + "."
    
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
