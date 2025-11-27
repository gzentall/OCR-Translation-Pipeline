#!/usr/bin/env python3

"""
OCR Comparison Tool for OCR Translation Pipeline.
Generate HTML reports comparing raw OCR vs corrected OCR.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class OCRComparisonTool:
    """Generate quality comparison reports."""
    
    def __init__(self, results_dir: Path):
        """
        Initialize comparison tool.
        
        Args:
            results_dir: Directory containing batch processing results
        """
        self.results_dir = results_dir
        self.results = self._load_results()
    
    def _load_results(self) -> List[Dict]:
        """Load all result JSON files from directory."""
        results = []
        
        for result_file in self.results_dir.glob('*.result.json'):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Warning: Could not load {result_file}: {e}")
        
        return results
    
    def generate_html_report(self, output_file: Path):
        """
        Generate HTML report with side-by-side comparisons.
        
        Args:
            output_file: Path to output HTML file
        """
        if not self.results:
            print("No results found to generate report.")
            return
        
        html = self._generate_html()
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Report generated: {output_file}")
        print(f"   Open in browser: file://{output_file.absolute()}")
    
    def _generate_html(self) -> str:
        """Generate complete HTML report."""
        # Calculate summary statistics
        total_docs = len(self.results)
        avg_confidence = sum(r.get('confidence', 0) for r in self.results) / total_docs if total_docs > 0 else 0
        total_corrections = sum(r.get('corrections_count', 0) for r in self.results)
        
        # Sort by confidence (lowest first - need most review)
        sorted_results = sorted(self.results, key=lambda x: x.get('confidence', 0))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Quality Comparison Report</title>
    <style>
        :root {{
            --primary-color: #6750a4;
            --surface-color: #f5f5f5;
            --on-surface: #1c1b1f;
            --error-color: #ba1a1a;
            --success-color: #198754;
            --warning-color: #ff9800;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: var(--on-surface);
            background: var(--surface-color);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: var(--primary-color);
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .summary-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
            font-weight: normal;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .document {{
            margin-bottom: 60px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .document-header {{
            background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
            padding: 20px;
            border-bottom: 2px solid #ddd;
        }}
        
        .document-title {{
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 10px;
            color: var(--primary-color);
        }}
        
        .document-meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.9em;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .confidence-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .confidence-high {{
            background: #d4edda;
            color: #155724;
        }}
        
        .confidence-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .confidence-low {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }}
        
        .comparison-side {{
            padding: 20px;
            background: white;
        }}
        
        .comparison-side:first-child {{
            border-right: 2px solid #e0e0e0;
        }}
        
        .side-header {{
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary-color);
        }}
        
        .raw-header {{
            color: #dc3545;
        }}
        
        .corrected-header {{
            color: #198754;
        }}
        
        .text-content {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            font-size: 0.95em;
            padding: 15px;
            background: #fafafa;
            border-radius: 4px;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .corrections-list {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        .corrections-header {{
            font-weight: bold;
            margin-bottom: 10px;
            color: var(--primary-color);
        }}
        
        .correction-item {{
            padding: 8px 12px;
            margin: 8px 0;
            background: white;
            border-left: 3px solid var(--primary-color);
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        .correction-original {{
            color: #dc3545;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}
        
        .correction-arrow {{
            color: #666;
            margin: 0 8px;
        }}
        
        .correction-fixed {{
            color: #198754;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}
        
        .correction-reason {{
            color: #666;
            font-style: italic;
            margin-top: 4px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 900px) {{
            .comparison {{
                grid-template-columns: 1fr;
            }}
            
            .comparison-side:first-child {{
                border-right: none;
                border-bottom: 2px solid #e0e0e0;
            }}
        }}
        
        .legend {{
            margin: 30px 0;
            padding: 15px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            border-radius: 4px;
        }}
        
        .legend-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #1976d2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 OCR Quality Comparison Report</h1>
        <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Documents</h3>
                <div class="value">{total_docs}</div>
            </div>
            <div class="summary-card">
                <h3>Average Confidence</h3>
                <div class="value">{avg_confidence:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Total Corrections</h3>
                <div class="value">{total_corrections}</div>
            </div>
            <div class="summary-card">
                <h3>Corrections/Doc</h3>
                <div class="value">{total_corrections/total_docs:.1f}</div>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title">📖 How to Read This Report</div>
            <ul>
                <li><strong>Left side (red):</strong> Raw OCR output from Google Vision</li>
                <li><strong>Right side (green):</strong> AI-corrected text using context</li>
                <li><strong>Confidence score:</strong> LLM's confidence in corrections (0-100%)</li>
                <li><strong>Corrections list:</strong> Specific changes made with explanations</li>
                <li><strong>Sorted by confidence:</strong> Lowest confidence first (needs most review)</li>
            </ul>
        </div>
"""
        
        # Generate document sections
        for i, result in enumerate(sorted_results, 1):
            html += self._generate_document_section(result, i)
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_document_section(self, result: Dict, index: int) -> str:
        """Generate HTML for a single document comparison."""
        pdf_name = result.get('pdf_file', 'Unknown')
        confidence = result.get('confidence', 0)
        corrections = result.get('corrections', [])
        raw_text = result.get('raw_text', '')
        corrected_text = result.get('corrected_text', '')
        provider = result.get('provider_used', 'unknown')
        date_processed = result.get('date_processed', '')
        metadata = result.get('metadata', {})
        
        # Determine confidence class
        if confidence >= 80:
            confidence_class = 'confidence-high'
        elif confidence >= 60:
            confidence_class = 'confidence-medium'
        else:
            confidence_class = 'confidence-low'
        
        # Truncate text for display
        raw_display = raw_text[:3000] + ('...' if len(raw_text) > 3000 else '')
        corrected_display = corrected_text[:3000] + ('...' if len(corrected_text) > 3000 else '')
        
        html = f"""
        <div class="document">
            <div class="document-header">
                <div class="document-title">📄 {index}. {pdf_name}</div>
                <div class="document-meta">
                    <div class="meta-item">
                        <strong>Confidence:</strong>
                        <span class="confidence-badge {confidence_class}">{confidence}%</span>
                    </div>
                    <div class="meta-item">
                        <strong>Provider:</strong> {provider.upper()}
                    </div>
                    <div class="meta-item">
                        <strong>Corrections:</strong> {len(corrections)}
                    </div>
                    <div class="meta-item">
                        <strong>Date:</strong> {metadata.get('date', 'unknown')}
                    </div>
                    <div class="meta-item">
                        <strong>Language:</strong> {metadata.get('expected_language', 'unknown')}
                    </div>
                </div>
            </div>
            
            <div class="comparison">
                <div class="comparison-side">
                    <div class="side-header raw-header">❌ Raw OCR (Google Vision)</div>
                    <div class="text-content">{self._escape_html(raw_display)}</div>
                </div>
                <div class="comparison-side">
                    <div class="side-header corrected-header">✅ AI-Corrected Text</div>
                    <div class="text-content">{self._escape_html(corrected_display)}</div>
                </div>
            </div>
"""
        
        if corrections:
            html += f"""
            <div class="corrections-list">
                <div class="corrections-header">🔧 Corrections Made ({len(corrections)})</div>
"""
            
            # Show up to 20 corrections
            for correction in corrections[:20]:
                original = correction.get('original', '')
                fixed = correction.get('corrected', '')
                reason = correction.get('reason', '')
                
                html += f"""
                <div class="correction-item">
                    <div>
                        <span class="correction-original">"{self._escape_html(original)}"</span>
                        <span class="correction-arrow">→</span>
                        <span class="correction-fixed">"{self._escape_html(fixed)}"</span>
                    </div>
                    <div class="correction-reason">{self._escape_html(reason)}</div>
                </div>
"""
            
            if len(corrections) > 20:
                html += f"""
                <div style="margin-top: 10px; color: #666; font-style: italic;">
                    ... and {len(corrections) - 20} more corrections
                </div>
"""
            
            html += """
            </div>
"""
        
        html += """
        </div>
"""
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def print_summary(self):
        """Print text summary of results."""
        if not self.results:
            print("No results found.")
            return
        
        print(f"\n{'='*80}")
        print(f"OCR Quality Comparison Summary")
        print(f"{'='*80}")
        print(f"Total documents: {len(self.results)}")
        
        avg_confidence = sum(r.get('confidence', 0) for r in self.results) / len(self.results)
        print(f"Average confidence: {avg_confidence:.1f}%")
        
        total_corrections = sum(r.get('corrections_count', 0) for r in self.results)
        print(f"Total corrections: {total_corrections}")
        print(f"Average corrections/doc: {total_corrections/len(self.results):.1f}")
        
        print(f"\n{'='*80}")
        print("Documents by confidence:")
        print(f"{'='*80}")
        
        sorted_results = sorted(self.results, key=lambda x: x.get('confidence', 0))
        for result in sorted_results:
            confidence = result.get('confidence', 0)
            corrections = result.get('corrections_count', 0)
            pdf_name = result.get('pdf_file', 'Unknown')
            
            if confidence >= 80:
                emoji = '✅'
            elif confidence >= 60:
                emoji = '⚠️ '
            else:
                emoji = '❌'
            
            print(f"{emoji} {confidence:3.0f}% | {corrections:3d} corrections | {pdf_name}")
        
        print(f"{'='*80}\n")


def generate_quality_report(results_dir: str):
    """
    Main entry point for generating quality reports.
    
    Args:
        results_dir: Directory containing batch processing results
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"Error: Results directory not found: {results_dir}")
        return
    
    tool = OCRComparisonTool(results_path)
    
    # Print text summary
    tool.print_summary()
    
    # Generate HTML report
    output_file = results_path / 'quality_report.html'
    tool.generate_html_report(output_file)
    
    print(f"\n✅ Done! Open the report in your browser:")
    print(f"   file://{output_file.absolute()}\n")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Generate OCR quality comparison report'
    )
    parser.add_argument(
        'results_dir',
        help='Directory containing batch processing results'
    )
    
    args = parser.parse_args()
    generate_quality_report(args.results_dir)


if __name__ == "__main__":
    main()

