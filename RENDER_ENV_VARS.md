# Render Environment Variables

## Required R2 Configuration

Add these environment variables to your Render service to enable R2 storage:

```env
USE_R2=true
R2_ENDPOINT_URL=https://868ccd57fac77f7230e081dd06fa08c0.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=5e4aea981277d0a2b658b2cc365fa645
R2_SECRET_ACCESS_KEY=7c30373db53b7eda638e459d0ad694a7262212fcbb5030bd5984b7c809e577ff
R2_BUCKET_NAME=documents
```

## How to Add to Render

1. Go to https://dashboard.render.com/
2. Select your service: `ocr-translation-pipeline`
3. Click **Environment** in the left sidebar
4. Click **Add Environment Variable**
5. Add each key-value pair above
6. Click **Save Changes**
7. Render will automatically redeploy

## Why This Is Needed

- `ocr_storage/` is gitignored (not in deployment)
- All 178 documents + 1,384 images are stored in R2
- Without these env vars, the app can't access R2
- With these env vars, the app loads everything from R2

## Expected Result

After adding env vars and redeploying:
- ✅ All 178 documents will load
- ✅ All images will be served via R2 CDN
- ✅ Fast, free hosting
- ✅ No storage costs

## Troubleshooting

If documents still don't load:
1. Check Render logs for R2 connection errors
2. Verify all 5 env vars are set correctly
3. Check that deployment completed successfully
4. Try manual redeploy if auto-deploy didn't trigger

