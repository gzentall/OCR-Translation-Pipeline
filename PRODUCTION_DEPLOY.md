# 🚀 Production Deployment Guide

## Deployment Options

Choose the deployment method that best fits your needs:

### Option 1: Railway (Recommended - Easiest)
- ✅ Free tier available ($5/month after)
- ✅ Automatic deployments from GitHub
- ✅ Built-in PostgreSQL
- ✅ SSL certificates automatic
- ⏱️ Time: 10 minutes

### Option 2: Render
- ✅ Free tier available
- ✅ Auto-deploy from GitHub
- ✅ PostgreSQL included
- ✅ SSL automatic
- ⏱️ Time: 15 minutes

### Option 3: Heroku
- ✅ Well-documented
- ✅ Easy CLI deployment
- ✅ PostgreSQL add-on
- 💰 $7/month minimum
- ⏱️ Time: 10 minutes

### Option 4: VPS (DigitalOcean, Linode, etc.)
- ✅ Full control
- ✅ Best performance
- ⚠️ Requires server management
- 💰 $5-20/month
- ⏱️ Time: 30-60 minutes

---

## 🎯 Quick Deploy to Railway (Recommended)

### Step 1: Prepare Repository

```bash
cd /Users/gzentall/OCR-Translation-Pipeline

# Commit deployment files
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the Procfile

### Step 3: Add PostgreSQL Database

1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Copy the DATABASE_URL from the database service

### Step 4: Set Environment Variables

In Railway project settings → Variables, add:

```bash
SECRET_KEY=0ak6Un1xcya+amPcwRLiwDOmsfl/LREIqWHb69Jh+WU=
FLASK_ENV=production
APP_URL=https://your-app-name.railway.app
RESEND_API_KEY=re_Dt8agkFh_PcEVr1Rx1rcbsVWMVCDhNRJh
GCP_VISION_API_KEY=AIzaSyChdvtdC7FuuBahNnR8qEqH6ZpYGrlFciU
GEOAPIFY_API_KEY=73701c273b8346369613a794dee93b88
DATABASE_URL=(use the one from Railway PostgreSQL)
```

### Step 5: Initialize Database

In Railway CLI or web terminal:

```bash
railway run python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"
railway run python3 seed_database.py
```

### Step 6: Access Your App

Your app will be at: `https://your-app-name.railway.app`

---

## 🎯 Quick Deploy to Heroku

### Step 1: Install Heroku CLI

```bash
brew install heroku/brew/heroku  # macOS
# or visit: https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Create Heroku App

```bash
cd /Users/gzentall/OCR-Translation-Pipeline

heroku login
heroku create your-app-name
```

### Step 3: Add PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

### Step 4: Set Environment Variables

```bash
heroku config:set SECRET_KEY="0ak6Un1xcya+amPcwRLiwDOmsfl/LREIqWHb69Jh+WU="
heroku config:set FLASK_ENV=production
heroku config:set RESEND_API_KEY="re_Dt8agkFh_PcEVr1Rx1rcbsVWMVCDhNRJh"
heroku config:set GCP_VISION_API_KEY="AIzaSyChdvtdC7FuuBahNnR8qEqH6ZpYGrlFciU"
heroku config:set GEOAPIFY_API_KEY="73701c273b8346369613a794dee93b88"
```

### Step 5: Deploy

```bash
git push heroku main
```

### Step 6: Initialize Database

```bash
heroku run python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"
heroku run python3 seed_database.py
```

### Step 7: Access Your App

```bash
heroku open
```

---

## 🎯 Deploy to Render

### Step 1: Create Render Account

Go to [render.com](https://render.com) and sign up

### Step 2: Create Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name:** ocr-pipeline
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 300 app:app`

### Step 3: Add PostgreSQL Database

1. Click "New" → "PostgreSQL"
2. Copy the Internal Database URL

### Step 4: Set Environment Variables

In Web Service → Environment:

```bash
SECRET_KEY=0ak6Un1xcya+amPcwRLiwDOmsfl/LREIqWHb69Jh+WU=
FLASK_ENV=production
APP_URL=https://ocr-pipeline.onrender.com
RESEND_API_KEY=re_Dt8agkFh_PcEVr1Rx1rcbsVWMVCDhNRJh
GCP_VISION_API_KEY=AIzaSyChdvtdC7FuuBahNnR8qEqH6ZpYGrlFciU
GEOAPIFY_API_KEY=73701c273b8346369613a794dee93b88
DATABASE_URL=(paste the Internal Database URL)
```

### Step 5: Deploy

Render will automatically deploy when you push to GitHub

### Step 6: Initialize Database

Use Render Shell:

```bash
python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"
python3 seed_database.py
```

---

## 🎯 Deploy to VPS (DigitalOcean/Linode)

### Step 1: Create VPS

1. Create a droplet/instance with Ubuntu 22.04
2. SSH into your server

### Step 2: Setup Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx poppler-utils

# Install supervisor
sudo apt install supervisor
```

### Step 3: Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/yourusername/OCR-Translation-Pipeline.git
cd OCR-Translation-Pipeline
sudo chown -R $USER:$USER .
```

### Step 4: Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Step 5: Configure PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE ocr_translation;
CREATE USER ocruser WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE ocr_translation TO ocruser;
\q
```

### Step 6: Configure Environment

```bash
cp .env.production .env
nano .env
# Update DATABASE_URL to: postgresql://ocruser:your-secure-password@localhost/ocr_translation
# Update APP_URL to your domain
```

### Step 7: Initialize Database

```bash
python3 -c "from scripts.database import init_db, Base, engine; Base.metadata.create_all(engine)"
python3 seed_database.py
```

### Step 8: Configure Supervisor

```bash
sudo cp supervisor.conf.example /etc/supervisor/conf.d/ocr-pipeline.conf
sudo nano /etc/supervisor/conf.d/ocr-pipeline.conf
# Update paths as needed

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ocr-pipeline
```

### Step 9: Configure Nginx

```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/ocr-pipeline
sudo nano /etc/nginx/sites-available/ocr-pipeline
# Update domain name

sudo ln -s /etc/nginx/sites-available/ocr-pipeline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 10: Setup SSL

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📋 Post-Deployment Checklist

After deploying to any platform:

### 1. Test the Application

```bash
# Check status
curl https://your-domain.com/status

# Expected response with api_key_exists: true
```

### 2. Login and Change Password

1. Go to: `https://your-domain.com/login`
2. Login with: `gabe@zentall.com` / `mRKPKAWrLn3#VFB#Rsu`
3. **Change password immediately!**

### 3. Test Upload

1. Go to: `https://your-domain.com/browse`
2. Upload a test PDF
3. Verify OCR and translation work

### 4. Create User Accounts

1. Go to: `https://your-domain.com/users-page`
2. Add team members
3. Test invitation emails

### 5. Monitor Logs

**Railway:**
```bash
railway logs
```

**Heroku:**
```bash
heroku logs --tail
```

**Render:**
Check logs in dashboard

**VPS:**
```bash
sudo supervisorctl tail -f ocr-pipeline stdout
```

### 6. Setup Monitoring

Consider adding:
- [Sentry](https://sentry.io) for error tracking
- [UptimeRobot](https://uptimerobot.com) for uptime monitoring
- Database backups (most platforms have automatic backups)

---

## 🔒 Security Checklist

- [ ] Changed default admin password
- [ ] HTTPS enabled (SSL certificate)
- [ ] SECRET_KEY is secure (64+ characters)
- [ ] FLASK_ENV set to 'production'
- [ ] Database credentials secured
- [ ] API keys restricted in Google Cloud Console
- [ ] Email sender verified in Resend

---

## 🐛 Troubleshooting

### Application won't start
```bash
# Check logs for errors
# Verify all environment variables are set
# Test database connection
```

### Database connection fails
```bash
# Check DATABASE_URL format
# Verify database exists
# Test connection with psql
```

### OCR/Translation fails
```bash
# Verify GCP_VISION_API_KEY is set
# Check Google Cloud Console for quota
# Test API: python3 test_integrations.py
```

### Email not sending
```bash
# Verify RESEND_API_KEY is set
# Check sender email is verified in Resend
# Test: python3 -c "from scripts.email_service import send_user_invite; print(send_user_invite('test@example.com', 'Test', 'token123'))"
```

---

## 📞 Need Help?

- Check logs first
- Review environment variables
- Test API connections: `python3 test_integrations.py`
- Check deployment platform docs
- Review `DEPLOYMENT_CHECKLIST.md` for detailed troubleshooting

---

## ✨ You're Live!

Once deployed:

1. Access your app at your production URL
2. Share with your team
3. Start processing documents
4. Monitor usage and costs

**Congratulations on your deployment! 🎉**


