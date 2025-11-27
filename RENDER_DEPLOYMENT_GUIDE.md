# Render Deployment Guide

Guide for deploying updates to your existing Render.com deployment.

**Your Site**: https://ocr-translation-pipeline.onrender.com/

---

## ⚠️ Important: Render Storage Considerations

**Render Hobby plan uses EPHEMERAL storage** - files are lost on each deploy/restart!

You have two options:

### Option 1: Add Persistent Disk (Recommended)
**Cost**: $1-2/month for 1-5 GB  
**Pros**: Simple, fast, keeps data between deploys  
**Best for**: Your current setup with local JSON storage

### Option 2: Use External Storage
**Cost**: $0-5/month (S3, Cloudflare R2)  
**Pros**: Scalable, separate from app  
**Best for**: Future growth, multiple servers

---

## 🚀 Quick Deployment (Option 1 - With Persistent Disk)

### Step 1: Add Persistent Disk to Your Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click on your `ocr-translation-pipeline` service
3. Go to **"Disks"** tab
4. Click **"Add Disk"**
5. Configure:
   - **Name**: `ocr-data`
   - **Mount Path**: `/var/data`
   - **Size**: 5 GB (for your 3.6 GB data + growth)
6. Click **"Save Changes"**

⚠️ **Your app will restart** - this is expected.

### Step 2: Update Code to Use Persistent Disk

You need to modify your app to store data on the persistent disk instead of the ephemeral filesystem.

Create a new file `scripts/render_config.py`:

```python
"""
Render-specific configuration for persistent storage.
"""
import os

# Check if running on Render with persistent disk
RENDER_DISK_PATH = os.environ.get('RENDER_DISK_PATH', '/var/data')
IS_RENDER = os.environ.get('RENDER', False)

if IS_RENDER and os.path.exists(RENDER_DISK_PATH):
    # Use persistent disk
    OCR_STORAGE_BASE = os.path.join(RENDER_DISK_PATH, 'ocr_storage')
    IMAGES_BASE = os.path.join(RENDER_DISK_PATH, 'letters', 'work')
    REFERENCE_DATA = os.path.join(RENDER_DISK_PATH, 'reference_data.json')
else:
    # Use local paths (development)
    OCR_STORAGE_BASE = 'ocr_storage'
    IMAGES_BASE = 'letters/work'
    REFERENCE_DATA = 'reference_data.json'

# Ensure directories exist
os.makedirs(OCR_STORAGE_BASE, exist_ok=True)
os.makedirs(os.path.join(OCR_STORAGE_BASE, 'documents'), exist_ok=True)
os.makedirs(IMAGES_BASE, exist_ok=True)
```

Update `scripts/local_storage.py` to use this config:

```python
# At the top of the file, add:
from scripts.render_config import OCR_STORAGE_BASE

# Then replace any hardcoded 'ocr_storage' paths with OCR_STORAGE_BASE
```

### Step 3: Set Environment Variable in Render

1. In Render Dashboard → Your Service → **Environment**
2. Add environment variable:
   - **Key**: `RENDER_DISK_PATH`
   - **Value**: `/var/data`
3. Click **"Save Changes"**

### Step 4: Deploy Code

```bash
# On your local machine
cd /Users/gzentall/OCR-Translation-Pipeline

# Make sure you're on the feature branch
git checkout feature/ocr-quality-enhancement

# Push to trigger deploy
git push origin feature/ocr-quality-enhancement
```

Render will **automatically deploy** when you push to the connected branch!

### Step 5: Upload Data to Render

Once deployed, you need to upload your data to the persistent disk.

**Option A: Use Render Shell (Easiest)**

1. In Render Dashboard → Your Service
2. Click **"Shell"** tab
3. You'll get a terminal connected to your running service
4. Run these commands:

```bash
# In Render shell
cd /var/data

# Create directories
mkdir -p ocr_storage/documents
mkdir -p letters/work

# Now you need to upload files from local to here
# See "Upload Data" section below
```

**Option B: Upload via API/Script**

From your local machine, create an upload script:

```python
# scripts/upload_to_render.py
import requests
import json
from pathlib import Path

RENDER_URL = "https://ocr-translation-pipeline.onrender.com"

# Upload a document
def upload_document(doc_path):
    with open(doc_path) as f:
        doc_data = json.load(f)
    
    response = requests.post(
        f"{RENDER_URL}/api/documents",
        json=doc_data,
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    return response.json()

# Upload all documents
for doc_file in Path('ocr_storage/documents').glob('*.json'):
    print(f"Uploading {doc_file.name}...")
    upload_document(doc_file)
```

---

## 🚀 Alternative: Quick Deployment (Option 2 - Using Current Setup)

If you don't want to add persistent disk yet, you can use Render's ephemeral storage with a trade-off:

**Trade-off**: Data will reset on each deploy, but for a read-only archive this might be acceptable.

### Step 1: Include Data in Git (Not Recommended for Large Data)

**⚠️ Not recommended** - Your 3.5 GB of images will make the repo huge.

### Step 2: Use Render Build Command to Download Data

In Render Dashboard → Your Service → Settings:

**Build Command**:
```bash
pip install -r requirements.txt && python scripts/download_data.sh
```

Create `scripts/download_data.sh`:
```bash
#!/bin/bash
# Download data from external storage on each deploy
aws s3 sync s3://your-bucket/ocr_storage ./ocr_storage
aws s3 sync s3://your-bucket/images ./letters/work
```

---

## 📤 Uploading Data to Render

Since you can't use rsync/scp with Render, you have a few options:

### Method 1: Use Render Shell + wget/curl

1. Upload your data files to a temporary location (Dropbox, Google Drive, etc.)
2. In Render Shell:

```bash
cd /var/data

# Download your data archive
curl -L "https://your-dropbox-link.com/data.tar.gz" -o data.tar.gz

# Extract
tar -xzf data.tar.gz

# Verify
ls -lh ocr_storage/documents | wc -l  # Should show 177
ls -lh letters/work | wc -l  # Should show 1481
```

### Method 2: Create a Data Upload Endpoint

Add to `app.py`:

```python
@app.route('/admin/upload-document', methods=['POST'])
@login_required
def upload_document_data():
    """Admin endpoint to upload document data."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    doc_id = data.get('id')
    
    # Save to persistent disk
    storage.save_document(doc_id, data)
    
    return jsonify({'success': True})

@app.route('/admin/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Admin endpoint to upload images."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    file = request.files['image']
    filename = secure_filename(file.filename)
    
    # Save to persistent disk
    image_path = os.path.join(IMAGES_BASE, filename)
    file.save(image_path)
    
    return jsonify({'success': True, 'filename': filename})
```

Then create a local script to upload:

```python
# scripts/upload_to_render_service.py
import requests
import json
from pathlib import Path

BASE_URL = "https://ocr-translation-pipeline.onrender.com"
# You'll need to get your auth token after logging in

def login():
    response = requests.post(f"{BASE_URL}/login", json={
        "email": "gabe@zentall.com",
        "password": "your-password"
    })
    return response.cookies

def upload_documents(cookies):
    for doc_file in Path('ocr_storage/documents').glob('*.json'):
        with open(doc_file) as f:
            doc = json.load(f)
        
        print(f"Uploading {doc_file.name}...")
        response = requests.post(
            f"{BASE_URL}/admin/upload-document",
            json=doc,
            cookies=cookies
        )
        if response.status_code != 200:
            print(f"  Error: {response.text}")

def upload_images(cookies):
    for img_file in Path('letters/work').glob('*.png'):
        print(f"Uploading {img_file.name}...")
        with open(img_file, 'rb') as f:
            files = {'image': (img_file.name, f, 'image/png')}
            response = requests.post(
                f"{BASE_URL}/admin/upload-image",
                files=files,
                cookies=cookies
            )
        if response.status_code != 200:
            print(f"  Error: {response.text}")

if __name__ == '__main__':
    cookies = login()
    upload_documents(cookies)
    upload_images(cookies)
```

---

## 🔄 Simple Deployment Workflow

Once set up, your workflow is:

```bash
# 1. Make changes locally
git add .
git commit -m "Your changes"

# 2. Push to trigger deploy
git push origin feature/ocr-quality-enhancement

# 3. Render automatically deploys (takes 2-5 minutes)

# 4. Check deployment status at:
# https://dashboard.render.com/
```

No need to SSH, no need to manually restart - **Render handles it all!**

---

## ✅ Verification After Deploy

1. Go to https://ocr-translation-pipeline.onrender.com/
2. Check that documents load (should show 177)
3. Open a document and verify:
   - Summary displays
   - Images load
   - Sender/recipient show correctly
4. Check References tab

---

## 📊 Current State

Your deployment:
- **Platform**: Render.com (Hobby Plan - $0/month)
- **URL**: https://ocr-translation-pipeline.onrender.com/
- **Data**: Currently uses ephemeral storage (resets on deploy)
- **Auto-deploy**: Enabled (pushes to branch trigger deploy)

After adding persistent disk:
- **Storage**: 5 GB persistent disk ($1-2/month)
- **Data**: Survives deploys and restarts
- **Total cost**: ~$1-2/month

---

## 🎯 Recommended Next Steps

1. **Add Persistent Disk** (5 GB for $1-2/month)
   - Ensures data survives deploys
   - Mount at `/var/data`

2. **Update Code** to use persistent disk paths
   - Modify `local_storage.py` to check for `/var/data`
   - Create directories on first run

3. **Deploy Code Update**
   - Push to GitHub
   - Render auto-deploys

4. **Upload Data** via Render Shell
   - Use wget/curl to download from temporary storage
   - Or use upload script method

5. **Verify** everything works

---

## 💡 Alternative: Use S3 for Images

For the 3.5 GB of images, consider Cloudflare R2 (S3-compatible):
- **Cost**: Free up to 10 GB storage
- **Bandwidth**: 10 GB/month free
- **Benefits**: Don't need to upload on each deploy, images load faster

Setup:
```python
# In app.py
import boto3

s3 = boto3.client('s3',
    endpoint_url='https://your-account.r2.cloudflarestorage.com',
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY')
)

@app.route('/documents/<doc_id>/images/<int:page_num>')
def get_document_image(doc_id, page_num):
    # Generate presigned URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'ocr-images', 'Key': f'{doc_id}-{page_num}.png'},
        ExpiresIn=3600
    )
    return redirect(url)
```

Upload once:
```bash
# Install rclone
brew install rclone

# Configure for R2
rclone config

# Upload images
rclone sync letters/work/ r2:ocr-images/
```

---

## 🆘 Troubleshooting

### Deploy Failed
Check build logs in Render Dashboard → Your Service → Logs

### Data Not Persisting
Verify persistent disk is mounted:
```bash
# In Render shell
df -h | grep /var/data
ls -la /var/data
```

### Images Not Loading
Check image paths and permissions:
```bash
# In Render shell
ls -lh /var/data/letters/work/ | head -10
```

### Environment Variables Missing
Render Dashboard → Your Service → Environment
Make sure all required vars are set:
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `GEOAPIFY_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS` (base64 encoded)
- `RENDER_DISK_PATH`

---

## 📝 Summary

**For your Render deployment:**

1. ✅ Code deploys automatically on git push
2. ⚠️ Need to add persistent disk for data ($1-2/month)
3. 📤 Upload data via Render Shell or API
4. 🚀 Total deployment time: 30-60 minutes (mostly data upload)

**Current commits to deploy:**
- Summary generation (92 documents)
- Name mapping fixes
- European location corrections
- UI improvements

All ready to go! 🎉

