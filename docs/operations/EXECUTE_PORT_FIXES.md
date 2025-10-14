# Execute Port Fixes - IMMEDIATE ACTION REQUIRED

**Date**: October 7, 2025
**Status**: 🔴 Ready to Execute
**Estimated Time**: 5 minutes

---

## 🎯 What This Will Fix

1. ✅ Add PgBouncer port binding (6452) - **CRITICAL**
2. ✅ Move Customer UI from 8100 → 8101
3. ✅ Move Admin Console from 8101 → 8201
4. ✅ Move Enhanced Memory from 7070 → 8301
5. ✅ Update API to use correct PgBouncer connection
6. ✅ Verify all ports match SPEC-086

---

## 📋 Pre-Flight Checklist

Before running the fix script, verify these files exist:

```bash
# 1. Check scripts are present
ls -la /Users/swami/WorkSpace/ninaivalaigal/scripts/fix-ports-spec-086.sh
ls -la /Users/swami/WorkSpace/ninaivalaigal/scripts/validate-ports.sh

# 2. Make executable
chmod +x /Users/swami/WorkSpace/ninaivalaigal/scripts/*.sh

# 3. Verify your containers are running
container list | grep ninaivalaigal
```

---

## 🚀 Execution Steps

### Step 1: Run the Fix Script

```bash
cd /Users/swami/WorkSpace/ninaivalaigal
./scripts/fix-ports-spec-086.sh
```

**What it does**:
- Stops and recreates PgBouncer with `-p 6452:6432`
- Stops and recreates API with updated PgBouncer connection
- Stops and recreates Customer UI on port 8101
- Stops and recreates Admin Console on port 8201
- Waits for all services to stabilize
- Runs health checks

**Expected output**:
```
╔══════════════════════════════════════════════════════════════════════╗
║          SPEC-086 Port Correction - Apple CLI Dev                   ║
╚══════════════════════════════════════════════════════════════════════╝

Database IP: 192.168.64.188
Redis IP: 192.168.64.189

=== 1. Fixing PgBouncer Port (ADD port binding) ===
Note: PgBouncer was running WITHOUT -p flag (no port exposed to host)
✅ PgBouncer now on port 6452 (host) → 6432 (container)

=== 2. Updating API with Correct PgBouncer Connection ===
✅ API restarted with correct PgBouncer connection

=== 3. Fixing Customer UI Port: 8100 → 8101 ===
✅ Customer UI now on port 8101

=== 4. Fixing Admin Console Port: 8101 → 8201 ===
✅ Admin Console now on port 8201

=== Waiting for services to start (10 seconds) ===

╔══════════════════════════════════════════════════════════════════════╗
║          SPEC-086 Compliance Verification                            ║
╚══════════════════════════════════════════════════════════════════════╝

=== Port Bindings (SPEC-086 Apple Dev) ===
Expected Ports: 5452, 6452, 6399, 13390, 8101, 8201

container *:5452
container *:6452
container *:6399
container *:13390
container *:8101
container *:8201

=== Service Health Checks ===
API Health: {"status":"ok"}
Customer UI: HTTP 200
Admin Console: HTTP 200

✅ SPEC-086 Compliance Complete!
```

### Step 2: Validate the Fix

```bash
./scripts/validate-ports.sh apple dev
```

**Expected result**: All checks should PASS

---

## 🔍 Verification Commands

After running the fix, verify manually:

```bash
# 1. Check all ports are listening
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201)" | awk '{print $1, $9}' | sort -u

# Expected output:
# container *:5452
# container *:6452   ← NEW!
# container *:6399
# container *:13390
# container *:8101   ← MOVED!
# container *:8201   ← MOVED!

# 2. Test PgBouncer connection
psql "postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev" -c "SELECT 1;"

# Expected: Should connect successfully

# 3. Test API
curl http://localhost:13390/health

# Expected: {"status":"ok"}

# 4. Test Customer UI
curl -I http://localhost:8101/

# Expected: HTTP/1.1 200 OK

# 5. Test Admin Console
curl -I http://localhost:8201/

# Expected: HTTP/1.1 200 OK
```

---

## 📊 Updated Service URLs

After the fix, use these URLs:

```bash
# Database & Cache
postgresql://localhost:5452              # Direct PostgreSQL
postgresql://localhost:6452              # PgBouncer (use this!)
redis://localhost:6399                   # Redis

# API
http://localhost:13390                   # API root
http://localhost:13390/health            # Health check
http://localhost:13390/docs              # Swagger UI

# User Interfaces
http://localhost:8101                    # Customer UI (External)
http://localhost:8201                    # Admin Console (Internal)
http://localhost:8301                    # Enhanced Memory (if running)
```

---

## 🔧 If Something Goes Wrong

### PgBouncer Won't Start

```bash
# Check if config file was created
ls -la /tmp/pgbouncer.ini

# Check PgBouncer logs
container logs ninaivalaigal-dev-pgbouncer

# Try starting manually
container stop ninaivalaigal-dev-pgbouncer
container delete ninaivalaigal-dev-pgbouncer
container run -d --name ninaivalaigal-dev-pgbouncer -p 6452:6432 nina-pgbouncer:arm64
```

### API Won't Connect to PgBouncer

```bash
# Get PgBouncer IP
PGBOUNCER_IP=$(container list | grep pgbouncer | awk '{print $4}')
echo "PgBouncer IP: $PGBOUNCER_IP"

# Verify PgBouncer is accessible from API container
container exec ninaivalaigal-dev-api ping -c 3 $PGBOUNCER_IP

# Check if PgBouncer is listening inside container
container exec ninaivalaigal-dev-pgbouncer netstat -tlnp | grep 6432
```

### UI Containers Won't Start

```bash
# Check if ports are already in use
lsof -nP -iTCP:8101 -sTCP:LISTEN
lsof -nP -iTCP:8201 -sTCP:LISTEN

# If in use, find what's using them
ps aux | grep <PID>

# Force kill if needed
kill -9 <PID>
```

---

## 🎓 What Changed

### Before
```
ninaivalaigal-dev-pgbouncer: Running but NO port binding ❌
API → PgBouncer: Via container IP (192.168.64.208:6432)
Customer UI: Port 8100 (wrong)
Admin Console: Port 8101 (wrong)
```

### After
```
ninaivalaigal-dev-pgbouncer: Running with -p 6452:6432 ✅
API → PgBouncer: Via localhost:6452 (correct!)
Customer UI: Port 8101 ✅
Admin Console: Port 8201 ✅
```

---

## 📝 Post-Fix Actions

Once all ports are corrected:

1. **Update your bookmarks**:
   - Customer UI: http://localhost:8101
   - Admin Console: http://localhost:8201

2. **Update any scripts/configs** that hardcode old ports

3. **Test end-to-end**:
   - Login to Customer UI
   - Login to Admin Console
   - Create a test memory via API
   - Verify data persists

4. **Document success**:
   - Take screenshot of working stack
   - Note any issues encountered
   - Update team wiki/docs

---

## ✅ Success Criteria

All these should be TRUE after running the fix:

- [ ] Port 6452 is listening (PgBouncer)
- [ ] Port 8101 is listening (Customer UI)
- [ ] Port 8201 is listening (Admin Console)
- [ ] API health check returns `{"status":"ok"}`
- [ ] Customer UI loads without errors
- [ ] Admin Console loads without errors
- [ ] PgBouncer shows active connections
- [ ] No port collision warnings
- [ ] `./scripts/validate-ports.sh` passes with 0 failures

---

## 🚨 Emergency Rollback

If the fix breaks something critical:

```bash
# Stop everything
container stop ninaivalaigal-dev-api
container stop ninaivalaigal-dev-pgbouncer
container stop ninaivalaigal-dev-ui-customer
container stop ninaivalaigal-dev-ui-admin

# Start services one by one with original settings
# (Refer to original startup commands before the fix)

# Or use the unified stack script
./scripts/nina-intelligence-stack-start-unified.sh
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `container logs <container-name> 2>&1 | tail -50`
2. Check the corrections doc: `docs/PORT_MATRIX_CORRECTIONS.md`
3. Verify against canonical matrix: `docs/network/NINAIVALAIGAL_PORT_MATRIX_V2.md`
4. Review troubleshooting: `docs/CONTAINER_BUILD_DEPLOYMENT_GUIDE.md`

---

**Ready to Execute**: YES ✅
**Risk Level**: Low (only port changes, no data affected)
**Rollback Available**: YES
**Estimated Downtime**: ~2 minutes

🚀 **Run the fix script now to achieve SPEC-086 compliance!**
