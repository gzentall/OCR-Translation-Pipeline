#!/usr/bin/env python3

"""
Flask web application for OCR and translation pipeline.
Provides a web interface for uploading PDFs and processing them through OCR and translation.
"""

import os
import subprocess
import tempfile
import shutil
import traceback
import html
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Project paths
PROJECT_ROOT = Path(__file__).parent
INBOX_DIR = PROJECT_ROOT / "letters" / "inbox"
WORK_DIR = PROJECT_ROOT / "letters" / "work"
OUT_DIR = PROJECT_ROOT / "letters" / "out"
EN_DIR = OUT_DIR / "en"

# Ensure directories exist
for directory in [INBOX_DIR, WORK_DIR, OUT_DIR, EN_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_ocr_script(pdf_path):
    """Run the Vision OCR script on a PDF file."""
    script_path = PROJECT_ROOT / "scripts" / "run_vision_ocr.sh"
    try:
        result = subprocess.run(
            [str(script_path), str(pdf_path)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300  # 5 minute timeout for large files
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "OCR processing timed out (5 minutes)"
    except Exception as e:
        return False, "", str(e)


def run_translation_script(text_file_path):
    """Run the Google Translate script on a text file."""
    script_path = PROJECT_ROOT / "scripts" / "translate_google.py"
    try:
        result = subprocess.run(
            ["python3", str(script_path), str(text_file_path)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120  # 2 minute timeout for translation
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Translation timed out (2 minutes)"
    except Exception as e:
        return False, "", str(e)


@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload and processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
    except Exception as e:
        return jsonify({'error': f'File validation failed: {str(e)}'}), 400
    
    # Generate unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{unique_id}{ext}"
    
    # Save uploaded file
    pdf_path = INBOX_DIR / unique_filename
    file.save(str(pdf_path))
    
    try:
        print(f"[DEBUG] Starting OCR processing for: {pdf_path}")
        
        # Run OCR - pass relative path to the script
        relative_pdf_path = f"letters/inbox/{unique_filename}"
        success, stdout, stderr = run_ocr_script(relative_pdf_path)
        print(f"[DEBUG] OCR result - success: {success}, stdout: {stdout[:200]}, stderr: {stderr[:200]}")
        
        if not success:
            return jsonify({
                'error': 'OCR processing failed',
                'details': stderr,
                'stdout': stdout
            }), 500
        
        # Find the generated text file
        text_filename = f"{name}_{unique_id}.vision.txt"
        text_path = WORK_DIR / text_filename
        print(f"[DEBUG] Looking for OCR text file: {text_path}")
        
        if not text_path.exists():
            # List files in work directory for debugging
            work_files = list(WORK_DIR.glob("*.txt"))
            return jsonify({
                'error': 'OCR text file not found',
                'details': f'Expected: {text_path}',
                'available_files': [str(f) for f in work_files]
            }), 500
        
        print(f"[DEBUG] Starting translation for: {text_path}")
        
        # Run translation
        success, stdout, stderr = run_translation_script(text_path)
        print(f"[DEBUG] Translation result - success: {success}, stdout: {stdout[:200]}, stderr: {stderr[:200]}")
        
        if not success:
            return jsonify({
                'error': 'Translation failed',
                'details': stderr,
                'stdout': stdout
            }), 500
        
        # Find the translated file
        translated_filename = f"{name}_{unique_id}.translated.txt"
        translated_path = WORK_DIR / translated_filename
        print(f"[DEBUG] Looking for translated file: {translated_path}")
        
        if not translated_path.exists():
            # List files in work directory for debugging
            work_files = list(WORK_DIR.glob("*.txt"))
            return jsonify({
                'error': 'Translated file not found',
                'details': f'Expected: {translated_path}',
                'available_files': [str(f) for f in work_files]
            }), 500
        
        # Move translated file to output directory
        final_translated_path = EN_DIR / translated_filename
        print(f"[DEBUG] Moving translated file to: {final_translated_path}")
        shutil.move(str(translated_path), str(final_translated_path))
        
        # Read the translated content
        with open(final_translated_path, 'r', encoding='utf-8') as f:
            translated_content = f.read()
        
        # Decode HTML entities (like &#39; for apostrophes)
        translated_content = html.unescape(translated_content)
        
        print(f"[DEBUG] Successfully processed file, content length: {len(translated_content)}")
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'original_filename': filename,
            'translated_content': translated_content,
            'download_url': f'/download/{translated_filename}'
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Upload processing failed: {str(e)}")
        print(f"[ERROR] Traceback: {error_traceback}")
        return jsonify({
            'error': 'Processing failed',
            'details': str(e),
            'traceback': error_traceback
        }), 500
    
    finally:
        # Clean up uploaded file
        if pdf_path.exists():
            pdf_path.unlink()


@app.route('/download/<filename>')
def download_file(filename):
    """Download processed files."""
    file_path = EN_DIR / filename
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/status')
def status():
    """Check system status and prerequisites."""
    status_info = {
        'api_key_exists': (PROJECT_ROOT / '.gcp_api_key').exists(),
        'directories_exist': {
            'inbox': INBOX_DIR.exists(),
            'work': WORK_DIR.exists(),
            'out': OUT_DIR.exists(),
            'en': EN_DIR.exists()
        },
        'scripts_exist': {
            'ocr': (PROJECT_ROOT / 'scripts' / 'run_vision_ocr.sh').exists(),
            'translate': (PROJECT_ROOT / 'scripts' / 'translate_google.py').exists()
        }
    }
    
    # Check if Docker is available
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        status_info['docker_available'] = True
    except:
        status_info['docker_available'] = False
    
    return jsonify(status_info)


@app.route('/test')
def test_endpoint():
    """Simple test endpoint to verify the server is working."""
    return jsonify({
        'message': 'Server is working!',
        'timestamp': str(uuid.uuid4())[:8]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
