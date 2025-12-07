# Testing Your API Key

Since billing is enabled and the project is operational, let's verify everything is working.

## Current Status

From the logs:
- ✅ Documents are being saved successfully
- ⚠️ Metadata extraction is returning "Unknown" values (failing gracefully)
- ⚠️ No API key found in `.openai_api_key` file or environment variable

## Steps to Verify

### 1. Check Where Your Server Reads the API Key

The server looks for the key in this order:
1. `OPENAI_API_KEY` environment variable
2. `.openai_api_key` file in the project root

### 2. Set Up the API Key

**Option A: Environment Variable (Recommended for Production)**
```bash
# For local development
export OPENAI_API_KEY="sk-your-key-here"

# For production (Render/Railway/etc.)
# Set it in your hosting platform's environment variables
```

**Option B: File (Easier for Local Development)**
```bash
# Create the file
echo "sk-your-key-here" > .openai_api_key

# Make sure it's readable
chmod 600 .openai_api_key
```

### 3. Test the Key

```bash
python3 -c "
import openai
from pathlib import Path
import os

# Try to get key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    key_file = Path('.openai_api_key')
    if key_file.exists():
        api_key = key_file.read_text().strip()

if api_key:
    print(f'Testing key: {api_key[:15]}...')
    client = openai.OpenAI(api_key=api_key)
    try:
        models = list(client.models.list())
        print(f'✅ Key works! Found {len(models)} models')
    except Exception as e:
        print(f'❌ Error: {e}')
else:
    print('❌ No API key found')
"
```

### 4. Test Metadata Extraction

After setting up the key, try uploading a new document and check the logs:

```bash
# Watch logs in real-time
tail -f server.log | grep -E "Metadata extraction|Metadata extracted"
```

**Look for:**
- ✅ Success: `[DEBUG] Metadata extracted: sender=Robert Zentall, recipient=Betty Zentall`
- ❌ Still failing: `[DEBUG] Metadata extracted: sender=Unknown, recipient=Unknown`

### 5. If Still Getting "Unknown" Values

Check the full error:
```bash
tail -100 server.log | grep -A 5 "Metadata extraction"
```

Common issues:
- **401 error**: Key is invalid or project billing isn't properly configured
- **No error but Unknown**: Key might not be accessible to the server process
- **Client not available**: Key file exists but can't be read

## What Fixed It

Based on your setup:
- ✅ Billing is enabled ($8.84 credit balance)
- ✅ Default project is operational
- ✅ Existing key has "All" permissions

The remaining issue is likely:
- The API key needs to be configured where your server is running
- Or the server needs to be restarted after setting the key

## Next Steps

1. **Set the API key** using one of the methods above
2. **Restart your server** (if running locally or in production)
3. **Upload a test document** and check the logs
4. **Verify metadata extraction** shows actual names instead of "Unknown"



