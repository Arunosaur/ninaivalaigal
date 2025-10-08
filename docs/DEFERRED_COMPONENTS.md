# Deferred Components - Not Optional, Just Delayed

**Status:** Documented for future implementation
**Date:** 2024-10-06

---

## Components Deferred (Not Optional!)

These are **NOT optional** - they're part of the complete platform. Just delaying until core infrastructure is stable.

### 1. eM Automation Agent (SPEC-046)

**Current Status:**
- ❌ Old naming: `nv-em`
- ✅ Has working scripts: `nv-em-start.sh`, `nv-em-stop.sh`, `nv-em-status.sh`
- ✅ Image: `ninaivalaigal-em:latest`
- ✅ Port: 7070
- ✅ Dockerfile: `Dockerfile.em`

**What It Does:**
- Procedural Macro/Automation Agent
- Records and replays task workflows
- FastAPI service with `/health` endpoint
- Enables e^M macro recording functionality
- Plugin for repeatable task flows

**New Naming (SPEC-086):**
```
ninaivalaigal-dev-em        (dev environment)
ninaivalaigal-test-em       (test environment)
ninaivalaigal-prod-em       (prod environment)
```

**Port Strategy:**
- Port 7070 (no SPEC-086 offset - optional service)
- Or use base 7000 + env offset + runtime offset if needed

**Integration Tasks:**
1. Rename container to `ninaivalaigal-{env}-em`
2. Add to unified stack script as optional component
3. Add health checks to `stack-status.sh`
4. Add to configuration system
5. Update documentation

**Files to Update:**
- `scripts/nv-em-start.sh` → integrate into unified script
- `scripts/nv-em-stop.sh` → integrate into unified script
- `scripts/nv-em-status.sh` → integrate into stack-status
- `Dockerfile.em` → review for consistency

**Dependencies:**
- API must be running (may need API endpoints)
- Database connection (stores macro definitions)
- Redis (caches macro state)

---

### 2. Customer App UI (SPEC-075)

**Current Status:**
- ⚠️ Image may not exist: `ninaivalaigal-customer-app:latest`
- ✅ Naming already correct: `ninaivalaigal-dev-customer-app`
- ✅ Port defined: 8101 (Apple CLI + Dev)
- ❌ Not in current stack startup

**What It Does:**
- External customer-facing web application
- Built with modern UI framework
- Connects to API at localhost:13390

**Integration Tasks:**
1. Build image: `docker-compose -f compose.docker.yml build customer-app`
2. Convert to Apple Container CLI compatible build
3. Add to unified stack script
4. Add health checks
5. Test end-to-end flow

**Files to Create/Update:**
- Build instructions in unified script
- Health check endpoint verification
- Frontend routing configuration

---

### 3. Admin Console UI (SPEC-075)

**Current Status:**
- ⚠️ Image may not exist: `ninaivalaigal-admin-console:latest`
- ✅ Naming already correct: `ninaivalaigal-dev-admin-console`
- ✅ Port defined: 8201 (Apple CLI + Dev)
- ❌ Not in current stack startup

**What It Does:**
- Internal staff/admin web application
- Advanced features and admin controls
- Connects to API at localhost:13390

**Integration Tasks:**
1. Build image: `docker-compose -f compose.docker.yml build admin-console`
2. Convert to Apple Container CLI compatible build
3. Add to unified stack script
4. Add health checks
5. Test admin workflows

---

### 4. API Server (SPEC-011, SPEC-018)

**Current Status:**
- ✅ Image exists: `nina-api:arm64`
- ✅ Naming correct: `ninaivalaigal-dev-api`
- ✅ Port defined: 13390 (Apple CLI + Dev)
- ❌ Not in current stack startup (deferred until PgBouncer connection works)

**What It Does:**
- FastAPI backend server
- Memory management endpoints
- Authentication and RBAC
- Health and metrics endpoints

**Integration Tasks:**
1. Fix PgBouncer connection issue (IP detection)
2. Add to unified stack script (after PgBouncer)
3. Verify all dependencies in image
4. Test health endpoint
5. Test database connectivity through PgBouncer

**Connection Requirements:**
- **MUST** connect through PgBouncer (port 6452)
- Redis connection (port 6399)
- Environment variables properly set

---

## Implementation Priority

### Phase 1: Core Infrastructure (Current - Day 4)
✅ Database (PostgreSQL + pgvector)
✅ PgBouncer (connection pooling)
✅ Redis (cache)
🚧 Fix PgBouncer IP detection issue

### Phase 2: Application Layer (Day 5)
1. API Server - get running with PgBouncer connection
2. Test API health endpoints
3. Verify database operations

### Phase 3: User Interfaces (Day 6-7)
1. Build Customer App image (if needed)
2. Build Admin Console image (if needed)
3. Add both to stack
4. Test full end-to-end flow

### Phase 4: Advanced Features (Day 8+)
1. eM Automation Agent
2. Background worker (if needed)
3. Additional services as needed

---

## Configuration Files Needed

### For eM Agent

**configs/defaults.env:**
```bash
DEFAULT_EM_IMAGE="ninaivalaigal-em:latest"
BASE_EM_PORT=7000  # or just use 7070 fixed
```

**Environment variables needed:**
```bash
EM_SHARED_SECRET=<secret_for_auth>
EM_DATABASE_URL=postgresql://nina:password@localhost:6452/ninaivalaigal_dev
```

---

## Current Stack vs Complete Stack

### Current Stack (Running Now)
```
✅ ninaivalaigal-dev-db
✅ ninaivalaigal-dev-pgbouncer
✅ ninaivalaigal-dev-redis
```

### Complete Stack (Target)
```
ninaivalaigal-dev-db           ← Running
ninaivalaigal-dev-pgbouncer    ← Running (needs connection fix)
ninaivalaigal-dev-redis        ← Running
ninaivalaigal-dev-api          ← Next
ninaivalaigal-dev-customer-app ← After API
ninaivalaigal-dev-admin-console← After API
ninaivalaigal-dev-em           ← After UIs
```

---

## Why Deferred?

1. **Incremental validation** - Ensure each layer works before adding next
2. **Dependency order** - API needs PgBouncer, UIs need API, eM needs API
3. **Image availability** - Some images may need building first
4. **Focus** - Get infrastructure bulletproof before adding applications

---

## Next Actions

1. ✅ Document deferred components (this file)
2. 🚧 Fix PgBouncer IP detection in unified script
3. 🚧 Add API to stack startup
4. 🚧 Test API health and database connectivity
5. 📋 Build UI images if needed
6. 📋 Add UIs to stack
7. 📋 Add eM agent last

---

**Remember:** These components are NOT optional - they're essential parts of the platform. We're just being methodical about implementation order.
