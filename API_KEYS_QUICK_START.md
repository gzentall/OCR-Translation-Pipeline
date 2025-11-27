# 🔑 API Keys Quick Start

## You Need 2 Required API Keys:

### 1️⃣ Google Cloud API Key (REQUIRED)
**Used for:** OCR (Vision API) + Translation

**Get it:**
1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable these APIs:
   - Cloud Vision API
   - Cloud Translation API
4. Go to: **APIs & Services → Credentials**
5. Click: **Create credentials → API key**
6. Copy the key

**Save it:**
```bash
echo "YOUR_GOOGLE_API_KEY_HERE" > .gcp_api_key
```

---

### 2️⃣ OpenAI API Key (REQUIRED)
**Used for:** AI document processing

**Get it:**
1. Go to: https://platform.openai.com/api-keys
2. Sign in (you'll need billing set up)
3. Click: **Create new secret key**
4. Name it: "OCR Pipeline"
5. Copy the key (starts with `sk-`)

**Save it:**
```bash
echo "sk-YOUR_OPENAI_KEY_HERE" > .openai_api_key
```

---

### 3️⃣ Notion API (OPTIONAL)
Only if you want Notion integration.

**Get it:**
1. Go to: https://www.notion.so/my-integrations
2. Click: **New integration**
3. Name it, select workspace
4. Copy the token (starts with `secret_`)

**Save it:**
```bash
echo "secret_YOUR_NOTION_TOKEN" > .notion_api_key
```

---

## ✅ Verify Setup

Run the automated setup helper:
```bash
python3 setup_api_keys.py
```

Or check manually:
```bash
ls -la .gcp_api_key .openai_api_key
```

Test API connections:
```bash
python3 test_integrations.py
```

---

## 🚀 Start Using the App

Once your keys are set up:

```bash
# Terminal 1: Flask backend
python3 app.py

# Terminal 2: Next.js frontend
cd ocr-auth && npm run dev
```

Then visit:
- **Main App (Material M3)**: http://localhost:5001/browse
- **Auth System**: http://localhost:3000

---

## 💡 Tips

- **Security**: These files are in `.gitignore` - never commit them!
- **Costs**: Google Cloud has free tier; OpenAI charges per use
- **Testing**: Start with small documents to test
- **Help**: Check `SETUP_APIS.md` for detailed instructions






