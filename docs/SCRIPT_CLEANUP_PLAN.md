# Script Cleanup Plan

## Current Situation (Too Many Stack Scripts!)

We have **7 different stack start scripts**. This needs consolidation.

## Apple Container CLI Scripts

### ✅ KEEP - Primary Scripts
1. **`start-apple-container-stack.sh`** (root) - 70 lines
   - Purpose: Simple Apple Container CLI stack startup
   - Uses: `nv-db`, `nv-pgbouncer`, `nv-api` naming
   - Status: **CANONICAL - Use this for Apple Container CLI**

### 🔄 REVIEW - Legacy Scripts
2. **`scripts/nv-stack-start.sh`** - 118 lines
   - Purpose: Original Apple Container CLI stack
   - May be older version of above
   - Action: Compare with `start-apple-container-stack.sh`, merge if needed, then remove

3. **`scripts/nina-intelligence-stack-start.sh`** - 183 lines
   - Purpose: Intelligence stack (graph database)
   - Different from main stack
   - Action: **KEEP** if it's for graph/intelligence features

4. **`scripts/nina-intelligence-stack-start-unified.sh`** - 196 lines
   - Purpose: Unified intelligence stack?
   - Action: Verify if different from above, remove if duplicate

### ❌ REMOVE - Docker-based Scripts
5. **`scripts/stack-start.sh`** - 312 lines
   - Purpose: Docker-based stack
   - We're using Apple Container CLI, not Docker
   - Action: **REMOVE** (use docker-compose for Docker instead)

6. **`scripts/stack-start-unified.sh`** - 354 lines
   - Purpose: Another Docker unified stack
   - Action: **REMOVE** (duplicate)

7. **`scripts/stack-start-complete.sh`** - 455 lines
   - Purpose: Yet another Docker stack variant
   - Action: **REMOVE** (duplicate)

## Recommendation: Clean Architecture

### For Apple Container CLI (What we want):
```bash
# Single entry point
./start-apple-container-stack.sh

# Or via Makefile
make apple-stack-up    # Should call start-apple-container-stack.sh
```

### For Docker (Fallback):
```bash
# Use docker-compose, not custom scripts
make docker-dev-up     # Uses compose.docker.yml
```

### For Intelligence/Graph:
```bash
# If separate stack needed
./scripts/nina-intelligence-stack-start.sh
```

## Action Items

1. ✅ Remove `scripts/apple-stack-up.sh` (just created duplicate)
2. ⬜ Update Makefile `apple-dev-up` to call `start-apple-container-stack.sh`
3. ⬜ Remove Docker-based stack scripts (stack-start*.sh)
4. ⬜ Verify intelligence stack scripts are still needed
5. ⬜ Document final architecture

## Final Structure (Proposed)

```
Root:
  start-apple-container-stack.sh    # Apple Container CLI main stack

scripts/:
  nv-db-start.sh                    # Individual service scripts
  nv-pgbouncer-start.sh
  nv-api-start.sh
  nina-intelligence-stack-start.sh  # Separate intelligence stack (if needed)

  # Remove these:
  stack-start.sh                    ❌
  stack-start-unified.sh            ❌
  stack-start-complete.sh           ❌
  nv-stack-start.sh                 ❌ (duplicate of root script)
```

## Current Status: 2025-10-07

- Cleaned up: apple-stack-up.sh (removed duplicate)
- Next: Update Makefile to use canonical script
- Pending: Remove legacy Docker scripts
