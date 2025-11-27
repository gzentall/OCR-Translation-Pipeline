# 🚀 Deployment Checklist

## Pre-Deployment Tasks

### 1. Environment Variables Setup ✅

Create a `.env` file with all required environment variables:

```bash
# Copy the example file
cp .env.example .env
```

**Required Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `RESEND_API_KEY` - Email service API key
- `APP_URL` - Your production URL (e.g., https://your-domain.com)
- `SECRET_KEY` - Flask session secret (generate a secure one)
- `FLASK_ENV` - Set to 'production'

**Optional Variables:**
- `GEOAPIFY_API_KEY` - For location autocomplete
- `NOTION_API_KEY` - For Notion integration
- `OPENAI_API_KEY` - For AI document processing (if using OpenAI)

### 2. API Keys Configuration ✅

Ensure all API key files exist:
- `.gcp_api_key` - Google Cloud API key (Vision + Translation)
- `.openai_api_key` - OpenAI API key (optional)
- `.notion_api_key` - Notion API key (optional)

**Or** set environment variables:
```bash
export GOOGLE_CLOUD_API_KEY="your-key-here"
export OPENAI_API_KEY="sk-your-key-here"
```

### 3. Database Setup ✅

#### A. Create PostgreSQL Database

**Local PostgreSQL:**
```bash
createdb ocr_translation
```

**Or use a hosted service:**
- [Neon](https://neon.tech) - Serverless PostgreSQL (Free tier available)
- [Supabase](https://supabase.com) - PostgreSQL with extras (Free tier available)
- [Railway](https://railway.app) - Easy PostgreSQL hosting
- [Heroku Postgres](https://www.heroku.com/postgres)

#### B. Set DATABASE_URL

```bash
# Format: postgresql://username:password@host:port/database
export DATABASE_URL="postgresql://user:password@localhost:5432/ocr_translation"

# Or for cloud services (example Neon format):
export DATABASE_URL="postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/ocr_translation?sslmode=require"
```

#### C. Initialize Database Tables

```bash
python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine); print('✓ Database initialized')"
```

#### D. Seed Initial Admin User

```bash
python3 seed_database.py
```

This creates an admin user. **Change the default password immediately after deployment!**

### 4. Security Hardening 🔒

#### A. Generate Secure Secret Key

```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Update in `app.py` line 41 or set environment variable:
```bash
export SECRET_KEY="your-generated-secret-key-here"
```

#### B. Update Flask Config for Production

In `app.py`, ensure these are set correctly:

```python
app.secret_key = os.getenv('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')
app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache static files
```

#### C. Disable Debug Mode

In `app.py` line 1769:
```python
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)  # debug=False for production
```

### 5. Dependencies Installation ✅

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (for PDF processing)
# macOS:
brew install poppler

# Ubuntu/Debian:
sudo apt-get install poppler-utils

# CentOS/RHEL:
sudo yum install poppler-utils
```

### 6. Directory Structure ✅

Ensure all required directories exist:

```bash
mkdir -p letters/inbox
mkdir -p letters/work
mkdir -p letters/out/en
mkdir -p letters/out/pdf
mkdir -p letters/out/qa
mkdir -p ocr_storage/documents
mkdir -p ocr_storage/people
```

### 7. File Permissions ✅

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Ensure writable directories
chmod 755 letters/{inbox,work,out}
chmod 755 ocr_storage
```

### 8. Test Integrations ✅

```bash
# Test all API connections
python3 test_integrations.py

# Expected output:
# ✅ Google Cloud Vision API: Working
# ✅ Google Cloud Translation API: Working
# ✅ Database Connection: Working
# ✅ Email Service (Resend): Configured
```

### 9. Git Cleanup ✅

Review and commit your changes:

```bash
# Review what's changed
git status

# Review specific files
git diff app.py
git diff scripts/

# Stage changes
git add .

# Commit with meaningful message
git commit -m "Prepare for deployment: security hardening and configuration"

# Push to remote
git push origin main
```

**Important:** Ensure `.env`, API key files, and `ocr_storage/` are in `.gitignore` (already configured).

---

## Deployment Options

### Option 1: Traditional Server (VPS/EC2)

#### A. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv

# Install PostgreSQL (if hosting locally)
sudo apt install postgresql postgresql-contrib

# Install Nginx (reverse proxy)
sudo apt install nginx

# Install Supervisor (process manager)
sudo apt install supervisor
```

#### B. Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/yourusername/OCR-Translation-Pipeline.git
cd OCR-Translation-Pipeline
sudo chown -R $USER:$USER .
```

#### C. Configure Environment

```bash
# Create .env file
nano .env

# Add all environment variables (see .env.example)
```

#### D. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### E. Setup Gunicorn

```bash
pip install gunicorn

# Test gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

#### F. Configure Supervisor

Create `/etc/supervisor/conf.d/ocr-pipeline.conf`:

```ini
[program:ocr-pipeline]
directory=/var/www/OCR-Translation-Pipeline
command=/var/www/OCR-Translation-Pipeline/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 app:app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/ocr-pipeline.err.log
stdout_logfile=/var/log/ocr-pipeline.out.log
environment=PATH="/var/www/OCR-Translation-Pipeline/venv/bin"
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ocr-pipeline
```

#### G. Configure Nginx

Create `/etc/nginx/sites-available/ocr-pipeline`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /var/www/OCR-Translation-Pipeline/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ocr-pipeline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### H. Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 2: Docker Deployment

#### A. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p letters/inbox letters/work letters/out/en ocr_storage/documents

# Expose port
EXPOSE 5001

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
```

#### B. Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - APP_URL=${APP_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./letters:/app/letters
      - ./ocr_storage:/app/ocr_storage
      - ./.gcp_api_key:/app/.gcp_api_key:ro
      - ./.openai_api_key:/app/.openai_api_key:ro
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ocr_translation
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

#### C. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# Initialize database
docker-compose exec web python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"

# Seed admin user
docker-compose exec web python3 seed_database.py

# View logs
docker-compose logs -f web
```

### Option 3: Platform as a Service (PaaS)

#### Heroku

1. Create `Procfile`:
```
web: gunicorn app:app --workers 4
```

2. Create `runtime.txt`:
```
python-3.11.6
```

3. Deploy:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set RESEND_API_KEY="your-key"
git push heroku main
heroku run python3 seed_database.py
```

#### Railway

1. Connect GitHub repository
2. Add PostgreSQL service
3. Set environment variables
4. Deploy automatically on push

#### Render

1. Create Web Service from repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Add PostgreSQL database
5. Configure environment variables

---

## Post-Deployment Checklist

### 1. Verify Application ✅

```bash
# Check if app is running
curl https://your-domain.com/status

# Expected response:
# {"api_key_exists": true, "directories_exist": {...}, ...}
```

### 2. Test Upload Feature ✅

1. Login at: `https://your-domain.com/login`
2. Upload a test PDF at: `https://your-domain.com/browse`
3. Verify OCR and translation work correctly

### 3. Create Admin Users ✅

1. Login with seeded admin account
2. Go to: `https://your-domain.com/users-page`
3. Create user accounts for your team
4. Test email invitations work

### 4. Monitor Logs ✅

```bash
# Supervisor logs
sudo tail -f /var/log/ocr-pipeline.out.log
sudo tail -f /var/log/ocr-pipeline.err.log

# Or Docker logs
docker-compose logs -f web

# Or check Flask log
tail -f flask.log
```

### 5. Setup Monitoring & Backups 🔍

#### A. Database Backups

```bash
# Create backup script
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/ocr-pipeline"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql
# Keep last 30 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-db.sh" | crontab -
```

#### B. Application Monitoring

Consider adding:
- [Sentry](https://sentry.io) - Error tracking
- [Datadog](https://www.datadoghq.com) - Application monitoring
- [UptimeRobot](https://uptimerobot.com) - Uptime monitoring

#### C. Log Rotation

Create `/etc/logrotate.d/ocr-pipeline`:

```
/var/log/ocr-pipeline*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
}
```

### 6. Performance Optimization 🚀

#### A. Enable Gzip Compression (Nginx)

Add to nginx config:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

#### B. Setup CDN for Static Files

Consider using:
- Cloudflare (Free SSL + CDN)
- AWS CloudFront
- Netlify (for static assets)

#### C. Database Connection Pooling

Already configured with SQLAlchemy NullPool for serverless databases.

### 7. Security Audit ✅

- [ ] HTTPS enabled (SSL certificate)
- [ ] Secret keys rotated from defaults
- [ ] Debug mode disabled
- [ ] Database credentials secured
- [ ] API keys restricted (Google Cloud Console)
- [ ] CORS configured appropriately
- [ ] Rate limiting implemented (optional)
- [ ] Firewall rules configured

### 8. Documentation Updates ✅

- [ ] Update README.md with production URL
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedures

---

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `RESEND_API_KEY` | Resend API key for emails | `re_xxx...` |
| `APP_URL` | Your production URL | `https://your-domain.com` |
| `SECRET_KEY` | Flask session secret | Generated 64-char hex string |

### Optional

| Variable | Description | Example |
|----------|-------------|---------|
| `GEOAPIFY_API_KEY` | Location autocomplete | Your API key |
| `NOTION_API_KEY` | Notion integration | `secret_xxx...` |
| `OPENAI_API_KEY` | OpenAI AI processing | `sk-xxx...` |
| `FLASK_ENV` | Environment mode | `production` |
| `PORT` | Server port | `5001` |

### File-based API Keys

Alternatively, create these files in project root:
- `.gcp_api_key` - Google Cloud API key
- `.openai_api_key` - OpenAI API key
- `.notion_api_key` - Notion API key

---

## Troubleshooting

### Application won't start

```bash
# Check logs
sudo supervisorctl tail -f ocr-pipeline stderr

# Common issues:
# 1. Missing DATABASE_URL
# 2. Database not initialized
# 3. Port already in use
# 4. Missing dependencies
```

### Database connection errors

```bash
# Test connection
python3 -c "from scripts.database import engine; print(engine.connect())"

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Upload fails

```bash
# Check disk space
df -h

# Check directory permissions
ls -la letters/

# Check max upload size (nginx)
grep client_max_body_size /etc/nginx/sites-enabled/ocr-pipeline
```

### OCR/Translation not working

```bash
# Verify API keys
python3 test_integrations.py

# Check Google Cloud quotas
# Visit: https://console.cloud.google.com/apis/dashboard
```

---

## Rollback Plan

If deployment fails:

```bash
# Revert to previous version
git revert HEAD
git push

# Restart services
sudo supervisorctl restart ocr-pipeline

# Or with Docker
docker-compose down
git checkout previous-stable-tag
docker-compose up -d
```

---

## Support Contacts

- Database issues: Check cloud provider dashboard
- Email delivery: [Resend Dashboard](https://resend.com/dashboard)
- API quotas: [Google Cloud Console](https://console.cloud.google.com)

---

## Next Steps

After successful deployment:

1. ✅ Change default admin password
2. ✅ Create user accounts for your team
3. ✅ Upload test documents to verify pipeline
4. ✅ Setup monitoring and alerts
5. ✅ Schedule regular backups
6. ✅ Document any custom configurations

**Congratulations on your deployment! 🎉**


