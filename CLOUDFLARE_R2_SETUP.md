# Cloudflare R2 Setup for Render Free Tier

## Cost Comparison

### Option 1: Upgrade Render
- **Render Starter plan**: $7/month
- **Persistent disk**: Included
- **Total**: $7/month ($84/year)

### Option 2: Use Cloudflare R2 (Recommended)
- **Render**: Stay on Free tier = $0/month
- **Cloudflare R2**: FREE for 10 GB storage = $0/month
- **Total**: $0/month ($0/year)

**Savings**: $84/year! 💰

---

## Cloudflare R2 Details

**What you get FREE:**
- ✅ 10 GB storage (you need 3.6 GB)
- ✅ 1 million Class A operations/month (writes)
- ✅ 10 million Class B operations/month (reads)
- ✅ Zero egress fees (unlike S3)
- ✅ S3-compatible API

**Your usage estimate:**
- Storage: 3.6 GB (36% of free tier)
- Reads: ~1,000-5,000/month (0.05% of free tier)
- Writes: ~200/month for updates (0.02% of free tier)

**Conclusion**: You'll stay well within free tier limits.

---

## Complexity Analysis

### Setup Complexity: **Low-Medium**

**Time investment:**
- Initial setup: 2-3 hours
- Code modifications: 1-2 hours
- Data upload: 30-60 minutes
- **Total**: 4-6 hours one-time

**Technical difficulty**: Medium
- If comfortable with APIs: Easy
- If new to cloud storage: Moderate learning curve

### What You'll Need to Change

**1. Create Cloudflare R2 bucket** (15 minutes)
**2. Modify 3 files in your codebase** (1-2 hours)
**3. Upload data once** (30-60 minutes)
**4. Deploy** (5 minutes)

---

## Step-by-Step Setup

### Part 1: Create Cloudflare R2 Account

1. **Sign up for Cloudflare** (if you don't have account)
   - Go to https://dash.cloudflare.com/sign-up
   - Free tier, no credit card required

2. **Enable R2**
   - Go to https://dash.cloudflare.com/
   - Click "R2" in left sidebar
   - Click "Purchase R2 Plan" (it's free!)

3. **Create a bucket**
   - Click "Create bucket"
   - Name: `ocr-documents`
   - Location: Automatic
   - Click "Create bucket"

4. **Get API credentials**
   - Go to R2 → "Manage R2 API Tokens"
   - Click "Create API token"
   - Name: `ocr-pipeline-access`
   - Permissions: "Object Read & Write"
   - Click "Create API token"
   - **Save these** (you'll need them):
     - Access Key ID
     - Secret Access Key
     - Endpoint URL (looks like: `https://xxxxx.r2.cloudflarestorage.com`)

---

### Part 2: Modify Your Code

#### File 1: Create `scripts/r2_storage.py`

```python
"""
Cloudflare R2 storage adapter.
S3-compatible storage for documents and images.
"""
import os
import json
import boto3
from botocore.client import Config

class R2Storage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        self.bucket = 'ocr-documents'
    
    def save_document(self, doc_id, doc_data):
        """Save document JSON to R2."""
        key = f'documents/{doc_id}.json'
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(doc_data),
            ContentType='application/json'
        )
    
    def get_document(self, doc_id):
        """Get document JSON from R2."""
        key = f'documents/{doc_id}.json'
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return json.loads(response['Body'].read())
        except Exception as e:
            return None
    
    def list_documents(self):
        """List all document IDs."""
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix='documents/'
        )
        docs = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.json'):
                doc_id = obj['Key'].replace('documents/', '').replace('.json', '')
                docs.append(doc_id)
        return docs
    
    def get_image_url(self, image_name, expires_in=3600):
        """Generate presigned URL for image."""
        key = f'images/{image_name}'
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )
        return url
    
    def upload_image(self, image_name, image_data):
        """Upload image to R2."""
        key = f'images/{image_name}'
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image_data,
            ContentType='image/png'
        )
    
    def get_metadata(self):
        """Get metadata.json from R2."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key='metadata.json')
            return json.loads(response['Body'].read())
        except:
            return {'people': {}, 'references': {}}
    
    def save_metadata(self, metadata):
        """Save metadata.json to R2."""
        self.s3.put_object(
            Bucket=self.bucket,
            Key='metadata.json',
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
```

#### File 2: Update `scripts/local_storage.py`

Add R2 support at the top:

```python
# At the top of the file
import os
from scripts.r2_storage import R2Storage

# Check if we should use R2
USE_R2 = os.environ.get('USE_R2', 'false').lower() == 'true'

if USE_R2:
    print("🌐 Using Cloudflare R2 for storage")
    storage_backend = R2Storage()
else:
    print("💾 Using local file storage")
    storage_backend = None  # Use existing local file methods

class LocalOCRStorage:
    def __init__(self, storage_path='ocr_storage'):
        self.storage_path = storage_path
        self.documents_path = os.path.join(storage_path, 'documents')
        self.metadata_path = os.path.join(storage_path, 'metadata.json')
        
        # Use R2 if enabled
        self.use_r2 = USE_R2
        if self.use_r2:
            self.r2 = R2Storage()
        else:
            # Create local directories
            os.makedirs(self.documents_path, exist_ok=True)
    
    def get_document(self, doc_id):
        """Get a document by ID."""
        if self.use_r2:
            return self.r2.get_document(doc_id)
        else:
            # Existing local file logic
            doc_file = os.path.join(self.documents_path, f'{doc_id}.json')
            if os.path.exists(doc_file):
                with open(doc_file, 'r') as f:
                    return json.load(f)
            return None
    
    def update_document(self, doc_id, updates):
        """Update a document."""
        doc = self.get_document(doc_id)
        if doc:
            doc.update(updates)
            if self.use_r2:
                self.r2.save_document(doc_id, doc)
            else:
                # Existing local file logic
                doc_file = os.path.join(self.documents_path, f'{doc_id}.json')
                with open(doc_file, 'w') as f:
                    json.dump(doc, f, indent=2)
    
    # Update other methods similarly...
```

#### File 3: Update `app.py`

Update image serving:

```python
# Add at top
from scripts.r2_storage import R2Storage

USE_R2 = os.environ.get('USE_R2', 'false').lower() == 'true'
if USE_R2:
    r2_storage = R2Storage()

@app.route('/documents/<doc_id>/images/<int:page_num>')
def get_document_image(doc_id, page_num):
    """Serve document images."""
    if USE_R2:
        # Get image from R2
        image_name = f'{doc_id}-{page_num}.png'
        presigned_url = r2_storage.get_image_url(image_name)
        return redirect(presigned_url)
    else:
        # Existing local file serving logic
        image_path = os.path.join('letters/work', f'{doc_id}-{page_num}.png')
        return send_file(image_path)
```

---

### Part 3: Set Environment Variables in Render

1. Go to Render Dashboard → Your Service → Environment
2. Add these variables:
   - `USE_R2` = `true`
   - `R2_ENDPOINT_URL` = `https://xxxxx.r2.cloudflarestorage.com`
   - `R2_ACCESS_KEY_ID` = `<your-access-key>`
   - `R2_SECRET_ACCESS_KEY` = `<your-secret-key>`

---

### Part 4: Upload Your Data to R2

Create upload script `scripts/upload_to_r2.py`:

```python
"""
Upload local data to Cloudflare R2.
Run this once to migrate data.
"""
import os
from pathlib import Path
from scripts.r2_storage import R2Storage
import json

def upload_all_data():
    r2 = R2Storage()
    
    print("📤 Uploading documents...")
    doc_count = 0
    for doc_file in Path('ocr_storage/documents').glob('*.json'):
        with open(doc_file) as f:
            doc = json.load(f)
        
        doc_id = doc_file.stem
        r2.save_document(doc_id, doc)
        doc_count += 1
        if doc_count % 10 == 0:
            print(f"   Uploaded {doc_count} documents...")
    
    print(f"✅ Uploaded {doc_count} documents")
    
    print("\n📤 Uploading images...")
    img_count = 0
    for img_file in Path('letters/work').glob('*.png'):
        with open(img_file, 'rb') as f:
            img_data = f.read()
        
        r2.upload_image(img_file.name, img_data)
        img_count += 1
        if img_count % 100 == 0:
            print(f"   Uploaded {img_count} images...")
    
    print(f"✅ Uploaded {img_count} images")
    
    print("\n📤 Uploading metadata...")
    with open('ocr_storage/metadata.json') as f:
        metadata = json.load(f)
    r2.save_metadata(metadata)
    print("✅ Uploaded metadata")
    
    print("\n🎉 All data uploaded to Cloudflare R2!")

if __name__ == '__main__':
    # Set your R2 credentials first
    os.environ['R2_ENDPOINT_URL'] = 'https://xxxxx.r2.cloudflarestorage.com'
    os.environ['R2_ACCESS_KEY_ID'] = 'your-access-key'
    os.environ['R2_SECRET_ACCESS_KEY'] = 'your-secret-key'
    
    upload_all_data()
```

Run it:
```bash
pip install boto3
python3 scripts/upload_to_r2.py
```

Upload time: 10-30 minutes for 3.6 GB

---

### Part 5: Deploy

```bash
git add .
git commit -m "Add Cloudflare R2 storage support"
git push origin feature/ocr-quality-enhancement
```

Render will auto-deploy!

---

## Pros and Cons

### Cloudflare R2 Approach

**Pros:**
- ✅ **FREE** (saves $84/year)
- ✅ Fast global CDN
- ✅ No egress fees
- ✅ Scalable (up to 10 GB free)
- ✅ Keep Render free tier
- ✅ Better for serving images (faster)
- ✅ Data accessible from anywhere

**Cons:**
- ❌ Requires code changes (4-6 hours)
- ❌ Dependency on external service
- ❌ Slightly more complex architecture
- ❌ Need to manage R2 credentials

### Render Starter Plan

**Pros:**
- ✅ Simpler setup (no code changes)
- ✅ Everything in one place
- ✅ Persistent disk just works
- ✅ More RAM (512 MB → 512 MB with disk)

**Cons:**
- ❌ Costs $7/month ($84/year)
- ❌ Still limited by Render instance
- ❌ Slower image serving
- ❌ No CDN for images

---

## Recommendation

**For your use case (177 documents, mostly static archive):**

### Go with Cloudflare R2 ✅

**Why:**
1. **Free** vs $84/year - significant savings
2. Your data is mostly **read-only** (perfect for R2)
3. **4-6 hours** of work is worth $84 saved
4. **Better performance** for serving images (CDN)
5. **Scalable** - works for 1,000s of documents later

**Time investment breakdown:**
- R2 account setup: 15 min
- Code modifications: 2 hours
- Testing locally: 1 hour
- Data upload: 30-60 min
- Deploy & verify: 30 min
- **Total**: ~4-5 hours

**When to upgrade Render instead:**
1. If you need SSH access frequently
2. If you're running background jobs
3. If you need more than 512 MB RAM
4. If time is more valuable than $84/year

---

## Next Steps

If you choose R2:
1. I can help create the code modifications
2. We'll test locally first
3. Then upload data and deploy

If you choose Render Starter:
1. Just upgrade in dashboard
2. Add persistent disk
3. Deploy and upload data

What would you like to do?

---

## Hybrid Option

**Most cost-effective:**
- Use R2 for images (3.5 GB) - FREE
- Keep documents local on Render Free tier
- Only ~4 MB of documents won't persist (acceptable loss?)
- Re-process documents if needed (you have the source PDFs)

This way:
- Images load fast from CDN
- Documents can be regenerated
- Stay on free tier
- Minimal code changes

