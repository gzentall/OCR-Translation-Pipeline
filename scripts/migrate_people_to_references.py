#!/usr/bin/env python3

"""
Migrate people from local storage to PostgreSQL Reference system
"""

import os
import sys
import asyncio
import asyncpg
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.local_storage import LocalOCRStorage

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / 'ocr-auth' / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

async def get_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

async def migrate_people_to_references():
    """Migrate people from local storage to Reference system"""
    
    # Initialize local storage
    storage = LocalOCRStorage()
    
    # Get all people
    people = storage.get_people_with_documents()
    
    print(f"Found {len(people)} people to migrate")
    
    conn = await get_connection()
    
    try:
        async with conn.transaction():
            # Track created references
            reference_map = {}  # person_name -> reference_id
            
            # Create references for each person
            for person in people:
                person_name = person['name']
                aliases = person.get('aliases', [])
                
                # Generate CUID-like ID
                ref_id = f"cm{str(uuid.uuid4()).replace('-', '')[:20]}"
                
                # Create Reference
                await conn.execute('''
                    INSERT INTO "Reference" (id, type, "canonicalName", notes, "createdBy")
                    VALUES ($1, $2, $3, $4, $5)
                ''', ref_id, 'PERSON', person_name, f"Migrated from local storage. First mentioned: {person.get('first_mentioned', 'unknown')}", 'AUTO')
                
                reference_map[person_name] = ref_id
                
                # Create variants for aliases
                for alias in aliases:
                    if alias and alias != person_name:  # Don't duplicate canonical name
                        variant_id = f"cm{str(uuid.uuid4()).replace('-', '')[:20]}"
                        try:
                            await conn.execute('''
                                INSERT INTO "ReferenceVariant" (id, "parentId", label, "createdBy", "createdAt")
                                VALUES ($1, $2, $3, $4, $5)
                            ''', variant_id, ref_id, alias, 'AUTO', datetime.now())
                        except Exception as e:
                            print(f"Error creating variant '{alias}' for '{person_name}': {e}")
                
                print(f"Created reference for '{person_name}' with {len(aliases)} variants")
            
            # Now link documents to references
            documents = storage.list_documents()
            linked_count = 0
            
            for doc_id, doc_metadata in documents:
                
                # Get PostgreSQL document ID (it might be different)
                pg_doc = await conn.fetchrow('SELECT id FROM "Document" WHERE id = $1', doc_id)
                
                if not pg_doc:
                    print(f"Warning: Document {doc_id} not found in PostgreSQL")
                    continue
                
                # Get full document data to access people field
                doc_data = storage.get_document(doc_id)
                if not doc_data:
                    continue
                
                people_in_doc = doc_data.get('people', [])
                doc_references = set()  # Track to avoid duplicates
                
                for person_entry in people_in_doc:
                    # Handle both string and dict formats
                    if isinstance(person_entry, dict):
                        person_name = person_entry.get('normalized_name', '')
                        original_name = person_entry.get('original_name', '')
                    else:
                        person_name = storage.normalize_name(person_entry)
                        original_name = person_entry
                    
                    if person_name in reference_map:
                        ref_id = reference_map[person_name]
                        
                        # Avoid duplicate links
                        link_key = (doc_id, ref_id, original_name)
                        if link_key in doc_references:
                            continue
                        doc_references.add(link_key)
                        
                        # Create DocumentReference
                        try:
                            await conn.execute('''
                                INSERT INTO "DocumentReference" ("documentId", "referenceId", "matchText", confidence, role, "createdAt")
                                VALUES ($1, $2, $3, $4, $5, $6)
                                ON CONFLICT ("documentId", "referenceId", "matchText") DO NOTHING
                            ''', doc_id, ref_id, original_name, 70, 'mentioned', datetime.now())
                            
                            linked_count += 1
                        except Exception as e:
                            print(f"Error linking document {doc_id} to reference {ref_id}: {e}")
            
            print(f"\nMigration complete!")
            print(f"- Created {len(reference_map)} references")
            print(f"- Created document links: {linked_count}")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(migrate_people_to_references())

