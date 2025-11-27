# Project Structure

## 📁 Primary Application

**`app.py`** - Main Flask Application ✅
- Material Design 3 web interface
- PDF upload and processing
- OCR via Google Vision API
- Translation via Google Translate API
- Document management with local JSON storage
- People tracking and extraction
- No authentication required (simple and clean)

**Access:** http://localhost:5001/browse

---

## 📂 Directory Structure

```
OCR-Translation-Pipeline/
├── app.py                      # Main Flask application ⭐
├── letters/
│   ├── inbox/                  # Upload PDFs here
│   ├── work/                   # Temporary processing files
│   └── out/en/                 # Translated output files
├── scripts/
│   ├── run_vision_ocr.sh       # OCR processing script
│   ├── translate_google.py     # Translation script
│   ├── local_storage.py        # JSON-based storage
│   └── fallback_ai_processor.py # Rule-based AI processing
├── templates/                  # Flask HTML templates (Material Design 3)
├── static/
│   └── css/tokens.css          # Material Design 3 tokens
├── ocr_storage/                # Document storage (JSON)
├── _archived/                  # Alternative implementations (see below)
├── README.md                   # Main documentation
├── API_KEYS_QUICK_START.md     # API setup guide
└── .gcp_api_key                # Google Cloud API key (required)
```

---

## 📦 Archived Applications

Located in `_archived/` directory:

### Node.js Applications
- **`ocr-auth/`** - Next.js authentication frontend (Tailwind CSS)
- **`letters-mcp/`** - MCP server for document management

### Alternative Flask Apps
- **`app_with_auth.py`** - Flask with JWT authentication
- **`app_simple_auth.py`** - Flask with session-based auth
- **`flask_api.py`** - Flask API for Next.js integration

### Documentation
- **`HYBRID_SETUP.md`** - Hybrid architecture setup guide

**See:** `_archived/README.md` for details on archived applications.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt
brew install poppler

# 2. Set up API key
echo "YOUR_GOOGLE_CLOUD_API_KEY" > .gcp_api_key

# 3. Start the app
python3 app.py

# 4. Open browser
open http://localhost:5001/browse
```

---

## 🎯 Why This Structure?

**Simplified:** The main `app.py` provides everything you need:
- ✅ Single file to run
- ✅ No authentication complexity
- ✅ Beautiful Material Design 3 UI
- ✅ No Node.js dependencies
- ✅ Easy to deploy and maintain

**Archived:** Alternative implementations are preserved but separated to avoid confusion.

---

## 📚 Documentation

- **`README.md`** - Main project documentation
- **`API_KEYS_QUICK_START.md`** - API setup instructions
- **`SETUP_APIS.md`** - Detailed API configuration guide
- **`_archived/README.md`** - Information about archived apps

---

**Last Updated:** November 11, 2025
