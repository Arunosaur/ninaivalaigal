# Frontend Deployment Guide

**Version:** 2.0 (FastAPI Templating)
**Last Updated:** January 2025
**Status:** Production
**References:** SPEC-005 (Admin Dashboard), SPEC-146 (Customer UI), SPEC-016 (CI/CD)

---

## Overview

This guide covers deployment of the FastAPI-based frontend (customer and admin UIs) using Jinja2 templates. The deployment process is integrated into the main FastAPI application, so there's no separate frontend build step.

---

## Architecture

### Deployment Model

```
┌─────────────────────────────────────┐
│     FastAPI Application              │
│  ┌─────────────┐  ┌──────────────┐ │
│  │ Customer UI  │  │  Admin UI    │ │
│  │ (Jinja2)     │  │  (Jinja2)    │ │
│  └─────────────┘  └──────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │     API Endpoints              │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   PostgreSQL + Redis + Prometheus   │
└─────────────────────────────────────┘
```

**Key Points:**
- Single FastAPI service handles both customer and admin UIs
- No separate frontend build process
- Templates served directly by FastAPI
- Static assets (CSS, JS) served via FastAPI static files

---

## Prerequisites

### Required Services

- **FastAPI Application**: Core API service (port 13370)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache and session storage (port 6379)
- **Prometheus**: Metrics (port 9090) - Optional
- **Grafana**: Dashboards (port 3001) - Optional

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ninaivalaigal

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256

# Application
API_URL=http://localhost:13370
ENVIRONMENT=production
```

---

## Deployment Steps

### 1. Customer UI Deployment

#### Local Development

```bash
# Start services
make stack-up

# Access customer UI
open http://localhost:13370/customer/dashboard
```

#### Production Deployment

```bash
# Build Docker image
docker build -t ninaivalaigal-api:latest .

# Run container
docker run -d \
  -p 13370:13370 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e JWT_SECRET_KEY=... \
  --name ninaivalaigal-api \
  ninaivalaigal-api:latest
```

#### Customer UI Routes

- `/customer/login` - Login page
- `/customer/signup` - Registration page
- `/customer/dashboard` - Customer dashboard
- `/customer/memories` - Memory browser
- `/customer/memories/new` - Create memory
- `/customer/teams` - Team management
- `/customer/profile` - Profile settings

---

### 2. Admin UI Deployment

#### Local Development

```bash
# Start services
make stack-up

# Access admin UI (requires VPN/internal network)
open http://localhost:13370/admin/dashboard
```

#### Production Deployment (Internal)

Admin UI is served on the same FastAPI instance but requires:
- **VPN Access**: Internal network only
- **Role-Based Access**: Admin/staff roles only
- **IP Whitelist**: Optional additional security

#### Admin UI Routes

- `/admin/login` - Admin login
- `/admin/dashboard` - Admin dashboard
- `/admin/users` - User management
- `/admin/teams` - Team management
- `/admin/contexts` - Context management
- `/admin/analytics` - Analytics dashboard

---

### 3. CI/CD Integration

### GitHub Actions Workflow

See **SPEC-016** for complete CI/CD architecture. The frontend deployment is integrated into the main API deployment workflow.

**Key Workflow Steps:**

```yaml
# .github/workflows/api-deploy.yml
name: Deploy API (with Frontend)

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t ninaivalaigal-api:${{ github.sha }} .

      - name: Deploy to production
        run: |
          # Deployment steps
          # (See SPEC-016 for details)
```

**No Frontend Build Step Required:**
- Templates are included in the Docker image
- Static assets are served directly by FastAPI
- No webpack/vite/build process needed

---

## Environment Configuration

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
API_URL=http://localhost:13370
DATABASE_URL=postgresql://localhost:5432/ninaivalaigal
REDIS_URL=redis://localhost:6379
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
API_URL=https://api.ninaivalaigal.com
DATABASE_URL=postgresql://prod-db:5432/ninaivalaigal
REDIS_URL=redis://prod-redis:6379
JWT_SECRET_KEY=<production-secret>
```

---

## Static Assets

### Static Files Configuration

```python
# In FastAPI app setup
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Static Assets Structure

```
static/
├── css/
│   └── output.css          # TailwindCSS compiled
├── js/
│   └── alpine.js          # Alpine.js (if not using CDN)
└── images/
    └── logo.png
```

### CDN vs Local Assets

**Option 1: CDN (Development)**
```html
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

**Option 2: Local Assets (Production)**
```html
<link rel="stylesheet" href="/static/css/output.css">
<script src="/static/js/alpine.js" defer></script>
```

---

## Security Configuration

### Customer UI Security

- **HTTPS**: Required in production
- **JWT Tokens**: Stored in httpOnly cookies
- **CORS**: Configured for customer domain
- **Rate Limiting**: Applied to all endpoints

### Admin UI Security

- **VPN Access**: Required for internal access
- **Role-Based Access**: Admin/staff roles only
- **IP Whitelist**: Optional additional security
- **Session Timeout**: 8-hour session timeout

---

## Monitoring & Observability

### Grafana Dashboards

See **SPEC-118** for monitoring setup. Frontend metrics are included in:

- **API Performance Dashboard**: Request rates, latency
- **Service Health Dashboard**: Uptime, errors
- **Business Metrics Dashboard**: User activity, memory operations

### Frontend-Specific Metrics

- **Page Load Time**: Tracked via Prometheus
- **Error Rate**: 4xx/5xx errors tracked
- **User Activity**: Memory operations, team creation

---

## Troubleshooting

### Common Issues

#### 1. Templates Not Found

**Error**: `TemplateNotFound: customer/dashboard.html`

**Solution**:
```bash
# Check template directory
ls -la services/core-api/lib/customer/templates/

# Verify template path in router
templates = Jinja2Templates(directory="templates/customer")
```

#### 2. Static Files Not Loading

**Error**: `404 Not Found` for `/static/css/output.css`

**Solution**:
```python
# Verify static files mount
app.mount("/static", StaticFiles(directory="static"), name="static")

# Check file permissions
chmod -R 755 static/
```

#### 3. Authentication Not Working

**Error**: Users redirected to login even after authentication

**Solution**:
- Check JWT token in cookies
- Verify Redis session storage
- Check middleware authentication logic

---

## Rollback Procedure

### Rollback Steps

1. **Stop current deployment**
   ```bash
   docker stop ninaivalaigal-api
   ```

2. **Start previous version**
   ```bash
   docker run -d \
     --name ninaivalaigal-api \
     ninaivalaigal-api:previous-version
   ```

3. **Verify deployment**
   ```bash
   curl http://localhost:13370/health
   ```

---

## Performance Optimization

### Template Caching

Jinja2 templates are automatically cached in production:

```python
# FastAPI automatically caches compiled templates
templates = Jinja2Templates(
    directory="templates",
    auto_reload=False  # Disable in production
)
```

### Database Query Optimization

- Use eager loading to minimize queries
- Cache frequently accessed data in Redis
- Use database indexes for common queries

### Static Asset Optimization

- Minify CSS/JS files
- Enable gzip compression
- Use CDN for static assets (if applicable)

---

## References

- **SPEC-005**: Admin Dashboard (FastAPI templating)
- **SPEC-146**: Customer UI (FastAPI templating)
- **SPEC-016**: CI/CD Pipeline Architecture
- **SPEC-114**: Auth & Security Integration
- **SPEC-118**: Observability & Performance Budgets

---

**Status**: ✅ **Production-Ready**
**Last Updated**: January 2025
**Next Review**: After deployment validation
