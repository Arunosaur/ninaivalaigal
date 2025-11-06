# Spec 005: Admin Dashboard for User/Team/Organization Management

> **⚠️ ARCHITECTURE UPDATE (2025-11-02):**
> This SPEC has been updated to use **FastAPI + Jinja2 templates** instead of React/Next.js.
> **See:** `docs/ADMIN_UI_FASTAPI_ANALYSIS.md` for detailed analysis.

## Overview

Build a web-based admin dashboard to manage users, teams, organizations, and context permissions in the mem0 system. This addresses the current gap where user management requires direct database access.

**Implementation Approach:** FastAPI serves Jinja2 templates with Alpine.js for interactivity. No separate frontend build process required.

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
- **Response Time**: &lt;500ms for all admin operations
- **Page Load**: P95 latency &lt;1s for all admin pages
- **Pagination**: Handle 10,000+ users efficiently
- **Search**: Real-time search with &lt;200ms response
- **Caching**: Cache frequently accessed data (template caching, Redis for queries)
- **Template Optimization**: Jinja2 template caching enabled
- **Static Assets**: CDN for static assets (CSS, JS, images)

#### Security
- **Admin Authentication**: Secure login for admin users
- **Role-Based Access**: Different admin permission levels (admin, super_admin, staff)
- **Network Security**: VPN/Tailscale access required for admin UI
- **IP Whitelist**: Network-level IP whitelist enforcement
- **Session Management**: Secure session handling with 15-minute expiration
- **Audit Trail**: Log all admin actions with details
- **SSL/TLS**: Internal CA or self-signed certificates for HTTPS

#### Usability
- **Responsive Design**: Works on desktop and tablet
- **Intuitive Navigation**: Clear menu structure
- **Bulk Operations**: Select multiple items for batch actions
- **Error Handling**: Clear error messages and recovery

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Admin Router (/admin/*)                              │  │
│  │  ├── Jinja2 Templates (templates/admin/*.html)       │  │
│  │  ├── Alpine.js (client-side interactivity)            │  │
│  │  └── TailwindCSS (styling)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Admin Endpoints (/api/v1/admin/*)          │  │
│  │  ├── User Management                                   │  │
│  │  ├── Team Management                                   │  │
│  │  ├── Context Management                                │  │
│  │  └── Activity Logging                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database + Redis Sessions + JWT Auth           │
└─────────────────────────────────────────────────────────────┘
```

**Key Changes:**
- ✅ **No separate frontend build** - Templates served directly by FastAPI
- ✅ **Single deployment** - FastAPI handles both UI and API
- ✅ **Simpler architecture** - No CORS, no separate static hosting
- ✅ **IP whitelisting** - FastAPI middleware handles security

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

> **⚠️ ARCHITECTURE UPDATE (2025-11-02):**
> This SPEC has been updated to reflect our current architecture decision: **FastAPI + Jinja2 templates** instead of React/Next.js.
> **See:** `docs/ADMIN_UI_FASTAPI_ANALYSIS.md` and `docs/FRONTEND_ARCHITECTURE_DECISION.md`

#### Technology Stack
- **Backend Framework**: FastAPI (Python)
- **Template Engine**: Jinja2 (built into FastAPI)
- **Styling**: TailwindCSS (via CDN or build process)
- **Interactivity**: Alpine.js (lightweight, ~3KB) or HTMX
- **Charts**: Chart.js (via CDN) for analytics visualization
- **Forms**: Server-side form handling with FastAPI

#### Key Components (Jinja2 Templates)
```
templates/admin/
├── base.html              # Base layout with navigation
├── dashboard.html         # System overview page
├── users.html             # User CRUD operations
├── teams.html             # Team CRUD operations
├── contexts.html          # Context search and management
├── activity.html          # System activity viewer
└── components/            # Reusable Jinja2 macros and partials
    ├── macros.html        # Common macros (buttons, forms, tables)
    ├── user_table.html    # Reusable user table macro
    ├── team_card.html     # Team display component macro
    ├── context_list.html  # Context list component macro
    └── pagination.html     # Pagination macro
```

**Template Organization Strategy:**
- **Macros**: Reusable Jinja2 macros in `components/macros.html` for common UI patterns
- **Partials**: Template partials for complex components (e.g., `user_table.html`)
- **Template Inheritance**: Base template with blocks for content, scripts, styles
- **Component Reuse**: Shared macros reduce duplication between admin pages

#### Implementation Pattern
```python
# FastAPI Router Example
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates/admin")

@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    users = db.query(User).all()
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "users": users}
    )
```

```jinja2
{# templates/admin/users.html #}
{% extends "admin/base.html" %}

{% block content %}
<div x-data="{ users: {{ users | tojson }}, searchTerm: '' }">
    <h2 class="text-3xl font-bold mb-4">User Management</h2>

    <input
        type="text"
        x-model="searchTerm"
        placeholder="Search users..."
        class="mb-4"
    >

    <table class="min-w-full">
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Teams</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr x-show="searchTerm === '' || '{{ user.name }}'.includes(searchTerm)">
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.team_count }}</td>
                <td>
                    <span class="px-2 py-1 rounded {% if user.active %}bg-green-600{% else %}bg-red-600{% endif %}">
                        {{ user.status }}
                    </span>
                </td>
                <td>
                    <a href="/admin/users/{{ user.id }}/edit">Edit</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up FastAPI admin router and template directory
- [ ] Create FastAPI admin endpoints (already exists)
- [ ] Implement JWT admin authentication (already exists)
- [ ] Build basic user CRUD templates (Jinja2)
- [ ] Create responsive admin base template (TailwindCSS)

### Phase 2: User & Team Management (Week 2)
- [ ] Complete user management templates (Jinja2)
- [ ] Build team creation and management templates
- [ ] Implement user-team assignment forms
- [ ] Add search and filtering (Alpine.js)
- [ ] Create bulk operations (server-side processing)

### Phase 3: Context & Permissions (Week 3)
- [ ] Build context browser templates
- [ ] Implement ownership transfer forms
- [ ] Create permission sharing UI (Jinja2 + Alpine.js)
- [ ] Add context analytics (Chart.js)
- [ ] Build activity logging templates

### Phase 4: Dashboard & Polish (Week 4)
- [ ] Create system dashboard template
- [ ] Add usage analytics charts (Chart.js)
- [ ] Implement system health monitoring (FastAPI endpoints)
- [ ] Add comprehensive error handling (FastAPI exception handlers)
- [ ] Performance optimization (template caching, CDN for static assets)

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

### Network Security
- **VPN/Tailscale Required**: Admin UI accessible only via VPN connection
- **IP Whitelist Enforcement**:
  - Network level: Nginx/firewall IP whitelist
  - Application level: FastAPI middleware IP check
  - Only allow internal network ranges (10.0.0.0/8, 192.168.0.0/16)
- **No Public Access**: Admin UI must never be exposed to public internet

### Admin Authentication
- **Separate Admin Roles**: `admin`, `super_admin`, `staff` roles
- **Admin Session Management**: 15-minute session expiration (shorter than customer sessions)
- **Multi-Factor Authentication**: Optional 2FA for admin accounts (future enhancement)
- **JWT Token Validation**: Strict JWT RS256 validation with role claims

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

### Smoke Tests (Backend Connectivity)
- Backend health endpoint reachability (`/health`)
- PostgreSQL connection verification via API
- Redis cache operations via API
- Database query execution tests
- End-to-end admin API workflows

**Example Smoke Test:**
```python
# tests/integration/test_admin_connectivity.py
def test_backend_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_database_connectivity():
    response = client.get("/api/v1/admin/users")
    assert response.status_code in [200, 401]  # 401 if no auth, but connection works

def test_redis_connectivity():
    # Test Redis operations via API
    response = client.post("/api/v1/admin/cache/test")
    assert response.status_code in [200, 401]
```

### Manual Testing
- Admin user experience flows
- Responsive design validation
- Performance under load
- Security penetration testing

## Deployment

### Development Environment
```bash
# Start FastAPI with admin endpoints and templates
cd services/core-api
python -m uvicorn main:app --reload --port 13390

# Admin UI accessible at: http://localhost:13390/admin
```

### Production Deployment (Internal Server)

**Network Security:**
- Admin UI must be accessible only via VPN/Tailscale
- IP whitelist enforced at network level (firewall/nginx)
- No public internet access

**Deployment Architecture:**
```
VPN/Tailscale → Nginx (SSL Termination + IP Whitelist) → FastAPI (systemd/uvicorn) → PostgreSQL/Redis
```

**Pre-Deployment Verification:**
```bash
# 1. Verify backend health
curl http://localhost:13390/health
# Expected: {"status":"ok"}

# 2. Verify PostgreSQL connection
container exec ninaivalaigal-dev-db \
  psql -U nina -d ninaivalaigal_dev -c "SELECT 1"
# Expected: Returns 1

# 3. Verify Redis connection
container exec ninaivalaigal-dev-redis redis-cli PING
# Expected: PONG

# 4. Verify FastAPI can query database
curl http://localhost:13390/api/v1/admin/health
# Expected: Database connectivity status
```

**Environment Variable Security:**
- Create `.env.example` template with all required variables (no secrets)
- Ensure `.env` files are in `.gitignore`
- Document required environment variables:
  - `DATABASE_URL` - PostgreSQL connection string
  - `REDIS_URL` - Redis connection string
  - `SECRET_KEY` - JWT secret key (use secure generation)
  - `ADMIN_SESSION_TIMEOUT` - Session expiration (default: 900 seconds)
  - `ALLOWED_IP_NETWORKS` - Comma-separated IP networks for whitelist
- Use secure secret management for CI/CD (GitHub Secrets, Vault)
- Never commit secrets to Git

**Environment File Template (`.env.example`):**
```bash
# Database
DATABASE_URL=postgresql://nina:password@localhost:5432/ninaivalaigal_dev

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ADMIN_SESSION_TIMEOUT=900

# Network Security
ALLOWED_IP_NETWORKS=10.0.0.0/8,192.168.0.0/16

# Environment
ENVIRONMENT=production
```

**Implementation:**

1. **Nginx Reverse Proxy Configuration:**
```nginx
# /etc/nginx/sites-available/admin
server {
    listen 443 ssl;
    server_name admin.ninaivalaigal.internal;

    # SSL Configuration (Internal CA)
    ssl_certificate /etc/ssl/certs/admin-internal.crt;
    ssl_certificate_key /etc/ssl/private/admin-internal.key;

    # IP Whitelist
    allow 10.0.0.0/8;        # Internal network
    allow 192.168.0.0/16;   # VPN range
    deny all;

    location /admin {
        proxy_pass http://127.0.0.1:13390;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/admin {
        proxy_pass http://127.0.0.1:13390;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **FastAPI Process Management (systemd):**
```ini
# /etc/systemd/system/ninaivalaigal-admin.service
[Unit]
Description=Ninaivalaigal Admin UI (FastAPI)
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=ninaivalaigal
WorkingDirectory=/opt/ninaivalaigal/services/core-api
Environment="PATH=/opt/ninaivalaigal/venv/bin"
ExecStart=/opt/ninaivalaigal/venv/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 13390 \
    --workers 4 \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **FastAPI Middleware for IP Whitelist (Additional Layer):**
```python
# Additional security layer in FastAPI
from fastapi import Request, HTTPException
from ipaddress import ip_address, ip_network

ALLOWED_NETWORKS = [
    ip_network("10.0.0.0/8"),
    ip_network("192.168.0.0/16"),
]

@app.middleware("http")
async def ip_whitelist_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        client_ip = request.client.host
        if not any(ip_address(client_ip) in net for net in ALLOWED_NETWORKS):
            raise HTTPException(status_code=403, detail="Access denied")
    return await call_next(request)
```

**Note:** With FastAPI templating, there's no separate frontend build process. Templates are served directly by FastAPI, making deployment simpler. However, security is enforced at multiple layers (VPN, nginx IP whitelist, FastAPI middleware).

## Success Metrics

### Functional Success
- [ ] Admin can create/manage users without database access
- [ ] Team management workflows complete in &lt;2 minutes
- [ ] Context ownership transfers work correctly
- [ ] All admin actions are properly logged

### Performance Success
- [ ] Admin UI loads in &lt;2 seconds
- [ ] User list with 1000+ users loads in &lt;1 second
- [ ] Search results appear in &lt;200ms
- [ ] Bulk operations complete in &lt;5 seconds

### User Experience Success
- [ ] Non-technical admins can use the system
- [ ] Clear error messages and recovery paths
- [ ] Responsive design works on tablets
- [ ] Intuitive navigation requires no training

This admin dashboard will transform mem0 from a developer-only tool into a production-ready system that non-technical stakeholders can manage effectively.

---

## Related Taiga User Stories

**Coverage: 38% → Target: 100%**

- **Story #110**: US-98 - Admin User Management API (P0)
- **Story #111**: US-99 - Admin UI Integration & Polish (P0)
- **Story #112**: US-100 - Admin Activity Logging System (P0)
- **Story #113**: US-101 - Context Admin Management API (P1)
- **Story #114**: US-102 - System Dashboard & Monitoring (P1)

**Analysis:** `/tasks/SPEC_005_COVERAGE_ANALYSIS.md`
**View in Taiga:** http://localhost:9000/project/ninaivalaigal

**Key Gaps Identified:**
- Admin user CRUD endpoints missing
- UI shell exists but disconnected from APIs
- No activity logging/audit trail
- Context admin functionality incomplete
- Dashboard shows mock data only
