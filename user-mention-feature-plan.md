# User Mention Feature Plan

## Overview
Add ability to tag users in comments using @mentions. Tagged users receive email notifications with deep links to the document. If not authenticated, users authenticate first then are redirected to the document. Includes a notifications menu in the header showing unread mentions with a counter badge.

## Key Design Decisions

- **Deep Link Format**: `/documents/{doc_id}?tab=comments&comment={comment_id}` (opens document dialog - editor for Editors/Admins, read-only for Viewers in future)
- **Multiple Mentions**: Support multiple @mentions in a single comment
- **Mention Storage**: Store as metadata (user IDs) + display as `@username` in text
- **Email Notifications**: Sent only on initial comment creation (not on edits)
- **Login Redirect**: Support `?next=` parameter for post-authentication redirect
- **Notifications Menu**: Header menu with counter badge, shows most recent 20 unread mentions
- **Notification Display**: Shows comment preview (2-3 lines) and link to document

## Implementation Plan

### Phase 1: Backend - User Listing API

**File**: `app.py`

1. **Create endpoint to get active users** (`GET /api/users/active`):
   - **Access Control**: `@require_auth` (any authenticated user can see active users)
   - Query database for users where `is_active=True`
   - Return list with: `id`, `email`, `first_name`, `last_name`, `username` (full name)
   - Format: `{ "users": [...], "success": true }`

### Phase 2: Backend - Comment Storage Updates

**File**: `scripts/local_storage.py`

1. **Update comment structure**:
   - Add `mentioned_users` field (array of user IDs)
   - Keep `note` field with `@username` text for display

2. **Update `add_context_note()` method**:
   - Accept optional `mentioned_user_ids` parameter
   - Store mentioned user IDs in comment object
   - Return comment with `mentioned_users` field

### Phase 3: Backend - Email Notification Service

**File**: `scripts/email_service.py`

1. **Create `send_mention_notification()` function**:
   - **Parameters**: `email`, `first_name`, `commenter_name`, `document_title`, `doc_id`, `deep_link`
   - **Email Content**:
     - Subject: "{commenter_name} mentioned you in a comment"
     - HTML template with:
       - Greeting
       - "{commenter_name} mentioned you in a comment on document: {document_title}"
       - Button linking to deep link
       - Plain text fallback
   - **Deep Link Format**: `{APP_URL}/documents/{doc_id}?tab=comments&comment={comment_id}`
   - Use same styling as existing email templates

### Phase 4: Backend - Comment Endpoint Updates

**File**: `app.py`

1. **Update `POST /documents/<doc_id>/comments` endpoint**:
   - Accept `mentioned_user_ids` array in request body (or parse from text)
   - Extract mentioned user IDs from comment text (parse `@username` patterns)
   - Store mentioned user IDs in comment
   - After successful comment creation:
     - Get document title for notifications
     - For each mentioned user:
       - Create notification (call notification storage method)
       - Send email notification
     - Log any email failures (don't fail comment creation if email fails)

2. **Update comment response**:
   - Include `mentioned_users` array with user info (id, name, email)
   - Include `comment_id` for deep linking

### Phase 5: Backend - Notification System

**File**: `scripts/local_storage.py` or new `scripts/notifications.py`

1. **Create notification storage system**:
   - Store notifications per user (in database or separate storage)
   - Notification structure:
     ```json
     {
       "id": "notif_123",
       "user_id": 456,
       "type": "mention",
       "comment_id": "ctx_123",
       "document_id": "doc_456",
       "document_title": "Letter from 1935",
       "commenter_name": "John Doe",
       "comment_preview": "Hey @Jane, can you review...",
       "read": false,
       "created_at": "2025-01-01T12:00:00"
     }
     ```

2. **Notification methods**:
   - `create_notification(user_id, comment_id, document_id, commenter_name, comment_preview)` - Create notification
   - `get_user_notifications(user_id, limit=20, unread_only=False)` - Get notifications for user
   - `mark_notification_read(notification_id)` - Mark as read
   - `mark_all_read(user_id)` - Mark all as read
   - `get_unread_count(user_id)` - Get count of unread notifications

**File**: `app.py`

3. **Create notification endpoints**:
   - `GET /api/notifications` - Get user's notifications (most recent 20, unread first)
   - `GET /api/notifications/count` - Get unread count
   - `POST /api/notifications/<notification_id>/read` - Mark notification as read
   - `POST /api/notifications/read-all` - Mark all as read
   - All require authentication

### Phase 6: Backend - Deep Link & Authentication

**File**: `app.py`

1. **Update login endpoint** (`POST /login`):
   - Check for `next` parameter in request (from query string or form)
   - After successful login, redirect to `next` if provided, otherwise `/`
   - Validate `next` parameter (must be relative URL, prevent open redirect)

2. **Update document route** (`GET /documents/<doc_id>` or handle in frontend):
   - Check for `tab` query parameter
   - Check for `comment` query parameter (comment ID to highlight)
   - If user not authenticated:
     - Store deep link in session: `session['redirect_after_login'] = request.url`
     - Redirect to `/login?next={encoded_url}`
   - If authenticated:
     - Frontend handles opening document dialog with specified tab active
     - Scroll to/highlight specified comment if `comment` param present

### Phase 7: Frontend - Notifications Menu

**File**: `templates/browse.html`

1. **Add notifications menu to header**:
   - Icon button with Material Icons "notifications" or "notifications_none"
   - Counter badge showing unread count (hidden if 0)
   - Positioned in header navigation area
   - Material Design 3 styling

2. **Create notifications dropdown menu**:
   - Opens on click (below icon button)
   - Shows list of notifications (most recent 20)
   - Each notification shows:
     - Commenter name
     - Comment preview (2-3 lines, truncated)
     - Document title
     - Timestamp (relative: "2 hours ago")
     - Unread indicator (dot/badge)
   - "Mark all as read" button at bottom
   - "View all notifications" link (if more than 20)
   - Empty state: "No notifications"

3. **Notification item click handler**:
   - Mark notification as read
   - Open document dialog with comments tab
   - Scroll to/highlight the comment
   - Close notifications menu

4. **Real-time updates**:
   - Poll `/api/notifications/count` every 30 seconds
   - Update badge count
   - Refresh menu if open

### Phase 8: Frontend - Autocomplete UI

**File**: `templates/browse.html`

1. **Add autocomplete container**:
   - Positioned absolutely below comment input
   - Hidden by default
   - Material Design 3 styling
   - Max height with scroll
   - Z-index above other elements

2. **Add @mention detection**:
   - Listen for `@` keypress in comment textarea
   - On `@`:
     - Show autocomplete dropdown
     - Fetch active users from `/api/users/active`
     - Filter users based on text after `@`
   - On typing after `@`:
     - Filter autocomplete list
     - Highlight first item
   - On arrow keys:
     - Navigate autocomplete list
   - On Enter/Tab:
     - Insert selected username (format: `@First Last`)
     - Close autocomplete
   - On Escape:
     - Close autocomplete
   - On click outside:
     - Close autocomplete

3. **Autocomplete rendering**:
   - Show user full name (`First Last`)
   - Show email in smaller text below
   - Highlight matching text
   - Show selected state (hover/arrow key navigation)

### Phase 9: Frontend - Comment Submission Updates

**File**: `templates/browse.html`

1. **Update `addComment()` function**:
   - Parse comment text for `@username` patterns (match `@First Last` format)
   - Match usernames to user IDs from active users list
   - Include `mentioned_user_ids` array in POST request
   - Handle response with mentioned users info
   - After successful comment creation:
     - Notifications will be created automatically by backend

2. **Update comment rendering**:
   - Highlight `@username` mentions in comment text (different color/style)
   - Show mention badges/chips (optional visual indicator)

### Phase 10: Frontend - Deep Link Handling

**File**: `templates/browse.html`

1. **Add deep link handler on page load**:
   - Check URL for `doc_id` parameter (e.g., `?doc=doc_123`)
   - Check URL for `tab` parameter
   - Check URL for `comment` parameter (comment ID to highlight)
   - If document ID present:
     - Open document dialog using `showDocument(doc_id)`
     - Switch to specified tab if provided
     - Scroll to/highlight specified comment if provided
   - Remove query parameters from URL after handling

2. **Update `showDocument()` function**:
   - Accept optional `tab` and `commentId` parameters
   - Open specified tab if provided
   - Scroll to comment if provided (add highlight animation)
   - Update URL to include deep link params (for sharing)

3. **Update login redirect handling**:
   - On login page, check for `next` parameter
   - After successful login, redirect to `next` URL
   - Frontend handles deep link parameters from redirected URL

## Key Functions to Create/Modify

1. **`GET /api/users/active`** - NEW in `app.py`
   - Returns list of active users for autocomplete
   - Access: Any authenticated user

2. **`send_mention_notification()`** - NEW in `email_service.py`
   - Sends email notification to mentioned user
   - Includes deep link to document

3. **Notification storage methods** - NEW in `scripts/local_storage.py` or `scripts/notifications.py`
   - `create_notification()` - Create notification record
   - `get_user_notifications()` - Get notifications for user
   - `mark_notification_read()` - Mark as read
   - `mark_all_read()` - Mark all as read
   - `get_unread_count()` - Get unread count

4. **Notification API endpoints** - NEW in `app.py`
   - `GET /api/notifications` - Get user's notifications
   - `GET /api/notifications/count` - Get unread count
   - `POST /api/notifications/<id>/read` - Mark as read
   - `POST /api/notifications/read-all` - Mark all as read

5. **`add_context_note()`** - MODIFY in `local_storage.py`
   - Add `mentioned_user_ids` parameter
   - Store mentioned users in comment

6. **`POST /documents/<doc_id>/comments`** - MODIFY in `app.py`
   - Parse mentions from text
   - Create notifications for mentioned users
   - Send email notifications
   - Return mentioned users info

7. **`POST /login`** - MODIFY in `app.py`
   - Handle `next` parameter for redirect
   - Validate `next` URL (prevent open redirect)

8. **`addComment()`** - MODIFY in `browse.html`
   - Parse @mentions and include in request

9. **`@mention autocomplete handler`** - NEW in `browse.html`
   - Handle @ keypress, autocomplete display, user selection

10. **Notifications menu** - NEW in `browse.html`
    - Header icon with badge
    - Dropdown menu with notification list
    - Click handlers for notifications
    - Real-time count updates

## Data Structure Changes

**Comment Object** (in document JSON):
```json
{
  "id": "ctx_123",
  "note": "Hey @John Doe, can you review this?",
  "username": "Jane Smith",
  "createdAt": "2025-01-01T12:00:00",
  "mentioned_users": [123, 456],  // NEW: Array of user IDs
  "mentioned_users_info": [        // NEW: Cached user info for display
    {"id": 123, "name": "John Doe", "email": "john@example.com"},
    {"id": 456, "name": "Jane Smith", "email": "jane@example.com"}
  ]
}
```

**Notification Object** (stored per user):
```json
{
  "id": "notif_123",
  "user_id": 456,
  "type": "mention",
  "comment_id": "ctx_123",
  "document_id": "doc_456",
  "document_title": "Letter from 1935",
  "commenter_name": "John Doe",
  "comment_preview": "Hey @Jane, can you review this section?",
  "read": false,
  "created_at": "2025-01-01T12:00:00"
}
```

**Storage Options for Notifications**:
- Option A: Store in database (new `notifications` table) - Recommended
- Option B: Store in user's document metadata (simpler, but less scalable)
- Option C: Store in separate JSON file per user (middle ground)

## Security Considerations

- Validate `next` parameter in login (prevent open redirect attacks)
- Only allow relative URLs in `next` parameter
- Sanitize user input in comment text
- Rate limit email notifications (prevent spam)
- Validate mentioned user IDs exist and are active
- Don't expose inactive users in autocomplete
- Users can only see their own notifications
- Validate notification ownership before marking as read
- Limit notification query results (prevent DoS)

## Testing Considerations

1. **Unit Tests**:
   - Mention parsing from text
   - User ID matching
   - Email notification sending
   - Notification creation and retrieval
   - Unread count calculation

2. **Integration Tests**:
   - Comment creation with mentions
   - Notification creation
   - Email delivery
   - Deep link redirect flow
   - Authentication redirect
   - Notification marking as read

3. **Manual Testing**:
   - Type @ in comment, see autocomplete
   - Select user from autocomplete
   - Submit comment with mentions
   - Verify notification appears in menu
   - Verify badge count updates
   - Verify email received
   - Click email link (authenticated) → opens document dialog
   - Click email link (not authenticated) → login → redirect to document
   - Click notification in menu → opens document, highlights comment
   - Mark notification as read → badge count decreases
   - Mark all as read → all notifications marked read
   - Test multiple mentions in one comment
   - Test invalid @mentions (non-existent users)
   - Test notification limit (20 most recent)
   - Test notification ordering (unread first, then by date)

## Dependencies

- Existing comment system
- Existing email service (Resend API)
- Existing user database
- Existing authentication system
- Material Design 3 UI components

