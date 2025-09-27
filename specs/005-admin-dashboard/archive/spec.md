# Spec 005: Admin Dashboard for User/Team/Organization Management

## Overview

Build a web-based admin dashboard to manage users, teams, organizations, and context permissions in the mem0 system. This addresses the current gap where user management requires direct database access.

## Problem Statement

Currently, mem0 has:
- ✅ Database schema for users/teams/organizations
- ✅ JWT authentication with role-based permissions
- ✅ Environment variable user ID assignment
- ❌ No UI for managing users, teams, or permissions
- ❌ No way for non-technical admins to manage the system

## Requirements

### Functional Requirements

#### User Management
- **Create Users**: Add new users with email, name, role assignment
- **Edit Users**: Update user details, roles, active status
- **Delete Users**: Deactivate users (soft delete to preserve context ownership)
- **List Users**: Paginated user list with search and filtering
- **User Details**: View user's contexts, teams, and activity

#### Team Management
- **Create Teams**: Add teams with name, description, and initial members
- **Edit Teams**: Update team details and membership
- **Delete Teams**: Remove teams (with context ownership transfer)
- **List Teams**: View all teams with member counts and activity
- **Team Details**: View team contexts, members, and permissions

#### Organization Management
- **Create Organizations**: Add organizations with hierarchy
- **Edit Organizations**: Update org structure and settings
- **Organization Hierarchy**: Visual tree view of org structure
- **Cross-Org Permissions**: Manage access between organizations

#### Context Management
- **Context Ownership**: View and transfer context ownership
- **Sharing Permissions**: Grant team/org access to contexts
- **Context Browser**: Search and browse all contexts
- **Usage Analytics**: View context activity and memory counts

#### System Administration
- **Dashboard Overview**: System health, user counts, active contexts
- **Activity Logs**: User actions and system events
- **Database Status**: Connection health, storage usage
- **Configuration**: System settings and environment variables

### Non-Functional Requirements

#### Performance
- **Response Time**: <500ms for all admin operations
- **Pagination**: Handle 10,000+ users efficiently
- **Search**: Real-time search with <200ms response
- **Caching**: Cache frequently accessed data

#### Security
- **Admin Authentication**: Secure login for admin users
- **Role-Based Access**: Different admin permission levels
- **Audit Trail**: Log all admin actions
- **Session Management**: Secure session handling

#### Usability
- **Responsive Design**: Works on desktop and tablet
- **Intuitive Navigation**: Clear menu structure
- **Bulk Operations**: Select multiple items for batch actions
- **Error Handling**: Clear error messages and recovery

## Technical Design

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Web UI  │    │  FastAPI Admin  │    │   PostgreSQL    │
│   (React SPA)   │◄──►│   Endpoints     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Static Assets  │    │   JWT Auth      │    │  Existing MCP   │
│   (Nginx)       │    │   Middleware    │    │   & CLI Tools   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Backend Implementation

#### New FastAPI Endpoints
```python
# Admin User Management
POST   /admin/users              # Create user
GET    /admin/users              # List users (paginated)
GET    /admin/users/{user_id}    # Get user details
PUT    /admin/users/{user_id}    # Update user
DELETE /admin/users/{user_id}    # Deactivate user

# Admin Team Management
POST   /admin/teams              # Create team
GET    /admin/teams              # List teams
GET    /admin/teams/{team_id}    # Get team details
PUT    /admin/teams/{team_id}    # Update team
DELETE /admin/teams/{team_id}    # Delete team

# Admin Organization Management
POST   /admin/organizations      # Create organization
GET    /admin/organizations      # List organizations
GET    /admin/organizations/{org_id} # Get org details
PUT    /admin/organizations/{org_id} # Update organization

# Admin Context Management
GET    /admin/contexts           # List all contexts
PUT    /admin/contexts/{context_id}/owner # Transfer ownership
POST   /admin/contexts/{context_id}/share # Grant access

# Admin Dashboard
GET    /admin/dashboard          # System overview
GET    /admin/activity           # Activity logs
GET    /admin/health             # System health
```

#### Database Extensions
```sql
-- Admin activity logging
CREATE TABLE admin_activity_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- System configuration
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Frontend Implementation

#### Technology Stack
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **State Management**: React Query for server state
- **Routing**: React Router for navigation
- **Forms**: React Hook Form with validation
- **Charts**: Chart.js for analytics visualization

#### Key Components
```typescript
// Core Layout
AdminLayout          // Main layout with navigation
Dashboard            // System overview page
UserManagement       // User CRUD operations
TeamManagement       // Team CRUD operations
ContextBrowser       // Context search and management
ActivityLog          // System activity viewer

// Shared Components
DataTable           // Reusable table with pagination/search
UserSelector        // User picker component
PermissionMatrix    // Visual permission editor
ConfirmDialog       // Confirmation modals
LoadingSpinner      // Loading states
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up React admin app structure
- [ ] Create FastAPI admin endpoints
- [ ] Implement JWT admin authentication
- [ ] Build basic user CRUD operations
- [ ] Create responsive admin layout

### Phase 2: User & Team Management (Week 2)
- [ ] Complete user management UI
- [ ] Build team creation and management
- [ ] Implement user-team assignment
- [ ] Add search and filtering
- [ ] Create bulk operations

### Phase 3: Context & Permissions (Week 3)
- [ ] Build context browser
- [ ] Implement ownership transfer
- [ ] Create permission sharing UI
- [ ] Add context analytics
- [ ] Build activity logging

### Phase 4: Dashboard & Polish (Week 4)
- [ ] Create system dashboard
- [ ] Add usage analytics charts
- [ ] Implement system health monitoring
- [ ] Add comprehensive error handling
- [ ] Performance optimization

## API Specifications

### User Management API

#### Create User
```http
POST /admin/users
Content-Type: application/json
Authorization: Bearer {admin_jwt}

{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "teams": [1, 2],
  "organizations": [1]
}

Response: 201 Created
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### List Users
```http
GET /admin/users?page=1&limit=50&search=john&role=user
Authorization: Bearer {admin_jwt}

Response: 200 OK
{
  "users": [
    {
      "id": 123,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "active": true,
      "last_active": "2024-01-15T09:00:00Z",
      "context_count": 5,
      "team_count": 2
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3
  }
}
```

### Team Management API

#### Create Team
```http
POST /admin/teams
Content-Type: application/json
Authorization: Bearer {admin_jwt}

{
  "name": "Frontend Team",
  "description": "React and UI development",
  "members": [123, 124, 125],
  "organization_id": 1
}

Response: 201 Created
{
  "id": 10,
  "name": "Frontend Team",
  "description": "React and UI development",
  "member_count": 3,
  "context_count": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Security Considerations

### Admin Authentication
- **Separate Admin Roles**: `admin`, `super_admin` roles
- **Admin Session Management**: Shorter session timeouts
- **Multi-Factor Authentication**: Optional 2FA for admin accounts
- **IP Restrictions**: Limit admin access to specific networks

### Audit Trail
- **Action Logging**: All admin actions logged with details
- **Data Retention**: Configurable log retention periods
- **Export Capability**: Export audit logs for compliance
- **Real-time Alerts**: Notify on suspicious admin activity

### Data Protection
- **Soft Deletes**: Preserve data integrity when "deleting" users
- **Backup Validation**: Ensure backups before destructive operations
- **Permission Validation**: Double-check permissions before granting access
- **Rate Limiting**: Prevent admin API abuse

## Testing Strategy

### Unit Tests
- Admin endpoint functionality
- Permission validation logic
- Data transformation utilities
- Component rendering and behavior

### Integration Tests
- End-to-end admin workflows
- Database transaction integrity
- Authentication and authorization
- API error handling

### Manual Testing
- Admin user experience flows
- Responsive design validation
- Performance under load
- Security penetration testing

## Deployment

### Development Environment
```bash
# Start admin development server
cd admin-ui
npm run dev

# Start FastAPI with admin endpoints
cd server
python main.py --enable-admin
```

### Production Deployment
```bash
# Build admin UI
cd admin-ui
npm run build

# Deploy with nginx
cp -r build/* /var/www/mem0-admin/

# Configure nginx
location /admin {
    try_files $uri $uri/ /admin/index.html;
}

location /api/admin {
    proxy_pass http://localhost:8000;
}
```

## Success Metrics

### Functional Success
- [ ] Admin can create/manage users without database access
- [ ] Team management workflows complete in <2 minutes
- [ ] Context ownership transfers work correctly
- [ ] All admin actions are properly logged

### Performance Success
- [ ] Admin UI loads in <2 seconds
- [ ] User list with 1000+ users loads in <1 second
- [ ] Search results appear in <200ms
- [ ] Bulk operations complete in <5 seconds

### User Experience Success
- [ ] Non-technical admins can use the system
- [ ] Clear error messages and recovery paths
- [ ] Responsive design works on tablets
- [ ] Intuitive navigation requires no training

This admin dashboard will transform mem0 from a developer-only tool into a production-ready system that non-technical stakeholders can manage effectively.
