#!/usr/bin/env bash

# This helper script loops over all PDF files in letters/inbox and runs the
# Vision OCR pipeline on each of them.  It delegates to run_vision_ocr.sh for
# the actual OCR.  Use this when you have multiple documents and want to
# process them in one command.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INBOX_DIR="$PROJECT_ROOT/letters/inbox"
if [[ ! -d "$INBOX_DIR" ]]; then
    echo "Expected inbox directory at $INBOX_DIR not found" >&2
    exit 1
fi

shopt -s nullglob
pdf_files=("$INBOX_DIR"/*.pdf)
if [[ ${#pdf_files[@]} -eq 0 ]]; then
    echo "No PDF files found in $INBOX_DIR.  Add files and try again." >&2
    exit 0
fi

echo "Processing ${#pdf_files[@]} PDF(s) in $INBOX_DIR…"
for pdf in "${pdf_files[@]}"; do
    rel_path="${pdf#${PROJECT_ROOT}/}"
    echo "\n=== Running Vision OCR on $rel_path ==="
    "$SCRIPT_DIR/run_vision_ocr.sh" "$rel_path"
done
echo "\nAll documents processed.  Check the letters/work folder for .vision.txt files."