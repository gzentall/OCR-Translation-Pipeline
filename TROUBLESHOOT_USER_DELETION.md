# Troubleshooting User Deletion in Production

## Problem
Unable to delete users in production environment.

## Changes Made

### 1. Enhanced Logging
Added detailed logging to help diagnose the issue:
- Authentication/authorization logging in `require_role()` decorator
- User deletion operation logging in both soft delete and hard delete endpoints
- Frontend console logging with detailed error messages

### 2. Session Configuration Improvements
- Added `ProxyFix` middleware for production environments behind load balancers/proxies
- Configured explicit session cookie settings
- Added session lifetime configuration

### 3. Frontend Error Handling
- Enhanced error messages with details
- Added `credentials: 'same-origin'` to fetch requests to ensure cookies are sent
- Console logging for debugging

## How to Diagnose the Issue

### Step 1: Check Server Logs
After deploying these changes, try to delete a user and check your production logs for:

```
[AUTH] Endpoint: delete_user, Required role: Admin
[AUTH] Session authenticated: True/False
[AUTH] Session user_id: <id>
[AUTH] Session role: <role>
```

**Common Issues:**
- If `Session authenticated: False` → Session is not being maintained
- If `Session role: None` → Role is not being stored in session
- If `Insufficient permissions` → User doesn't have Admin role

### Step 2: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Try to delete a user
4. Look for error messages starting with:
   - `deactivateUser called for:`
   - `Response status:`
   - `Response data:`

**Common Issues:**
- HTTP 401: Authentication failed
- HTTP 403: Authorization failed (not Admin)
- HTTP 500: Server error (check server logs)

### Step 3: Check Browser Cookies
1. Open DevTools → Application/Storage tab
2. Look for cookie named `ocr_session`
3. Verify:
   - Cookie exists
   - Cookie is not expired
   - Cookie has correct domain
   - Cookie Secure flag matches (should be Secure for HTTPS)

## Common Production Issues & Fixes

### Issue 1: Sessions Not Persisting Behind Proxy/Load Balancer
**Symptom:** User gets logged out randomly, or session data is lost

**Solution:** The `ProxyFix` middleware has been added. Make sure your environment variable is set:
```bash
FLASK_ENV=production
```

### Issue 2: HTTPS/Cookie Secure Mismatch
**Symptom:** Cookies not being sent, 401 errors

**Check:**
1. Is your production site using HTTPS?
2. Is `FLASK_ENV=production` set correctly?

**Temporary Fix (NOT RECOMMENDED for production):**
If you need to test, you can temporarily disable secure cookies by setting:
```bash
FLASK_ENV=development
```

### Issue 3: Session Cookie Domain Mismatch
**Symptom:** Cookie is set but not sent with requests

**Check:**
- Are you accessing the site via the correct domain?
- Is there a www vs non-www mismatch?

**Fix:** Add to your environment:
```bash
SESSION_COOKIE_DOMAIN=.yourdomain.com
```

### Issue 4: Database Connection Issues
**Symptom:** 500 errors when trying to delete

**Check server logs for:**
```
[DELETE USER] Error deleting user: <error message>
```

**Common causes:**
- Database connection pooling issues
- Transaction timeout
- Database lock

### Issue 5: User Role Not Set Correctly
**Symptom:** "Insufficient permissions" error

**Fix:** Check the user's role in the database:
```sql
SELECT id, email, role, is_active FROM users WHERE email = 'your-admin@email.com';
```

Make sure role is `Admin` (case-sensitive).

## Quick Fixes to Try

### 1. Clear Session and Re-login
1. Logout from production
2. Clear browser cookies for your domain
3. Login again
4. Try deleting a user

### 2. Verify Admin User in Database
Run this to ensure your user is an Admin:
```python
python3 -c "
from scripts.database import DatabaseSession, User
with DatabaseSession() as db:
    user = db.query(User).filter_by(email='YOUR_EMAIL').first()
    if user:
        print(f'Role: {user.role.value}, Active: {user.is_active}')
    else:
        print('User not found')
"
```

### 3. Check Environment Variables
Make sure these are set in production:
```bash
FLASK_ENV=production
SECRET_KEY=<your-secret-key>
DATABASE_URL=<your-database-url>
```

### 4. Restart Your Production Server
After deploying these changes, restart your application to ensure all changes are loaded.

## Testing the Fix

1. **Deploy the updated code** to production
2. **Restart your application server**
3. **Clear your browser cache and cookies**
4. **Login again** as an Admin user
5. **Open browser DevTools** (F12) and go to Console tab
6. **Try to delete a user**
7. **Check both:**
   - Browser console for frontend logs
   - Server logs for backend logs

## Expected Successful Output

### Browser Console:
```
deactivateUser called for: 4 Test User
Sending DELETE request to: /api/users/4
Response status: 200
Response data: {success: true, message: "User deactivated successfully"}
```

### Server Logs:
```
[AUTH] Endpoint: delete_user, Required role: Admin
[AUTH] Session authenticated: True
[AUTH] Session user_id: 1
[AUTH] Session role: Admin
[AUTH] Authorization successful
[DELETE USER] Request received for user_id: 4
[DELETE USER] Current session user: 1, role: Admin
[DELETE USER] Deactivating user: test@example.com
[DELETE USER] Successfully deactivated user: test@example.com
```

## Still Not Working?

If after all these steps it's still not working, provide me with:

1. **Server logs** showing the [AUTH] and [DELETE USER] messages
2. **Browser console output** when attempting deletion
3. **Browser cookie information** (screenshot of the ocr_session cookie)
4. **Environment**: What platform are you hosting on? (Render, Railway, Heroku, etc.)

## Rollback Instructions

If these changes cause issues, you can rollback by:
```bash
git diff HEAD app.py templates/users.html
git checkout app.py templates/users.html
```

Then redeploy.

