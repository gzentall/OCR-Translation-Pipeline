"""
Cloudflare R2 Storage Adapter
S3-compatible storage for documents, images, and metadata.
"""
import os
import json
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Dict, List, Optional


class R2Storage:
    """Cloudflare R2 storage adapter using S3-compatible API."""
    
    def __init__(self):
        """Initialize R2 client with credentials from environment."""
        self.endpoint_url = os.environ.get('R2_ENDPOINT_URL')
        self.access_key_id = os.environ.get('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.environ.get('R2_BUCKET_NAME', 'documents')
        
        if not all([self.endpoint_url, self.access_key_id, self.secret_access_key]):
            raise ValueError(
                "R2 credentials missing. Please set R2_ENDPOINT_URL, "
                "R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY in environment."
            )
        
        # Initialize S3 client with R2 configuration
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'  # R2 uses 'auto' region
        )
        
        print(f"🌐 R2Storage initialized: bucket={self.bucket_name}")
    
    # ========================================
    # Document Operations
    # ========================================
    
    def save_document(self, doc_id: str, doc_data: Dict) -> bool:
        """
        Save document JSON to R2.
        
        Args:
            doc_id: Document identifier
            doc_data: Document data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f'documents/{doc_id}.json'
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(doc_data, indent=2),
                ContentType='application/json'
            )
            return True
        except ClientError as e:
            print(f"Error saving document {doc_id} to R2: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        Get document JSON from R2.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document data dictionary or None if not found
        """
        try:
            key = f'documents/{doc_id}.json'
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error getting document {doc_id} from R2: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document JSON from R2.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f'documents/{doc_id}.json'
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting document {doc_id} from R2: {e}")
            return False
    
    def list_documents(self) -> List[str]:
        """
        List all document IDs in R2.
        
        Returns:
            List of document IDs
        """
        try:
            doc_ids = []
            paginator = self.s3.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix='documents/'
            ):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.json'):
                        # Extract doc_id from 'documents/doc_id.json'
                        doc_id = key.replace('documents/', '').replace('.json', '')
                        doc_ids.append(doc_id)
            
            return doc_ids
        except ClientError as e:
            print(f"Error listing documents from R2: {e}")
            return []
    
    # ========================================
    # Image Operations
    # ========================================
    
    def upload_image(self, image_name: str, image_data: bytes) -> bool:
        """
        Upload image to R2.
        
        Args:
            image_name: Image filename (e.g., 'doc_id-1.png')
            image_data: Image binary data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f'images/{image_name}'
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType='image/png'
            )
            return True
        except ClientError as e:
            print(f"Error uploading image {image_name} to R2: {e}")
            return False
    
    def upload_image_from_file(self, image_path: Path) -> bool:
        """
        Upload image from local file to R2.
        
        Args:
            image_path: Path to local image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return self.upload_image(image_path.name, image_data)
        except Exception as e:
            print(f"Error uploading image file {image_path}: {e}")
            return False
    
    def get_image_url(self, image_name: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for image.
        
        Args:
            image_name: Image filename (e.g., 'doc_id-1.png')
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string or None if error
        """
        try:
            key = f'images/{image_name}'
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL for {image_name}: {e}")
            return None
    
    def delete_image(self, image_name: str) -> bool:
        """
        Delete image from R2.
        
        Args:
            image_name: Image filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f'images/{image_name}'
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting image {image_name} from R2: {e}")
            return False
    
    def list_images(self, prefix: str = '') -> List[str]:
        """
        List all images in R2.
        
        Args:
            prefix: Optional prefix to filter images (e.g., 'doc_id-')
            
        Returns:
            List of image filenames
        """
        try:
            image_names = []
            paginator = self.s3.get_paginator('list_objects_v2')
            
            search_prefix = f'images/{prefix}' if prefix else 'images/'
            
            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=search_prefix
            ):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    # Extract filename from 'images/filename.png'
                    image_name = key.replace('images/', '')
                    image_names.append(image_name)
            
            return image_names
        except ClientError as e:
            print(f"Error listing images from R2: {e}")
            return []
    
    # ========================================
    # Metadata Operations
    # ========================================
    
    def get_metadata(self) -> Dict:
        """
        Get metadata.json from R2.
        
        Returns:
            Metadata dictionary or empty structure if not found
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key='metadata.json')
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # Return empty metadata structure
                return {
                    'people': {},
                    'references': {},
                    'documents': {}
                }
            print(f"Error getting metadata from R2: {e}")
            return {'people': {}, 'references': {}, 'documents': {}}
    
    def save_metadata(self, metadata: Dict) -> bool:
        """
        Save metadata.json to R2.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key='metadata.json',
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )
            return True
        except ClientError as e:
            print(f"Error saving metadata to R2: {e}")
            return False
    
    # ========================================
    # Utility Operations
    # ========================================
    
    def test_connection(self) -> bool:
        """
        Test R2 connection by listing buckets.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list objects in bucket
            self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            print(f"✅ R2 connection test successful: {self.bucket_name}")
            return True
        except ClientError as e:
            print(f"❌ R2 connection test failed: {e}")
            return False
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with document count, image count, total size
        """
        try:
            stats = {
                'documents': 0,
                'images': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0
            }
            
            paginator = self.s3.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    
                    if key.startswith('documents/'):
                        stats['documents'] += 1
                    elif key.startswith('images/'):
                        stats['images'] += 1
                    
                    stats['total_size_bytes'] += size
            
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
            
            return stats
        except ClientError as e:
            print(f"Error getting storage stats: {e}")
            return {'documents': 0, 'images': 0, 'total_size_bytes': 0, 'total_size_mb': 0}

