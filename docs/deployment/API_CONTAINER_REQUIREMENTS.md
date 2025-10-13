# API Container Requirements & Connection Architecture

**Document Version:** 1.0
**Last Updated:** October 12, 2025
**Related SPECs:** SPEC-086 (Multi-Runtime Port Allocation)

---

## 🎯 Overview

This document defines the **mandatory requirements** for running the Ninaivalaigal API container, including database connection architecture, dynamic IP resolution, and Redis configuration.

---

## 🔒 Critical Architecture Rules

### **1. PgBouncer Mandate - ALL Database Connections**

**✅ REQUIRED:** All database connections from the API **MUST** go through PgBouncer.

```
API Container → PgBouncer (port 6432) → PostgreSQL (port 5432)
```

**❌ FORBIDDEN:** Direct database connections from API containers.

**Rationale:**
- Connection pooling and resource efficiency
- Transaction-mode connection management
- Protection against connection exhaustion
- Consistent connection handling across environments

---

## 🌐 Dynamic IP Resolution

### **Container IP Detection**

All container IPs are **dynamically resolved** at runtime using:

```bash
# Correct IP extraction (column 6)
get_container_ip() {
    local container_name=$1
    container list | grep "$container_name" | awk '{print $6}'
}

# Example usage
PGBOUNCER_IP=$(get_container_ip "ninaivalaigal-dev-pgbouncer")
REDIS_IP=$(get_container_ip "ninaivalaigal-dev-redis")
DB_IP=$(get_container_ip "ninaivalaigal-dev-db")
```

**⚠️ Common Bug:** Using `awk '{print $(NF)}'` extracts the **last field** ("MB" from memory column), not the IP address!

### **Why Dynamic IPs?**

- Apple Container CLI assigns IPs dynamically on container start
- IPs change between container restarts
- No DNS resolution between containers (must use IPs)
- Enables true container isolation and portability

---

## 📦 API Container Creation Requirements

### **Required Environment Variables**

```bash
# 1. DATABASE CONNECTION (via PgBouncer)
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${PGBOUNCER_IP}:6432/${DB_NAME}"
NINAIVALAIGAL_DATABASE_URL="${DATABASE_URL}"  # Fallback

# 2. REDIS CONNECTION
REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"
NINAIVALAIGAL_REDIS_URL="${REDIS_URL}"  # Fallback

# Optional individual Redis settings
REDIS_HOST="${REDIS_IP}"
REDIS_PORT=6379
REDIS_PASSWORD="${REDIS_PASSWORD}"

# 3. APPLICATION SETTINGS
NINAIVALAIGAL_JWT_SECRET="${JWT_SECRET}"
NINA_ENV="${ENV}"  # dev/test/prod

# 4. PYTHON PATH
PYTHONPATH=/app:/app/server
```

### **Complete Container Run Command**

```bash
# 1. Dynamically resolve container IPs
PGBOUNCER_IP=$(container list | grep "ninaivalaigal-${ENV}-pgbouncer" | awk '{print $6}')
REDIS_IP=$(container list | grep "ninaivalaigal-${ENV}-redis" | awk '{print $6}')

# 2. Construct connection URLs
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${PGBOUNCER_IP}:6432/${DB_NAME}"
REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"

# 3. Start API container with SPEC-086 compliant name
container run -d --name "ninaivalaigal-${ENV}-api" \
    -p "${API_PORT}:8000" \
    -e DATABASE_URL="${DATABASE_URL}" \
    -e NINAIVALAIGAL_DATABASE_URL="${DATABASE_URL}" \
    -e REDIS_URL="${REDIS_URL}" \
    -e NINAIVALAIGAL_REDIS_URL="${REDIS_URL}" \
    -e REDIS_HOST="${REDIS_IP}" \
    -e REDIS_PORT=6379 \
    -e REDIS_PASSWORD="${REDIS_PASSWORD}" \
    -e NINAIVALAIGAL_JWT_SECRET="${JWT_SECRET}" \
    -e NINA_ENV="${ENV}" \
    -e PYTHONPATH=/app:/app/server \
    nina-api:arm64
```

---

## 🔴 Redis Connection Requirements

### **Authentication**

Redis **ALWAYS requires authentication** in all environments:

```bash
# Get the actual Redis password from container config
container inspect ninaivalaigal-dev-redis | grep requirepass

# Common passwords by environment:
# - dev:  nina_redis_dev_password
# - test: nina_redis_test_password
# - prod: (from secrets management)
```

### **Connection URL Format**

```bash
# URL format with password authentication
redis://:${PASSWORD}@${HOST}:${PORT}/${DB}

# Example
redis://:nina_redis_dev_password@192.168.64.105:6379/0
```

### **Testing Redis Connection**

```bash
# Get Redis IP
REDIS_IP=$(container list | grep "ninaivalaigal-dev-redis" | awk '{print $6}')

# Test with correct password
redis-cli -h ${REDIS_IP} -p 6379 -a "nina_redis_dev_password" PING
# Expected: PONG

# Common error: WRONGPASS invalid username-password pair
# Solution: Check actual password from container inspect
```

---

## 🚨 Common Errors & Solutions

### **Error 1: "Rate limiting error: Name or service not known"**

**Cause:** Using hostname `redis:6379` instead of IP address

**Solution:**
```bash
# ❌ WRONG: Using hostname
REDIS_URL="redis://redis:6379"

# ✅ CORRECT: Using dynamic IP
REDIS_IP=$(container list | grep "ninaivalaigal-dev-redis" | awk '{print $6}')
REDIS_URL="redis://:${PASSWORD}@${REDIS_IP}:6379/0"
```

### **Error 2: "invalid username-password pair or user is disabled"**

**Cause:** Wrong Redis password

**Solution:**
```bash
# Get actual password from container
container inspect ninaivalaigal-dev-redis | grep requirepass

# Use correct password in REDIS_URL
REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"
```

### **Error 3: API connects directly to database**

**Cause:** `DATABASE_URL` points to DB port instead of PgBouncer

**Solution:**
```bash
# ❌ WRONG: Direct DB connection (port 5432)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/ninaivalaigal_dev"

# ✅ CORRECT: Through PgBouncer (port 6432)
DATABASE_URL="postgresql://nina:password@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"
```

### **Error 4: Container IP shows as "MB"**

**Cause:** Using `$(NF)` in awk which gets last field (memory column)

**Solution:**
```bash
# ❌ WRONG: Gets "MB" from memory column
awk '{print $(NF)}'

# ✅ CORRECT: Gets IP from column 6
awk '{print $6}'
```

---

## 📋 Pre-Start Checklist

Before starting the API container, verify:

- [ ] ✅ Database container is running
- [ ] ✅ PgBouncer container is running and can connect to DB
- [ ] ✅ Redis container is running with authentication enabled
- [ ] ✅ Dynamic IP resolution function is correct (`awk '{print $6}'`)
- [ ] ✅ `DATABASE_URL` points to PgBouncer (port 6432), NOT direct DB
- [ ] ✅ `REDIS_URL` includes correct password and dynamic IP
- [ ] ✅ Container name follows SPEC-086: `ninaivalaigal-${ENV}-api` (NO runtime suffix!)

---

## 🔍 Validation Commands

### **1. Verify PgBouncer Connection**

```bash
PGBOUNCER_PORT=6452  # Adjust for your environment

PGPASSWORD="${DB_PASSWORD}" psql \
    -h localhost \
    -p ${PGBOUNCER_PORT} \
    -U nina \
    -d ninaivalaigal_dev \
    -c "SELECT 'PgBouncer → DB: CONNECTED ✅' AS status, version();"
```

### **2. Verify Redis Connection**

```bash
REDIS_IP=$(container list | grep "ninaivalaigal-dev-redis" | awk '{print $6}')
redis-cli -h ${REDIS_IP} -p 6379 -a "nina_redis_dev_password" PING
# Expected: PONG
```

### **3. Verify API Health**

```bash
curl -s http://localhost:${API_PORT}/health | jq .
# Expected: {"status": "ok"}
```

### **4. Verify Connection Architecture**

```bash
# Check API environment variables
container exec ninaivalaigal-dev-api env | grep -E "DATABASE_URL|REDIS_URL"

# Verify PgBouncer IP is in DATABASE_URL (port 6432)
# Verify Redis IP is in REDIS_URL with password
```

---

## 🏗️ Container Naming (SPEC-086)

**✅ CORRECT Container Names:**
```
ninaivalaigal-dev-db
ninaivalaigal-dev-pgbouncer
ninaivalaigal-dev-redis
ninaivalaigal-dev-api
ninaivalaigal-dev-customer-app
ninaivalaigal-dev-admin-console
```

**❌ WRONG Container Names (DO NOT USE):**
```
ninaivalaigal-dev-db-apple        # Runtime suffix violates SPEC-086
ninaivalaigal-dev-api-docker      # Runtime suffix violates SPEC-086
nv-api                            # Old naming convention
```

**Reference:** See `specs/086-multi-runtime-port-allocation/README.md` lines 232-263

---

## 📚 Related Documentation

- **SPEC-086:** Multi-Runtime Port Allocation & Network Architecture
- **Container Builds:** `how-to/container-builds/README.md`
- **Stack Startup Script:** `scripts/stack-start-complete.sh`
- **Archived Violations:** `scripts/archive/spec-086-violations-2025-10-12/`

---

## 🔧 Troubleshooting Workflow

1. **Check container status:**
   ```bash
   container list | grep ninaivalaigal-dev
   ```

2. **Verify IPs are correctly resolved:**
   ```bash
   container list | grep "ninaivalaigal-dev-pgbouncer" | awk '{print $6}'
   ```

3. **Check API logs for connection errors:**
   ```bash
   container logs ninaivalaigal-dev-api 2>&1 | tail -50
   ```

4. **Validate PgBouncer → DB connection:**
   ```bash
   PGPASSWORD="${DB_PASSWORD}" psql -h localhost -p 6452 -U nina -d ninaivalaigal_dev -c "SELECT 1;"
   ```

5. **Validate Redis authentication:**
   ```bash
   redis-cli -h ${REDIS_IP} -p 6379 -a "${REDIS_PASSWORD}" PING
   ```

---

## ✅ Success Criteria

API container is correctly configured when:

1. ✅ Container is running: `container list | grep ninaivalaigal-dev-api`
2. ✅ Health endpoint responds: `curl http://localhost:13390/health` → `{"status": "ok"}`
3. ✅ Database connection goes through PgBouncer (port 6432 in DATABASE_URL)
4. ✅ Redis connection works with correct password and dynamic IP
5. ✅ Container name follows SPEC-086 (no runtime suffix)
6. ✅ All environment variables are set correctly
7. ✅ No errors in API logs: `container logs ninaivalaigal-dev-api`

---

**Last Verified:** October 12, 2025
**Stack Version:** Complete Stack v2.0.0
**Compliance:** SPEC-086 ✅
