# Batch Document Processing Guide

This guide documents the complete pipeline for processing batches of PDF documents through OCR, translation, and metadata extraction.

## Overview

The batch processing pipeline automatically processes PDF documents through these stages:
1. **Google Vision OCR** - Extracts handwritten text from PDFs
2. **Image Extraction** - Extracts page images for display using pdftoppm
3. **Translation** - Translates non-English text to English using Google Translate
4. **Metadata Extraction** - Identifies sender, recipient, and locations
5. **Reference Extraction** - Categorizes people, places, events, themes, and emotions
6. **Document Storage** - Saves to local storage with all metadata

## Prerequisites

### Required Services
- **Google Cloud Vision API** - For handwriting OCR
- **Google Translate API** - For translation
- **OpenAI API** - For LLM-based reference extraction and summarization

### Required Tools
- `poppler-utils` (for `pdftoppm` command)
  ```bash
  brew install poppler  # macOS
  ```

### API Keys
Ensure these environment variables or files are set:
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud service account JSON
- `.openai_api_key` - File containing OpenAI API key
- `.translate_api_key` - File containing Google Translate API key

## File Organization

### Input Files
Place PDF files in:
```
letters/inbox/
```

Expected filename format:
```
NNN-YYYY-MM-DD-lang.pdf
```
Examples:
- `108-1935-09-17-ger.pdf` - Document 108, dated Sept 17, 1935, German
- `109-1936-10-21-fre.pdf` - Document 109, dated Oct 21, 1936, French
- `110-xxx-ger.pdf` - Document 110, unknown date, German

**Language codes (ISO 639-2):**
- `ger` - German
- `fre` - French
- `eng` - English
- `spa` - Spanish
- `ita` - Italian
- `pol` - Polish
- `rus` - Russian

### Output Structure
```
ocr_storage/
├── documents/          # Individual document JSON files
│   ├── doc_YYYYMMDD_HHMMSS.json
│   └── ...
├── metadata.json      # Global metadata index
└── people/            # People/reference data

letters/
└── work/              # Working directory
    ├── *.vision.txt   # OCR output from Google Vision
    ├── *.png          # Extracted page images
    └── ...
```

## Usage

### Basic Usage

Process all unprocessed PDFs:
```bash
python3 scripts/batch_process_new_documents.py
```

### Process Specific Range

Process only files 108-177:
```bash
python3 scripts/batch_process_new_documents.py --start 108 --end 177
```

### Background Processing

For large batches, run in background:
```bash
nohup python3 scripts/batch_process_new_documents.py --start 108 --end 177 > batch.log 2>&1 &
```

Monitor progress:
```bash
tail -f batch.log
```

## Processing Pipeline Details

### 1. Google Vision OCR
- Calls `scripts/run_vision_ocr.sh` 
- Extracts handwritten and printed text
- Outputs to `letters/work/{filename}.vision.txt`
- Timeout: 5 minutes per document
- **Quality**: Google Vision is optimized for handwriting recognition

### 2. Image Extraction
- Uses `pdftoppm` to extract pages as PNG images
- Resolution: 300 DPI
- Stored in `letters/work/`
- Used for display in the web UI
- Linked to document via `page_images` field

### 3. Translation
- Automatically translates non-English documents
- Uses Google Translate API
- Preserves original text in `original_text` field
- Translation in `translated_text` field
- Skips if source language is English

### 4. Metadata Extraction
- Uses `EnvelopeExtractor` with LLM
- **Context-Aware**: Uses `context/reference_data.json`
- Extracts:
  - Sender name
  - Recipient name  
  - Sender location
  - Recipient location
- **Special handling**: Recognizes "Betty Zentall" and "Robert Zentall" as primary correspondents

### 5. Reference Extraction
- Uses `ReferenceExtractor` with OpenAI GPT-4
- **Categories**:
  - **People**: Names of individuals mentioned
  - **Places**: Locations, addresses, cities, countries
  - **Events**: Historical events, personal events, dates
  - **Themes**: Topics, subjects, concepts
  - **Emotions**: Emotional tone, sentiments expressed
- Each reference includes name and context
- References are linked to documents

### 6. Summary Generation
- Uses `AIProcessor.generate_summary()`
- Creates concise summary of document content
- Language-aware summarization
- First line used as document title

### 7. Document Storage
- Saves to `ocr_storage/documents/{doc_id}.json`
- Updates global `metadata.json` index
- Auto-generates unique document ID
- Sets status to "new"
- All fields:
  ```json
  {
    "id": "doc_20251126_143036",
    "title": "Letter from Robert to Betty",
    "original_text": "...",
    "translated_text": "...",
    "summary": "...",
    "language": "ger",
    "date": "1935-09-17",
    "sender": "Robert Zentall",
    "recipient": "Betty Zentall",
    "sender_location": "Vienna, Austria",
    "recipient_location": "Paris, France",
    "page_images": ["letters/work/108-xxx-ger-1.png", ...],
    "source_file": "letters/inbox/108-xxx-ger.pdf",
    "status": "new",
    "reviews": [],
    "created_at": "2025-11-26T14:30:36",
    "updated_at": "2025-11-26T14:30:36"
  }
  ```

## Context File

The `context/reference_data.json` file provides domain knowledge to improve extraction accuracy:

```json
{
  "Robert Zentall": {
    "aliases": ["Robert Zweigenthal", "Bobby", "R. Zentall"],
    "type": "person",
    "context": "Primary correspondent..."
  },
  "Betty Zentall": {
    "aliases": ["Elizabeth Aigner", "Elisabeth Zentall", "Betty"],
    "type": "person", 
    "context": "Primary correspondent..."
  },
  "Vienna": {
    "type": "place",
    "context": "City in Austria where Robert lived..."
  }
}
```

## Performance

### Typical Timing (per document)
- Google Vision OCR: 15-30 seconds
- Translation: 5-10 seconds
- Reference Extraction: 10-15 seconds
- Summary Generation: 5-10 seconds
- **Total**: ~45-60 seconds per document

### For 70 Documents
- Expected time: 50-70 minutes
- With 2-second pause between documents to avoid rate limiting

## Error Handling

### Common Issues

**1. "pdftoppm not found"**
```bash
brew install poppler
```

**2. "Google Vision OCR failed"**
- Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Verify Google Cloud Vision API is enabled
- Check API quota/billing

**3. "Translation failed"**
- Check `.translate_api_key` file exists
- Verify Google Translate API is enabled
- Invalid language codes will skip translation

**4. "Reference extraction error"**
- Check `.openai_api_key` file exists
- Verify OpenAI API has sufficient credits
- Check API rate limits

### Partial Failures
The pipeline continues even if some steps fail:
- Translation failure → Uses original text
- Reference extraction failure → No references added
- Metadata extraction failure → Uses default "Unknown" values
- Summary failure → Uses filename as title

Document is only marked as failed if:
- OCR produces less than 50 characters
- Image extraction completely fails
- Document save fails

## Monitoring

### Check Progress
```bash
tail -f batch.log
```

### Check How Many Processed
```bash
ls -1 ocr_storage/documents/*.json | wc -l
```

### View Summary Statistics
Look for final output in log:
```
================================================================================
BATCH PROCESSING COMPLETE
================================================================================
✅ Successful: 68
❌ Failed: 2
⏱️  Time elapsed: 58.3 minutes
📊 Average: 50.0 seconds per document
================================================================================
```

## Troubleshooting

### Script Hangs on OCR
- OCR has 5-minute timeout per document
- Check `letters/work/` for partial output
- Some documents may be very long or low quality

### Out of Memory
- Process in smaller batches (e.g., 10-20 at a time)
- Use `--start` and `--end` flags

### API Rate Limits
- Script includes 2-second pause between documents
- OpenAI: Check your tier limits
- Google Vision: Usually generous free tier
- Google Translate: Check quota in Google Cloud Console

### Re-running After Failure
The script automatically skips already-processed files:
- Checks `source_file` field in existing documents
- Only processes PDFs not yet in storage
- Safe to re-run multiple times

## Quality Assurance

After batch processing:

1. **Check Document Count**
   ```bash
   # Should match number of PDFs processed
   ls ocr_storage/documents/*.json | wc -l
   ```

2. **Review in Web UI**
   - Navigate to http://localhost:5001
   - Check status filter shows "New" documents
   - Spot-check translations and references
   - Verify images display correctly

3. **Check for Empty Summaries**
   ```bash
   grep -l '"summary": ""' ocr_storage/documents/*.json
   ```

4. **Verify References**
   - Check References tab in UI
   - Should see categorized references
   - People, places, events should be extracted

## Script Maintenance

### Location
```
scripts/batch_process_new_documents.py
```

### Key Functions
- `run_ocr_on_pdf()` - Calls Google Vision OCR
- `extract_pdf_images()` - Extracts display images
- `translate_document()` - Handles translation with language mapping
- `extract_document_metadata()` - Uses EnvelopeExtractor
- `extract_document_references()` - Uses ReferenceExtractor
- `process_single_document()` - Main pipeline orchestration

### Customization

**Add New Language:**
```python
lang_map = {
    'ger': 'de',
    'fre': 'fr',
    'dut': 'nl',  # Add Dutch
    # ...
}
```

**Adjust Timeouts:**
```python
subprocess.run([...], timeout=300)  # 5 minutes -> adjust as needed
```

**Change Image Resolution:**
```python
subprocess.run(['pdftoppm', '-png', '-r', '300', ...])  # 300 DPI
```

## Future Batch Processing

To process future batches:

1. **Add PDFs to inbox:**
   ```bash
   cp new_documents/*.pdf letters/inbox/
   ```

2. **Run batch processor:**
   ```bash
   # Process all new files
   python3 scripts/batch_process_new_documents.py
   
   # Or specific range
   python3 scripts/batch_process_new_documents.py --start 178 --end 250
   ```

3. **Monitor and verify:**
   ```bash
   tail -f batch.log
   ```

4. **Review in UI:**
   - Check new documents appear
   - Verify metadata accuracy
   - Review references

## Cost Estimation

### Per Document (approximate)
- Google Vision OCR: $0.015 (2 pages)
- Google Translate: $0.0002 (500 chars)
- OpenAI GPT-4: $0.03 (reference extraction + summary)
- **Total**: ~$0.045 per document

### For 70 Documents
- **Total cost**: ~$3.15

Actual costs vary based on:
- Document length (number of pages)
- Text length (affects translation and LLM costs)
- API tier/pricing changes

## Support

For issues:
1. Check this guide first
2. Review error messages in batch log
3. Test with single document using `--start N --end N`
4. Check API keys and quotas
5. Verify all prerequisites installed

## Version History

- **v1.0** (2025-11-26): Initial batch processor
  - Google Vision OCR integration
  - Translation with language mapping
  - Full metadata and reference extraction
  - Context-aware processing

