# Fixing Project API Key Issues

Since OpenAI now requires all API keys to be associated with a project, the `sk-proj-...` key format is correct. The 401 error is likely due to **project configuration issues**, not the key format itself.

## Steps to Fix

### 1. Verify Project Has Billing Enabled

1. Go to https://platform.openai.com/org/projects
2. Click on "Default project" (or your project)
3. Check the **Billing** section:
   - Ensure there's a payment method attached
   - Verify there are credits available
   - Check that API usage is enabled for the project

### 2. Check Project API Access

1. In your project settings, look for:
   - **API Access** toggle - should be ON
   - **Usage Limits** - ensure they're not set to $0
   - **Model Access** - verify GPT-3.5-turbo and GPT-4o are enabled

### 3. Verify Key Permissions

When creating the key, ensure:
- **Permissions:** "All" ✅ (you have this)
- **Project:** "Default project" ✅ (this is fine)

### 4. Test the Key Directly

After creating the key, test it immediately:

```bash
# Save the key
echo "sk-proj-YOUR-KEY-HERE" > .openai_api_key

# Test it
python3 -c "
import openai
from pathlib import Path

api_key = Path('.openai_api_key').read_text().strip()
client = openai.OpenAI(api_key=api_key)

try:
    # Test with a simple API call
    response = client.models.list()
    print('✅ Key works!')
    print(f'Found {len(list(response))} models')
except openai.AuthenticationError as e:
    print(f'❌ Authentication failed: {e}')
    print('Check:')
    print('  1. Project has billing enabled')
    print('  2. Project has API access enabled')
    print('  3. Key permissions are set to "All"')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### 5. Common Issues and Solutions

#### Issue: "Incorrect API key provided"
**Solution:**
- Verify the project has billing/credits
- Check that API access is enabled for the project
- Ensure the key wasn't revoked

#### Issue: "Project not found" or "Invalid project"
**Solution:**
- Make sure you're using the key in the same organization where it was created
- Verify the project still exists

#### Issue: "Insufficient credits"
**Solution:**
- Add payment method to the project
- Add credits to the project
- Check usage limits aren't set too low

### 6. Alternative: Create a New Project

If "Default project" isn't working:

1. Go to https://platform.openai.com/org/projects
2. Click "+ Create project"
3. Name it (e.g., "Postmark Pipeline")
4. Set up billing for this project
5. Create a new API key associated with this project
6. Use this new key

### 7. Check Organization Settings

If you're part of an organization:

1. Go to https://platform.openai.com/org/settings
2. Check **API Access** settings
3. Verify project-level API access is enabled
4. Check if there are any organization-level restrictions

## After Fixing

1. **Update your key file:**
   ```bash
   nano .openai_api_key
   # Paste the new key
   ```

2. **Restart your server**

3. **Check logs:**
   ```bash
   tail -f server.log | grep -E "Metadata extraction|authentication"
   ```

4. **Look for success:**
   ```
   [DEBUG] Metadata extracted: sender=..., recipient=...
   ```

## What to Check in Logs

After restarting, look for:

**Success:**
```
[DEBUG] Metadata extracted: sender=Robert Zentall, recipient=Betty Zentall
```

**Still failing:**
```
❌ Metadata extraction authentication error: Error code: 401
```

If still failing, check:
- Project billing status
- Project API access settings
- Key permissions (should be "All")
- Organization-level restrictions



