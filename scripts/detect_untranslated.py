#!/usr/bin/env python3

"""
Untranslated Text Detection Module for OCR Translation Pipeline.
Uses LLM to identify words/phrases that weren't translated and remain in the original language.
"""

import os
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()


class UntranslatedTextDetector:
    """Detect untranslated words/phrases in translated documents using LLM."""
    
    # Language code to full name mapping
    LANGUAGE_NAMES = {
        'fr': 'French',
        'fre': 'French',
        'de': 'German',
        'ger': 'German',
        'es': 'Spanish',
        'spa': 'Spanish',
        'it': 'Italian',
        'ita': 'Italian',
        'pl': 'Polish',
        'pol': 'Polish',
        'ru': 'Russian',
        'rus': 'Russian',
        'en': 'English',
        'eng': 'English',
    }
    
    def __init__(self, api_key: str = None):
        """Initialize detector with OpenAI API key."""
        self.api_key = api_key or self._get_api_key()
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        return api_key.strip()
    
    def _get_language_name(self, code: str) -> str:
        """Convert language code to full name."""
        return self.LANGUAGE_NAMES.get(code.lower(), code)
    
    def detect_untranslated_text(
        self, 
        translated_text: str, 
        original_text: str = None,
        source_language: str = "unknown"
    ) -> List[Dict]:
        """
        Use LLM to identify words/phrases that remain untranslated.
        
        Args:
            translated_text: The English translation to analyze
            original_text: Optional original language text for context
            source_language: The source language code (e.g., 'fr', 'de')
            
        Returns:
            List of dicts with {text, start, end, original_language, suggestion}
        """
        if not translated_text or len(translated_text.strip()) < 10:
            return []
        
        lang_name = self._get_language_name(source_language)
        
        # Build the prompt
        prompt = self._build_detection_prompt(translated_text, original_text, lang_name)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert linguist specializing in translation quality analysis. 
Your task is to identify words or phrases in translated text that were NOT properly translated 
and remain in the original language (typically French, German, Spanish, Italian, Polish, or Russian).

IMPORTANT DISTINCTIONS:
- DO flag: Foreign words that should have been translated (e.g., "maison" should be "house")
- DO flag: Partial translations where foreign words are mixed with English
- DO NOT flag: Proper nouns (names of people, places, organizations)
- DO NOT flag: Intentionally preserved terms (e.g., "Mademoiselle" as a title, "café" as a loanword)
- DO NOT flag: Common loanwords accepted in English (café, ballet, renaissance, etc.)

Return ONLY valid JSON. No markdown, no explanation."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Extract and validate markers
            markers = result.get('untranslated', [])
            validated_markers = self._validate_and_position_markers(markers, translated_text, source_language)
            
            return validated_markers
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"  ⚠️  Detection error: {e}")
            return []
    
    def _build_detection_prompt(
        self, 
        translated_text: str, 
        original_text: str,
        lang_name: str
    ) -> str:
        """Build the LLM prompt for detection."""
        
        # Truncate long texts
        max_length = 6000
        if len(translated_text) > max_length:
            translated_text = translated_text[:max_length] + "\n\n[... text truncated ...]"
        
        prompt = f"""Analyze this English translation and identify any words or phrases that were NOT translated and remain in {lang_name} or another foreign language.

TRANSLATED TEXT (should be English):
\"\"\"
{translated_text}
\"\"\"
"""
        
        if original_text:
            orig_preview = original_text[:2000] if len(original_text) > 2000 else original_text
            prompt += f"""
ORIGINAL TEXT (for reference - in {lang_name}):
\"\"\"
{orig_preview}
\"\"\"
"""
        
        prompt += """
Return a JSON object with this structure:
{
  "untranslated": [
    {
      "text": "the exact untranslated word/phrase as it appears",
      "suggestion": "suggested English translation",
      "reason": "brief explanation why this should be translated"
    }
  ],
  "analysis": "brief overall assessment of translation quality"
}

If there are no untranslated words/phrases, return: {"untranslated": [], "analysis": "Translation appears complete"}
"""
        
        return prompt
    
    def _validate_and_position_markers(
        self, 
        markers: List[Dict], 
        translated_text: str,
        source_language: str
    ) -> List[Dict]:
        """Validate markers and add position information."""
        validated = []
        
        for marker in markers:
            text = marker.get('text', '')
            if not text:
                continue
            
            # Find all occurrences in the translated text
            start = 0
            while True:
                pos = translated_text.find(text, start)
                if pos == -1:
                    # Try case-insensitive search
                    lower_text = translated_text.lower()
                    pos = lower_text.find(text.lower(), start)
                    if pos == -1:
                        break
                
                validated.append({
                    'text': text,
                    'start': pos,
                    'end': pos + len(text),
                    'original_language': source_language,
                    'suggestion': marker.get('suggestion', ''),
                    'reason': marker.get('reason', '')
                })
                
                start = pos + len(text)
                
                # Only find first occurrence to avoid duplicates
                break
        
        # Sort by position
        validated.sort(key=lambda x: x['start'])
        
        return validated


def detect_untranslated_text(
    translated_text: str,
    original_text: str = None,
    source_language: str = "unknown"
) -> List[Dict]:
    """
    Convenience function to detect untranslated text.
    
    Args:
        translated_text: The English translation to analyze
        original_text: Optional original language text for context
        source_language: The source language code
        
    Returns:
        List of marker dicts with {text, start, end, original_language, suggestion}
    """
    detector = UntranslatedTextDetector()
    return detector.detect_untranslated_text(translated_text, original_text, source_language)


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect untranslated text in translations')
    parser.add_argument('--text', type=str, help='Text to analyze')
    parser.add_argument('--file', type=str, help='File containing text to analyze')
    parser.add_argument('--lang', type=str, default='fr', help='Source language code')
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        # Demo text
        text = """
        My dear friend, I received your lettre yesterday. The weather here in Paris is 
        très magnifique. I hope to see you bientôt at the maison. The children are 
        doing well and send their amour. Please give my regards to your famille.
        """
        print("Using demo text with French words mixed in...")
    
    print(f"\nAnalyzing text ({len(text)} chars)...")
    print("-" * 60)
    
    detector = UntranslatedTextDetector()
    markers = detector.detect_untranslated_text(text, source_language=args.lang)
    
    if markers:
        print(f"\n✅ Found {len(markers)} untranslated word(s)/phrase(s):\n")
        for i, marker in enumerate(markers, 1):
            print(f"  {i}. \"{marker['text']}\"")
            print(f"     Position: {marker['start']}-{marker['end']}")
            if marker.get('suggestion'):
                print(f"     Suggestion: {marker['suggestion']}")
            if marker.get('reason'):
                print(f"     Reason: {marker['reason']}")
            print()
    else:
        print("\n✅ No untranslated text detected - translation appears complete.")

