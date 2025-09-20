# Apple Container CLI Stack Checklist

**Purpose**: Prevent going in circles by tracking what worked and what didn't work for each stack component.

## 📋 **BEFORE GitHub Workflow Action (Original Working Stack)**

### ✅ **Database (nv-db)**
**Status**: ✅ **WORKING** (Confirmed in APPLE_CONTAINER_CLI_STATUS_REPORT.md)
- **What Worked**:
  - PostgreSQL 15.14 + pgvector
  - Port mapping: 5433 (host) → 5432 (container)
  - Credentials: `nina/change_me_securely`
  - Custom scripts with Apple Container CLI syntax
  - Health checks and readiness detection
- **Evidence**: Status report shows "✔ DB: nv-db running"

### ✅ **PgBouncer (nv-pgbouncer)**  
**Status**: ✅ **WORKING** (Confirmed in status report)
- **What Worked**:
  - Custom ARM64 image (nina-pgbouncer:arm64)
  - Dynamic config generation in scripts
  - Connected to database via `localhost:5433`
  - MD5 authentication with proper hash generation
  - Port mapping: 6433 (host) → 6432 (container)
- **Evidence**: Status report shows "✔ PgB: nv-pgbouncer running"
- **Key Insight**: Used **localhost** networking, not host.lima.internal

### 🔧 **API (nina-api:arm64)**
**Status**: 🔧 **95% COMPLETE** (Built but minor config needed)
- **What Worked**:
  - Custom ARM64 image built successfully
  - All Python dependencies resolved
  - Security imports fixed
- **What Didn't Work**:
  - Database connection configuration (easily fixable)
- **Evidence**: Status report shows "🔧 API: nina-api:arm64 built"

---

## 🔄 **WITH GitHub Workflow Action (Current Debugging)**

### ✅ **Database (nv-db)**
**Status**: ✅ **CONSISTENTLY WORKING**
- **✅ What Works**:
  - Container starts successfully every time
  - PostgreSQL ready to accept connections
  - Port 5433 accessible
  - Credentials: `postgres/test123` (aligned across stack)
- **Evidence**: All workflow logs show database ready

### 🔄 **PgBouncer (nv-pgbouncer)**
**Status**: 🔄 **PARTIALLY WORKING** (Container starts, networking issues)

#### **Build Issues - RESOLVED**:
- **❌ What Failed**: COPY pgbouncer.ini/userlist.txt (files not found)
- **✅ What Fixed It**: Self-contained Dockerfile with baked-in config
- **Evidence**: Commit 20f47e1 "implement self-contained PgBouncer"

#### **Authentication Issues - RESOLVED**:
- **❌ What Failed**: MD5 hash complexity, root user warnings
- **✅ What Fixed It**: `auth_type=any`, non-root pgbouncer user
- **Evidence**: PgBouncer logs show stats (container running)

#### **Networking Issues - ROOT CAUSE IDENTIFIED**:
**❌ All Previous Attempts Failed**:
1. **❌ host.docker.internal**: DNS lookup failed
   - Evidence: Logs show "DNS lookup failed: host.docker.internal"
2. **❌ host.lima.internal**: DNS lookup failed  
   - Evidence: Logs show "DNS lookup failed: host.lima.internal"
3. **❌ 127.0.0.1**: Connection failed
   - Evidence: Logs show "connect failed" to 127.0.0.1:5433
4. **❌ localhost**: Resolves to 127.0.0.1, same issue
   - Evidence: Logs show connection attempts to 127.0.0.1
5. **❌ nv-db:5432**: Container name resolution issues
   - Evidence: Still connection failures
6. **❌ Dynamic IP approach**: Template substitution failed
   - Evidence: Latest run still shows API trying 127.0.0.1:6432

**🎯 ROOT CAUSE DISCOVERED**:
- **API container trying to reach PgBouncer at 127.0.0.1:6432**
- **Inside container, 127.0.0.1 = API container itself, NOT PgBouncer**
- **Need API to use PgBouncer's container IP, not localhost**

**✅ COMPLETE SOLUTION PROVIDED BY USER**:
- **PgBouncer**: Use DB container IP (dynamic detection working)
- **API**: Must use PgBouncer container IP, not 127.0.0.1
- **Implementation**: Get PGB_IP dynamically, pass to API as NINAIVALAIGAL_DATABASE_URL

### 🔄 **API (nv-api)**
**Status**: 🔄 **ENVIRONMENT ISSUES RESOLVED, NETWORKING PENDING**

#### **Environment Variable Issues - RESOLVED**:
1. **❌ Missing JWT_SECRET**: "NINAIVALAIGAL_JWT_SECRET environment variable is required"
   - **✅ Fixed**: Added NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci"
   - Evidence: Commit 8732bc4
2. **❌ Wrong DATABASE_URL variable**: API expects NINAIVALAIGAL_DATABASE_URL
   - **✅ Fixed**: Changed DATABASE_URL → NINAIVALAIGAL_DATABASE_URL  
   - Evidence: Commit 28aecec

#### **Networking Issues - IN PROGRESS**:
- **❌ Current Issue**: API can't connect to PgBouncer at 127.0.0.1:6432
- **Root Cause**: Same Apple Container CLI networking limitation
- **Status**: Depends on PgBouncer networking fix

---

## 🎯 **CURRENT STATUS & NEXT STEPS**

### **What We Know Works**:
1. ✅ **Self-contained PgBouncer approach** (eliminates build issues)
2. ✅ **auth_type=any** (eliminates authentication complexity)
3. ✅ **Correct environment variables** for API
4. ✅ **Database always works** (PostgreSQL + pgvector)

### **What We're Testing**:
1. 🔄 **Container-to-container networking** (nv-db:5432 for PgBouncer)
2. 🔄 **Complete stack connectivity** (DB → PgBouncer → API)

### **Key Insights**:
1. **Original working setup used localhost** - but this doesn't work in GitHub Actions
2. **Apple Container CLI networking** requires container-to-container communication
3. **Self-contained approach** eliminates all build/config issues
4. **Environment variable alignment** is critical for API

### **Success Criteria**:
- [ ] PgBouncer connects to nv-db container (no more "bouncer config error")
- [ ] API connects to PgBouncer via container networking
- [ ] All health checks pass
- [ ] Complete green workflow

### **🎯 FINAL SOLUTION (User-Provided)**:

**Complete Container-to-Container Implementation:**

```bash
# 1) DB - Get container IP
DB_IP="$(container inspect nv-db --format '{{ .NetworkSettings.IPAddress }}')"

# 2) PgBouncer - Use DB container IP (WORKING)
container run -d --name nv-pgbouncer -p 6432:6432 \
  -e DB_HOST="$DB_IP" nina-pgbouncer:arm64

# 3) API - Use PgBouncer container IP (NOT 127.0.0.1)
PGB_IP="$(container inspect nv-pgbouncer --format '{{ .NetworkSettings.IPAddress }}')"
NINAIVALAIGAL_DATABASE_URL="postgresql://postgres:test123@${PGB_IP}:6432/testdb"

container run -d --name nv-api -p 13370:8000 \
  -e NINAIVALAIGAL_DATABASE_URL="$NINAIVALAIGAL_DATABASE_URL" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \
  nina-api:arm64
```

**Why This Works:**
- ✅ **No localhost anywhere** between containers
- ✅ **API connects to PgBouncer's container IP**, not 127.0.0.1
- ✅ **PgBouncer connects to DB's container IP** (already working)
- ✅ **Ports still published to host** (5433, 6432, 13370) for human checks

**Key Insight**: `127.0.0.1` inside container = container itself, not host or other containers

### **Debugging Commands**:
```bash
# Check container IPs
container exec nv-api sh -c "python -c 'import socket; print(socket.gethostbyname(\"localhost\"))'"
container exec nv-pgbouncer sh -c "nc -zv ${DB_IP} 5432"
container exec nv-api sh -c "nc -zv ${PGB_IP} 6432"

# Always dump logs on failure
container logs nv-pgbouncer
container logs nv-db  
container logs nv-api
```

---

## 📊 **EVIDENCE SUMMARY**

### **Successful Commits**:
- `20f47e1`: Self-contained PgBouncer (eliminated build issues)
- `8732bc4`: Added JWT_SECRET (eliminated API startup issue)  
- `28aecec`: Fixed DATABASE_URL variable name (eliminated API config issue)
- `96c3db5`: Dynamic container IP networking (PgBouncer working)
- `32ef2f9`: Template substitution with envsubst (PgBouncer connects to DB)

### **Latest Status (Run 17883737905) - STILL FAILING**:
- ✅ **PgBouncer**: Successfully connecting to DB via container IP
- ❌ **API**: STILL trying 127.0.0.1:6432 despite our changes
- 🎯 **Root Cause**: API script changes not taking effect - hardcoded localhost in workflow

### **CRITICAL DISCOVERY**:
**Our API script changes are being ignored!** The workflow is still using the old approach.
**Evidence**: API logs show "connection to server at 127.0.0.1, port 6432 failed"

### **🎯 NEW ROOT CAUSE FOUND (Run 17883873413)**:
**Problem**: `container inspect nv-pgbouncer` failing, falling back to 127.0.0.1
**Evidence**: `[api] PgBouncer IP: 127.0.0.1` (should be container IP like 192.168.65.3)
**Real Issue**: Container IP detection not working in Apple Container CLI

### **CONTAINER INSPECT FAILING**:
1. ❌ **PgBouncer container inspect returns nothing** 
2. ❌ **Falls back to 127.0.0.1** (our fallback value)
3. ❌ **API tries to connect to 127.0.0.1:6432** (container itself, not PgBouncer)
4. ❌ **Connection refused** (no service on API container port 6432)

### **🚨 APPLE CONTAINER CLI COMPATIBILITY ISSUE FOUND**:
**Problem**: Used Docker `--format` flag which Apple Container CLI doesn't support
**Evidence**: `Error: Unknown option '--format'` in workflow logs
**Root Cause**: Apple Container CLI uses different syntax than Docker

### **✅ FIXED WITH JQ PARSING**:
- ❌ `container inspect --format '{{ .NetworkSettings.IPAddress }}'` (Docker syntax)
- ✅ `container inspect nv-pgbouncer | jq -r '.[0].NetworkSettings.IPAddress'` (Apple CLI)
- ✅ Added container status check before IP extraction
- ✅ Apple Container CLI compatible commands throughout

### **Failed Approaches**:
- Host networking attempts (host.docker.internal, host.lima.internal, 127.0.0.1, localhost)
- External config files (COPY errors)
- MD5 authentication complexity

### **Workflow Evidence**:
- **10+ failed runs** with systematic debugging
- **Each failure provided specific error messages** for targeted fixes
- **Progressive improvement**: Build → Auth → Environment → Networking

**This checklist ensures we don't repeat failed approaches and build on proven successes!** 🎯
