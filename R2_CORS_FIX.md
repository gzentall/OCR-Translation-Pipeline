# R2 CORS Configuration Fix

**Problem:** Images not loading on production due to CORS policy blocking R2 requests.

**Error in Console:**
```
Access to fetch at 'https://r2.cloudflarestorage.com/documents...' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' 
header is present on the requested resource.
```

---

## Solution: Add CORS Rules to R2 Bucket

### Step 1: Go to Cloudflare Dashboard

1. Visit: https://dash.cloudflare.com/
2. Navigate to: **R2** → **documents** bucket
3. Click on **Settings** tab
4. Scroll to **CORS Policy**

### Step 2: Add CORS Configuration

Click **Edit CORS Policy** and paste this JSON:

```json
[
  {
    "AllowedOrigins": [
      "https://postmark.zentall.com",
      "https://ocr-translation-pipeline.onrender.com",
      "http://localhost:5001"
    ],
    "AllowedMethods": [
      "GET",
      "HEAD"
    ],
    "AllowedHeaders": [
      "*"
    ],
    "ExposeHeaders": [
      "ETag",
      "Content-Length"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

### Step 3: Save and Test

1. Click **Save**
2. Wait 1-2 minutes for changes to propagate
3. Refresh your production site
4. Open any document
5. Images should now load!

---

## What This Does

- **AllowedOrigins**: Tells R2 to allow requests from your domains
  - Production: `postmark.zentall.com`
  - Render: `ocr-translation-pipeline.onrender.com`
  - Local dev: `localhost:5001`

- **AllowedMethods**: Only allow safe read operations (GET, HEAD)

- **AllowedHeaders**: Accept any request headers

- **ExposeHeaders**: Allow JavaScript to read response headers

- **MaxAgeSeconds**: Cache CORS preflight for 1 hour

---

## Alternative: Make Bucket Public (Not Recommended)

If CORS doesn't work, you can make the bucket public:

### Pros:
- No CORS issues
- Faster (direct URLs, no redirects)
- Simpler

### Cons:
- Anyone with the URL can access images
- URLs are obscure but not secret

### How to Make Public:
1. R2 Dashboard → **documents** bucket
2. Settings → **Public Access**
3. Toggle **Allow Public Access**
4. Update app.py to use public URLs instead of presigned

---

## Testing After CORS Fix

### 1. Check Console
Open DevTools (F12) → Console
- Should see: `✅ Image loaded successfully`
- Should NOT see: CORS errors

### 2. Test Image Loading
- Open any document
- Images should appear instantly
- Check Network tab: Status 200 (not blocked)

### 3. Test Panning
- Zoom in > 100%
- Cursor should change to "grab"
- Click and drag → Should pan
- Cursor should change to "grabbing" while dragging

---

## If CORS Still Doesn't Work

### Check R2 Settings
```bash
# Verify CORS was applied
curl -I https://r2.cloudflarestorage.com/documents/...
# Should include: Access-Control-Allow-Origin: https://postmark.zentall.com
```

### Alternative: Proxy Images Through Flask

Modify `app.py` to serve images directly instead of redirecting:

```python
@app.route('/documents/<doc_id>/images/<int:page_num>')
def get_document_image(doc_id, page_num):
    """Serve images directly from R2 (no redirect)"""
    if local_storage.use_r2 and local_storage.r2:
        image_name = f"{doc_id}-{page_num}.png"
        
        # Get image data from R2
        image_data = local_storage.r2.get_image_data(image_name)
        
        if image_data:
            # Serve directly (no redirect)
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/png'
            response.headers['Cache-Control'] = 'public, max-age=3600'
            return response
    
    # Fallback to local...
```

This avoids CORS entirely but uses more Render bandwidth.

---

## Expected Result

After CORS is configured:
- ✅ Images load instantly
- ✅ No CORS errors in console
- ✅ Panning works when zoomed > 100%
- ✅ Performance remains fast (cached presigned URLs)

---

**Next Step:** Configure CORS in Cloudflare R2 Dashboard now!


