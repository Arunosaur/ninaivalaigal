# Admin Console UI Container - Apple Container CLI
**Internal/staff admin interface (React/Vite)**

---

## Container Information

- **Name**: `ninaivalaigal-dev-ui-admin`
- **Image**: `nina-admin-console:arm64`
- **Base**: `node:20-alpine`
- **Architecture**: ARM64
- **Port Mapping**: `8102:8102` (dev)
- **Purpose**: Internal admin interface

---

## What's Inside

### Application
- **React** application built with Vite
- **Static files** served via http-server
- **Admin pages** only (SPEC-083 separation)
- **Dependencies**: React, React Router, Axios, Recharts

### Key Directories
```
/app/
└── admin/           # Admin console static files
    ├── index.html
    ├── assets/      # JS, CSS, images
    └── ...
```

---

## Prerequisites

### Source Files
```bash
# Frontend admin files must exist
/Users/swami/WorkSpace/ninaivalaigal/frontend/admin/
```

### Tools Required
```bash
brew install jq curl
```

### API Dependency
- API must be running for full functionality
- Can start UI independently for development

---

## Build Process

### Method 1: Apple Container CLI

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build (~30 seconds)
container build --no-cache -t nina-admin-console:arm64 -f apps/admin-console/Dockerfile .

# Verify
container image list | grep nina-admin-console
```

### Method 2: Docker Build + Transfer

```bash
# Build with Docker
docker build --no-cache -t nina-admin-console:arm64 -f apps/admin-console/Dockerfile .

# Transfer
docker save nina-admin-console:arm64 -o /tmp/nina-admin-console.tar
container image load --input /tmp/nina-admin-console.tar
```

---

## Dockerfile

**Location**: `/Users/swami/WorkSpace/ninaivalaigal/apps/admin-console/Dockerfile`

```dockerfile
# Admin Console Dockerfile - Serves internal/staff pages only
FROM node:20-alpine

WORKDIR /app

# Copy ONLY admin/internal pages (SPEC-083 separation)
COPY ../../frontend/admin ./admin

# Install http-server for serving static files
RUN npm install -g http-server

# Expose port
EXPOSE 8102

# Serve the admin directory
CMD ["http-server", "./admin", "-p", "8102", "--cors"]
```

**Key Points**:
- Lightweight Node.js Alpine base
- http-server for static file serving
- CORS enabled for API calls
- SPEC-083 compliant (admin-only pages)

---

## Runtime Configuration

### Basic Start

```bash
container run -d --name ninaivalaigal-dev-ui-admin \
  -p 8102:8102 \
  nina-admin-console:arm64
```

### With API Configuration

```bash
# No environment variables needed - API URL is in frontend code
# Or use environment variable if supported by your build

container run -d --name ninaivalaigal-dev-ui-admin \
  -p 8102:8102 \
  nina-admin-console:arm64
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| None | - | - | Static files, config in build |

**Note**: API URL is typically configured at build time in Vite config or environment variables during frontend build.

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-ui-admin
```

### Check Logs
```bash
container logs ninaivalaigal-dev-ui-admin

# Should see:
# Starting up http-server, serving ./admin
# http-server listening on http://0.0.0.0:8102
```

### Access UI
```bash
# Open in browser
open http://localhost:8102

# Or test with curl
curl -I http://localhost:8102
# Should return 200 OK with HTML
```

### Test Static Files
```bash
# Check for index.html
curl http://localhost:8102/index.html

# Check for assets
curl -I http://localhost:8102/assets/
```

---

## Get Container IP

```bash
ADMIN_IP=$(container inspect ninaivalaigal-dev-ui-admin | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Admin Console IP: $ADMIN_IP"

# Access from other containers
curl http://${ADMIN_IP}:8102
```

---

## Frontend Configuration

### API Endpoint Configuration

The admin console needs to know the API URL. This is typically set during build:

```javascript
// In frontend code (vite.config.ts or .env)
VITE_API_URL=http://localhost:13390

// Or in production
VITE_API_URL=https://api.ninaivalaigal.com
```

### Build-Time Configuration

If you need to rebuild with different API URL:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/frontend-nextjs/apps/admin-console

# Set API URL
echo "VITE_API_URL=http://localhost:13390" > .env.local

# Build
npm run build

# Copy build to frontend/admin
cp -r dist/* ../../frontend/admin/

# Rebuild container
cd ../..
container build --no-cache -t nina-admin-console:arm64 -f apps/admin-console/Dockerfile .
```

---

## Development Workflow

### Local Development (without container)
```bash
cd /Users/swami/WorkSpace/ninaivalaigal/frontend-nextjs/apps/admin-console

# Install dependencies
npm install

# Run dev server
npm run dev
# Starts on http://localhost:5173
```

### Build for Production
```bash
# Build optimized bundle
npm run build

# Preview build
npm run preview

# Copy to frontend/admin
cp -r dist/* ../../frontend/admin/

# Build container
container build --no-cache -t nina-admin-console:arm64 -f apps/admin-console/Dockerfile .
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
container logs ninaivalaigal-dev-ui-admin

# Common issues:
# 1. Port conflict
lsof -i :8102

# 2. Missing files
container run --rm nina-admin-console:arm64 ls -la /app/admin/
```

### 404 Not Found

```bash
# Check if index.html exists
container exec ninaivalaigal-dev-ui-admin ls -la /app/admin/

# Should show index.html and assets/
```

### Cannot Connect to API

```bash
# Check browser console for CORS errors
# Check API is running
curl http://localhost:13390/health

# Verify API URL in frontend code
container exec ninaivalaigal-dev-ui-admin cat /app/admin/index.html | grep -i api

# Check CORS is enabled on API
curl -H "Origin: http://localhost:8102" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  http://localhost:13390/api/auth/login
```

### Static Assets Not Loading

```bash
# Check asset paths
container exec ninaivalaigal-dev-ui-admin find /app/admin/assets/

# Test asset loading
curl -I http://localhost:8102/assets/index-[hash].js

# Check http-server logs
container logs -f ninaivalaigal-dev-ui-admin
```

---

## Integration

### With API

The admin console makes API calls to:
- `GET /api/admin/*` - Admin endpoints
- `POST /api/auth/login` - Authentication
- `GET /api/users` - User management
- `GET /api/teams` - Team management
- `GET /api/metrics` - Dashboard metrics

Ensure API CORS allows `http://localhost:8102`:

```python
# In API (server/main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8102", "http://localhost:8101"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Monitoring

### Access Logs
```bash
# View access logs
container logs -f ninaivalaigal-dev-ui-admin

# Shows:
# [2025-10-10 19:00:00] GET /index.html 200
# [2025-10-10 19:00:01] GET /assets/index.js 200
```

### Container Stats
```bash
container stats ninaivalaigal-dev-ui-admin
```

---

## Performance

### Production Optimization

For production builds:

```bash
# Enable gzip compression
container run -d --name ninaivalaigal-prod-ui-admin \
  -p 8102:8102 \
  nina-admin-console:arm64

# Or use nginx for better performance (alternative Dockerfile)
FROM nginx:alpine
COPY frontend/admin /usr/share/nginx/html
EXPOSE 80
```

### Caching

http-server has basic caching. For better caching, use nginx:

```nginx
location /assets/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

location / {
  expires -1;
  add_header Cache-Control "no-cache";
}
```

---

## Security

### Non-Root User
The container runs as node user (Alpine default).

### CORS
CORS is enabled (`--cors` flag), which is needed for API calls but should be restricted in production.

### Content Security Policy
Add CSP headers in production:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';";
```

---

## Clean Up

```bash
container stop ninaivalaigal-dev-ui-admin
container delete ninaivalaigal-dev-ui-admin
container image rm nina-admin-console:arm64
```

---

## Quick Reference

```bash
# Build
container build --no-cache -t nina-admin-console:arm64 -f apps/admin-console/Dockerfile .

# Start
container run -d --name ninaivalaigal-dev-ui-admin \
  -p 8102:8102 \
  nina-admin-console:arm64

# Verify
curl -I http://localhost:8102
open http://localhost:8102

# Logs
container logs -f ninaivalaigal-dev-ui-admin

# Get IP
ADMIN_IP=$(container inspect ninaivalaigal-dev-ui-admin | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

---

## Features

- **Dashboard** - System metrics and health
- **User Management** - Create, edit, deactivate users
- **Team Management** - Team creation and membership
- **Content Moderation** - Review flagged content
- **Analytics** - Usage statistics and reports
- **Settings** - System configuration

**Access**: http://localhost:8102
