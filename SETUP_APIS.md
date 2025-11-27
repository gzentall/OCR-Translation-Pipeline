# API Setup Guide

This guide will walk you through setting up all the API keys needed for the OCR Translation Pipeline.

## 📋 Prerequisites

You'll need accounts with the following services:
- Google Cloud Platform (for OCR and Translation)
- OpenAI (for AI processing)
- Resend (for email - already configured)

---

## 1. Google Cloud API Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name your project (e.g., "OCR Translation Pipeline")
4. Click **"Create"**

### Step 2: Enable Required APIs

1. In the Google Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for and enable these APIs:
   - **Cloud Vision API** (for OCR)
   - **Cloud Translation API** (for translation)

### Step 3: Create an API Key

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"API key"**
3. Copy the API key that appears
4. (Optional but recommended) Click **"Restrict Key"** and:
   - Select **"API restrictions"**
   - Choose **"Restrict key"**
   - Select only: **Cloud Vision API** and **Cloud Translation API**
   - Click **"Save"**

### Step 4: Save Your API Key

Create a file named `.gcp_api_key` in the project root:

```bash
echo "your-google-cloud-api-key-here" > .gcp_api_key
```

**Important:** This file is in `.gitignore` and will NOT be committed to git.

---

## 2. OpenAI API Setup

### Step 1: Create an OpenAI Account

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Add billing information (required for API access)

### Step 2: Create an API Key

1. Go to [API Keys](https://platform.openai.com/api-keys)
2. Click **"Create new secret key"**
3. Give it a name (e.g., "OCR Pipeline")
4. Copy the key (you won't be able to see it again!)

### Step 3: Save Your API Key

Create a file named `.openai_api_key` in the project root:

```bash
echo "sk-your-openai-api-key-here" > .openai_api_key
```

**Or** set it as an environment variable:

```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

---

## 3. Notion API Setup (Optional)

Only needed if you want to sync documents to Notion.

### Step 1: Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"New integration"**
3. Name it (e.g., "OCR Pipeline")
4. Select your workspace
5. Click **"Submit"**

### Step 2: Get the Integration Token

1. Copy the **"Internal Integration Token"** (starts with `secret_`)

### Step 3: Share Database with Integration

1. In Notion, create or open the database you want to use
2. Click **"Share"** in the top right
3. Invite your integration
4. Click **"Invite"**

### Step 4: Save Your API Key

```bash
echo "secret_your-notion-token-here" > .notion_api_key
```

---

## 4. Quick Setup Script

Run this automated setup script:

```bash
python3 setup_api_keys.py
```

This will:
- ✅ Check which API keys are configured
- ✅ Prompt you to enter missing keys
- ✅ Create the necessary files
- ✅ Test API connectivity

---

## 5. Verify Setup

Test that all APIs are working:

```bash
python3 test_integrations.py
```

You should see:
- ✅ Google Cloud Vision API: Working
- ✅ Google Cloud Translation API: Working
- ✅ OpenAI Integration: Working
- ✅ Notion Integration: Working (if configured)

---

## 📁 File Structure

After setup, you should have:

```
OCR-Translation-Pipeline/
├── .gcp_api_key              # Google Cloud API key (REQUIRED)
├── .openai_api_key           # OpenAI API key (REQUIRED)
├── .notion_api_key           # Notion API key (optional)
├── ocr-auth/.env             # Next.js environment variables (already set)
└── .env                      # Flask environment variables (optional)
```

---

## 🔒 Security Notes

- **Never commit API keys to git** - All key files are in `.gitignore`
- **Restrict API keys** - Use API restrictions in Google Cloud Console
- **Rotate keys regularly** - Change keys periodically
- **Monitor usage** - Check your API usage dashboards
- **Set spending limits** - Configure billing alerts

---

## 💰 Costs

### Google Cloud
- **Vision API**: ~$1.50 per 1,000 pages (first 1,000/month free)
- **Translation API**: ~$20 per 1M characters

### OpenAI
- **GPT-4o**: ~$5 per 1M input tokens
- **GPT-4o-mini**: ~$0.15 per 1M input tokens (fallback)

### Resend
- **Free tier**: 100 emails/day, 3,000/month

---

## 🆘 Troubleshooting

### "API key not found" error
- Check that the key file exists in the project root
- Ensure there are no extra spaces or newlines
- Verify the file name is correct (e.g., `.gcp_api_key`)

### "Permission denied" error
- Enable the required APIs in Google Cloud Console
- Wait a few minutes for API enablement to propagate
- Check API restrictions on your key

### "Invalid authentication credentials" error
- Verify the API key is correct
- Check if the key has been restricted
- Try creating a new key

### "Quota exceeded" error
- Check your billing account is active
- Review usage in API dashboard
- Consider upgrading your plan

---

## 📞 Support

If you need help:
1. Check the [README.md](README.md) for general setup
2. Review [HYBRID_SETUP.md](HYBRID_SETUP.md) for deployment
3. Run `python3 test_integrations.py` to diagnose issues

---

## ✅ Next Steps

After setting up your API keys:

1. **Start the servers**:
   ```bash
   # Terminal 1: Flask API
   python3 app.py
   
   # Terminal 2: Next.js frontend
   cd ocr-auth && npm run dev
   ```

2. **Upload a test document** at `http://localhost:3000`

3. **View processed documents** at `http://localhost:5001/browse`

Enjoy your OCR pipeline! 🚀






