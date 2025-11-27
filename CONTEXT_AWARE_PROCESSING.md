# Context-Aware Document Processing

**Date**: Nov 26, 2025  
**Status**: ✅ Implemented & Running

## Problem Identified

The initial batch processing was producing poor quality results:
1. **Generic Summaries**: AI was generating generic "WHO: The text is..." summaries
2. **No Context Usage**: OCR errors weren't being corrected using domain knowledge
3. **Poor Entity Recognition**: Sender/recipient not being identified correctly

## Root Cause

The batch processor was using:
- **Raw Google Vision OCR** → No correction of OCR errors
- **Direct Google Translate** → No context to improve accuracy
- **Basic AI Summarization** → No domain knowledge

## Solution: Enhanced OCR Pipeline

### Architecture

```
PDF Document
    ↓
[Google Vision OCR] ← Initial text extraction
    ↓
[EnhancedOCRProcessor] ← Context-aware correction
    ↓  (uses reference_data.json)
[Google Translate] ← Translates corrected text
    ↓
[Entity Extraction] ← Identifies people/places/events
    ↓
[Document Storage] ← Saves enhanced result
```

### Key Components

#### 1. EnhancedOCRProcessor
**File**: `scripts/enhanced_ocr_processor.py`

**Features**:
- Loads context from `context/reference_data.json`
- Uses OpenAI GPT-4 to correct OCR errors
- Applies domain knowledge about:
  - People (Robert Zentall, Betty Zentall, aliases)
  - Places (Vienna, Paris, common locations)
  - Historical context
  - Document patterns

**Example Correction**:
```
Raw OCR:     "Roberl Zweigenlhal"
Corrected:   "Robert Zentall" (using context/aliases)
```

#### 2. Context File
**File**: `context/reference_data.json`

**Structure**:
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
  }
}
```

**Purpose**:
- Corrects OCR name recognition errors
- Provides aliases for matching
- Gives historical context
- Improves entity extraction

### Implementation

#### Updated Pipeline

**File**: `scripts/batch_process_new_documents.py`

**Changes**:
1. **Imports BatchOCRProcessor**:
```python
from scripts.batch_processor import BatchOCRProcessor
```

2. **Uses Enhanced OCR**:
```python
def run_enhanced_ocr(pdf_path, batch_processor, context, source_lang):
    # Run Google Vision OCR
    ocr_result = batch_processor.run_ocr_on_pdf(pdf_path)
    raw_text = ocr_result['text']
    
    # Apply context-aware correction
    enhanced = batch_processor.processor.correct_with_context(raw_text, metadata)
    corrected_text = enhanced.get('corrected_text', raw_text)
    
    return (raw_text, corrected_text)
```

3. **Stores Both Versions**:
```python
doc_data = {
    'raw_text': raw_text,        # Original OCR
    'original_text': corrected_text,  # Context-corrected
    'translated_text': translated_text,
    ...
}
```

### Results & Improvements

#### Test Document: 131-1932-08-02-ger.pdf

**Before (Raw OCR)**:
- Sender: "Unknown"
- Summary: "WHO: The text is from..."
- OCR errors uncorrected

**After (Context-Aware)**:
- ✅ Sender: "Robert Zentall" (correctly identified!)
- ✅ Text corrected: 1703 → 1665 chars (OCR errors fixed)
- ✅ 16 references extracted (4 people, 4 places, 2 events, 3 themes, 3 emotions)

**Processing Time**: ~90 seconds per document
- +40 seconds for context-aware correction
- But much higher quality results!

### Benefits

#### 1. Improved Accuracy
- **OCR Error Correction**: Fixes common OCR mistakes
- **Name Recognition**: Correctly identifies people using aliases
- **Location Identification**: Better place recognition

#### 2. Better Metadata
- **Sender/Recipient**: Uses context to identify correspondents
- **Date Recognition**: Improves date extraction
- **Reference Categorization**: More accurate entity classification

#### 3. Quality Translations
- **Corrected Source Text**: Translates from corrected text, not raw OCR
- **Better Context**: Translation has cleaner input

#### 4. Historical Preservation
- **Raw Text Saved**: Original OCR preserved for reference
- **Corrections Documented**: Shows what was corrected
- **Context Applied**: Uses domain knowledge appropriately

### Configuration

#### OpenAI API
The EnhancedOCRProcessor uses OpenAI GPT-4 for correction:
```python
batch_processor = BatchOCRProcessor(
    provider='openai',
    context_file='context/reference_data.json'
)
```

**Cost Per Document**: ~$0.02-0.03 (for correction step)

#### Context Updates
To improve results, update `context/reference_data.json`:

```json
{
  "New Person": {
    "aliases": ["Alias 1", "Alias 2"],
    "type": "person",
    "context": "Description and historical info"
  },
  "New Place": {
    "type": "place",
    "context": "Geographic and historical info"
  }
}
```

### Monitoring

#### Progress Tracking
```bash
# Watch live processing
tail -f batch_131_177_context.log

# Check document count
ls -1 ocr_storage/documents/*.json | wc -l

# Verify correction is working
tail -50 batch_131_177_context.log | grep "Text corrected"
```

#### Quality Checks
Look for these indicators in logs:
- ✅ "Text corrected (N chars)" - Context applied
- ✅ Sender/Recipient identified (not "Unknown")
- ✅ References extracted with multiple types

### Performance

#### Timeline (per document)
1. Google Vision OCR: ~20-30 seconds
2. Context-aware correction: ~30-40 seconds ⭐ NEW
3. Image extraction: ~5 seconds
4. Translation: ~5-10 seconds
5. Metadata extraction: ~10 seconds
6. Reference extraction: ~10 seconds
7. Summary & save: ~5 seconds

**Total**: ~90 seconds per document (was ~50 seconds without context)

#### For 47 Remaining Documents (131-177)
- **Expected time**: ~70 minutes
- **Extra cost**: ~$1.20 (for context correction)
- **Quality improvement**: Significant ⭐

### Comparison

| Aspect | Without Context | With Context |
|--------|----------------|--------------|
| OCR Quality | Raw errors | Corrected ✅ |
| Sender ID | Often "Unknown" | Usually correct ✅ |
| Summaries | Generic | Better quality ✅ |
| References | Basic | Categorized ✅ |
| Time | 50 sec | 90 sec |
| Cost | $0.045 | $0.065 |
| **Value** | Lower | Higher ⭐ |

### Future Enhancements

1. **Expand Context**: Add more people, places, events to reference_data.json
2. **Custom Prompts**: Tailor correction prompts for specific document types
3. **Batch Context Updates**: Learn from processed documents to improve context
4. **Quality Metrics**: Track correction quality over time

### Files Modified

1. `scripts/batch_process_new_documents.py` - Integrated EnhancedOCRProcessor
2. `scripts/batch_processor.py` - Already had context-aware processing
3. `scripts/enhanced_ocr_processor.py` - Core correction engine
4. `context/reference_data.json` - Domain knowledge database

### Rollback Option

If context-aware processing causes issues:
```python
# Revert to raw OCR (in process_single_document):
original_text = run_ocr_on_pdf(pdf_path, project_root)
# Instead of:
# ocr_result = run_enhanced_ocr(...)
```

### Current Status

**Batch Processing**: Running with context-aware enhancement  
**Documents**: 130 of 177 (47 remaining)  
**Log**: `batch_131_177_context.log`  
**ETA**: ~70 minutes

---

**Summary**: Context-aware processing significantly improves OCR quality, entity recognition, and metadata extraction by leveraging domain knowledge from reference_data.json.

