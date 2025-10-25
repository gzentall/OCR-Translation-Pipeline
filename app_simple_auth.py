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
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
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

# Enable CORS for Next.js frontend
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

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
    """Redirect to Next.js frontend."""
    return redirect('http://localhost:3000')

# API endpoints for Next.js frontend
@app.route('/api/documents')
@require_auth
def api_documents():
    """API endpoint to get all documents"""
    try:
        # Load documents from local storage
        storage = LocalOCRStorage()
        documents = []
        
        for doc_id, doc_meta in storage.metadata.get('documents', {}).items():
            documents.append({
                'id': doc_id,
                'title': doc_meta.get('title', 'Untitled'),
                'dateProcessed': doc_meta.get('date_processed', ''),
                'sourceLanguage': doc_meta.get('source_language', 'unknown'),
                'targetLanguage': doc_meta.get('target_language', 'en'),
                'fileSize': doc_meta.get('file_size', 0),
                'summary': doc_meta.get('summary', ''),
                'pageCount': doc_meta.get('page_count', 0),
                'createdAt': doc_meta.get('date_processed', ''),
                'updatedAt': doc_meta.get('date_processed', ''),
                'status': doc_meta.get('status', 'New')
            })
        
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/references')
@require_auth
def api_references():
    """API endpoint to get all references"""
    try:
        # Load references from local storage
        storage = LocalOCRStorage()
        references = []
        
        # Get people data (which is stored as references)
        for person_name, person_data in storage.metadata.get('people', {}).items():
            references.append({
                'id': person_name,
                'type': 'PERSON',
                'name': person_name,  # Changed from canonicalName
                'notes': person_data.get('context', ''),
                'aliases': person_data.get('aliases', []),  # Changed from variants
                'documentCount': len(person_data.get('documents', [])),
                'firstMentioned': person_data.get('first_mentioned', ''),  # Changed from createdAt
            })
        
        return jsonify({'references': references})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-references')
def api_test_references():
    """Test endpoint to get all references without authentication"""
    try:
        # Load references from local storage
        storage = LocalOCRStorage()
        references = []
        
        # Get people data (which is stored as references)
        for person_name, person_data in storage.metadata.get('people', {}).items():
            references.append({
                'id': person_name,
                'type': 'PERSON',
                'name': person_name,  # Changed from canonicalName
                'notes': person_data.get('context', ''),
                'aliases': person_data.get('aliases', []),  # Changed from variants
                'documentCount': len(person_data.get('documents', [])),
                'firstMentioned': person_data.get('first_mentioned', ''),  # Changed from createdAt
            })
        
        return jsonify({'references': references})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
@require_auth
def api_users():
    """API endpoint to get all users (admin only)"""
    user = USERS.get(session['user_id'])
    if not user or user.get('role') != 'SUPER_ADMIN':
        return jsonify({'error': 'Forbidden'}), 403
    
    try:
        users = []
        for user_id, user_data in USERS.items():
            users.append({
                'id': user_id,
                'username': user_data.get('username', ''),
                'email': user_data.get('email', ''),
                'role': user_data.get('role', 'USER'),
                'isActive': user_data.get('active', True),
                'createdAt': user_data.get('created_at', ''),
                'lastLogin': user_data.get('last_login', None)
            })
        
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-users')
def api_test_users():
    """Test endpoint to get all users without authentication"""
    try:
        users = []
        for user_id, user_data in USERS.items():
            users.append({
                'id': user_id,
                'username': user_data.get('username', ''),
                'email': user_data.get('email', ''),
                'role': user_data.get('role', 'USER'),
                'isActive': user_data.get('active', True),
                'createdAt': user_data.get('created_at', ''),
                'lastLogin': user_data.get('last_login', None)
            })
        
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@require_auth
def api_stats():
    """API endpoint to get system statistics"""
    try:
        storage = LocalOCRStorage()
        
        # Count documents
        total_documents = len(storage.metadata.get('documents', {}))
        
        # Count references
        total_references = len(storage.metadata.get('references', {}))
        
        # Count users
        total_users = len(USERS)
        
        # Count documents this month
        current_month = datetime.now().strftime('%Y-%m')
        documents_this_month = 0
        for doc_meta in storage.metadata.get('documents', {}).values():
            if doc_meta.get('date_processed', '').startswith(current_month):
                documents_this_month += 1
        
        # Get languages processed
        languages = set()
        for doc_meta in storage.metadata.get('documents', {}).values():
            source_lang = doc_meta.get('source_language', 'unknown')
            if source_lang != 'unknown':
                languages.add(source_lang)
        
        # Mock recent activity
        recent_activity = [
            {
                'id': '1',
                'type': 'document',
                'description': f'New document uploaded',
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': '2',
                'type': 'reference',
                'description': 'Reference updated',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return jsonify({
            'totalDocuments': total_documents,
            'totalReferences': total_references,
            'totalUsers': total_users,
            'documentsThisMonth': documents_this_month,
            'languagesProcessed': list(languages),
            'recentActivity': recent_activity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Test endpoint without authentication
@app.route('/api/test-documents')
def api_test_documents():
    """Test endpoint to get documents without authentication"""
    try:
        storage = LocalOCRStorage()
        documents = []
        
        for doc_id, doc_meta in storage.metadata.get('documents', {}).items():
            # Try to load the full document data from the individual JSON file
            doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
            if os.path.exists(doc_file_path):
                with open(doc_file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
            else:
                doc_data = doc_meta
            
            # Get people/references associated with this document
            people = []
            for person_name, person_data in storage.metadata.get('people', {}).items():
                if doc_id in person_data.get('documents', []):
                    people.append({
                        'id': person_name,
                        'name': person_data.get('aliases', [person_name])[0],
                        'aliases': person_data.get('aliases', [])
                    })
            
                # Extract location information
                from_location = ''
                to_location = ''
                if doc_data.get('sender_location'):
                    from_location = doc_data['sender_location'].get('display_name', '')
                if doc_data.get('recipient_location'):
                    to_location = doc_data['recipient_location'].get('display_name', '')
                
                # Fix swapped original/translated text fields
                original_text = doc_data.get('original_text', '')
                translated_text = doc_data.get('translated_text', '')
                
                # If original_text is very short (like "Save Changes") and translated_text is long,
                # they're likely swapped
                if len(original_text) < 50 and len(translated_text) > 100:
                    original_text, translated_text = translated_text, original_text
                
                documents.append({
                    'id': doc_id,
                    'title': doc_data.get('title', 'Untitled'),
                    'dateProcessed': doc_data.get('date_processed', ''),
                    'documentDate': doc_data.get('document_date', ''),
                    'sourceLanguage': doc_data.get('source_language', 'unknown'),
                    'targetLanguage': doc_data.get('target_language', 'en'),
                    'fileSize': doc_data.get('file_size', 0),
                    'summary': doc_data.get('summary', ''),
                    'pageCount': doc_data.get('page_count', 0),
                    'createdAt': doc_data.get('date_processed', ''),
                    'updatedAt': doc_data.get('date_processed', ''),
                    'status': doc_data.get('status', 'New'),
                    'originalText': original_text,
                    'translatedText': translated_text,
                    'sender': doc_data.get('sender', ''),
                    'recipient': doc_data.get('recipient', ''),
                    'fromLocation': from_location,
                    'toLocation': to_location,
                    'people': people
                })
        
        return jsonify({'documents': documents, 'count': len(documents)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>')
@require_auth
def api_get_document(doc_id):
    """API endpoint to get a specific document"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            # Fallback to metadata only
            doc_meta = storage.metadata.get('documents', {}).get(doc_id)
            if not doc_meta:
                return jsonify({'error': 'Document not found'}), 404
            doc_data = doc_meta
        
        # Get people/references associated with this document
        people = []
        for person_name, person_data in storage.metadata.get('people', {}).items():
            if doc_id in person_data.get('documents', []):
                people.append({
                    'id': person_name,
                    'name': person_data.get('aliases', [person_name])[0],
                    'aliases': person_data.get('aliases', [])
                })
        
        # Extract location information
        from_location = ''
        to_location = ''
        if doc_data.get('sender_location'):
            from_location = doc_data['sender_location'].get('display_name', '')
        if doc_data.get('recipient_location'):
            to_location = doc_data['recipient_location'].get('display_name', '')
        
        # Fix swapped original/translated text fields
        original_text = doc_data.get('original_text', '')
        translated_text = doc_data.get('translated_text', '')
        
        # If original_text is very short (like "Save Changes") and translated_text is long,
        # they're likely swapped
        if len(original_text) < 50 and len(translated_text) > 100:
            original_text, translated_text = translated_text, original_text
        
        document = {
            'id': doc_id,
            'title': doc_data.get('title', 'Untitled'),
            'dateProcessed': doc_data.get('date_processed', ''),
            'documentDate': doc_data.get('document_date', ''),
            'sourceLanguage': doc_data.get('source_language', 'unknown'),
            'targetLanguage': doc_data.get('target_language', 'en'),
            'fileSize': doc_data.get('file_size', 0),
            'summary': doc_data.get('summary', ''),
            'pageCount': doc_data.get('page_count', 0),
            'createdAt': doc_data.get('date_processed', ''),
            'updatedAt': doc_data.get('date_processed', ''),
            'status': doc_data.get('status', 'New'),
            'originalText': original_text,
            'translatedText': translated_text,
            'sender': doc_data.get('sender', ''),
            'recipient': doc_data.get('recipient', ''),
            'fromLocation': from_location,
            'toLocation': to_location,
            'people': people
        }
        
        return jsonify({'document': document})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>', methods=['PUT'])
@require_auth
def api_update_document(doc_id):
    """API endpoint to update a specific document"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            # Fallback to metadata only
            doc_meta = storage.metadata.get('documents', {}).get(doc_id)
            if not doc_meta:
                return jsonify({'error': 'Document not found'}), 404
            doc_data = doc_meta
        
        data = request.get_json()
        
        # Update document data
        if 'summary' in data:
            doc_data['summary'] = data['summary']
        if 'dateProcessed' in data:
            doc_data['date_processed'] = data['dateProcessed']
        if 'documentDate' in data:
            doc_data['document_date'] = data['documentDate']
        if 'originalText' in data:
            doc_data['original_text'] = data['originalText']
        if 'translatedText' in data:
            doc_data['translated_text'] = data['translatedText']
        if 'sender' in data:
            doc_data['sender'] = data['sender']
        if 'recipient' in data:
            doc_data['recipient'] = data['recipient']
        if 'fromLocation' in data:
            doc_data['from_location'] = data['fromLocation']
        if 'toLocation' in data:
            doc_data['to_location'] = data['toLocation']
        if 'status' in data:
            doc_data['status'] = data['status']
        
        # Save updated data to individual JSON file if it exists
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        # Also update metadata
        storage.metadata['documents'][doc_id] = doc_data
        storage._save_metadata()
        
        return jsonify({'success': True, 'message': 'Document updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>')
def api_test_get_document(doc_id):
    """Test endpoint to get a specific document without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            # Fallback to metadata only
            doc_meta = storage.metadata.get('documents', {}).get(doc_id)
            if not doc_meta:
                return jsonify({'error': 'Document not found'}), 404
            doc_data = doc_meta
        
        # Get people/references associated with this document
        people = []
        for person_name, person_data in storage.metadata.get('people', {}).items():
            if doc_id in person_data.get('documents', []):
                people.append({
                    'id': person_name,
                    'name': person_data.get('aliases', [person_name])[0],
                    'aliases': person_data.get('aliases', [])
                })
        
        # Extract location information
        from_location = ''
        to_location = ''
        if doc_data.get('sender_location'):
            from_location = doc_data['sender_location'].get('display_name', '')
        if doc_data.get('recipient_location'):
            to_location = doc_data['recipient_location'].get('display_name', '')
        
        # Fix swapped original/translated text fields
        original_text = doc_data.get('original_text', '')
        translated_text = doc_data.get('translated_text', '')
        
        # If original_text is very short (like "Save Changes") and translated_text is long,
        # they're likely swapped
        if len(original_text) < 50 and len(translated_text) > 100:
            original_text, translated_text = translated_text, original_text
        
        document = {
            'id': doc_id,
            'title': doc_data.get('title', 'Untitled'),
            'dateProcessed': doc_data.get('date_processed', ''),
            'documentDate': doc_data.get('document_date', ''),
            'sourceLanguage': doc_data.get('source_language', 'unknown'),
            'targetLanguage': doc_data.get('target_language', 'en'),
            'fileSize': doc_data.get('file_size', 0),
            'summary': doc_data.get('summary', ''),
            'pageCount': doc_data.get('page_count', 0),
            'createdAt': doc_data.get('date_processed', ''),
            'updatedAt': doc_data.get('date_processed', ''),
            'status': doc_data.get('status', 'New'),
            'originalText': original_text,
            'translatedText': translated_text,
            'sender': doc_data.get('sender', ''),
            'recipient': doc_data.get('recipient', ''),
            'fromLocation': from_location,
            'toLocation': to_location,
            'people': people
        }
        
        return jsonify(document)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>', methods=['PUT'])
def api_test_update_document(doc_id):
    """Test endpoint to update a specific document without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            # Fallback to metadata only
            doc_meta = storage.metadata.get('documents', {}).get(doc_id)
            if not doc_meta:
                return jsonify({'error': 'Document not found'}), 404
            doc_data = doc_meta
        
        data = request.get_json()
        
        # Update document data
        if 'summary' in data:
            doc_data['summary'] = data['summary']
        if 'dateProcessed' in data:
            doc_data['date_processed'] = data['dateProcessed']
        if 'documentDate' in data:
            doc_data['document_date'] = data['documentDate']
        if 'originalText' in data:
            doc_data['original_text'] = data['originalText']
        if 'translatedText' in data:
            doc_data['translated_text'] = data['translatedText']
        if 'sender' in data:
            doc_data['sender'] = data['sender']
        if 'recipient' in data:
            doc_data['recipient'] = data['recipient']
        if 'fromLocation' in data:
            doc_data['from_location'] = data['fromLocation']
        if 'toLocation' in data:
            doc_data['to_location'] = data['toLocation']
        if 'status' in data:
            doc_data['status'] = data['status']
        
        # Save updated data to individual JSON file if it exists
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        # Also update metadata
        storage.metadata['documents'][doc_id] = doc_data
        storage._save_metadata()
        
        return jsonify({'success': True, 'message': 'Document updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>/comments')
def api_test_get_document_comments(doc_id):
    """Test endpoint to get document comments without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            return jsonify({'comments': [], 'count': 0})
        
        # Get comments from document data
        comments = doc_data.get('comments', [])
        
        return jsonify({'comments': comments, 'count': len(comments)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>/comments', methods=['POST'])
def api_test_add_document_comment(doc_id):
    """Test endpoint to add a comment to a document without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.get_json()
        comment_text = data.get('text', '').strip()
        
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400
        
        # Create new comment
        new_comment = {
            'id': f'c{len(doc_data.get("comments", [])) + 1}',
            'author': data.get('author', 'Current User'),
            'text': comment_text,
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Add comment to document data
        if 'comments' not in doc_data:
            doc_data['comments'] = []
        doc_data['comments'].append(new_comment)
        
        # Save updated data to individual JSON file
        with open(doc_file_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        # Also update metadata
        storage.metadata['documents'][doc_id] = doc_data
        storage._save_metadata()
        
        return jsonify({'success': True, 'comment': new_comment})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>/images/<int:page>')
@require_auth
def api_get_document_image(doc_id, page):
    """API endpoint to get document image"""
    try:
        storage = LocalOCRStorage()
        doc_meta = storage.metadata.get('documents', {}).get(doc_id)
        
        if not doc_meta:
            return jsonify({'error': 'Document not found'}), 404
        
        # Try to find the image file
        image_path = storage.get_document_image_path(doc_id, page)
        
        if image_path and os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            # Return a placeholder image or 404
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>/images/<int:page>')
def api_test_get_document_image(doc_id, page):
    """Test API endpoint to get document image without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to find the image file
        image_path = storage.get_document_image_path(doc_id, page)
        
        if image_path and os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            # Return a placeholder image or 404
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/people')
@require_auth
def api_get_people():
    """API endpoint to get all people/references"""
    try:
        storage = LocalOCRStorage()
        people = []
        
        for person_name, person_data in storage.metadata.get('people', {}).items():
            people.append({
                'id': person_name,
                'name': person_data.get('aliases', [person_name])[0],
                'aliases': person_data.get('aliases', []),
                'firstMentioned': person_data.get('first_mentioned', ''),
                'documentCount': len(person_data.get('documents', []))
            })
        
        return jsonify({'people': people, 'count': len(people)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-people')
def api_test_get_people():
    """Test endpoint to get all people/references without authentication"""
    try:
        storage = LocalOCRStorage()
        people = []
        
        for person_name, person_data in storage.metadata.get('people', {}).items():
            people.append({
                'id': person_name,
                'name': person_data.get('aliases', [person_name])[0],
                'aliases': person_data.get('aliases', []),
                'firstMentioned': person_data.get('first_mentioned', ''),
                'documentCount': len(person_data.get('documents', []))
            })
        
        return jsonify({'people': people, 'count': len(people)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<doc_id>/history')
@require_auth
def api_get_document_history(doc_id):
    """API endpoint to get document history/audit events"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            return jsonify({'error': 'Document not found'}), 404
        
        # Create mock history events based on document data
        history_events = []
        
        # Document creation event
        if doc_data.get('date_processed'):
            history_events.append({
                'id': f'create_{doc_id}',
                'action': 'DOCUMENT_CREATE',
                'actor': 'System',
                'description': f'Document created (VERSION 1)',
                'fieldsChanged': ['title', 'summary', 'document_date'],
                'timestamp': doc_data['date_processed'],
                'metadata': {
                    'version': 1,
                    'source': 'upload'
                }
            })
        
        # Document modification events (mock based on status changes)
        if doc_data.get('status') and doc_data['status'] != 'New':
            history_events.append({
                'id': f'modify_{doc_id}',
                'action': 'DOCUMENT_UPDATE',
                'actor': 'Gabe Zentall',
                'description': f'Modified the summary',
                'fieldsChanged': ['summary'],
                'timestamp': doc_data.get('date_processed', ''),
                'metadata': {
                    'status': doc_data['status']
                }
            })
        
        # People addition event (if people exist)
        if doc_data.get('people') and len(doc_data['people']) > 0:
            history_events.append({
                'id': f'people_{doc_id}',
                'action': 'PEOPLE_ADD',
                'actor': 'Gabe Zentall',
                'description': f'Added people to this document',
                'fieldsChanged': ['people'],
                'timestamp': doc_data.get('date_processed', ''),
                'metadata': {
                    'people': doc_data['people']
                }
            })
        
        # Sort events by timestamp (newest first)
        history_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'events': history_events, 'count': len(history_events)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-documents/<doc_id>/history')
def api_test_get_document_history(doc_id):
    """Test endpoint to get document history without authentication"""
    try:
        storage = LocalOCRStorage()
        
        # Try to load the full document data from the individual JSON file
        doc_file_path = os.path.join(storage.documents_dir, f"{doc_id}.json")
        if os.path.exists(doc_file_path):
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
        else:
            return jsonify({'error': 'Document not found'}), 404
        
        # Create mock history events based on document data
        history_events = []
        
        # Document creation event
        if doc_data.get('date_processed'):
            history_events.append({
                'id': f'create_{doc_id}',
                'action': 'DOCUMENT_CREATE',
                'actor': 'System',
                'description': f'Document created (VERSION 1)',
                'fieldsChanged': ['title', 'summary', 'document_date'],
                'timestamp': doc_data['date_processed'],
                'metadata': {
                    'version': 1,
                    'source': 'upload'
                }
            })
        
        # Document modification events (mock based on status changes)
        if doc_data.get('status') and doc_data['status'] != 'New':
            history_events.append({
                'id': f'modify_{doc_id}',
                'action': 'DOCUMENT_UPDATE',
                'actor': 'Gabe Zentall',
                'description': f'Modified the summary',
                'fieldsChanged': ['summary'],
                'timestamp': doc_data.get('date_processed', ''),
                'metadata': {
                    'status': doc_data['status']
                }
            })
        
        # People addition event (if people exist)
        if doc_data.get('people') and len(doc_data['people']) > 0:
            history_events.append({
                'id': f'people_{doc_id}',
                'action': 'PEOPLE_ADD',
                'actor': 'Gabe Zentall',
                'description': f'Added people to this document',
                'fieldsChanged': ['people'],
                'timestamp': doc_data.get('date_processed', ''),
                'metadata': {
                    'people': doc_data['people']
                }
            })
        
        # Sort events by timestamp (newest first)
        history_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'events': history_events, 'count': len(history_events)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-form')
@require_auth
def upload_form():
    """Serve the upload form for modal loading."""
    return render_template('upload_modal.html')

@app.route('/browse')
@require_auth
def browse():
    """Redirect to Next.js frontend."""
    return redirect('http://localhost:3000')

@app.route('/stats-page')
@require_auth
def stats_page():
    """Redirect to Next.js frontend."""
    return redirect('http://localhost:3000')

@app.route('/people-page')
@require_auth
def people_page():
    """Redirect to Next.js frontend."""
    return redirect('http://localhost:3000/references')

@app.route('/users-page')
@require_auth
def users_page():
    """Redirect to Next.js frontend."""
    return redirect('http://localhost:3000/users')

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
@require_auth
def get_document_history(doc_id):
    """Get history for a specific document."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        event_type = request.args.get('eventType', 'all')
        
        # For now, return mock history data
        # In a real implementation, you would query your audit log database
        mock_history = [
            {
                'id': '1',
                'timestamp': '2025-01-27T10:30:00Z',
                'description': 'Gabe Zentall created "Sample Document"',
                'action': 'DOCUMENT_CREATE',
                'actor': {
                    'id': 'user1',
                    'username': 'gzentall',
                    'email': 'gzentall@example.com'
                },
                'metadata': {
                    'changes': ['title', 'summary'],
                    'timestamp': '2025-01-27T10:30:00Z'
                }
            },
            {
                'id': '2',
                'timestamp': '2025-01-27T10:35:00Z',
                'description': 'Gabe Zentall modified "Sample Document"',
                'action': 'DOCUMENT_UPDATE',
                'actor': {
                    'id': 'user1',
                    'username': 'gzentall',
                    'email': 'gzentall@example.com'
                },
                'metadata': {
                    'changes': ['summary'],
                    'previousTitle': 'Sample Document',
                    'newTitle': 'Sample Document'
                }
            },
            {
                'id': '3',
                'timestamp': '2025-01-27T10:40:00Z',
                'description': 'System processed "Sample Document"',
                'action': 'DOCUMENT_PROCESS',
                'actor': None,
                'metadata': {
                    'processingType': 'OCR',
                    'timestamp': '2025-01-27T10:40:00Z'
                }
            }
        ]
        
        # Apply filters
        filtered_history = mock_history
        
        if start_date:
            filtered_history = [h for h in filtered_history if h['timestamp'] >= start_date]
        if end_date:
            filtered_history = [h for h in filtered_history if h['timestamp'] <= end_date + 'T23:59:59Z']
        if event_type != 'all':
            filtered_history = [h for h in filtered_history if h['action'] == event_type]
        
        # Apply pagination
        total = len(filtered_history)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_history = filtered_history[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_history,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': (total + limit - 1) // limit
            }
        })
        
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


# -----------------------------
# References (with stable IDs) - COMMENTED OUT DUE TO DUPLICATE ROUTE
# -----------------------------

# @app.route('/api/references', methods=['GET'])
# async def list_references():
#     """List all references with optional filtering."""
#     try:
#         ref_type = request.args.get('type')
#         query = request.args.get('q') or request.args.get('query')
#         
#         references = await simple_reference_service.search_references(query=query, ref_type=ref_type)
#         return jsonify({
#             'success': True,
#             'references': references,
#             'total': len(references)
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/api/references/<ref_id>', methods=['GET'])
# def get_reference(ref_id):
#     """Get a specific reference by ID."""
#     try:
#         reference = local_storage.get_reference(ref_id)
#         if not reference:
#             return jsonify({'success': False, 'error': 'Reference not found'}), 404
#         
#         return jsonify({
#             'success': True,
#             'reference': reference
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/api/references', methods=['POST'])
# def create_reference():
#     """Create a new reference."""
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'success': False, 'error': 'No data provided'}), 400
#         
#         ref_type = data.get('type')
#         name = data.get('name')
#         aliases = data.get('aliases', [])
#         notes = data.get('notes', '')
#         
#         if not ref_type or not name:
#             return jsonify({'success': False, 'error': 'Type and name are required'}), 400
#         
#         reference = local_storage.add_reference(ref_type, name, aliases, notes)
#         if not reference:
#             return jsonify({'success': False, 'error': 'Failed to create reference'}), 400
#         
#         return jsonify({
#             'success': True,
#             'reference': reference
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/api/references/<ref_id>', methods=['PUT'])
# def update_reference(ref_id):
#     """Update a reference."""
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'success': False, 'error': 'No data provided'}), 400
#         
#         name = data.get('name')
#         aliases = data.get('aliases')
#         notes = data.get('notes')
#         
#         reference = local_storage.update_reference(ref_id, name, aliases, notes)
#         if not reference:
#             return jsonify({'success': False, 'error': 'Reference not found'}), 404
#         
#         return jsonify({
#             'success': True,
#             'reference': reference
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/api/references/<ref_id>', methods=['DELETE'])
# def delete_reference(ref_id):
#     """Delete a reference."""
#     try:
#         success = local_storage.delete_reference(ref_id)
#         if not success:
#             return jsonify({'success': False, 'error': 'Reference not found'}), 404
#         
#         return jsonify({
#             'success': True,
#             'message': 'Reference deleted successfully'
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/api/references/<source_id>/merge', methods=['POST'])
# def merge_references(source_id):
#     """Merge a source reference into a target reference."""
#     try:
#         data = request.get_json()
#         if not data or not data.get('targetId'):
#             return jsonify({'success': False, 'error': 'targetId is required'}), 400
#         
#         success = local_storage.merge_references(source_id, data['targetId'])
#         if not success:
#             return jsonify({'success': False, 'error': 'Merge failed'}), 400
#         
#         return jsonify({
#             'success': True,
#             'message': f'Reference {source_id} merged into {data["targetId"]}'
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500


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
    app.run(debug=True, host='0.0.0.0', port=port)
