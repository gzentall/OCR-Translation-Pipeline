#!/usr/bin/env python3
"""Quick script to upload metadata.json to R2"""

import os
import json
import boto3
from pathlib import Path

# R2 configuration
endpoint_url = os.getenv("R2_ENDPOINT_URL")
access_key_id = os.getenv("R2_ACCESS_KEY_ID")
secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME")

if not all([endpoint_url, access_key_id, secret_access_key, bucket_name]):
    print("❌ R2 credentials not set in environment")
    exit(1)

# Initialize S3 client for R2
s3_client = boto3.client(
    service_name='s3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='auto'
)

# Load local metadata
metadata_file = Path("ocr_storage/metadata.json")
with open(metadata_file) as f:
    metadata = json.load(f)

print(f"Uploading metadata with {len(metadata['documents'])} documents to R2...")

# Upload to R2
s3_client.put_object(
    Bucket=bucket_name,
    Key="metadata.json",
    Body=json.dumps(metadata, indent=2),
    ContentType='application/json'
)

print(f"✅ Metadata uploaded to R2!")
print(f"   Documents: {len(metadata['documents'])}")
print(f"   People: {len(metadata.get('people', {}))}")

