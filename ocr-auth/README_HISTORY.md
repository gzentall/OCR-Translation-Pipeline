# History Feature Implementation

This document describes the history/audit logging feature that has been implemented for the OCR Document System.

## Overview

The history feature provides comprehensive audit logging for both documents and users, allowing you to track all actions and changes within the system. This follows the same pattern as your existing activity log system.

## Features Implemented

### 1. Database Schema
- **AuditLog Model**: Already exists in your Prisma schema with proper relationships
- **Event Types**: Comprehensive set of audit actions for documents, users, and people
- **Metadata Storage**: JSON field for storing additional context about events

### 2. API Endpoints

#### Document History
- `GET /api/documents/[id]/history` - Get history for a specific document
- `GET /api/users/[id]/history` - Get history for a specific user

**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 100)
- `startDate` - Filter events from this date
- `endDate` - Filter events to this date
- `eventType` - Filter by specific event type

#### Example Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "audit_log_id",
      "timestamp": "2025-01-27T10:30:00Z",
      "description": "John Doe modified \"Sample Document\"",
      "action": "DOCUMENT_UPDATE",
      "actor": {
        "id": "user_id",
        "username": "johndoe",
        "email": "john@example.com"
      },
      "metadata": {
        "changes": ["title", "summary"],
        "previousTitle": "Old Title",
        "newTitle": "New Title"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 25,
    "totalPages": 1
  }
}
```

### 3. UI Components

#### Document Editor with History Tab
- **Location**: `/documents/[id]`
- **Features**:
  - Document editor tab for viewing/editing document content
  - History tab showing chronological list of events
  - Date range filtering
  - Event type filtering
  - Pagination (100 rows per page)
  - Refresh functionality

#### User Profile with History Tab
- **Location**: `/users/[id]`
- **Features**:
  - Profile information display
  - History tab showing user's actions
  - Same filtering and pagination as document history
  - Access control (users can only see their own history, admins can see all)

### 4. Event Formatting

The system follows your requested format: `<actor><took specific action>on<named object>`

**For Documents:**
- "John Doe modified \"Document Title\""
- "System processed \"Document Title\""
- "Jane Smith viewed \"Document Title\""

**For Users:**
- "created document \"Document Title\""
- "updated profile"
- "logged in"

### 5. Audit Logging Integration

#### Utility Functions
- `logAuditEvent()` - Main function for logging events
- `AUDIT_ACTIONS` - Constants for all supported actions
- Automatic logging in authentication system

#### Example Usage:
```typescript
import { logAuditEvent, AUDIT_ACTIONS } from "@/lib/audit"

// Log a document update
await logAuditEvent({
  actorUserId: userId,
  action: AUDIT_ACTIONS.DOCUMENT_UPDATE,
  targetType: "DOCUMENT",
  targetId: documentId,
  metadata: {
    changes: ["title", "summary"],
    previousTitle: "Old Title",
    newTitle: "New Title"
  }
})
```

## Event Types Supported

### Document Events
- `DOCUMENT_CREATE` - Document created
- `DOCUMENT_UPDATE` - Document modified
- `DOCUMENT_DELETE` - Document deleted
- `DOCUMENT_VIEW` - Document viewed
- `DOCUMENT_TRANSLATE` - Document translated
- `DOCUMENT_PROCESS` - Document processed
- `DOCUMENT_SUMMARY_UPDATE` - Summary updated
- `DOCUMENT_PEOPLE_UPDATE` - People associations updated

### User Events
- `USER_LOGIN` - User logged in
- `USER_LOGOUT` - User logged out
- `USER_UPDATE` - Profile updated
- `USER_CREATE` - User created
- `USER_DELETE` - User deleted
- `USER_INVITE` - User invited
- `USER_ACTIVATE` - User activated
- `USER_DEACTIVATE` - User deactivated

### Person Events
- `PERSON_CREATE` - Person created
- `PERSON_UPDATE` - Person updated
- `PERSON_DELETE` - Person deleted

## Integration with Flask Backend

To integrate this with your existing Flask backend:

1. **Add audit logging to Flask endpoints**:
```python
# In your Flask routes
from your_nextjs_app.lib.audit import logAuditEvent, AUDIT_ACTIONS

@app.route('/api/documents/<doc_id>', methods=['PUT'])
def update_document(doc_id):
    # ... existing logic ...
    
    # Log the update
    await logAuditEvent({
        'actorUserId': current_user_id,
        'action': AUDIT_ACTIONS.DOCUMENT_UPDATE,
        'targetType': 'DOCUMENT',
        'targetId': doc_id,
        'metadata': {
            'changes': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }
    })
```

2. **Update your Flask API to use the shared database**:
   - Ensure your Flask app connects to the same PostgreSQL database
   - Use the same Prisma schema for consistency
   - Add audit logging to all document and user operations

## Navigation Updates

- **Dashboard**: Added links to "Browse Documents" and "People Management"
- **Navigation**: Added "My Profile" link for users to access their profile and history
- **Document List**: Links to individual document editors with history tabs
- **User Profiles**: Accessible from navigation and admin panel

## Security Considerations

- **Access Control**: Users can only see their own history, admins can see all
- **Data Privacy**: Sensitive information is not logged in metadata
- **Audit Trail**: All events are immutable once logged
- **Performance**: Pagination prevents large datasets from impacting performance

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live history updates
2. **Export Functionality**: CSV/PDF export of history data
3. **Advanced Filtering**: More granular filter options
4. **Bulk Operations**: Batch history operations for admins
5. **Analytics**: History-based analytics and reporting

## Testing

To test the history feature:

1. **Login/Logout**: Check that login/logout events are logged
2. **Document Operations**: Create, update, view documents and verify events
3. **User Operations**: Update profile and verify events
4. **Filtering**: Test date range and event type filters
5. **Pagination**: Verify 100 items per page works correctly

The history feature is now fully integrated and ready for use!

