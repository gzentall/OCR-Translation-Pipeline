#!/usr/bin/env python3

"""
Envelope Metadata Extractor for OCR Translation Pipeline.
Extracts structured metadata from envelope scans using OCR + LLM analysis.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class EnvelopeExtractor:
    """
    Extract structured metadata from envelope images.
    
    Uses Google Vision OCR to read envelope text, then OpenAI to parse
    and extract structured fields like sender, receiver, addresses, etc.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the envelope extractor."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.openai_client = None
        try:
            self.openai_client = self._init_openai()
        except Exception as e:
            print(f"⚠️  EnvelopeExtractor: Could not initialize OpenAI client: {e}")
            print("⚠️  Metadata extraction will be disabled")
        
    def _init_openai(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key_file = Path('.openai_api_key')
            if api_key_file.exists():
                api_key = api_key_file.read_text().strip()
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        # Validate and clean API key (same as AIProcessor)
        api_key = self._validate_api_key(api_key)
        
        return openai.OpenAI(api_key=api_key)
    
    def _validate_api_key(self, api_key: str) -> str:
        """Validate and clean OpenAI API key."""
        if not api_key:
            raise ValueError("API key is empty")
        
        # Strip all whitespace including newlines
        api_key = ''.join(api_key.split())
        
        # Remove any quotes that might have been included
        api_key = api_key.strip('"\'')
        
        # Validate format - accept both regular keys (sk-*) and project keys (sk-proj-*)
        if not api_key.startswith('sk-'):
            raise ValueError(f"Invalid API key format. OpenAI keys should start with 'sk-'. Got: {api_key[:10]}...")
        
        if len(api_key) < 20:
            raise ValueError("API key appears too short (minimum 20 characters)")
        
        return api_key
    
    def run_ocr_on_image(self, image_path: Path) -> Optional[str]:
        """
        Run Google Vision OCR on an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text or None if OCR fails
        """
        script_path = self.project_root / "scripts" / "run_vision_ocr.sh"
        
        if not script_path.exists():
            print(f"  ⚠️ OCR script not found: {script_path}")
            return None
        
        try:
            # Run the vision OCR script
            result = subprocess.run(
                ['bash', str(script_path), str(image_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"  ⚠️ OCR failed: {result.stderr}")
                return None
            
            # Read the output file (script creates .vision.txt file)
            output_file = image_path.with_suffix('').with_suffix('.vision.txt')
            if output_file.exists():
                return output_file.read_text()
            else:
                return result.stdout
                
        except Exception as e:
            print(f"  ❌ OCR error: {e}")
            return None
    
    def extract_metadata(self, ocr_text: str, document_name: str = "") -> Dict:
        """
        Extract structured metadata from envelope OCR text using LLM.
        
        Args:
            ocr_text: Raw OCR text from envelope
            document_name: Optional document filename for context
            
        Returns:
            Dict with structured envelope metadata
        """
        prompt = f"""You are analyzing an envelope from WWII-era correspondence (1932-1942) between Robert and Betty Zentall (originally Zweigenthal).

Known Context:
- Robert Zentall (Robert Zweigenthal): Soldier in French army, stationed in Agde, France
- Betty Zentall (Betty/Elizabeth Zweigenthal, née Aigner): Wife, lived in Paris
- Common locations: Paris, Agde, Prague, Berlin
- Wartime correspondence, often military mail (S.P. numbers = Secteur Postal)

OCR Text from Envelope:
{ocr_text}

Extract the following structured information:

1. **Sender**: Name of person sending the letter
2. **Sender Location**: City and country where sender was located
3. **Receiver**: Name of person receiving the letter  
4. **Receiver Location**: City/address and country where letter was sent
5. **Date**: Any visible postmark date or written date
6. **Postal Markings**: Military postal codes (S.P.), stamps, postmarks
7. **Return Address**: If visible
8. **Delivery Address**: Complete address if legible

Return JSON:
{{
  "sender": "Name or 'Unknown'",
  "sender_location": "City, Country or 'Unknown'",
  "receiver": "Name or 'Unknown'",
  "receiver_location": "City/Address, Country or 'Unknown'",
  "date": "Date or 'Unknown'",
  "postal_markings": ["Any postal codes, stamps, markings"],
  "return_address": "Full address if visible or 'Unknown'",
  "delivery_address": "Full address if visible or 'Unknown'",
  "confidence": 85,
  "notes": "Any additional observations"
}}

Return ONLY valid JSON, no other text."""

        # Check if OpenAI client is available
        if not self.openai_client:
            print(f"  ⚠️  OpenAI client not available, skipping metadata extraction")
            return {
                'sender': 'Unknown',
                'sender_location': 'Unknown',
                'recipient': 'Unknown',
                'receiver': 'Unknown',  # Keep both for compatibility
                'recipient_location': 'Unknown',
                'receiver_location': 'Unknown',  # Keep both for compatibility
                'date': 'Unknown',
                'postal_markings': [],
                'return_address': 'Unknown',
                'delivery_address': 'Unknown',
                'confidence': 0,
                'notes': 'Metadata extraction disabled - OpenAI API key not available'
            }
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing historical envelopes and extracting structured metadata. You understand WWII-era postal systems and military mail."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            result['document_name'] = document_name
            result['source'] = 'envelope_ocr'
            
            # Ensure both 'receiver' and 'recipient' are present for compatibility
            if 'receiver' in result and 'recipient' not in result:
                result['recipient'] = result['receiver']
            if 'recipient' in result and 'receiver' not in result:
                result['receiver'] = result['recipient']
            if 'receiver_location' in result and 'recipient_location' not in result:
                result['recipient_location'] = result['receiver_location']
            if 'recipient_location' in result and 'receiver_location' not in result:
                result['receiver_location'] = result['recipient_location']
            
            return result
            
        except openai.AuthenticationError as e:
            print(f"  ❌ Metadata extraction authentication error: {e}")
            return {
                'sender': 'Unknown',
                'sender_location': 'Unknown',
                'recipient': 'Unknown',
                'receiver': 'Unknown',
                'recipient_location': 'Unknown',
                'receiver_location': 'Unknown',
                'date': 'Unknown',
                'postal_markings': [],
                'return_address': 'Unknown',
                'delivery_address': 'Unknown',
                'confidence': 0,
                'notes': f'Metadata extraction failed - authentication error: {str(e)}'
            }
        except openai.APIError as e:
            print(f"  ❌ Metadata extraction API error: {e}")
            return {
                'sender': 'Unknown',
                'sender_location': 'Unknown',
                'recipient': 'Unknown',
                'receiver': 'Unknown',
                'recipient_location': 'Unknown',
                'receiver_location': 'Unknown',
                'date': 'Unknown',
                'postal_markings': [],
                'return_address': 'Unknown',
                'delivery_address': 'Unknown',
                'confidence': 0,
                'notes': f'Metadata extraction failed - API error: {str(e)}'
            }
        except Exception as e:
            print(f"  ❌ Metadata extraction error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'sender': 'Unknown',
                'sender_location': 'Unknown',
                'recipient': 'Unknown',
                'receiver': 'Unknown',
                'receiver_location': 'Unknown',
                'date': 'Unknown',
                'postal_markings': [],
                'return_address': 'Unknown',
                'delivery_address': 'Unknown',
                'confidence': 0,
                'notes': f'Extraction failed: {str(e)}',
                'document_name': document_name,
                'source': 'envelope_ocr',
                'error': str(e)
            }
    
    def process_envelope(self, image_path: Path) -> Dict:
        """
        Process an envelope image: OCR + metadata extraction.
        
        Args:
            image_path: Path to envelope image
            
        Returns:
            Dict with envelope metadata
        """
        print(f"\n📧 Processing envelope: {image_path.name}")
        
        # Run OCR
        print("  🔍 Running OCR...")
        ocr_text = self.run_ocr_on_image(image_path)
        
        if not ocr_text or len(ocr_text.strip()) < 10:
            print("  ⚠️ No text extracted from image")
            return {
                'error': 'No OCR text extracted',
                'image_path': str(image_path)
            }
        
        print(f"  ✓ Extracted {len(ocr_text)} characters")
        
        # Extract metadata
        print("  🧠 Analyzing with LLM...")
        metadata = self.extract_metadata(ocr_text, image_path.stem)
        metadata['image_path'] = str(image_path)
        metadata['ocr_text'] = ocr_text
        
        print(f"  ✓ Sender: {metadata.get('sender', 'Unknown')}")
        print(f"  ✓ Receiver: {metadata.get('receiver', 'Unknown')}")
        print(f"  ✓ Date: {metadata.get('date', 'Unknown')}")
        print(f"  ✓ Confidence: {metadata.get('confidence', 0)}%")
        
        return metadata
    
    def process_pdf_envelopes(self, pdf_path: Path, work_dir: Path) -> List[Dict]:
        """
        Process envelope images associated with a PDF document.
        
        Typically looks for page_001.png (often the envelope) for each PDF.
        
        Args:
            pdf_path: Path to the PDF file
            work_dir: Directory containing extracted PNG images
            
        Returns:
            List of metadata dicts (one per envelope image found)
        """
        pdf_stem = pdf_path.stem
        
        # Look for associated PNG files
        envelope_images = list(work_dir.glob(f"*{pdf_stem}*page_001.png"))
        
        if not envelope_images:
            # Try looking for the PDF stem directly in work folder
            envelope_images = [p for p in work_dir.glob("*.png") 
                             if pdf_stem.lower() in p.stem.lower() and "page_001" in p.stem]
        
        if not envelope_images:
            print(f"  ⚠️ No envelope images found for {pdf_path.name}")
            return []
        
        results = []
        for image_path in envelope_images:
            metadata = self.process_envelope(image_path)
            results.append(metadata)
        
        return results


def main():
    """Command-line interface for envelope extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract metadata from envelope images')
    parser.add_argument('--image', type=str, help='Single envelope image to process')
    parser.add_argument('--pdf', type=str, help='PDF file to find and process envelope for')
    parser.add_argument('--work-dir', type=str, default='letters/work', 
                       help='Directory containing extracted page images')
    parser.add_argument('--output', type=str, help='Output JSON file for results')
    
    args = parser.parse_args()
    
    extractor = EnvelopeExtractor()
    
    if args.image:
        # Process single image
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: Image not found: {image_path}")
            return
        
        metadata = extractor.process_envelope(image_path)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(metadata, indent=2))
            print(f"\n💾 Saved to: {output_path}")
        else:
            print(f"\n{json.dumps(metadata, indent=2)}")
    
    elif args.pdf:
        # Process envelope for a PDF
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: PDF not found: {pdf_path}")
            return
        
        work_dir = Path(args.work_dir)
        results = extractor.process_pdf_envelopes(pdf_path, work_dir)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(results, indent=2))
            print(f"\n💾 Saved to: {output_path}")
        else:
            for result in results:
                print(f"\n{json.dumps(result, indent=2)}")
    
    else:
        print("Error: Must specify --image or --pdf")
        parser.print_help()


if __name__ == '__main__':
    main()
