#!/usr/bin/env python3

"""
Reference Service for Flask app
Provides database operations for the Reference system using PostgreSQL
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Add the ocr-auth directory to the path to import Prisma client
ocr_auth_path = Path(__file__).parent.parent / 'ocr-auth'
sys.path.insert(0, str(ocr_auth_path))

try:
    from prisma import PrismaClient
except ImportError:
    print("Prisma client not found. Please run 'npx prisma generate' in the ocr-auth directory.")
    print(f"Looking in: {ocr_auth_path}")
    sys.exit(1)

class ReferenceService:
    def __init__(self):
        self.prisma = PrismaClient()
    
    async def search_references(self, query: str = None, ref_type: str = None) -> List[Dict]:
        """Search references with optional filtering"""
        where_clause = {}
        
        if query:
            where_clause['OR'] = [
                {
                    'canonicalName': {
                        'contains': query,
                        'mode': 'insensitive'
                    }
                },
                {
                    'variants': {
                        'some': {
                            'label': {
                                'contains': query,
                                'mode': 'insensitive'
                            }
                        }
                    }
                }
            ]
        
        if ref_type:
            where_clause['type'] = ref_type
        
        references = await self.prisma.reference.find_many(
            where=where_clause,
            include={
                'variants': True,
                'documentRefs': {
                    'include': {
                        'document': {
                            'select': {
                                'id': True,
                                'title': True
                            }
                        }
                    }
                }
            },
            order_by={'canonicalName': 'asc'}
        )
        
        return [
            {
                'id': ref.id,
                'canonicalName': ref.canonicalName,
                'type': ref.type,
                'notes': ref.notes,
                'createdBy': ref.createdBy,
                'createdAt': ref.createdAt.isoformat(),
                'updatedAt': ref.updatedAt.isoformat(),
                'childrenCount': len(ref.variants),
                'linkedDocsCount': len(ref.documentRefs),
                'variants': [
                    {
                        'id': variant.id,
                        'label': variant.label,
                        'createdBy': variant.createdBy,
                        'createdAt': variant.createdAt.isoformat()
                    }
                    for variant in ref.variants
                ],
                'linkedDocuments': [
                    {
                        'id': doc_ref.document.id,
                        'title': doc_ref.document.title,
                        'confidence': doc_ref.confidence,
                        'matchText': doc_ref.matchText,
                        'role': doc_ref.role,
                        'createdAt': doc_ref.createdAt.isoformat()
                    }
                    for doc_ref in ref.documentRefs
                ]
            }
            for ref in references
        ]
    
    async def get_reference_by_id(self, ref_id: str) -> Optional[Dict]:
        """Get a reference by ID with full details"""
        reference = await self.prisma.reference.find_unique(
            where={'id': ref_id},
            include={
                'variants': True,
                'documentRefs': {
                    'include': {
                        'document': {
                            'select': {
                                'id': True,
                                'title': True
                            }
                        }
                    }
                }
            }
        )
        
        if not reference:
            return None
        
        return {
            'id': reference.id,
            'canonicalName': reference.canonicalName,
            'type': reference.type,
            'notes': reference.notes,
            'createdBy': reference.createdBy,
            'createdAt': reference.createdAt.isoformat(),
            'updatedAt': reference.updatedAt.isoformat(),
            'childrenCount': len(reference.variants),
            'linkedDocsCount': len(reference.documentRefs),
            'variants': [
                {
                    'id': variant.id,
                    'label': variant.label,
                    'createdBy': variant.createdBy,
                    'createdAt': variant.createdAt.isoformat()
                }
                for variant in reference.variants
            ],
            'linkedDocuments': [
                {
                    'id': doc_ref.document.id,
                    'title': doc_ref.document.title,
                    'confidence': doc_ref.confidence,
                    'matchText': doc_ref.matchText,
                    'role': doc_ref.role,
                    'createdAt': doc_ref.createdAt.isoformat()
                }
                for doc_ref in reference.documentRefs
            ]
        }
    
    async def create_reference(self, canonical_name: str, ref_type: str, notes: str = None, 
                             initial_variants: List[str] = None) -> Dict:
        """Create a new reference"""
        if initial_variants is None:
            initial_variants = []
        
        # Create the reference with variants
        reference = await self.prisma.reference.create(
            data={
                'type': ref_type,
                'canonicalName': canonical_name,
                'notes': notes,
                'createdBy': 'HUMAN',
                'variants': {
                    'create': [
                        {
                            'label': canonical_name,
                            'createdBy': 'HUMAN'
                        }
                    ] + [
                        {
                            'label': variant,
                            'createdBy': 'HUMAN'
                        }
                        for variant in initial_variants
                    ]
                }
            },
            include={
                'variants': True,
                'documentRefs': True
            }
        )
        
        return {
            'id': reference.id,
            'canonicalName': reference.canonicalName,
            'type': reference.type,
            'notes': reference.notes,
            'createdBy': reference.createdBy,
            'createdAt': reference.createdAt.isoformat(),
            'updatedAt': reference.updatedAt.isoformat(),
            'childrenCount': len(reference.variants),
            'linkedDocsCount': len(reference.documentRefs),
            'variants': [
                {
                    'id': variant.id,
                    'label': variant.label,
                    'createdBy': variant.createdBy,
                    'createdAt': variant.createdAt.isoformat()
                }
                for variant in reference.variants
            ],
            'linkedDocuments': []
        }
    
    async def update_reference(self, ref_id: str, updates: Dict) -> Optional[Dict]:
        """Update a reference"""
        reference = await self.prisma.reference.update(
            where={'id': ref_id},
            data={
                **updates,
                'updatedAt': datetime.now()
            },
            include={
                'variants': True,
                'documentRefs': {
                    'include': {
                        'document': {
                            'select': {
                                'id': True,
                                'title': True
                            }
                        }
                    }
                }
            }
        )
        
        return {
            'id': reference.id,
            'canonicalName': reference.canonicalName,
            'type': reference.type,
            'notes': reference.notes,
            'createdBy': reference.createdBy,
            'createdAt': reference.createdAt.isoformat(),
            'updatedAt': reference.updatedAt.isoformat(),
            'childrenCount': len(reference.variants),
            'linkedDocsCount': len(reference.documentRefs),
            'variants': [
                {
                    'id': variant.id,
                    'label': variant.label,
                    'createdBy': variant.createdBy,
                    'createdAt': variant.createdAt.isoformat()
                }
                for variant in reference.variants
            ],
            'linkedDocuments': [
                {
                    'id': doc_ref.document.id,
                    'title': doc_ref.document.title,
                    'confidence': doc_ref.confidence,
                    'matchText': doc_ref.matchText,
                    'role': doc_ref.role,
                    'createdAt': doc_ref.createdAt.isoformat()
                }
                for doc_ref in reference.documentRefs
            ]
        }
    
    async def delete_reference(self, ref_id: str) -> bool:
        """Delete a reference (only if no document links)"""
        try:
            # Check if reference has any document links
            doc_refs = await self.prisma.documentreference.find_many(
                where={'referenceId': ref_id}
            )
            
            if doc_refs:
                return False  # Cannot delete reference with linked documents
            
            await self.prisma.reference.delete(where={'id': ref_id})
            return True
        except Exception as e:
            print(f"Error deleting reference: {e}")
            return False
    
    async def merge_references(self, source_id: str, target_id: str) -> bool:
        """Merge source reference into target reference"""
        try:
            # Get source reference with all its data
            source_ref = await self.prisma.reference.find_unique(
                where={'id': source_id},
                include={
                    'variants': True,
                    'documentRefs': True
                }
            )
            
            if not source_ref:
                return False
            
            # Move all variants from source to target
            for variant in source_ref.variants:
                await self.prisma.referencevariant.update(
                    where={'id': variant.id},
                    data={'parentId': target_id}
                )
            
            # Move all document references from source to target
            for doc_ref in source_ref.documentRefs:
                await self.prisma.documentreference.update(
                    where={'id': doc_ref.id},
                    data={'referenceId': target_id}
                )
            
            # Delete the source reference
            await self.prisma.reference.delete(where={'id': source_id})
            return True
        except Exception as e:
            print(f"Error merging references: {e}")
            return False
    
    async def add_variant(self, ref_id: str, label: str) -> bool:
        """Add a variant to a reference"""
        try:
            await self.prisma.referencevariant.create(
                data={
                    'parentId': ref_id,
                    'label': label,
                    'createdBy': 'HUMAN'
                }
            )
            return True
        except Exception as e:
            print(f"Error adding variant: {e}")
            return False
    
    async def remove_variant(self, variant_id: str) -> bool:
        """Remove a variant from a reference"""
        try:
            await self.prisma.referencevariant.delete(where={'id': variant_id})
            return True
        except Exception as e:
            print(f"Error removing variant: {e}")
            return False
    
    async def get_metrics(self) -> Dict:
        """Get reference system metrics"""
        total_references = await self.prisma.reference.count()
        total_variants = await self.prisma.referencevariant.count()
        total_document_refs = await self.prisma.documentreference.count()
        
        low_confidence_count = await self.prisma.documentreference.count(
            where={'confidence': {'lt': 50}}
        )
        
        high_confidence_count = await self.prisma.documentreference.count(
            where={'confidence': {'gte': 80}}
        )
        
        documents_with_refs = await self.prisma.document.count(
            where={'references': {'some': {}}}
        )
        
        total_documents = await self.prisma.document.count()
        
        return {
            'totalReferences': total_references,
            'totalVariants': total_variants,
            'totalDocumentRefs': total_document_refs,
            'lowConfidenceCount': low_confidence_count,
            'highConfidenceCount': high_confidence_count,
            'documentsWithRefs': documents_with_refs,
            'totalDocuments': total_documents,
            'hitRate': (documents_with_refs / total_documents * 100) if total_documents > 0 else 0,
            'lowConfidenceRate': (low_confidence_count / total_document_refs * 100) if total_document_refs > 0 else 0
        }
    
    async def close(self):
        """Close the Prisma client"""
        await self.prisma.disconnect()

# Global instance
reference_service = ReferenceService()
