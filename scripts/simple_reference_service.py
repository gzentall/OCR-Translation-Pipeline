#!/usr/bin/env python3

"""
Simple Reference Service for Flask app (without Prisma dependency)
Provides basic reference operations using direct database queries
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

class SimpleReferenceService:
    def __init__(self):
        # Get database URL from environment
        self.database_url = os.getenv('DATABASE_URL')
        print(f"DATABASE_URL from env: {self.database_url}")
        
        if not self.database_url:
            # Try to construct from individual components
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', '')
            database = os.getenv('DB_NAME', 'ocr_project')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            print(f"Constructed database URL: {self.database_url[:50]}...")
        else:
            print(f"Using database URL: {self.database_url[:50]}...")
    
    async def get_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.database_url)
    
    async def search_references(self, query: str = None, ref_type: str = None) -> List[Dict]:
        """Search references with optional filtering"""
        conn = await self.get_connection()
        try:
            where_conditions = []
            params = []
            param_count = 0
            
            if query:
                param_count += 1
                where_conditions.append(f"""
                    (r."canonicalName" ILIKE ${param_count} OR 
                     EXISTS (SELECT 1 FROM "ReferenceVariant" rv WHERE rv."parentId" = r.id AND rv.label ILIKE ${param_count}))
                """)
                params.append(f'%{query}%')
            
            if ref_type:
                param_count += 1
                where_conditions.append(f'r.type = ${param_count}')
                params.append(ref_type)
            
            where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
            
            sql = f"""
                SELECT 
                    r.id,
                    r."canonicalName",
                    r.type,
                    r.notes,
                    r."createdBy",
                    r."createdAt",
                    r."updatedAt",
                    COUNT(DISTINCT rv.id) as children_count,
                    COUNT(DISTINCT dr.id) as linked_docs_count
                FROM "Reference" r
                LEFT JOIN "ReferenceVariant" rv ON rv."parentId" = r.id
                LEFT JOIN "DocumentReference" dr ON dr."referenceId" = r.id
                WHERE {where_clause}
                GROUP BY r.id, r."canonicalName", r.type, r.notes, r."createdBy", r."createdAt", r."updatedAt"
                ORDER BY r."canonicalName"
            """
            
            rows = await conn.fetch(sql, *params)
            
            references = []
            for row in rows:
                # Get variants for this reference
                variants_sql = 'SELECT id, label, "createdBy", "createdAt" FROM "ReferenceVariant" WHERE "parentId" = $1 ORDER BY label'
                variant_rows = await conn.fetch(variants_sql, row['id'])
                
                references.append({
                    'id': row['id'],
                    'canonicalName': row['canonicalName'],
                    'type': row['type'],
                    'notes': row['notes'],
                    'createdBy': row['createdBy'],
                    'createdAt': row['createdAt'].isoformat(),
                    'updatedAt': row['updatedAt'].isoformat(),
                    'childrenCount': row['children_count'],
                    'linkedDocsCount': row['linked_docs_count'],
                    'variants': [
                        {
                            'id': v['id'],
                            'label': v['label'],
                            'createdBy': v['createdBy'],
                            'createdAt': v['createdAt'].isoformat()
                        }
                        for v in variant_rows
                    ]
                })
            
            return references
        finally:
            await conn.close()
    
    async def get_reference_by_id(self, ref_id: str) -> Optional[Dict]:
        """Get a reference by ID with full details"""
        conn = await self.get_connection()
        try:
            # Get reference
            ref_sql = 'SELECT * FROM "Reference" WHERE id = $1'
            ref_row = await conn.fetchrow(ref_sql, ref_id)
            
            if not ref_row:
                return None
            
            # Get variants
            variants_sql = 'SELECT * FROM "ReferenceVariant" WHERE "parentId" = $1 ORDER BY label'
            variant_rows = await conn.fetch(variants_sql, ref_id)
            
            # Get document references
            doc_refs_sql = '''
                SELECT dr.*, d.title as document_title
                FROM "DocumentReference" dr
                JOIN "Document" d ON d.id = dr."documentId"
                WHERE dr."referenceId" = $1
                ORDER BY dr."createdAt"
            '''
            doc_ref_rows = await conn.fetch(doc_refs_sql, ref_id)
            
            return {
                'id': ref_row['id'],
                'canonicalName': ref_row['canonicalName'],
                'type': ref_row['type'],
                'notes': ref_row['notes'],
                'createdBy': ref_row['createdBy'],
                'createdAt': ref_row['createdAt'].isoformat(),
                'updatedAt': ref_row['updatedAt'].isoformat(),
                'childrenCount': len(variant_rows),
                'linkedDocsCount': len(doc_ref_rows),
                'variants': [
                    {
                        'id': variant['id'],
                        'label': variant['label'],
                        'createdBy': variant['createdBy'],
                        'createdAt': variant['createdAt'].isoformat()
                    }
                    for variant in variant_rows
                ],
                'linkedDocuments': [
                    {
                        'id': doc_ref['documentId'],
                        'title': doc_ref['document_title'],
                        'confidence': doc_ref['confidence'],
                        'matchText': doc_ref['matchText'],
                        'role': doc_ref['role'],
                        'createdAt': doc_ref['createdAt'].isoformat()
                    }
                    for doc_ref in doc_ref_rows
                ]
            }
        finally:
            await conn.close()
    
    async def create_reference(self, canonical_name: str, ref_type: str, notes: str = None, 
                             initial_variants: List[str] = None) -> Dict:
        """Create a new reference"""
        if initial_variants is None:
            initial_variants = []
        
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                # Generate CUID-like ID
                ref_id = f"cm{str(uuid.uuid4()).replace('-', '')[:20]}"
                
                # Create reference with explicit updatedAt
                now = datetime.now()
                print(f"Creating reference with ID: {ref_id}")
                print(f"Type: {ref_type}, Name: {canonical_name}, Notes: {notes}")
                print(f"CreatedAt: {now}, UpdatedAt: {now}")
                
                # Try a simpler approach - let the database handle the timestamps
                ref_sql = '''
                    INSERT INTO "Reference" (id, type, "canonicalName", notes, "createdBy")
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                '''
                ref_row = await conn.fetchrow(ref_sql, ref_id, ref_type, canonical_name, notes, 'HUMAN')
                
                # Create only the provided variants (don't auto-add canonical name)
                variant_sql = '''
                    INSERT INTO "ReferenceVariant" (id, "parentId", label, "createdBy", "createdAt")
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                '''
                for variant in initial_variants:
                    if variant:  # Only add non-empty variants
                        variant_id = f"cm{str(uuid.uuid4()).replace('-', '')[:20]}"
                        await conn.fetchrow(variant_sql, variant_id, ref_row['id'], variant, 'HUMAN', now)
                
                return {
                    'id': ref_row['id'],
                    'canonicalName': ref_row['canonicalName'],
                    'type': ref_row['type'],
                    'notes': ref_row['notes'],
                    'createdBy': ref_row['createdBy'],
                    'createdAt': ref_row['createdAt'].isoformat(),
                    'updatedAt': ref_row['updatedAt'].isoformat(),
                    'childrenCount': len(initial_variants),
                    'linkedDocsCount': 0
                }
        finally:
            await conn.close()
    
    async def update_reference(self, ref_id: str, updates: Dict) -> Optional[Dict]:
        """Update a reference"""
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                # Build update SQL
                set_clauses = []
                params = []
                param_count = 0
                
                if 'canonicalName' in updates:
                    param_count += 1
                    set_clauses.append(f'"canonicalName" = ${param_count}')
                    params.append(updates['canonicalName'])
                
                if 'type' in updates:
                    param_count += 1
                    set_clauses.append(f'type = ${param_count}')
                    params.append(updates['type'])
                
                if 'notes' in updates:
                    param_count += 1
                    set_clauses.append(f'notes = ${param_count}')
                    params.append(updates['notes'])
                
                # Always update updatedAt
                param_count += 1
                set_clauses.append(f'"updatedAt" = ${param_count}')
                params.append(datetime.now())
                
                if set_clauses:
                    param_count += 1
                    sql = f'''
                        UPDATE "Reference"
                        SET {", ".join(set_clauses)}
                        WHERE id = ${param_count}
                        RETURNING *
                    '''
                    params.append(ref_id)
                    
                    ref_row = await conn.fetchrow(sql, *params)
                    
                    if not ref_row:
                        return None
                
                # Handle variants if provided
                if 'initialVariants' in updates:
                    # Get existing variants
                    existing_variants = await conn.fetch(
                        'SELECT id, label FROM "ReferenceVariant" WHERE "parentId" = $1',
                        ref_id
                    )
                    existing_labels = {v['label'] for v in existing_variants}
                    new_labels = set(updates['initialVariants'])
                    
                    # Delete variants that are no longer in the list
                    for variant in existing_variants:
                        if variant['label'] not in new_labels:
                            await conn.execute(
                                'DELETE FROM "ReferenceVariant" WHERE id = $1',
                                variant['id']
                            )
                    
                    # Add new variants
                    for label in new_labels:
                        if label and label not in existing_labels:
                            variant_id = f"cm{str(uuid.uuid4()).replace('-', '')[:20]}"
                            await conn.execute('''
                                INSERT INTO "ReferenceVariant" (id, "parentId", label, "createdBy", "createdAt")
                                VALUES ($1, $2, $3, $4, $5)
                            ''', variant_id, ref_id, label, 'HUMAN', datetime.now())
                
                return await self.get_reference_by_id(ref_id)
        finally:
            await conn.close()
    
    async def delete_reference(self, ref_id: str) -> bool:
        """Delete a reference"""
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                # Check for linked documents
                doc_count = await conn.fetchval(
                    'SELECT COUNT(*) FROM "DocumentReference" WHERE "referenceId" = $1',
                    ref_id
                )
                
                if doc_count > 0:
                    raise ValueError(f'Cannot delete reference with {doc_count} linked documents')
                
                # Delete variants first
                await conn.execute('DELETE FROM "ReferenceVariant" WHERE "parentId" = $1', ref_id)
                
                # Delete reference
                result = await conn.execute('DELETE FROM "Reference" WHERE id = $1', ref_id)
                
                return result == 'DELETE 1'
        finally:
            await conn.close()
    
    async def merge_references(self, source_id: str, target_id: str) -> bool:
        """Merge source reference into target reference"""
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                # Move variants from source to target (skip duplicates)
                await conn.execute('''
                    INSERT INTO "ReferenceVariant" (id, "parentId", label, "createdBy", "createdAt")
                    SELECT 
                        'cm' || substring(md5(random()::text) from 1 for 20),
                        $1,
                        rv.label,
                        rv."createdBy",
                        rv."createdAt"
                    FROM "ReferenceVariant" rv
                    WHERE rv."parentId" = $2
                    AND NOT EXISTS (
                        SELECT 1 FROM "ReferenceVariant" rv2 
                        WHERE rv2."parentId" = $1 AND rv2.label = rv.label
                    )
                ''', target_id, source_id)
                
                # Delete source variants
                await conn.execute('DELETE FROM "ReferenceVariant" WHERE "parentId" = $1', source_id)
                
                # Move document references from source to target (handle duplicates)
                await conn.execute('''
                    UPDATE "DocumentReference"
                    SET "referenceId" = $1
                    WHERE "referenceId" = $2
                    AND NOT EXISTS (
                        SELECT 1 FROM "DocumentReference" dr2
                        WHERE dr2."documentId" = "DocumentReference"."documentId"
                        AND dr2."referenceId" = $1
                    )
                ''', target_id, source_id)
                
                # Delete remaining source document references (duplicates)
                await conn.execute('DELETE FROM "DocumentReference" WHERE "referenceId" = $1', source_id)
                
                # Delete source reference
                result = await conn.execute('DELETE FROM "Reference" WHERE id = $1', source_id)
                
                return result == 'DELETE 1'
        finally:
            await conn.close()
    
    async def get_metrics(self) -> Dict:
        """Get reference system metrics"""
        conn = await self.get_connection()
        try:
            # Get basic counts
            total_refs = await conn.fetchval('SELECT COUNT(*) FROM "Reference"')
            total_variants = await conn.fetchval('SELECT COUNT(*) FROM "ReferenceVariant"')
            total_doc_refs = await conn.fetchval('SELECT COUNT(*) FROM "DocumentReference"')
            
            # Get confidence stats
            low_confidence = await conn.fetchval('SELECT COUNT(*) FROM "DocumentReference" WHERE confidence < 50')
            high_confidence = await conn.fetchval('SELECT COUNT(*) FROM "DocumentReference" WHERE confidence >= 80')
            
            # Get document stats
            docs_with_refs = await conn.fetchval('SELECT COUNT(DISTINCT "documentId") FROM "DocumentReference"')
            total_docs = await conn.fetchval('SELECT COUNT(*) FROM "Document"')
            
            return {
                'totalReferences': total_refs,
                'totalVariants': total_variants,
                'totalDocumentRefs': total_doc_refs,
                'lowConfidenceCount': low_confidence,
                'highConfidenceCount': high_confidence,
                'documentsWithRefs': docs_with_refs,
                'totalDocuments': total_docs,
                'hitRate': (docs_with_refs / total_docs * 100) if total_docs > 0 else 0,
                'lowConfidenceRate': (low_confidence / total_doc_refs * 100) if total_doc_refs > 0 else 0
            }
        finally:
            await conn.close()

# Global instance
simple_reference_service = SimpleReferenceService()
