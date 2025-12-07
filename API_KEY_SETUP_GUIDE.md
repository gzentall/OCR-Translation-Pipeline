# OpenAI API Key Setup Guide

## The Issue

Your current API key starts with `sk-proj-`, which is a **project key**. These keys are tied to a specific OpenAI project and may not work with all API endpoints or may require additional project configuration.

## Solution: Create a Standard API Key

### Option 1: Create a Non-Project Key (If Available)

1. Go to https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. In the dialog:
   - **Owned by:** Select "You" ✅ (you have this correct)
   - **Name:** Enter a name like "Postmark Pipeline Key" ✅ (you have this correct)
   - **Project:** Try selecting "No project" or leaving it blank/unselected
   - **Permissions:** Select "All" ✅ (you have this correct)
4. Click "Create secret key"
5. **IMPORTANT:** Copy the key immediately - it starts with `sk-` but NOT `sk-proj-`

### Option 2: Fix Project Key Configuration

If you must use a project key, ensure:

1. **Project has API Access Enabled:**
   - Go to https://platform.openai.com/org/projects
   - Select your project (or "Default project")
   - Ensure "API access" is enabled
   - Check that billing is set up for the project

2. **Project Has Sufficient Credits:**
   - Go to https://platform.openai.com/account/billing
   - Ensure the project has credits or a payment method

3. **Key Permissions:**
   - The key should have "All" permissions (which you have ✅)

### Option 3: Use Organization-Level Key

If you're part of an organization:
1. Go to https://platform.openai.com/account/api-keys
2. Look for organization-level key creation (may be in a different section)
3. Create a key that's not tied to a specific project

## After Creating the Key

1. **Update your `.openai_api_key` file:**
   ```bash
   # Edit the file
   nano .openai_api_key
   # Paste the new key (should start with sk- but not sk-proj-)
   # Save and exit
   ```

2. **Or set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-your-new-key-here"
   ```

3. **Verify the key format:**
   ```bash
   head -c 10 .openai_api_key
   # Should show: sk- (not sk-proj-)
   ```

4. **Restart your server:**
   ```bash
   # If running locally, restart Flask
   # If running in production, restart via your hosting platform
   ```

5. **Test the key:**
   ```bash
   python3 -c "
   from scripts.envelope_extractor import EnvelopeExtractor
   extractor = EnvelopeExtractor()
   print('✅ Key is valid!' if extractor.openai_client else '❌ Key failed')
   "
   ```

## What to Look For

**Good key format:**
- Starts with `sk-` (not `sk-proj-`)
- About 50+ characters long
- No spaces or newlines

**Bad key format:**
- Starts with `sk-proj-` (project key - may not work)
- Has spaces or newlines
- Less than 20 characters

## Troubleshooting

If you still get 401 errors after creating a new key:

1. **Check key format:**
   ```bash
   cat .openai_api_key | head -c 20
   ```

2. **Check for whitespace:**
   ```bash
   cat .openai_api_key | wc -c
   # Should be around 50-60 characters, not more
   ```

3. **Verify key is being read:**
   ```bash
   python3 -c "
   from pathlib import Path
   key = Path('.openai_api_key').read_text().strip()
   print(f'Key length: {len(key)}')
   print(f'Key starts with: {key[:10]}')
   "
   ```

4. **Check server logs after restart:**
   ```bash
   tail -f server.log | grep -E "Metadata extraction|API key|authentication"
   ```

## Current Status

Based on your logs, the `sk-proj-...` key is being rejected by OpenAI's API with:
```
Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-proj-...', 'code': 'invalid_api_key'}}
```

This confirms that project keys are not working for your use case. You need a standard API key that starts with `sk-` but not `sk-proj-`.



