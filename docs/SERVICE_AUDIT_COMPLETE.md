# Complete Service Connection Audit

**Date:** October 20, 2025, 10:15 PM
**Auditor:** Developer C
**Scope:** All ninaivalaigal services - PgBouncer & Redis connections

---

## 📊 Executive Summary

| Status | Count | Services |
|--------|-------|----------|
| ✅ Compliant | 2 | memory-service, core-api |
| ❌ Needs Fix | 2 | graphops, stack-start-complete.sh |
| ⚠️ No DB Access | 4 | jaeger, load-tester, em, grpc-gateway |
| 🔍 Unknown | 4 | business-service, graph-service, admin-vendor, customer |

---

## ✅ COMPLIANT SERVICES

### **1. Memory Service (Rust/SQLx)**
**Container:** `ninaivalaigal-dev-memory-service`
**Script:** `rust-services/memory-service/nv-memory-service-start.sh`
**Status:** ✅ **PERFECT**

**PgBouncer:**
- ✅ Uses: `$NINA_DB_USER`, `$NINA_DB_PASSWORD` from `.env.dev`
- ✅ Connects to: `ninaivalaigal-dev-pgbouncer-sess` (port 6433)
- ✅ Mode: Session (correct for SQLx prepared statements)

**Redis:**
- ✅ Uses: `$REDIS_URL` with password support

---

### **2. Core API (Python FastAPI)**
**Container:** `ninaivalaigal-dev-core-api`
**Script:** `services/core-api/nv-core-api-start.sh`
**Status:** ✅ **FIXED** (just updated)

**PgBouncer:**
- ✅ Uses: `$NINA_DB_USER`, `$NINA_DB_PASSWORD` from `.env.dev`
- ✅ Connects to: `ninaivalaigal-dev-pgbouncer-tx` (port 6432)
- ✅ Mode: Transaction (correct for stateless REST)

**Redis:**
- ✅ Uses: `$REDIS_URL` with password support

---

## ❌ CRITICAL ISSUES FOUND

### **3. GraphOps (Cypher Queries)**
**Container:** `ninaivalaigal-dev-graphops`
**Script:** `scripts/nv-graphops-start.sh`
**Status:** ❌ **CRITICAL - HARDCODED CREDENTIALS**

**Problems:**
1. **Line 33:** Looking for old single `ninaivalaigal-dev-pgbouncer`
   ```bash
   PGBOUNCER_IP=$(container list | grep ninaivalaigal-dev-pgbouncer | awk '{print $6}')
   ```
   ❌ Should use: `ninaivalaigal-dev-pgbouncer-tx`

2. **Line 44:** **HARDCODED credentials in code!**
   ```bash
   DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"
   ```
   ❌ Should use: `$NINA_DB_USER`, `$NINA_DB_PASSWORD` from `.env.dev`

3. No Redis connection (might not need it)

**Fix Required:**
```bash
# Load environment
source "$PROJECT_ROOT/.env.dev"

# Use TX mode for stateless Cypher queries
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV:-dev}-pgbouncer-tx}
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Use environment variables
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV:-dev}"
```

---

### **4. Stack Start Complete Script**
**Script:** `scripts/stack-start-complete.sh`
**Status:** ❌ **OUTDATED - REFERENCES OLD PGBOUNCER**

**Problems:**
1. **Line 29:** References old single PgBouncer
   ```bash
   readonly PGBOUNCER_CONTAINER="ninaivalaigal-${ENV}-pgbouncer"
   ```
   ❌ Doesn't exist anymore (replaced with dual PgBouncer)

2. **Line 263:** API connects to old PgBouncer
   ```bash
   local database_url="postgresql://${DB_USER}:${DB_PASSWORD}@${pgbouncer_ip}:6432/${DB_NAME}"
   ```
   ⚠️ Works but references old container name

**Impact:**
- This script will fail when trying to start the stack
- Says "PgBouncer not found" because looking for wrong container

**Fix Required:**
```bash
# Line 29 - Use TX mode as default for API/UI services
readonly PGBOUNCER_TX_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-tx"
readonly PGBOUNCER_SESS_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-sess"

# Line 256 - Get TX mode IP for API
local pgbouncer_ip=$(get_container_ip "$PGBOUNCER_TX_CONTAINER")
```

---

## ⚠️ SERVICES WITHOUT DATABASE ACCESS

### **5. Jaeger (Observability)**
**Container:** `ninaivalaigal-dev-jaeger`
**Status:** ℹ️ **N/A - Doesn't need DB/Redis**

Jaeger is for distributed tracing. No database or Redis connection needed.

---

### **6. Load Tester**
**Container:** `ninaivalaigal-dev-load-tester`
**Status:** ℹ️ **N/A - Testing tool**

Load testing tool, doesn't connect directly to DB.

---

### **7. Enhanced Memory (EM)**
**Container:** `ninaivalaigal-dev-em`
**Status:** ℹ️ **Unknown - Need to investigate**

Started via `fix-ui-ports-only.sh` line 54:
```bash
container run -d --name ninaivalaigal-dev-em -p 8301:7070 nina-em:arm64
```

No environment variables passed. Need to check if it connects to DB/Redis internally.

---

### **8. gRPC Gateway**
**Container:** `ninaivalaigal-dev-grpc-gateway`
**Status:** ℹ️ **N/A - Gateway routing only**

Gateway for gRPC traffic. Doesn't connect to DB directly.

---

## 🔍 SERVICES NEEDING INVESTIGATION

### **9. Business Service**
**Container:** `ninaivalaigal-dev-business-service`
**Status:** 🔍 **UNKNOWN**

**Action Required:**
- Find start script or Dockerfile
- Check if uses PgBouncer
- Should use **transaction mode** (stateless business logic)

---

### **10. Graph Service**
**Container:** `ninaivalaigal-dev-graph-service`
**Status:** 🔍 **UNKNOWN**

**Action Required:**
- Find start script or Dockerfile
- Check if uses PgBouncer
- Likely needs **session mode** if using prepared statements

---

### **11. Admin Vendor UI**
**Container:** `ninaivalaigal-dev-admin-vendor`
**Status:** 🔍 **UNKNOWN**

**Action Required:**
- Frontend application
- Probably doesn't connect to DB directly (uses API)
- Check Redis for session storage

---

### **12. Customer UI**
**Container:** `ninaivalaigal-dev-customer`
**Status:** 🔍 **NOT RUNNING** (not in container list)

**Action Required:**
- Check if supposed to be running
- Frontend application
- Probably doesn't connect to DB directly

---

## 🎯 IMMEDIATE ACTION ITEMS

### **Priority 1: Fix Critical Security Issues**
1. **GraphOps:** Remove hardcoded credentials (Line 44)
2. **GraphOps:** Update to use environment variables
3. **GraphOps:** Connect to `pgbouncer-tx` instead of old single PgBouncer

### **Priority 2: Fix Stack Start Script**
1. **stack-start-complete.sh:** Update to use dual PgBouncer
2. Add `PGBOUNCER_TX_CONTAINER` and `PGBOUNCER_SESS_CONTAINER`
3. Update all PgBouncer references

### **Priority 3: Investigate Unknown Services**
1. Find start scripts for: business-service, graph-service
2. Check their database connections
3. Route to appropriate PgBouncer mode

---

## 📝 Recommended Fixes

### **Fix GraphOps Start Script:**
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load centralized environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    source "$PROJECT_ROOT/.env.dev"
else
    echo "❌ .env.dev not found"
    exit 1
fi

# Use environment variables
NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-graphops"
IMAGE_NAME="ninaivalaigal-graphops:arm64"

# Task #85: Use PgBouncer TRANSACTION mode for GraphOps
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    echo "❌ PgBouncer-TX not found"
    echo "   Start it first: ./scripts/nv-pgbouncer-tx-start.sh"
    exit 1
fi

# Build DATABASE_URL from environment variables
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"

# ... rest of script
```

### **Fix Stack Start Complete:**
```bash
# Line 29 - Update container names
readonly PGBOUNCER_TX_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-tx"
readonly PGBOUNCER_SESS_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-sess"

# Line 256 - Use TX mode for API (stateless)
local pgbouncer_ip=$(get_container_ip "$PGBOUNCER_TX_CONTAINER")
```

---

## ✅ Success Criteria

- [ ] All services use environment variables (no hardcoded credentials)
- [ ] Stateless services connect to `pgbouncer-tx` (port 6432)
- [ ] Services with prepared statements connect to `pgbouncer-sess` (port 6433)
- [ ] All services use `$REDIS_URL` with password from `.env.dev`
- [ ] No references to old single `ninaivalaigal-dev-pgbouncer`
- [ ] All start scripts source `.env.dev`

---

## 📊 Summary Stats

| Category | Count |
|----------|-------|
| **Total Services** | 12 |
| **Compliant** | 2 (17%) |
| **Need Fixes** | 2 (17%) |
| **No DB Access** | 4 (33%) |
| **Unknown** | 4 (33%) |

**Critical Issues:** 2 (GraphOps hardcoded creds, stack script outdated)
**Estimated Fix Time:** 2-3 hours
**Risk Level:** 🔴 High (hardcoded credentials in production code)

---

**Next Steps:**
1. Fix GraphOps immediately (security issue)
2. Update stack-start-complete.sh
3. Investigate unknown services
4. Test all connections end-to-end

**Generated:** October 20, 2025, 10:20 PM
**Developer C ready to implement fixes**
