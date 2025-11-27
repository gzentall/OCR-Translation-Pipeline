#!/usr/bin/env python3

"""
Script to set primary aliases for key people, making them the canonical display names.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.local_storage import LocalOCRStorage

# Load environment variables
load_dotenv()

def set_primary_alias(storage: LocalOCRStorage, normalized_key: str, primary_alias: str):
    """
    Set a specific alias as the primary (first) alias for a person.
    """
    if normalized_key not in storage.metadata["people"]:
        print(f"  ⚠️  {normalized_key} not found in people metadata")
        return False
    
    person_data = storage.metadata["people"][normalized_key]
    aliases = person_data.get("aliases", [])
    
    # Remove the primary_alias if it exists elsewhere in the list
    aliases = [a for a in aliases if a.lower() != primary_alias.lower()]
    
    # Add it at the beginning
    aliases.insert(0, primary_alias)
    
    person_data["aliases"] = aliases
    
    print(f"  ✅ Set '{primary_alias}' as primary alias for '{normalized_key}'")
    print(f"     All aliases: {aliases[:5]}{'...' if len(aliases) > 5 else ''}")
    
    return True


def set_primary_aliases(storage_dir: Path):
    """
    Set primary display names for key people.
    """
    print("="*80)
    print("SETTING PRIMARY ALIASES")
    print("="*80)

    storage = LocalOCRStorage(str(storage_dir))

    # Define the primary aliases we want
    primary_mappings = {
        "robert zentall": "Robert Zentall",
        "betty zentall": "Betty Zentall"
    }

    print("\n🔄 Updating primary aliases...")
    
    for normalized_key, primary_alias in primary_mappings.items():
        set_primary_alias(storage, normalized_key, primary_alias)
    
    storage._save_metadata()
    
    print("\n================================================================================")
    print("SUMMARY")
    print("================================================================================")
    print(f"Updated {len(primary_mappings)} people with primary aliases")
    print("================================================================================")

    print("\n🎉 Primary aliases set!")


if __name__ == '__main__':
    storage_path = Path('ocr_storage')
    if not storage_path.exists():
        print(f"Error: Storage directory not found at {storage_path}")
        sys.exit(1)
    
    set_primary_aliases(storage_path)

