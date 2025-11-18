# US#93/US#95: Python Router Deprecation Plan

**Developer F**
**Date**: 2025-01-31
**Status**: 📋 Planning Phase

---

## 🎯 Objective

Deprecate Python memory routers that have been migrated to Rust, following SPEC-131 (Memory Router Rationalization) Phase 3 cleanup.

---

## 📊 Migration Status

### ✅ Migrated to Rust (Phase 1 Complete)

| Python Router | Rust Endpoint | Status |
|--------------|---------------|--------|
| `memory_injection_api.py` | `/memory/injection/*` | ✅ Migrated |
| `queue_api.py` | `/queue/*` | ✅ Migrated |

### 🔍 Health API Status

| Python Router | Rust Endpoint | Status |
|--------------|---------------|--------|
| `memory_health_api.py` | `/health` | ✅ Already exists in Rust |

**Note**: Rust service already has `/health` endpoint. Need to verify if `memory_health_api.py` duplicates functionality.

---

## 📋 Deprecation Plan

### Phase 1: Documentation & Communication (Week 1)

#### 1.1 Mark Routers as Deprecated
- [ ] Add deprecation warnings to Python router files
- [ ] Update OpenAPI documentation with deprecation notices
- [ ] Add deprecation date and migration deadline

#### 1.2 Create Migration Guide
- [ ] Document endpoint mapping (Python → Rust)
- [ ] Create client migration examples
- [ ] Document breaking changes (if any)
- [ ] Performance comparison guide

#### 1.3 Update API Documentation
- [ ] Update Swagger/OpenAPI docs
- [ ] Mark deprecated endpoints
- [ ] Add migration links

---

### Phase 2: Parallel Operation (Week 2-3)

#### 2.1 Keep Python Routers Active
- [ ] Python routers remain functional
- [ ] Monitor usage metrics
- [ ] Track client adoption of Rust endpoints

#### 2.2 Client Migration Support
- [ ] Update client SDKs to use Rust endpoints
- [ ] Provide migration scripts
- [ ] Support both endpoints during transition

#### 2.3 Monitoring
- [ ] Track endpoint usage
- [ ] Monitor error rates
- [ ] Performance comparison

---

### Phase 3: Deprecation (Week 4)

#### 3.1 Remove Router Registration
**File**: `server/main.py`

**Remove**:
```python
# Line 321
from memory_injection_api import router as memory_injection_router

# Line 391
app.include_router(memory_injection_router)
```

**Note**: `queue_api.py` is not currently registered in `main.py` (only in backup file), so may already be deprecated.

#### 3.2 Archive Router Files
- [ ] Move to `server/deprecated/` directory
- [ ] Add deprecation notice at top of files
- [ ] Update git history tags

#### 3.3 Update Dependencies
- [ ] Remove unused imports
- [ ] Clean up `requirements.txt` if applicable
- [ ] Update documentation

---

## 📝 Files to Modify

### 1. Python Router Files (Add Deprecation Notice)

#### `server/memory_injection_api.py`
```python
"""
SPEC-036: Memory Injection API Endpoints
⚠️  DEPRECATED: This router has been migrated to Rust Memory Service
⚠️  Migration Date: 2025-01-31
⚠️  Removal Date: 2025-04-30 (3 months grace period)
⚠️  New Endpoint: http://localhost:13393/memory/injection/*
⚠️  See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md

This router will be removed in Phase 3. Please migrate to Rust endpoints.
"""
```

#### `server/queue_api.py`
```python
"""
⚠️  DEPRECATED: This router has been migrated to Rust Memory Service
⚠️  Migration Date: 2025-01-31
⚠️  Removal Date: 2025-04-30
⚠️  New Endpoint: http://localhost:13393/queue/*
"""
```

#### `server/memory_health_api.py`
```python
"""
⚠️  DEPRECATED: Health endpoint available in Rust Memory Service
⚠️  New Endpoint: http://localhost:13393/health
"""
```

### 2. Main Application File

#### `server/main.py`
**Current** (lines 321, 391):
```python
from memory_injection_api import router as memory_injection_router  # noqa: E402
...
app.include_router(memory_injection_router)
```

**After Deprecation**:
```python
# DEPRECATED: memory_injection_api migrated to Rust Memory Service
# See: tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md
# from memory_injection_api import router as memory_injection_router  # noqa: E402
...
# app.include_router(memory_injection_router)  # DEPRECATED
```

---

## 🔄 Endpoint Mapping

### Memory Injection API

| Python Endpoint | Rust Endpoint | Notes |
|----------------|---------------|-------|
| `POST /memory/injection/analyze` | `POST /memory/injection/analyze` | Same path |
| `POST /memory/injection/execute` | `POST /memory/injection/execute` | Same path |
| `POST /memory/injection/bulk` | `POST /memory/injection/bulk` | Same path |

**Base URL Change**:
- Python: `http://localhost:13390` (Core API)
- Rust: `http://localhost:13393` (Memory Service)

### Queue API

| Python Endpoint | Rust Endpoint | Notes |
|----------------|---------------|-------|
| `POST /queue/tasks` | `POST /queue/tasks` | Same path |
| `GET /queue/jobs/:job_id` | `GET /queue/jobs/:job_id` | Same path |
| `GET /queue/stats` | `GET /queue/stats` | Same path |
| `POST /queue/memory/:memory_id/process` | `POST /queue/memory/:memory_id/process` | Same path |
| `GET /queue/health` | `GET /queue/health` | Same path |

**Base URL Change**:
- Python: `http://localhost:13390`
- Rust: `http://localhost:13393`

### Health API

| Python Endpoint | Rust Endpoint | Notes |
|----------------|---------------|-------|
| `GET /health` (memory health) | `GET /health` | Same path |

**Base URL Change**:
- Python: `http://localhost:13390`
- Rust: `http://localhost:13393`

---

## 📚 Client Migration Guide

### Before (Python Core API)
```python
import requests

BASE_URL = "http://localhost:13390"
headers = {"Authorization": f"Bearer {token}"}

# Injection API
response = requests.post(
    f"{BASE_URL}/memory/injection/analyze",
    json=analysis_request,
    headers=headers
)

# Queue API
response = requests.post(
    f"{BASE_URL}/queue/tasks",
    json=task_request,
    headers=headers
)
```

### After (Rust Memory Service)
```python
import requests

# Memory Service base URL
MEMORY_SERVICE_URL = "http://localhost:13393"
headers = {"Authorization": f"Bearer {token}"}

# Injection API (same endpoints, different base URL)
response = requests.post(
    f"{MEMORY_SERVICE_URL}/memory/injection/analyze",
    json=analysis_request,
    headers=headers
)

# Queue API (same endpoints, different base URL)
response = requests.post(
    f"{MEMORY_SERVICE_URL}/queue/tasks",
    json=task_request,
    headers=headers
)
```

### Key Changes
1. **Base URL**: Change from port `13390` to `13393`
2. **Service**: Calls go directly to Memory Service instead of Core API
3. **Endpoints**: Same paths, same request/response formats
4. **Authentication**: Same JWT token format

---

## ⚠️ Breaking Changes

### None Expected
- ✅ Same endpoint paths
- ✅ Same request/response formats
- ✅ Same authentication method
- ✅ Same error codes

### Only Change
- ⚠️ **Base URL**: Port change from `13390` to `13393`
- ⚠️ **Service**: Direct call to Memory Service (no Core API proxy)

---

## 📊 Migration Checklist

### Pre-Deprecation
- [ ] Verify Rust endpoints work correctly
- [ ] Run integration tests against Rust service
- [ ] Performance benchmarks pass SPEC-131 targets
- [ ] Update client SDKs
- [ ] Update API documentation

### Deprecation Phase
- [ ] Add deprecation warnings to Python routers
- [ ] Update OpenAPI documentation
- [ ] Notify all client teams
- [ ] Monitor usage metrics
- [ ] Track migration progress

### Removal Phase
- [ ] Confirm no active clients using Python endpoints
- [ ] Remove router registration from `main.py`
- [ ] Archive router files
- [ ] Update documentation
- [ ] Remove unused dependencies

---

## 🗓️ Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 1: Documentation** | 1 week | 📋 Ready to start |
| **Phase 2: Parallel Operation** | 2-3 weeks | ⏳ Pending |
| **Phase 3: Removal** | 1 week | ⏳ Pending |

**Total**: 4-5 weeks

**Deprecation Date**: 2025-01-31
**Removal Date**: 2025-04-30 (3 months grace period)

---

## 📈 Success Metrics

### Migration Progress
- [ ] 0% clients using Python endpoints
- [ ] All clients migrated to Rust endpoints
- [ ] Zero errors in Rust endpoints
- [ ] Performance targets met

### Performance Improvements
- [ ] Queue API: P99 < 10ms (target met)
- [ ] Injection API: >1000 memories/sec (target met)
- [ ] Resource usage: 30% reduction (target met)

---

## 🔗 References

- **SPEC-131**: Memory Router Rationalization
- **Migration Plan**: `specs/131-memory-router-rationalization/MIGRATION_PLAN.md`
- **Rust Implementation**: `rust-services/memory-service/src/api/`
- **Production Readiness**: `tasks/active/US_93_95_PRODUCTION_READY.md`

---

## 📝 Notes

1. **Grace Period**: 3 months between deprecation and removal
2. **Monitoring**: Track usage to ensure no active clients before removal
3. **Rollback Plan**: Keep Python routers in git history for emergency rollback
4. **Documentation**: All changes must be documented before removal

---

**Status**: Ready to begin Phase 1 (Documentation & Communication)




