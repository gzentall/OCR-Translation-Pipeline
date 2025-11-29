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
from pathlib import Path
from datetime import datetime
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
from scripts.database import DatabaseSession, User, Document, Reference, ReferenceType, UserRole
from sqlalchemy import text
from scripts.email_service import send_user_invite
from botocore.exceptions import ClientError

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
ai_processor = FallbackAIProcessor()
geoapify_client = GeoapifyClient()
envelope_extractor = EnvelopeExtractor()

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
    """Format a datetime as relative time (e.g., '2 hours ago')"""
    if not dt:
        return "Never signed in"
    
    now = datetime.utcnow()
    diff = relativedelta(now, dt)
    
    if diff.years > 0:
        return f"{diff.years} year{'s' if diff.years != 1 else ''} ago"
    elif diff.months > 0:
        return f"{diff.months} month{'s' if diff.months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.hours > 0:
        return f"{diff.hours} hour{'s' if diff.hours != 1 else ''} ago"
    elif diff.minutes > 0:
        return f"{diff.minutes} minute{'s' if diff.minutes != 1 else ''} ago"
    else:
        return "Just now"


@app.route('/')
@require_auth
def index():
    """Serve the main application page (Documents tab)."""
    # Get user info from session (user is authenticated due to @require_auth decorator)
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
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
    # Get user info from session
    user = None
    if session.get('authenticated'):
        user = {
            'id': session.get('user_id'),
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
            
            # Redirect to main app
            return redirect('/')
    
    return render_template('login.html')

# User Management API Endpoints

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
            
            # Reactivate user
            user.is_active = True
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
            "message": "User reactivated and invitation sent" if email_sent else "User reactivated (email not sent)",
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
            
            # 1. From page_images (most reliable)
            if page_images and len(page_images) >= page_num:
                image_path = Path(page_images[page_num - 1])
                possible_names.append(image_path.name)
            
            # 2. Using title/filename base (common pattern)
            if title_base:
                possible_names.append(f"{title_base}-{page_num}.png")
            
            # 3. Using doc_id pattern
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
    """Get all reviews for a document."""
    try:
        reviews = local_storage.get_reviews(doc_id)
        return jsonify({
            'success': True,
            'reviews': reviews
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
        return jsonify({
            'success': True,
            'comments': comments
        })
    except Exception as e:
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
        if not username:
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
        
        comment = local_storage.add_context_note(doc_id, username, note)
        
        if comment:
            return jsonify({
                'success': True,
                'comment': comment
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
def delete_document_comment(doc_id, comment_id):
    """Delete a comment."""
    try:
        success = local_storage.delete_context_note(comment_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comment deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Comment not found or deletion failed'
            }), 404
    except Exception as e:
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
