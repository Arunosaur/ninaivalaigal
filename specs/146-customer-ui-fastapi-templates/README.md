# SPEC-146: Customer UI with FastAPI Templates

**Status:** ✅ Active
**Priority:** High
**Category:** Frontend - Customer UI
**Related:** SPEC-005 (Admin Dashboard), SPEC-083 (Product Surface Split), SPEC-114 (Auth & Security)

---

## Overview

Build a customer-facing web interface using **FastAPI + Jinja2 templates** for end-users (individuals, teams, organizations). This provides a public-facing UI that customers use to manage their memories, teams, and billing.

**Implementation Approach:** FastAPI serves Jinja2 templates with Alpine.js for interactivity. No separate frontend build process required.

---

## Problem Statement

Currently, the system has:
- ✅ Customer-facing API endpoints (FastAPI)
- ✅ JWT authentication with customer role support
- ✅ Database schema for customers, teams, organizations
- ❌ No public-facing UI for customers
- ❌ Customers must use API directly or third-party tools

---

## Requirements

### Functional Requirements

#### Authentication & User Management
- **Signup/Login**: Customer registration and login flow
- **Session Management**: JWT-based session with Redis persistence
- **Password Reset**: Secure password reset flow
- **Profile Management**: Customer profile editing

#### Memory Management
- **Memory Browser**: View and search memories
- **Memory Creation**: Create new memories via UI
- **Memory Editing**: Edit existing memories
- **Memory Deletion**: Delete memories with confirmation

#### Team & Organization Management
- **Team Creation**: Create teams via UI
- **Team Management**: Manage team members and permissions
- **Organization Management**: Create and manage organizations
- **Billing**: View and manage billing information (if applicable)

#### Dashboard & Analytics
- **Customer Dashboard**: Overview of user's memories, teams, activity
- **Usage Analytics**: View memory usage, team activity
- **Activity Feed**: Recent activity and updates

### Non-Functional Requirements

#### Performance
- **Lighthouse Performance Score**: >90 (target)
- **Lighthouse Accessibility Score**: 100 (required)
- **First Contentful Paint (FCP)**: <1.5s
- **Time to Interactive (TTI)**: <3.0s
- **Largest Contentful Paint (LCP)**: <2.5s
- **Cumulative Layout Shift (CLS)**: <0.1

#### Security
- **JWT RS256 Authentication**: Secure token-based auth
- **Session Persistence**: Redis-backed session storage
- **Role-Based Access**: Customer role enforcement
- **HTTPS Required**: All traffic over HTTPS
- **Security Headers**: CSP, X-Frame-Options, etc.

#### Monitoring & Analytics
- **Error Tracking**: Track and report UI errors
- **Real User Monitoring (RUM)**: Monitor real user performance
- **Analytics**: Track user behavior (privacy-compliant)
- **Performance Monitoring**: Track Core Web Vitals

#### Accessibility
- **WCAG AA Compliance**: Meet accessibility standards
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: ARIA labels and semantic HTML
- **Color Contrast**: WCAG AA contrast ratios

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Customer Router (/customer/* or /app/*)             │  │
│  │  ├── Jinja2 Templates (templates/customer/*.html)   │  │
│  │  ├── Alpine.js (client-side interactivity)            │  │
│  │  └── TailwindCSS (styling)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Customer Endpoints (/api/v1/*)              │  │
│  │  ├── Authentication (/auth/login, /auth/signup)       │  │
│  │  ├── Memory Management                                │  │
│  │  ├── Team Management                                  │  │
│  │  └── Dashboard Data                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database + Redis Sessions + JWT Auth           │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- ✅ **No separate frontend build** - Templates served directly by FastAPI
- ✅ **Single deployment** - FastAPI handles both UI and API
- ✅ **Simpler architecture** - No CORS, no separate static hosting
- ✅ **Public CDN or FastAPI serving** - Flexible deployment options

---

### Backend Implementation

#### FastAPI Endpoints (Already Exists)
```python
# Authentication
POST   /auth/login              # Customer login
POST   /auth/signup              # Customer registration
POST   /auth/refresh             # Refresh JWT token
POST   /auth/logout              # Logout (clear session)

# Memory Management
GET    /api/v1/memories          # List memories
POST   /api/v1/memories          # Create memory
GET    /api/v1/memories/{id}     # Get memory
PUT    /api/v1/memories/{id}    # Update memory
DELETE /api/v1/memories/{id}    # Delete memory

# Team Management
GET    /api/v1/teams             # List teams
POST   /api/v1/teams              # Create team
GET    /api/v1/teams/{id}         # Get team
PUT    /api/v1/teams/{id}         # Update team

# Dashboard
GET    /api/v1/dashboard         # Dashboard data
```

#### Customer UI Routes (New)
```python
# Customer UI Pages
GET    /customer/dashboard        # Customer dashboard (Jinja2 template)
GET    /customer/memories         # Memory browser (Jinja2 template)
GET    /customer/memories/new     # Create memory form (Jinja2 template)
GET    /customer/memories/{id}    # View memory (Jinja2 template)
GET    /customer/teams            # Team management (Jinja2 template)
GET    /customer/profile          # Profile settings (Jinja2 template)
GET    /customer/login            # Login page (Jinja2 template)
GET    /customer/signup           # Signup page (Jinja2 template)
```

---

### Frontend Implementation

#### Technology Stack
- **Backend Framework**: FastAPI (Python)
- **Template Engine**: Jinja2 (built into FastAPI)
- **Styling**: TailwindCSS (via CDN or build process)
- **Interactivity**: Alpine.js (lightweight, ~3KB)
- **Charts**: Chart.js (via CDN) for analytics visualization
- **Forms**: Server-side form handling with FastAPI

#### Template Structure
```
templates/customer/
├── base.html              # Base layout with navigation
├── dashboard.html         # Customer dashboard
├── login.html             # Login page
├── signup.html            # Signup page
├── memories.html          # Memory browser/list
├── memory_form.html       # Create/edit memory form
├── memory_detail.html     # Memory detail view
├── teams.html             # Team management
├── profile.html           # Profile settings
└── components/            # Reusable Jinja2 macros and partials
    ├── macros.html        # Common macros (buttons, forms, cards)
    ├── memory_card.html   # Memory card component
    ├── team_card.html     # Team card component
    └── pagination.html    # Pagination macro
```

#### Implementation Pattern
```python
# FastAPI Router Example
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/customer", tags=["customer"])
templates = Jinja2Templates(directory="templates/customer")

@router.get("/dashboard", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer)
):
    # Fetch dashboard data
    memories = get_user_memories(current_user.id, db)
    teams = get_user_teams(current_user.id, db)

    return templates.TemplateResponse(
        "customer/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "memories": memories,
            "teams": teams
        }
    )
```

---

## Authentication Integration

### JWT RS256 Authentication
- **Token Generation**: Backend generates JWT tokens with RS256 algorithm
- **Token Validation**: FastAPI middleware validates JWT on protected routes
- **Session Storage**: Redis stores session metadata
- **Token Refresh**: Automatic token refresh before expiration

### Session Management
- **Session Expiration**: 24-hour session (longer than admin 15-minute sessions)
- **Redis Backend**: Session data stored in Redis
- **Logout**: Clear session from Redis on logout

### Role Enforcement
- **Customer-Only Routes**: Middleware ensures only `customer` role can access
- **Redirect to Login**: Unauthenticated users redirected to `/customer/login`
- **Protected Routes**: All `/customer/*` routes require authentication

---

## Performance Requirements

### Core Web Vitals Targets
- **LCP (Largest Contentful Paint)**: <2.5s
- **FID (First Input Delay)**: <100ms
- **CLS (Cumulative Layout Shift)**: <0.1

### Lighthouse Scores
- **Performance**: >90
- **Accessibility**: 100 (required)
- **Best Practices**: >90
- **SEO**: >90

### Optimization Strategies
- **Template Caching**: Enable Jinja2 template caching
- **Static Asset CDN**: Serve CSS/JS from CDN
- **Image Optimization**: Compress and optimize images
- **Lazy Loading**: Lazy load non-critical content
- **Database Query Optimization**: Efficient queries with proper indexing

---

## Monitoring & Analytics

### Error Tracking
- **Error Logging**: Log all UI errors to backend
- **Error Reporting**: User-friendly error messages
- **Error Analytics**: Track error rates and types

### Real User Monitoring (RUM)
- **Performance Metrics**: Track Core Web Vitals
- **User Journey**: Track user navigation patterns
- **Performance Budgets**: Alert on performance degradation

### Analytics
- **Privacy-Compliant**: GDPR/privacy-compliant analytics
- **User Behavior**: Track key user actions (opt-in)
- **Performance Monitoring**: Track page load times

---

## Deployment

### Development Environment
```bash
# Start FastAPI with customer UI endpoints
cd services/core-api
python -m uvicorn main:app --reload --port 13390

# Customer UI accessible at: http://localhost:13390/customer
```

### Production Deployment Options

#### Option 1: FastAPI Serves Templates Directly
```bash
# FastAPI serves templates directly - no separate build step
# Customer UI is served from FastAPI routes:
# - /customer/dashboard → templates/customer/dashboard.html
# - /customer/memories → templates/customer/memories.html

# Configure nginx (reverse proxy)
location /customer {
    proxy_pass http://localhost:13390;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

#### Option 2: Public CDN (Static Assets)
```bash
# If using CDN for static assets:
# - Templates served by FastAPI
# - CSS/JS/images served from CDN (Cloudflare, AWS CloudFront)
```

**Domain:** `app.ninaivalaigal.com` (public-facing)

**SSL:** Let's Encrypt automatic SSL certificates

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

# 4. Verify customer API endpoints
curl http://localhost:13390/api/v1/memories
# Expected: 401 (unauthorized) or 200 (if authenticated) - confirms connectivity
```

**Environment Variable Security:**
- Create `.env.example` template with all required variables (no secrets)
- Ensure `.env` files are in `.gitignore`
- Document required environment variables:
  - `DATABASE_URL` - PostgreSQL connection string
  - `REDIS_URL` - Redis connection string
  - `SECRET_KEY` - JWT secret key (use secure generation)
  - `CUSTOMER_SESSION_TIMEOUT` - Session expiration (default: 86400 seconds / 24 hours)
  - `API_URL` - FastAPI base URL (for internal calls)
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
CUSTOMER_SESSION_TIMEOUT=86400

# API Configuration
API_URL=http://localhost:13390

# Environment
ENVIRONMENT=production
```

---

## Implementation Plan

### Phase 1: Authentication & Base Templates (Week 1)
- [ ] Create FastAPI customer router
- [ ] Build login/signup templates (Jinja2)
- [ ] Implement JWT authentication integration
- [ ] Create base customer template (TailwindCSS)
- [ ] Set up session management (Redis)

### Phase 2: Memory Management UI (Week 2)
- [ ] Build memory browser template
- [ ] Create memory form template (create/edit)
- [ ] Implement memory detail view
- [ ] Add search and filtering (Alpine.js)
- [ ] Connect to existing memory API endpoints

### Phase 3: Dashboard & Teams (Week 3)
- [ ] Build customer dashboard template
- [ ] Create team management templates
- [ ] Add usage analytics (Chart.js)
- [ ] Implement activity feed
- [ ] Add profile management

### Phase 4: Performance & Polish (Week 4)
- [ ] Optimize templates for performance
- [ ] Add accessibility features (ARIA, keyboard nav)
- [ ] Implement error handling
- [ ] Set up monitoring and analytics
- [ ] Lighthouse optimization and testing

---

## Success Metrics

### Functional Success
- [ ] Customers can create/manage memories via UI
- [ ] Authentication flow works correctly
- [ ] Team management workflows complete
- [ ] All customer actions are properly logged

### Performance Success
- [ ] Lighthouse Performance score >90
- [ ] Lighthouse Accessibility score =100
- [ ] FCP <1.5s, TTI <3.0s
- [ ] All Core Web Vitals meet targets

### User Experience Success
- [ ] Intuitive navigation requires no training
- [ ] Clear error messages and recovery paths
- [ ] Responsive design works on mobile/tablet
- [ ] Accessibility tested and verified

---

## Security Considerations

### Authentication
- **JWT RS256**: Secure token-based authentication
- **Session Management**: Redis-backed session storage
- **Password Security**: Strong password requirements
- **HTTPS Required**: All traffic over HTTPS

### Authorization
- **Role-Based Access**: Customer role enforcement
- **Resource Ownership**: Users can only access their own data
- **API Rate Limiting**: Prevent abuse

### Security Headers
- **CSP (Content Security Policy)**: Prevent XSS attacks
- **X-Frame-Options**: Prevent clickjacking
- **X-Content-Type-Options**: Prevent MIME sniffing
- **Strict-Transport-Security**: Force HTTPS

---

## Testing Strategy

### Unit Tests
- Template rendering logic
- Authentication middleware
- API endpoint functionality

### Integration Tests
- End-to-end customer workflows
- Authentication and authorization
- Database transaction integrity

### Smoke Tests (Backend Connectivity)
- Backend health endpoint reachability (`/health`)
- PostgreSQL connection verification via API
- Redis cache operations via API
- Authentication flow end-to-end
- Customer API endpoint connectivity

**Example Smoke Test:**
```python
# tests/integration/test_customer_connectivity.py
def test_backend_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_database_connectivity():
    # Test customer data access
    response = client.get("/api/v1/memories")
    assert response.status_code in [200, 401]  # 401 if no auth, but connection works

def test_redis_session_storage():
    # Test Redis session operations
    response = client.post("/auth/login", json={"email": "test@example.com", "password": "test"})
    assert response.status_code in [200, 401]
```

### Performance Tests
- Lighthouse CI enforcement
- Core Web Vitals testing
- Load testing

### Accessibility Tests
- WCAG AA compliance testing
- Keyboard navigation testing
- Screen reader testing

---

## Related SPECs

- **SPEC-005**: Admin Dashboard (internal UI)
- **SPEC-083**: Product Surface Split & Naming
- **SPEC-114**: Auth & Security (JWT RS256, session management)
- **SPEC-003**: Core API Architecture (API endpoints)

---

## Related Taiga User Stories

**To be created/updated:**
- Customer UI Authentication Integration
- Customer Memory Management UI
- Customer Dashboard Implementation
- Customer UI Performance Optimization
- Customer UI Monitoring & Analytics

---

**Status:** Ready for Implementation
**Last Updated:** 2025-11-02
