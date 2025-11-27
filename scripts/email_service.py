#!/usr/bin/env python3

"""
Email service using Resend API for sending user invitations and notifications.
"""

import os
from typing import Optional
import resend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Resend with API key
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
APP_URL = os.getenv('APP_URL', 'http://localhost:5001')

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_user_invite(email: str, first_name: str, invite_token: str, inviter_name: Optional[str] = None) -> bool:
    """
    Send invitation email to new user with password setup link.
    
    Args:
        email: Recipient email address
        first_name: Recipient's first name
        invite_token: Unique token for password setup
        inviter_name: Name of the user who sent the invitation (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    
    if not RESEND_API_KEY:
        print("Warning: RESEND_API_KEY not configured. Email not sent.")
        print(f"Invite link for {email}: {APP_URL}/accept-invite?token={invite_token}")
        return False
    
    invite_link = f"{APP_URL}/accept-invite?token={invite_token}"
    
    # Create personalized greeting
    inviter_text = f" by {inviter_name}" if inviter_name else ""
    
    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #6750a4;
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 500;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .content h2 {{
                color: #1c1b1f;
                font-size: 20px;
                font-weight: 500;
                margin-top: 0;
            }}
            .content p {{
                color: #49454f;
                margin: 16px 0;
            }}
            .button {{
                display: inline-block;
                background-color: #6750a4;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 20px;
                font-weight: 500;
                margin: 24px 0;
            }}
            .button:hover {{
                background-color: #5542a6;
            }}
            .footer {{
                background-color: #f3edf7;
                padding: 20px 30px;
                text-align: center;
                color: #79747e;
                font-size: 14px;
            }}
            .expiry-notice {{
                background-color: #fff8e1;
                border-left: 4px solid #ffb300;
                padding: 12px 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .expiry-notice p {{
                margin: 0;
                color: #663c00;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Postmark</h1>
            </div>
            <div class="content">
                <h2>Hi {first_name},</h2>
                <p>You've been invited{inviter_text} to join Postmark, our document management and translation system.</p>
                <p>To get started, please set up your password by clicking the button below:</p>
                <center>
                    <a href="{invite_link}" class="button">Set Up My Password</a>
                </center>
                <div class="expiry-notice">
                    <p><strong>Note:</strong> This invitation link will expire in 7 days for security purposes.</p>
                </div>
                <p>If you're having trouble clicking the button, you can copy and paste this link into your browser:</p>
                <p style="font-size: 12px; color: #79747e; word-break: break-all;">{invite_link}</p>
                <p>If you didn't expect this invitation, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Postmark. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version for email clients that don't support HTML
    text_content = f"""
    Hi {first_name},
    
    You've been invited{inviter_text} to join Postmark, our document management and translation system.
    
    To get started, please set up your password by visiting this link:
    {invite_link}
    
    Note: This invitation link will expire in 7 days for security purposes.
    
    If you didn't expect this invitation, you can safely ignore this email.
    
    © 2024 Postmark. All rights reserved.
    """
    
    try:
        # Send email via Resend
        params = {
            "from": "Postmark <gabe@zentall.com>",
            "to": [email],
            "subject": "You're invited to join Postmark",
            "html": html_content,
            "text": text_content
        }
        
        response = resend.Emails.send(params)
        print(f"✓ Invitation email sent to {email}")
        print(f"  Message ID: {response.get('id', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending invitation email to {email}: {e}")
        print(f"  💡 INVITE LINK (copy this): {invite_link}")
        return False


def send_password_reset(email: str, first_name: str, reset_token: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        email: Recipient email address
        first_name: Recipient's first name
        reset_token: Unique token for password reset
    
    Returns:
        True if email sent successfully, False otherwise
    """
    
    if not RESEND_API_KEY:
        print("Warning: RESEND_API_KEY not configured. Email not sent.")
        return False
    
    reset_link = f"{APP_URL}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #6750a4;
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .button {{
                display: inline-block;
                background-color: #6750a4;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 20px;
                font-weight: 500;
                margin: 24px 0;
            }}
            .footer {{
                background-color: #f3edf7;
                padding: 20px 30px;
                text-align: center;
                color: #79747e;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hi {first_name},</h2>
                <p>We received a request to reset your password for your Postmark account.</p>
                <center>
                    <a href="{reset_link}" class="button">Reset My Password</a>
                </center>
                <p>This link will expire in 1 hour for security purposes.</p>
                <p>If you didn't request this password reset, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Postmark. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": "Postmark <gabe@zentall.com>",
            "to": [email],
            "subject": "Reset your Postmark password",
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"✓ Password reset email sent to {email}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending password reset email: {e}")
        return False


if __name__ == '__main__':
    # Test email service
    print("Testing email service...")
    print(f"API Key configured: {bool(RESEND_API_KEY)}")
    print(f"App URL: {APP_URL}")
    
    if RESEND_API_KEY:
        print("\nTo test sending an email, uncomment the following line:")
        print('# send_user_invite("test@example.com", "Test", "test-token-123", "Admin")')
    else:
        print("\n⚠ RESEND_API_KEY not configured. Set it in .env file to enable email sending.")

