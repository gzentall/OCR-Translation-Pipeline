#!/usr/bin/env bash

# This script performs OCR on a PDF using the Google Vision API.
# It accepts a path to a PDF file (relative to the project root) and
# writes a text file containing the concatenated OCR results for each page.
#
# Prerequisites:
#   * Create a Google Cloud project.
#   * Enable the Vision API.
#   * Generate an API key and store it in `.gcp_api_key` at the root of this project.
#   * Install Docker and ensure the `ghcr.io/johnleetw/poppler:latest` image can be pulled.
#
# Usage:
#   bash run_vision_ocr.sh letters/inbox/your_document.pdf
#
# The resulting text file will be written to `letters/work/<pdf-name>.vision.txt`.

set -euo pipefail

INPUT_PDF="${1:?Usage: run_vision_ocr.sh <letters/inbox/your_document.pdf>}"

# Resolve the project root. This script lives in vision_project/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure the input file exists.
if [[ ! -f "$PROJECT_ROOT/$INPUT_PDF" ]]; then
    echo "Input file $INPUT_PDF does not exist under $PROJECT_ROOT" >&2
    exit 1
fi

# Read the Vision API key from the .gcp_api_key file. The file should contain just the key on one line.
API_KEY_FILE="$PROJECT_ROOT/.gcp_api_key"
if [[ ! -f "$API_KEY_FILE" ]]; then
    echo "Missing $API_KEY_FILE. Please place your Google Vision API key in this file." >&2
    exit 1
fi
GCP_VISION_API_KEY="$(<"$API_KEY_FILE")"
if [[ -z "$GCP_VISION_API_KEY" ]]; then
    echo "API key is empty in $API_KEY_FILE" >&2
    exit 1
fi

# Derive output filenames.
PDF_BASENAME="$(basename "$INPUT_PDF")"
PDF_STEM="${PDF_BASENAME%.pdf}"

WORK_DIR="$PROJECT_ROOT/letters/work"
mkdir -p "$WORK_DIR"

TEXT_OUT="$WORK_DIR/${PDF_STEM}.vision.txt"
: > "$TEXT_OUT"  # truncate output file

# Temporary directory for image conversion. Use a subdir in work to avoid clobbering other files.
TMP_DIR="$WORK_DIR/${PDF_STEM}_vision_tmp"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

echo "[run_vision_ocr] Converting PDF to PNG pages…"

# Use local poppler to convert PDF pages to PNGs at 300 DPI
# Check if pdftoppm is available locally
if command -v pdftoppm >/dev/null 2>&1; then
    echo "[run_vision_ocr] Using local pdftoppm..."
    pdftoppm -r 300 -png "$PROJECT_ROOT/$INPUT_PDF" "$TMP_DIR/tmp"
else
    echo "[run_vision_ocr] pdftoppm not found locally, trying Docker..."
    # Fallback to Docker if local pdftoppm is not available
    docker run --rm -v "$PROJECT_ROOT/letters":/data ghcr.io/johnleetw/poppler:latest \
        pdftoppm -r 300 -png "/data/${INPUT_PDF#letters/}" "/data/${WORK_DIR#${PROJECT_ROOT}/}/${PDF_STEM}_vision_tmp/tmp"
fi

echo "[run_vision_ocr] Performing OCR via Google Vision API…"

# Loop over the generated PNG files in numerical order.
for page_img in "$TMP_DIR"/*.png; do
    # Use Python to handle the entire OCR process in one go to avoid shell variable issues
    page_text=$(python3 - <<PY
import base64
import json
import requests
import sys

# Read and encode the image
with open("$page_img", "rb") as f:
    img_data = f.read()
    img_b64 = base64.b64encode(img_data).decode('utf-8')

# Prepare the request
url = "https://vision.googleapis.com/v1/images:annotate?key=$GCP_VISION_API_KEY"
data = {
    "requests": [{
        "image": {"content": img_b64},
        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
    }]
}

# Make the request and parse response in one go
try:
    response = requests.post(url, json=data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        resp = result.get('responses', [{}])[0]
        if 'error' in resp:
            print(f"API Error: {resp['error']}")
        else:
            full = resp.get('fullTextAnnotation', {})
            text = full.get('text', '')
            print(text)
    else:
        print(f"API request failed with status {response.status_code}: {response.text}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
except Exception as e:
    print(f"Error during OCR: {e}")
PY
)
    # Append the extracted text to the output file, followed by a blank line between pages.
    printf "%s\n\n" "$page_text" >> "$TEXT_OUT"
    echo "[run_vision_ocr] Processed $(basename "$page_img")"
done

# Cleanup temporary images.
rm -rf "$TMP_DIR"

echo "[run_vision_ocr] OCR complete. Output saved to $TEXT_OUT"