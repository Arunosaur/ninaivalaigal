# API Container - Apple Container CLI
**Main FastAPI backend with all routes and business logic**

---

## Container Information

- **Name**: `ninaivalaigal-dev-api`
- **Image**: `nina-api:arm64`
- **Base**: `python:3.11-slim`
- **Architecture**: ARM64
- **Port Mapping**: `13390:8000` (dev)
- **Entry Point**: `run_server.py` → `server/main.py`

---

## What's Inside

### Application
- **FastAPI backend** - All API routes and business logic
- **Routers**: Auth, users, teams, memory, context, graph intelligence, workflows
- **Database**: PostgreSQL via PgBouncer (with AGE + pgvector)
- **Redis**: Rate limiting, caching, sessions
- **Security**: JWT auth, RBAC, CORS, rate limiting
- **Observability**: Health checks, metrics, monitoring

### Key Files
```
/app/
├── server/
│   ├── main.py                    # Main FastAPI app
│   ├── config.py                  # Configuration
│   ├── database.py                # Database manager
│   ├── redis_client.py            # Redis client
│   ├── routers/                   # API route modules
│   ├── security/                  # Auth & middleware
│   └── requirements.txt           # Python dependencies
├── run_server.py                  # Entry point
├── alembic/                       # Database migrations
└── frontend/                      # Static files (if served)
```

---

## Prerequisites

### Dependencies Running
```bash
# Must be started first (in order)
1. ninaivalaigal-dev-db          # Database
2. ninaivalaigal-dev-redis       # Redis
3. ninaivalaigal-dev-pgbouncer   # PgBouncer

# Get their IPs
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

### Tools Required
```bash
# jq for JSON parsing
brew install jq

# curl for testing
brew install curl
```

---

## Build Process

### Method 1: Apple Container CLI

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build (1-2 minutes)
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# Verify dependencies
container run --rm nina-api:arm64 pip list | grep -E "structlog|fastapi|uvicorn"
```

### Method 2: Docker Build + Transfer

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build with Docker (1-2 minutes)
docker build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# Verify critical dependencies
docker run --rm nina-api:arm64 pip list | grep -E "structlog|stripe|reportlab|psycopg"

# Transfer
docker save nina-api:arm64 -o /tmp/nina-api-$(date +%Y%m%d-%H%M%S).tar
container image load --input /tmp/nina-api-*.tar
```

### ⚠️ CRITICAL: Always Use --no-cache

After ANY of these changes:
- `server/requirements.txt` modifications
- Dockerfile changes
- Base image updates

```bash
# Wrong - will miss new dependencies
container build -t nina-api:arm64 -f Dockerfile.api .

# Correct
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
```

---

## Dockerfile

**Location**: `/Users/swami/WorkSpace/ninaivalaigal/Dockerfile.api`

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvloop httptools structlog

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY server/ ./server/
COPY frontend/ ./frontend/
COPY run_server.py ./
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "run_server.py"]
```

---

## Runtime Configuration

### Get Connection Information
```bash
# Get service IPs
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "PgBouncer IP: $PGB_IP"
echo "Redis IP: $REDIS_IP"
```

### Start Container

```bash
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
  -e ENVIRONMENT="dev" \
  -e LOG_LEVEL="debug" \
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64

# Wait for startup
sleep 10
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection (via PgBouncer) |
| `NINAIVALAIGAL_DATABASE_URL` | Yes | - | Same as DATABASE_URL (legacy) |
| `REDIS_URL` | Yes | - | Redis connection with auth |
| `NINAIVALAIGAL_JWT_SECRET` | Yes | - | JWT signing secret |
| `ENVIRONMENT` | No | `production` | Environment (`dev`/`test`/`staging`/`prod`) |
| `LOG_LEVEL` | No | `info` | Logging level |
| `PYTHONPATH` | No | `/app` | Python module search path |

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-api
```

### Check Logs
```bash
# View all logs
container logs ninaivalaigal-dev-api

# Follow logs
container logs -f ninaivalaigal-dev-api

# Check for errors
container logs ninaivalaigal-dev-api | grep -E "ERROR|CRITICAL"

# Check startup
container logs ninaivalaigal-dev-api | grep -E "Application startup|Uvicorn running"
```

### Health Check
```bash
# Basic health
curl http://localhost:13390/health
# Expected: {"status":"ok"}

# Detailed health
curl http://localhost:13390/api/health

# OpenAPI docs
open http://localhost:13390/docs
```

### Test Database Connection
```bash
# Should show database version
curl http://localhost:13390/api/health/database
```

### Test Redis Connection
```bash
# Should confirm Redis connectivity
curl http://localhost:13390/api/health/redis
```

### Test Authentication
```bash
# Should return 401 without auth
curl -X POST http://localhost:13390/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"wrong"}'  # pragma: allowlist secret
```

---

## Get Container IP

```bash
API_IP=$(container inspect ninaivalaigal-dev-api | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "API IP: $API_IP"

# For EM or other services to connect
EM_CONNECTION="http://${API_IP}:8000"
```

---

## Common Operations

### Run Database Migrations
```bash
# Inside container
container exec ninaivalaigal-dev-api alembic upgrade head

# Check current version
container exec ninaivalaigal-dev-api alembic current

# Show migration history
container exec ninaivalaigal-dev-api alembic history
```

### Access Python Shell
```bash
# Python REPL with app context
container exec -it ninaivalaigal-dev-api python

# Then in Python:
# >>> from server.database import DatabaseManager
# >>> from server.redis_client import redis_client
```

### Check Dependencies
```bash
# List all installed packages
container exec ninaivalaigal-dev-api pip list

# Check specific dependency
container exec ninaivalaigal-dev-api pip show structlog

# Verify imports work
container exec ninaivalaigal-dev-api python -c "import structlog; import stripe; import reportlab; print('✅ All imports work')"
```

---

## Monitoring

### Performance Metrics
```bash
# Prometheus metrics
curl http://localhost:13390/metrics

# Performance summary
curl http://localhost:13390/api/metrics/performance
```

### Active Connections
```bash
# Check database connections via PgBouncer
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW CLIENTS;" | grep nina
```

### Redis Usage
```bash
# Check Redis keys created by API
redis-cli -h localhost -p 6389 -a nina_redis_dev_password --scan --pattern "rate_limit:*"
redis-cli -h localhost -p 6389 -a nina_redis_dev_password --scan --pattern "session:*"
redis-cli -h localhost -p 6389 -a nina_redis_dev_password --scan --pattern "cache:*"
```

### Memory Usage
```bash
# Container stats
container stats ninaivalaigal-dev-api
```

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
container logs ninaivalaigal-dev-api
```

**Common issues**:

1. **Missing dependencies**:
   ```bash
   # Error: ModuleNotFoundError: No module named 'structlog'
   # Solution: Rebuild with --no-cache
   container stop ninaivalaigal-dev-api
   container delete ninaivalaigal-dev-api
   container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
   # Then restart
   ```

2. **Database connection failed**:
   ```bash
   # Error: could not connect to server
   # Solution: Check PgBouncer is running and IP is correct
   PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   ping -c 3 $PGB_IP
   psql "postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" -c "SELECT 1;"  # pragma: allowlist secret
   ```

3. **Redis connection failed**:
   ```bash
   # Error: Error connecting to redis
   # Solution: Check Redis is running and password is correct
   REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   redis-cli -h $REDIS_IP -a nina_redis_dev_password ping
   ```

4. **Port conflict**:
   ```bash
   # Error: address already in use
   lsof -i :13390
   # Kill conflicting process or use different port
   ```

### Import Errors

**Error**: `ModuleNotFoundError`
```bash
# Check if dependency is in requirements.txt
grep {module_name} server/requirements.txt

# If missing, add it
echo "{module_name}==X.Y.Z" >> server/requirements.txt

# Rebuild with --no-cache
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
```

### Database Connection Issues

**Error**: `RuntimeError: Database connection failed`
```bash
# Test direct DB connection
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
psql "postgresql://nina:change_me_securely@${DB_IP}:5432/nina" -c "SELECT 1;"  # pragma: allowlist secret

# Test PgBouncer connection
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
psql "postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" -c "SELECT 1;"  # pragma: allowlist secret

# Check environment variables
container exec ninaivalaigal-dev-api env | grep DATABASE_URL
```

### Authentication Failures

**Error**: `Rate limiting error: Authentication required`
```bash
# Check Redis URL has password
container exec ninaivalaigal-dev-api env | grep REDIS_URL
# Should show: redis://:password@IP:6379/0
#                      ^password here

# Test Redis auth
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
redis-cli -h $REDIS_IP -a nina_redis_dev_password ping
```

### Health Check Fails

**Error**: `Health check failed`
```bash
# Check what the health endpoint returns
curl -v http://localhost:13390/health

# Check if server is listening
container exec ninaivalaigal-dev-api netstat -tuln | grep 8000

# Check application logs
container logs ninaivalaigal-dev-api | tail -50
```

---

## Complete Startup Script

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting API Container ==="

# 1. Verify prerequisites
echo "Checking prerequisites..."
for service in ninaivalaigal-dev-db ninaivalaigal-dev-redis ninaivalaigal-dev-pgbouncer; do
  if ! container list | grep -q "$service"; then
    echo "Error: $service not running"
    exit 1
  fi
done

# 2. Get service IPs
echo "Getting service IPs..."
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "PgBouncer IP: $PGB_IP"
echo "Redis IP: $REDIS_IP"

# 3. Test connections
echo "Testing database connection..."
if ! psql "postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" -c "SELECT 1;" > /dev/null 2>&1; then  # pragma: allowlist secret
  echo "Error: Cannot connect to database via PgBouncer"
  exit 1
fi

echo "Testing Redis connection..."
if ! redis-cli -h $REDIS_IP -a nina_redis_dev_password ping > /dev/null 2>&1; then
  echo "Error: Cannot connect to Redis"
  exit 1
fi

# 4. Start API
echo "Starting API container..."
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
  -e ENVIRONMENT="dev" \
  -e LOG_LEVEL="debug" \
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64

# 5. Wait for startup
echo "Waiting for API to start..."
sleep 10

# 6. Verify
echo "Testing API health..."
if curl -f http://localhost:13390/health > /dev/null 2>&1; then
  echo "✅ API is healthy"
  echo ""
  echo "API URL: http://localhost:13390"
  echo "API Docs: http://localhost:13390/docs"
  echo ""
  API_IP=$(container inspect ninaivalaigal-dev-api | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
  echo "API IP (for other containers): $API_IP"
else
  echo "❌ API health check failed"
  echo "Logs:"
  container logs ninaivalaigal-dev-api | tail -20
  exit 1
fi
```

---

## Integration

### With EM (Enhanced Memory)
```bash
# EM needs to connect to API
API_IP=$(container inspect ninaivalaigal-dev-api | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start EM with API connection
container run -d --name ninaivalaigal-dev-em \
  -e API_URL="http://${API_IP}:8000" \
  nina-em:arm64
```

### With UI Containers
```bash
# UI needs API endpoint
API_IP=$(container inspect ninaivalaigal-dev-api | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start UI with API connection
container run -d --name ninaivalaigal-dev-ui-admin \
  -e NEXT_PUBLIC_API_URL="http://localhost:13390" \
  -e INTERNAL_API_URL="http://${API_IP}:8000" \
  nina-admin-console:arm64
```

---

## Performance Tuning

### Development
```bash
# Lower worker count, verbose logging
-e WORKERS=2
-e LOG_LEVEL=debug
-e RELOAD=true
```

### Production
```bash
# More workers, structured logging
-e WORKERS=4
-e LOG_LEVEL=info
-e RELOAD=false
```

---

## Security

### JWT Secret
```bash
# Generate secure secret
SECURE_SECRET=$(openssl rand -base64 32)

# Use in production
-e NINAIVALAIGAL_JWT_SECRET="${SECURE_SECRET}"  # pragma: allowlist secret
```

### Database Credentials
```bash
# Use environment-specific passwords
-e DATABASE_URL="postgresql://nina:${SECURE_DB_PASSWORD}@${PGB_IP}:6432/nina"  # pragma: allowlist secret
```

---

## Clean Up

```bash
container stop ninaivalaigal-dev-api
container delete ninaivalaigal-dev-api
container image rm nina-api:arm64
```

---

## Quick Reference

```bash
# Build
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# Get IPs
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64

# Verify
curl http://localhost:13390/health

# Logs
container logs -f ninaivalaigal-dev-api
```
