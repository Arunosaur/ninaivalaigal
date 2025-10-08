# Port Compliance - Final Status
**Date**: October 7, 2025, 7:10 PM CST
**Session**: Port Matrix V2 Validation & Correction

---

## 🎯 Current Status

### ✅ Working Correctly (Do NOT Touch)
| Service | Port | Status | Notes |
|---------|------|--------|-------|
| PostgreSQL | 5452 | ✅ Perfect | Running since session start |
| PgBouncer | 6452 | ✅ **RESTORED** | Just fixed - SCRAM auth working |
| Redis | 6399 | ✅ Perfect | Running since session start |
| API | 13390 | ✅ Perfect | Connected to PgBouncer correctly |

### ❌ Needs Port Fix (UI Only)
| Service | Current Port | Should Be | Action Required |
|---------|--------------|-----------|-----------------|
| Customer UI | 8100 | 8101 | Restart with -p 8101:8101 |
| Admin Console | 8101 | 8201 | Restart with -p 8201:8102 |
| Enhanced Memory | No host port | 8301 | Restart with -p 8301:7070 |

---

## 📋 What Happened Today

### 1. Port Matrix V2 Created ✅
- **File**: `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
- **File**: `config/ports.nv.yaml`
- Added EM (Enhanced Memory) service to matrix
- Cross-validated with user's ZIP file - **Perfect match!**

### 2. PgBouncer Restored ✅
**Issue**: Accidentally deleted PgBouncer container
**Resolution**:
1. Found `nina-pgbouncer:arm64` image in Docker (built Oct 5)
2. Saved to tar and loaded into Apple Container CLI
3. Retrieved SCRAM password hash from PostgreSQL
4. Started with correct configuration using DB IP (container name resolution doesn't work)
5. Verified working with test query

**Lesson Learned**: Always backup images before deleting containers

### 3. Container Naming Clarified ✅
**Pattern**: `ninaivalaigal-{env}-{service}` (NO runtime suffix)

Examples:
- ✅ `ninaivalaigal-dev-api`
- ❌ NOT `ninaivalaigal-dev-api-apple`

---

## 🚀 Next Steps

### Immediate Action Required

Run this script to fix UI ports:
```bash
chmod +x /Users/swami/WorkSpace/ninaivalaigal/scripts/fix-ui-ports-only.sh
/Users/swami/WorkSpace/ninaivalaigal/scripts/fix-ui-ports-only.sh
```

**This script is SAFE because:**
- ✅ Only touches UI containers (customer, admin, EM)
- ✅ Does NOT touch Database
- ✅ Does NOT touch PgBouncer (just fixed!)
- ✅ Does NOT touch Redis
- ✅ Does NOT touch API

### After Fix, Verify

```bash
# Should show all 7 ports
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201|8301)"

# Expected output:
# container *:5452   (PostgreSQL)
# container *:6452   (PgBouncer)
# container *:6399   (Redis)
# container *:13390  (API)
# container *:8101   (Customer UI)
# container *:8201   (Admin Console)
# container *:8301   (Enhanced Memory)
```

---

## 📚 Documentation Created

1. **Port Matrix V2**: `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
2. **Machine Config**: `config/ports.nv.yaml`
3. **Corrections Doc**: `docs/PORT_MATRIX_CORRECTIONS.md`
4. **Enforcement System**: `docs/PORT_ENFORCEMENT_SYSTEM.md`
5. **Correction Plan**: `docs/PORT_CORRECTION_PLAN.md`
6. **Execution Guide**: `EXECUTE_PORT_FIXES.md`
7. **Fix Script**: `scripts/fix-ui-ports-only.sh`
8. **Validation Script**: `scripts/validate-ports.sh`

---

## 🔐 Critical Information to Remember

### PgBouncer Configuration
- **Image**: `nina-pgbouncer:arm64` (built Oct 5, 2025)
- **Authentication**: SCRAM-SHA-256 with password hash from pg_shadow
- **Database Connection**: Uses IP address (container name doesn't resolve)
- **Port**: 6452 (host) → 6432 (container)

### Container Network
- Containers communicate via **IP addresses**, NOT container names
- Container name DNS resolution is not working in Apple Container CLI
- Port 5432 is PostgreSQL's internal port
- Port 5452 is host-mapped port (for external access)

---

## ⚠️ Safety Protocols

### Before Deleting ANY Container:
1. ✅ Check if image exists: `docker images | grep <name>`
2. ✅ Backup if needed: `docker save <image> -o /tmp/backup.tar`
3. ✅ Verify image can be loaded back: `container image load -i /tmp/backup.tar`
4. ⚠️  ONLY THEN delete container

### Container Images We Have:
```bash
docker images | grep nina

nina-api:arm64              # API server
nina-customer-ui:arm64      # Customer-facing UI
nina-admin-console:arm64    # Internal admin UI
nina-em:arm64               # Enhanced Memory
nina-pgbouncer:arm64        # PgBouncer (critical!)
nina-intelligence-db:arm64  # PostgreSQL (if in Docker)
```

---

## 📊 Port Matrix Reference (Apple Dev)

| Service | Port | Formula | Status |
|---------|------|---------|--------|
| PostgreSQL | 5452 | 5432+0+20 | ✅ |
| PgBouncer | 6452 | 6432+0+20 | ✅ |
| Redis | 6399 | 6379+0+20 | ✅ |
| API | 13390 | 13370+0+20 | ✅ |
| UI-External | 8101 | 8081+0+20 | ❌ (currently 8100) |
| UI-Internal | 8201 | 8181+0+20 | ❌ (currently 8101) |
| EM | 8301 | 8281+0+20 | ❌ (no host port) |

**Formula**: `Final Port = Base + Environment Offset + Runtime Offset`
- Runtime Offset: +0 (Docker), +10 (Colima), +20 (Apple)
- Environment Offset: +0 (Dev), +100 (Test), +200 (Prod)

---

## ✅ Success Criteria

After running fix script, ALL of these must be true:

- [ ] Port 5452 listening (PostgreSQL)
- [ ] Port 6452 listening (PgBouncer)
- [ ] Port 6399 listening (Redis)
- [ ] Port 13390 listening (API)
- [ ] Port 8101 listening (Customer UI)
- [ ] Port 8201 listening (Admin Console)
- [ ] Port 8301 listening (Enhanced Memory)
- [ ] API health check returns `{"status":"ok"}`
- [ ] Customer UI loads (HTTP 200)
- [ ] Admin Console loads (HTTP 200)
- [ ] EM health check works (HTTP 200)
- [ ] Can connect to PgBouncer: `psql postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev`

---

## 🎓 Lessons Learned

1. **Never delete containers without image backup** - Cost us 1+ hour to restore PgBouncer
2. **Container name resolution doesn't work** - Must use IP addresses for inter-container communication
3. **SCRAM passwords are critical** - PgBouncer needs exact hash from pg_shadow
4. **Port matrix must be enforced** - Manual port assignments led to mismatches
5. **Documentation is essential** - Would have been lost without Oct 5 PgBouncer docs

---

## 📞 Support Resources

- **SPEC-086**: `specs/SPEC-086-multi-runtime-port-allocation.md`
- **PgBouncer Fix 2025**: `docs/archive/status/PGBOUNCER_FIX_2025-10-05.md`
- **Container Guide**: `docs/CONTAINER_BUILD_DEPLOYMENT_GUIDE.md`
- **Architecture**: `docs/CONTAINER_ARCHITECTURE.md`

---

**Status**: 4 of 7 services SPEC-086 compliant
**Remaining**: UI port fixes only (safe operation)
**Risk Level**: LOW (only UI containers affected)
**Estimated Time**: 2 minutes to fix

**Run `/Users/swami/WorkSpace/ninaivalaigal/scripts/fix-ui-ports-only.sh` when ready**
