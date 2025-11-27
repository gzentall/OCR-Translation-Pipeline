# OCR Quality Enhancement System

## Overview

This system enhances OCR quality by post-processing Google Vision API results with LLMs (OpenAI GPT-4 or Claude) to correct handwriting recognition errors using contextual understanding.

## Architecture

```
PDF Document
    ↓
Google Vision OCR (existing)
    ↓
Enhanced OCR Processor (NEW)
    - Loads reference context (names, places, phrases)
    - Sends to LLM with context
    - Receives corrected text + explanations
    ↓
Local JSON Storage (enhanced)
    - Stores both original and corrected text
    - Stores confidence scores
    - Stores correction metadata
    ↓
Production PostgreSQL (when ready)
```

## Key Components

### 1. Reference Context (`context/reference_data.json`)
- Known people (names, nicknames, relationships)
- Known locations (addresses, cities)
- Common phrases (greetings, closings)
- Historical context

**Purpose**: Helps LLM make intelligent corrections based on domain knowledge.

### 2. Enhanced OCR Processor (`scripts/enhanced_ocr_processor.py`)
- Supports OpenAI GPT-4o and Claude
- Context-aware prompt engineering
- Dual-LLM comparison mode
- Entity extraction capabilities

**Key Method**: `correct_with_context(ocr_text, metadata)`

### 3. Batch Processor (`scripts/batch_processor.py`)
- Processes multiple PDFs in parallel
- Integrates with existing OCR pipeline
- Saves detailed results and metrics
- Supports dry-run mode

**Usage**:
```bash
python scripts/batch_processor.py \
    --input letters/inbox \
    --output letters/enhanced_results \
    --provider openai \
    --parallel 3
```

### 4. Comparison Tool (`scripts/ocr_comparison_tool.py`)
- Generates HTML reports
- Side-by-side text comparison
- Shows corrections with explanations
- Confidence scoring

**Usage**:
```bash
python scripts/ocr_comparison_tool.py letters/test_results/
```

### 5. Database Schema Updates (`scripts/database.py`)

New columns added to `documents` table:
- `corrected_text` (Text): LLM-corrected OCR output
- `correction_confidence` (Integer): 0-100 confidence score
- `correction_metadata` (Text): JSON with correction details
- `is_reviewed` (Boolean): Editor approval status

### 6. Export Tool (`scripts/export_to_production.py`)
- Migrates local data to PostgreSQL
- Supports dry-run mode
- Validates export completion
- Handles references and linking

**Usage**:
```bash
# Test export (safe)
python scripts/export_to_production.py --dry-run

# Actual export (requires confirmation)
python scripts/export_to_production.py --confirm
```

### 7. Database Migration (`scripts/migrate_database.py`)
- Adds new columns to existing databases
- Checks if columns already exist
- Includes verification

**Usage**:
```bash
python scripts/migrate_database.py
```

## Workflow

### Phase 1: Local Testing (YOU ARE HERE)

1. **Setup API Key**:
   ```bash
   export OPENAI_API_KEY="your-key"
   # or create .openai_api_key file
   ```

2. **Update Reference Context**:
   Edit `context/reference_data.json` with known names, places, phrases

3. **Process Test Dataset**:
   ```bash
   python scripts/batch_processor.py \
       --input letters/test_dataset \
       --output letters/test_results \
       --provider openai
   ```

4. **Review Quality Report**:
   ```bash
   python scripts/ocr_comparison_tool.py letters/test_results/
   open letters/test_results/quality_report.html
   ```

5. **Iterate**: If quality is low, update prompts or context, re-run

### Phase 2: Full Dataset Processing

Once satisfied with test results:

```bash
# Backup data
cp -r ocr_storage ocr_storage_backup_$(date +%Y%m%d)

# Process all documents
python scripts/batch_processor.py \
    --input letters/inbox \
    --output letters/enhanced_results \
    --provider openai \
    --parallel 3

# Validate
python scripts/validate_batch.py letters/enhanced_results/
```

### Phase 3: Production Migration

1. **Migrate Database Schema**:
   ```bash
   # On production database
   export DATABASE_URL="postgresql://..."
   python scripts/migrate_database.py
   ```

2. **Test Export** (dry-run):
   ```bash
   python scripts/export_to_production.py --dry-run
   ```

3. **Actual Export**:
   ```bash
   python scripts/export_to_production.py --confirm --validate
   ```

4. **Deploy UI Updates** (merge to main, deploy to Render)

## Data Flow

### Original OCR Text
- Always preserved in `original_text` field
- Never modified or deleted
- Available for rollback

### Corrected Text
- Stored in `corrected_text` field
- Shown during editing/review
- Becomes canonical after editor approval

### Translation
- Based on `corrected_text` (not raw OCR)
- Higher quality due to better source text

### Editor Workflow
1. View document with `corrected_text`
2. See "AI-enhanced (85% confidence)" badge
3. Use existing edit functionality to fix remaining errors
4. Save → marks `is_reviewed = True`
5. In browse mode → show final text only

## Cost Estimates

- Test dataset (2 docs): ~$0.01-0.02
- Full dataset (<200 docs): $2-4 with GPT-4o
- Per document: ~$0.01-0.02
- Enterprise OpenAI accounts may have better rates

## Quality Metrics

Target confidence scores:
- **High confidence (80-100%)**: Ready for editor review
- **Medium confidence (60-79%)**: Needs careful review
- **Low confidence (<60%)**: May need re-processing or manual transcription

Typical improvements:
- Fixes gibberish characters
- Corrects alphabet mixing (Cyrillic in English)
- Improves name recognition
- Preserves formatting
- Adds context-based corrections

## Rollback Strategy

If corrections make things worse:

```bash
# Restore backup
cp -r ocr_storage_backup_YYYYMMDD ocr_storage

# Database: original_text is always preserved
# Just ignore corrected_text field
```

## Troubleshooting

### "OPENAI_API_KEY not found"
```bash
export OPENAI_API_KEY="your-key"
# or create .openai_api_key file
```

### "Database connection failed"
```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
```

### Low confidence scores
- Add more context to `context/reference_data.json`
- Update prompts in `enhanced_ocr_processor.py`
- Try Claude instead of OpenAI (or use both)

### OCR script not found
- Make sure you're running from project root
- Check that `scripts/run_vision_ocr.sh` exists and is executable

## Files Created/Modified

**New Files**:
- `context/reference_data.json`
- `scripts/enhanced_ocr_processor.py`
- `scripts/batch_processor.py`
- `scripts/ocr_comparison_tool.py`
- `scripts/export_to_production.py`
- `scripts/migrate_database.py`
- `scripts/validate_batch.py`
- `TESTING_INSTRUCTIONS.md`
- `OCR_ENHANCEMENT_README.md` (this file)

**Modified Files**:
- `scripts/database.py` (added new columns)
- `scripts/local_storage.py` (to be updated for new fields)
- `app.py` (to be updated with new API endpoints)
- `templates/browse.html` (to be updated with UI badges)

## Next Steps

See `TESTING_INSTRUCTIONS.md` for step-by-step testing guide.

## Support

For issues or questions:
1. Check this README
2. Review `TESTING_INSTRUCTIONS.md`
3. Check the quality report HTML for specific issues
4. Review server logs for API errors

