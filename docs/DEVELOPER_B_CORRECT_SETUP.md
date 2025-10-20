# Developer B - Correct Core API Setup

**STOP!** ❌ Do NOT use the old `mem0` configuration.

---

## ❌ **WRONG Configuration (OLD - mem0)**

```bash
# DON'T USE THIS:
export DATABASE_URL=postgresql://mem0user:mem0pass@localhost:5432/mem0db  # pragma: allowlist secret
conda run -n nina python services/core-api/main.py &
```

**Problems:**
- ❌ Direct PostgreSQL connection (bypasses PgBouncer)
- ❌ Using `mem0user` (outdated user)
- ❌ Using `mem0db` (outdated database name)
- ❌ Port 5432 instead of PgBouncer port
- ❌ Running from wrong directory

---

## ✅ **CORRECT Configuration (ninaivalaigal)**

### **Option 1: Use Existing Container** ⭐ RECOMMENDED

The Core API is already running in a container. Just test against it:

```bash
# Test the running Core API
curl http://localhost:13390/health

# View API docs
open http://localhost:13390/docs

# Run your tests
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'  # pragma: allowlist secret
```

**Why this is best:**
- ✅ Already configured correctly
- ✅ Using PgBouncer for connection pooling
- ✅ Proper environment variables set
- ✅ No need to run manually

---

### **Option 2: Run Locally for Development**

If you need to run Core API locally for debugging:

```bash
# 1. Set correct environment variables
export DATABASE_URL="postgresql://nina:nina@localhost:6452/ninaivalaigal_dev"  # pragma: allowlist secret
export REDIS_URL="redis://localhost:6399"
export NINAIVALAIGAL_JWT_SECRET="your-secret-key"  # pragma: allowlist secret
export ENVIRONMENT="development"

# 2. Make sure PgBouncer and Redis are running
make check-stack  # Should show db, pgbouncer, redis running

# 3. Run from correct directory
cd /Users/swami/WorkSpace/ninaivalaigal
conda activate nina
python server/main.py  # Note: server/main.py, NOT services/core-api/main.py

# 4. Test
curl http://localhost:8000/health  # Local dev runs on 8000
```

---

## 📋 **Correct Connection Details**

### **Database Connection**
```bash
# Through PgBouncer (CORRECT):
Host: localhost
Port: 6452          # PgBouncer port, NOT 5432!
Database: ninaivalaigal_dev  # NOT mem0db
User: nina          # NOT mem0user
Password: nina      # Check .env for actual password

# Full URL:
postgresql://nina:nina@localhost:6452/ninaivalaigal_dev  # pragma: allowlist secret
```

### **Why PgBouncer?**
- ✅ Connection pooling (prevents exhaustion)
- ✅ Better performance under load
- ✅ Production-like setup
- ⚠️ Exception: Rust Memory Service bypasses PgBouncer (documented technical debt - Task #85)

---

## 🔍 **How to Find Running Services**

```bash
# Check what's running
container list

# Find Core API
container list | grep core-api
# Output: ninaivalaigal-dev-core-api on 192.168.66.93:13390

# Find PgBouncer
container list | grep pgbouncer
# Output: ninaivalaigal-dev-pgbouncer on 192.168.66.90:6452

# Find Redis
container list | grep redis
# Output: ninaivalaigal-dev-redis on 192.168.66.89:6399
```

---

## 🧪 **Testing Checklist for Task #39**

### **Step 1: Verify Services Running**
```bash
# Core API
curl http://localhost:13390/health
# Expected: {"status":"healthy","service":"core-api","version":"1.0.0"}

# PgBouncer
psql -h localhost -p 6452 -U nina -d ninaivalaigal_dev -c "SELECT 1;"
# Expected: Returns 1

# Redis
redis-cli -p 6399 PING
# Expected: PONG
```

### **Step 2: Test Authentication Endpoints**
```bash
# Login (will fail without valid user, but tests endpoint)
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'  # pragma: allowlist secret

# Check available endpoints
curl http://localhost:13390/openapi.json | jq '.paths | keys'
```

### **Step 3: Test Memory Endpoints**
```bash
# List available memory endpoints
curl http://localhost:13390/openapi.json | jq '.paths | keys | .[] | select(startswith("/memory"))'

# Test memory health
curl http://localhost:13390/memory/health
```

---

## 🔧 **Environment Variables Reference**

```bash
# Core API Configuration
export DATABASE_URL="postgresql://nina:nina@localhost:6452/ninaivalaigal_dev"  # pragma: allowlist secret
export REDIS_URL="redis://localhost:6399"
export NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-prod"  # pragma: allowlist secret
export ENVIRONMENT="development"
export PORT="8000"  # For local dev

# Optional: OpenTelemetry (if testing tracing)
export OTEL_SERVICE_NAME="ninaivalaigal-core-api"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_TRACING_ENABLED="true"
```

---

## 📁 **Directory Structure**

```
ninaivalaigal/
├── server/
│   └── main.py          ← Run THIS for Core API
├── services/
│   ├── core-api/        ← OLD location (deprecated)
│   └── ...
└── scripts/
    └── nv-core-api-start.sh  ← Or use this script
```

---

## 🚀 **Quick Start Commands**

```bash
# Check everything is running
make check-stack

# Test Core API
curl http://localhost:13390/health

# View API documentation
open http://localhost:13390/docs

# Run your tests
cd /Users/swami/WorkSpace/ninaivalaigal
# Use testing guide: docs/DEVELOPER_B_TASK39_GUIDE.md
```

---

## ⚠️ **Common Mistakes to Avoid**

1. ❌ **Using `mem0` anything** - That's old/deprecated
2. ❌ **Port 5432 directly** - Use PgBouncer port 6452
3. ❌ **Running from `services/core-api/`** - Use `server/main.py`
4. ❌ **Using `/api/` prefix in URLs** - Core API has no prefix
5. ❌ **Wrong ports** - Use 13390 (container) or 8000 (local dev)

---

## 📚 **Documentation References**

- **Task #39 Guide:** `docs/DEVELOPER_B_TASK39_GUIDE.md`
- **Port Allocation:** `config/ports.nv.yaml`
- **Environment Setup:** `.env.example`
- **API Documentation:** http://localhost:13390/docs

---

## ❓ **Still Have Questions?**

1. **"Where is the Core API running?"**
   - Container: `ninaivalaigal-dev-core-api` on port 13390
   - Check: `container list | grep core-api`

2. **"Why not use mem0db?"**
   - That's old. We're now using `ninaivalaigal_dev`
   - Check: `psql -h localhost -p 6452 -U nina -l`

3. **"Why PgBouncer?"**
   - Connection pooling for production readiness
   - Port 6452, not direct PostgreSQL 5432

---

**When in doubt, use the containerized Core API at `http://localhost:13390`!** ✅
