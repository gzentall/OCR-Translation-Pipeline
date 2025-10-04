#!/usr/bin/env python3

"""
Auto-tagger service for Flask app
Provides automatic reference extraction and tagging functionality
"""

import re
import asyncio
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add the ocr-auth directory to the path to import Prisma client
ocr_auth_path = Path(__file__).parent.parent / 'ocr-auth'
sys.path.insert(0, str(ocr_auth_path))

try:
    from prisma import PrismaClient
except ImportError:
    print("Prisma client not found. Please run 'npx prisma generate' in the ocr-auth directory.")
    print(f"Looking in: {ocr_auth_path}")
    sys.exit(1)

class AutoTagger:
    def __init__(self):
        self.prisma = PrismaClient()
        self.nickname_map = {
            "Robert": ["Rob", "Bobby", "Bob", "Robt"],
            "Elizabeth": ["Liz", "Liza", "Beth", "Betsy"],
            "William": ["Bill", "Will", "Billy"],
            "Richard": ["Rick", "Rich", "Dick"],
            "Michael": ["Mike", "Mick", "Mickey"],
            "Christopher": ["Chris", "Kit"],
            "Daniel": ["Dan", "Danny"],
            "Matthew": ["Matt", "Matty"],
            "Anthony": ["Tony", "Ant"],
            "David": ["Dave", "Davey"]
        }
    
    def clean_text(self, text: str) -> str:
        """Clean text for processing"""
        # Fix line-end hyphenations: grand- mother → grandmother
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        
        # Collapse weird whitespace but preserve diacritics
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_names(self, text: str) -> List[Dict]:
        """Extract potential names from text"""
        names = []
        
        # Rule 1: Capitalized two-word patterns (likely names)
        name_pattern = re.compile(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b')
        
        for match in name_pattern.finditer(text):
            full_name = match.group(0)
            first_name = match.group(1)
            last_name = match.group(2)
            
            # Skip common non-name words
            skip_words = ['The', 'This', 'That', 'There', 'Here', 'Where', 'When', 'How', 'What', 'Why']
            if first_name in skip_words:
                continue
            
            # Check for nickname matches
            confidence = 15  # Base confidence for capitalized two-token name
            context = 'Capitalized name pattern'
            
            # Check if this matches a known nickname
            for canonical, nicknames in self.nickname_map.items():
                if first_name in nicknames:
                    confidence += 10
                    context = f'Nickname match: {first_name} → {canonical}'
                    break
            
            # Check frequency (appears multiple times)
            frequency = len(re.findall(re.escape(full_name), text, re.IGNORECASE))
            if frequency >= 2:
                confidence += 10
                context += f' (appears {frequency} times)'
            
            names.append({
                'name': full_name,
                'confidence': min(confidence, 100),
                'context': context,
                'type': 'PERSON'
            })
        
        # Rule 2: Single capitalized words that might be names
        single_name_pattern = re.compile(r'\b([A-Z][a-z]{2,})\b')
        
        for match in single_name_pattern.finditer(text):
            name = match.group(0)
            
            # Skip common words
            skip_words = ['The', 'This', 'That', 'There', 'Here', 'Where', 'When', 'How', 'What', 'Why', 
                         'Dear', 'Love', 'Sincerely', 'Yours']
            if name in skip_words:
                continue
            
            # Check for nickname matches
            confidence = 5  # Lower base confidence for single names
            context = 'Single capitalized word'
            
            for canonical, nicknames in self.nickname_map.items():
                if name in nicknames:
                    confidence += 15
                    context = f'Nickname match: {name} → {canonical}'
                    break
            
            # Check frequency
            frequency = len(re.findall(re.escape(name), text, re.IGNORECASE))
            if frequency >= 2:
                confidence += 5
                context += f' (appears {frequency} times)'
            
            if confidence >= 20:  # Only include if confidence is reasonable
                names.append({
                    'name': name,
                    'confidence': min(confidence, 100),
                    'context': context,
                    'type': 'PERSON'
                })
        
        return names
    
    def extract_places(self, text: str) -> List[Dict]:
        """Extract potential places from text"""
        places = []
        
        # Common place indicators
        place_indicators = ['in', 'at', 'from', 'to', 'near', 'around', 'outside', 'inside']
        
        # Known place names and patterns
        known_places = [
            'Vienna', 'Wien', 'Paris', 'London', 'Berlin', 'Munich', 'Hamburg',
            'New York', 'Los Angeles', 'Chicago', 'Boston', 'Philadelphia',
            'Germany', 'France', 'England', 'Austria', 'Switzerland'
        ]
        
        # Look for place indicators followed by capitalized words
        place_pattern = re.compile(
            rf'\b({"|".join(place_indicators)})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            re.IGNORECASE
        )
        
        for match in place_pattern.finditer(text):
            place = match.group(2)
            confidence = 10
            context = f'Place indicator: {match.group(1)}'
            
            # Check if it's a known place
            if any(known_place.lower() in place.lower() or place.lower() in known_place.lower() 
                   for known_place in known_places):
                confidence += 20
                context += ' (known place)'
            
            places.append({
                'name': place,
                'confidence': min(confidence, 100),
                'context': context,
                'type': 'PLACE'
            })
        
        # Look for known places directly
        for place in known_places:
            if re.search(rf'\b{re.escape(place)}\b', text, re.IGNORECASE):
                places.append({
                    'name': place,
                    'confidence': 30,
                    'context': 'Known place name',
                    'type': 'PLACE'
                })
        
        return places
    
    async def find_or_create_reference(self, name: str, ref_type: str, created_by: str = 'AUTO'):
        """Find existing reference or create new one"""
        # First, try to find existing reference by canonical name
        reference = await self.prisma.reference.find_first(
            where={
                'canonicalName': {
                    'equals': name,
                    'mode': 'insensitive'
                }
            },
            include={'variants': True}
        )
        
        if reference:
            return reference
        
        # Try to find by variant labels
        variant = await self.prisma.referencevariant.find_first(
            where={
                'label': {
                    'equals': name,
                    'mode': 'insensitive'
                }
            },
            include={
                'parent': {
                    'include': {'variants': True}
                }
            }
        )
        
        if variant:
            return variant.parent
        
        # Create new reference
        reference = await self.prisma.reference.create(
            data={
                'type': ref_type,
                'canonicalName': name,
                'createdBy': created_by,
                'variants': {
                    'create': {
                        'label': name,
                        'createdBy': created_by
                    }
                }
            },
            include={'variants': True}
        )
        
        return reference
    
    async def add_variant_if_new(self, reference_id: str, label: str):
        """Add variant if it doesn't already exist"""
        existing = await self.prisma.referencevariant.find_first(
            where={
                'parentId': reference_id,
                'label': {
                    'equals': label,
                    'mode': 'insensitive'
                }
            }
        )
        
        if not existing:
            await self.prisma.referencevariant.create(
                data={
                    'parentId': reference_id,
                    'label': label,
                    'createdBy': 'AUTO'
                }
            )
    
    async def run_for_document(self, document_id: str) -> Dict:
        """Run auto-tagging for a specific document"""
        document = await self.prisma.document.find_unique(
            where={'id': document_id},
            include={'references': True}
        )
        
        if not document or not document.translatedText:
            raise ValueError('Document not found or no translated text available')
        
        cleaned_text = self.clean_text(document.translatedText)
        result = {
            'linked': 0,
            'newParents': 0,
            'newChildren': 0,
            'lowConfidence': 0
        }
        
        # Extract names and places
        names = self.extract_names(cleaned_text)
        places = self.extract_places(cleaned_text)
        
        all_extractions = names + places
        
        # Process each extraction
        for extraction in all_extractions:
            try:
                # Find or create reference
                reference = await self.find_or_create_reference(
                    extraction['name'],
                    extraction['type'],
                    'AUTO'
                )
                
                # Check if this is a new parent
                if (reference.createdBy == 'AUTO' and 
                    reference.createdAt > datetime.now().replace(microsecond=0)):
                    result['newParents'] += 1
                
                # Add variant if it's different from canonical name
                if extraction['name'].lower() != reference.canonicalName.lower():
                    await self.add_variant_if_new(reference.id, extraction['name'])
                    result['newChildren'] += 1
                
                # Create or update document reference
                existing_doc_ref = await self.prisma.documentreference.find_first(
                    where={
                        'documentId': document_id,
                        'referenceId': reference.id,
                        'matchText': extraction['name']
                    }
                )
                
                if not existing_doc_ref:
                    await self.prisma.documentreference.create(
                        data={
                            'documentId': document_id,
                            'referenceId': reference.id,
                            'matchText': extraction['name'],
                            'confidence': extraction['confidence'],
                            'role': 'mentioned'
                        }
                    )
                    result['linked'] += 1
                    
                    if extraction['confidence'] < 50:
                        result['lowConfidence'] += 1
                
            except Exception as e:
                print(f"Error processing extraction '{extraction['name']}': {e}")
        
        return result
    
    async def run_batch(self, rebuild: bool = False) -> Dict:
        """Run auto-tagging for all documents"""
        result = {
            'linked': 0,
            'newParents': 0,
            'newChildren': 0,
            'lowConfidence': 0
        }
        
        # Get documents to process
        where_clause = {}
        if not rebuild:
            where_clause = {
                'references': {
                    'none': {}
                }
            }
        
        documents = await self.prisma.document.find_many(
            where=where_clause,
            include={'references': True}
        )
        
        print(f"Processing {len(documents)} documents...")
        
        for document in documents:
            try:
                doc_result = await self.run_for_document(document.id)
                
                result['linked'] += doc_result['linked']
                result['newParents'] += doc_result['newParents']
                result['newChildren'] += doc_result['newChildren']
                result['lowConfidence'] += doc_result['lowConfidence']
                
                print(f"Document {document.id}: {doc_result['linked']} linked, "
                      f"{doc_result['newParents']} new parents, {doc_result['newChildren']} new children")
                
            except Exception as e:
                print(f"Error processing document {document.id}: {e}")
        
        return result
    
    async def close(self):
        """Close the Prisma client"""
        await self.prisma.disconnect()

# Global instance
auto_tagger = AutoTagger()
