#!/usr/bin/env python3
"""Upload missing images to R2"""

import os
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
s3 = boto3.client(
    service_name='s3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='auto'
)

print("Fetching existing R2 images...")
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix='images/')

r2_images = set()
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            filename = obj['Key'].replace('images/', '')
            r2_images.add(filename)

print(f"  Found {len(r2_images)} images in R2")

# Get local images
work_dir = Path("letters/work")
local_images = list(work_dir.glob("*.png"))
print(f"  Found {len(local_images)} images locally")

# Find missing
missing = [img for img in local_images if img.name not in r2_images]
print(f"\n⚠️  Need to upload: {len(missing)} images")

if not missing:
    print("✅ All images already in R2!")
    exit(0)

# Upload missing images
print(f"\nUploading {len(missing)} images...")
uploaded = 0
failed = 0

for img_file in missing:
    try:
        with open(img_file, 'rb') as f:
            img_data = f.read()
        
        key = f"images/{img_file.name}"
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=img_data,
            ContentType='image/png'
        )
        uploaded += 1
        if uploaded % 10 == 0:
            print(f"  Uploaded {uploaded}/{len(missing)}...")
    except Exception as e:
        print(f"  ❌ Failed: {img_file.name}: {e}")
        failed += 1

print(f"\n✅ Upload complete!")
print(f"   Uploaded: {uploaded}")
if failed:
    print(f"   Failed: {failed}")
print(f"   Total in R2: {len(r2_images) + uploaded}")

