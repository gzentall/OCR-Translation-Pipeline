#!/usr/bin/env bash
# Build script for Render deployment
# Note: Render free tier doesn't support apt-get, so we skip system packages

set -o errexit

echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python dependencies installed"

# Check if poppler is available (Render may have it pre-installed)
if command -v pdftoppm &> /dev/null; then
    echo "✅ Poppler (pdftoppm) is available"
else
    echo "⚠️  Poppler not found - PDF processing may require alternative approach"
fi

echo "🎉 Build complete!"

