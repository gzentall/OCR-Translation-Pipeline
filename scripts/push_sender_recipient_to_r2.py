#!/usr/bin/env python3
"""Push sender/recipient fields from local documents to R2."""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))
load_dotenv()

os.environ['USE_R2'] = 'true'

from scripts.r2_storage import R2Storage

def main():
    r2 = R2Storage()
    docs_dir = Path('ocr_storage/documents')
    updated = 0
    
    print('📤 Pushing sender/recipient to R2...')
    
    for doc_file in sorted(docs_dir.glob('*.json')):
        doc_id = doc_file.stem
        
        with open(doc_file) as f:
            local_doc = json.load(f)
        
        r2_doc = r2.get_document(doc_id)
        
        if r2_doc:
            r2_doc['sender'] = local_doc.get('sender', '')
            r2_doc['recipient'] = local_doc.get('recipient', '')
            
            if r2.save_document(doc_id, r2_doc):
                updated += 1
                if updated % 30 == 0:
                    print(f'  {updated} documents...')
    
    print(f'✅ Updated {updated} documents in R2')

if __name__ == '__main__':
    main()

