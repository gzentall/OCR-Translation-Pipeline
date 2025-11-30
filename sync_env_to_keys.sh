#!/bin/bash
# =========================================
# Sync .env file to individual API key files
# =========================================

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🔄 Syncing .env to API key files..."

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Source the .env file
set -a
source .env 2>/dev/null || true
set +a

create_key_file() {
    local var_name=$1
    local file_name=$2
    local var_value="${!var_name}"
    
    if [ -n "$var_value" ]; then
        echo "$var_value" > "$file_name"
        chmod 600 "$file_name"
        echo "✓ Created $file_name from $var_name"
        return 0
    fi
    return 1
}

echo ""

# Google Cloud API - try both variable names
if ! create_key_file "GOOGLE_CLOUD_API_KEY" ".gcp_api_key"; then
    if ! create_key_file "GCP_VISION_API_KEY" ".gcp_api_key"; then
        echo "⚠️  Skipped .gcp_api_key (no Google Cloud key found)"
    fi
fi

# OpenAI API
if ! create_key_file "OPENAI_API_KEY" ".openai_api_key"; then
    echo "⚠️  Skipped .openai_api_key (OPENAI_API_KEY is empty)"
fi

# Notion API
if ! create_key_file "NOTION_API_KEY" ".notion_api_key"; then
    echo "○  Skipped .notion_api_key (optional, not set)"
fi

echo ""
echo "✅ Sync complete!"
echo ""
echo "Next steps:"
echo "  1. Test your setup: python3 test_integrations.py"
echo "  2. Start Flask: python3 app.py"
echo "  3. Start Next.js: cd ocr-auth && npm run dev"






