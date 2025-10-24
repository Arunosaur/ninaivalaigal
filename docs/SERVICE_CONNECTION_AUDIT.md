# Service Connection Audit - PgBouncer & Redis

**Date:** October 20, 2025, 10:10 PM
**Objective:** Audit all services for proper PgBouncer/Redis connections using environment variables

---

## 📋 Services to Audit

| Service | Running | Database | Redis | Status |
|---------|---------|----------|-------|--------|
| ninaivalaigal-dev-em | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-load-tester | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-business-service | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-memory-service | ✅ | ✅ SESS | ✅ | ✅ Fixed (Task #85) |
| ninaivalaigal-dev-grpc-gateway | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-graphops | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-core-api | ✅ | ✅ TX | ✅ | ✅ Fixed (Just now) |
| ninaivalaigal-dev-graph-service | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-jaeger | ✅ | N/A | N/A | ℹ️ Observability |
| ninaivalaigal-dev-admin-vendor | ✅ | ? | ? | 🔍 Checking |
| ninaivalaigal-dev-customer | ❓ | ? | ? | 🔍 Checking |

---

## 🎯 Connection Strategy

### **PgBouncer Routing:**
- **Transaction Mode (port 6432):** Stateless services (Core API, GraphOps, Business Service, etc.)
- **Session Mode (port 6433):** Services with prepared statements (Memory Service)

### **Redis:**
- All services should use `$REDIS_URL` from `.env.dev`
- Format: `redis://:$REDIS_PASSWORD@$REDIS_IP:6379/0`

---

## 🔍 Audit Results

### ✅ **1. Memory Service (Rust/SQLx)**

**Container:** `ninaivalaigal-dev-memory-service`
**Start Script:** `rust-services/memory-service/nv-memory-service-start.sh`
**Status:** ✅ **COMPLIANT**

**PgBouncer:**
- ✅ Uses environment variables: `$NINA_DB_USER`, `$NINA_DB_PASSWORD`
- ✅ Connects to: `ninaivalaigal-dev-pgbouncer-sess` (port 6433)
- ✅ Correct mode: **Session** (required for SQLx prepared statements)

**Redis:**
- ✅ Uses environment variables: `$REDIS_URL`
- ✅ Includes password if set

**Code:**
```bash
# Line 48
PGBOUNCER_CONTAINER="ninaivalaigal-${NINA_ENV}-pgbouncer-sess"
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6433/..."
```

---

### ✅ **2. Core API (Python FastAPI)**

**Container:** `ninaivalaigal-dev-core-api`
**Start Script:** `services/core-api/nv-core-api-start.sh`
**Status:** ✅ **FIXED** (just updated)

**PgBouncer:**
- ✅ Uses environment variables: `$NINA_DB_USER`, `$NINA_DB_PASSWORD`
- ✅ Connects to: `ninaivalaigal-dev-pgbouncer-tx` (port 6432)
- ✅ Correct mode: **Transaction** (optimal for stateless REST)

**Redis:**
- ✅ Uses environment variables: `$REDIS_URL` (with password support)

**Changes Made:**
```bash
# Line 44 - Updated to use TX mode
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}

# Lines 60-67 - Redis with password
REDIS_PASSWORD=${REDIS_PASSWORD:-}
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"
fi
```

---

### 🔍 **3. GraphOps**

**Container:** `ninaivalaigal-dev-graphops`
**Start Script:** `scripts/nv-graphops-start.sh`
**Status:** 🔍 **NEEDS REVIEW**

Let me check this one...
