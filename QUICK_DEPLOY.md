# ⚡ Quick Deployment Guide

This guide will get you deployed in minutes.

## Prerequisites

- PostgreSQL database (local or cloud)
- Python 3.11+
- API keys ready (Google Cloud, Resend)

---

## 🚀 Option 1: Docker (Fastest)

Perfect if you have Docker installed:

```bash
# 1. Configure environment
cp env.template .env
nano .env  # Add your DATABASE_URL, API keys, etc.

# 2. Create API key files
echo "your-google-api-key" > .gcp_api_key

# 3. Deploy with Docker
bash deploy.sh docker

# ✅ Done! App running at http://localhost:5001
```

---

## 🐍 Option 2: Traditional Python (Most Control)

### Step 1: Setup Environment

```bash
# Clone and enter directory
cd /path/to/OCR-Translation-Pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Poppler (for PDF processing)
brew install poppler  # macOS
# sudo apt install poppler-utils  # Ubuntu/Debian
```

### Step 2: Configure

```bash
# Copy environment template
cp env.template .env

# Edit with your values
nano .env
```

**Required in .env:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/ocr_translation
RESEND_API_KEY=re_your_key_here
APP_URL=https://your-domain.com
SECRET_KEY=generate-with-python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Create API key files:**
```bash
echo "your-google-cloud-api-key" > .gcp_api_key
```

### Step 3: Initialize Database

```bash
# Create tables
python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"

# Create admin user
python3 seed_database.py
```

### Step 4: Run

**Development:**
```bash
python3 app.py
```

**Production:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 app:app
```

---

## 🌐 Option 3: Deploy to Cloud (Heroku/Railway/Render)

### Heroku

```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
heroku config:set RESEND_API_KEY="re_your_key"
heroku config:set APP_URL="https://your-app-name.herokuapp.com"

# Deploy
git push heroku main

# Initialize database
heroku run python3 seed_database.py
```

### Railway

1. Connect your GitHub repo to Railway
2. Add PostgreSQL database service
3. Set environment variables in dashboard
4. Deploy automatically

### Render

1. Create new Web Service from repo
2. Add PostgreSQL database
3. Set environment variables
4. Deploy

---

## ✅ Verify Deployment

1. **Check Status**
   ```bash
   curl https://your-domain.com/status
   ```

2. **Login**
   - Go to: `https://your-domain.com/login`
   - Default admin: `admin@example.com`
   - Password: `admin123` (CHANGE THIS!)

3. **Test Upload**
   - Go to: `https://your-domain.com/browse`
   - Upload a test PDF
   - Verify OCR and translation work

---

## 🔧 Common Issues

### "DATABASE_URL not set"
```bash
# Check .env file exists and is loaded
cat .env | grep DATABASE_URL

# For production, export manually:
export DATABASE_URL="postgresql://..."
```

### "API key not found"
```bash
# Create API key file
echo "your-key" > .gcp_api_key

# Or use environment variable
export GOOGLE_CLOUD_API_KEY="your-key"
```

### "Port already in use"
```bash
# Find what's using port 5001
lsof -i :5001

# Kill the process or use different port
PORT=5002 python3 app.py
```

### Database connection fails
```bash
# Test connection
python3 -c "from scripts.database import engine; print(engine.connect())"

# Common issues:
# - Wrong credentials in DATABASE_URL
# - PostgreSQL not running
# - Firewall blocking connection
```

---

## 📚 More Help

- **Full Deployment Guide:** `DEPLOYMENT_CHECKLIST.md`
- **API Setup:** `API_KEYS_QUICK_START.md`
- **Test Integrations:** `python3 test_integrations.py`
- **Deployment Script:** `bash deploy.sh help`

---

## 🎉 You're Deployed!

Next steps:
1. Change default admin password
2. Create user accounts for your team
3. Upload documents and test the pipeline
4. Setup backups: `bash deploy.sh backup-db`
5. Monitor logs for any issues

**Need help?** Check the troubleshooting section in `DEPLOYMENT_CHECKLIST.md`



