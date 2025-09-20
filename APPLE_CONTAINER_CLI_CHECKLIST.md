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

#### **Networking Issues - IN PROGRESS**:
**Attempts Made**:
1. **❌ host.docker.internal**: DNS lookup failed
   - Evidence: Logs show "DNS lookup failed: host.docker.internal"
2. **❌ host.lima.internal**: DNS lookup failed  
   - Evidence: Logs show "DNS lookup failed: host.lima.internal"
3. **❌ 127.0.0.1**: Connection failed
   - Evidence: Logs show "connect failed" to 127.0.0.1:5433
4. **❌ localhost**: Resolves to 127.0.0.1, same issue
   - Evidence: Logs show connection attempts to 127.0.0.1
5. **🔄 nv-db:5432**: Container-to-container (CURRENT ATTEMPT)
   - Status: Just implemented, not yet tested

**Key Discovery**: Original working setup used **localhost** but containers can't reach host via 127.0.0.1 in Apple Container CLI

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

### **If Current Approach Fails**:
Consider **simplified workflow approach** from user's analysis:
- Direct container commands without complex networking
- Minimal configuration for CI validation
- Focus on proving Apple Container CLI viability

---

## 📊 **EVIDENCE SUMMARY**

### **Successful Commits**:
- `20f47e1`: Self-contained PgBouncer (eliminated build issues)
- `8732bc4`: Added JWT_SECRET (eliminated API startup issue)  
- `28aecec`: Fixed DATABASE_URL variable name (eliminated API config issue)
- `af6daff`: Container-to-container networking (current test)

### **Failed Approaches**:
- Host networking attempts (host.docker.internal, host.lima.internal, 127.0.0.1, localhost)
- External config files (COPY errors)
- MD5 authentication complexity

### **Workflow Evidence**:
- **10+ failed runs** with systematic debugging
- **Each failure provided specific error messages** for targeted fixes
- **Progressive improvement**: Build → Auth → Environment → Networking

**This checklist ensures we don't repeat failed approaches and build on proven successes!** 🎯
