# Zombie Containers Issue - RESOLVED

**Date:** Oct 16, 2025 @ 3:11 PM  
**Issue:** Old `nv-*` containers kept reappearing despite cleanup  
**Status:** ✅ FIXED

---

## 🐛 Root Cause

**Two health check scripts were auto-starting old containers:**

1. **`scripts/comprehensive-health-monitor.sh`**
   - Lines 94-124: Checked for `nv-db`, `nv-redis`, `nv-pgbouncer`, `nv-api`, `nv-ui`
   - Automatically restarted them if not found
   - Ran every 5 minutes (300s interval)

2. **`scripts/runtime-aware-health-check.sh`**
   - Line 55: Grep pattern included old container names
   - `grep -E 'nv-db|nv-api|nv-redis|nv-pgbouncer'`

---

## ✅ Fix Applied

### Updated `scripts/comprehensive-health-monitor.sh`:
```bash
# OLD (Lines 94-124):
if ! container list | grep -q "nv-db.*running"; then
    safe_container_restart "nv-db" "nv-db-start.sh"
fi

# NEW:
if ! container list | grep -q "ninaivalaigal-dev-db.*running"; then
    log "⚠️ Database (ninaivalaigal-dev-db) not running"
    log "   Manual start required: ./start-apple-container-stack.sh"
fi
```

**Changes:**
- ✅ Updated all container names to `ninaivalaigal-dev-*` pattern
- ✅ Removed auto-restart of old containers
- ✅ Changed to monitoring-only mode (no auto-fix)
- ✅ Added deprecation warnings for old containers

### Updated `scripts/runtime-aware-health-check.sh`:
```bash
# OLD (Line 55):
CONTAINER_LIST_CMD="container list | grep -E 'nv-db|nv-api|nv-redis|nv-pgbouncer'"

# NEW:
CONTAINER_LIST_CMD="container list | grep -E 'ninaivalaigal-dev'"
```

---

## 🧹 Cleanup Actions

```bash
# Stopped old containers
container stop nv-db

# Removed old containers
container rm nv-db
# (nv-redis, nv-pgbouncer, nv-api, nv-ui didn't exist)
```

---

## ✅ Current Status

**Only correct containers running:**
```
ninaivalaigal-dev-db           ✅ Running
ninaivalaigal-dev-pgbouncer    ✅ Running
ninaivalaigal-dev-redis        ✅ Running
ninaivalaigal-dev-core-api     ✅ Running
ninaivalaigal-dev-em           ✅ Running
ninaivalaigal-dev-ui-admin     ✅ Running
ninaivalaigal-dev-ui-customer  ✅ Running
```

**No `nv-*` containers present!** 🎉

---

## 📋 What Was Fixed

| File | Issue | Fix |
|------|-------|-----|
| `scripts/comprehensive-health-monitor.sh` | Auto-restarted `nv-db`, `nv-redis`, etc. | Changed to monitor `ninaivalaigal-dev-*` only |
| `scripts/runtime-aware-health-check.sh` | Grep pattern included old names | Updated to `ninaivalaigal-dev` pattern |
| Running containers | `nv-db` was running | Stopped and removed |

---

## 🚀 Going Forward

**Old containers will NOT restart because:**
1. ✅ Health monitors updated to new names
2. ✅ Old start scripts archived (`scripts/archive/legacy-nv-scripts-2025-10-10/`)
3. ✅ No cron jobs or launchd services found
4. ✅ Old containers removed from system

**If `nv-*` containers appear again:**
```bash
# Check for running health monitors
ps aux | grep -E "comprehensive-health|runtime-aware" | grep -v grep

# Check cron
crontab -l | grep nina

# Check launchd
launchctl list | grep nina

# Stop and remove immediately
container stop nv-db nv-redis nv-pgbouncer nv-api nv-ui
container rm nv-db nv-redis nv-pgbouncer nv-api nv-ui
```

---

## 📝 Files Modified

- [x] `scripts/comprehensive-health-monitor.sh` - Updated container names, disabled auto-restart
- [x] `scripts/runtime-aware-health-check.sh` - Fixed grep pattern
- [x] `enable-pgvector.sh` - New script for Developer B

---

**The zombie containers are DEAD and will stay dead!** 💀🎉
