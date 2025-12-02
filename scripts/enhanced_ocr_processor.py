#!/usr/bin/env python3

"""
Enhanced OCR Processor for OCR Translation Pipeline.
Post-processes OCR results using LLMs to correct handwriting recognition errors.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Claude support disabled.")


class EnhancedOCRProcessor:
    """
    Post-process OCR results with LLM-based contextual correction.
    
    Uses OpenAI GPT-4 and/or Claude to intelligently correct OCR errors
    by understanding document context and using reference data.
    """
    
    def __init__(self, provider='openai', context_file='context/reference_data.json'):
        """
        Initialize the enhanced OCR processor.
        
        Args:
            provider: 'openai', 'claude', or 'both'
            context_file: Path to reference data JSON file
        """
        self.provider = provider.lower()
        self.reference_context = self._load_context(context_file)
        
        # Initialize API clients
        if self.provider in ['openai', 'both']:
            self.openai_client = self._init_openai()
        
        if self.provider in ['claude', 'both']:
            if ANTHROPIC_AVAILABLE:
                self.claude_client = self._init_claude()
            else:
                print("Warning: Claude requested but anthropic not available. Falling back to OpenAI.")
                self.provider = 'openai'
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key_file = Path('.openai_api_key')
            if api_key_file.exists():
                api_key = api_key_file.read_text().strip()
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .openai_api_key file")
        
        return openai.OpenAI(api_key=api_key)
    
    def _init_claude(self):
        """Initialize Claude (Anthropic) client."""
        if not ANTHROPIC_AVAILABLE:
            return None
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            api_key_file = Path('.anthropic_api_key')
            if api_key_file.exists():
                api_key = api_key_file.read_text().strip()
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or .anthropic_api_key file")
        
        return anthropic.Anthropic(api_key=api_key)
    
    def _load_context(self, context_file: str) -> dict:
        """Load reference context data from JSON file."""
        context_path = Path(context_file)
        if not context_path.exists():
            print(f"Warning: Context file not found: {context_file}")
            return self._get_default_context()
        
        try:
            with open(context_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading context file: {e}")
            return self._get_default_context()
    
    def _get_default_context(self) -> dict:
        """Return default context if file not available."""
        return {
            "people": [],
            "locations": [],
            "common_phrases": {"greetings": [], "closings": []},
            "historical_period": "unknown",
            "languages": ["English"]
        }
    
    def correct_with_context(self, ocr_text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Correct OCR errors using document context and reference data.
        
        Args:
            ocr_text: Raw OCR output from Google Vision
            metadata: Optional metadata dict with keys:
                - document_type: 'letter', 'document', etc.
                - date: Document date
                - expected_language: Primary language
                
        Returns:
            {
                'corrected_text': str,
                'confidence': float (0-100),
                'corrections': [{'original': str, 'corrected': str, 'reason': str}],
                'uncertain_segments': [str],
                'provider_used': str
            }
        """
        if metadata is None:
            metadata = {}
        
        # Choose correction method based on provider
        if self.provider == 'both':
            return self._correct_with_both(ocr_text, metadata)
        elif self.provider == 'claude':
            return self._correct_with_claude(ocr_text, metadata)
        else:  # openai
            return self._correct_with_openai(ocr_text, metadata)
    
    def _build_correction_prompt(self, ocr_text: str, metadata: Dict) -> str:
        """
        Build the correction prompt with context from reference data.
        
        This is the key to good corrections - providing enough context
        for the LLM to make intelligent decisions.
        """
        # Extract known entities from reference context
        known_people = []
        for person in self.reference_context.get('people', []):
            known_people.extend(person.get('variations', [person['name']]))
        
        known_locations = []
        for location in self.reference_context.get('locations', []):
            if 'address' in location:
                known_locations.append(location['address'])
            if 'city' in location:
                known_locations.append(location['city'])
            known_locations.extend(location.get('variations', []))
        
        common_greetings = self.reference_context.get('common_phrases', {}).get('greetings', [])
        common_closings = self.reference_context.get('common_phrases', {}).get('closings', [])
        
        # Build prompt
        prompt = f"""You are correcting OCR errors from a handwritten historical document.

Document Context:
- Type: {metadata.get('document_type', 'personal letter')}
- Date: {metadata.get('date', 'unknown')}
- Language: {metadata.get('expected_language', 'English')}
- Historical Period: {self.reference_context.get('historical_period', 'unknown')}

Known People (family members who might be mentioned):
{', '.join(known_people) if known_people else 'None specified'}

Known Locations (addresses/cities that might appear):
{', '.join(known_locations[:5]) if known_locations else 'None specified'}

Common Greetings in these documents:
{', '.join(common_greetings) if common_greetings else 'Dear, Dearest, etc.'}

Common Closings:
{', '.join(common_closings) if common_closings else 'Love, Best regards, etc.'}

OCR Text (contains errors from handwriting recognition):
{ocr_text}

Instructions:
1. Fix obvious OCR errors (character misreads like "jour" -> "your", gibberish, wrong alphabet)
2. Use the context above - known names, locations, common phrases
3. Preserve ALL formatting, line breaks, and spacing EXACTLY as in the original
4. For very uncertain corrections where multiple interpretations are possible, mark with [?]
5. Keep truly illegible text as [illegible]
6. Do NOT add or remove content - only correct errors

Respond in JSON format:
{{
  "corrected_text": "the corrected document with exact formatting preserved",
  "corrections": [
    {{"original": "text-with-error", "corrected": "fixed-text", "reason": "explanation"}},
  ],
  "confidence": 85,
  "uncertain_segments": ["any segments marked with [?]"]
}}

Important: Return ONLY the JSON, no other text before or after."""

        return prompt
    
    def _correct_with_openai(self, ocr_text: str, metadata: Dict, retry_count: int = 0) -> Dict:
        """Correct text using OpenAI GPT-4 with resilient error handling."""
        prompt = self._build_correction_prompt(ocr_text, metadata)
        
        # If text is very long, truncate it to avoid issues
        max_input_length = 10000
        if len(ocr_text) > max_input_length:
            print(f"  ⚠️ Text too long ({len(ocr_text)} chars), truncating to {max_input_length}")
            ocr_text_truncated = ocr_text[:max_input_length] + "\n\n[... text truncated for processing ...]"
            prompt = self._build_correction_prompt(ocr_text_truncated, metadata)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for better performance
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at correcting OCR errors in historical handwritten documents. You understand context and use it to make intelligent corrections. Always return valid JSON with properly escaped strings."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent corrections
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            # Try to parse JSON with resilient error handling
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as je:
                print(f"  ⚠️ JSON parse error: {str(je)[:100]}")
                # Try to extract corrected text even if JSON is malformed
                result = self._extract_from_malformed_json(result_text, ocr_text)
                
                # Retry once with a simpler prompt if this is the first attempt
                if retry_count == 0:
                    print(f"  🔄 Retrying with simplified prompt...")
                    return self._correct_with_openai_simple(ocr_text, metadata)
            
            result['provider_used'] = 'openai'
            return result
            
        except Exception as e:
            print(f"  ❌ Error with OpenAI correction: {str(e)[:200]}")
            return {
                'corrected_text': ocr_text,
                'confidence': 0,
                'corrections': [],
                'uncertain_segments': [],
                'provider_used': 'openai',
                'error': str(e)
            }
    
    def _correct_with_openai_simple(self, ocr_text: str, metadata: Dict) -> Dict:
        """Simplified correction that just asks for corrected text without detailed JSON."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at correcting OCR errors in historical handwritten documents from WWII era. Correct the text but preserve all formatting exactly."
                    },
                    {
                        "role": "user",
                        "content": f"Correct this OCR text from a handwritten letter. Known people: Betty Zentall, Robert Zentall. Known locations: Paris, Agde. This is from WWII correspondence (1939-1942).\n\nReturn ONLY the corrected text, no JSON, no explanations:\n\n{ocr_text[:8000]}"
                    }
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            corrected = response.choices[0].message.content.strip()
            
            # SAFEGUARD: If corrected text is significantly shorter than original (< 30%),
            # something went wrong - fall back to original
            if len(corrected) < len(ocr_text) * 0.3:
                print(f"  ⚠️ Corrected text too short ({len(corrected)} chars vs {len(ocr_text)} original), using original")
                return {
                    'corrected_text': ocr_text,
                    'confidence': 50,
                    'corrections': [],
                    'uncertain_segments': [],
                    'provider_used': 'openai-simple-fallback',
                    'error': 'Corrected text too short - using original'
                }
            
            # Count approximate corrections by comparing word differences
            original_words = set(ocr_text.lower().split())
            corrected_words = set(corrected.lower().split())
            estimated_corrections = len(original_words.symmetric_difference(corrected_words)) // 2
            
            return {
                'corrected_text': corrected,
                'confidence': 75,  # Lower confidence for simple mode
                'corrections': [{'original': 'various', 'corrected': 'various', 'reason': 'Simple correction mode - no detailed tracking'}],
                'uncertain_segments': [],
                'provider_used': 'openai-simple',
                'corrections_count': estimated_corrections
            }
            
        except Exception as e:
            print(f"  ❌ Simple correction also failed: {e}")
            return {
                'corrected_text': ocr_text,
                'confidence': 0,
                'corrections': [],
                'uncertain_segments': [],
                'provider_used': 'openai-simple',
                'error': str(e)
            }
    
    def _extract_from_malformed_json(self, text: str, original_ocr: str) -> Dict:
        """Try to extract useful data from malformed JSON response."""
        result = {
            'corrected_text': original_ocr,
            'confidence': 0,
            'corrections': [],
            'uncertain_segments': [],
            'error': 'Malformed JSON'
        }
        
        # Try to extract corrected_text field even if JSON is broken
        import re
        match = re.search(r'"corrected_text"\s*:\s*"(.*?)"(?=,\s*"|\s*})', text, re.DOTALL)
        if match:
            corrected = match.group(1)
            # Unescape basic JSON escapes
            corrected = corrected.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            result['corrected_text'] = corrected
            result['confidence'] = 60  # Partial confidence since we extracted something
            print(f"  ✓ Extracted corrected text from malformed JSON")
        
        return result
    
    def _correct_with_claude(self, ocr_text: str, metadata: Dict) -> Dict:
        """Correct text using Claude (Anthropic)."""
        if not ANTHROPIC_AVAILABLE or not hasattr(self, 'claude_client'):
            return self._correct_with_openai(ocr_text, metadata)
        
        prompt = self._build_correction_prompt(ocr_text, metadata)
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            result_text = response.content[0].text
            result = json.loads(result_text)
            result['provider_used'] = 'claude'
            
            return result
            
        except Exception as e:
            print(f"Error with Claude correction: {e}")
            return {
                'corrected_text': ocr_text,
                'confidence': 0,
                'corrections': [],
                'uncertain_segments': [],
                'provider_used': 'claude',
                'error': str(e)
            }
    
    def _correct_with_both(self, ocr_text: str, metadata: Dict) -> Dict:
        """
        Run both OpenAI and Claude, compare results, return the best.
        
        Chooses based on confidence score, or merges if similar.
        """
        print("Running corrections with both OpenAI and Claude...")
        
        openai_result = self._correct_with_openai(ocr_text, metadata)
        claude_result = self._correct_with_claude(ocr_text, metadata)
        
        # Compare confidence scores
        openai_confidence = openai_result.get('confidence', 0)
        claude_confidence = claude_result.get('confidence', 0)
        
        if openai_confidence > claude_confidence:
            print(f"Using OpenAI result (confidence: {openai_confidence} vs {claude_confidence})")
            openai_result['comparison'] = {
                'openai_confidence': openai_confidence,
                'claude_confidence': claude_confidence
            }
            return openai_result
        else:
            print(f"Using Claude result (confidence: {claude_confidence} vs {openai_confidence})")
            claude_result['comparison'] = {
                'openai_confidence': openai_confidence,
                'claude_confidence': claude_confidence
            }
            return claude_result
    
    def extract_entities(self, corrected_text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Extract structured entities from corrected text.
        
        Returns:
            {
                'sender': {'name': str, 'location': str},
                'recipient': {'name': str, 'location': str},
                'people_mentioned': [str],
                'locations_mentioned': [str],
                'dates_mentioned': [str],
                'document_summary': str
            }
        """
        if metadata is None:
            metadata = {}
        
        prompt = f"""Extract structured information from this document:

{corrected_text}

Return JSON with:
{{
  "sender": {{"name": "sender name", "location": "sender location"}},
  "recipient": {{"name": "recipient name", "location": "recipient location"}},
  "people_mentioned": ["list", "of", "people"],
  "locations_mentioned": ["list", "of", "locations"],
  "dates_mentioned": ["list", "of", "dates"],
  "document_summary": "2-sentence summary"
}}

Return ONLY the JSON."""

        try:
            if self.provider in ['openai', 'both']:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You extract structured data from documents."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            else:
                response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return json.loads(response.content[0].text)
        
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {
                'sender': {'name': '', 'location': ''},
                'recipient': {'name': '', 'location': ''},
                'people_mentioned': [],
                'locations_mentioned': [],
                'dates_mentioned': [],
                'document_summary': '',
                'error': str(e)
            }


def main():
    """Test the enhanced OCR processor."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_ocr_processor.py <text_file> [--provider openai|claude|both]")
        sys.exit(1)
    
    text_file = sys.argv[1]
    provider = 'openai'
    
    if '--provider' in sys.argv:
        provider = sys.argv[sys.argv.index('--provider') + 1]
    
    # Read OCR text
    with open(text_file, 'r') as f:
        ocr_text = f.read()
    
    # Process
    processor = EnhancedOCRProcessor(provider=provider)
    result = processor.correct_with_context(ocr_text)
    
    # Display results
    print("=" * 80)
    print(f"Provider: {result.get('provider_used')}")
    print(f"Confidence: {result.get('confidence')}%")
    print("=" * 80)
    print("\nCorrected Text:")
    print(result['corrected_text'])
    print("\n" + "=" * 80)
    print(f"\nCorrections made: {len(result.get('corrections', []))}")
    for correction in result.get('corrections', [])[:10]:  # Show first 10
        print(f"  - '{correction['original']}' -> '{correction['corrected']}' ({correction['reason']})")
    
    # Extract entities
    print("\n" + "=" * 80)
    print("Extracting entities...")
    entities = processor.extract_entities(result['corrected_text'])
    print(f"Sender: {entities.get('sender', {}).get('name')}")
    print(f"Recipient: {entities.get('recipient', {}).get('name')}")
    print(f"People mentioned: {', '.join(entities.get('people_mentioned', []))}")
    print(f"Summary: {entities.get('document_summary')}")


if __name__ == "__main__":
    main()

