# Admin Activity Logging System

**SPEC-005: Admin Dashboard**
**US-100: Admin Activity Logging System**

## Overview

The Admin Activity Logging System provides comprehensive audit logging for all admin operations, ensuring compliance, accountability, and security monitoring.

## Features

- ✅ **Automatic Logging**: Log all admin actions with minimal code changes
- ✅ **Rich Metadata**: Captures IP address, user agent, target resources, and custom details
- ✅ **Query API**: Filter logs by admin user, action type, target, date range
- ✅ **Summary Statistics**: Get activity summaries and most active admins
- ✅ **Retention Policy**: Automatic cleanup of logs older than 90 days (configurable)
- ✅ **Background Services**: Non-blocking async logging with background cleanup

## Database Schema

The system uses the `admin_activity_log` table created by migration `0130_admin_activity_logs`:

```sql
CREATE TABLE admin_activity_log (
    id UUID PRIMARY KEY,
    admin_user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### GET /admin/activity
Query admin activity logs with filters.

**Query Parameters:**
- `admin_user_id` (optional): Filter by admin user ID
- `action` (optional): Filter by action type
- `target_type` (optional): Filter by target type (user, team, organization, etc.)
- `target_id` (optional): Filter by target ID
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter
- `limit` (default: 100): Maximum results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "admin_user_id": "uuid",
      "action": "create_organization",
      "target_type": "organization",
      "target_id": "uuid",
      "details": {"organization_name": "Example Org"},
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2025-11-02T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### GET /admin/activity/summary
Get summary statistics of admin activity.

**Query Parameters:**
- `admin_user_id` (optional): Filter by admin user ID
- `days` (default: 30): Number of days to include

**Response:**
```json
{
  "total_actions": 150,
  "action_distribution": {
    "create_organization": 10,
    "update_user": 25,
    "delete_user": 5
  },
  "most_active_admins": [
    {"admin_user_id": "uuid", "count": 50}
  ],
  "period_days": 30,
  "start_date": "2025-10-03T10:00:00Z"
}
```

## Usage Examples

### Basic Logging

```python
from fastapi import Depends, Request
from server.routers.admin_activity import get_activity_logger
from server.admin.helpers import get_admin_user_id_from_request, log_admin_action_async

@router.post("/admin/users")
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user),
    activity_logger = Depends(get_activity_logger),
):
    # Create user...
    user = db.create_user(...)

    # Log admin action
    admin_user_id = get_admin_user_id_from_request(current_user)
    if admin_user_id:
        await log_admin_action_async(
            activity_logger,
            admin_user_id=admin_user_id,
            action="create_user",
            target_type="user",
            target_id=user.id,
            details={"email": user.email, "role": user.role},
            request=request,
        )

    return user
```

### Using AdminAction Enum

For type safety, use the `AdminAction` enum:

```python
from server.admin.activity_logger import AdminAction

await log_admin_action_async(
    activity_logger,
    admin_user_id=admin_user_id,
    action=AdminAction.CREATE_USER.value,
    target_type="user",
    target_id=user.id,
    details={"email": user.email},
    request=request,
)
```

### Logging Without Request Object

If you don't have a Request object, you can skip IP/user agent:

```python
await log_admin_action_async(
    activity_logger,
    admin_user_id=admin_user_id,
    action="update_team",
    target_type="team",
    target_id=team_id,
    details={"name": "New Team Name"},
    request=None,  # No IP/user agent captured
)
```

## Integration Checklist

- [x] Database migration created (`0130_admin_activity_logs.py`)
- [x] AdminActivityLogger class implemented
- [x] API endpoints created (`/admin/activity`, `/admin/activity/summary`)
- [x] Helper functions for easy integration
- [ ] Integration into user management endpoints
- [ ] Integration into team management endpoints
- [ ] Integration into organization management endpoints (example done)
- [ ] Integration into context management endpoints
- [ ] Migration run (requires database)
- [ ] Integration tests written

## Migration

To create the table, run:

```bash
python3 -m alembic upgrade head
```

## Retention Policy

By default, logs are retained for 90 days. The cleanup service runs hourly and automatically removes logs older than the retention period.

To change retention period:

```python
activity_logger = AdminActivityLogger(db_pool, retention_days=180)  # 180 days
```

## Testing

The system gracefully handles failures:
- If logging fails, it doesn't break the main operation
- If database connection fails, logging is skipped
- All logging operations are non-blocking

## Future Enhancements

- [ ] Real-time webhook notifications for sensitive actions
- [ ] Export logs to external audit systems
- [ ] Custom retention policies per action type
- [ ] Integration with SIEM systems
- [ ] Dashboard UI for viewing logs
