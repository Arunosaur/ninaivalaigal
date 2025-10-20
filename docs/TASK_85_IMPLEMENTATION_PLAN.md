# Task #85: Fix PgBouncer Bypass - Implementation Plan

**Developer:** Developer C
**Start Date:** October 20, 2025, 6:16 PM
**Priority:** 🔴 P0 - ARCHITECTURAL BLOCKER
**Deadline:** Week 2 (November 3, 2025)

---

## 🔍 Root Cause Analysis - CONFIRMED

### **The Problem:**
Memory Service (Rust/SQLx) **intentionally bypasses PgBouncer** and connects directly to PostgreSQL on port 5432.

**Evidence:**
```bash
# From: rust-services/memory-service/nv-memory-service-start.sh:46-58
# Resolve Database IP (bypass PgBouncer for Rust/SQLx compatibility)
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/ninaivalaigal_${NINA_ENV}"
```

**Why it bypasses:**
- SQLx uses **prepared statements** (confirmed in `storage.rs`: `sqlx::query_as` with `$1`, `$2` parameters)
- PgBouncer in **transaction mode** doesn't support prepared statements
- Comment says: "bypassing PgBouncer for SQLx compatibility"

**Impact:**
- ❌ Breaks connection pooling architecture
- ❌ Memory Service creates its own connections (max 8)
- ❌ Blocks service decomposition (violates architecture)
- ❌ Can't scale properly

---

## ✅ Solution: Switch PgBouncer to Session Mode

### **What is Session Mode?**
- **Transaction mode:** One server connection per transaction (fast, but no prepared statements)
- **Session mode:** One server connection per client connection (slower, but supports prepared statements)

### **Trade-offs:**
| Feature | Transaction Mode | Session Mode |
|---------|------------------|--------------|
| Connection reuse | ✅ Excellent | ⚠️ Good |
| Prepared statements | ❌ No | ✅ Yes |
| SQLx/Rust compatibility | ❌ No | ✅ Yes |
| Performance | ✅ Best | ⚠️ Good |

**Decision:** Session mode is the **only option** that supports SQLx prepared statements.

---

## 📋 Implementation Steps

### **Step 1: Update PgBouncer Configuration** ⏳

**File:** `containers/pgbouncer/Dockerfile`

**Current (Line 23):**
```dockerfile
&& echo 'pool_mode = transaction' >> /etc/pgbouncer/pgbouncer.ini.template \
```

**Change to:**
```dockerfile
&& echo 'pool_mode = session' >> /etc/pgbouncer/pgbouncer.ini.template \
```

**Also update duplicate (Line 15):**
```dockerfile
&& echo '* = host=${DB_HOST} port=5432 pool_mode=transaction' >> /etc/pgbouncer/pgbouncer.ini.template \
```

**Change to:**
```dockerfile
&& echo '* = host=${DB_HOST} port=5432 pool_mode=session' >> /etc/pgbouncer/pgbouncer.ini.template \
```

---

### **Step 2: Update Memory Service to Use PgBouncer** ⏳

**File:** `rust-services/memory-service/nv-memory-service-start.sh`

**Current (Lines 46-58):**
```bash
# Resolve Database IP (bypass PgBouncer for Rust/SQLx compatibility)
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/ninaivalaigal_${NINA_ENV}"
```

**Change to:**
```bash
# Use PgBouncer (now in session mode, supports prepared statements)
PGBOUNCER_CONTAINER="ninaivalaigal-${NINA_ENV}-pgbouncer"
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    echo "❌ Unable to find PgBouncer container ($PGBOUNCER_CONTAINER)."
    echo "   Please ensure PgBouncer is running."
    exit 1
fi
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"
echo "   Database: $PGBOUNCER_IP:6432 (via PgBouncer - session mode)"
```

---

### **Step 3: Rebuild and Test** ⏳

**3a. Rebuild PgBouncer:**
```bash
cd /Users/swami/WorkSpace/ninaivalaigal
docker build -t nina-pgbouncer:latest containers/pgbouncer/
```

**3b. Restart PgBouncer in Apple Container CLI:**
```bash
# Stop existing
container stop ninaivalaigal-dev-pgbouncer
container rm ninaivalaigal-dev-pgbouncer

# Export and load updated image
docker save -o /tmp/pgbouncer.tar nina-pgbouncer:latest
container image load -i /tmp/pgbouncer.tar
rm /tmp/pgbouncer.tar

# Start with session mode
./scripts/nv-pgbouncer-start.sh  # Or equivalent script
```

**3c. Verify PgBouncer Config:**
```bash
container exec ninaivalaigal-dev-pgbouncer cat /etc/pgbouncer/pgbouncer.ini | grep pool_mode
# Expected: pool_mode = session
```

---

### **Step 4: Test Memory Service with PgBouncer** ⏳

**4a. Stop existing Memory Service:**
```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service
./nv-memory-service-stop.sh
```

**4b. Start with updated script:**
```bash
./nv-memory-service-start.sh
```

**4c. Check logs for PgBouncer connection:**
```bash
container logs ninaivalaigal-dev-memory-service | grep -i "database\|connection"
# Should show connection to port 6432, not 5432
```

**4d. Test prepared statements work:**
```bash
# Create a memory
curl -X POST http://localhost:13393/memories \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test memory","context_id":"00000000-0000-0000-0000-000000000000"}'

# Fetch memories
curl http://localhost:13393/memories \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### **Step 5: Verify Connection Pooling** ⏳

**5a. Check PgBouncer stats:**
```bash
container exec ninaivalaigal-dev-pgbouncer psql -p 6432 -U nina -d pgbouncer -c "SHOW POOLS;"
```

**Expected output:**
```
 database  | user | cl_active | cl_waiting | sv_active | sv_idle | sv_used | ...
-----------+------+-----------+------------+-----------+---------+---------+-----
 ninaival... | nina |     8    |     0      |     8     |    0    |    0    | ...
```

**5b. Verify no direct connections to port 5432:**
```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT count(*) FROM pg_stat_activity WHERE application_name = 'memory-service';"
# Should be 0 (all connections via PgBouncer now)
```

---

### **Step 6: Integration Tests** ⏳

**6a. Run Memory Service health check:**
```bash
curl http://localhost:13393/health
# Expected: {"status":"healthy"}
```

**6b. Load test with concurrent requests:**
```bash
# Use Task #72 load tester
for i in {1..100}; do
  curl -X POST http://localhost:13393/memories \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"content\":\"Test $i\",\"context_id\":\"00000000-0000-0000-0000-000000000000\"}" &
done
wait

# Check PgBouncer handled connections
container exec ninaivalaigal-dev-pgbouncer psql -p 6432 -U nina -d pgbouncer -c "SHOW STATS;"
```

---

### **Step 7: Documentation** ⏳

**Update files:**
- ✅ `docs/TASK_85_PGBOUNCER_PREPARED_STATEMENTS.md` - Already exists
- 🆕 `docs/TASK_85_IMPLEMENTATION_PLAN.md` - This file
- 🆕 `docs/TASK_85_TEST_RESULTS.md` - Create after testing
- 📝 Update `docs/SPEC_099_100_GAP_ANALYSIS_OCT20.md` - Mark Task #85 complete

---

## 📊 Success Criteria

- [  ] PgBouncer running in session mode
- [  ] Memory Service connects to port 6432 (PgBouncer)
- [  ] Prepared statements work correctly
- [  ] Connection pooling operational
- [  ] No direct connections to port 5432
- [  ] All health checks passing
- [  ] Load test successful (100+ concurrent requests)
- [  ] Documentation updated

---

## ⏱️ Timeline

**Total Estimate:** 2-3 weeks

| Phase | Duration | Status |
|-------|----------|--------|
| Investigation | 2 hours | ✅ Complete |
| PgBouncer config change | 1 hour | ⏳ Next |
| Memory Service update | 2 hours | ⏳ Pending |
| Testing & validation | 1 week | ⏳ Pending |
| Load testing | 3 days | ⏳ Pending |
| Documentation | 2 days | ⏳ Pending |

**Start:** October 20, 2025, 6:16 PM
**Expected Completion:** November 3, 2025

---

## 🚨 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Session mode slower than transaction mode | Medium | Monitor performance, optimize pool size |
| Existing services break | High | Test each service individually |
| Connection limit exceeded | Medium | Tune max_client_conn and default_pool_size |

---

## 📝 Notes

- This is a **breaking change** - all services using PgBouncer must be restarted
- Session mode uses more server connections than transaction mode
- May need to increase PostgreSQL `max_connections` setting
- Monitor PgBouncer stats after rollout

---

**Status:** IN PROGRESS - Developer C
**Next Step:** Update PgBouncer Dockerfile (Step 1)
