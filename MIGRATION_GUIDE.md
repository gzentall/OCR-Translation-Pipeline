# Migration Guide: Local to Remote Server

This guide covers migrating your OCR Translation Pipeline from local development to a remote hosted server.

## Overview

The system has three main data components:
1. **Local Storage** - JSON files and images (`ocr_storage/`, `letters/work/`)
2. **PostgreSQL Database** - User accounts, document metadata
3. **Application Code** - Python/Flask backend, HTML/JS frontend

## Migration Options

### Option 1: Full Local Storage Migration (Recommended for Current Setup)

Since you're primarily using local JSON storage, this is the simplest approach.

#### Step 1: Prepare Remote Server

```bash
# SSH into remote server
ssh user@your-server.com

# Create application directory
mkdir -p /var/www/ocr-translation-pipeline
cd /var/www/ocr-translation-pipeline

# Clone repository
git clone <your-repo-url> .
git checkout feature/ocr-quality-enhancement
```

#### Step 2: Transfer Data Files

From your **local machine**:

```bash
# Transfer OCR storage (documents + metadata)
rsync -avz --progress \
  ocr_storage/ \
  user@your-server.com:/var/www/ocr-translation-pipeline/ocr_storage/

# Transfer images
rsync -avz --progress \
  letters/work/*.png \
  user@your-server.com:/var/www/ocr-translation-pipeline/letters/work/

# Transfer reference data
rsync -avz --progress \
  reference_data.json \
  user@your-server.com:/var/www/ocr-translation-pipeline/
```

**Estimated Transfer Time**: 
- 177 documents (4.1 MB): < 1 minute
- 1,481 images (3.5 GB): 10-30 minutes on good connection (50-100 Mbps)
- Total data: ~3.6 GB (excluding source PDFs)

#### Step 3: Set Up Remote Environment

On **remote server**:

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
  poppler-utils \
  postgresql \
  postgresql-contrib

# Set up environment variables
cp .env.example .env
nano .env  # Edit with production values
```

Required in `.env`:
```bash
# Flask
SECRET_KEY=<generate-new-secret-key>
FLASK_ENV=production

# OpenAI API
OPENAI_API_KEY=<your-api-key>

# Geoapify API  
GEOAPIFY_API_KEY=<your-api-key>

# Google Cloud (for OCR/Translation)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Database
DATABASE_URL=postgresql://user:password@localhost/ocr_db

# File paths
OCR_STORAGE_PATH=/var/www/ocr-translation-pipeline/ocr_storage
```

#### Step 4: Set Up PostgreSQL

```bash
# Create database
sudo -u postgres createdb ocr_db
sudo -u postgres createuser ocr_user -P  # Set password

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ocr_db TO ocr_user;"

# Run migrations
python3 scripts/database.py  # Initialize schema
```

#### Step 5: Set Up Production Server

**Using Gunicorn + Nginx:**

```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/ocr-pipeline.service
```

**Service file** (`/etc/systemd/system/ocr-pipeline.service`):
```ini
[Unit]
Description=OCR Translation Pipeline
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ocr-translation-pipeline
Environment="PATH=/var/www/ocr-translation-pipeline/venv/bin"
ExecStart=/var/www/ocr-translation-pipeline/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    app:app

[Install]
WantedBy=multi-user.target
```

**Nginx configuration** (`/etc/nginx/sites-available/ocr-pipeline`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running operations
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    location /static {
        alias /var/www/ocr-translation-pipeline/static;
        expires 30d;
    }

    location /letters/work {
        alias /var/www/ocr-translation-pipeline/letters/work;
        expires 30d;
    }
}
```

Enable and start:
```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/ocr-pipeline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start application
sudo systemctl enable ocr-pipeline
sudo systemctl start ocr-pipeline
```

#### Step 6: SSL/HTTPS (Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: PostgreSQL Database Migration

If you want to fully use PostgreSQL instead of local JSON:

#### Step 1: Export Current Data to PostgreSQL Format

Create a migration script to convert JSON → PostgreSQL:

```bash
# On local machine
python3 scripts/migrate_json_to_postgres.py
pg_dump ocr_db > ocr_db_backup.sql
```

#### Step 2: Transfer Database

```bash
# Transfer SQL dump
scp ocr_db_backup.sql user@your-server.com:/tmp/

# On remote server
psql -U ocr_user -d ocr_db -f /tmp/ocr_db_backup.sql
```

---

### Option 3: Cloud Storage Integration

For larger deployments, consider cloud storage:

#### AWS S3 for Images
```python
# Update app.py to serve images from S3
import boto3

s3_client = boto3.client('s3')

@app.route('/documents/<doc_id>/images/<int:page_num>')
def get_document_image(doc_id, page_num):
    # Generate presigned URL
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'your-bucket', 'Key': f'{doc_id}-{page_num}.png'},
        ExpiresIn=3600
    )
    return redirect(url)
```

Upload images:
```bash
aws s3 sync letters/work/ s3://your-bucket/images/ --acl private
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup all local data (documents, images, database)
- [ ] Document current system configuration
- [ ] Test migrations on staging server first
- [ ] Ensure API keys are ready for production
- [ ] Set up DNS records for domain

### Data Transfer
- [ ] Transfer `ocr_storage/` directory (177 document JSONs)
- [ ] Transfer `letters/work/` images (~600 files)
- [ ] Transfer `reference_data.json`
- [ ] Export and transfer PostgreSQL database (if using)
- [ ] Transfer `.env` with production values

### Server Setup
- [ ] Install Python 3.9+ and dependencies
- [ ] Install PostgreSQL
- [ ] Install poppler-utils (for pdftoppm)
- [ ] Install Nginx
- [ ] Set up systemd service
- [ ] Configure firewall (allow ports 80, 443)
- [ ] Set up SSL certificate

### Post-Migration
- [ ] Test document browsing
- [ ] Test document editing and saving
- [ ] Test image loading
- [ ] Test reference management
- [ ] Test search functionality
- [ ] Test batch processing (if needed)
- [ ] Set up monitoring/logging
- [ ] Set up automated backups

---

## Maintenance & Backups

### Automated Backups

**Daily backup script** (`/root/backup-ocr.sh`):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/ocr-pipeline"

mkdir -p $BACKUP_DIR

# Backup data files
tar -czf $BACKUP_DIR/ocr_storage_$DATE.tar.gz \
  /var/www/ocr-translation-pipeline/ocr_storage

tar -czf $BACKUP_DIR/images_$DATE.tar.gz \
  /var/www/ocr-translation-pipeline/letters/work

# Backup database
pg_dump ocr_db | gzip > $BACKUP_DIR/ocr_db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
sudo crontab -e
# Add: 0 2 * * * /root/backup-ocr.sh
```

---

## Performance Optimization

### For 177+ Documents

1. **Enable Caching**:
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   
   @app.route('/api/documents')
   @cache.cached(timeout=300)
   def list_documents():
       ...
   ```

2. **Image Optimization**:
   ```bash
   # Compress images before upload
   for img in letters/work/*.png; do
       convert "$img" -quality 85 -resize 2000x2000\> "$img"
   done
   ```

3. **Database Indexes**:
   ```sql
   CREATE INDEX idx_documents_title ON documents(title);
   CREATE INDEX idx_documents_date ON documents(document_date);
   CREATE INDEX idx_references_name ON references(name);
   ```

---

## Troubleshooting

### Images Not Loading
```bash
# Check permissions
sudo chown -R www-data:www-data /var/www/ocr-translation-pipeline/letters/work
sudo chmod -R 755 /var/www/ocr-translation-pipeline/letters/work
```

### API Keys Not Working
```bash
# Verify environment variables are loaded
sudo systemctl status ocr-pipeline
journalctl -u ocr-pipeline -n 50
```

### Slow Performance
```bash
# Check Gunicorn worker count
# Recommended: (2 * CPU cores) + 1
sudo nano /etc/systemd/system/ocr-pipeline.service
# Adjust --workers parameter
```

---

## Cost Estimates (AWS Example)

For 177 documents + 600 images:

- **EC2 t3.small**: $15-20/month
- **RDS PostgreSQL (db.t3.micro)**: $15/month (optional)
- **S3 Storage (1 GB)**: $0.02/month
- **CloudFront CDN**: $1-5/month
- **Total**: ~$30-40/month

**Digital Ocean Droplet**: $12-24/month for similar specs

---

## Questions to Consider

Before migrating, decide:

1. **Storage Strategy**: Keep JSON files or migrate to full PostgreSQL?
2. **Image Hosting**: Local filesystem, S3, or CDN?
3. **Scaling**: Single server or load balanced?
4. **Domain**: What will be the production URL?
5. **Backup Strategy**: How often? Where stored?
6. **Monitoring**: CloudWatch, Datadog, self-hosted?

---

## Next Steps

1. Set up a staging/test server first
2. Run through this guide on staging
3. Test all functionality
4. Document any issues/customizations
5. Schedule production migration during low-usage time
6. Migrate production with tested process
7. Monitor for 24-48 hours post-migration

---

## Support

If you encounter issues during migration:
- Check application logs: `journalctl -u ocr-pipeline -f`
- Check Nginx logs: `tail -f /var/log/nginx/error.log`
- Verify environment: `env | grep -E 'OPENAI|GOOGLE|GEOAPIFY'`
- Test connectivity: `curl http://localhost:5001/api/documents`

