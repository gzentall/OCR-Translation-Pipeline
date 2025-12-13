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
import sys
import secrets
import bcrypt
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_file, redirect, session, make_response
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta

# Load environment variables from .env file
load_dotenv()

# Add scripts directory to path for local storage
sys.path.append(str(Path(__file__).parent / 'scripts'))
from scripts.local_storage import LocalOCRStorage
from scripts.fallback_ai_processor import FallbackAIProcessor
from scripts.geoapify_client import GeoapifyClient
from scripts.envelope_extractor import EnvelopeExtractor
from scripts.database import DatabaseSession, User, Document, Reference, ReferenceType, UserRole, Notification
from sqlalchemy import text
from scripts.email_service import send_user_invite, send_mention_notification, send_rejection_notification
from botocore.exceptions import ClientError
# Import enhanced processing components
from scripts.batch_processor import BatchOCRProcessor
from scripts.ai_processor import AIProcessor
from scripts.translate_google import translate_text
from scripts.extract_references import ReferenceExtractor
from scripts.extract_references_enhanced import extract_references_with_context
import json
import openai

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size

# Security configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-12345-change-in-production')
if os.getenv('FLASK_ENV') == 'production' and SECRET_KEY == 'dev-secret-key-12345-change-in-production':
    raise ValueError("SECRET_KEY must be set in production! Set it in .env or environment variables.")

app.secret_key = SECRET_KEY
is_production = os.getenv('FLASK_ENV') == 'production'

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = is_production  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['SESSION_COOKIE_NAME'] = 'ocr_session'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000 if is_production else 0  # 1 year cache in prod

# Trust proxy headers in production (for session cookies behind load balancers)
if is_production:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    print("✅ ProxyFix middleware enabled for production")

print(f"🔧 Session config: SECURE={app.config['SESSION_COOKIE_SECURE']}, HTTPONLY={app.config['SESSION_COOKIE_HTTPONLY']}, SAMESITE={app.config['SESSION_COOKIE_SAMESITE']}")

# Project paths
PROJECT_ROOT = Path(__file__).parent
INBOX_DIR = PROJECT_ROOT / "letters" / "inbox"
WORK_DIR = PROJECT_ROOT / "letters" / "work"
OUT_DIR = PROJECT_ROOT / "letters" / "out"
EN_DIR = OUT_DIR / "en"

# Ensure directories exist
for directory in [INBOX_DIR, WORK_DIR, OUT_DIR, EN_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize local storage, AI processor, Geoapify client, and envelope extractor
local_storage = LocalOCRStorage()
try:
    ai_processor = AIProcessor()
except Exception as e:
    print(f"Warning: Could not initialize AIProcessor, using fallback: {e}")
    ai_processor = FallbackAIProcessor()
geoapify_client = GeoapifyClient()
envelope_extractor = EnvelopeExtractor()

# Initialize enhanced processing components
context_file = PROJECT_ROOT / "context" / "reference_data.json"
context_data = {}
if context_file.exists():
    try:
        with open(context_file, 'r') as f:
            context_data = json.load(f)
        print(f"✅ Loaded context file with {len(context_data)} entries")
    except Exception as e:
        print(f"⚠️  Could not load context file: {e}")

# Initialize batch processor and reference extractor (lazy initialization)
batch_processor = None
ref_extractor = None

def get_batch_processor():
    """Get or create BatchOCRProcessor instance."""
    global batch_processor
    if batch_processor is None:
        batch_processor = BatchOCRProcessor(provider='openai', context_file=str(context_file))
    return batch_processor

def get_ref_extractor():
    """Get or create ReferenceExtractor instance."""
    global ref_extractor
    if ref_extractor is None:
        ref_extractor = ReferenceExtractor()
    return ref_extractor

# R2 URL Cache - Cache presigned URLs for 50 minutes (they're valid for 1 hour)
# Structure: {image_key: (url, expiry_timestamp)}
_r2_url_cache = {}
_r2_cache_ttl = 3000  # 50 minutes in seconds

def get_cached_r2_url(image_key):
    """Get a cached R2 presigned URL if still valid, otherwise None."""
    if image_key in _r2_url_cache:
        url, expiry = _r2_url_cache[image_key]
        if time.time() < expiry:
            return url
        else:
            # Expired, remove from cache
            del _r2_url_cache[image_key]
    return None

def cache_r2_url(image_key, url):
    """Cache an R2 presigned URL with expiry timestamp."""
    expiry = time.time() + _r2_cache_ttl
    _r2_url_cache[image_key] = (url, expiry)

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


# Authentication and Authorization Helpers
def get_current_user():
    """Get current user from session"""
    if not session.get('authenticated') or not session.get('user_id'):
        return None
    
    with DatabaseSession() as db:
        user = db.query(User).filter_by(id=session.get('user_id'), is_active=True).first()
        return user


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # Check if this is an API endpoint (starts with /api)
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def require_role(min_role='Viewer'):
    """
    Decorator to require a minimum role level.
    Role hierarchy: Admin > Editor > Viewer
    
    Usage: @require_role('Admin') or @require_role('Editor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Debug logging
            endpoint = request.endpoint or 'unknown'
            print(f"[AUTH] Endpoint: {endpoint}, Required role: {min_role}")
            print(f"[AUTH] Session authenticated: {session.get('authenticated')}")
            print(f"[AUTH] Session user_id: {session.get('user_id')}")
            print(f"[AUTH] Session role: {session.get('role')}")
            print(f"[AUTH] Session keys: {list(session.keys())}")
            
            if not session.get('authenticated'):
                print(f"[AUTH] Authentication failed - not authenticated")
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            user_role_str = session.get('role')
            if not user_role_str:
                print(f"[AUTH] Authorization failed - no role assigned")
                return jsonify({'success': False, 'error': 'No role assigned'}), 403
            
            # Convert string role to UserRole enum
            try:
                user_role = UserRole[user_role_str.upper()]
                required_role = UserRole[min_role.upper()]
                print(f"[AUTH] User role: {user_role}, Required: {required_role}")
            except (KeyError, AttributeError) as e:
                print(f"[AUTH] Invalid role error: {e}")
                return jsonify({'success': False, 'error': 'Invalid role'}), 403
            
            # Check if user has sufficient permissions
            if not user_role >= required_role:
                print(f"[AUTH] Insufficient permissions: {user_role} < {required_role}")
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            
            print(f"[AUTH] Authorization successful")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def format_relative_time(dt):
    """Format a datetime as relative time (e.g., '2 hours ago')
    
    Uses total time difference for accurate calculations instead of component-wise differences.
    """
    if not dt:
        return "Never signed in"
    
    now = datetime.utcnow()
    
    # Handle both timezone-aware and naive datetimes
    if dt.tzinfo is not None:
        # Convert timezone-aware datetime to UTC naive
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    # Calculate total time difference
    delta = now - dt
    
    # Handle negative differences (future dates) - shouldn't happen but be safe
    if delta.total_seconds() < 0:
        return "Just now"
    
    total_seconds = delta.total_seconds()
    
    # Convert to appropriate units based on total difference
    if total_seconds < 60:
        return "Just now"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif total_seconds < 2592000:  # Less than 30 days (approximate month)
        days = int(total_seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        # For months and years, use relativedelta to handle variable month lengths
        diff = relativedelta(now, dt)
        if diff.years > 0:
            return f"{diff.years} year{'s' if diff.years != 1 else ''} ago"
        elif diff.months > 0:
            return f"{diff.months} month{'s' if diff.months != 1 else ''} ago"
        else:
            # Fallback to days
            days = int(total_seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"


@app.route('/')
@require_auth
def index():
    """Serve the main application page (Documents tab)."""
    # Get full user info from database including avatar_url
    user_id = session.get('user_id')
    user = None
    try:
        with DatabaseSession() as db:
            db_user = db.query(User).filter_by(id=user_id).first()
            if db_user:
                user = db_user.to_dict()
            else:
                user = {
                    'id': user_id,
                    'username': session.get('username'),
                    'role': session.get('role')
                }
    except Exception as e:
        print(f"[ERROR] Failed to fetch user from database: {e}")
        # Fall back to session data
        user = {
            'id': user_id,
            'username': session.get('username'),
            'role': session.get('role'),
            'first_name': session.get('user_first_name', ''),
            'last_name': session.get('user_last_name', '')
        }
    print(f"DEBUG: User authenticated - {user}")  # Debug log
    
    return render_template('browse.html', user=user)

@app.route('/upload-form')
def upload_form():
    """Serve the upload form for modal loading."""
    return render_template('upload_modal.html')


@app.route('/browse')
def browse():
    """Serve the main application interface."""
    # Get full user info from database including avatar_url
    user = None
    if session.get('authenticated'):
        user_id = session.get('user_id')
        try:
            with DatabaseSession() as db:
                db_user = db.query(User).filter_by(id=user_id).first()
                if db_user:
                    user = db_user.to_dict()
                else:
                    user = {
                        'id': user_id,
                        'username': session.get('username'),
                        'role': session.get('role')
                    }
        except Exception as e:
            print(f"[ERROR] Failed to fetch user from database: {e}")
            user = {
                'id': user_id,
                'username': session.get('username'),
                'role': session.get('role')
            }
    return render_template('browse.html', user=user)


@app.route('/stats-page')
def stats_page():
    """Serve the statistics page interface."""
    return render_template('stats.html')


@app.route('/people-page')
def people_page():
    """Serve the people management page."""
    return render_template('people.html')

@app.route('/users-page')
@require_auth
def users_page():
    """Serve the user management page."""
    # Get user info from session
    user = None
    if session.get('authenticated'):
        user = {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
    response = make_response(render_template('users.html', user=user, cache_bust=datetime.utcnow().timestamp()))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/logout')
def logout():
    """Logout user and redirect to login page."""
    # Clear session data
    session.clear()
    return redirect('/login')


# ===== Profile API =====

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user's profile."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            return jsonify({
                'success': True,
                'profile': user.to_dict()
            })
    except Exception as e:
        print(f"[ERROR] Failed to get profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update current user's profile."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Update allowed fields
            if 'first_name' in data and data['first_name']:
                user.first_name = data['first_name'].strip()
            
            if 'last_name' in data and data['last_name']:
                user.last_name = data['last_name'].strip()
            
            if 'username' in data:
                new_username = data['username'].strip() if data['username'] else None
                if new_username:
                    # Check if username is already taken
                    existing = db.query(User).filter(User.username == new_username, User.id != user_id).first()
                    if existing:
                        return jsonify({'success': False, 'error': 'Username already taken'}), 400
                user.username = new_username
            
            if 'email' in data and data['email']:
                new_email = data['email'].strip().lower()
                # Check if email is already taken
                existing = db.query(User).filter(User.email == new_email, User.id != user_id).first()
                if existing:
                    return jsonify({'success': False, 'error': 'Email already in use'}), 400
                user.email = new_email
            
            # Handle password change
            if 'new_password' in data and data['new_password']:
                current_password = data.get('current_password', '')
                
                # Verify current password if user has one
                if user.password_hash:
                    if not current_password:
                        return jsonify({'success': False, 'error': 'Current password required'}), 400
                    if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
                
                # Set new password
                new_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user.password_hash = new_hash
            
            db.commit()
            
            # Update session with new user info
            session['user_first_name'] = user.first_name
            session['user_last_name'] = user.last_name
            session['user_email'] = user.email
            
            return jsonify({
                'success': True,
                'profile': user.to_dict(),
                'message': 'Profile updated successfully'
            })
            
    except Exception as e:
        print(f"[ERROR] Failed to update profile: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/profile/avatar', methods=['POST'])
@require_auth
def upload_avatar():
    """Upload a new avatar image."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': 'No avatar file provided'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        
        # Generate unique filename
        import uuid
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Save to avatars directory
        avatars_dir = Path('static/avatars')
        avatars_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = avatars_dir / filename
        file.save(str(filepath))
        
        # Update user's avatar_url
        avatar_url = f"/static/avatars/{filename}"
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                # Delete old avatar if it exists and is a local file
                if user.avatar_url and user.avatar_url.startswith('/static/avatars/'):
                    old_path = Path(user.avatar_url.lstrip('/'))
                    if old_path.exists():
                        old_path.unlink()
                
                user.avatar_url = avatar_url
                db.commit()
                
                return jsonify({
                    'success': True,
                    'avatar_url': avatar_url,
                    'profile': user.to_dict(),
                    'message': 'Avatar uploaded successfully'
                })
        
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    except Exception as e:
        print(f"[ERROR] Failed to upload avatar: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/profile/avatar', methods=['DELETE'])
@require_auth
def delete_avatar():
    """Delete user's avatar image."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Delete avatar file if it exists
            if user.avatar_url and user.avatar_url.startswith('/static/avatars/'):
                filepath = Path(user.avatar_url.lstrip('/'))
                if filepath.exists():
                    filepath.unlink()
            
            user.avatar_url = None
            db.commit()
            
            return jsonify({
                'success': True,
                'profile': user.to_dict(),
                'message': 'Avatar removed successfully'
            })
            
    except Exception as e:
        print(f"[ERROR] Failed to delete avatar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Serve the login page or handle login attempts."""
    if request.method == 'POST':
        email = request.form.get('username')  # Accept email in username field
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('login.html', error='Email and password are required')
        
        with DatabaseSession() as db:
            # Find user by email
            user = db.query(User).filter_by(email=email, is_active=True).first()
            
            if not user:
                return render_template('login.html', error='Invalid email or password')
            
            # Check if user has set a password
            if not user.password_hash:
                return render_template('login.html', error='Please check your email for an invitation link to set up your password')
            
            # Verify password
            try:
                password_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            except Exception as e:
                print(f"Password verification error: {e}")
                password_valid = False
            
            if not password_valid:
                return render_template('login.html', error='Invalid email or password')
            
            # Update last sign in
            user.last_sign_in = datetime.utcnow()
            db.commit()
            
            # Set session data
            session['user_id'] = user.id
            session['username'] = f"{user.first_name} {user.last_name}"
            session['email'] = user.email
            session['role'] = user.role.value  # Store as string
            session['authenticated'] = True
            
            print(f"DEBUG: Login successful for {user.email}")
            
            # Check for redirect parameter
            next_url = request.args.get('next') or request.form.get('next')
            if next_url:
                # Validate next URL (prevent open redirect attacks)
                # Only allow relative URLs
                if next_url.startswith('/') and not next_url.startswith('//'):
                    return redirect(next_url)
            
            # Redirect to main app
            return redirect('/')
    
    return render_template('login.html')

# User Management API Endpoints

@app.route('/api/users/active', methods=['GET'])
@require_auth
def get_active_users():
    """Get list of active users for @mention autocomplete (any authenticated user)."""
    try:
        with DatabaseSession() as db:
            # Get only active users
            users = db.query(User).filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
            
            users_data = []
            for user in users:
                users_data.append({
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': f"{user.first_name} {user.last_name}",  # Full name for display
                    'avatar_url': user.avatar_url,
                    'initials': user.get_initials()
                })
            
            return jsonify({"users": users_data, "success": True})
    except Exception as e:
        print(f"Error getting active users: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users', methods=['GET'])
@require_role('Admin')
def get_users():
    """Get list of all users (Admin only)."""
    try:
        with DatabaseSession() as db:
            # Show all users (active and inactive) - frontend will display them differently
            users = db.query(User).order_by(User.created_at.desc()).all()
            
            users_data = []
            for user in users:
                user_dict = user.to_dict()
                # Add relative time for last sign in
                user_dict['last_sign_in_relative'] = format_relative_time(user.last_sign_in)
                users_data.append(user_dict)
            
            response = make_response(jsonify({"users": users_data, "success": True}))
            # Prevent caching
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users', methods=['POST'])
@require_role('Admin')
def create_user():
    """Create a new user and send invitation email (Admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "success": False}), 400
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}", "success": False}), 400
        
        email = data['email'].strip().lower()
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        role_str = data['role'].strip()
        
        # Validate role
        try:
            role = UserRole[role_str.upper()]
        except KeyError:
            return jsonify({"error": f"Invalid role: {role_str}", "success": False}), 400
        
        print(f"Creating user: {first_name} {last_name} ({email}) with role {role_str}")
        
        with DatabaseSession() as db:
            print("  Database session opened")
            # Check if user already exists
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user:
                print("  User already exists")
                return jsonify({"error": "A user with this email already exists", "success": False}), 400
            
            # Generate invite token
            invite_token = secrets.token_urlsafe(32)
            print(f"  Generated invite token: {invite_token[:10]}...")
            
            # Create new user
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                is_active=False,  # Will be activated when they set password
                invite_token=invite_token,
                password_hash=None
            )
            print(f"  User object created")
            
            db.add(new_user)
            print(f"  User added to session")
            
            db.commit()
            print(f"  Database committed - User ID: {new_user.id}")
            
            # Get user data before session closes
            user_data = new_user.to_dict()
            user_id = new_user.id
            print(f"  User data serialized")
        
        # Send invitation email after session is closed
        inviter_name = session.get('username', 'Admin')
        email_sent = send_user_invite(email, first_name, invite_token, inviter_name)
        
        print(f"User created: ID={user_id}, Email={email}, Role={role_str}")
        
        return jsonify({
            "success": True,
            "message": "User created and invitation sent" if email_sent else "User created (email not sent)",
            "user": user_data,
            "email_sent": email_sent
        })
            
    except Exception as e:
        import traceback
        print(f"Error creating user: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_role('Admin')
def update_user(user_id):
    """Update user details (Admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "success": False}), 400
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found", "success": False}), 404
            
            # Update allowed fields
            if 'first_name' in data:
                user.first_name = data['first_name'].strip()
            if 'last_name' in data:
                user.last_name = data['last_name'].strip()
            if 'email' in data:
                new_email = data['email'].strip().lower()
                # Check if email is already taken by another user
                existing = db.query(User).filter(User.email == new_email, User.id != user_id).first()
                if existing:
                    return jsonify({"error": "Email already taken", "success": False}), 400
                user.email = new_email
            
            if 'role' in data:
                try:
                    user.role = UserRole[data['role'].upper()]
                except KeyError:
                    return jsonify({"error": f"Invalid role: {data['role']}", "success": False}), 400
            
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            
            user.updated_at = datetime.utcnow()
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "User updated successfully",
                "user": user.to_dict()
            })
            
    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users/<int:user_id>/reactivate', methods=['POST'])
@require_role('Admin')
def reactivate_user(user_id):
    """Reactivate an inactive user and resend invitation (Admin only)."""
    try:
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found", "success": False}), 404
            
            # Generate new invite token
            invite_token = secrets.token_urlsafe(32)
            
            # Resend invite - keep user inactive until they activate
            user.is_active = False  # Keep inactive until they set password
            user.invite_token = invite_token
            user.password_hash = None  # Clear password so they can set a new one
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Get user info before session closes
            email = user.email
            first_name = user.first_name
            
        # Send invitation email
        inviter_name = session.get('username', 'Admin')
        email_sent = send_user_invite(email, first_name, invite_token, inviter_name)
        
        return jsonify({
            "success": True,
            "message": "Invitation sent successfully" if email_sent else "Invitation sent (email not sent)",
            "email_sent": email_sent
        })
            
    except Exception as e:
        print(f"Error reactivating user: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_role('Admin')
def delete_user(user_id):
    """
    DEPRECATED - Soft delete endpoint (set is_active=False).
    This is kept for backward compatibility but not used in the UI.
    The UI now uses hard-delete (/hard-delete) for all deletions.
    
    Note: is_active=False represents "pending activation" (invited but no password set),
    not "deleted". To delete a user, use the hard-delete endpoint.
    """
    try:
        if user_id == session.get('user_id'):
            return jsonify({"error": "Cannot delete your own account", "success": False}), 400
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found", "success": False}), 404
            
            # Soft delete: set is_active to False
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "User deactivated successfully"
            })
            
    except Exception as e:
        import traceback
        print(f"[DELETE USER] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/users/<int:user_id>/hard-delete', methods=['DELETE'])
@require_role('Admin')
def hard_delete_user(user_id):
    """
    Permanently delete user from database (Admin only).
    This completely removes the user from the system.
    """
    try:
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found", "success": False}), 404
            
            # Don't allow deleting yourself
            if user.id == session.get('user_id'):
                return jsonify({"error": "Cannot delete your own account", "success": False}), 400
            
            user_email = user.email
            
            # HARD DELETE - permanently remove from database
            db.delete(user)
            db.commit()
            
            print(f"✅ User deleted: {user_email} (by user {session.get('username')})")
            
            return jsonify({
                "success": True,
                "message": f"User deleted successfully"
            })
            
    except Exception as e:
        import traceback
        print(f"❌ Error deleting user: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/auth/me', methods=['GET'])
def get_current_user_info():
    """Get current authenticated user info."""
    if not session.get('authenticated'):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=session.get('user_id')).first()
            if not user:
                return jsonify({"success": False, "error": "User not found"}), 404
            
            return jsonify({
                "success": True,
                "user": user.to_dict()
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/accept-invite', methods=['GET', 'POST'])
def accept_invite():
    """Handle user invitation acceptance and password setup."""
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            return render_template('accept_invite.html', error='Invalid invitation link')
        
        # Validate token and get user info
        with DatabaseSession() as db:
            user = db.query(User).filter_by(invite_token=token).first()
            if not user:
                return render_template('accept_invite.html', error='Invalid or expired invitation link')
            
            return render_template('accept_invite.html', token=token, email=user.email, first_name=user.first_name)
    
    elif request.method == 'POST':
        token = request.form.get('token')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not token or not password:
            return render_template('accept_invite.html', token=token, error='All fields are required')
        
        if password != confirm_password:
            return render_template('accept_invite.html', token=token, error='Passwords do not match')
        
        if len(password) < 8:
            return render_template('accept_invite.html', token=token, error='Password must be at least 8 characters')
        
        with DatabaseSession() as db:
            user = db.query(User).filter_by(invite_token=token).first()
            if not user:
                return render_template('accept_invite.html', error='Invalid or expired invitation link')
            
            # Set password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.password_hash = password_hash
            user.is_active = True
            user.invite_token = None  # Clear the token
            user.updated_at = datetime.utcnow()
            db.commit()
            
            # Auto-login the user
            session['user_id'] = user.id
            session['username'] = f"{user.first_name} {user.last_name}"
            session['email'] = user.email
            session['role'] = user.role.value
            session['authenticated'] = True
            
            return redirect('/')
    
    return render_template('accept_invite.html')


@app.route('/documents/<doc_id>/images/<int:page_num>')
def get_document_image(doc_id, page_num):
    """Serve original document images from R2 or local storage."""
    try:
        # Get full document to access page_images field
        doc = local_storage.get_document(doc_id)
        if not doc:
            return "Document not found", 404
        
        # If R2 is enabled, use public R2 URL (simple redirect - restore old working behavior)
        # Allow disabling R2 image serving via environment variable (useful if images aren't uploaded yet)
        use_r2_images = local_storage.use_r2 and local_storage.r2 and os.getenv('USE_R2_IMAGES', 'true').lower() == 'true'
        
        if use_r2_images:
            # Build list of possible image names to try (in order of likelihood)
            page_images = doc.get('page_images', [])
            title = doc.get('title', '')
            filename = doc.get('filename', '')
            
            # Extract base name from title or filename
            title_base = None
            if title:
                title_base = title.split(' - ')[0].strip()
            elif filename:
                title_base = Path(filename).stem
            
            # Build list of possible image names
            possible_names = []
            
            # 1. Doc ID subfolder pattern (used by promote_document.py)
            possible_names.append(f"{doc_id}/page_{page_num}.png")
            
            # 2. From page_images (most reliable for older docs)
            if page_images and len(page_images) >= page_num:
                image_path = Path(page_images[page_num - 1])
                possible_names.append(image_path.name)
            
            # 3. Using title/filename base (common pattern)
            if title_base:
                possible_names.append(f"{title_base}-{page_num}.png")
            
            # 4. Using doc_id pattern (flat)
            possible_names.append(f"{doc_id}-{page_num}.png")
            
            # Log what we're trying
            print(f"🔍 [IMAGE DEBUG] doc_id={doc_id}, page_num={page_num}, trying patterns: {possible_names}")
            
            # Try each pattern - check R2 first, then redirect if found
            # If head_object fails, try public URL anyway (fallback)
            for image_name in possible_names:
                if not image_name:
                    continue
                
                # First try to verify existence in R2
                try:
                    key = f'images/{image_name}'
                    try:
                        local_storage.r2.s3.head_object(Bucket=local_storage.r2.bucket_name, Key=key)
                        # Found it! Use presigned URL instead of public URL (bucket may not be public)
                        presigned_url = local_storage.r2.get_image_url(image_name, expires_in=3600)
                        print(f"✅ [IMAGE DEBUG] Found image in R2: {image_name}, using presigned URL")
                        return redirect(presigned_url)
                    except ClientError as e:
                        # Not found in R2, try next pattern
                        error_code = e.response.get('Error', {}).get('Code', '')
                        if error_code in ('404', 'NoSuchKey'):
                            print(f"❌ [IMAGE DEBUG] {image_name} not found in R2 (404/NoSuchKey), trying next pattern")
                            continue  # Try next pattern
                        else:
                            # Other error, log but continue
                            print(f"⚠️ [IMAGE DEBUG] Error checking R2 for {image_name}: {e}")
                            continue
                except Exception as e:
                    # Network/connection error - try presigned URL anyway as fallback
                    print(f"⚠️ [IMAGE DEBUG] Error accessing R2 for {image_name}, trying presigned URL: {e}")
                    try:
                        presigned_url = local_storage.r2.get_image_url(image_name, expires_in=3600)
                        return redirect(presigned_url)
                    except Exception as e2:
                        print(f"❌ [IMAGE DEBUG] Failed to generate presigned URL: {e2}")
                        continue
            
            # If we get here, none of the patterns were found via head_object
            # Try generating presigned URL for the first (most likely) pattern anyway
            if possible_names:
                fallback_name = possible_names[0]
                try:
                    presigned_url = local_storage.r2.get_image_url(fallback_name, expires_in=3600)
                    print(f"⚠️ [IMAGE DEBUG] No pattern confirmed in R2, trying presigned URL fallback: {fallback_name}")
                    return redirect(presigned_url)
                except Exception as e:
                    print(f"❌ [IMAGE DEBUG] Failed to generate presigned URL for fallback: {e}")
            else:
                print(f"❌ [IMAGE DEBUG] No possible names generated for doc_id={doc_id}, page_num={page_num}")
        
        # Local storage mode or R2 fallback
        # Check if document has page_images field
        page_images = doc.get('page_images', [])
        if page_images and len(page_images) >= page_num:
            # Use the stored page_images path (0-indexed, so page_num-1)
            image_path = Path(page_images[page_num - 1])
            if image_path.exists():
                return send_file(str(image_path), mimetype='image/png')
        
        # Fallback: Look for image files in the work directory using various patterns
        work_dir = Path("letters/work")
        
        # Build comprehensive list of patterns to try
        image_patterns = []
        
        # Patterns using doc_id
        image_patterns.extend([
            f"{doc_id}-{page_num}.png",              # pdftoppm default: doc_id-1.png
            f"{doc_id}_page_{page_num:03d}.png",      # doc_id_page_001.png
            f"{doc_id}_page_{page_num}.png",          # doc_id_page_1.png
            f"{doc_id}_{page_num}.png",               # doc_id_1.png
            f"{doc_id}_page_{page_num:02d}.png"       # doc_id_page_01.png
        ])
        
        # Patterns using title/filename base (if available)
        if title_base:
            image_patterns.extend([
                f"{title_base}-{page_num}.png",       # title-1.png (most common)
                f"{title_base}_{page_num}.png",       # title_1.png
                f"{title_base}_page_{page_num:03d}.png",  # title_page_001.png
                f"{title_base}_page_{page_num}.png",  # title_page_1.png
                f"{title_base}_page_{page_num:02d}.png"   # title_page_01.png
            ])
        
        # Also try patterns from page_images if available
        if page_images and len(page_images) >= page_num:
            image_path_from_list = Path(page_images[page_num - 1])
            # Try absolute path first
            if image_path_from_list.exists():
                image_patterns.insert(0, str(image_path_from_list))
            # Also try just the filename in work_dir
            image_patterns.insert(0, image_path_from_list.name)
        
        image_path = None
        for pattern in image_patterns:
            # Handle both absolute paths and relative paths
            if Path(pattern).is_absolute():
                test_path = Path(pattern)
            else:
                test_path = work_dir / pattern
            
            if test_path.exists():
                image_path = test_path
                print(f"Found image using pattern: {pattern}")
                break
        
        if not image_path:
            print(f"Image not found for doc {doc_id} page {page_num}. Tried patterns: {image_patterns[:10]}...")
            return "Image not found", 404
        
        return send_file(str(image_path), mimetype='image/png')
        
    except Exception as e:
        print(f"Error serving image: {e}")
        import traceback
        traceback.print_exc()
        return "Error serving image", 500


@app.route('/debug/test')
def debug_test():
    """Simple test endpoint to verify routes are working."""
    return jsonify({"status": "ok", "message": "Debug routes are working"})

@app.route('/debug/r2-images/<doc_id>')
@require_auth
def debug_r2_images(doc_id):
    """Debug endpoint to check what images exist in R2 for a document."""
    try:
        doc = local_storage.get_document(doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        
        result = {
            "doc_id": doc_id,
            "title": doc.get('title', ''),
            "filename": doc.get('filename', ''),
            "page_images": doc.get('page_images', []),
            "page_count": doc.get('page_count', 0)
        }
        
        # Get expected image names
        page_images = doc.get('page_images', [])
        title = doc.get('title', '')
        filename = doc.get('filename', '')
        
        title_base = None
        if title:
            title_base = title.split(' - ')[0].strip()
        elif filename:
            title_base = Path(filename).stem
        
        expected_names = []
        if page_images:
            for img_path in page_images:
                expected_names.append(Path(img_path).name)
        if title_base:
            expected_names.append(f"{title_base}-1.png")
        expected_names.append(f"{doc_id}-1.png")
        
        result["expected_names"] = list(set(expected_names))  # Remove duplicates
        
        # Check R2 if enabled
        if local_storage.use_r2 and local_storage.r2:
            try:
                # List all images in R2
                r2_images = local_storage.r2.list_images()
                result["r2_total_images"] = len(r2_images)
                
                # Check which expected names exist
                found_in_r2 = []
                missing_in_r2 = []
                
                for name in expected_names:
                    if name in r2_images:
                        found_in_r2.append(name)
                    else:
                        missing_in_r2.append(name)
                
                result["found_in_r2"] = found_in_r2
                result["missing_in_r2"] = missing_in_r2
                
                # Show sample of R2 images (first 20)
                result["r2_sample_images"] = sorted(r2_images)[:20]
                
            except Exception as e:
                result["r2_error"] = str(e)
        else:
            result["r2_enabled"] = False
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Helper functions for enhanced document processing

def parse_filename(filename: str) -> dict:
    """Parse document filename to extract metadata.
    
    Expected format: NNN-YYYY-MM-DD-lang.pdf or NNN-YYYY-MM-DD-lang_uniqueid.pdf
    Example: 002-1938-01-05-ger.pdf or 179-1942-08-15-fre_32f4d356.pdf
    """
    stem = Path(filename).stem
    
    # Remove unique ID suffix if present (e.g., "fre_32f4d356" -> "fre")
    # The unique ID is appended with underscore during upload
    if '_' in stem:
        stem = stem.rsplit('_', 1)[0]  # Remove last underscore and everything after
    
    parts = stem.split('-')
    
    # Extract language code (last part after removing unique ID)
    lang_code = parts[-1] if len(parts) > 0 else 'unknown'
    # Validate it's a known language code (3 letters)
    if len(lang_code) != 3 or not lang_code.isalpha():
        lang_code = 'unknown'
    
    metadata = {
        'number': parts[0] if len(parts) > 0 else None,
        'date': None,
        'language': lang_code
    }
    
    # Try to parse date from middle parts
    if len(parts) >= 4:
        try:
            year = parts[1]
            month = parts[2] if len(parts[2]) == 2 else '01'
            day = parts[3] if len(parts[3]) == 2 else '01'
            metadata['date'] = f"{year}-{month}-{day}"
        except:
            pass
    
    return metadata


def decode_html_entities(text: str) -> str:
    """Decode HTML entities in text (&#39; → ', &amp; → &, etc.)."""
    if not text or not isinstance(text, str):
        return text
    return html.unescape(text)


def extract_pdf_images(pdf_path: Path, output_dir: Path) -> list:
    """Extract images from PDF using pdftoppm."""
    # Create unique prefix for this PDF
    pdf_id = pdf_path.stem
    output_prefix = output_dir / pdf_id
    
    try:
        # Run pdftoppm to extract pages as PNG images
        subprocess.run([
            'pdftoppm',
            '-png',
            '-r', '300',  # 300 DPI for good quality
            str(pdf_path),
            str(output_prefix)
        ], check=True, capture_output=True)
        
        # Find generated images
        images = sorted(output_dir.glob(f"{pdf_id}-*.png"))
        return [str(img.relative_to(PROJECT_ROOT)) for img in images]
        
    except subprocess.CalledProcessError as e:
        print(f"Error extracting images: {e}")
        return []
    except FileNotFoundError:
        print("pdftoppm not found. Install poppler-utils to extract images.")
        return []


def translate_with_llm(original_text: str, source_lang: str, context: dict) -> str:
    """Translate text directly using LLM when Google Translate fails.
    
    Args:
        original_text: Original OCR text to translate
        source_lang: Source language code (e.g., 'fre', 'ger')
        context: Context document for reference
        
    Returns:
        Translated English text, or original text if translation fails
    """
    try:
        global ai_processor
        if ai_processor is None or not hasattr(ai_processor, 'client') or ai_processor.client is None:
            print("⚠️  AI processor not available for LLM translation")
            return original_text
        
        client = ai_processor.client
        
        # Map language codes to full names
        lang_names = {
            'fre': 'French', 'fra': 'French',
            'ger': 'German', 'deu': 'German',
            'hun': 'Hungarian', 'pol': 'Polish',
            'rus': 'Russian', 'yid': 'Yiddish'
        }
        source_lang_name = lang_names.get(source_lang, source_lang)
        
        # Build context string
        context_str = ""
        if context:
            people_list = [k for k, v in context.items() if isinstance(v, dict) and (v.get('type') == 'person' or 'variations' in v)][:15]
            places_list = [k for k, v in context.items() if isinstance(v, dict) and (v.get('type') == 'place' or 'location' in str(v).lower())][:15]
            if people_list or places_list:
                context_str = f"\nKnown people: {', '.join(people_list)}\nKnown places: {', '.join(places_list)}"
        
        prompt = f"""Translate this {source_lang_name} text to English. This is a historical document (WWII era correspondence).
{context_str}

IMPORTANT:
- Translate accurately and completely
- Preserve all formatting, line breaks, and structure
- Keep proper names as they appear (don't translate names)
- If text is unclear or illegible, indicate with [illegible] or [unclear]
- Return ONLY the English translation, no explanations

TEXT TO TRANSLATE:
{original_text[:6000]}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in historical documents and WWII-era correspondence."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        translated = response.choices[0].message.content.strip()
        
        # Sanity check - translation should be reasonably similar in length
        if len(translated) < len(original_text) * 0.3:
            print(f"⚠️  LLM translation too short ({len(translated)} chars vs {len(original_text)} original)")
            return original_text
        
        print(f"✅ LLM translation successful ({len(translated)} chars)")
        return translated
        
    except Exception as e:
        print(f"⚠️  LLM translation failed: {e}")
        return original_text


def review_and_refine_translation(translated_text: str, original_ocr_text: str, 
                                  context: dict, source_lang: str) -> tuple:
    """Review and refine Google Translate output using LLM with context.
    
    Args:
        translated_text: Google Translate output (already HTML decoded)
        original_ocr_text: Original OCR text (for reference)
        context: Context document (reference_data.json)
        source_lang: Source language code
        
    Returns:
        Tuple of (refined_translation, metadata_hints)
    """
    try:
        # Use the global ai_processor if available and valid, otherwise skip
        global ai_processor
        if ai_processor is None:
            print("⚠️  AI processor is None, skipping translation refinement")
            return translated_text, {}
        
        if not hasattr(ai_processor, 'client'):
            print("⚠️  AI processor does not have client attribute (using fallback), skipping translation refinement")
            return translated_text, {}
        
        if ai_processor.client is None:
            print("⚠️  AI processor client is None, skipping translation refinement")
            return translated_text, {}
        
        # Use the validated client from ai_processor
        client = ai_processor.client
        
        # Build context string from reference_data.json
        context_str = ""
        if context:
            people_list = []
            places_list = []
            if isinstance(context, dict):
                for key, value in context.items():
                    if isinstance(value, dict):
                        if value.get('type') == 'person' or 'variations' in value:
                            people_list.append(key)
                        elif value.get('type') == 'place' or 'location' in str(value).lower():
                            places_list.append(key)
            
            context_str = f"""
Known People: {', '.join(people_list[:20]) if people_list else 'None specified'}
Known Places: {', '.join(places_list[:20]) if places_list else 'None specified'}
"""
        
        # Build prompt for translation refinement
        prompt = f"""You are reviewing and refining a machine translation of a historical document from {source_lang} to English.

CONTEXT ABOUT THE COLLECTION:
{context_str}

ORIGINAL OCR TEXT (for reference, may contain errors):
{original_ocr_text[:1000]}

GOOGLE TRANSLATE OUTPUT (to be refined):
{translated_text[:4000]}

Your task:
1. Fix any mistranslations or awkward phrasings
2. Use context about known people and places to correct names and locations
3. Improve historical context and terminology accuracy
4. Preserve formatting, line breaks, and structure EXACTLY
5. Keep the same tone and style
6. Do NOT translate the OCR text directly - refine the existing translation

Return ONLY the refined translation text, no explanations or JSON formatting."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in historical documents. Your task is to refine machine translations while preserving accuracy and historical context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        refined_text = response.choices[0].message.content.strip()
        
        # Extract metadata hints from the refined text (basic extraction)
        metadata_hints = {}
        # This could be enhanced to extract sender/recipient hints, but for now return empty
        
        return refined_text, metadata_hints
        
    except openai.AuthenticationError as e:
        print(f"⚠️  Translation refinement authentication error: {e}")
        print("⚠️  Invalid API key - skipping translation refinement")
        return translated_text, {}
    except openai.APIError as e:
        print(f"⚠️  Translation refinement API error: {e}")
        return translated_text, {}
    except Exception as e:
        print(f"⚠️  Translation refinement error: {e}")
        import traceback
        traceback.print_exc()
        return translated_text, {}


def process_uploaded_document(pdf_path: Path, work_dir: Path) -> dict:
    """Process a single uploaded PDF document through the complete enhanced pipeline.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        work_dir: Working directory for temporary files
        
    Returns:
        Document data dictionary or None on error
    """
    doc_id = None
    try:
        print(f"[DEBUG] Processing document: {pdf_path.name}")
        
        # Parse filename for metadata
        file_metadata = parse_filename(pdf_path.name)
        source_lang = file_metadata.get('language', 'unknown')
        
        # Get processors
        batch_proc = get_batch_processor()
        ref_ext = get_ref_extractor()
        
        # Step 1: Run Enhanced OCR with context-aware correction
        print(f"[DEBUG] Running enhanced OCR...")
        try:
            metadata_for_ocr = {
                'language': source_lang,
                'context': context_data,
                'filename': pdf_path.name
            }
            
            ocr_result = batch_proc.run_ocr_on_pdf(pdf_path)
            if not ocr_result:
                print("[ERROR] OCR failed")
                return None
            
            raw_text = ocr_result['text']
            print(f"[DEBUG] OCR complete ({len(raw_text)} chars)")
            
            # Apply LLM correction with context
            print(f"[DEBUG] Applying context-aware correction...")
            enhanced = batch_proc.processor.correct_with_context(raw_text, metadata_for_ocr)
            original_text = enhanced.get('corrected_text', raw_text)
            print(f"[DEBUG] Text corrected ({len(original_text)} chars)")
            
            if not original_text or len(original_text) < 50:
                # If corrected text is too short but raw OCR was OK, use raw OCR
                if raw_text and len(raw_text) >= 50:
                    print(f"[WARNING] Corrected text too short ({len(original_text) if original_text else 0} chars), using raw OCR ({len(raw_text)} chars)")
                    original_text = raw_text
                else:
                    print(f"[ERROR] OCR produced insufficient text ({len(original_text) if original_text else 0} chars, raw: {len(raw_text) if raw_text else 0} chars)")
                    return None
        except Exception as e:
            print(f"[ERROR] OCR processing failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Step 2: Extract images for display
        print(f"[DEBUG] Extracting images...")
        try:
            image_paths = extract_pdf_images(pdf_path, work_dir)
            if not image_paths:
                image_paths = []
            print(f"[DEBUG] Extracted {len(image_paths)} page(s)")
        except Exception as e:
            print(f"[WARNING] Image extraction failed: {e}")
            image_paths = []
        
        # Step 3: Translate
        print(f"[DEBUG] Translating...")
        translation_succeeded = False
        try:
            translated_text = translate_document(original_text, source_lang)
            
            # Ensure translation is a string
            if isinstance(translated_text, (list, tuple)):
                translated_text = translated_text[0] if translated_text else ''
            
            if not translated_text:
                print("[WARNING] Translation returned empty")
                translated_text = original_text
            else:
                translation_succeeded = True
        except Exception as e:
            print(f"[WARNING] Translation failed: {e}")
            translated_text = original_text
        
        # Step 4: Decode HTML entities
        print(f"[DEBUG] Decoding HTML entities...")
        try:
            original_text = decode_html_entities(original_text)
            translated_text = decode_html_entities(translated_text)
            raw_text = decode_html_entities(raw_text)
        except Exception as e:
            print(f"[WARNING] HTML entity decoding failed: {e}")
        
        # Step 5: LLM Translation Review and Refinement
        # Only refine if translation actually succeeded - otherwise we'd be feeding
        # untranslated text to the refinement prompt, causing confused output
        print(f"[DEBUG] Reviewing and refining translation...")
        if translation_succeeded:
            try:
                refined_text, metadata_hints = review_and_refine_translation(
                    translated_text, original_text, context_data, source_lang
                )
                refined_text = decode_html_entities(refined_text)
            except Exception as e:
                print(f"[WARNING] Translation refinement failed: {e}, using translated text")
                refined_text = translated_text
        else:
            # Translation failed - try direct LLM translation instead
            print(f"[DEBUG] Google Translate failed, attempting LLM translation...")
            refined_text = translate_with_llm(original_text, source_lang, context_data)
            if not refined_text or refined_text == original_text:
                print(f"[WARNING] LLM translation also failed, using original text")
                refined_text = original_text
        
        # Step 6: Extract metadata (sender, recipient, locations)
        print(f"[DEBUG] Extracting metadata...")
        try:
            metadata = envelope_extractor.extract_metadata(original_text, pdf_path.name)
            # Ensure 'recipient' field exists (envelope_extractor may return 'receiver')
            if 'receiver' in metadata and 'recipient' not in metadata:
                metadata['recipient'] = metadata['receiver']
            if 'receiver_location' in metadata and 'recipient_location' not in metadata:
                metadata['recipient_location'] = metadata['receiver_location']
            print(f"[DEBUG] Metadata extracted: sender={metadata.get('sender', 'Unknown')}, recipient={metadata.get('recipient', metadata.get('receiver', 'Unknown'))}")
        except Exception as e:
            print(f"[WARNING] Metadata extraction failed: {e}")
            import traceback
            traceback.print_exc()
            metadata = {}
        
        # Step 7: Extract references with context
        print(f"[DEBUG] Extracting references...")
        # Initialize defaults
        simple_refs = {}
        detailed_refs = {}
        for ref_type in ['people', 'places', 'events', 'themes', 'emotions']:
            simple_refs[ref_type] = []
            detailed_refs[ref_type] = []
        
        try:
            references = extract_references_with_context(
                ai_processor,
                refined_text,  # Use refined translation for reference extraction
                document_date=file_metadata.get('date'),
                sender=metadata.get('sender'),
                recipient=metadata.get('recipient'),
                sender_location=metadata.get('sender_location'),
                recipient_location=metadata.get('recipient_location')
            )
            
            # Convert tuple format (name, context) to simple and detailed formats
            if references:
                for ref_type in ['people', 'places', 'events', 'themes', 'emotions']:
                    ref_list = references.get(ref_type, [])
                    simple_refs[ref_type] = []
                    detailed_refs[ref_type] = []
                    for item in ref_list:
                        if isinstance(item, tuple) and len(item) >= 2:
                            name, context = item[0], item[1]
                            simple_refs[ref_type].append(name)
                            detailed_refs[ref_type].append({'name': name, 'context': context})
                        elif isinstance(item, dict):
                            name = item.get('name', str(item))
                            context = item.get('context', '')
                            simple_refs[ref_type].append(name)
                            detailed_refs[ref_type].append({'name': name, 'context': context})
                        else:
                            name = str(item)
                            simple_refs[ref_type].append(name)
                            detailed_refs[ref_type].append({'name': name, 'context': ''})
        except Exception as e:
            print(f"[WARNING] Reference extraction error: {e}")
            import traceback
            traceback.print_exc()
            # Keep initialized empty dicts
        
        # Step 8: Generate summary using refined translation
        print(f"[DEBUG] Generating summary...")
        try:
            summary = ai_processor.generate_summary(refined_text, source_lang)
            
            # Check if summary generation failed (returns None or error message)
            if summary is None or (isinstance(summary, str) and summary.startswith("Summary generation failed")):
                print(f"[WARNING] Summary generation failed or returned None")
                summary = "Summary unavailable - AI processing error"
            else:
                summary = decode_html_entities(summary)
        except Exception as e:
            print(f"[WARNING] Summary generation error: {e}")
            summary = "Summary unavailable - AI processing error"
        
        # Generate document ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare document data with defaults for all fields
        title = pdf_path.stem
        title = decode_html_entities(title)
        
        # Ensure all text fields have defaults (empty string if None)
        raw_text = raw_text or ''
        original_text = original_text or ''
        translated_text = translated_text or original_text or ''  # Fallback to original if translation failed
        refined_text = refined_text or translated_text or original_text or ''  # Fallback chain
        summary = summary or 'Summary unavailable - processing incomplete'
        
        # Ensure metadata has defaults
        doc_data = {
            'id': doc_id,
            'filename': pdf_path.name,
            'title': title or 'Untitled Document',
            'raw_text': raw_text,
            'original_text': original_text,
            'translated_text': translated_text,
            'refined_text': refined_text,
            'summary': summary,
            'language': source_lang or 'unknown',
            'date': file_metadata.get('date') or '',
            'sender': metadata.get('sender') or '',
            'recipient': metadata.get('recipient') or '',
            'sender_location': metadata.get('sender_location') or '',
            'recipient_location': metadata.get('recipient_location') or '',
            'references': simple_refs or {},
            'people': simple_refs.get('people', []) if simple_refs else [],
            'page_images': image_paths or [],
            'page_count': len(image_paths) if image_paths else 0,
            'source_file': str(pdf_path),
            'status': 'new',
            'reviews': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save document
        print(f"[DEBUG] Saving document with ID: {doc_id}...")
        try:
            saved_id = local_storage.add_document(doc_data, doc_id=doc_id)
            print(f"[DEBUG] Document saved successfully with ID: {saved_id}")
            
            # Log the upload event in document history
            local_storage.log_history(
                saved_id,
                'System',
                'uploaded',
                'document was uploaded and processed'
            )
            print(f"[DEBUG] Logged upload event in history")
        except Exception as e:
            print(f"[ERROR] Failed to save document: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Add references to global metadata
        print(f"[DEBUG] Adding references to metadata...")
        ref_count = 0
        try:
            for ref_type, ref_list in detailed_refs.items():
                singular_type = ref_type.rstrip('s') if ref_type != 'themes' else 'theme'
                for ref_data in ref_list:
                    ref_name = ref_data.get('name', '')
                    if ref_name:
                        try:
                            local_storage.add_reference(
                                ref_type=singular_type,
                                name=ref_name,
                                aliases=[],
                                notes=ref_data.get('context', '')
                            )
                            local_storage.add_reference_to_document(doc_id, ref_name)
                            ref_count += 1
                        except Exception as e:
                            print(f"[WARNING] Could not add reference '{ref_name}': {e}")
        except Exception as e:
            print(f"[WARNING] Failed to add references to metadata: {e}")
        
        print(f"[DEBUG] Added {ref_count} references to metadata")
        print(f"[DEBUG] Document {doc_id} saved successfully!")
        print(f"[DEBUG] Returning doc_data with id: {doc_data.get('id')}")
        
        return doc_data
        
    except Exception as e:
        print(f"[ERROR] Error processing document: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Full traceback:\n{error_traceback}")
        # Try to clean up if doc_id was created
        if doc_id:
            try:
                print(f"[DEBUG] Attempting to clean up document {doc_id}")
                local_storage.delete_document(doc_id)
            except Exception as cleanup_error:
                print(f"[WARNING] Failed to clean up document {doc_id}: {cleanup_error}")
        return None


def translate_document(text: str, source_lang: str) -> str:
    """Translate document text to English."""
    if source_lang == 'eng' or not text:
        return text
    
    # Map ISO 639-2 (3-letter) to ISO 639-1 (2-letter) codes
    lang_map = {
        'ger': 'de',   # German
        'fre': 'fr',   # French
        'spa': 'es',   # Spanish
        'ita': 'it',   # Italian
        'pol': 'pl',   # Polish
        'rus': 'ru',   # Russian
        'eng': 'en'    # English
    }
    
    google_lang = lang_map.get(source_lang, source_lang)
    
    try:
        translated = translate_text(text, target_language='en', source_language=google_lang)
        
        # Google Translate returns tuple (text, detected_lang) - extract just text
        if isinstance(translated, (list, tuple)):
            translated = translated[0]
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload and processing with enhanced pipeline."""
    print(f"[DEBUG] Upload endpoint called")
    try:
        print(f"[DEBUG] Checking request.files...")
        if 'file' not in request.files:
            print(f"[DEBUG] No 'file' in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print(f"[DEBUG] File received: {file.filename}")
        if file.filename == '':
            print(f"[DEBUG] Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            print(f"[DEBUG] File not allowed: {file.filename}")
            return jsonify({'error': 'Only PDF files are allowed'}), 400
    except Exception as e:
        print(f"[ERROR] File validation exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'File validation failed: {str(e)}'}), 400
    
    # Use original filename (file is deleted after processing, so conflicts are rare)
    filename = secure_filename(file.filename)
    print(f"[DEBUG] Using filename: {filename}")
    
    # Save uploaded file
    pdf_path = INBOX_DIR / filename
    print(f"[DEBUG] Saving file to: {pdf_path}")
    try:
        file.save(str(pdf_path))
        print(f"[DEBUG] File saved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save uploaded file: {str(e)}'}), 500
    
    try:
        print(f"[DEBUG] Starting enhanced processing for: {pdf_path}")
        
        # Process document through enhanced pipeline
        doc_data = process_uploaded_document(pdf_path, WORK_DIR)
        
        if not doc_data:
            return jsonify({
                'error': 'Document processing failed',
                'details': 'See server logs for details'
            }), 500
        
        # Get refined text for response (fallback to translated_text if refined_text not available)
        display_text = doc_data.get('refined_text') or doc_data.get('translated_text', '')
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'original_filename': filename,
            'translated_content': display_text,
            'stored_document_id': doc_data.get('id'),
            'ai_processed': True,
            'summary': doc_data.get('summary', ''),
            'people': doc_data.get('people', [])
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
        try:
            if 'pdf_path' in locals() and pdf_path.exists():
                pdf_path.unlink()
                print(f"[DEBUG] Cleaned up uploaded file: {pdf_path}")
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to clean up file: {cleanup_error}")


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


@app.route('/documents')
def list_documents():
    """List all stored documents."""
    try:
        documents = local_storage.list_documents()
        # Convert tuples to dictionaries and include reviews and status
        document_list = []
        error_count = 0
        
        for doc_id, metadata in documents:
            try:
                # Get full document to include reviews and status
                full_doc = local_storage.get_document(doc_id)
                doc_data = {
                    'id': doc_id,
                    **metadata
                }
                # Add reviews if available
                if full_doc and 'reviews' in full_doc:
                    doc_data['reviews'] = full_doc['reviews']
                else:
                    doc_data['reviews'] = []
                
                # Add status from full document (ensure it's always present)
                if full_doc and 'status' in full_doc:
                    doc_data['status'] = full_doc['status']
                else:
                    doc_data['status'] = 'new'  # Default to 'new' if missing
                
                # Add page_count from full document (needed for thumbnail display)
                if full_doc and 'page_count' in full_doc:
                    doc_data['page_count'] = full_doc['page_count']
                elif full_doc and 'page_images' in full_doc:
                    doc_data['page_count'] = len(full_doc['page_images'])
                else:
                    doc_data['page_count'] = 0
                
                # Add summary from full document (needed for list display)
                if full_doc and 'summary' in full_doc:
                    doc_data['summary'] = full_doc['summary']
                elif 'summary' in metadata:
                    # Fallback to metadata summary if full doc doesn't have it
                    doc_data['summary'] = metadata.get('summary', '')
                else:
                    doc_data['summary'] = ''
                
                document_list.append(doc_data)
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Error processing document {doc_id}: {e}")
                error_count += 1
                continue
        
        if error_count > 0:
            print(f"Warning: {error_count} documents had errors and were skipped")
        
        response = make_response(jsonify({
            'success': True,
            'documents': document_list,
            'total': len(document_list)
        }))
        # Prevent caching of document list
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>')
def get_document(doc_id):
    """Get a specific document by ID."""
    # Check if this is a browser request with query parameters (deep link)
    # If so, redirect to main page with query params
    if request.args.get('tab') or request.args.get('comment'):
        # This is a deep link from email - redirect to main page
        tab = request.args.get('tab', '')
        comment = request.args.get('comment', '')
        redirect_url = f'/?doc={doc_id}'
        if tab:
            redirect_url += f'&tab={tab}'
        if comment:
            redirect_url += f'&comment={comment}'
        return redirect(redirect_url)
    
    # Check if this is an API request (has Accept: application/json header)
    # or if it's an AJAX request
    is_api_request = (
        request.headers.get('Accept', '').startswith('application/json') or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        request.is_json
    )
    
    # If not an API request, redirect to main page
    if not is_api_request:
        return redirect(f'/?doc={doc_id}')
    
    # API request - return JSON
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
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error retrieving document {doc_id}: {e}")
        print(f"[ERROR] Traceback: {error_traceback}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_traceback
        }), 500


@app.route('/people', methods=['GET', 'POST'])
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


@app.route('/people/search')
def search_references():
    """Search references with parent-child hierarchy support."""
    try:
        query = request.args.get('q', '').strip()
        ref_type = request.args.get('type', None)
        
        if not query:
            # Return all people if no query
            people = local_storage.get_people_with_documents()
            results = []
            for person in people:
                results.append({
                    'name': person['name'],
                    'is_parent': False,
                    'parent_name': None,
                    'children_count': 0
                })
            return jsonify({
                'success': True,
                'results': results
            })
        
        # Search with hierarchy
        results = local_storage.search_references_with_hierarchy(query, ref_type)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/people/<person_name>/documents')
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
        new_type = data.get('type', 'person')
        new_aliases = data.get('aliases', [])
        new_secondary_refs = data.get('secondary_references', [])
        
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400
        
        success = local_storage.update_person(
            person_name, 
            new_name, 
            new_context,
            new_type,
            new_aliases,
            new_secondary_refs
        )
        
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
def add_person_to_document(doc_id):
    """Add a person reference to a document (resolves children to canonical parent)."""
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
        
        # Resolve child references to their canonical parent
        resolved_ref = local_storage.get_reference_with_parent(person_name)
        canonical_name = resolved_ref.get('canonical_name', person_name) if resolved_ref else person_name
        
        print(f"Adding reference: '{person_name}' -> resolved to canonical: '{canonical_name}'")
        
        success = local_storage.add_person_to_document(doc_id, canonical_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Person {canonical_name} added to document',
                'canonical_name': canonical_name,
                'original_name': person_name
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


@app.route('/documents/<doc_id>/status', methods=['PUT'])
def update_document_status(doc_id):
    """Update document status."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        status = data.get('status')
        if not status:
            return jsonify({
                'success': False,
                'error': 'Missing status field'
            }), 400
        
        # Update the document status
        success = local_storage.update_document(doc_id, {'status': status})
        
        if success:
            # Log the status change in history
            username = session.get('username', 'System')
            local_storage.log_history(
                doc_id, 
                username, 
                'status_change', 
                f'changed status to {status}'
            )
            
            # If status is 'reject', send email notifications to admins
            if status.lower() == 'reject':
                try:
                    # Get all admin users
                    with DatabaseSession() as db:
                        admin_users = db.query(User).filter(
                            User.role == UserRole.ADMIN,
                            User.is_active == True
                        ).all()
                        admin_emails = [user.email for user in admin_users if user.email]
                    
                    if admin_emails:
                        # Get document title
                        doc = local_storage.get_document(doc_id)
                        doc_title = doc.get('title', doc_id) if doc else doc_id
                        
                        # Send rejection notifications
                        sent_count = send_rejection_notification(
                            admin_emails=admin_emails,
                            document_title=doc_title,
                            document_id=doc_id,
                            rejected_by=username
                        )
                        print(f"Sent {sent_count} rejection notification(s) for document {doc_id}")
                except Exception as e:
                    print(f"Error sending rejection notifications: {e}")
                    # Don't fail the status update if email fails
            
            return jsonify({
                'success': True,
                'message': 'Status updated successfully',
                'status': status
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


@app.route('/documents/<doc_id>', methods=['PUT'])
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
            # Log the update in history if fields changed (exclude required fields that are always sent)
            username = session.get('username', 'System')
            # Exclude 'title' and 'summary' which are always sent and don't indicate an edit
            changed_field_keys = [k for k in data.keys() if k not in ['regenerate_summary', 'title', 'summary']]
            
            if changed_field_keys:
                # Create human-readable field names
                field_name_map = {
                    'document_date': 'date',
                    'sender': 'sender',
                    'recipient': 'recipient',
                    'sender_location': 'sender location',
                    'recipient_location': 'recipient location',
                    'original_text': 'original text',
                    'translated_text': 'translation',
                    'comments': 'comments'
                }
                
                readable_fields = [field_name_map.get(k, k) for k in changed_field_keys]
                
                # Format nicely: "field1, field2, and field3"
                if len(readable_fields) == 1:
                    field_text = readable_fields[0]
                elif len(readable_fields) == 2:
                    field_text = f"{readable_fields[0]} and {readable_fields[1]}"
                else:
                    field_text = ', '.join(readable_fields[:-1]) + f", and {readable_fields[-1]}"
                
                local_storage.log_history(
                    doc_id,
                    username,
                    'edit',
                    f'edited the {field_text}'
                )
            
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


@app.route('/documents/<doc_id>/review', methods=['POST'])
def add_document_review(doc_id):
    """Mark a document as reviewed by the current user."""
    try:
        # Get user info from session
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        user_id = session.get('user_id')
        username = session.get('username')
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        review = local_storage.add_review(doc_id, str(user_id), username, notes)
        
        if review:
            return jsonify({
                'success': True,
                'review': review
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add review'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/reviews', methods=['GET'])
def get_document_reviews(doc_id):
    """Get all reviews for a document with user info."""
    try:
        reviews = local_storage.get_reviews(doc_id)
        
        # Get user IDs from reviews
        user_ids = [review.get('userId') for review in reviews if review.get('userId')]
        
        # Fetch user info for reviewers
        reviewers_info = {}
        if user_ids:
            with DatabaseSession() as db:
                users = db.query(User).filter(User.id.in_(user_ids)).all()
                for user in users:
                    reviewers_info[str(user.id)] = {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'username': f"{user.first_name} {user.last_name}"
                    }
        
        # Enhance reviews with user info
        enhanced_reviews = []
        for review in reviews:
            enhanced_review = review.copy()
            user_id_str = str(review.get('userId', ''))
            if user_id_str in reviewers_info:
                enhanced_review['user_info'] = reviewers_info[user_id_str]
            enhanced_reviews.append(enhanced_review)
        
        return jsonify({
            'success': True,
            'reviews': enhanced_reviews
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/history', methods=['GET'])
def get_document_history(doc_id):
    """Get history log for a document."""
    try:
        history = local_storage.get_history(doc_id)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/history', methods=['POST'])
def add_document_history(doc_id):
    """Add a history entry to a document."""
    try:
        # Get user info from session
        username = session.get('username', 'System')
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        action = data.get('action', '')
        details = data.get('details', '')
        
        if not action or not details:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: action and details'
            }), 400
        
        success = local_storage.log_history(doc_id, username, action, details)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'History logged successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to log history'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== Context Notes (Comments) API =====

@app.route('/documents/<doc_id>/comments', methods=['GET'])
def get_document_comments(doc_id):
    """Get all comments for a document."""
    try:
        comments = local_storage.list_context_notes(doc_id)
        
        # Enrich comments with current user avatars
        # Build a cache of user avatars by username
        usernames = set(c.get('username') for c in comments if c.get('username'))
        avatar_cache = {}
        
        if usernames:
            with DatabaseSession() as db:
                # Look up users by their display name (first_name + last_name)
                for username in usernames:
                    # Username in comments is typically "First Last"
                    parts = username.split(' ', 1)
                    if len(parts) == 2:
                        user = db.query(User).filter_by(first_name=parts[0], last_name=parts[1]).first()
                        if user and user.avatar_url:
                            avatar_cache[username] = user.avatar_url
        
        # Add current avatar_url to each comment
        for comment in comments:
            username = comment.get('username')
            if username in avatar_cache:
                comment['avatar_url'] = avatar_cache[username]
        
        return jsonify({
            'success': True,
            'comments': comments
        })
    except Exception as e:
        print(f"[ERROR] Failed to get comments: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/comments', methods=['POST'])
def add_document_comment(doc_id):
    """Add a comment to a document."""
    try:
        # Get user info from session
        username = session.get('username')
        user_id = session.get('user_id')
        if not username or not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        note = data.get('note', '').strip()
        if not note:
            return jsonify({
                'success': False,
                'error': 'Comment text is required'
            }), 400
        
        # Get mentioned user IDs from request
        mentioned_user_ids = data.get('mentioned_user_ids', [])
        if not isinstance(mentioned_user_ids, list):
            mentioned_user_ids = []
        
        # Check if this is a context comment (for LLM reprocessing)
        is_context = data.get('is_context', False)
        
        # Get user's avatar URL
        avatar_url = None
        with DatabaseSession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                avatar_url = user.avatar_url
        
        # Add comment with mentions and context flag
        comment = local_storage.add_context_note(doc_id, username, note, mentioned_user_ids, is_context, avatar_url)
        
        if comment:
            # Get document info for notifications
            doc = local_storage.get_document(doc_id)
            document_title = doc.get('title', 'Untitled Document') if doc else 'Untitled Document'
            comment_id = comment.get('id')
            comment_preview = note[:200] + '...' if len(note) > 200 else note
            
            # Create notifications and send emails for mentioned users
            if mentioned_user_ids:
                with DatabaseSession() as db:
                    # Get mentioned users
                    mentioned_users = db.query(User).filter(
                        User.id.in_(mentioned_user_ids),
                        User.is_active == True
                    ).all()
                    
                    for mentioned_user in mentioned_users:
                        # Skip if user mentioned themselves
                        if mentioned_user.id == user_id:
                            continue
                        
                        # Create notification
                        notification = Notification(
                            user_id=mentioned_user.id,
                            type='mention',
                            comment_id=comment_id,
                            document_id=doc_id,
                            document_title=document_title,
                            commenter_name=username,
                            comment_preview=comment_preview,
                            read=False
                        )
                        db.add(notification)
                        
                        # Send email notification
                        try:
                            send_mention_notification(
                                email=mentioned_user.email,
                                first_name=mentioned_user.first_name,
                                commenter_name=username,
                                document_title=document_title,
                                doc_id=doc_id,
                                comment_id=comment_id
                            )
                        except Exception as e:
                            print(f"Error sending mention notification to {mentioned_user.email}: {e}")
                            # Don't fail comment creation if email fails
                    
                    db.commit()
            
            return jsonify({
                'success': True,
                'comment': comment,
                'mentioned_users': mentioned_user_ids,
                'is_context': is_context,
                'show_reprocess_dialog': is_context  # Frontend should show reprocess dialog if this is a context comment
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add comment'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/comments/<comment_id>', methods=['PUT'])
def update_document_comment(doc_id, comment_id):
    """Update a comment."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        note = data.get('note', '').strip()
        if not note:
            return jsonify({
                'success': False,
                'error': 'Comment text is required'
            }), 400
        
        updated_comment = local_storage.update_context_note(comment_id, note)
        
        if updated_comment:
            return jsonify({
                'success': True,
                'comment': updated_comment
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Comment not found or update failed'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/comments/<comment_id>', methods=['DELETE'])
@require_auth
def delete_document_comment(doc_id, comment_id):
    """Delete a comment."""
    try:
        print(f"[DEBUG] Attempting to delete comment {comment_id} from doc {doc_id}")
        
        # First check if the comment exists in the document directly
        doc = local_storage.get_document(doc_id)
        if not doc:
            print(f"[DEBUG] Document {doc_id} not found")
            return jsonify({
                'success': False,
                'error': f'Document {doc_id} not found'
            }), 404
        
        # Check if comment exists in document's context_notes
        context_notes = doc.get('context_notes', [])
        deleted_comment = None
        for note in context_notes:
            if note.get('id') == comment_id:
                deleted_comment = note
                break
        
        if not deleted_comment:
            print(f"[DEBUG] Comment {comment_id} not found in document's context_notes")
            return jsonify({
                'success': False,
                'error': f'Comment {comment_id} not found in document'
            }), 404
        
        # Check if this was a context comment (for reprocess dialog)
        was_context_comment = deleted_comment.get('is_context', False)
        
        # Try the standard deletion method first
        success = local_storage.delete_context_note(comment_id)
        
        if not success:
            # Fallback: directly remove from document if metadata index is out of sync
            print(f"[DEBUG] Standard deletion failed, trying direct removal")
            filtered_notes = [n for n in context_notes if n.get('id') != comment_id]
            if len(filtered_notes) < len(context_notes):
                doc['context_notes'] = filtered_notes
                # Save the updated document
                if local_storage.use_r2 and local_storage.r2:
                    local_storage.r2.save_document(doc_id, doc)
                # Also update local if exists
                doc_file = local_storage.documents_dir / f"{doc_id}.json"
                if doc_file.parent.exists():
                    with open(doc_file, 'w') as f:
                        json.dump(doc, f, indent=2)
                success = True
                print(f"[DEBUG] Direct removal successful")
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comment deleted successfully',
                'was_context_comment': was_context_comment,
                'show_reprocess_dialog': was_context_comment  # Show dialog if context was removed
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Comment not found or deletion failed'
            }), 404
    except Exception as e:
        print(f"[ERROR] Failed to delete comment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== Document Reprocessing API =====

@app.route('/documents/<doc_id>/status', methods=['GET'])
def get_document_status(doc_id):
    """Get the processing status of a document."""
    try:
        status = local_storage.get_processing_status(doc_id)
        return jsonify({
            'success': True,
            **status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/documents/<doc_id>/reprocess', methods=['POST'])
@require_auth
def reprocess_document(doc_id):
    """Trigger reprocessing of a document with context.
    
    Request body:
    {
        "fields": ["translation", "summary", "sender", "recipient", "references"],
        "use_raw_ocr": false  // If true, re-run from raw OCR text
    }
    """
    try:
        # Check document exists
        doc = local_storage.get_document(doc_id)
        if not doc:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        # Check if already processing
        current_status = local_storage.get_processing_status(doc_id)
        if current_status.get('status') == 'processing':
            return jsonify({
                'success': False,
                'error': 'Document is already being processed'
            }), 409
        
        data = request.get_json() or {}
        fields = data.get('fields', ['translation', 'summary', 'sender', 'recipient', 'references'])
        use_raw_ocr = data.get('use_raw_ocr', False)
        
        # Validate fields
        valid_fields = {'translation', 'summary', 'sender', 'recipient', 'references'}
        invalid_fields = set(fields) - valid_fields
        if invalid_fields:
            return jsonify({
                'success': False,
                'error': f'Invalid fields: {invalid_fields}'
            }), 400
        
        # Set status to processing
        local_storage.set_processing_status(doc_id, 'processing')
        
        # Get user info for history logging
        username = session.get('username', 'system')
        
        # Start background processing
        thread = threading.Thread(
            target=reprocess_document_async,
            args=(doc_id, fields, use_raw_ocr, username)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Document reprocessing started',
            'fields': fields,
            'use_raw_ocr': use_raw_ocr
        })
    except Exception as e:
        print(f"[ERROR] Failed to start reprocessing: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def reprocess_document_async(doc_id: str, fields: list, use_raw_ocr: bool, username: str):
    """Background function to reprocess a document with context.
    
    Args:
        doc_id: Document ID to reprocess
        fields: List of fields to regenerate
        use_raw_ocr: If True, re-run from raw OCR text
        username: Username for history logging
    """
    try:
        print(f"[REPROCESS] Starting reprocessing for document {doc_id}")
        print(f"[REPROCESS] Fields: {fields}, use_raw_ocr: {use_raw_ocr}")
        
        # Get the document
        doc = local_storage.get_document(doc_id)
        if not doc:
            print(f"[REPROCESS] Document {doc_id} not found")
            local_storage.set_processing_status(doc_id, 'error', 'Document not found')
            return
        
        # Collect document context (all is_context=True comments)
        doc_context_comments = local_storage.get_document_context_comments(doc_id)
        document_context = "\n".join([
            f"- {c.get('username', 'Editor')}: {c.get('note', '')}" 
            for c in doc_context_comments
        ])
        print(f"[REPROCESS] Found {len(doc_context_comments)} context comments")
        
        # Merge with global context
        merged_context = dict(context_data)  # Start with global context
        if document_context:
            merged_context['document_specific_context'] = document_context
        
        # Get source text
        if use_raw_ocr and doc.get('raw_text'):
            source_text = doc.get('raw_text')
            print(f"[REPROCESS] Using raw OCR text ({len(source_text)} chars)")
        else:
            source_text = doc.get('original_text', '')
            print(f"[REPROCESS] Using original text ({len(source_text)} chars)")
        
        source_lang = doc.get('language', 'unknown')
        results = {'success': [], 'failed': []}
        
        # Reprocess each requested field
        if 'translation' in fields:
            try:
                print(f"[REPROCESS] Regenerating translation...")
                # Try LLM translation with context
                translated = translate_with_llm(source_text, source_lang, merged_context)
                if translated and translated != source_text:
                    doc['translated_text'] = translated
                    results['success'].append('translation')
                    print(f"[REPROCESS] Translation successful ({len(translated)} chars)")
                else:
                    results['failed'].append('translation')
                    print(f"[REPROCESS] Translation returned same text or failed")
            except Exception as e:
                print(f"[REPROCESS] Translation failed: {e}")
                results['failed'].append('translation')
        
        if 'summary' in fields:
            try:
                print(f"[REPROCESS] Regenerating summary...")
                text_for_summary = doc.get('translated_text') or source_text
                
                # Build context string for summary
                context_str = ""
                if document_context:
                    context_str = f"\n\nEditor-provided context:\n{document_context}"
                
                summary = ai_processor.generate_summary(text_for_summary + context_str)
                if summary and not summary.startswith("Summary generation failed"):
                    doc['summary'] = summary
                    results['success'].append('summary')
                    print(f"[REPROCESS] Summary successful")
                else:
                    results['failed'].append('summary')
                    print(f"[REPROCESS] Summary generation returned error")
            except Exception as e:
                print(f"[REPROCESS] Summary failed: {e}")
                results['failed'].append('summary')
        
        if 'sender' in fields or 'recipient' in fields:
            try:
                print(f"[REPROCESS] Regenerating metadata (sender/recipient)...")
                # Use envelope extractor with context
                metadata = envelope_extractor.extract_metadata(
                    source_text + (f"\n\nContext: {document_context}" if document_context else ""),
                    doc.get('filename', '')
                )
                
                if 'sender' in fields and metadata.get('sender'):
                    doc['sender'] = metadata.get('sender')
                    doc['sender_location'] = metadata.get('sender_location', '')
                    results['success'].append('sender')
                    print(f"[REPROCESS] Sender extracted: {doc['sender']}")
                elif 'sender' in fields:
                    results['failed'].append('sender')
                
                if 'recipient' in fields and metadata.get('recipient'):
                    doc['recipient'] = metadata.get('recipient')
                    doc['recipient_location'] = metadata.get('recipient_location', '')
                    results['success'].append('recipient')
                    print(f"[REPROCESS] Recipient extracted: {doc['recipient']}")
                elif 'recipient' in fields:
                    results['failed'].append('recipient')
            except Exception as e:
                print(f"[REPROCESS] Metadata extraction failed: {e}")
                if 'sender' in fields:
                    results['failed'].append('sender')
                if 'recipient' in fields:
                    results['failed'].append('recipient')
        
        if 'references' in fields:
            try:
                print(f"[REPROCESS] Regenerating references...")
                text_for_refs = doc.get('translated_text') or source_text
                
                references = extract_references_with_context(
                    ai_processor,
                    text_for_refs + (f"\n\nContext: {document_context}" if document_context else ""),
                    document_date=doc.get('date'),
                    sender=doc.get('sender'),
                    recipient=doc.get('recipient'),
                    sender_location=doc.get('sender_location'),
                    recipient_location=doc.get('recipient_location')
                )
                
                if references:
                    simple_refs = references.get('simple', references)
                    doc['references'] = simple_refs
                    doc['people'] = simple_refs.get('people', [])
                    results['success'].append('references')
                    print(f"[REPROCESS] References extracted: {len(doc.get('people', []))} people")
                else:
                    results['failed'].append('references')
            except Exception as e:
                print(f"[REPROCESS] Reference extraction failed: {e}")
                results['failed'].append('references')
        
        # Update document timestamp
        doc['updated_at'] = datetime.now().isoformat()
        doc['last_reprocessed'] = datetime.now().isoformat()
        doc['last_reprocessed_by'] = username
        
        # Save the updated document
        local_storage.save_document(doc_id, doc)
        print(f"[REPROCESS] Document saved")
        
        # Log to history
        history_message = f"Reprocessed: {', '.join(results['success'])}"
        if results['failed']:
            history_message += f" (failed: {', '.join(results['failed'])})"
        local_storage.log_history(doc_id, 'reprocessed', username, history_message)
        
        # Set status to ready
        if results['failed'] and not results['success']:
            local_storage.set_processing_status(doc_id, 'error', f"All fields failed: {', '.join(results['failed'])}")
        else:
            local_storage.set_processing_status(doc_id, 'ready')
        
        print(f"[REPROCESS] Completed. Success: {results['success']}, Failed: {results['failed']}")
        
    except Exception as e:
        print(f"[REPROCESS] Fatal error: {e}")
        traceback.print_exc()
        local_storage.set_processing_status(doc_id, 'error', str(e))
        local_storage.log_history(doc_id, 'reprocess_error', username, f"Reprocessing failed: {str(e)}")


# ===== Notifications API =====

@app.route('/api/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """Get user's notifications (most recent 20, unread first)."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        with DatabaseSession() as db:
            # Get notifications: unread first, then by created_at desc, limit 20
            notifications = db.query(Notification).filter_by(user_id=user_id).order_by(
                Notification.read.asc(),  # Unread first (False < True)
                Notification.created_at.desc()
            ).limit(20).all()
            
            notifications_data = [n.to_dict() for n in notifications]
            
            return jsonify({
                'success': True,
                'notifications': notifications_data
            })
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/notifications/count', methods=['GET'])
@require_auth
def get_notification_count():
    """Get count of unread notifications for current user."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        with DatabaseSession() as db:
            count = db.query(Notification).filter_by(
                user_id=user_id,
                read=False
            ).count()
            
            return jsonify({
                'success': True,
                'count': count
            })
    except Exception as e:
        print(f"Error getting notification count: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        with DatabaseSession() as db:
            notification = db.query(Notification).filter_by(
                id=notification_id,
                user_id=user_id  # Ensure user owns this notification
            ).first()
            
            if not notification:
                return jsonify({
                    'success': False,
                    'error': 'Notification not found'
                }), 404
            
            notification.read = True
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            })
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/notifications/read-all', methods=['POST'])
@require_auth
def mark_all_notifications_read():
    """Mark all notifications as read for current user."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        with DatabaseSession() as db:
            updated = db.query(Notification).filter_by(
                user_id=user_id,
                read=False
            ).update({'read': True})
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'{updated} notifications marked as read',
                'count': updated
            })
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/geocode', methods=['GET'])
def geocode_location():
    """Geocode an address or search for a location using Geoapify."""
    try:
        query = request.args.get('query', '')
        country = request.args.get('country', None)
        autocomplete = request.args.get('autocomplete', 'true').lower() == 'true'
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400
        
        if autocomplete:
            # Use autocomplete for suggestions
            results = geoapify_client.autocomplete_location(query, country=country, limit=5)
            return jsonify({
                'success': True,
                'results': results
            })
        else:
            # Use regular geocoding for exact address
            result = geoapify_client.geocode_address(query, country=country)
            return jsonify({
                'success': True,
                'result': result
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract-envelope', methods=['POST'])
def extract_envelope_addresses():
    """Extract sender and recipient addresses from OCR text."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        original_text = data.get('original_text', '')
        
        if not original_text:
            return jsonify({
                'success': False,
                'error': 'Missing original_text'
            }), 400
        
        # Extract addresses using envelope extractor
        result = envelope_extractor.extract_metadata(original_text)
        
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Determine if we're in debug mode
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5001))
    
    # Initialize database tables on first run (for deployment)
    try:
        from scripts.database import Base, engine
        print("Checking database tables...")
        Base.metadata.create_all(engine)
        print("✅ Database tables ready")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Setup logging for production
    if not debug_mode:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/flask.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('OCR Pipeline startup')
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
