#!/usr/bin/env python3
"""
Script to populate the local storage with sample references.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.local_storage import LocalOCRStorage

def populate_references():
    """Add sample references to the local storage."""
    storage = LocalOCRStorage()
    
    # Sample references with hierarchy and types
    sample_references = [
        {
            'type': 'PERSON',
            'name': 'Robert Lweisenthal',
            'aliases': ['robert lweisenthal', 'Robert Lweisenthal', 'Bob'],
            'notes': 'Main correspondent in the letters'
        },
        {
            'type': 'PERSON', 
            'name': 'Elizabeth Zentall',
            'aliases': ['elizabeth zentall', 'Elizabeth Zentall', 'Liz'],
            'notes': 'Family member mentioned in correspondence'
        },
        {
            'type': 'PERSON',
            'name': 'Gabe Zentall', 
            'aliases': ['gabe', 'Gabe', 'Gabriel'],
            'notes': 'Recipient of many letters'
        },
        {
            'type': 'PERSON',
            'name': 'His Rol',
            'aliases': ['his rol', 'His Rol'],
            'notes': 'Mentioned in German letters'
        },
        {
            'type': 'PLACE',
            'name': 'Münster',
            'aliases': ['Münster', 'Munster', 'Münster, Germany'],
            'notes': 'German city mentioned in correspondence'
        },
        {
            'type': 'PLACE',
            'name': 'Haus Kalm',
            'aliases': ['Haus Kalm', 'Haus Kalm, Germany'],
            'notes': 'Specific location mentioned in letters'
        },
        {
            'type': 'PLACE',
            'name': 'Paris',
            'aliases': ['Paris', 'Paris, France'],
            'notes': 'City mentioned in travel plans'
        },
        {
            'type': 'PLACE',
            'name': 'Hamburg',
            'aliases': ['Hamburg', 'Hamburg, Germany'],
            'notes': 'German city mentioned in travel plans'
        },
        {
            'type': 'EVENT',
            'name': 'World War II',
            'aliases': ['WWII', 'World War 2', 'Second World War'],
            'notes': 'Historical context for the correspondence'
        },
        {
            'type': 'EVENT',
            'name': 'Business Exhibition',
            'aliases': ['exhibition', 'trade show', 'business display'],
            'notes': 'Business event mentioned in letters'
        }
    ]
    
    print("Adding sample references...")
    added_count = 0
    
    for ref_data in sample_references:
        try:
            reference = storage.add_reference(
                ref_type=ref_data['type'],
                name=ref_data['name'],
                aliases=ref_data['aliases'],
                notes=ref_data['notes']
            )
            if reference:
                print(f"✅ Added {ref_data['type']}: {ref_data['name']}")
                added_count += 1
            else:
                print(f"❌ Failed to add {ref_data['name']}")
        except Exception as e:
            print(f"❌ Error adding {ref_data['name']}: {e}")
    
    print(f"\n🎉 Successfully added {added_count} references!")
    
    # List all references to verify
    print("\n📋 All references in the system:")
    all_refs = storage.list_references()
    for ref in all_refs:
        print(f"  {ref['type']}: {ref['name']} (ID: {ref['id']})")
        if ref.get('aliases'):
            print(f"    Aliases: {', '.join(ref['aliases'])}")
        if ref.get('notes'):
            print(f"    Notes: {ref['notes']}")
        print()

if __name__ == "__main__":
    populate_references()

