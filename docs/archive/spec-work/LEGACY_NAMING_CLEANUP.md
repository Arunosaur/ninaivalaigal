# Legacy Naming Cleanup Plan
**Date**: October 10, 2025
**Issue**: Old `nv-*` container names still referenced throughout codebase

---

## Current Naming Standard (CORRECT)
Pattern: `ninaivalaigal-{env}-{service}`

**Required Containers:**
- `ninaivalaigal-dev-db` (NOT `nv-db`)
- `ninaivalaigal-dev-redis` (NOT `nv-redis`)
- `ninaivalaigal-dev-pgbouncer` (NOT `nv-pgbouncer`)
- `ninaivalaigal-dev-api` (NOT `nv-api`)
- `ninaivalaigal-dev-em`
- `ninaivalaigal-dev-ui-admin`
- `ninaivalaigal-dev-ui-customer`

**Source**: PORT_COMPLIANCE_FINAL_STATUS.md

---

## Files to Update

### GitHub Workflows (6 files)
1. `.github/workflows/macstudio-validate-clean.yml` - Uses `nv-db`, `nv-pgbouncer`, `nv-api`
2. `.github/workflows/dev-stack-validation.yml` - Creates `nv-db` container
3. `.github/workflows/healthcheck-restart.yml` - References `nv-db-temp`
4. `.github/workflows/macstudio-validate-specs-matrix.yml.disabled`
5. `.github/workflows/macstudio-validate.yml.disabled`
6. `.github/workflows/macstudio-stack-validate.yml.disabled`

### Scripts to DELETE (Legacy nv-* scripts - 50+ files)
```bash
scripts/nv-db-start.sh
scripts/nv-db-stop.sh
scripts/nv-db-status.sh
scripts/nv-redis-start.sh
scripts/nv-pgbouncer-start.sh
scripts/nv-pgbouncer-stop.sh
scripts/nv-api-start.sh
scripts/nv-api-stop.sh
scripts/nv-api-diagnose-repair-*.sh
scripts/nv-stack-start.sh
scripts/nv-stack-stop.sh
scripts/nv-stack-status.sh
scripts/nv-test-db.sh
```

### Scripts to UPDATE (Reference nv-*)
```bash
scripts/bring-up-dev.sh
scripts/capture-working-state.sh
scripts/nina-intelligence-health-monitor.sh
scripts/consolidation/*.sh (multiple files)
```

---

## Correct Stack Scripts

**Should be using:**
- `scripts/stack-start.sh` or `scripts/stack-start-complete.sh`
- `scripts/stack-stop.sh`
- `scripts/stack-status.sh`

These use the correct `ninaivalaigal-dev-*` naming from `scripts/common/config-loader.sh`.

---

## Recommended Actions

### Phase 1: Stop Using Legacy Scripts
1. **Remove all `nv-*` scripts from scripts/ directory**
   ```bash
   cd /Users/swami/WorkSpace/ninaivalaigal/scripts
   rm -f nv-*.sh
   ```

2. **Archive them if needed**
   ```bash
   mkdir -p archive/legacy-nv-scripts
   mv nv-*.sh archive/legacy-nv-scripts/
   ```

### Phase 2: Update GitHub Workflows
1. Update `.github/workflows/macstudio-validate-clean.yml`:
   - Replace `nv-db-start.sh` → Use proper stack-start.sh
   - Replace `nv-pgbouncer-start.sh` → Integrated in stack-start.sh
   - Replace `nv-api-start.sh` → Integrated in stack-start.sh
   - Replace container names: `nv-db` → `ninaivalaigal-dev-db`

2. Update `.github/workflows/dev-stack-validation.yml`:
   - Replace `--name nv-db` → `--name ninaivalaigal-dev-db`
   - Replace `nv-pgbouncer` → `ninaivalaigal-dev-pgbouncer`
   - Replace `nv-api` → `ninaivalaigal-dev-api`

### Phase 3: Update Makefile
Check if Makefile has targets calling `nv-*` scripts:
```bash
grep -n "nv-" Makefile
```

### Phase 4: Clean Up Running Containers
```bash
# Stop and remove legacy named containers
container stop nv-db nv-redis nv-api nv-pgbouncer 2>/dev/null || true
container delete nv-db nv-redis nv-api nv-pgbouncer 2>/dev/null || true

# Verify only correct naming remains
container list | grep ninaivalaigal-dev
```

---

## Why This Matters

1. **GitHub Actions keep creating `nv-db`** - This is why you keep seeing it
2. **Scripts conflict** - Multiple scripts trying to manage different container names
3. **Documentation mismatch** - Docs say `ninaivalaigal-dev-*` but scripts use `nv-*`
4. **Debugging confusion** - Hard to know which container has what data

---

## Current Container State

### RUNNING (Correct Naming)
```
✅ ninaivalaigal-dev-api
✅ ninaivalaigal-dev-pgbouncer
✅ ninaivalaigal-dev-redis
✅ ninaivalaigal-dev-em
✅ ninaivalaigal-dev-ui-admin
✅ ninaivalaigal-dev-ui-customer
```

### RUNNING (Incorrect - Legacy)
```
❌ nv-db (basic pgvector) - Should be stopped/removed
❌ nv-redis - Duplicate of ninaivalaigal-dev-redis
```

### STOPPED (Has AGE + pgvector data)
```
⚠️ test-consolidated-db (nina-intelligence-db:arm64)
⚠️ nina-intelligence-db (nina-intelligence-db:arm64)
```

---

## Immediate Next Steps

1. **Rename one of the stopped containers with AGE to correct name**
2. **Delete all `nv-*` legacy scripts**
3. **Update GitHub workflows to use correct naming**
4. **Stop and remove legacy `nv-db` and `nv-redis` containers**

This will prevent the legacy naming from ever coming back.
