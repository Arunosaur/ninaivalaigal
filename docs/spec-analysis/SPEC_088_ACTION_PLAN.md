# SPEC-088: API Versioning Strategy - Action Plan

**Date**: November 2, 2025 3:05 AM
**Status**: 📋 **PLANNED** (Currently ~10-15% Complete)
**Priority**: 🔴 **HIGH** - Critical for API stability and backward compatibility
**US**: #568

---

## Executive Summary

SPEC-088 is currently **incomplete** with only stub documentation and ad-hoc implementation. A comprehensive versioning strategy exists in `shared/contracts/docs/VERSIONING_STRATEGY.md` but needs to be consolidated with SPEC-088 as the authoritative source.

**Current State**: ~10-15% complete (stubs + 2 v1 endpoints)
**Target State**: 100% complete with systematic versioning infrastructure
**Estimated Effort**: 3-5 days

---

## Current State Analysis

### ✅ What Exists

**Documentation (Stubs Only)**:
- `specs/088-api-versioning-strategy/README.md` - Headers only
- `specs/088-api-versioning-strategy/breaking-changes.md` - Headers only
- `specs/088-api-versioning-strategy/deprecation-policy.md` - Headers only
- `specs/088-api-versioning-strategy/format.md` - Partial content

**Implementation (Ad-hoc)**:
- 2 routers use `/api/v1/` prefix:
  - GDPR compliance endpoints
  - HIPAA compliance endpoints
- No systematic versioning infrastructure
- No versioning middleware
- No version routing logic

**External Documentation**:
- `shared/contracts/docs/VERSIONING_STRATEGY.md` - **Comprehensive** versioning strategy
  - Complete semantic versioning guidelines
  - Breaking change management
  - Deprecation policies
  - Migration strategies

### ❌ What's Missing

**Documentation**:
- [ ] Complete README.md with versioning overview
- [ ] Full breaking-changes.md with examples
- [ ] Complete deprecation-policy.md with timelines
- [ ] Finish format.md with all versioning formats
- [ ] Migration guides for version upgrades
- [ ] API version compatibility matrix

**Infrastructure**:
- [ ] Versioning middleware for automatic routing
- [ ] Version negotiation logic (Accept header, URL prefix)
- [ ] Version deprecation warnings in responses
- [ ] Automated version compatibility testing
- [ ] Version-specific OpenAPI schemas
- [ ] Version routing configuration

**Implementation**:
- [ ] Systematic `/api/v1/` prefix for all endpoints
- [ ] Version-specific router organization
- [ ] Backward compatibility layer
- [ ] Version migration utilities
- [ ] API version health checks

---

## Duplication Analysis

### **Issue**: Duplicate Versioning Documentation

**Location 1**: `specs/088-api-versioning-strategy/` (SPEC-088)
- **Status**: Incomplete (stubs only)
- **Should be**: Authoritative source

**Location 2**: `shared/contracts/docs/VERSIONING_STRATEGY.md`
- **Status**: Complete and comprehensive
- **Issue**: Creates confusion about authoritative source

### **Recommendation**: Consolidate

**Option 1: Merge into SPEC-088** (RECOMMENDED)
1. Move content from `shared/contracts/docs/VERSIONING_STRATEGY.md` to SPEC-088
2. Update SPEC-088 with complete documentation
3. Replace `VERSIONING_STRATEGY.md` with reference to SPEC-088
4. Make SPEC-088 the single source of truth

**Option 2: Cross-Reference**
1. Keep both documents
2. Add clear cross-references
3. Define scope boundaries
4. Risk: Ongoing maintenance burden

**Decision**: **Option 1** - Consolidate into SPEC-088

---

## Related SPECs Analysis

### **SPEC-087: API Surface Contracts**
- **Relationship**: Complementary
- **Overlap**: None
- **Coordination**: SPEC-088 defines versioning strategy, SPEC-087 defines contract format
- **Action**: Ensure versioning strategy aligns with contract definitions

### **SPEC-089: Breaking Change Management**
- **Relationship**: Related (possible overlap)
- **Overlap**: Deprecation policies
- **Coordination**: SPEC-088 should reference SPEC-089 for breaking change process
- **Action**: Coordinate deprecation timelines and policies

### **SPEC-003: Core API Architecture**
- **Relationship**: Complementary
- **Overlap**: None
- **Coordination**: Versioning infrastructure must align with core architecture
- **Action**: Ensure version routing fits within existing architecture

### **SPEC-100: API Container Modularization**
- **Relationship**: Complementary
- **Overlap**: None
- **Coordination**: Each module may have independent versioning
- **Action**: Define per-module vs. global versioning strategy

---

## Implementation Plan

### **Phase 1: Documentation Completion** (2 days)

**Priority**: 🔴 **CRITICAL** - Foundation for implementation

#### **Task 1.1: Consolidate Versioning Documentation**
- [ ] Review `shared/contracts/docs/VERSIONING_STRATEGY.md`
- [ ] Extract key content and examples
- [ ] Merge into SPEC-088 documentation
- [ ] Organize into appropriate files (README, breaking-changes, deprecation-policy, format)

**Files to Complete**:
1. **`README.md`**
   - Overview of versioning strategy
   - Semantic versioning guidelines
   - Version format specifications
   - Version negotiation methods
   - Examples and best practices

2. **`breaking-changes.md`**
   - Definition of breaking changes
   - Breaking change categories
   - Impact assessment guidelines
   - Communication strategy
   - Real-world examples

3. **`deprecation-policy.md`**
   - Deprecation timeline (e.g., 6 months notice)
   - Deprecation warning format
   - Sunset schedule
   - Migration support
   - Communication channels

4. **`format.md`**
   - URL versioning: `/api/v1/`, `/api/v2/`
   - Header versioning: `Accept: application/vnd.ninaivalaigal.v1+json`
   - Query parameter versioning: `?api-version=1`
   - Custom header: `X-API-Version: 1`
   - Version precedence rules

5. **`migration-guide.md`** (NEW)
   - Version upgrade procedures
   - Backward compatibility guidelines
   - Migration utilities
   - Testing strategies

6. **`compatibility-matrix.md`** (NEW)
   - API version compatibility table
   - Client SDK version requirements
   - Deprecated feature timeline
   - Support lifecycle

#### **Task 1.2: Update Cross-References**
- [ ] Replace `shared/contracts/docs/VERSIONING_STRATEGY.md` with reference to SPEC-088
- [ ] Add cross-references to SPEC-087, SPEC-089
- [ ] Update SPEC_INDEX.md with completion status
- [ ] Update related SPECs to reference SPEC-088

**Deliverables**:
- ✅ Complete SPEC-088 documentation
- ✅ Single authoritative source for versioning
- ✅ Clear cross-references to related SPECs

---

### **Phase 2: Infrastructure Implementation** (2 days)

**Priority**: 🟡 **HIGH** - Enables systematic versioning

#### **Task 2.1: Versioning Middleware**

**File**: `lib/middleware/api_versioning.py`

```python
"""
API Versioning Middleware

Handles version negotiation and routing based on:
1. URL prefix: /api/v1/, /api/v2/
2. Accept header: application/vnd.ninaivalaigal.v1+json
3. Custom header: X-API-Version: 1
4. Query parameter: ?api-version=1
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import re

class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API version negotiation and routing"""

    SUPPORTED_VERSIONS = ["1", "2"]  # Add versions as they're released
    DEFAULT_VERSION = "1"

    async def dispatch(self, request: Request, call_next):
        # Extract version from request
        version = self._extract_version(request)

        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. "
                       f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}"
            )

        # Add version to request state
        request.state.api_version = version

        # Add deprecation warning if applicable
        response = await call_next(request)
        if self._is_deprecated(version):
            response.headers["X-API-Deprecation"] = (
                f"API version {version} is deprecated. "
                f"Please upgrade to version {self.DEFAULT_VERSION}."
            )
            response.headers["X-API-Sunset"] = self._get_sunset_date(version)

        # Add version to response headers
        response.headers["X-API-Version"] = version

        return response

    def _extract_version(self, request: Request) -> str:
        """Extract API version from request (precedence order)"""

        # 1. URL prefix: /api/v1/
        url_match = re.match(r"/api/v(\d+)/", request.url.path)
        if url_match:
            return url_match.group(1)

        # 2. Custom header: X-API-Version
        if "X-API-Version" in request.headers:
            return request.headers["X-API-Version"]

        # 3. Accept header: application/vnd.ninaivalaigal.v1+json
        accept = request.headers.get("Accept", "")
        accept_match = re.search(r"application/vnd\.ninaivalaigal\.v(\d+)\+json", accept)
        if accept_match:
            return accept_match.group(1)

        # 4. Query parameter: ?api-version=1
        if "api-version" in request.query_params:
            return request.query_params["api-version"]

        # 5. Default version
        return self.DEFAULT_VERSION

    def _is_deprecated(self, version: str) -> bool:
        """Check if version is deprecated"""
        # TODO: Load from configuration
        deprecated_versions = []  # e.g., ["0"]
        return version in deprecated_versions

    def _get_sunset_date(self, version: str) -> str:
        """Get sunset date for deprecated version"""
        # TODO: Load from configuration
        sunset_dates = {}  # e.g., {"0": "2025-12-31"}
        return sunset_dates.get(version, "")
```

#### **Task 2.2: Version Routing**

**File**: `lib/routing/version_router.py`

```python
"""
Version-aware routing for API endpoints

Organizes routers by version and provides version-specific routing.
"""

from fastapi import APIRouter, Request
from typing import Dict, List

class VersionedAPIRouter:
    """Router that supports multiple API versions"""

    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}

    def add_version(self, version: str, router: APIRouter):
        """Add a router for a specific API version"""
        self.routers[version] = router

    def get_router(self, version: str) -> APIRouter:
        """Get router for specific version"""
        if version not in self.routers:
            raise ValueError(f"No router for version {version}")
        return self.routers[version]

    def get_all_routers(self) -> List[APIRouter]:
        """Get all version routers"""
        return list(self.routers.values())


# Example usage:
# v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
# v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
#
# versioned_router = VersionedAPIRouter()
# versioned_router.add_version("1", v1_router)
# versioned_router.add_version("2", v2_router)
```

#### **Task 2.3: Version-Specific OpenAPI Schemas**

**File**: `lib/openapi/versioned_schema.py`

```python
"""
Generate version-specific OpenAPI schemas

Each API version gets its own OpenAPI schema for documentation.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def generate_versioned_openapi(app: FastAPI, version: str) -> dict:
    """Generate OpenAPI schema for specific API version"""

    return get_openapi(
        title=f"Ninaivalaigal API v{version}",
        version=version,
        description=f"API version {version} documentation",
        routes=app.routes,
        servers=[
            {"url": f"/api/v{version}", "description": f"Version {version}"}
        ]
    )

# Example usage:
# @app.get("/api/v1/openapi.json")
# async def get_v1_openapi():
#     return generate_versioned_openapi(app, "1")
```

**Deliverables**:
- ✅ Versioning middleware implemented
- ✅ Version routing infrastructure
- ✅ Version-specific OpenAPI schemas
- ✅ Deprecation warning system

---

### **Phase 3: Systematic Implementation** (1 day)

**Priority**: 🟢 **MEDIUM** - Apply versioning to all endpoints

#### **Task 3.1: Organize Routers by Version**

**Current Structure**:
```
lib/api/
  ├── auth.py
  ├── memory.py
  ├── context.py
  └── ...
```

**Target Structure**:
```
lib/api/
  ├── v1/
  │   ├── __init__.py
  │   ├── auth.py
  │   ├── memory.py
  │   ├── context.py
  │   └── ...
  ├── v2/  (future)
  │   └── ...
  └── versioning.py  (version routing logic)
```

#### **Task 3.2: Apply `/api/v1/` Prefix**

**Current** (ad-hoc):
```python
# Only 2 routers use v1 prefix
router = APIRouter(prefix="/api/v1/gdpr", tags=["gdpr"])
router = APIRouter(prefix="/api/v1/hipaa", tags=["hipaa"])
```

**Target** (systematic):
```python
# All routers use v1 prefix
v1_auth_router = APIRouter(prefix="/api/v1/auth", tags=["v1", "auth"])
v1_memory_router = APIRouter(prefix="/api/v1/memory", tags=["v1", "memory"])
v1_context_router = APIRouter(prefix="/api/v1/context", tags=["v1", "context"])
# ... all other routers
```

#### **Task 3.3: Update Main Application**

**File**: `services/core-api/main.py`

```python
from lib.middleware.api_versioning import APIVersioningMiddleware
from lib.routing.version_router import VersionedAPIRouter
from lib.api.v1 import (
    auth_router,
    memory_router,
    context_router,
    # ... other v1 routers
)

app = FastAPI(title="Ninaivalaigal API")

# Add versioning middleware
app.add_middleware(APIVersioningMiddleware)

# Set up versioned routing
versioned_router = VersionedAPIRouter()

# Add v1 routers
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v1_router.include_router(auth_router)
v1_router.include_router(memory_router)
v1_router.include_router(context_router)
# ... include all other v1 routers

versioned_router.add_version("1", v1_router)

# Include versioned routers in app
for router in versioned_router.get_all_routers():
    app.include_router(router)
```

**Deliverables**:
- ✅ All endpoints use `/api/v1/` prefix
- ✅ Routers organized by version
- ✅ Versioning middleware active
- ✅ Version-specific documentation

---

### **Phase 4: Testing & Validation** (0.5 days)

**Priority**: 🟢 **MEDIUM** - Ensure versioning works correctly

#### **Task 4.1: Version Negotiation Tests**

**File**: `tests/test_api_versioning.py`

```python
"""
Tests for API versioning functionality
"""

import pytest
from fastapi.testclient import TestClient

def test_url_prefix_versioning(client: TestClient):
    """Test version extraction from URL prefix"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["X-API-Version"] == "1"

def test_header_versioning(client: TestClient):
    """Test version extraction from X-API-Version header"""
    response = client.get("/api/health", headers={"X-API-Version": "1"})
    assert response.status_code == 200
    assert response.headers["X-API-Version"] == "1"

def test_accept_header_versioning(client: TestClient):
    """Test version extraction from Accept header"""
    response = client.get(
        "/api/health",
        headers={"Accept": "application/vnd.ninaivalaigal.v1+json"}
    )
    assert response.status_code == 200
    assert response.headers["X-API-Version"] == "1"

def test_query_param_versioning(client: TestClient):
    """Test version extraction from query parameter"""
    response = client.get("/api/health?api-version=1")
    assert response.status_code == 200
    assert response.headers["X-API-Version"] == "1"

def test_unsupported_version(client: TestClient):
    """Test error handling for unsupported version"""
    response = client.get("/api/v99/health")
    assert response.status_code == 400
    assert "Unsupported API version" in response.json()["detail"]

def test_deprecation_warning(client: TestClient):
    """Test deprecation warning for old versions"""
    # Assuming v0 is deprecated
    response = client.get("/api/v0/health")
    assert "X-API-Deprecation" in response.headers
    assert "X-API-Sunset" in response.headers
```

#### **Task 4.2: Backward Compatibility Tests**

**File**: `tests/test_version_compatibility.py`

```python
"""
Tests for backward compatibility between API versions
"""

def test_v1_auth_endpoints_exist(client: TestClient):
    """Ensure v1 auth endpoints are accessible"""
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "test123",
        "name": "Test User"
    })
    assert response.status_code in [200, 201, 400]  # 400 if user exists

def test_v1_memory_endpoints_exist(client: TestClient):
    """Ensure v1 memory endpoints are accessible"""
    response = client.get("/api/v1/memory/memories")
    assert response.status_code in [200, 401]  # 401 if not authenticated
```

**Deliverables**:
- ✅ Version negotiation tests passing
- ✅ Backward compatibility verified
- ✅ Deprecation warnings tested
- ✅ Error handling validated

---

## Success Criteria

### **Documentation Complete** ✅
- [ ] All SPEC-088 documentation files complete
- [ ] Single authoritative source established
- [ ] Cross-references to related SPECs added
- [ ] Migration guides available
- [ ] Compatibility matrix documented

### **Infrastructure Implemented** ✅
- [ ] Versioning middleware active
- [ ] Version routing functional
- [ ] Version-specific OpenAPI schemas
- [ ] Deprecation warning system working

### **Systematic Implementation** ✅
- [ ] All endpoints use `/api/v1/` prefix
- [ ] Routers organized by version
- [ ] Main application updated
- [ ] Version negotiation working

### **Testing Complete** ✅
- [ ] Version negotiation tests passing
- [ ] Backward compatibility verified
- [ ] Deprecation warnings tested
- [ ] Error handling validated

---

## Timeline

**Total Estimated Time**: 3-5 days

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Documentation | 2 days | 🔴 CRITICAL | None |
| Phase 2: Infrastructure | 2 days | 🟡 HIGH | Phase 1 |
| Phase 3: Implementation | 1 day | 🟢 MEDIUM | Phase 2 |
| Phase 4: Testing | 0.5 days | 🟢 MEDIUM | Phase 3 |

**Start Date**: TBD
**Target Completion**: TBD

---

## Dependencies

### **Blocking**
- None - can start immediately

### **Related**
- SPEC-087: API Surface Contracts (coordinate contract format)
- SPEC-089: Breaking Change Management (coordinate deprecation policy)
- SPEC-003: Core API Architecture (ensure alignment)
- SPEC-100: API Container Modularization (define per-module versioning)

---

## Risks & Mitigation

### **Risk 1: Breaking Existing Clients**
**Impact**: 🔴 HIGH
**Probability**: 🟡 MEDIUM
**Mitigation**:
- Implement backward compatibility layer
- Provide migration period with both old and new endpoints
- Communicate changes early and clearly

### **Risk 2: Performance Overhead**
**Impact**: 🟡 MEDIUM
**Probability**: 🟢 LOW
**Mitigation**:
- Optimize version negotiation logic
- Cache version routing decisions
- Monitor performance metrics

### **Risk 3: Documentation Drift**
**Impact**: 🟡 MEDIUM
**Probability**: 🟡 MEDIUM
**Mitigation**:
- Establish single source of truth (SPEC-088)
- Automate documentation generation where possible
- Regular documentation reviews

---

## Next Steps

### **Immediate** (Today)
1. [ ] Review and approve this action plan
2. [ ] Assign developer to US#568
3. [ ] Update Taiga story status to "Planned"
4. [ ] Schedule kickoff meeting

### **Phase 1 Start** (Next)
1. [ ] Review `shared/contracts/docs/VERSIONING_STRATEGY.md`
2. [ ] Begin consolidating documentation into SPEC-088
3. [ ] Create migration-guide.md and compatibility-matrix.md
4. [ ] Update cross-references

### **Ongoing**
1. [ ] Daily standup updates
2. [ ] Code reviews for each phase
3. [ ] Testing after each phase
4. [ ] Documentation updates

---

## Resources

### **Documentation**
- Current SPEC-088: `specs/088-api-versioning-strategy/`
- External docs: `shared/contracts/docs/VERSIONING_STRATEGY.md`
- Related SPECs: SPEC-087, SPEC-089, SPEC-003, SPEC-100

### **Implementation**
- Middleware: `lib/middleware/api_versioning.py` (to be created)
- Routing: `lib/routing/version_router.py` (to be created)
- OpenAPI: `lib/openapi/versioned_schema.py` (to be created)

### **Testing**
- Version tests: `tests/test_api_versioning.py` (to be created)
- Compatibility tests: `tests/test_version_compatibility.py` (to be created)

### **References**
- FastAPI versioning: https://fastapi.tiangolo.com/advanced/sub-applications/
- Semantic versioning: https://semver.org/
- API versioning best practices: https://restfulapi.net/versioning/

---

## Conclusion

SPEC-088 is currently incomplete (~10-15%) but has a clear path to completion. The action plan provides:

1. ✅ **Clear phases** with specific deliverables
2. ✅ **Realistic timeline** (3-5 days)
3. ✅ **Prioritized tasks** (documentation first)
4. ✅ **Risk mitigation** strategies
5. ✅ **Success criteria** for validation

**Priority**: Complete documentation (Phase 1) first to establish authoritative source, then build infrastructure (Phase 2) to enable systematic versioning.

**Status**: Ready for developer assignment and implementation.

---

**Document Created**: November 2, 2025 3:10 AM
**Status**: 📋 **READY FOR IMPLEMENTATION**
**Owner**: TBD
**US**: #568
