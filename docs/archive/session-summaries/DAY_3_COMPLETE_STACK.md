# Day 3: Complete Stack Infrastructure - SPEC-086 Compliant

**Date:** 2024-10-06
**Status:** ✅ Complete Stack Implementation
**Architecture:** SPEC-086 Multi-Runtime Port Allocation

---

## 🎯 What We Built

### Complete Stack Architecture

```
External Users
    ↓
┌─────────────────────────────────────────┐
│  UI Layer (SPEC-086 Ports)              │
│  • Customer App:    8101                │
│  • Admin Console:   8201                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  API Layer                               │
│  • FastAPI Backend: 13390               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Connection Pooling (MANDATORY)         │
│  • PgBouncer:       6452                │
│  ⚠️  ALL apps MUST connect through here │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Data Layer                              │
│  • PostgreSQL:      5452 (admin only)   │
│  • Redis Cache:     6399                │
└─────────────────────────────────────────┘
```

---

## 📦 Components

### 1. PostgreSQL Database
- **Container:** `ninaivalaigal-dev-db`
- **Image:** `nina-intelligence-db:arm64` or `ghcr.io/arunosaur/ninaivalaigal-db:latest`
- **Port:** 5452 (Apple CLI dev)
- **Features:**
  - PostgreSQL 15.14
  - pgvector extension (vector embeddings)
  - Apache AGE extension (graph database)
  - MD5 authentication
  - Persistent volume

### 2. PgBouncer (Connection Pooler)
- **Container:** `ninaivalaigal-dev-pgbouncer`
- **Image:** `bitnami/pgbouncer:1.22.1` (multi-arch) or `nina-pgbouncer:arm64`
- **Port:** 6452
- **Features:**
  - Transaction pooling mode
  - 100 max client connections
  - 20 default pool size
  - ⚠️ **MANDATORY:** All application connections MUST go through PgBouncer

### 3. Redis Cache
- **Container:** `ninaivalaigal-dev-redis`
- **Image:** `redis:7-alpine`
- **Port:** 6399
- **Features:**
  - Password authentication
  - 512MB memory limit
  - LRU eviction policy
  - Persistent volume

### 4. FastAPI Backend
- **Container:** `ninaivalaigal-dev-api`
- **Image:** `nina-api:arm64`
- **Port:** 13390
- **Features:**
  - Connected through PgBouncer (not direct DB)
  - Redis integration
  - JWT authentication
  - Health endpoints
  - OpenAPI docs

### 5. Customer UI (External)
- **Container:** `ninaivalaigal-dev-customer-app`
- **Image:** `ninaivalaigal-ui:latest` or `ninaivalaigal-customer-app:latest`
- **Port:** 8101
- **Purpose:** Public-facing customer application

### 6. Admin Console (Internal)
- **Container:** `ninaivalaigal-dev-admin-console`
- **Image:** `ninaivalaigal-ui:latest` or `ninaivalaigal-admin-console:latest`
- **Port:** 8201
- **Purpose:** Internal staff and admin interface

---

## 🚀 Usage

### Starting the Complete Stack

```bash
# Recommended: Use make command
make stack-start

# Direct script execution
./scripts/stack-start-complete.sh
```

**What happens:**
1. ✅ Starts PostgreSQL with pgvector + Apache AGE
2. ✅ Waits for DB to be ready
3. ✅ Starts PgBouncer connected to DB
4. ✅ Tests PgBouncer connection pooling
5. ✅ Starts Redis cache
6. ✅ Starts API (connected through PgBouncer)
7. ✅ Starts Customer UI (optional, if image exists)
8. ✅ Starts Admin Console (optional, if image exists)

### Checking Stack Status

```bash
make stack-check
```

**Reports:**
- Container running state (all 6 components)
- Database health and extensions
- PgBouncer connection pooling status
- Redis health and memory usage
- API health endpoint status
- Full container listing

### Stopping the Stack

```bash
make stack-stop
```

**Stops in reverse order:**
Admin Console → Customer UI → API → Redis → PgBouncer → Database

### Restarting the Stack

```bash
make stack-restart
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Environment
export NINA_ENV=dev

# Database
export NINA_DB_PASSWORD=dev_password_change_in_production

# Redis
export NINA_REDIS_PASSWORD=dev_redis_password

# API
export NINA_JWT_SECRET=dev_jwt_secret_change_in_production

# Images (optional overrides)
export NINA_DB_IMAGE=ghcr.io/arunosaur/ninaivalaigal-db:latest
export NINA_PGBOUNCER_IMAGE=bitnami/pgbouncer:1.22.1
```

### SPEC-086 Port Matrix (Apple CLI Dev)

| Component | Port | Purpose |
|-----------|------|---------|
| PostgreSQL | 5452 | Direct DB (admin only) |
| **PgBouncer** | **6452** | **App connections (MANDATORY)** |
| Redis | 6399 | Cache |
| API | 13390 | Backend |
| Customer UI | 8101 | External |
| Admin Console | 8201 | Internal |

---

## ⚠️ Critical Rules

### 1. PgBouncer Mandate

**ALL application connections MUST go through PgBouncer (port 6452)**

❌ **WRONG:**
```python
DATABASE_URL = "postgresql://nina:password@localhost:5452/ninaivalaigal_dev"
```

✅ **CORRECT:**
```python
DATABASE_URL = "postgresql://nina:password@localhost:6452/ninaivalaigal_dev"
```

**Why?**
- Connection pooling prevents database connection exhaustion
- Better performance under load
- Production parity (production also uses PgBouncer)
- Enables connection monitoring and metrics

### 2. Direct Database Access

Direct database port (5452) is **ONLY** for:
- Database administration
- Migrations (Alembic)
- Backups
- Manual psql access

---

## 🏗️ Building Images

### Database Image

```bash
cd containers/consolidated-db
container build --no-cache -t nina-intelligence-db:arm64 .
```

### API Image

```bash
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
```

### PgBouncer Image (if using custom)

```bash
cd containers/pgbouncer
container build -t nina-pgbouncer:arm64 .
```

### UI Images (via Docker Compose)

```bash
# Customer app
docker-compose -f compose.docker.yml build customer-app

# Admin console
docker-compose -f compose.docker.yml build admin-console
```

---

## 📊 Health Checks

### Database

```bash
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev -c "SELECT version();"
```

### PgBouncer

```bash
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 6452 -U nina -d ninaivalaigal_dev -c "SELECT 1;"
```

### Redis

```bash
redis-cli -h localhost -p 6399 -a dev_redis_password ping
```

### API

```bash
curl http://localhost:13390/health
curl http://localhost:13390/docs
```

### Customer UI

```bash
curl http://localhost:8101
```

### Admin Console

```bash
curl http://localhost:8201
```

---

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check if image exists
container image list | grep nina

# View logs
container logs ninaivalaigal-dev-db
container logs ninaivalaigal-dev-pgbouncer
container logs ninaivalaigal-dev-api

# Check ports
lsof -i :5452
lsof -i :6452
lsof -i :6399
```

### PgBouncer Connection Issues

```bash
# Test database is accessible
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# Check PgBouncer logs
container logs ninaivalaigal-dev-pgbouncer

# Verify PgBouncer container has DB IP
container list | grep ninaivalaigal-dev-db
```

### API Not Connecting to Database

**Common issue:** API trying to connect directly to DB instead of PgBouncer

**Check:**
```bash
container logs ninaivalaigal-dev-api | grep -i database

# Should show connection to PgBouncer IP, not DB IP
```

### Image Not Found

```bash
# Database
cd containers/consolidated-db
container build --no-cache -t nina-intelligence-db:arm64 .

# API
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# PgBouncer (use bitnami instead)
export NINA_PGBOUNCER_IMAGE=bitnami/pgbouncer:1.22.1
```

---

## 📈 Features

### Graceful Degradation

- UIs are optional - stack starts even if UI images don't exist
- API is semi-optional - infrastructure starts regardless
- Clear warnings if components are missing

### Image Flexibility

- Supports GHCR images or local builds
- Auto-detects available images
- Environment variable overrides

### Health Monitoring

- Container state checking
- Database query tests
- PgBouncer connection pooling verification
- Redis PING tests
- API health endpoint checks

### SPEC-086 Compliance

- Unified naming convention
- Predictable port allocation
- Environment separation (dev/test/prod)
- Runtime-specific ports

---

## 📝 Makefile Commands

```bash
# Stack Management
make stack-start          # Start complete stack
make stack-stop           # Stop all containers
make stack-check          # Detailed health report
make stack-restart        # Stop + start

# Testing
make test-crash-recovery  # Validate recovery capabilities
```

---

## 🎯 Success Criteria

✅ **All 6 components defined and managed**
✅ **PgBouncer mandate enforced**
✅ **Health checks for all layers**
✅ **SPEC-086 port allocation followed**
✅ **Graceful degradation for optional components**
✅ **Clear error messages and warnings**
✅ **Unified naming convention**

---

## 🚧 Known Limitations

### 1. Apple Container CLI

- No native `--restart` flag
- External watchdog needed for auto-restart
- Container layer caching requires `--no-cache` for rebuilds

### 2. Password Configuration

- Multiple sources (env files, scripts, containers)
- **TODO Day 4:** Consolidate to single source of truth

### 3. UI Images

- May not exist if not built via docker-compose
- Scripts handle gracefully with warnings
- Build separately if needed

---

## 📅 Next Steps

### Day 4 (Planned)

1. **Password Consolidation**
   - Single source of truth for all passwords
   - Environment variable standardization
   - Update all scripts consistently

2. **API Image Improvements**
   - Ensure latest dependencies
   - Add --no-cache protocol
   - Dependency verification

3. **Stack Testing**
   - Test full startup sequence
   - Validate PgBouncer connections
   - Smoke test all endpoints

### Day 5 (Planned)

1. **Complete Stack Testing**
   - End-to-end flow testing
   - Load testing through PgBouncer
   - UI integration testing

2. **Documentation Polish**
   - Connection string examples
   - Architecture diagrams
   - Troubleshooting playbook

3. **Commit & Push**
   - Tag: `v0.9-phase1-day5`
   - Update WORKING_STATE.md
   - Push to GitHub

---

## 📊 Comparison

### Before Day 3

- ❌ Only DB + Redis managed
- ❌ No PgBouncer in scripts
- ❌ No API/UI management
- ❌ Manual container startup
- ❌ No health checks

### After Day 3

- ✅ Complete 6-component stack
- ✅ PgBouncer mandate enforced
- ✅ Automated startup sequence
- ✅ Comprehensive health checks
- ✅ SPEC-086 compliant
- ✅ Production-ready architecture

---

**Last Updated:** 2024-10-06 13:40:00
**Status:** Ready for Day 4 testing and password consolidation
