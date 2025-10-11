# API Container Rebuild - Current Status
**Date**: October 10, 2025, 14:11 CST
**Session**: API Container Rebuild After Cleanup

---

## ❌ CRITICAL ISSUES IDENTIFIED

### 1. Naming Standard Violations
**CORRECT STANDARD**: `ninaivalaigal-{env}-{service}` (e.g., `ninaivalaigal-dev-db`)
**SOURCE**: PORT_COMPLIANCE_FINAL_STATUS.md

**Current Violations:**
- ❌ `nv-db` - should be `ninaivalaigal-dev-db`
- ❌ `nv-redis` - should be `ninaivalaigal-dev-redis` (but one exists correctly)
- ❌ `nv-api` - should be `ninaivalaigal-dev-api` (but one exists correctly)

### 2. Database Container Issues
**PROBLEM**: Using wrong database container without AGE extension

**Current State:**
- `nv-db` (pgvector/pgvector:pg15) - Running
  - ✅ Has pgvector extension
  - ❌ Missing Apache AGE extension

**Required State:**
- `ninaivalaigal-dev-db` with `nina-intelligence-db:arm64` image
  - ✅ Must have pgvector extension
  - ✅ Must have Apache AGE extension
  - Dockerfile: `/scripts/consolidation/Dockerfile.nv-db-age`

**Stopped Containers Found:**
- `nina-intelligence-db` - STOPPED
- `test-consolidated-db` (nina-intelligence-db:arm64) - STOPPED

### 3. API Container Status
- ✅ `ninaivalaigal-dev-api` - RUNNING (correct name)
- ✅ Built with latest code (import errors fixed)
- ❌ Health endpoint returning Internal Server Error
- ❌ Connected to wrong database (`nv-db` instead of proper `ninaivalaigal-dev-db`)

### 4. PgBouncer Container Status
- ✅ `ninaivalaigal-dev-pgbouncer` - RUNNING (correct name)
- ✅ Using custom `nina-pgbouncer:arm64` image
- ✅ SCRAM-SHA-256 authentication working
- ❌ Pointed at wrong database (nv-db IP: 192.168.64.79)

---

## 📊 Current Container Inventory

### Running (Correctly Named)
```
ninaivalaigal-dev-api          - 192.168.64.94   ✅ Correct naming
ninaivalaigal-dev-pgbouncer    - 192.168.64.92   ✅ Correct naming
ninaivalaigal-dev-redis        - 192.168.64.189  ✅ Correct naming
ninaivalaigal-dev-ui-admin     - 192.168.64.73   ✅ Correct naming
ninaivalaigal-dev-ui-customer  - 192.168.64.72   ✅ Correct naming
ninaivalaigal-dev-em           - 192.168.64.74   ✅ Correct naming
```

### Running (Incorrect/Legacy Names)
```
nv-db                          - 192.168.64.79   ❌ Should be ninaivalaigal-dev-db
nv-redis                       - 192.168.64.80   ❌ Duplicate, should be removed
```

### Stopped (Should Be Running)
```
nina-intelligence-db           - STOPPED         ❌ Should be running as ninaivalaigal-dev-db
test-consolidated-db           - STOPPED         ❌ Test container
```

### Stopped (Should Be Removed)
```
nv-api                         - STOPPED         ❌ Legacy name
ninaivalaigal-dev-api-apple    - STOPPED         ❌ Old with -apple suffix
Kaikeyi, Sumitra, Kausalya, Seetha               ❌ Test containers
```

---

## 🎯 REQUIRED ACTIONS (In Order)

### Phase 1: Rebuild Proper Database
1. **Build nina-intelligence-db:arm64 with AGE + pgvector**
   ```bash
   cd /Users/swami/WorkSpace/ninaivalaigal/scripts/consolidation
   docker build -t nina-intelligence-db:arm64 -f Dockerfile.nv-db-age .
   ```

2. **Stop and remove nv-db (wrong database)**
   ```bash
   container stop nv-db
   container delete nv-db
   ```

3. **Start ninaivalaigal-dev-db with correct image**
   ```bash
   container run -d --name ninaivalaigal-dev-db \
     -p 5452:5432 \
     -e POSTGRES_DB=nina \
     -e POSTGRES_USER=nina \
     -e POSTGRES_PASSWORD=change_me_securely \
     nina-intelligence-db:arm64
   ```

4. **Verify extensions**
   ```bash
   container exec ninaivalaigal-dev-db psql -U nina -d nina -c "\dx"
   # Should show: age, vector, plpgsql
   ```

### Phase 2: Reconnect PgBouncer
1. **Get new database IP**
   ```bash
   DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   ```

2. **Get SCRAM hash from new database**
   ```bash
   SCRAM_HASH=$(container exec ninaivalaigal-dev-db psql -U nina -d nina -At -c "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';")
   ```

3. **Restart PgBouncer with correct database**
   ```bash
   container rm -f ninaivalaigal-dev-pgbouncer
   container run -d --name ninaivalaigal-dev-pgbouncer -p 6452:6432 \
     -e DB_HOST="$DB_IP" \
     -e SCRAM_PASSWORD="$SCRAM_HASH" \
     nina-pgbouncer:arm64
   ```

### Phase 3: Reconnect API
1. **Get PgBouncer and Redis IPs**
   ```bash
   PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   ```

2. **Restart API with correct connections**
   ```bash
   container rm -f ninaivalaigal-dev-api
   container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
     -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
     -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
     -e REDIS_HOST="$REDIS_IP" \
     -e REDIS_PORT="6379" \
     -e REDIS_PASSWORD="nina_redis_dev_password" \  # pragma: allowlist secret
     -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
     -e PYTHONPATH="/app:/app/server" \
     nina-api:arm64
   ```

3. **Verify API health**
   ```bash
   curl http://localhost:13390/health
   ```

### Phase 4: Cleanup Legacy Containers
```bash
# Remove legacy nv-* containers
container stop nv-redis && container delete nv-redis
container delete nv-api

# Remove test/old containers
container delete ninaivalaigal-dev-api-apple
container delete nina-intelligence-db
container delete test-consolidated-db
container delete Kaikeyi Sumitra Kausalya Seetha

# Remove stopped nina-intelligence-cache if exists
container delete nina-intelligence-cache 2>/dev/null || true
```

---

## 📝 What Went Wrong This Session

1. **Import Error Fixed**: Changed relative import in `standalone_teams.py` ✅
2. **Image Built**: New API image built with fix ✅
3. **Image Loaded**: Loaded into Apple Container CLI ✅
4. **Wrong Database**: Connected API to `nv-db` (missing AGE) instead of proper database ❌
5. **PgBouncer Issues**: Had to recreate PgBouncer multiple times ❌
6. **Naming Confusion**: Mixed legacy `nv-*` names with correct `ninaivalaigal-dev-*` names ❌

---

## 🔒 PREVENT FUTURE REGRESSIONS

### 1. Always Use Correct Naming
- **Database**: `ninaivalaigal-dev-db` (NOT `nv-db`)
- **PgBouncer**: `ninaivalaigal-dev-pgbouncer` (NOT `nv-pgbouncer`)
- **Pattern**: `ninaivalaigal-{env}-{service}`

### 2. Always Verify Database Extensions
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "\dx"
# Must show: age, vector, plpgsql
```

### 3. Never Use Direct Database Connection
- **Always** use PgBouncer
- **Never** connect API directly to database

### 4. Document Container Backups
- Need to create backup .tar files of all working containers
- Store in `/Users/swami/ninaivalaigal/backups/`
- Tag working images in Docker registry

---

## ✅ Success Criteria

- [ ] `ninaivalaigal-dev-db` running with AGE + pgvector
- [ ] `ninaivalaigal-dev-pgbouncer` connected to correct database
- [ ] `ninaivalaigal-dev-api` connected through PgBouncer
- [ ] API health endpoint returning 200 OK
- [ ] No legacy `nv-*` containers running
- [ ] All stopped test containers removed

---

**Next Steps**: Execute Phase 1-4 actions in order, validating each phase before proceeding.
