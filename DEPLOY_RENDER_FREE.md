# 🆓 Deploy to Render (FREE)

## 100% Free Deployment Instructions

### What's Included in Free Tier
- ✅ 750 hours/month free compute
- ✅ SSL certificate (HTTPS)
- ✅ Auto-deploy from GitHub
- ✅ Use your existing Neon database (free)
- ⚠️ App sleeps after 15 min inactivity (wakes in ~30 sec)
- ⚠️ 512MB RAM limit

**Perfect for:** Testing, demos, low-traffic production

---

## 🚀 Deploy in 10 Minutes

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (free, no credit card required)

### Step 2: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account
3. Select repository: `gzentall/OCR-Translation-Pipeline`
4. Click **"Connect"**

### Step 3: Configure Service

Fill in these settings:

**Basic Settings:**
- **Name:** `postmark-ocr-pipeline`
- **Region:** Oregon (US West) or Frankfurt (Europe)
- **Branch:** `main`
- **Runtime:** Python 3

**Build Settings:**
- **Build Command:**
  ```bash
  pip install -r requirements.txt && pip install gunicorn
  ```

- **Start Command:**
  ```bash
  gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 300 app:app
  ```

**Instance Type:**
- Select: **Free** (512 MB RAM, sleeps after 15 min)

### Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add each of these (click "+ Add Environment Variable" for each):

```bash
FLASK_ENV=production
SECRET_KEY=0ak6Un1xcya+amPcwRLiwDOmsfl/LREIqWHb69Jh+WU=
RESEND_API_KEY=re_Dt8agkFh_PcEVr1Rx1rcbsVWMVCDhNRJh
GCP_VISION_API_KEY=AIzaSyChdvtdC7FuuBahNnR8qEqH6ZpYGrlFciU
GEOAPIFY_API_KEY=73701c273b8346369613a794dee93b88
DATABASE_URL=postgresql://neondb_owner:npg_qV16ZxKNvWOu@ep-icy-dawn-aful2k78.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require
APP_URL=https://postmark-ocr-pipeline.onrender.com
```

*(Note: Update APP_URL after deployment if Render gives you a different URL)*

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for initial build
3. Render will give you a URL like: `https://postmark-ocr-pipeline.onrender.com`

### Step 6: Initialize Database

Once deployed, use Render Shell:

1. In Render dashboard, click your service
2. Click **"Shell"** tab
3. Run these commands:

```bash
python3 << 'EOF'
from scripts.database import init_db, Base, engine
Base.metadata.create_all(engine)
print("✅ Database initialized")
EOF

python3 seed_database.py
```

### Step 7: Update APP_URL

If your URL is different than expected:

1. Go to **"Environment"** tab
2. Update `APP_URL` to your actual Render URL
3. Click **"Save Changes"** (triggers redeploy)

---

## ✅ Test Your Deployment

1. **Health Check:**
   ```bash
   curl https://postmark-ocr-pipeline.onrender.com/status
   ```

2. **Login:**
   - Visit: `https://postmark-ocr-pipeline.onrender.com/login`
   - Email: `gabe@zentall.com`
   - Password: `mRKPKAWrLn3#VFB#Rsu`
   - **Change password immediately!**

3. **Test Upload:**
   - Go to `/browse`
   - Upload a test PDF
   - Verify OCR works

---

## 🔄 Auto-Deploy

Every time you push to GitHub, Render will automatically redeploy!

```bash
git add .
git commit -m "Update application"
git push origin main
# Render deploys automatically
```

---

## ⚠️ Free Tier Limitations

### Sleep After Inactivity
- App sleeps after 15 minutes of no requests
- First request after sleep takes ~30 seconds to wake
- Subsequent requests are instant

**Workaround:** Use a free uptime monitor to ping your app every 10 minutes:
- [UptimeRobot](https://uptimerobot.com) (free)
- [Cron-job.org](https://cron-job.org) (free)

### RAM Limit (512MB)
- Should be fine for most OCR tasks
- If you hit limits, consider upgrading to $7/month plan (512MB → 2GB)

### Build Time
- ~5-10 minutes for first deploy
- ~2-5 minutes for updates

---

## 💰 Cost Comparison

| Platform | Free Tier | After Free |
|----------|-----------|------------|
| **Render** | ✅ Forever free | $7/month for more RAM |
| Railway | $5 trial credit | $5/month minimum |
| Heroku | ❌ No free tier | $7/month |
| Vercel | ✅ Free (but not for Flask) | N/A |
| Fly.io | ✅ Free (3 VMs) | Pay as you go |

---

## 🚀 Upgrade Options

If you outgrow the free tier:

**Render Starter - $7/month:**
- No sleep
- 512MB RAM
- Better performance

**Render Standard - $25/month:**
- 2GB RAM
- Faster CPU
- Better for high traffic

---

## 🐛 Troubleshooting

### Build fails
- Check build logs in Render dashboard
- Verify `requirements.txt` is valid
- Ensure `poppler-utils` is in system dependencies

### App crashes on startup
- Check runtime logs
- Verify all environment variables are set
- Test database connection

### OCR/Translation fails
- Verify `GCP_VISION_API_KEY` is set correctly
- Check Google Cloud Console for quota
- View logs for specific error messages

### First request very slow
- This is normal - app is waking from sleep
- Consider setting up UptimeRobot to keep it awake
- Or upgrade to paid plan for no-sleep

---

## 📈 Monitoring

Render provides:
- ✅ Real-time logs
- ✅ Metrics dashboard
- ✅ Email alerts for crashes
- ✅ Custom health checks

---

## ✨ You're Live on Render!

**Your app will be at:** `https://postmark-ocr-pipeline.onrender.com`

**Free. Forever. With SSL. Auto-deploys.**

Perfect for testing and low-traffic production use! 🎉

---

## 🆙 When to Upgrade

Consider paid tier when:
- Sleep delay becomes annoying
- You need faster response times
- Traffic increases significantly
- You hit 512MB RAM limit

Until then, enjoy the free tier! 😊


