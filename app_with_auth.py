#!/usr/bin/env python3

"""
Flask web application for OCR and translation pipeline with authentication.
Provides a web interface for uploading PDFs and processing them through OCR and translation.
"""

import os
import subprocess
import tempfile
import shutil
import traceback
import html
import sys
import jwt
import bcrypt
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid

# Add scripts directory to path for local storage
sys.path.append(str(Path(__file__).parent / 'scripts'))
from scripts.local_storage import LocalOCRStorage
from scripts.fallback_ai_processor import FallbackAIProcessor

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

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

# Initialize local storage and AI processor
local_storage = LocalOCRStorage()
ai_processor = FallbackAIProcessor()

ALLOWED_EXTENSIONS = {'pdf'}

# Simple in-memory user storage (in production, use a database)
USERS = {
    'gzentall': {
        'username': 'gzentall',
        'email': 'gabe@zentall.com',
        'password_hash': '$2b$12$MW7tZ/tTaGieqPgSTtc5oe8mGP6PNBwLwuU5/oE4Rci5C/9bva1.y',
        'role': 'SUPER_ADMIN',
        'is_active': True
    }
}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_auth(f):
    """Decorator to require authentication."""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_role(required_role):
    """Decorator to require specific role."""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = USERS.get(session['user_id'])
            if not user or user['role'] != required_role and user['role'] != 'SUPER_ADMIN':
                flash('Insufficient permissions', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def run_ocr_script(pdf_path, doc_id=None):
    """Run the Vision OCR script on a PDF file."""
    script_path = PROJECT_ROOT / "scripts" / "run_vision_ocr.sh"
    try:
        cmd = [str(script_path), str(pdf_path)]
        if doc_id:
            cmd.append(doc_id)
        
        result = subprocess.run(
            cmd,
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = USERS.get(username)
        if user and user['is_active'] and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = username
            session['user_role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    """Serve the main application page (Documents tab)."""
    return render_template('browse.html', user=USERS.get(session['user_id']))

@app.route('/upload-form')
@require_auth
def upload_form():
    """Serve the upload form for modal loading."""
    return render_template('upload_modal.html')

@app.route('/browse')
@require_auth
def browse():
    """Serve the main application interface."""
    return render_template('browse.html', user=USERS.get(session['user_id']))

@app.route('/stats-page')
@require_auth
def stats_page():
    """Serve the statistics page interface."""
    return render_template('stats.html', user=USERS.get(session['user_id']))

@app.route('/people-page')
@require_auth
def people_page():
    """Serve the people management page."""
    return render_template('people.html', user=USERS.get(session['user_id']))

@app.route('/users-page')
@require_auth
@require_role('SUPER_ADMIN')
def users_page():
    """Serve the user management page (SuperAdmin only)."""
    return render_template('users.html', user=USERS.get(session['user_id']), users=USERS)

@app.route('/documents/<doc_id>/images/<int:page_num>')
@require_auth
def get_document_image(doc_id, page_num):
    """Serve original document images."""
    try:
        # Get document metadata to find image path
        doc_metadata = local_storage.metadata["documents"].get(doc_id)
        if not doc_metadata:
            return "Document not found", 404
        
        # Look for image files in the work directory
        work_dir = Path("letters/work")
        image_pattern = f"{doc_id}_page_{page_num:03d}.png"
        image_path = work_dir / image_pattern
        
        if not image_path.exists():
            # Try alternative naming patterns
            alt_patterns = [
                f"{doc_id}_page_{page_num}.png",
                f"{doc_id}_{page_num}.png",
                f"{doc_id}_page_{page_num:02d}.png"
            ]
            
            for pattern in alt_patterns:
                alt_path = work_dir / pattern
                if alt_path.exists():
                    image_path = alt_path
                    break
            else:
                return "Image not found", 404
        
        return send_file(str(image_path), mimetype='image/png')
        
    except Exception as e:
        print(f"Error serving image: {e}")
        return "Error serving image", 500

@app.route('/upload', methods=['POST'])
@require_auth
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
        
        # Generate document ID for image naming
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Run OCR - pass relative path to the script
        relative_pdf_path = f"letters/inbox/{unique_filename}"
        success, stdout, stderr = run_ocr_script(relative_pdf_path, doc_id)
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
        
        # Read the original OCR text for storage
        original_text = ""
        if text_path.exists():
            with open(text_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
        
        print(f"[DEBUG] Successfully processed file, content length: {len(translated_content)}")
        
        # Process with AI and store locally
        try:
            print("[DEBUG] Processing document with AI...")
            ai_result = ai_processor.process_document(
                translated_content, 
                source_language="unknown",  # We could detect this from the translation script
                document_date=datetime.now().isoformat()
            )
            
            # Prepare document data for storage
            document_data = {
                "title": f"{name} - {datetime.now().strftime('%Y-%m-%d')}",
                "date_processed": datetime.now().isoformat(),
                "source_language": "unknown",  # Could be detected from translation script
                "target_language": "en",
                "original_text": original_text,
                "translated_text": translated_content,
                "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "summary": ai_result.get("summary", ""),
                "people": ai_result.get("people", [])
            }
            
            # Store in local database with the same doc_id used for images
            doc_id = local_storage.add_document(document_data, doc_id)
            print(f"[DEBUG] Document stored with ID: {doc_id}")
            
        except Exception as e:
            print(f"[WARNING] AI processing failed: {e}")
            # Still store the document without AI processing
            document_data = {
                "title": f"{name} - {datetime.now().strftime('%Y-%m-%d')}",
                "date_processed": datetime.now().isoformat(),
                "source_language": "unknown",
                "target_language": "en",
                "original_text": original_text,
                "translated_text": translated_content,
                "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "summary": "AI processing failed - manual review required",
                "people": []
            }
            doc_id = local_storage.add_document(document_data, doc_id)
            print(f"[DEBUG] Document stored without AI processing, ID: {doc_id}")
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'original_filename': filename,
            'translated_content': translated_content,
            'download_url': f'/download/{translated_filename}',
            'stored_document_id': doc_id,
            'ai_processed': 'summary' in locals() and ai_result.get("summary", "") != "AI processing failed - manual review required"
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
@require_auth
def download_file(filename):
    """Download processed files."""
    file_path = EN_DIR / filename
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/status')
@require_auth
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
@require_auth
def test_endpoint():
    """Simple test endpoint to verify the server is working."""
    return jsonify({
        'message': 'Server is working!',
        'timestamp': str(uuid.uuid4())[:8]
    })

@app.route('/documents')
@require_auth
def list_documents():
    """List all stored documents."""
    try:
        documents = local_storage.list_documents()
        # Convert tuples to dictionaries
        document_list = []
        for doc_id, metadata in documents:
            document_list.append({
                'id': doc_id,
                **metadata
            })
        
        return jsonify({
            'success': True,
            'documents': document_list,
            'total': len(document_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/documents/<doc_id>')
@require_auth
def get_document(doc_id):
    """Get a specific document by ID."""
    try:
        document = local_storage.get_document(doc_id)
        if document:
            return jsonify({
                'success': True,
                'document': document
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/people', methods=['GET', 'POST'])
@require_auth
def handle_people():
    """List all people mentioned in documents or add a new person."""
    if request.method == 'GET':
        try:
            people = local_storage.get_people()
            return jsonify({
                'success': True,
                'people': people,
                'total': len(people)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        """Add a new person reference."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            name = data.get('name', '').strip()
            aliases = data.get('aliases', [])
            context = data.get('context', '').strip()
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Name is required'
                }), 400
            
            # Add the person to the database
            success = local_storage.add_person(name, aliases, context)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Person added successfully',
                    'person': {
                        'name': name,
                        'aliases': aliases,
                        'context': context
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add person (may already exist)'
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/people/detailed')
@require_auth
def get_people_detailed():
    """Get all people with their associated documents."""
    try:
        people = local_storage.get_people_with_documents()
        return jsonify({
            'success': True,
            'people': people,
            'total': len(people)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/people/sorted')
@require_auth
def get_people_sorted():
    """Get all people sorted by frequency (document count) for dropdown menus."""
    try:
        people = local_storage.get_people_with_documents()
        # Return simplified format for dropdown menus
        sorted_people = []
        for person in people:
            sorted_people.append({
                'original_name': person['name'],
                'normalized_name': person['name'],  # For compatibility
                'document_count': person['document_count']
            })
        
        return jsonify({
            'success': True,
            'people': sorted_people,
            'total': len(sorted_people)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/people/<person_name>/documents')
@require_auth
def get_person_documents(person_name):
    """Get all documents that mention a specific person."""
    try:
        documents = local_storage.get_person_documents(person_name)
        return jsonify({
            'success': True,
            'person_name': person_name,
            'documents': documents,
            'total': len(documents)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/people/<person_name>', methods=['PUT'])
@require_auth
@require_role('ADMIN')
def update_person(person_name):
    """Update a person's name and context, or merge with another person."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if this is a merge operation
        is_merge = data.get('merge', False)
        if is_merge:
            target_name = data.get('name')
            if not target_name:
                return jsonify({
                    'success': False,
                    'error': 'Target name is required for merge'
                }), 400
            
            success = local_storage.merge_person(person_name, target_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Person {person_name} merged into {target_name}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Merge failed - person not found or merge operation failed'
                }), 404
        
        # Regular update operation
        new_name = data.get('name', person_name)
        new_context = data.get('context')
        
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400
        
        success = local_storage.update_person(person_name, new_name, new_context)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Person updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Person not found or update failed'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/documents/<doc_id>/people', methods=['POST'])
@require_auth
@require_role('ADMIN')
def add_person_to_document(doc_id):
    """Add a person reference to a document."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        person_name = data.get('person_name', '').strip()
        if not person_name:
            return jsonify({
                'success': False,
                'error': 'Person name is required'
            }), 400
        
        success = local_storage.add_person_to_document(doc_id, person_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Person {person_name} added to document'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add person to document'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/documents/<doc_id>/people', methods=['DELETE'])
@require_auth
@require_role('ADMIN')
def remove_person_from_document(doc_id):
    """Remove a person reference from a document."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        person_name = data.get('person_name', '').strip()
        if not person_name:
            return jsonify({
                'success': False,
                'error': 'Person name is required'
            }), 400
        
        success = local_storage.remove_person_from_document(doc_id, person_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Person {person_name} removed from document'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to remove person from document'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/people/<person_name>', methods=['DELETE'])
@require_auth
@require_role('ADMIN')
def remove_person(person_name):
    """Remove a person from the database."""
    try:
        success = local_storage.remove_person(person_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Person removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Person not found or removal failed'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search')
@require_auth
def search_documents():
    """Search documents by query."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400
        
        results = local_storage.search_documents(query)
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/export')
@require_auth
def export_data():
    """Export all data."""
    try:
        export_format = request.args.get('format', 'json')
        
        if export_format == 'json':
            data = local_storage.export_to_notion_format()
            return jsonify({
                'success': True,
                'data': data
            })
        elif export_format == 'report':
            report = local_storage.generate_report()
            return jsonify({
                'success': True,
                'report': report
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Use "json" or "report"'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stats')
@require_auth
def get_statistics():
    """Get statistics about stored data."""
    try:
        documents = local_storage.list_documents()
        people = local_storage.get_people()
        
        # Language statistics
        languages = {}
        for _, metadata in documents:
            lang = metadata['source_language']
            languages[lang] = languages.get(lang, 0) + 1
        
        # Most mentioned people
        people_by_docs = [(name, len(data['documents'])) for name, data in people.items()]
        people_by_docs.sort(key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_documents': len(documents),
                'total_people': len(people),
                'languages': languages,
                'most_mentioned_people': people_by_docs[:5]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/documents/<doc_id>', methods=['PUT'])
@require_auth
@require_role('ADMIN')
def update_document(doc_id):
    """Update a document."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if we should regenerate summary
        regenerate_summary = data.pop('regenerate_summary', False)
        
        # Validate required fields (title is always required, summary only if not regenerating)
        if 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: title'
            }), 400
        
        if not regenerate_summary and 'summary' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: summary'
            }), 400
        
        # Update the document
        success = local_storage.update_document(doc_id, data, regenerate_summary=regenerate_summary)
        
        if success:
            # Get the updated document to return the new summary if regenerated
            updated_doc = local_storage.get_document(doc_id)
            response_data = {
                'success': True,
                'message': 'Document updated successfully'
            }
            
            if regenerate_summary and updated_doc:
                response_data['regenerated_summary'] = updated_doc.get('summary', '')
                response_data['regenerated_people'] = updated_doc.get('people', [])
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': 'Document not found or update failed'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/documents/<doc_id>', methods=['DELETE'])
@require_auth
@require_role('ADMIN')
def delete_document(doc_id):
    """Delete a document."""
    try:
        success = local_storage.delete_document(doc_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Document not found or deletion failed'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# User management API endpoints (SuperAdmin only)
@app.route('/api/users', methods=['GET'])
@require_auth
@require_role('SUPER_ADMIN')
def api_list_users():
    """List all users (SuperAdmin only)."""
    try:
        user_list = []
        for username, user_data in USERS.items():
            user_list.append({
                'username': username,
                'email': user_data['email'],
                'role': user_data['role'],
                'is_active': user_data['is_active']
            })
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total': len(user_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users', methods=['POST'])
@require_auth
@require_role('SUPER_ADMIN')
def api_create_user():
    """Create a new user (SuperAdmin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'USER')
        
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Username, email, and password are required'
            }), 400
        
        if username in USERS:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        USERS[username] = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'is_active': True
        }
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'username': username,
                'email': email,
                'role': role,
                'is_active': True
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<username>', methods=['PUT'])
@require_auth
@require_role('SUPER_ADMIN')
def api_update_user(username):
    """Update a user (SuperAdmin only)."""
    try:
        if username not in USERS:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update user data
        if 'email' in data:
            USERS[username]['email'] = data['email']
        if 'role' in data:
            USERS[username]['role'] = data['role']
        if 'is_active' in data:
            USERS[username]['is_active'] = data['is_active']
        if 'password' in data and data['password']:
            # Hash new password
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            USERS[username]['password_hash'] = password_hash
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<username>', methods=['DELETE'])
@require_auth
@require_role('SUPER_ADMIN')
def api_delete_user(username):
    """Delete a user (SuperAdmin only)."""
    try:
        if username not in USERS:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        if USERS[username]['role'] == 'SUPER_ADMIN':
            return jsonify({
                'success': False,
                'error': 'Cannot delete SUPER_ADMIN user'
            }), 400
        
        del USERS[username]
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
