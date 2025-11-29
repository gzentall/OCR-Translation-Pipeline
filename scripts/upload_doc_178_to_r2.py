#!/usr/bin/env python3
"""Upload document 178 JSON to R2"""

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

# Load document 178
doc_file = Path("ocr_storage/documents/doc_20251127_110849.json")
with open(doc_file) as f:
    doc = json.load(f)

doc_id = doc.get('id')
print(f"Uploading document to R2:")
print(f"  ID: {doc_id}")
print(f"  Filename: {doc.get('filename')}")
print(f"  Page count: {doc.get('page_count')}")

# Upload to R2
key = f"documents/{doc_id}.json"
s3_client.put_object(
    Bucket=bucket_name,
    Key=key,
    Body=json.dumps(doc, indent=2),
    ContentType='application/json'
)

print(f"\n✅ Document uploaded to R2 at: {key}")

