# Metadata Extraction Diagnosis Guide

## Where to Find Logs

### Local Development (localhost:5001)
Logs are written to **stdout/stderr** (the terminal where Flask is running).

**To view logs:**
```bash
# If running Flask directly
# Logs appear in the terminal where you ran: python app.py

# If running with gunicorn
tail -f gunicorn.log

# If running in a screen/tmux session
# Attach to the session and view the terminal output
```

### Production (Render/Railway/etc.)
Logs are typically available in your hosting platform's dashboard:
- **Render**: Dashboard → Your Service → Logs tab
- **Railway**: Dashboard → Your Service → Deployments → View Logs
- **Supervisor**: `sudo tail -f /var/log/ocr-pipeline-error.log`

## Key Log Messages to Look For

### 1. Initialization Phase

**Look for:**
```
⚠️  EnvelopeExtractor: Could not initialize OpenAI client: ...
⚠️  Metadata extraction will be disabled
```

**What it means:** The OpenAI API key is missing or invalid during initialization.

**How to fix:**
- Check that `.openai_api_key` file exists and contains a valid key
- Check that `OPENAI_API_KEY` environment variable is set
- Verify the API key format (should start with `sk-` and be at least 20 characters)
- Check for whitespace/newlines in the API key file

---

### 2. Metadata Extraction Start

**Look for:**
```
[DEBUG] Extracting metadata...
```

**What it means:** Metadata extraction has started. If you don't see this, the extraction step isn't being reached.

---

### 3. Successful Extraction

**Look for:**
```
[DEBUG] Metadata extracted: sender=..., recipient=...
```

**What it means:** Metadata was successfully extracted. Check the values to see if they're correct.

**Example:**
```
[DEBUG] Metadata extracted: sender=Robert Zentall, recipient=Betty Zentall
```

---

### 4. Client Not Available

**Look for:**
```
⚠️  OpenAI client not available, skipping metadata extraction
```

**What it means:** The OpenAI client wasn't initialized (likely due to invalid API key).

**How to fix:**
- Check the initialization logs (see #1 above)
- Verify API key is valid
- Restart the server after fixing the API key

---

### 5. Authentication Error

**Look for:**
```
❌ Metadata extraction authentication error: ...
```

**What it means:** The API key is invalid or has been revoked.

**Common error messages:**
- `Incorrect API key provided`
- `Invalid API key`
- `API key not found`

**How to fix:**
- Get a new API key from https://platform.openai.com/account/api-keys
- Update `.openai_api_key` file or `OPENAI_API_KEY` environment variable
- Restart the server

---

### 6. API Error

**Look for:**
```
❌ Metadata extraction API error: ...
```

**What it means:** The API call failed for reasons other than authentication (rate limit, service unavailable, etc.).

**Common causes:**
- Rate limit exceeded
- Service temporarily unavailable
- Invalid request format

**How to fix:**
- Wait and retry (if rate limited)
- Check OpenAI status page
- Verify the API key has sufficient credits

---

### 7. General Error

**Look for:**
```
[WARNING] Metadata extraction failed: ...
```

**What it means:** An unexpected error occurred during extraction.

**What to check:**
- Look for the full traceback in the logs
- Check if the error is related to JSON parsing
- Verify the OCR text is valid

---

## Complete Log Flow Example

### Successful Extraction:
```
[DEBUG] Extracting metadata...
[DEBUG] Metadata extracted: sender=Robert Zentall, recipient=Betty Zentall
```

### Failed Extraction (Invalid API Key):
```
⚠️  EnvelopeExtractor: Could not initialize OpenAI client: Invalid API key format
⚠️  Metadata extraction will be disabled
[DEBUG] Extracting metadata...
⚠️  OpenAI client not available, skipping metadata extraction
[DEBUG] Metadata extracted: sender=Unknown, recipient=Unknown
```

### Failed Extraction (API Error):
```
[DEBUG] Extracting metadata...
❌ Metadata extraction authentication error: Incorrect API key provided: sk-proj-...
[DEBUG] Metadata extracted: sender=Unknown, recipient=Unknown
```

---

## Quick Diagnostic Commands

### Check API Key File:
```bash
cat .openai_api_key | head -c 20
# Should show: sk-...
```

### Check Environment Variable:
```bash
echo $OPENAI_API_KEY | head -c 20
# Should show: sk-...
```

### Test EnvelopeExtractor Initialization:
```bash
cd /Users/gzentall/OCR-Translation-Pipeline
python3 -c "
from scripts.envelope_extractor import EnvelopeExtractor
try:
    extractor = EnvelopeExtractor()
    print('✅ EnvelopeExtractor initialized successfully')
    print(f'OpenAI client available: {extractor.openai_client is not None}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"
```

---

## Most Common Issues

1. **API Key Format Issue**
   - **Symptom:** `Invalid API key format` or `API key appears too short`
   - **Fix:** Check for whitespace/newlines, ensure key starts with `sk-`

2. **API Key Not Found**
   - **Symptom:** `OPENAI_API_KEY not found`
   - **Fix:** Create `.openai_api_key` file or set environment variable

3. **Invalid/Revoked Key**
   - **Symptom:** `Incorrect API key provided` or `Authentication error`
   - **Fix:** Get a new API key from OpenAI dashboard

4. **Rate Limiting**
   - **Symptom:** `API error` with rate limit message
   - **Fix:** Wait and retry, or upgrade OpenAI plan

---

## Next Steps After Diagnosis

1. **If API key is invalid:**
   - Get a new key from https://platform.openai.com/account/api-keys
   - Update the key file or environment variable
   - Restart the server

2. **If extraction is working but values are wrong:**
   - Check the OCR text quality
   - Verify the document text contains sender/recipient information
   - Consider improving the prompt in `scripts/envelope_extractor.py`

3. **If extraction is completely failing:**
   - Check the full traceback in logs
   - Verify the OpenAI API is accessible from your server
   - Test with a simple API call to verify connectivity



