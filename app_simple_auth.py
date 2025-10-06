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
import json
import time
import re
from pathlib import Path
import threading
from typing import Dict
from datetime import datetime
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid

def extract_date_from_title(title):
    """
    Extract date from document title.
    Looks for patterns like MM-DD-YYYY or YYYY-MM-DD in the title.
    Returns the date as a string in YYYY-MM-DD format, or None if no valid date found.
    """
    if not title:
        return None
    
    # Pattern 1: MM-DD-YYYY (like 01-05-1938)
    pattern1 = r'(\d{1,2})-(\d{1,2})-(\d{4})'
    match1 = re.search(pattern1, title)
    if match1:
        month, day, year = match1.groups()
        # Only consider dates before 2025
        if int(year) < 2025:
            try:
                # Validate the date
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    # Pattern 2: YYYY-MM-DD (like 1933-08-24)
    pattern2 = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    match2 = re.search(pattern2, title)
    if match2:
        year, month, day = match2.groups()
        # Only consider dates before 2025
        if int(year) < 2025:
            try:
                # Validate the date
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    return None

def update_document_dates():
    """
    Update all documents with extracted dates from their titles.
    """
    try:
        # Get all documents
        documents = local_storage.list_documents()
        updated_count = 0
        
        for doc_id, metadata in documents:
            title = metadata.get('title', '')
            current_document_date = metadata.get('document_date')
            
            # Extract date from title
            extracted_date = extract_date_from_title(title)
            
            if extracted_date and extracted_date != current_document_date:
                # Update the document with the extracted date
                update_data = {
                    'document_date': extracted_date
                }
                
                success = local_storage.update_document(doc_id, update_data, actor="system")
                if success:
                    updated_count += 1
                    print(f"Updated document {doc_id} with date {extracted_date}")
        
        return updated_count
        
    except Exception as e:
        print(f"Error updating document dates: {e}")
        return 0
from dotenv import load_dotenv

# Load environment variables from ocr-auth/.env
env_path = Path(__file__).parent / 'ocr-auth' / '.env'
load_dotenv(env_path)

# Add scripts directory to path for local storage
sys.path.append(str(Path(__file__).parent / 'scripts'))
from scripts.local_storage import LocalOCRStorage
from scripts.fallback_ai_processor import FallbackAIProcessor
from scripts.simple_reference_service import simple_reference_service

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Enable CORS for React app with credentials support
CORS(app, 
     origins=['http://localhost:3000', 'http://localhost:3001'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

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
        'password_hash': '$2b$12$h5US3E2pV5I/Nof8e1FYmuuph05kK1Pw87myqL72hn1LTZolXPghy',
        'role': 'ADMIN',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(minutes=30)).isoformat()
    },
    'admin': {
        'username': 'admin',
        'email': 'admin@example.com',
        'first_name': 'Admin',
        'last_name': '',
        'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',  # Same as gzentall for testing
        'role': 'EDITOR',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(hours=1)).isoformat()
    },
    'user1': {
        'username': 'user1',
        'email': 'user1@example.com',
        'first_name': 'User',
        'last_name': 'One',
        'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',  # Same as gzentall for testing
        'role': 'VIEWER',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(hours=2)).isoformat()
    },
    'inactive_user': {
        'username': 'inactive_user',
        'email': 'inactive@example.com',
        'first_name': 'Inactive',
        'last_name': 'User',
        'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',  # Same as gzentall for testing
        'role': 'VIEWER',
        'is_active': False,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(days=30)).isoformat()
    },
    'editor1': {
        'username': 'editor1',
        'email': 'editor@example.com',
        'first_name': 'Sarah',
        'last_name': 'Johnson',
        'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',
        'role': 'EDITOR',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(days=1)).isoformat()
    },
    'viewer1': {
        'username': 'viewer1',
        'email': 'viewer@example.com',
        'first_name': 'Mike',
        'last_name': 'Chen',
        'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',
        'role': 'VIEWER',
        'is_active': True,
        'is_activated': True,
        'invitation_token': None,
        'invited_at': None,
        'activated_at': datetime.now().isoformat(),
        'last_login': (datetime.now() - timedelta(days=7)).isoformat()
    },
    'pending_user': {
        'username': 'pending_user',
        'email': 'pending@example.com',
        'first_name': 'Alex',
        'last_name': 'Smith',
        'password_hash': None,
        'role': 'VIEWER',
        'is_active': True,
        'is_activated': False,
        'invitation_token': 'abc123',
        'invited_at': (datetime.now() - timedelta(days=3)).isoformat(),
        'activated_at': None,
        'last_login': None
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

# API endpoints for React app authentication
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API login endpoint for React app."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        user = USERS.get(username)
        if user and user['is_active'] and user.get('is_activated', True):
            if user['password_hash'] and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update last login time
                user['last_login'] = datetime.now().isoformat()
                
                session['user_id'] = username
                session['user_role'] = user['role']
                
                return jsonify({
                    'success': True,
                    'user': {
                        'username': username,
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'role': user['role']
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        elif user and not user.get('is_activated', True):
            return jsonify({'success': False, 'error': 'Account not activated'}), 401
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """API logout endpoint for React app."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/me', methods=['GET'])
def api_get_user():
    """Get current user info."""
    if 'user_id' in session:
        username = session['user_id']
        user = USERS.get(username)
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'username': username,
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'role': user['role']
                }
            })
    
    return jsonify({'success': False, 'error': 'Not authenticated'}), 401

@app.route('/api/seed/users', methods=['POST'])
def seed_users():
    """Seed the database with initial users."""
    try:
        # This would typically be used in development/testing
        # In production, you'd want to restrict this endpoint
        
        # Reset USERS to initial state
        global USERS
        USERS = {
            'gzentall': {
                'username': 'gzentall',
                'email': 'gabe@zentall.com',
                'first_name': 'Gabe',
                'last_name': 'Zentall',
                'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',
                'role': 'EDITOR',
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
                'last_name': 'User',
                'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',
                'role': 'EDITOR',
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
                'password_hash': '$2b$12$YO4pCCazkUslOmRLWzyWxOyW/P8zZO6GwXi5msc.REpAFM2pyELD2',
                'role': 'VIEWER',
                'is_active': True,
                'is_activated': True,
                'invitation_token': None,
                'invited_at': None,
                'activated_at': datetime.now().isoformat()
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Users seeded successfully',
            'users': list(USERS.keys())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/token-audit')
def token_audit():
    """Design token audit page."""
    return render_template('token_audit.html')

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
    return render_template('browse.html', user=user, cache_bust=time.time())

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
    return render_template('browse.html', user=user, cache_bust=time.time())

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
    if user['role'] != 'ADMIN':
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

# -----------------------------
# Upload preflight (CORS) helpers
# -----------------------------
@app.route('/upload', methods=['OPTIONS'])
def upload_options():
    return ('', 200)

@app.route('/api/uploads', methods=['OPTIONS'])
def api_uploads_options():
    return ('', 200)

# -----------------------------
# Simple in-memory job status store
# -----------------------------
JOB_STATE: Dict[str, Dict] = {}

def set_job(job_id: str, **kwargs):
    current = JOB_STATE.get(job_id, {})
    current.update(kwargs)
    JOB_STATE[job_id] = current

def get_job(job_id: str) -> Dict:
    return JOB_STATE.get(job_id, {})

@app.route('/api/uploads', methods=['POST'])
def api_uploads():
    """Async upload endpoint: accept file, start background processing, return jobId."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

        # Persist upload to inbox with unique name
        unique_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"
        pdf_path = INBOX_DIR / unique_filename
        file.save(str(pdf_path))

        job_id = str(uuid.uuid4())
        set_job(job_id, state='queued', progress=0, message='Queued', filename=filename)

        def worker():
            try:
                set_job(job_id, state='processing', progress=5, message='OCR started')
                # Use existing synchronous pipeline pieces
                doc_id_local = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                relative_pdf_path = f"letters/inbox/{unique_filename}"
                success, stdout, stderr = run_ocr_script(relative_pdf_path, doc_id_local)
                if not success:
                    set_job(job_id, state='error', progress=0, message=f"OCR failed: {stderr[:160]}")
                    return

                set_job(job_id, state='translating', progress=85, message='Translating…')

                text_filename = f"{name}_{unique_id}.vision.txt"
                text_path = WORK_DIR / text_filename
                success, stdout, stderr = run_translation_script(text_path)
                translation_failed = not success

                # move translated file as in /upload and store document (reuse logic by calling upload_file flow bits)
                try:
                    translated_filename = f"{name}_{unique_id}.translated.txt"
                    translated_path = WORK_DIR / translated_filename
                    final_translated_path = EN_DIR / translated_filename
                    if translated_path.exists():
                        shutil.move(str(translated_path), str(final_translated_path))
                        with open(final_translated_path, 'r', encoding='utf-8') as f:
                            translated_content = html.unescape(f.read())
                    else:
                        translated_content = ''

                    original_text = ''
                    if text_path.exists():
                        with open(text_path, 'r', encoding='utf-8') as f:
                            original_text = f.read()

                    document_data = {
                        "title": f"{name} - {datetime.now().strftime('%Y-%m-%d')}",
                        "date_processed": datetime.now().isoformat(),
                        "source_language": "unknown",
                        "target_language": "en",
                        "original_text": original_text,
                        "translated_text": translated_content,
                        "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                        "summary": "",
                        "people": [],
                        "status": "New",
                        "filename": filename,
                    }
                    stored_id = local_storage.add_document(document_data, doc_id_local)
                    if translation_failed:
                        set_job(job_id, state='warning', progress=100, message=f'OCR done; translation failed (id={stored_id})')
                    else:
                        set_job(job_id, state='complete', progress=100, message=f'Done (id={stored_id})')
                except Exception as ee:
                    set_job(job_id, state='error', progress=0, message=f"Store failed: {ee}")
            except Exception as e:
                set_job(job_id, state='error', progress=0, message=f"{type(e).__name__}: {e}")
            finally:
                if pdf_path.exists():
                    try:
                        pdf_path.unlink()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

        return jsonify({'success': True, 'jobs': [{'id': job_id, 'filename': filename}]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/status', methods=['GET'])
def api_uploads_status():
    ids = [i for i in request.args.get('ids', '').split(',') if i]
    jobs = [{'id': jid, **get_job(jid)} for jid in ids]
    return jsonify({'success': True, 'jobs': jobs})

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

# -----------------------------
# Comments API
# -----------------------------
@app.errorhandler(400)
def handle_400(e):
    """Log 400 errors to diagnose comment POST issues."""
    print(f"[400 ERROR] path={request.path}, method={request.method}, CT={request.headers.get('Content-Type')}, body_len={request.content_length}")
    try:
        raw_body = request.get_data(as_text=True)
        print(f"[400 ERROR] body preview: {raw_body[:500]}")
    except Exception as ex:
        print(f"[400 ERROR] couldn't read body: {ex}")
    return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

@app.route('/documents/<doc_id>/comments', methods=['GET'])
@require_auth
def list_comments(doc_id):
    try:
        comments = local_storage.list_comments(doc_id)
        print(f"[list_comments] doc_id={doc_id}, type={type(comments)}, len={len(comments) if isinstance(comments, list) else 'N/A'}, first_50_chars={str(comments)[:50]}")
        response = { 'success': True, 'comments': comments }
        print(f"[list_comments] response={str(response)[:200]}")
        return jsonify(response)
    except Exception as e:
        print(f"[list_comments] ERROR: {e}")
        return jsonify({ 'success': False, 'error': str(e) }), 500

@app.route('/documents/<doc_id>/comments', methods=['POST'])
@require_auth
def add_comment(doc_id):
    print(f"[DEBUG] add_comment called: doc_id={doc_id}, method={request.method}, CT={request.headers.get('Content-Type')}")
    try:
        # Accept JSON, raw body JSON, or form; be permissive about keys
        text = ''
        data = request.get_json(silent=True)
        print(f"[DEBUG] get_json returned: {type(data)}, {data}")
        if isinstance(data, dict):
            text = (data.get('text') or data.get('comment') or '').strip()
        if not text:
            # Try raw body parse if Content-Type was unusual
            raw = request.get_data(as_text=True) or ''
            try:
                j = json.loads(raw) if raw else None
                if isinstance(j, dict):
                    text = (j.get('text') or j.get('comment') or '').strip()
            except Exception:
                pass
        if not text and request.form:
            text = (request.form.get('text') or request.form.get('comment') or '').strip()
        if not text and request.args:
            text = (request.args.get('text') or request.args.get('comment') or '').strip()
        if not text:
            # Debug context to diagnose client payload issues (safe output)
            print(f"comments POST 400: missing text. CT={request.headers.get('Content-Type')} len={request.content_length} raw={ (request.get_data(as_text=True) or '')[:200] }")
            return jsonify({ 'success': False, 'error': 'Text is required' }), 400
        user = USERS.get(session['user_id'], {})
        author = f"{user.get('first_name','') } { user.get('last_name','') }".strip() or user.get('username','User')
        print(f"comments POST begin: doc_id={doc_id} author={author} text_len={len(text)}")
        created = local_storage.add_comment(doc_id, text, author)
        if not created:
            print(f"comments POST fail: add_comment returned None for doc_id={doc_id}")
            return jsonify({ 'success': False, 'error': 'Failed to add comment' }), 400
        print(f"comments POST ok: id={created.get('id')} at={created.get('createdAt')}")
        return jsonify({ 'success': True, 'comment': created })
    except Exception as e:
        print(f"/documents/{doc_id}/comments POST error: {e}")
        return jsonify({ 'success': False, 'error': str(e) }), 500

@app.route('/test')
@require_auth
def test_endpoint():
    """Simple test endpoint to verify the server is working."""
    return jsonify({
        'message': 'Server is working!',
        'timestamp': str(uuid.uuid4())[:8]
    })

@app.route('/api/test-documents')
def test_documents():
    """Test endpoint for React app - returns sample documents without authentication."""
    try:
        # Try to get real documents if possible, otherwise return mock data
        try:
            documents = local_storage.list_documents()
            document_list = []
            for doc_id, metadata in documents:
                try:
                    # Get full document data to include sender/recipient
                    full_doc = local_storage.get_document(doc_id)
                    if full_doc:
                        # Merge metadata with full document data, prioritizing full document data
                        document_data = {
                            'id': doc_id,
                            **metadata,
                            **full_doc,  # This will override metadata with full document data
                            'id': doc_id  # Ensure ID is correct
                        }
                        print(f"[DEBUG] Document {doc_id}: sender={full_doc.get('sender')}, recipient={full_doc.get('recipient')}")
                    else:
                        # Fallback to metadata only
                        document_data = {
                            'id': doc_id,
                            **metadata
                        }
                        print(f"[DEBUG] Document {doc_id}: no full document data")
                    document_list.append(document_data)
                except Exception as e:
                    print(f"[ERROR] Failed to process document {doc_id}: {e}")
                    # Fallback to metadata only
                    document_data = {
                        'id': doc_id,
                        **metadata
                    }
                    document_list.append(document_data)
        except Exception as e:
            # Fallback to mock data
            document_list = [
                {
                    'id': '099-1933-08-24-ger',
                    'title': 'Personal Letter from 1933',
                    'summary': 'This appears to be a personal letter involving Zabalein Now, If Ellen, Haus...',
                    'page_count': 2,
                    'people': ['Elizabeth Zentall', 'Betty'],
                    'date': '2025-09-30',
                    'filename': '1933-08-24-ger-letter.pdf',
                    'sender': 'Elizabeth Zentall',
                    'recipient': 'Betty',
                    'status': 'Processed',
                },
                {
                    'id': '100-1945-03-15-eng',
                    'title': 'Business Correspondence',
                    'summary': 'Official business letter regarding wartime correspondence and family matters...',
                    'page_count': 1,
                    'people': ['John Smith', 'Mary Johnson'],
                    'date': '2025-09-29',
                    'filename': '1945-03-15-eng-business.pdf',
                    'sender': 'John Smith',
                    'recipient': 'Mary Johnson',
                    'status': 'Pending',
                },
                {
                    'id': '101-1950-12-01-fra',
                    'title': 'French Document',
                    'summary': 'Document in French language with official stamps and signatures...',
                    'page_count': 3,
                    'people': ['Pierre Dubois'],
                    'date': '2025-09-28',
                    'filename': '1950-12-01-fra-document.pdf',
                    'sender': 'Pierre Dubois',
                    'recipient': 'Unknown',
                    'status': 'Processed',
                },
            ]
        
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

@app.route('/api/extract-dates', methods=['POST'])
def extract_dates():
    """Extract dates from document titles and update the database."""
    try:
        updated_count = update_document_dates()
        return jsonify({
            'success': True,
            'message': f'Successfully updated {updated_count} documents with extracted dates',
            'updated_count': updated_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Simple probe endpoint to verify this Flask app is the one React is hitting
@app.route('/api/ping', methods=['GET'])
def api_ping():
    return jsonify({
        'success': True,
        'app': 'app_simple_auth.py',
        'time': datetime.now().isoformat()
    })

@app.route('/api/test-users', methods=['GET'])
def api_test_users():
    """Test endpoint to get users without authentication - for debugging."""
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
                'activated_at': user_data.get('activated_at'),
                'last_login': user_data.get('last_login')
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

@app.route('/api/test-document/<doc_id>')
def test_single_document(doc_id):
    """Test endpoint to get a single document with full data."""
    try:
        full_doc = local_storage.get_document(doc_id)
        if full_doc:
            return jsonify({
                'success': True,
                'document': full_doc
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/test-history/<doc_id>', methods=['GET'])
def test_history(doc_id):
    """Test endpoint to check history without authentication."""
    try:
        history_result = local_storage.get_document_history(
            doc_id=doc_id,
            page=1,
            limit=100
        )
        return jsonify(history_result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/documents/<doc_id>', methods=['GET'])
def api_get_document(doc_id):
    """Get a single document with all its data."""
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

@app.route('/api/references', methods=['GET'])
def api_get_references():
    """Get all references with their hierarchy and types."""
    try:
        ref_type = request.args.get('type')
        query = request.args.get('query')
        
        references = local_storage.list_references(ref_type=ref_type, query=query)
        return jsonify({
            'success': True,
            'references': references
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references-merge', methods=['POST'])
def api_merge_references():
    print("DEBUG: Merge endpoint called!")
    """Merge multiple references into one."""
    try:
        data = request.get_json()
        if not data or 'referenceIds' not in data or 'targetReferenceId' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: referenceIds, targetReferenceId'
            }), 400
        
        reference_ids = data['referenceIds']
        target_id = data['targetReferenceId']
        
        if not isinstance(reference_ids, list) or len(reference_ids) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 references required for merge'
            }), 400
        
        if target_id not in reference_ids:
            return jsonify({
                'success': False,
                'error': 'Target reference must be in the list of references to merge'
            }), 400
        
        # Get the target reference
        target_reference = local_storage.get_reference(target_id)
        if not target_reference:
            return jsonify({
                'success': False,
                'error': 'Target reference not found'
            }), 404
        
        # Get all references to merge
        references_to_merge = []
        for ref_id in reference_ids:
            if ref_id != target_id:  # Skip the target reference
                ref = local_storage.get_reference(ref_id)
                if ref:
                    references_to_merge.append(ref)
        
        # Merge aliases and notes
        all_aliases = set(target_reference.get('aliases', []))
        all_notes = [target_reference.get('notes', '')]
        
        for ref in references_to_merge:
            # Add aliases from other references
            if ref.get('aliases'):
                all_aliases.update(ref['aliases'])
            
            # Add notes from other references
            if ref.get('notes'):
                all_notes.append(ref['notes'])
        
        # Update the target reference with merged data
        updated_reference = local_storage.update_reference(
            ref_id=target_id,
            name=target_reference['name'],
            aliases=list(all_aliases),
            notes='\n\n'.join(filter(None, all_notes))
        )
        
        if updated_reference:
            # Hard delete the other references (remove from database)
            deleted_count = 0
            for ref in references_to_merge:
                try:
                    # Remove from metadata
                    if ref['id'] in local_storage.metadata.get("references", {}):
                        del local_storage.metadata["references"][ref['id']]
                        local_storage.save_metadata()
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting merged reference {ref['id']}: {e}")
            
            return jsonify({
                'success': True,
                'reference': updated_reference,
                'deletedCount': deleted_count,
                'message': f'Successfully merged {len(references_to_merge)} references into {target_reference["name"]}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update target reference'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references/<ref_id>', methods=['GET'])
def api_get_reference(ref_id):
    """Get a single reference by ID."""
    try:
        reference = local_storage.get_reference(ref_id)
        if reference:
            return jsonify({
                'success': True,
                'reference': reference
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Reference not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references', methods=['POST'])
def api_create_reference():
    """Create a new reference."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        required_fields = ['type', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        reference = local_storage.add_reference(
            ref_type=data['type'],
            name=data['name'],
            aliases=data.get('aliases', []),
            notes=data.get('notes')
        )
        
        if reference:
            return jsonify({
                'success': True,
                'reference': reference
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create reference'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references/<ref_id>', methods=['PUT'])
def api_update_reference(ref_id):
    """Update a reference."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        reference = local_storage.update_reference(
            ref_id=ref_id,
            name=data.get('name'),
            aliases=data.get('aliases'),
            notes=data.get('notes')
        )
        
        if reference:
            return jsonify({
                'success': True,
                'reference': reference
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Reference not found or update failed'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references/<ref_id>', methods=['DELETE'])
def api_delete_reference(ref_id):
    """Delete a reference."""
    try:
        success = local_storage.delete_reference(ref_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Reference deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Reference not found or delete failed'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references/<ref_id>/documents', methods=['GET'])
def api_list_documents_for_reference(ref_id):
    """List all documents that reference the given reference."""
    try:
        documents = local_storage.list_documents_for_reference(ref_id)
        return jsonify({
            'success': True,
            'documents': documents,
            'total': len(documents)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/references/bulk-delete', methods=['POST'])
def api_bulk_delete_references():
    """Delete multiple references."""
    try:
        data = request.get_json()
        if not data or 'referenceIds' not in data:
            return jsonify({
                'success': False,
                'error': 'No reference IDs provided'
            }), 400
        
        reference_ids = data['referenceIds']
        if not isinstance(reference_ids, list) or len(reference_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid reference IDs'
            }), 400
        
        deleted_count = 0
        failed_ids = []
        
        for ref_id in reference_ids:
            try:
                success = local_storage.delete_reference(ref_id)
                if success:
                    deleted_count += 1
                else:
                    failed_ids.append(ref_id)
            except Exception as e:
                failed_ids.append(ref_id)
                print(f"Error deleting reference {ref_id}: {e}")
        
        return jsonify({
            'success': True,
            'deletedCount': deleted_count,
            'failedIds': failed_ids,
            'message': f'Deleted {deleted_count} references'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-images/<doc_id>/<int:page_num>')
def test_document_image(doc_id, page_num):
    """Test endpoint for document images without authentication."""
    try:
        # Try to get the real image first
        try:
            work_dir = Path("letters/work")
            # Look for image files with the pattern: doc_id_page_XXX.png
            image_files = list(work_dir.glob(f"{doc_id}_page_{page_num:03d}.png"))
            if not image_files:
                # Try alternative patterns
                image_files = list(work_dir.glob(f"{doc_id}_page_{page_num}.png"))
            if not image_files:
                image_files = list(work_dir.glob(f"{doc_id}_page_{page_num}.jpg"))
            if not image_files:
                image_files = list(work_dir.glob(f"{doc_id}_page_{page_num}.jpeg"))
            
            if image_files:
                print(f"Found image: {image_files[0]}")
                return send_file(str(image_files[0]), mimetype='image/png')
            else:
                print(f"No image found for {doc_id} page {page_num}")
        except Exception as e:
            print(f"Error looking for image: {e}")
            pass
        
        # Fallback: return a simple SVG placeholder
        svg_content = f"""
        <svg width="800" height="1000" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="1000" fill="white" stroke="black" stroke-width="2"/>
            <text x="400" y="400" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="black">
                Document Image
            </text>
            <text x="400" y="450" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="gray">
                {doc_id}
            </text>
            <text x="400" y="480" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="gray">
                Page {page_num}
            </text>
        </svg>
        """
        
        return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reset-password')
def reset_password():
    """Reset password for testing - REMOVE IN PRODUCTION"""
    username = request.args.get('username', 'gzentall')
    new_password = request.args.get('password', 'password123')
    
    if username in USERS:
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        USERS[username]['password_hash'] = password_hash
        return jsonify({
            'success': True,
            'message': f'Password reset for {username}',
            'new_password': new_password
        })
    else:
        return jsonify({
            'success': False,
            'message': f'User {username} not found'
        })

@app.route('/debug-storage')
def debug_storage():
    """Debug storage status - REMOVE IN PRODUCTION"""
    try:
        import os
        storage_info = {
            'metadata_documents_count': len(local_storage.metadata['documents']),
            'documents_dir_exists': os.path.exists('ocr_storage/documents'),
            'documents_dir_files': 0,
            'sample_doc_ids': list(local_storage.metadata['documents'].keys())[:3]
        }
        
        if os.path.exists('ocr_storage/documents'):
            storage_info['documents_dir_files'] = len(os.listdir('ocr_storage/documents'))
        
        return jsonify(storage_info)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/create-sample-docs')
def create_sample_docs():
    """Create sample documents for testing - REMOVE IN PRODUCTION"""
    try:
        import os
        import json
        from datetime import datetime
        
        # Ensure directories exist
        os.makedirs('ocr_storage/documents', exist_ok=True)
        
        # Create sample documents
        sample_docs = [
            {
                'id': 'sample_doc_1',
                'title': 'Sample Letter 1 - 1938',
                'date': '1938-01-15',
                'source_language': 'German',
                'target_language': 'English',
                'summary': 'This is a sample letter from 1938. It contains important historical information about the period.',
                'people': ['John Smith', 'Maria Garcia'],
                'status': 'completed',
                'created_at': datetime.now().isoformat(),
                'page_count': 2
            },
            {
                'id': 'sample_doc_2', 
                'title': 'Sample Letter 2 - 1940',
                'date': '1940-05-20',
                'source_language': 'French',
                'target_language': 'English',
                'summary': 'Another sample letter from 1940. This one discusses family matters and local events.',
                'people': ['Robert Johnson', 'Anna Müller'],
                'status': 'completed',
                'created_at': datetime.now().isoformat(),
                'page_count': 1
            }
        ]
        
        created_count = 0
        for doc in sample_docs:
            doc_file = f"ocr_storage/documents/{doc['id']}.json"
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)
            
            # Add to metadata
            local_storage.metadata['documents'][doc['id']] = {
                'title': doc['title'],
                'date': doc['date'],
                'summary': doc['summary'][:100] + '...' if len(doc['summary']) > 100 else doc['summary'],
                'people_count': len(doc['people']),
                'page_count': doc['page_count'],
                'status': doc['status']
            }
            created_count += 1
        
        # Save metadata
        local_storage.save_metadata()
        
        return jsonify({
            'success': True,
            'message': f'Created {created_count} sample documents',
            'documents': [doc['id'] for doc in sample_docs]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

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


@app.route('/api/documents/<doc_id>/history')
# @require_auth  # Temporarily disabled for testing
def get_document_history(doc_id):
    """Get history for a specific document."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        event_type = request.args.get('eventType', 'all')
        
        # Get real history data from local storage
        history_result = local_storage.get_document_history(
            doc_id=doc_id,
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type
        )
        
        return jsonify(history_result)
        
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
        
        # Never allow comments to be overwritten via this endpoint
        if 'comments' in data:
            data.pop('comments', None)

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
        if any(key in data for key in ['title', 'summary', 'translated_text', 'original_text', 'people', 'sender', 'recipient', 'sender_location', 'recipient_location', 'date_processed']):
            data['status'] = 'Editing'
        
        # Get current user for audit log
        user_id = session.get('user_id', 'unknown')
        user = USERS.get(user_id, {})
        current_user = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user_id
        
        # Update the document
        success = local_storage.update_document(doc_id, data, regenerate_summary=regenerate_summary, actor=current_user)
        
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
        
        # Get current user for audit log
        user_id = session.get('user_id', 'unknown')
        user = USERS.get(user_id, {})
        current_user = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user_id
        
        # Update only the status
        success = local_storage.update_document(doc_id, {'status': status}, actor=current_user)
        
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


# -----------------------------
# Context Notes (Per-letter)
# -----------------------------

@app.route('/documents/<doc_id>/context', methods=['GET'])
def list_context_notes(doc_id):
    """List all context notes for a document."""
    try:
        notes = local_storage.list_context_notes(doc_id)
        return jsonify({
            'success': True,
            'items': notes,
            'total': len(notes)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/documents/<doc_id>/context', methods=['POST'])
def add_context_note(doc_id):
    """Add a context note to a document."""
    try:
        data = request.get_json()
        if not data or not data.get('note'):
            return jsonify({'success': False, 'error': 'Note is required'}), 400

        created = local_storage.add_context_note(doc_id, data['note'])
        if not created:
            return jsonify({'success': False, 'error': 'Failed to add context note'}), 400

        return jsonify({'success': True, 'item': created})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/context/<context_id>', methods=['PUT'])
def update_context_note(context_id):
    """Update a context note by ID."""
    try:
        data = request.get_json()
        if not data or not data.get('note'):
            return jsonify({'success': False, 'error': 'Note is required'}), 400

        updated = local_storage.update_context_note(context_id, data['note'])
        if not updated:
            return jsonify({'success': False, 'error': 'Context note not found'}), 404

        return jsonify({'success': True, 'item': updated})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/context/<context_id>', methods=['DELETE'])
def delete_context_note(context_id):
    """Delete a context note by ID."""
    try:
        deleted = local_storage.delete_context_note(context_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Context note not found'}), 404
        return jsonify({'success': True, 'message': 'Context note deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# User management API endpoints (SuperAdmin only)
@app.route('/api/users', methods=['GET'])
@require_auth
def api_list_users():
    """List all users (SuperAdmin only)."""
    user = USERS.get(session['user_id'])
    if user['role'] != 'ADMIN':
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
                'activated_at': user_data.get('activated_at'),
                'last_login': user_data.get('last_login')
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
    if user['role'] != 'ADMIN':
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
    if user['role'] != 'ADMIN':
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
    if user['role'] != 'ADMIN':
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
    if user['role'] != 'ADMIN':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        if username not in USERS:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        if USERS[username]['role'] == 'ADMIN':
            return jsonify({
                'success': False,
                'error': 'Cannot delete ADMIN user'
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


# -----------------------------
# Document-Reference Relations
# -----------------------------

@app.route('/api/documents/<doc_id>/references', methods=['GET'])
def list_document_references(doc_id):
    """List all references for a document."""
    try:
        references = local_storage.list_document_references(doc_id)
        return jsonify({
            'success': True,
            'references': references,
            'total': len(references)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/documents/<doc_id>/references', methods=['POST'])
def add_document_reference(doc_id):
    """Add a reference to a document with optional role."""
    try:
        data = request.get_json()
        if not data or not data.get('referenceId'):
            return jsonify({'success': False, 'error': 'referenceId is required'}), 400
        
        role = data.get('role')
        success = local_storage.add_reference_to_document(doc_id, data['referenceId'], role)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to add reference to document'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Reference {data["referenceId"]} added to document {doc_id}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/documents/<doc_id>/references', methods=['DELETE'])
def remove_document_reference(doc_id):
    """Remove a reference from a document."""
    try:
        data = request.get_json()
        if not data or not data.get('referenceId'):
            return jsonify({'success': False, 'error': 'referenceId is required'}), 400
        
        success = local_storage.remove_reference_from_document(doc_id, data['referenceId'])
        if not success:
            return jsonify({'success': False, 'error': 'Failed to remove reference from document'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Reference {data["referenceId"]} removed from document {doc_id}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------
# New Reference System (PostgreSQL)
# -----------------------------

@app.route('/api/v2/references', methods=['GET'])
def list_references_v2():
    """List all references with optional filtering (PostgreSQL version)."""
    try:
        ref_type = request.args.get('type')
        query = request.args.get('q') or request.args.get('query')
        
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            references = loop.run_until_complete(
                simple_reference_service.search_references(query=query, ref_type=ref_type)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'references': references,
            'total': len(references)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references/<ref_id>', methods=['GET'])
def get_reference_v2(ref_id):
    """Get a specific reference by ID (PostgreSQL version)."""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            reference = loop.run_until_complete(
                simple_reference_service.get_reference_by_id(ref_id)
            )
        finally:
            loop.close()
        
        if not reference:
            return jsonify({'success': False, 'error': 'Reference not found'}), 404
        
        return jsonify({
            'success': True,
            'reference': reference
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references', methods=['POST'])
def create_reference_v2():
    """Create a new reference (PostgreSQL version)."""
    try:
        data = request.get_json()
        if not data or not data.get('canonicalName') or not data.get('type'):
            return jsonify({'success': False, 'error': 'canonicalName and type are required'}), 400
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            reference = loop.run_until_complete(
                simple_reference_service.create_reference(
                    canonical_name=data['canonicalName'],
                    ref_type=data['type'],
                    notes=data.get('notes'),
                    initial_variants=data.get('initialVariants', [])
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'reference': reference
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references/<ref_id>', methods=['PUT'])
def update_reference_v2(ref_id):
    """Update a reference (PostgreSQL version)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        updates = {}
        if 'canonicalName' in data:
            updates['canonicalName'] = data['canonicalName']
        if 'type' in data:
            updates['type'] = data['type']
        if 'notes' in data:
            updates['notes'] = data['notes']
        if 'initialVariants' in data:
            updates['initialVariants'] = data['initialVariants']
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            reference = loop.run_until_complete(
                simple_reference_service.update_reference(ref_id, updates)
            )
        finally:
            loop.close()
        
        if not reference:
            return jsonify({'success': False, 'error': 'Reference not found'}), 404
        
        return jsonify({
            'success': True,
            'reference': reference
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references/<ref_id>', methods=['DELETE'])
def delete_reference_v2(ref_id):
    """Delete a reference (PostgreSQL version)."""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                simple_reference_service.delete_reference(ref_id)
            )
        finally:
            loop.close()
        
        if not success:
            return jsonify({'success': False, 'error': 'Reference not found or has linked documents'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Reference deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references/<source_id>/merge', methods=['POST'])
def merge_references_v2(source_id):
    """Merge source reference into target reference (PostgreSQL version)."""
    try:
        data = request.get_json()
        if not data or not data.get('targetId'):
            return jsonify({'success': False, 'error': 'targetId is required'}), 400
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                simple_reference_service.merge_references(source_id, data['targetId'])
            )
        finally:
            loop.close()
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to merge references'}), 400
        
        return jsonify({
            'success': True,
            'message': 'References merged successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/references/metrics', methods=['GET'])
def get_reference_metrics():
    """Get reference system metrics (PostgreSQL version)."""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            metrics = loop.run_until_complete(
                simple_reference_service.get_metrics()
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/references-page')
@require_auth
def references_page():
    """References management page."""
    user = USERS.get(session['user_id'])
    return render_template('references.html', user=user, cache_bust=time.time())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
