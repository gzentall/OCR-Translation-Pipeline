# Deployment Update Guide

Quick guide to deploy the latest code and migrate local data to your existing hosted server.

## Overview

You need to:
1. Deploy latest code changes from `feature/ocr-quality-enhancement` branch
2. Transfer local data (177 documents + 1,481 images = ~3.6 GB)
3. Restart the application

---

## Step 1: Deploy Code Updates

SSH into your hosted server and update the code:

```bash
# SSH to your server
ssh user@your-server.com

# Navigate to application directory
cd /var/www/ocr-translation-pipeline  # Or wherever your app is deployed

# Stash any local changes (if any)
git stash

# Fetch latest changes
git fetch origin

# Checkout the feature branch with all new changes
git checkout feature/ocr-quality-enhancement
git pull origin feature/ocr-quality-enhancement

# Update Python dependencies (in case any changed)
source venv/bin/activate  # or however you activate your venv
pip install -r requirements.txt --upgrade
```

**Recent commits being deployed:**
- `3a573f1` - Summary generation for 92 documents
- `a1cd500` - Sender/recipient name mapping
- `4f28825` - European location geocoding fixes
- Plus UI improvements and bug fixes

---

## Step 2: Transfer Data Files

From your **local machine**, transfer the data:

### Option A: Full Data Sync (Recommended)

```bash
# Transfer all document JSONs
rsync -avz --progress \
  ocr_storage/ \
  user@your-server.com:/var/www/ocr-translation-pipeline/ocr_storage/

# Transfer all images (this is ~3.5 GB, will take 10-30 min)
rsync -avz --progress \
  letters/work/ \
  user@your-server.com:/var/www/ocr-translation-pipeline/letters/work/

# Transfer reference data
rsync -avz --progress \
  reference_data.json \
  user@your-server.com:/var/www/ocr-translation-pipeline/
```

**Progress tracking**: rsync will show you progress. For the images folder:
- On fast connection (100 Mbps): ~5-10 minutes
- On moderate connection (25 Mbps): ~20-30 minutes

### Option B: Incremental Sync (If you've already deployed some data)

Only sync new/changed files:

```bash
# Only sync documents from batch 108-177 (if older batches already deployed)
rsync -avz --progress \
  ocr_storage/documents/doc_202511*.json \
  user@your-server.com:/var/www/ocr-translation-pipeline/ocr_storage/documents/

# Only sync newer images
rsync -avz --progress --update \
  letters/work/ \
  user@your-server.com:/var/www/ocr-translation-pipeline/letters/work/

# Update metadata
rsync -avz --progress \
  ocr_storage/metadata.json \
  user@your-server.com:/var/www/ocr-translation-pipeline/ocr_storage/
```

---

## Step 3: Verify Data on Server

SSH back to the server and verify the data arrived:

```bash
ssh user@your-server.com
cd /var/www/ocr-translation-pipeline

# Check document count
echo "Documents: $(ls ocr_storage/documents/*.json | wc -l)"

# Check image count  
echo "Images: $(ls letters/work/*.png | wc -l)"

# Check a sample document has all fields
python3 << 'EOF'
import json
from pathlib import Path

# Check a recent document
doc_files = sorted(Path('ocr_storage/documents').glob('*.json'))
if doc_files:
    with open(doc_files[-1]) as f:
        doc = json.load(f)
    print(f"Sample document: {doc.get('title')}")
    print(f"  Has summary: {'Yes' if doc.get('summary') else 'No'}")
    print(f"  Has sender: {doc.get('sender', 'No')}")
    print(f"  Has recipient: {doc.get('recipient', 'No')}")
    print(f"  Page count: {doc.get('page_count', 0)}")
EOF
```

Expected output:
```
Documents: 177
Images: 1481
Sample document: 177-1932-10-16-ger
  Has summary: Yes
  Has sender: Robert Zentall
  Has recipient: (might be None for some)
  Page count: 4
```

---

## Step 4: Restart Application

Restart your application service (adjust based on your setup):

### If using systemd:
```bash
sudo systemctl restart ocr-pipeline
sudo systemctl status ocr-pipeline

# Check logs for any errors
journalctl -u ocr-pipeline -n 50 --no-pager
```

### If using PM2:
```bash
pm2 restart ocr-pipeline
pm2 logs ocr-pipeline --lines 50
```

### If using Docker:
```bash
docker-compose down
docker-compose up -d
docker-compose logs --tail=50
```

### If running directly:
```bash
# Kill old process
pkill -f "python.*app.py"

# Start new process
nohup python3 app.py > logs/app.log 2>&1 &
```

---

## Step 5: Verify Deployment

Test the live site:

```bash
# Check if server is responding
curl -I https://your-domain.com

# Check API is working
curl https://your-domain.com/api/documents | jq '.success'

# Should return: true
```

**Test in browser:**
1. Go to your deployed URL
2. Log in
3. Check document count shows 177
4. Open a document from batch 108-177
5. Verify:
   - ✅ Images load
   - ✅ Summary is present
   - ✅ Sender/recipient fields show (if populated)
   - ✅ Locations show correct (Prague = Czech Republic, not OK)
6. Open References tab - should show all people/places/etc.

---

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# On server
cd /var/www/ocr-translation-pipeline

# Revert code to previous version
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>

# Restart
sudo systemctl restart ocr-pipeline

# Data rollback (if you have backups)
# Restore from your most recent backup
```

**Prevention**: Before deploying, make a backup:
```bash
# On server, before deployment
tar -czf /tmp/ocr_backup_$(date +%Y%m%d).tar.gz \
  ocr_storage/ letters/work/
```

---

## Post-Deployment Checklist

- [ ] Code updated to `feature/ocr-quality-enhancement`
- [ ] All 177 documents transferred
- [ ] All 1,481 images transferred
- [ ] `reference_data.json` transferred
- [ ] Application restarted successfully
- [ ] No errors in logs
- [ ] Can access site at deployed URL
- [ ] Document list shows 177 items
- [ ] Images load in document viewer
- [ ] Summaries display for all documents
- [ ] Sender/recipient fields populate correctly
- [ ] Search and filters work
- [ ] References tab shows all reference types

---

## New Features Available After Deployment

Your users will now have:

1. **Complete Summaries** - All 177 documents now have AI-generated summaries
2. **Correct Locations** - Prague shows as Czech Republic, not Oklahoma
3. **Sender/Recipient** - Most documents have identified correspondents
4. **References System** - Complete with people, places, events, themes, emotions
5. **Bulk Operations** - Change status for multiple documents at once
6. **Select All** - Easy selection of documents and references
7. **Improved UI** - Better scrolling in document editor
8. **Bug Fixes** - Various stability and display improvements

---

## Monitoring & Maintenance

After deployment, monitor for a few hours:

```bash
# Watch logs in real-time
journalctl -u ocr-pipeline -f

# Or check for errors periodically
journalctl -u ocr-pipeline --since "10 minutes ago" | grep -i error

# Monitor disk space
df -h

# Monitor memory usage
free -h
```

---

## Common Issues & Solutions

### Images Not Loading
```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/ocr-translation-pipeline/letters/work
sudo chmod -R 755 /var/www/ocr-translation-pipeline/letters/work
```

### Missing Summaries
The summaries are stored in the document JSON files. If they're missing:
```bash
# Verify JSON files transferred correctly
ls -lh ocr_storage/documents/ | head -10

# Check a sample file
cat ocr_storage/documents/<some-doc>.json | jq '.summary'
```

### 500 Errors
```bash
# Check Python dependencies
pip list | grep -E "flask|openai|google"

# Verify environment variables
cat .env | grep -E "OPENAI|GOOGLE|SECRET"

# Check logs for detailed error
tail -f logs/app.log
```

### Old Data Still Showing
```bash
# Clear any application cache
sudo systemctl restart ocr-pipeline

# Clear browser cache and do hard refresh (Cmd+Shift+R)
```

---

## Data Size Summary

What you're transferring:
- **OCR Storage**: 4.1 MB (177 JSON files + metadata)
- **Images**: 3.5 GB (1,481 PNG files)
- **Reference Data**: ~100 KB (1 JSON file)
- **Total**: ~3.6 GB

**Transfer time estimate**:
- Fast connection (100 Mbps): 5-10 minutes
- Average connection (25-50 Mbps): 15-30 minutes
- Slow connection (10 Mbps): 45-60 minutes

---

## Quick Command Reference

```bash
# Full deployment in one go
ssh user@your-server.com << 'ENDSSH'
cd /var/www/ocr-translation-pipeline
git checkout feature/ocr-quality-enhancement
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart ocr-pipeline
ENDSSH

# Then from local machine
rsync -avz ocr_storage/ user@your-server.com:/var/www/ocr-translation-pipeline/ocr_storage/
rsync -avz letters/work/ user@your-server.com:/var/www/ocr-translation-pipeline/letters/work/
rsync -avz reference_data.json user@your-server.com:/var/www/ocr-translation-pipeline/
```

---

## Questions?

Before deploying, confirm:
1. ✅ What's the actual path to your app on the server?
2. ✅ How is the app currently running? (systemd/PM2/Docker/other)
3. ✅ Do you have SSH access and sufficient permissions?
4. ✅ Is there enough disk space? (Need ~4 GB free for new data)
5. ✅ Do you have a backup of current production data?

Good luck with the deployment! 🚀

