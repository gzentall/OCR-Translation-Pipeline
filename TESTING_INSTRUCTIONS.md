# OCR Quality Enhancement - Testing Instructions

## Prerequisites

Before running the batch processor, you need to configure your OpenAI API key:

### Option 1: Environment Variable
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Option 2: Create API Key File
```bash
echo "your-api-key-here" > .openai_api_key
```

### Option 3: Add to .env File
```bash
# Add to your .env file:
OPENAI_API_KEY=your-api-key-here
```

## Running the Test Dataset

Once the API key is configured, process the test dataset:

```bash
# Process test dataset with OpenAI
python3 scripts/batch_processor.py \
    --input letters/test_dataset \
    --output letters/test_results \
    --provider openai

# Generate quality report
python3 scripts/ocr_comparison_tool.py letters/test_results/

# Open the HTML report in your browser
open letters/test_results/quality_report.html
```

## Review Process

1. **Review the HTML Report**
   - Check confidence scores (aim for >80%)
   - Review corrections made
   - Verify formatting is preserved
   - Look for any errors introduced

2. **Iterate on Prompts if Needed**
   - If quality is poor, update prompts in `scripts/enhanced_ocr_processor.py`
   - Add more context to `context/reference_data.json`
   - Re-run batch processor

3. **Once Satisfied with Quality**
   - Proceed to Phase 4: Process full dataset
   - Document any improvements needed

## Testing with Both Providers

To compare OpenAI vs Claude:

```bash
# Test with both providers
python3 scripts/batch_processor.py \
    --input letters/test_dataset \
    --output letters/test_results_both \
    --provider both
```

This will run both LLMs and choose the result with higher confidence.

## Expected Results

After processing, you should see:
- `letters/test_results/*.corrected.txt` - Corrected text files
- `letters/test_results/*.result.json` - Detailed results with corrections
- `letters/test_results/batch_summary.json` - Summary statistics
- `letters/test_results/quality_report.html` - Visual comparison report

## Cost Estimates

- ~2 test documents × ~1,000 words = ~2,000 tokens input
- ~2,000 tokens output
- Total: ~4,000 tokens = $0.01-0.02 with GPT-4o

## Next Steps

After validating quality on test dataset:
1. Process full dataset (<200 documents)
2. Migrate refined data to production
3. Deploy to production with UI updates

