# GitHub Workflow Updates - Legacy Naming Removal
**Date**: October 10, 2025
**Action**: Action 2 from LEGACY_NAMING_CLEANUP.md

---

## Files to Update

### 1. `.github/workflows/macstudio-validate-clean.yml` (ACTIVE)

**Current Issues:**
- Lines 77-83: Uses `nv-db-start.sh`, `nv-pgbouncer-start.sh`, `nv-api-start.sh`
- Line 101-104: Logs from `nv-api`, `nv-pgbouncer`, `nv-db`

**Required Changes:**

```yaml
# BEFORE (Lines 77-83)
- name: Start Stack
  run: |
    chmod +x scripts/nv-*.sh

    echo "=== Starting Database ==="
    timeout 60 ./scripts/nv-db-start.sh || { echo "DB start timed out"; exit 1; }

    echo "=== Starting PgBouncer ==="
    timeout 60 ./scripts/nv-pgbouncer-start.sh || { echo "PgBouncer start timed out"; exit 1; }

    echo "=== Starting API ==="
    timeout 60 ./scripts/nv-api-start.sh || { echo "API start timed out"; exit 1; }

# AFTER (Lines 77-83)
- name: Start Stack
  run: |
    echo "=== Starting Complete Stack ==="
    export NINA_ENV=dev
    export NINA_RUNTIME=apple
    timeout 180 ./scripts/stack-start-complete.sh || { echo "Stack start timed out"; exit 1; }
```

```yaml
# BEFORE (Lines 101-104)
for c in nv-api nv-pgbouncer nv-db; do
  echo "::group::logs $c"
  container logs "$c" || true
  echo "::endgroup::"
done

# AFTER (Lines 101-104)
for c in ninaivalaigal-dev-api ninaivalaigal-dev-pgbouncer ninaivalaigal-dev-db; do
  echo "::group::logs $c"
  container logs "$c" || true
  echo "::endgroup::"
done
```

---

### 2. `.github/workflows/dev-stack-validation.yml` (ACTIVE)

**Current Issues:**
- Lines 55-76: Creates container named `nv-db`
- Lines 154-155: Cleans up `nv-api`, `nv-pgbouncer`, `nv-db`

**Required Changes:**

```yaml
# BEFORE (Lines 55-58)
docker run -d \
  --name nv-db \
  -p 5433:5432 \
  -e POSTGRES_DB=nina \

# AFTER (Lines 55-58)
docker run -d \
  --name ninaivalaigal-dev-db \
  -p 5433:5432 \
  -e POSTGRES_DB=nina \
```

```yaml
# BEFORE (Line 65)
if docker exec nv-db pg_isready -U nina -d nina; then

# AFTER (Line 65)
if docker exec ninaivalaigal-dev-db pg_isready -U nina -d nina; then
```

```yaml
# BEFORE (Line 75)
SCRAM_PASSWORD=$(docker exec nv-db psql -U nina -d nina -t -c "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')

# AFTER (Line 75)
SCRAM_PASSWORD=$(docker exec ninaivalaigal-dev-db psql -U nina -d nina -t -c "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')
```

```yaml
# BEFORE (Line 79-84)
- name: Start PgBouncer
  run: |
    docker run -d \
      --name nv-pgbouncer \
      -p 6433:6432 \

# AFTER (Line 79-84)
- name: Start PgBouncer
  run: |
    docker run -d \
      --name ninaivalaigal-dev-pgbouncer \
      -p 6433:6432 \
```

```yaml
# BEFORE (Line 99-103)
- name: Start API
  run: |
    docker run -d \
      --name nv-api \
      -p 8001:8000 \

# AFTER (Line 99-103)
- name: Start API
  run: |
    docker run -d \
      --name ninaivalaigal-dev-api \
      -p 8001:8000 \
```

```yaml
# BEFORE (Lines 136, 143-144)
docker exec nv-db psql -U nina -d nina -c "SELECT version();"
docker logs nv-db || true
docker logs nv-pgbouncer || true

# AFTER (Lines 136, 143-144)
docker exec ninaivalaigal-dev-db psql -U nina -d nina -c "SELECT version();"
docker logs ninaivalaigal-dev-db || true
docker logs ninaivalaigal-dev-pgbouncer || true
```

```yaml
# BEFORE (Lines 153-154)
docker stop nv-api nv-pgbouncer nv-db || true
docker rm nv-api nv-pgbouncer nv-db || true

# AFTER (Lines 153-154)
docker stop ninaivalaigal-dev-api ninaivalaigal-dev-pgbouncer ninaivalaigal-dev-db || true
docker rm ninaivalaigal-dev-api ninaivalaigal-dev-pgbouncer ninaivalaigal-dev-db || true
```

---

### 3. `.github/workflows/healthcheck-restart.yml` (ACTIVE)

**Current Issues:**
- Line 295-296: Creates `nv-db-temp`
- Line 531: Removes `nv-db-temp`, `nv-redis-temp`

**Required Changes:**

```yaml
# BEFORE (Lines 295-296)
"docker run -d --name nv-db-temp --rm -p 5432:5432 -e POSTGRES_PASSWORD=${{ env.POSTGRES_PASSWORD }} -e POSTGRES_DB=foundation_test postgres:15" \
"docker exec nv-db-temp pg_isready -U postgres"

# AFTER (Lines 295-296)
"docker run -d --name ninaivalaigal-temp-db --rm -p 5432:5432 -e POSTGRES_PASSWORD=${{ env.POSTGRES_PASSWORD }} -e POSTGRES_DB=foundation_test postgres:15" \
"docker exec ninaivalaigal-temp-db pg_isready -U postgres"
```

```yaml
# BEFORE (Line 531)
docker rm -f nv-db-temp nv-redis-temp ninaivalaigal-graph-db-temp ninaivalaigal-graph-redis-temp 2>/dev/null || true

# AFTER (Line 531)
docker rm -f ninaivalaigal-temp-db ninaivalaigal-temp-redis ninaivalaigal-graph-db-temp ninaivalaigal-graph-redis-temp 2>/dev/null || true
```

---

### 4-6. Disabled Workflows (LOW PRIORITY)

These workflows are disabled but should be updated for consistency:

- `.github/workflows/macstudio-validate-specs-matrix.yml.disabled`
- `.github/workflows/macstudio-validate.yml.disabled`
- `.github/workflows/macstudio-stack-validate.yml.disabled`

**Pattern to find/replace:**
- Find: `nv-db` → Replace: `ninaivalaigal-dev-db`
- Find: `nv-pgbouncer` → Replace: `ninaivalaigal-dev-pgbouncer`
- Find: `nv-redis` → Replace: `ninaivalaigal-dev-redis`
- Find: `nv-api` → Replace: `ninaivalaigal-dev-api`
- Find: `nv-mem0` → Replace: `ninaivalaigal-dev-mem0` (if needed)

---

## Testing Changes

After updating workflows:

1. **Test locally first:**
   ```bash
   # Verify stack starts with correct names
   export NINA_ENV=dev
   export NINA_RUNTIME=apple
   ./scripts/stack-start-complete.sh

   # Verify containers exist
   container list | grep ninaivalaigal-dev
   ```

2. **Test in GitHub Actions:**
   - Push to a test branch
   - Watch workflow run
   - Verify no `nv-*` containers are created

---

## Verification Checklist

After implementing changes:

- [ ] No `nv-db` containers created by workflows
- [ ] No `nv-pgbouncer` containers created by workflows
- [ ] No `nv-api` containers created by workflows
- [ ] All workflows use `ninaivalaigal-dev-*` naming
- [ ] Stack scripts work in CI environment
- [ ] Container logs accessible with new names

---

## Implementation Priority

**High Priority (Active Workflows):**
1. `macstudio-validate-clean.yml` - Used for validation
2. `dev-stack-validation.yml` - Used for testing
3. `healthcheck-restart.yml` - Used for health monitoring

**Low Priority (Disabled):**
4. `macstudio-validate-specs-matrix.yml.disabled`
5. `macstudio-validate.yml.disabled`
6. `macstudio-stack-validate.yml.disabled`

---

## Timeline

**Estimated Time:** 30-45 minutes
- File updates: 15 minutes
- Testing locally: 10 minutes
- GitHub Actions test run: 10-20 minutes

**When to do:** Next development session after AGE database is restored.
