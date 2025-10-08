# Port Matrix Corrections - October 7, 2025

## 🔍 Issues Discovered

### 1. PgBouncer Has No Port Binding ❌

**Problem**: PgBouncer container was started WITHOUT the `-p` port flag
```json
"publishedPorts": []
```

**Impact**:
- PgBouncer port 6452 not accessible from host
- API connecting to PgBouncer via internal container IP (192.168.64.208:6432) instead of localhost:6452
- Violates SPEC-086 port matrix specification

**Root Cause**:
- Startup script didn't include `-p 6452:6432` flag
- Container runs but only accessible within container network

**Fix**:
```bash
# Old (missing -p flag)
container run -d --name ninaivalaigal-dev-pgbouncer nina-pgbouncer:arm64

# New (correct)
container run -d --name ninaivalaigal-dev-pgbouncer -p 6452:6432 nina-pgbouncer:arm64
```

---

### 2. Container Naming Misconception ❌

**Problem**: Documentation/scripts assumed runtime-specific naming
```bash
# WRONG - what we assumed
ninaivalaigal-dev-api-apple
ninaivalaigal-dev-redis-docker
ninaivalaigal-dev-ui-customer-colima
```

**Actual Pattern** (verified from running system):
```bash
# CORRECT - actual naming
ninaivalaigal-dev-db
ninaivalaigal-dev-pgbouncer
ninaivalaigal-dev-redis
ninaivalaigal-dev-api
ninaivalaigal-dev-ui-customer
ninaivalaigal-dev-ui-admin
ninaivalaigal-dev-em
```

**Key Insight**:
- Container names are **environment-scoped only**
- NO runtime suffix (-apple, -docker, -colima)
- Multiple runtimes **cannot** run simultaneously on same environment
- Runtime distinction is **port-based only**

---

### 3. UI Port Mismatches

**Current vs SPEC-086**:
| Service | Current Port | Expected Port | Status |
|---------|--------------|---------------|--------|
| Customer UI | 8100 | 8101 | ❌ Wrong |
| Admin Console | 8101 | 8201 | ❌ Wrong |
| Enhanced Memory | 7070 | 8301 | ❌ Wrong |

**Root Cause**: Manual port assignment didn't follow SPEC-086 formula

---

## ✅ Corrections Made

### 1. Updated `config/ports.nv.yaml`

```yaml
# BEFORE (incorrect)
container_names:
  api: "ninaivalaigal-{env}-api-{runtime}"
  redis: "ninaivalaigal-{env}-redis-{runtime}"

# AFTER (correct)
container_names:
  api: "ninaivalaigal-{env}-api"
  redis: "ninaivalaigal-{env}-redis"
```

### 2. Fixed `scripts/validate-ports.sh`

```bash
# BEFORE
EXPECTED_CONTAINERS=(
    "ninaivalaigal-dev-api-apple"
    "ninaivalaigal-dev-redis-apple"
)

# AFTER
EXPECTED_CONTAINERS=(
    "ninaivalaigal-${ENVIRONMENT}-api"
    "ninaivalaigal-${ENVIRONMENT}-redis"
)
```

### 3. Updated `scripts/fix-ports-spec-086.sh`

- Added PgBouncer port binding with `-p 6452:6432`
- Added PgBouncer configuration generation
- Correct container names (no runtime suffix)

### 4. Updated Documentation

- `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
- `docs/PORT_ENFORCEMENT_SYSTEM.md`

---

## 🎓 Key Learnings

### Runtime vs Environment

**Environment** (dev/test/prod):
- Determines container **names**
- Adds +0/+100/+200 to ports
- Isolates data (different volumes)

**Runtime** (docker/colima/apple):
- Determines **ports only** (+0/+10/+20)
- Does NOT affect container names
- Cannot run multiple runtimes on same environment

### Correct Mental Model

```
Container Name = ninaivalaigal-{environment}-{service}
Port = Base + Environment_Offset + Runtime_Offset

Example:
  Name: ninaivalaigal-dev-api (same for all runtimes!)
  Docker Port: 13370 + 0 + 0 = 13370
  Colima Port: 13370 + 0 + 10 = 13380
  Apple Port: 13370 + 0 + 20 = 13390
```

### Simultaneous Runtime Limitations

**Cannot do this** (same environment):
```bash
# ❌ This will conflict (same container names)
docker run ... --name ninaivalaigal-dev-api -p 13370:8000
colima ... --name ninaivalaigal-dev-api -p 13380:8000  # Name collision!
```

**Can do this** (different environments):
```bash
# ✅ This works (different environments = different names)
docker run ... --name ninaivalaigal-dev-api -p 13370:8000
colima ... --name ninaivalaigal-test-api -p 13480:8000
apple ... --name ninaivalaigal-prod-api -p 13590:8000
```

---

## 📋 Action Items

### Immediate (Before Next Startup)

- [ ] Run `./scripts/fix-ports-spec-086.sh` to correct all ports
- [ ] Verify PgBouncer has port binding: `lsof -nP -iTCP:6452 -sTCP:LISTEN`
- [ ] Test API connects via localhost:6452 (not container IP)

### Short-term (This Week)

- [ ] Update all startup scripts to use correct container names
- [ ] Add port validation to pre-startup checks
- [ ] Document runtime limitations clearly
- [ ] Update SPEC-086 with clarified naming convention

### Long-term (Ongoing)

- [ ] Add automated port validation to CI/CD
- [ ] Create pre-commit hook for port validation
- [ ] Monitor for port drift in production
- [ ] Regular audits against SPEC-086

---

## 🔗 Related Files Modified

- ✅ `config/ports.nv.yaml` - Container name patterns corrected
- ✅ `scripts/validate-ports.sh` - Container name validation fixed
- ✅ `scripts/fix-ports-spec-086.sh` - PgBouncer port binding added
- ✅ `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md` - Naming convention clarified
- ✅ `docs/PORT_ENFORCEMENT_SYSTEM.md` - Updated with correct patterns

---

## 🎯 Verification Commands

```bash
# 1. Check container names (no runtime suffix)
container list | grep ninaivalaigal
# Should show: ninaivalaigal-dev-api, ninaivalaigal-dev-redis, etc.
# NOT: ninaivalaigal-dev-api-apple

# 2. Check PgBouncer has port binding
lsof -nP -iTCP:6452 -sTCP:LISTEN
# Should show: container *:6452

# 3. Check all expected ports
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201|8301)"

# 4. Run automated validation
./scripts/validate-ports.sh apple dev
```

---

## 📊 Before vs After

### Before

```
Running Containers:
- ninaivalaigal-dev-db ✅
- ninaivalaigal-dev-pgbouncer ⚠️ (no port binding)
- ninaivalaigal-dev-redis ✅
- ninaivalaigal-dev-api ✅
- ninaivalaigal-dev-ui-customer ❌ (wrong port 8100)
- ninaivalaigal-dev-ui-admin ❌ (wrong port 8101)
- ninaivalaigal-dev-em ❌ (wrong port 7070)

Listening Ports:
- 5452 ✅ PostgreSQL
- 6452 ❌ PgBouncer NOT listening
- 6399 ✅ Redis
- 13390 ✅ API
- 8100 ❌ Wrong (should be 8101)
- 8101 ❌ Wrong (should be 8201)
- 7070 ❌ Wrong (should be 8301)
```

### After (Target)

```
Running Containers:
- ninaivalaigal-dev-db ✅
- ninaivalaigal-dev-pgbouncer ✅ (port binding added)
- ninaivalaigal-dev-redis ✅
- ninaivalaigal-dev-api ✅
- ninaivalaigal-dev-ui-customer ✅ (corrected to 8101)
- ninaivalaigal-dev-ui-admin ✅ (corrected to 8201)
- ninaivalaigal-dev-em ✅ (corrected to 8301)

Listening Ports:
- 5452 ✅ PostgreSQL
- 6452 ✅ PgBouncer (NEW!)
- 6399 ✅ Redis
- 13390 ✅ API
- 8101 ✅ Customer UI (CORRECTED)
- 8201 ✅ Admin Console (CORRECTED)
- 8301 ✅ Enhanced Memory (CORRECTED)
```

---

**Status**: Corrections identified and scripts updated ✅
**Next Step**: Run fix script to apply corrections to live system
**Priority**: 🔴 High - Required for SPEC-086 compliance
