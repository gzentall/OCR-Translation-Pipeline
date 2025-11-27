# Deployment Checklist - User Deletion Fix

## ✅ Pre-Deployment
- [x] Code changes made to `app.py`
- [x] Code changes made to `templates/users.html`  
- [x] No linting errors
- [x] Documentation created

## 📦 Deploy to Production

### 1. Commit Changes
```bash
cd /Users/gzentall/OCR-Translation-Pipeline
git add app.py templates/users.html *.md
git commit -m "Fix: Add session fixes and debugging for user deletion in production"
git push origin main
```

### 2. Verify Environment Variables
Make sure these are set in your production environment:
- `FLASK_ENV=production` ← **CRITICAL for ProxyFix to work**
- `SECRET_KEY=<your-secret-key>`
- `DATABASE_URL=<your-database-url>`

### 3. Deploy & Restart
- **Render**: Push to git (auto-deploys)
- **Railway**: Push to git (auto-deploys) or manual redeploy
- **Other**: Deploy your code and restart the server

## 🧪 Testing

### 1. Clear Browser Cache
- Open browser in Incognito/Private mode, OR
- Clear cookies for your domain

### 2. Login as Admin
- Go to your production site
- Login with an Admin account

### 3. Open DevTools
- Press F12
- Go to Console tab

### 4. Try to Delete a User
- Go to Users page
- Click delete on a test user
- Watch the console output

### 5. Check Server Logs
Look for these log lines in your hosting platform:
```
[AUTH] Endpoint: delete_user, Required role: Admin
[AUTH] Session authenticated: True
[AUTH] Session user_id: <your-id>
[AUTH] Session role: Admin
[AUTH] Authorization successful
[DELETE USER] Successfully deactivated user: <email>
```

## ✅ Success Indicators

**Browser shows:**
- `Response status: 200`
- `Response data: {success: true, ...}`
- Alert: "User deactivated successfully"
- Page reloads and user is gone/deactivated

**Server logs show:**
- `[AUTH] Authorization successful`
- `[DELETE USER] Successfully deactivated user`

## ❌ If It Fails

### Collect This Information:

1. **Browser Console Output** (screenshot or copy)
2. **Server Logs** (the [AUTH] and [DELETE USER] lines)
3. **Environment Variables**:
   ```bash
   echo "FLASK_ENV: $FLASK_ENV"
   ```

### Common Issues:

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `Session authenticated: False` | Session not persisting | Check FLASK_ENV=production, clear cookies |
| `No role assigned` | Role not in session | Re-login, check user role in database |
| `Insufficient permissions` | User is not Admin | Verify user role in database |
| HTTP 401 | Not authenticated | Session/cookie issue, check ProxyFix |
| HTTP 403 | Not authorized | Check user role |
| HTTP 500 | Server error | Check full server logs for exception |

## 📚 Reference Documents

- `TROUBLESHOOT_USER_DELETION.md` - Detailed troubleshooting guide
- `USER_DELETION_FIX_SUMMARY.md` - Technical details of changes

## 🆘 Need Help?

Share these items:
1. Server logs with [AUTH] and [DELETE USER] lines
2. Browser console screenshot
3. Your hosting platform (Render/Railway/etc.)
4. Value of FLASK_ENV in production

## 🎯 Expected Timeline

- Deploy: 2-5 minutes
- Test: 1-2 minutes
- **Total: ~5-10 minutes**

## Notes

- ✅ No breaking changes
- ✅ Safe to deploy anytime
- ✅ Backward compatible
- ✅ Can be rolled back if needed
- ✅ Adds debugging that helps with other issues too

