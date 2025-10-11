# Customer UI Container - Apple Container CLI
**Customer-facing web interface (React/Vite)**

---

## Container Information

- **Name**: `ninaivalaigal-dev-ui-customer`
- **Image**: `nina-customer-ui:arm64`
- **Base**: `node:20-alpine`
- **Architecture**: ARM64
- **Port Mapping**: `8101:8101` (dev)
- **Purpose**: Customer-facing interface

---

## What's Inside

### Application
- **React** application built with Vite
- **Static files** served via http-server
- **Customer pages** only (SPEC-083 separation)
- **Dependencies**: React, React Router, Axios

### Key Directories
```
/app/
└── customer/        # Customer UI static files
    ├── index.html
    ├── assets/      # JS, CSS, images
    └── ...
```

---

## Prerequisites

### Source Files
```bash
# Frontend customer files must exist
/Users/swami/WorkSpace/ninaivalaigal/frontend/customer/
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
container build --no-cache -t nina-customer-ui:arm64 -f apps/customer/Dockerfile .

# Verify
container image list | grep nina-customer-ui
```

### Method 2: Docker Build + Transfer

```bash
# Build with Docker
docker build --no-cache -t nina-customer-ui:arm64 -f apps/customer/Dockerfile .

# Transfer
docker save nina-customer-ui:arm64 -o /tmp/nina-customer-ui.tar
container image load --input /tmp/nina-customer-ui.tar
```

---

## Dockerfile

**Location**: `/Users/swami/WorkSpace/ninaivalaigal/apps/customer/Dockerfile`

```dockerfile
# Customer App Dockerfile - Serves customer-facing pages only
FROM node:20-alpine

WORKDIR /app

# Copy ONLY customer-facing pages (SPEC-083 separation)
COPY ../../frontend/customer ./customer

# Install http-server for serving static files
RUN npm install -g http-server

# Expose port
EXPOSE 8101

# Serve the customer directory
CMD ["http-server", "./customer", "-p", "8101", "--cors"]
```

**Key Points**:
- Lightweight Node.js Alpine base
- http-server for static file serving
- CORS enabled for API calls
- SPEC-083 compliant (customer-only pages)

---

## Runtime Configuration

### Basic Start

```bash
container run -d --name ninaivalaigal-dev-ui-customer \
  -p 8101:8101 \
  nina-customer-ui:arm64
```

### With API Configuration

```bash
# No environment variables needed - API URL is in frontend code
container run -d --name ninaivalaigal-dev-ui-customer \
  -p 8101:8101 \
  nina-customer-ui:arm64
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| None | - | - | Static files, config in build |

**Note**: API URL is configured at build time in Vite config.

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-ui-customer
```

### Check Logs
```bash
container logs ninaivalaigal-dev-ui-customer

# Should see:
# Starting up http-server, serving ./customer
# http-server listening on http://0.0.0.0:8101
```

### Access UI
```bash
# Open in browser
open http://localhost:8101

# Or test with curl
curl -I http://localhost:8101
# Should return 200 OK with HTML
```

### Test Static Files
```bash
# Check for index.html
curl http://localhost:8101/index.html

# Check for assets
curl -I http://localhost:8101/assets/
```

---

## Get Container IP

```bash
CUSTOMER_IP=$(container inspect ninaivalaigal-dev-ui-customer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Customer UI IP: $CUSTOMER_IP"

# Access from other containers
curl http://${CUSTOMER_IP}:8101
```

---

## Frontend Configuration

### API Endpoint Configuration

```javascript
// In frontend code (vite.config.ts or .env)
VITE_API_URL=http://localhost:13390

// Or in production
VITE_API_URL=https://api.ninaivalaigal.com
```

### Build-Time Configuration

To rebuild with different API URL:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/frontend-nextjs/apps/customer

# Set API URL
echo "VITE_API_URL=http://localhost:13390" > .env.local

# Build
npm run build

# Copy build to frontend/customer
cp -r dist/* ../../frontend/customer/

# Rebuild container
cd ../..
container build --no-cache -t nina-customer-ui:arm64 -f apps/customer/Dockerfile .
```

---

## Development Workflow

### Local Development (without container)
```bash
cd /Users/swami/WorkSpace/ninaivalaigal/frontend-nextjs/apps/customer

# Install dependencies
npm install

# Run dev server
npm run dev
# Starts on http://localhost:5174
```

### Build for Production
```bash
# Build optimized bundle
npm run build

# Preview build
npm run preview

# Copy to frontend/customer
cp -r dist/* ../../frontend/customer/

# Build container
container build --no-cache -t nina-customer-ui:arm64 -f apps/customer/Dockerfile .
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
container logs ninaivalaigal-dev-ui-customer

# Common issues:
# 1. Port conflict
lsof -i :8101

# 2. Missing files
container run --rm nina-customer-ui:arm64 ls -la /app/customer/
```

### 404 Not Found

```bash
# Check if index.html exists
container exec ninaivalaigal-dev-ui-customer ls -la /app/customer/

# Should show index.html and assets/
```

### Cannot Connect to API

```bash
# Check browser console for errors
# Verify API is running
curl http://localhost:13390/health

# Verify API URL in frontend code
container exec ninaivalaigal-dev-ui-customer cat /app/customer/index.html | grep -i api

# Test API CORS
curl -H "Origin: http://localhost:8101" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  http://localhost:13390/api/auth/login
```

### Static Assets Not Loading

```bash
# Check asset paths
container exec ninaivalaigal-dev-ui-customer find /app/customer/assets/

# Test asset loading
curl -I http://localhost:8101/assets/index-[hash].js

# Check http-server logs
container logs -f ninaivalaigal-dev-ui-customer
```

---

## Integration

### With API

The customer UI makes API calls to:
- `POST /api/auth/login` - User authentication
- `POST /api/auth/signup` - User registration
- `GET /api/user/profile` - User profile
- `GET /api/memories` - User memories
- `POST /api/context` - Context management
- `GET /api/search` - Search functionality

Ensure API CORS allows `http://localhost:8101`:

```python
# In API (server/main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8101", "http://localhost:8102"],
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
container logs -f ninaivalaigal-dev-ui-customer

# Shows:
# [2025-10-10 19:00:00] GET /index.html 200
# [2025-10-10 19:00:01] GET /assets/index.js 200
```

### Container Stats
```bash
container stats ninaivalaigal-dev-ui-customer
```

---

## Performance

### Production Optimization

For production, consider using nginx:

```dockerfile
FROM nginx:alpine
COPY frontend/customer /usr/share/nginx/html
COPY nginx-customer.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Caching Headers

```nginx
location /assets/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

location / {
  try_files $uri $uri/ /index.html;
  expires -1;
  add_header Cache-Control "no-cache";
}
```

---

## Security

### Non-Root User
Container runs as node user (Alpine default).

### CORS
CORS is enabled for development. Restrict in production:

```nginx
add_header Access-Control-Allow-Origin "https://api.yourdomain.com";
```

### Content Security Policy
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;";
```

### HTTPS
In production, always use HTTPS:

```nginx
server {
  listen 443 ssl http2;
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;

  # Modern SSL config
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
}
```

---

## Clean Up

```bash
container stop ninaivalaigal-dev-ui-customer
container delete ninaivalaigal-dev-ui-customer
container image rm nina-customer-ui:arm64
```

---

## Quick Reference

```bash
# Build
container build --no-cache -t nina-customer-ui:arm64 -f apps/customer/Dockerfile .

# Start
container run -d --name ninaivalaigal-dev-ui-customer \
  -p 8101:8101 \
  nina-customer-ui:arm64

# Verify
curl -I http://localhost:8101
open http://localhost:8101

# Logs
container logs -f ninaivalaigal-dev-ui-customer

# Get IP
CUSTOMER_IP=$(container inspect ninaivalaigal-dev-ui-customer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

---

## Features

- **Sign Up / Login** - User authentication
- **Dashboard** - Personal memory dashboard
- **Memory Management** - Create, view, search memories
- **Context Tracking** - Active context management
- **Graph Visualization** - Memory connections
- **Search** - Intelligent memory search
- **Profile** - User profile and settings

**Access**: http://localhost:8101
