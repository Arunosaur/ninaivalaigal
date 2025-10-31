# Nina Intelligence Stack - Container Architecture

## Current Status (October 7, 2025)

### ✅ Running Containers

| Container | Image | Port Mapping | Status | Purpose |
|-----------|-------|--------------|--------|---------|
| ninaivalaigal-dev-db | nina-intelligence-db:arm64 | 5452→5432 | ✅ Running | PostgreSQL 15 with pgvector |
| ninaivalaigal-dev-pgbouncer | nina-pgbouncer:arm64 | 6442→6432 | ✅ Running | Connection pooler (SCRAM-SHA-256) |
| ninaivalaigal-dev-redis | redis:7-alpine | 6399→6379 | ✅ Running | Cache & rate limiting |
| ninaivalaigal-dev-api | nina-api:arm64 | 13390→8000 | ✅ Running | FastAPI backend with SPEC-055 lifespan |

**API Health**: http://localhost:13390/health → `{"status":"ok"}`
**API Docs**: http://localhost:13390/docs (Swagger UI) ✅

---

### 🔄 Containers To Deploy

| Container | Dockerfile | Port | Purpose | Priority |
|-----------|------------|------|---------|----------|
| **ninaivalaigal-dev-ui-customer** | `apps/customer/Dockerfile` | 8100 | External customer-facing UI | 🔴 High |
| **ninaivalaigal-dev-ui-admin** | `apps/admin-console/Dockerfile` | 8101 | Internal admin console | 🔴 High |
| **ninaivalaigal-dev-em** | `Dockerfile.em` | 7070 | Enhanced Memory (mem0ai) sidecar | 🟡 Medium |

---

## Container Dependencies

```
┌─────────────────────────────────────────────────────┐
│                    CLIENT LAYER                      │
│  ┌──────────────────┐      ┌───────────────────┐   │
│  │  Customer UI     │      │   Admin Console   │   │
│  │  (Port 8100)     │      │   (Port 8101)     │   │
│  └────────┬─────────┘      └─────────┬─────────┘   │
└───────────┼────────────────────────────┼─────────────┘
            │                            │
            └──────────────┬─────────────┘
                           │
┌──────────────────────────┴──────────────────────────┐
│                    API LAYER                         │
│  ┌─────────────────────────────────────────────┐   │
│  │           FastAPI Backend                    │   │
│  │           (Port 13390)                       │   │
│  │  • Health: /health                           │   │
│  │  • Docs: /docs (Swagger)                     │   │
│  │  • SPEC-055 Lifespan ✅                      │   │
│  └──────┬──────────────────┬───────────────────┘   │
└─────────┼──────────────────┼───────────────────────┘
          │                  │
          │                  └────────────┐
          │                               │
┌─────────┴─────────────────┬─────────────┴───────────┐
│      DATA/CACHE LAYER     │     OPTIONAL SERVICES   │
│  ┌──────────────────┐    ┌┴────────────────────┐   │
│  │   PgBouncer      │    │  Enhanced Memory    │   │
│  │   (Port 6442)    │    │  (Port 7070)        │   │
│  └────────┬─────────┘    └─────────────────────┘   │
│           │                                          │
│  ┌────────┴─────────┐    ┌─────────────────────┐   │
│  │   PostgreSQL     │    │      Redis          │   │
│  │   (Port 5452)    │    │    (Port 6399)      │   │
│  │   + pgvector     │    │                     │   │
│  └──────────────────┘    └─────────────────────┘   │
└───────────────────────────────────────────────────  ┘
```

---

## Container Details

### 1. Customer UI (External)

**Path**: `apps/customer/`
**Dockerfile**: `apps/customer/Dockerfile`
**Port**: 8100
**Technology**: React/Next.js (needs verification)

**Purpose**: Customer-facing interface for memory management

**Build Command**:
```bash
docker build --no-cache --platform linux/arm64 \
  -t nina-customer-ui:arm64 \
  -f apps/customer/Dockerfile \
  apps/customer/
```

**Environment Variables** (expected):
- `API_URL` or `NEXT_PUBLIC_API_URL`: http://localhost:13390
- `NODE_ENV`: development/production

---

### 2. Admin Console (Internal)

**Path**: `apps/admin-console/`
**Dockerfile**: `apps/admin-console/Dockerfile`
**Port**: 8101
**Technology**: React/Next.js or similar (needs verification)

**Purpose**: Internal administration and monitoring

**Build Command**:
```bash
docker build --no-cache --platform linux/arm64 \
  -t nina-admin-console:arm64 \
  -f apps/admin-console/Dockerfile \
  apps/admin-console/
```

**Environment Variables** (expected):
- `API_URL` or `NEXT_PUBLIC_API_URL`: http://localhost:13390
- `NODE_ENV`: development/production

---

### 3. Enhanced Memory (eM) Sidecar

**Path**: Root directory
**Dockerfile**: `Dockerfile.em`
**Port**: 7070
**Technology**: Python 3.11 + mem0ai + FastAPI

**Purpose**: Advanced memory enhancement using mem0ai library

**Dependencies**:
- mem0ai
- fastapi
- uvicorn[standard]
- pydantic

**Build Command**:
```bash
docker build --no-cache --platform linux/arm64 \
  -t nina-em:arm64 \
  -f Dockerfile.em .
```

**Run Command**:
```bash
container run -d --name ninaivalaigal-dev-em -p 7070:7070 \
  -e API_URL=http://192.168.64.61:8000 \
  nina-em:arm64
```

---

## Port Allocation (Development Environment)

| Service | Host Port | Container Port | Protocol |
|---------|-----------|----------------|----------|
| PostgreSQL | 5452 | 5432 | TCP |
| PgBouncer | 6442 | 6432 | TCP |
| Redis | 6399 | 6379 | TCP |
| API | 13390 | 8000 | HTTP |
| Enhanced Memory | 7070 | 7070 | HTTP |
| Customer UI | 8100 | 3000/8080 | HTTP |
| Admin Console | 8101 | 3000/8080 | HTTP |

---

## Deployment Order

**Order matters due to dependencies**:

1. ✅ Database (PostgreSQL) - Already running
2. ✅ PgBouncer - Already running
3. ✅ Redis - Already running
4. ✅ API Backend - Already running
5. 🔄 Enhanced Memory (eM) - Optional, can run independently
6. 🔄 Customer UI - Depends on API
7. 🔄 Admin Console - Depends on API

---

## Health Check Endpoints

| Service | Health Check URL | Expected Response |
|---------|------------------|-------------------|
| API | http://localhost:13390/health | `{"status":"ok"}` |
| Enhanced Memory | http://localhost:7070/health | TBD |
| Customer UI | http://localhost:8100/ | 200 OK |
| Admin Console | http://localhost:8101/ | 200 OK |

---

## Quick Start Commands

### Start All Containers
```bash
./scripts/nina-intelligence-stack-start-unified.sh --with-ui
```

### Start Individual Containers
```bash
# eM sidecar
./scripts/nv-em-start.sh

# UI
./scripts/nv-ui-start.sh
```

### Check Status
```bash
container list | grep ninaivalaigal
```

### Stop All
```bash
./scripts/nina-intelligence-stack-stop-unified.sh
```

---

## Tags for Quick Reference

- `#customer-ui` - External customer interface
- `#admin-console` - Internal admin interface
- `#enhanced-memory` - mem0ai sidecar
- `#container-architecture` - Overall structure
- `#deployment-order` - Startup sequence
- `#port-mapping` - Port allocations

---

**Document Version**: 1.0
**Last Updated**: October 7, 2025
**Status**: 4/7 containers running, 3 to deploy
