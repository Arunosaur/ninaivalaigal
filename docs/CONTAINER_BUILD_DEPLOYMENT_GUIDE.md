# Container Build & Deployment Master Guide

**Last Updated**: October 7, 2025
**Status**: Production Ready ✅

## Table of Contents
1. [Critical Lessons Learned](#critical-lessons-learned)
2. [Build Process](#build-process)
3. [Verification Checklist](#verification-checklist)
4. [Deployment Guide](#deployment-guide)
5. [Troubleshooting](#troubleshooting)
6. [Container Specifications](#container-specifications)

---

## Critical Lessons Learned

### **Issue #1: Apple Container CLI DNS Limitations**
**Problem**: Apple Container CLI on macOS Sequoia has DNS resolution issues during builds.
```bash
Error: Temporary failure resolving 'deb.debian.org'
```

**Solution**: Use Docker to build, then transfer to Apple Container CLI
```bash
# Build with Docker
docker build --no-cache --platform linux/arm64 -t nina-api:arm64 -f containers/api/Dockerfile .

# Save with timestamp
docker save nina-api:arm64 -o /tmp/nina-api-$(date +%Y%m%d-%H%M%S).tar

# Load into Apple Container CLI
container image load -i /tmp/nina-api-*.tar
```

**Reference**: [GitHub Issue #346](https://github.com/apple/container/issues/346)

### **Issue #2: Image Caching - The Silent Killer**
**Problem**: Apple Container CLI caches multiple versions of the same tag, leading to old code running.

**Critical Protocol**:
```bash
# 1. DELETE ALL old images before building
container image delete --all  # Or target specific images

# 2. Verify deletion
container image list | grep nina-api || echo "✅ Clean slate"

# 3. Build fresh
docker build --no-cache --platform linux/arm64 -t nina-api:arm64 -f containers/api/Dockerfile .

# 4. Save with UNIQUE timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker save nina-api:arm64 -o /tmp/nina-api-VERIFIED-${TIMESTAMP}.tar

# 5. Load and verify
container image load -i /tmp/nina-api-VERIFIED-${TIMESTAMP}.tar
container run --rm nina-api:arm64 cat /app/run_server.py | grep -n "/app/server"
```

### **Issue #3: SPEC-055 Compliance - Import-Time Database Connections**
**Problem**: Module imports created database connections, causing crashes when DB unavailable.

**Before (WRONG)**:
```python
# server/main.py - BAD PRACTICE
db_manager = DatabaseManager(database_url)  # Connects at import time!
```

**After (CORRECT)**:
```python
# server/main.py - SPEC-055 Compliant
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    logger.info("🚀 Starting API server...")

    # Initialize database connection AFTER app starts
    database_url = get_database_url()
    db_manager = DatabaseManager(database_url)
    app.state.db_manager = db_manager

    # Initialize other services
    app.state.spec_context_manager = SpecKitContextManager(app.state.db)
    app.state.auto_recorder = get_auto_recorder(app.state.db_manager)

    logger.info("🎉 API server startup complete!")

    yield  # Server is running

    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")
    if hasattr(app.state.db_manager, "close"):
        app.state.db_manager.close()
    logger.info("👋 Shutdown complete")

app = FastAPI(lifespan=lifespan)
```

**Benefits**:
- ✅ Container starts even if database temporarily unavailable
- ✅ Proper resource cleanup on shutdown
- ✅ Better error messages
- ✅ Graceful degradation

### **Issue #4: PYTHONPATH Configuration**
**Problem**: Module imports failed due to incorrect Python path.

**Solution**: Set PYTHONPATH in THREE places:

1. **Dockerfile** (line 24):
```dockerfile
ENV PYTHONPATH=/app:/app/server
```

2. **run_server.py** (lines 9-12):
```python
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
sys.path.insert(0, "/app/server")  # Absolute container path
sys.path.insert(0, os.path.join(app_dir, 'server'))  # Fallback
```

3. **Container environment** (runtime):
```bash
-e PYTHONPATH=/app:/app/server
```

### **Issue #5: Password Mismatches**
**Problem**: Different passwords in different scripts caused authentication failures.

**Solution**: Always check actual container environment:
```bash
# Check database password
container inspect ninaivalaigal-dev-db 2>/dev/null | grep POSTGRES_PASSWORD

# Check Redis password
container inspect ninaivalaigal-dev-redis 2>/dev/null | grep REDIS_PASSWORD
```

**Correct Passwords (Dev Environment)**:
- Database: `dev_password_change_in_production`
- Redis: `dev_redis_password`
- PgBouncer: Same as database (uses SCRAM-SHA-256)

### **Issue #6: Redis Connection Configuration**
**Problem**: Rate limiter middleware tried connecting to `redis:6379` instead of IP address.

**Solution**: Always set REDIS_URL explicitly:
```bash
-e REDIS_URL="redis://:dev_redis_password@192.168.64.189:6379/0"
```

---

## Build Process

### Prerequisites
```bash
# Ensure Docker is available (for building due to DNS issues)
which docker || echo "Install Docker Desktop"

# Ensure Apple Container CLI is available
which container || echo "Install Apple Container CLI"
```

### Build Steps (API Container)

```bash
# 1. Clean old images
container image delete --all

# 2. Build with Docker
cd /Users/swami/WorkSpace/ninaivalaigal
docker build --no-cache --platform linux/arm64 \
  -t nina-api:arm64 \
  -f containers/api/Dockerfile .

# 3. Verify Docker image
docker run --rm nina-api:arm64 cat /app/run_server.py | grep "/app/server"
docker run --rm -e NINAIVALAIGAL_JWT_SECRET=test nina-api:arm64 \
  python -c "import sys; sys.path.insert(0, '/app/server'); \
  from approval_workflow import ApprovalWorkflowManager; print('✅')"

# 4. Save with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker save nina-api:arm64 -o /tmp/nina-api-VERIFIED-${TIMESTAMP}.tar
echo "SAVED_FILE=/tmp/nina-api-VERIFIED-${TIMESTAMP}.tar" > /tmp/nina-build-info.txt

# 5. Load into Apple Container CLI
container image load -i /tmp/nina-api-VERIFIED-${TIMESTAMP}.tar

# 6. Verify Apple Container CLI image
container run --rm nina-api:arm64 cat /app/run_server.py | head -12 | tail -3
```

---

## Verification Checklist

Use this checklist for EVERY build:

- [ ] 1. Code changes saved in workspace
- [ ] 2. Old images deleted from Apple Container CLI
- [ ] 3. Built with Docker using `--no-cache`
- [ ] 4. Docker image verified (run_server.py content)
- [ ] 5. Docker image tested (imports work)
- [ ] 6. Saved to tar with timestamp
- [ ] 7. Loaded into Apple Container CLI
- [ ] 8. Apple Container CLI image verified (same content)
- [ ] 9. Container started with correct environment variables
- [ ] 10. Health check passes

**Pro Tip**: Save this as a script for automation.

---

## Deployment Guide

### Get Container IPs
```bash
# Database (via PgBouncer)
PGBOUNCER_IP=$(container list | grep pgbouncer | awk '{print $4}')

# Redis
REDIS_IP=$(container list | grep redis | awk '{print $4}')

echo "PgBouncer: $PGBOUNCER_IP"
echo "Redis: $REDIS_IP"
```

### Start API Container
```bash
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://:dev_redis_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production" \
  -e PYTHONPATH=/app:/app/server \
  -e ENVIRONMENT=development \
  nina-api:arm64
```

### Verify Deployment
```bash
# Wait for startup
sleep 10

# Check running
container list | grep ninaivalaigal-dev-api

# Test health endpoint
curl -s http://localhost:13390/health
# Expected: {"status":"ok"}

# Check logs for lifespan messages
container logs ninaivalaigal-dev-api 2>&1 | grep -E "Starting|Database|Redis|startup"
```

---

## Troubleshooting

### Container Stops Immediately

**Diagnosis**:
```bash
container logs ninaivalaigal-dev-api 2>&1 | tail -50
```

**Common Issues**:

1. **ModuleNotFoundError: No module named 'approval_workflow'**
   - Check: `container run --rm nina-api:arm64 cat /app/run_server.py | grep "/app/server"`
   - Fix: Rebuild with correct `run_server.py` (see Build Process)

2. **SASL authentication failed**
   - Check: Database password in container
   - Fix: Use correct password `dev_password_change_in_production`

3. **Redis connection error**
   - Check: Redis IP and password
   - Fix: Set REDIS_URL explicitly (see Deployment Guide)

4. **Import-time database connection**
   - Check: `server/main.py` has lifespan pattern
   - Fix: Implement SPEC-055 compliant lifespan (see Issue #3)

### Health Check Returns "Internal Server Error"

**Common Causes**:
- Redis connection failing
- Database authentication failing
- Missing environment variables

**Debug**:
```bash
# Check all environment variables
container exec ninaivalaigal-dev-api env | grep -E "DATABASE|REDIS|JWT"

# Test Redis connection
container exec ninaivalaigal-dev-api python -c "
import redis
r = redis.from_url('redis://:dev_redis_password@192.168.64.189:6379/0')
print(r.ping())
"

# Test database connection through PgBouncer
container exec ninaivalaigal-dev-api python -c "
import psycopg2
conn = psycopg2.connect('postgresql://nina:dev_password_change_in_production@192.168.64.208:6432/ninaivalaigal_dev')
print('✅ Connected')
conn.close()
"
```

---

## Container Specifications

### API Container (nina-api:arm64)

**Ports**:
- Container: 8000
- Host: 13390

**Required Environment Variables**:
```bash
DATABASE_URL                    # PostgreSQL via PgBouncer
NINAIVALAIGAL_DATABASE_URL      # Same as DATABASE_URL
REDIS_URL                        # Redis connection string
NINAIVALAIGAL_JWT_SECRET        # JWT signing secret
PYTHONPATH                       # /app:/app/server
ENVIRONMENT                      # development/production
```

**Dependencies**:
- Database (via PgBouncer on port 6432)
- Redis (on port 6379)

**Health Check**:
```bash
curl http://localhost:13390/health
```

**Swagger/API Docs**:
```bash
# Protected by authentication
curl http://localhost:13390/docs
```

### Database Container (nina-intelligence-db:arm64)

**Ports**:
- Container: 5432
- Host: 5452

**Credentials**:
- User: `nina`
- Password: `dev_password_change_in_production`
- Database: `ninaivalaigal_dev`

### PgBouncer Container (nina-pgbouncer:arm64)

**Ports**:
- Container: 6432
- Host: 6442

**Configuration**:
- Auth: SCRAM-SHA-256
- Pool Mode: transaction
- Max Connections: 100

### Redis Container (redis:7-alpine)

**Ports**:
- Container: 6379
- Host: 6399

**Credentials**:
- Password: `dev_redis_password`

**Configuration**:
- Max Memory: 512MB
- Eviction: allkeys-lru

---

## Quick Reference Commands

```bash
# Clean slate rebuild
container image delete --all
docker build --no-cache --platform linux/arm64 -t nina-api:arm64 -f containers/api/Dockerfile .
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker save nina-api:arm64 -o /tmp/nina-api-${TIMESTAMP}.tar
container image load -i /tmp/nina-api-${TIMESTAMP}.tar

# Get IPs
container list | grep -E "(pgbouncer|redis|db)" | awk '{print $1, $4}'

# Deploy
container stop ninaivalaigal-dev-api && container delete ninaivalaigal-dev-api
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.64.208:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://:dev_redis_password@192.168.64.189:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production" \
  -e PYTHONPATH=/app:/app/server \
  -e ENVIRONMENT=development \
  nina-api:arm64

# Test
curl http://localhost:13390/health
```

---

## Tags for Quick Reference

**Search Tags**:
- `#container-build` - Build process issues
- `#dns-issues` - Apple Container CLI DNS problems
- `#image-caching` - Stale image problems
- `#spec-055` - Import-time connection issues
- `#pythonpath` - Module import errors
- `#authentication` - Password/credential issues
- `#redis-connection` - Redis connectivity
- `#deployment` - Deployment procedures
- `#troubleshooting` - Debug procedures

**Related Files**:
- `CONTAINER_BUILD_CHECKLIST.md` - Quick checklist
- `API_CONTAINER_FIX_SUMMARY.md` - Original issue summary
- `containers/api/Dockerfile` - API container definition
- `server/main.py` - FastAPI app with lifespan
- `run_server.py` - Uvicorn startup script

---

**Document Version**: 1.0
**Maintained By**: Development Team
**Next Review**: When deployment issues occur
