#!/usr/bin/env python3
"""Upload metadata.json to R2"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from local_storage import LocalOCRStorage

# Initialize storage (this loads env vars and connects to R2)
storage = LocalOCRStorage()

if storage.use_r2 and storage.r2:
    print("Uploading metadata to R2...")
    storage.r2.upload_metadata(storage.metadata)
    print(f"✅ Metadata uploaded! Total documents: {len(storage.metadata['documents'])}")
else:
    print("❌ R2 not enabled or not configured")

