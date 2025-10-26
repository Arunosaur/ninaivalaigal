# SPEC-013 User Story Created ✅

**Date:** October 26, 2025, 2:55 AM
**Story Created:** 1 (US-124)
**Priority:** P3 - LOW
**Effort:** 1 day (or 4 hours with consolidation)

---

## 📊 Story Overview

### US-124: Create SPEC-013 Standard Dockerfiles
**Link:** http://localhost:9000/project/ninaivalaigal/us/124

**Priority:** P3 - LOW (not blocking production)
**Effort:** 1 day (or 4 hours with consolidation)
**Status:** Ready

**What It Does:**
- Creates 3 standard Dockerfiles in root directory
- Enables multi-arch builds (ARM64 + x86_64)
- Unblocks GitHub Actions workflow
- Completes SPEC-013 implementation

**Why Priority is LOW:**
- Infrastructure already perfect (workflow, Makefile, registry)
- Alternative Dockerfiles exist in other locations
- Not blocking production deployments
- Can be deferred until GHCR distribution becomes critical

---

## 🎯 Files to Create

### 1. Dockerfile.api
**Location:** `/Dockerfile.api`

**Requirements:**
- Base: python:3.11-slim
- Multi-stage build (builder + runtime)
- FastAPI application
- Health checks (`/health` endpoint)
- Non-root user (apiuser)
- Architecture: linux/amd64, linux/arm64

### 2. Dockerfile.postgres
**Location:** `/Dockerfile.postgres`

**Requirements:**
- Base: postgres:15
- pgvector extension
- Initialization scripts
- Health checks (`pg_isready`)
- Environment variable configuration
- Architecture: linux/amd64, linux/arm64

### 3. Dockerfile.pgbouncer
**Location:** `/Dockerfile.pgbouncer`

**Requirements:**
- Base: debian:12-slim
- PgBouncer connection pooler
- SCRAM-SHA-256 authentication
- Template-based configuration
- Environment variable substitution
- Architecture: linux/amd64, linux/arm64

---

## ✅ Acceptance Criteria (26 Total)

### Dockerfile Creation (3 ACs)
- [ ] **AC1**: Create `Dockerfile.api` in root
- [ ] **AC2**: Create `Dockerfile.postgres` in root
- [ ] **AC3**: Create `Dockerfile.pgbouncer` in root

### Dockerfile.api (6 ACs)
- [ ] **AC4**: Python 3.11-slim base
- [ ] **AC5**: Multi-stage build
- [ ] **AC6**: Health check (`/health`)
- [ ] **AC7**: Non-root user (apiuser)
- [ ] **AC8**: FastAPI dependencies
- [ ] **AC9**: Proper Python path handling

### Dockerfile.postgres (5 ACs)
- [ ] **AC10**: postgres:15 base
- [ ] **AC11**: pgvector extension
- [ ] **AC12**: Init scripts
- [ ] **AC13**: Health check (`pg_isready`)
- [ ] **AC14**: Environment configuration

### Dockerfile.pgbouncer (5 ACs)
- [ ] **AC15**: debian:12-slim base
- [ ] **AC16**: PgBouncer pooler
- [ ] **AC17**: SCRAM-SHA-256 auth
- [ ] **AC18**: Template-based config
- [ ] **AC19**: Environment substitution

### Build Validation (4 ACs)
- [ ] **AC20**: Multi-arch build succeeds
- [ ] **AC21**: `make release-local` works
- [ ] **AC22**: All 3 images build
- [ ] **AC23**: Health checks pass

### Integration Testing (3 ACs)
- [ ] **AC24**: GitHub Actions succeeds
- [ ] **AC25**: Architecture-agnostic
- [ ] **AC26**: Image sizes optimized

---

## 📊 Cross-References

### SPEC-013 Requirements Met

| SPEC Section | Requirement | This Story |
|--------------|-------------|------------|
| **Section 1.2** | Dockerfile Requirements | All 3 files |
| **Section 4.1** | API Container | Dockerfile.api |
| **Section 4.2** | Database Container | Dockerfile.postgres |
| **Section 4.3** | PgBouncer Container | Dockerfile.pgbouncer |

### SPEC-013 Sections Referenced

**Section 1.2: Dockerfile Requirements**
- ✅ Multi-stage builds (AC5)
- ✅ Architecture-agnostic base images (AC4, AC10, AC15)
- ✅ Health checks (AC6, AC13)
- ✅ Non-root user (AC7)
- ✅ Proper entry points (AC9)

**Section 4.1: API Container Specs**
- ✅ Base: python:3.11-slim
- ✅ Architecture: linux/amd64,linux/arm64
- ✅ Multi-stage build
- ✅ FastAPI application
- ✅ Health checks
- ✅ Non-root user

**Section 4.2: Database Container Specs**
- ✅ Base: postgres:15
- ✅ Architecture: linux/amd64,linux/arm64
- ✅ pgvector extension
- ✅ Initialization scripts
- ✅ Health checks

**Section 4.3: PgBouncer Container Specs**
- ✅ Base: debian:12-slim
- ✅ Architecture: linux/amd64,linux/arm64
- ✅ PgBouncer pooling
- ✅ SCRAM-SHA-256 auth
- ✅ Template-based config

### Infrastructure Files (Already Complete)

**GitHub Actions:**
- `.github/workflows/release-containers.yml` - Multi-arch workflow ✅

**Makefile:**
- `make release` - Push to GHCR ✅
- `make release-local` - Local testing ✅

**SPEC Documentation:**
- `specs/013-multi-architecture-container-strategy/spec.md` ✅

### Reference Dockerfiles (Can Use as Templates)

**Existing Dockerfiles to Consolidate:**
- `containers/api/Dockerfile` - API container
- `containers/ninaivalaigal-db/Dockerfile` - Database with pgvector
- `containers/pgbouncer/Dockerfile` - Connection pooler
- `docker/api/Dockerfile` - Alternative API
- `docker/services/Dockerfile.postgres` - Alternative DB

### Related SPECs
- **SPEC-014**: Infrastructure as Code (uses these containers)
- **SPEC-015**: Kubernetes Deployment (uses these images)
- **SPEC-016**: CI/CD Pipeline (builds these containers)
- **SPEC-017**: Development Environment (local testing)

### Related User Stories
- **ENABLES**: Multi-arch container distribution
- **UNBLOCKS**: GHCR automated publishing
- **COMPLETES**: SPEC-013 (60% → 100%)

---

## 🔧 Implementation Options

### Option 1: Create from Scratch
**Effort:** 1 day
**Pros:** Clean, standardized, optimized
**Cons:** More work, needs testing

### Option 2: Consolidate Existing ⭐ RECOMMENDED
**Effort:** 4 hours
**Pros:** Faster, proven, less testing
**Cons:** May need cleanup

**Recommended Approach:**
```bash
# Copy best versions
cp containers/api/Dockerfile Dockerfile.api
cp containers/ninaivalaigal-db/Dockerfile Dockerfile.postgres
cp containers/pgbouncer/Dockerfile Dockerfile.pgbouncer

# Standardize for multi-arch
# Test with make release-local
```

### Option 3: Symlink (Not Recommended)
**Effort:** 5 minutes
**Pros:** Immediate
**Cons:** Non-standard, confusing

---

## 🧪 Testing Strategy

### Local Testing
```bash
# Single-arch build
docker build -f Dockerfile.api -t test-api .
docker build -f Dockerfile.postgres -t test-db .
docker build -f Dockerfile.pgbouncer -t test-pgbouncer .

# Multi-arch build
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.api -t test-api:multi .

# Makefile testing
make release-local
```

### Health Check Validation
```bash
# Start containers
docker run -d --name test-api -p 8000:8000 test-api
docker run -d --name test-db -p 5432:5432 test-db

# Check health
docker inspect --format='{{.State.Health.Status}}' test-api
docker inspect --format='{{.State.Health.Status}}' test-db

# Should return "healthy"
```

### CI/CD Testing
```bash
# Create test tag
git tag -a v0.0.1-test -m "Test multi-arch build"
git push origin v0.0.1-test

# Workflow triggers automatically
# Check GitHub Actions
```

---

## 📊 Impact Analysis

### Before US-124
```
SPEC-013 Status:
├─ GitHub Actions: ✅ 100%
├─ Makefile: ✅ 100%
├─ GHCR Strategy: ✅ 100%
├─ Documentation: ✅ 100%
├─ Dockerfile.api: ❌ 0%
├─ Dockerfile.postgres: ❌ 0%
└─ Dockerfile.pgbouncer: ❌ 0%

Overall: 60% (4/7 components)
Multi-arch builds: BROKEN
```

### After US-124
```
SPEC-013 Status:
├─ GitHub Actions: ✅ 100%
├─ Makefile: ✅ 100%
├─ GHCR Strategy: ✅ 100%
├─ Documentation: ✅ 100%
├─ Dockerfile.api: ✅ 100%
├─ Dockerfile.postgres: ✅ 100%
└─ Dockerfile.pgbouncer: ✅ 100%

Overall: 100% (7/7 components) ✅
Multi-arch builds: WORKING ✅
```

**Change:** +40% coverage, multi-arch builds operational

---

## 💡 Why Priority is LOW

### Infrastructure Already Perfect
- ✅ GitHub Actions workflow ready
- ✅ Makefile targets ready
- ✅ Registry configured (GHCR)
- ✅ Documentation complete
- ✅ External validation working

### Not Blocking Production
- Local development works (other Dockerfiles exist)
- Production deployments possible (alternative paths)
- Can defer until GHCR distribution needed
- No immediate business impact

### Alternative Solutions Exist
- 33 Dockerfiles already in codebase
- Can use alternative locations temporarily
- Container builds work (just not standardized)

### When to Prioritize

**Increase Priority When:**
- Publishing to GHCR becomes important
- Deploying to multiple architectures (ARM64 + x86_64)
- Standardizing container distribution
- Onboarding new team members (clarity/consistency)
- CI/CD automation becomes critical

---

## 📈 Session Summary

**SPECs Analyzed Tonight:** 11 (003-013)

| SPEC | Coverage | Stories | Status |
|------|----------|---------|--------|
| 003 | 95% | 4 | Gaps |
| 004 | 54% | 5 | Gaps |
| 005 | 38% | 5 | Gaps |
| 006 | 94% | 0 | ✅ Complete |
| 007 | 100% | 0 | ✅ Complete |
| 008 | 95% | 0 | ✅ Near Complete |
| 009 | 40% | 5 | Gaps |
| 010 | 100% | 0 | ✅ Complete |
| 011 | 70% | 3 | Gaps |
| 012 | 95% | 1 | ⚠️ 5-min fix |
| **013** | **60%** | **1** | Gaps (LOW priority) |

**Complete/Near-Complete SPECs:** 6 (006, 007, 008, 010, 012)
**Total User Stories Created Tonight:** 25

**SPEC-013 After US-124:** Will be 100% COMPLETE! ✅

---

## 🎯 Recommendation

**Priority:** Keep at P3 - LOW

**Rationale:**
- Perfect infrastructure already in place
- Not blocking any production work
- Can be done later when GHCR distribution needed
- Other priorities are higher (US-120 database schema is P0)

**When to Implement:**
- After critical priorities (US-120, US-121)
- When publishing to GHCR becomes important
- When standardizing container strategy
- When onboarding requires clarity

**Quick Win if Prioritized:**
- Option 2 (consolidate existing): 4 hours
- Low risk (additive only)
- High value (completes entire SPEC)

---

**Documentation Complete:** October 26, 2025, 2:55 AM
**Story Created:** US-124
**Priority:** P3 - LOW
**Status:** ✅ **READY (when prioritized)**

**Perfect infrastructure waiting for 3 files!** 🐳
