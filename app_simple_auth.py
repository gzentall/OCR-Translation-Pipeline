#!/usr/bin/env python3

"""
Flask web application for OCR and translation pipeline with simple authentication.
Provides a web interface for uploading PDFs and processing them through OCR and translation.
"""

import os
import subprocess
import tempfile
import shutil
import traceback
import html
import sys
import bcrypt
import secrets
import requests
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

# Load environment variables from ocr-auth/.env.local
env_path = Path(__file__).parent / 'ocr-auth' / '.env.local'
load_dotenv(env_path)

# Add scripts directory to path for local storage
sys.path.append(str(Path(__file__).parent / 'scripts'))
from scripts.local_storage import LocalOCRStorage
from scripts.fallback_ai_processor import FallbackAIProcessor

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

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

# Simple user storage
USERS = {
    'gzentall': {
        'username': 'gzentall',
        'email': 'gabe@zentall.com',
        'first_name': 'Gabe',
        'last_name': 'Zentall',
        'password_hash': '$2b$12$MW7tZ/tTaGieqPgSTtc5oe8mGP6PNBwLwuU5/oE4Rci5C/9bva1.y',
        'role': 'SUPER_ADMIN',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat()
    },
    'admin': {
        'username': 'admin',
        'email': 'admin@example.com',
        'first_name': 'Admin',
        'last_name': '',
        'password_hash': '$2b$12$MW7tZ/tTaGieqPgSTtc5oe8mGP6PNBwLwuU5/oE4Rci5C/9bva1.y',  # Same as gzentall for testing
        'role': 'ADMIN',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat()
    },
    'user1': {
        'username': 'user1',
        'email': 'user1@example.com',
        'first_name': 'User',
        'last_name': 'One',
        'password_hash': '$2b$12$MW7tZ/tTaGieqPgSTtc5oe8mGP6PNBwLwuU5/oE4Rci5C/9bva1.y',  # Same as gzentall for testing
        'role': 'USER',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat()
    },
    'inactive_user': {
        'username': 'inactive_user',
        'email': 'inactive@example.com',
        'first_name': 'Inactive',
        'last_name': 'User',
        'password_hash': '$2b$12$MW7tZ/tTaGieqPgSTtc5oe8mGP6PNBwLwuU5/oE4Rci5C/9bva1.y',  # Same as gzentall for testing
        'role': 'USER',
        'is_active': False,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat()
    }
}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_invitation_email(email, username, invitation_token, inviter_name="Admin"):
    """Send invitation email using Resend."""
    try:
        resend_api_key = os.getenv('RESEND_API_KEY')
        if not resend_api_key:
            print("Warning: RESEND_API_KEY not found in environment variables")
            return False
        
        # Prefer Flask server URL so activation hits this app, fall back to APP_URL
        app_url = os.getenv('FLASK_API_URL', os.getenv('APP_URL', 'http://localhost:5001'))
        activation_url = f"{app_url}/activate?token={invitation_token}"
        
        email_data = {
            "from": "Postmark OCR <onboarding@resend.dev>",
            "to": [email],
            "subject": f"You're invited to join Postmark OCR",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Invitation to Postmark OCR</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📧 You're Invited!</h1>
                </div>
                <div class="content">
                    <h2>Welcome to Postmark OCR</h2>
                    <p>Hello {username},</p>
                    <p>{inviter_name} has invited you to join Postmark OCR, our document processing and translation platform.</p>
                    <p>Click the button below to activate your account and set up your password:</p>
                    <p style="text-align: center;">
                        <a href="{activation_url}" class="button">Activate Account</a>
                    </p>
                    <p><strong>What you can do after activation:</strong></p>
                    <ul>
                        <li>Set up your password</li>
                        <li>Configure a passkey for secure login</li>
                        <li>Edit your profile information</li>
                        <li>Access the document processing system</li>
                    </ul>
                    <p><small>This invitation link will expire in 7 days. If you didn't expect this invitation, you can safely ignore this email.</small></p>
                </div>
                <div class="footer">
                    <p>Postmark OCR - Document Processing Platform</p>
                </div>
            </body>
            </html>
            """
        }
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json=email_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Invitation email sent successfully to {email}")
            return True
        else:
            print(f"Failed to send invitation email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending invitation email: {str(e)}")
        return False

def require_auth(f):
    """Decorator to require authentication."""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

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
        if user and user['is_active'] and user.get('is_activated', True):
            if user['password_hash'] and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session['user_id'] = username
                session['user_role'] = user['role']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        elif user and not user.get('is_activated', True):
            flash('Account not activated. Please check your email for activation instructions.', 'error')
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/activate')
def activate_user():
    """User activation page."""
    token = request.args.get('token')
    if not token:
        return render_template('activation_error.html', error="Invalid activation link")
    
    # Find user by token
    user = None
    for username, user_data in USERS.items():
        if user_data.get('invitation_token') == token:
            user = user_data
            user['username'] = username
            break
    
    if not user:
        return render_template('activation_error.html', error="Invalid or expired activation link")
    
    # Check if token is expired (7 days)
    if user.get('invited_at'):
        invited_date = datetime.fromisoformat(user['invited_at'])
        if datetime.now() - invited_date > timedelta(days=7):
            return render_template('activation_error.html', error="Activation link has expired")
    
    # Check if already activated
    if user.get('is_activated', False):
        return render_template('activation_error.html', error="Account is already activated")
    
    return render_template('activation.html', user=user, token=token)

@app.route('/activate', methods=['POST'])
def complete_activation():
    """Complete user activation."""
    token = request.form.get('token')
    password = request.form.get('password')
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    
    if not token or not password:
        return render_template('activation_error.html', error="Token and password are required")
    
    # Find user by token
    user_username = None
    for username, user_data in USERS.items():
        if user_data.get('invitation_token') == token:
            user_username = username
            break
    
    if not user_username:
        return render_template('activation_error.html', error="Invalid activation token")
    
    user = USERS[user_username]
    
    # Check if already activated
    if user.get('is_activated', False):
        return render_template('activation_error.html', error="Account is already activated")
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user
    USERS[user_username].update({
        'password_hash': password_hash,
        'is_activated': True,
        'activated_at': datetime.now().isoformat(),
        'invitation_token': None,  # Clear token
        'first_name': first_name or user.get('first_name', ''),
        'last_name': last_name or user.get('last_name', '')
    })
    
    return render_template('activation_success.html', username=user_username)

@app.route('/')
@require_auth
def index():
    """Serve the main application page (Documents tab)."""
    user = USERS.get(session['user_id'])
    return render_template('browse.html', user=user)

@app.route('/upload-form')
@require_auth
def upload_form():
    """Serve the upload form for modal loading."""
    return render_template('upload_modal.html')

@app.route('/browse')
@require_auth
def browse():
    """Serve the main application interface."""
    user = USERS.get(session['user_id'])
    return render_template('browse.html', user=user)

@app.route('/stats-page')
@require_auth
def stats_page():
    """Serve the statistics page interface."""
    user = USERS.get(session['user_id'])
    return render_template('stats.html', user=user)

@app.route('/people-page')
@require_auth
def people_page():
    """Serve the people management page."""
    user = USERS.get(session['user_id'])
    return render_template('people.html', user=user)

@app.route('/users-page')
@require_auth
def users_page():
    """Serve the user management page (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    return render_template('users.html', user=user, users=USERS)

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
                "people": ai_result.get("people", []),
                "status": "New"
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
                "people": [],
                "status": "New"
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
        
        # If any changes are made (except status), automatically set status to "Editing"
        if any(key in data for key in ['title', 'summary', 'translated_text', 'people']):
            data['status'] = 'Editing'
        
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

@app.route('/documents/<doc_id>/status', methods=['PUT'])
@require_auth
def update_document_status(doc_id):
    """Update document status only."""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        status = data['status']
        if status not in ['New', 'Editing', 'Final']:
            return jsonify({
                'success': False,
                'error': 'Invalid status. Must be New, Editing, or Final'
            }), 400
        
        # Update only the status
        success = local_storage.update_document(doc_id, {'status': status})
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Document status updated to {status}'
            })
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
def api_list_users():
    """List all users (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_list = []
        for username, user_data in USERS.items():
            user_list.append({
                'username': username,
                'email': user_data['email'],
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'role': user_data['role'],
                'is_active': user_data['is_active'],
                'is_activated': user_data.get('is_activated', True),
                'invited_at': user_data.get('invited_at'),
                'activated_at': user_data.get('activated_at')
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
def api_create_user():
    """Create a new user (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'USER')
        
        if not username or not email:
            return jsonify({
                'success': False,
                'error': 'Username and email are required'
            }), 400
        
        if username in USERS:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        invited_at = datetime.now().isoformat()
        
        # Create user as inactive (not activated)
        USERS[username] = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password_hash': None,  # Will be set during activation
            'role': role,
            'is_active': True,  # Active but not activated
            'is_activated': False,
            'invitation_token': invitation_token,
            'invited_at': invited_at,
            'activated_at': None
        }
        
        # Send invitation email
        inviter = USERS.get(session['user_id'], {})
        inviter_name = f"{inviter.get('first_name', '')} {inviter.get('last_name', '')}".strip() or inviter.get('username', 'Admin')
        
        email_sent = send_invitation_email(email, username, invitation_token, inviter_name)
        
        return jsonify({
            'success': True,
            'message': f'User created successfully. Invitation email {"sent" if email_sent else "failed to send"} to {email}',
            'user': {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'is_active': True,
                'is_activated': False,
                'invited_at': invited_at
            },
            'email_sent': email_sent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<username>/resend-invite', methods=['POST'])
@require_auth
def api_resend_invite(username):
    """Resend invitation email to a not-yet-activated user (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    try:
        if username not in USERS:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        target = USERS[username]
        if target.get('is_activated', False):
            return jsonify({'success': False, 'error': 'User already activated'}), 400

        # Ensure a token exists; if expired/missing, create a new one
        if not target.get('invitation_token'):
            target['invitation_token'] = secrets.token_urlsafe(32)
        target['invited_at'] = datetime.now().isoformat()

        inviter = USERS.get(session['user_id'], {})
        inviter_name = f"{inviter.get('first_name', '')} {inviter.get('last_name', '')}".strip() or inviter.get('username', 'Admin')
        email_sent = send_invitation_email(target['email'], username, target['invitation_token'], inviter_name)

        return jsonify({
            'success': True,
            'message': f'Invitation {"resent" if email_sent else "failed to resend"} to {target["email"]}',
            'email_sent': email_sent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['PUT'])
@require_auth
def api_update_user(username):
    """Update a user (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
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
        if 'first_name' in data:
            USERS[username]['first_name'] = data.get('first_name', '')
        if 'last_name' in data:
            USERS[username]['last_name'] = data.get('last_name', '')
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
def api_delete_user(username):
    """Delete a user (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'SUPER_ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
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
