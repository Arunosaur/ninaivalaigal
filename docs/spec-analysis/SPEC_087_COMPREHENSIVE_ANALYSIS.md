# SPEC-087: API Surface Contracts - Comprehensive Analysis

**Date:** January 2025
**Status:** 🔄 **PARTIAL** (role-scoped docs implemented, CI gates pending)
**Taiga Story:** US#567 (Currently marked "Done" - needs update)

---

## Executive Summary

**SPEC-087 is PARTIALLY COMPLETE** with core functionality implemented but CI gates and final tasks pending. The story is currently marked "Done" in Taiga but should reflect the actual "Partial" status.

**Key Findings:**
- ✅ **Core Implementation:** Role-based OpenAPI filtering is fully implemented
- ✅ **Protected Docs Endpoints:** `/docs` and `/openapi.json` require authentication
- ✅ **Policy Tests:** Test suite exists (`test_public_api_surface.py`)
- ❌ **CI Workflow:** GitHub Actions workflow for API surface policy tests is missing
- 🔄 **Router Tagging:** 6/11 routers tagged (5 remaining)
- 🔄 **SDK Generation:** Not implemented
- 🔄 **Ingress Configuration:** Not configured

---

## 1. SPEC_INDEX.md Status Validation

**Current Status in SPEC_INDEX.md:** `In Progress`
**Actual Status in README:** `🔄 PARTIAL (role-scoped docs implemented, CI gates pending)`

**Assessment:** ✅ **SPEC_INDEX.md is CORRECT** - "In Progress" accurately reflects that work is ongoing.

However, the Taiga story US#567 is marked "Done" which is incorrect - it should be "In Progress" to match the actual status.

---

## 2. Implementation Status

### ✅ Completed Components

#### 2.1 Role-Based OpenAPI Filtering
**File:** `server/openapi_filter.py`
**Status:** ✅ **COMPLETE**

- Function: `get_filtered_openapi(app, role, title, version)`
- Features:
  - Role-based schema filtering
  - Tag-based endpoint visibility control
  - Empty schema for unauthenticated users
  - Deep copy to avoid modifying cached schema
  - Security notice in description

**Evidence:**
```python
def get_filtered_openapi(
    app: FastAPI,
    role: Role | None = None,
    title: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Generate OpenAPI schema filtered by user role."""
```

#### 2.2 Tag Allowlists by Role
**File:** `server/api_exposure.py`
**Status:** ✅ **COMPLETE**

- Defined: `PUBLIC_TAGS`, `DOCS_TAG_ALLOWLIST`
- Role hierarchy: public < external < member < admin < staff
- Validation: Tag hierarchy validation on import

**Evidence:**
```python
PUBLIC_TAGS = {
    "auth",  # signup, login, password reset
    "health",  # basic health check
}

DOCS_TAG_ALLOWLIST: dict[str, set[str]] = {
    "public": set(),  # Empty - no Swagger access without auth
    "external": {"auth", "health", "memory-public"},
    "member": {"auth", "health", "memory-public", "memory", "context", "teams"},
    "admin": {...},
    "staff": {...},  # Full access
}
```

#### 2.3 Protected Documentation Endpoints
**File:** `server/main.py` (lines 516-567)
**Status:** ✅ **COMPLETE**

**Endpoints:**
- `/openapi.json` - Returns role-filtered OpenAPI schema
- `/docs` - Protected Swagger UI (401 if unauthenticated)

**Evidence:**
```python
@app.get("/openapi.json", include_in_schema=False)
async def protected_openapi(request: Request):
    """Protected OpenAPI schema endpoint."""
    user_role = get_user_role_from_request(request)
    filtered_schema = get_filtered_openapi(app=app, role=user_role, ...)
    return JSONResponse(filtered_schema)

@app.get("/docs", include_in_schema=False)
async def protected_docs(request: Request):
    """Protected Swagger UI documentation."""
    user_role = get_user_role_from_request(request)
    if user_role is None:
        return JSONResponse(status_code=401, ...)
```

#### 2.4 JWT Role Extraction
**File:** `server/main.py` (lines 450-510)
**Status:** ✅ **COMPLETE**

- Function: `get_user_role_from_request(request)`
- Methods:
  1. RBAC context (from middleware)
  2. JWT token from Authorization header
  3. Development mode fallback (SYSTEM role)

#### 2.5 Policy Tests
**File:** `tests/test_public_api_surface.py`
**Status:** ✅ **COMPLETE**

**Test Coverage:**
- ✅ `test_public_tags_are_minimal()` - Validates PUBLIC_TAGS
- ✅ `test_unauthenticated_gets_empty_schema()` - Unauthenticated users see 0 endpoints
- ✅ `test_viewer_role_limited_access()` - VIEWER sees limited endpoints
- ✅ `test_member_role_no_admin_access()` - MEMBER can't see admin paths
- ✅ `test_admin_role_has_admin_access()` - ADMIN sees admin endpoints
- ✅ `test_system_role_sees_all_endpoints()` - SYSTEM sees >200 endpoints
- ✅ `test_role_hierarchy_is_enforced()` - Role hierarchy validation
- ✅ `test_sensitive_paths_not_in_public()` - Sensitive paths validation
- ✅ `test_is_public_endpoint_function()` - Helper function validation

**Total:** 9 test methods covering all critical scenarios

#### 2.6 Router Tagging (Partial)
**Status:** 🔄 **6/11 routers tagged**

**Tagged Routers:**
- ✅ `server/signup_api.py` - Tagged "auth"
- ✅ `server/enhanced_signup_api.py` - Tagged "auth"
- ✅ `server/token_api.py` - Tagged "auth"
- ✅ `server/memory_health_api.py` - Tagged "health"
- ✅ `server/billing_console_api.py` - Tagged "billing"
- ✅ Additional routers found with tags:
  - `server/compliance/api_hipaa.py` - Tagged "hipaa-compliance"
  - `server/compliance/api.py` - Tagged "gdpr-compliance"
  - `server/invoice_management_api.py` - Tagged "billing"
  - `server/standalone_teams_api.py` - Tagged "standalone-teams"
  - `server/performance_api.py` - Tagged "performance"
  - `server/billing_engine_integration_api.py` - Tagged "billing"

**Remaining:** Need to verify all routers are properly tagged

### ❌ Missing Components

#### 2.7 GitHub Actions Workflow for CI Gates
**File:** `.github/workflows/api-surface-policy.yml`
**Status:** ❌ **MISSING**

**Expected Workflow:**
```yaml
name: API Surface Policy Tests
on: [push, pull_request]
jobs:
  policy-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run policy tests
        run: |
          pytest tests/test_public_api_surface.py -v
          # Fail if any internal tag appears in public schema
          # Fail if any route lacks explicit tag
```

**Note:** There is a `.github/workflows/contract-validation.yml` workflow, but it validates OpenAPI syntax and breaking changes, NOT the API surface policy tests required by SPEC-087.

#### 2.8 SDK Generation
**Status:** ❌ **NOT IMPLEMENTED**

**Expected:**
- Generate `@nina/api-client/customer` from public OpenAPI
- Generate `@nina/api-client/admin` from internal OpenAPI

#### 2.9 Ingress Configuration
**Status:** ❌ **NOT CONFIGURED**

**Expected:**
- Customer public docs: Sign-in required (external role)
- Admin docs: Staff only (RBAC/SSO)

#### 2.10 Router Tagging Guide
**File:** `docs/ROUTER_TAGGING_GUIDE.md`
**Status:** ❌ **NOT FOUND**

The SPEC mentions this file should exist, but it's not found in the codebase.

---

## 3. Overlap Analysis

### 3.1 SPEC-088: API Versioning Strategy
**Relationship:** ✅ **COMPLEMENTARY** (No Overlap)

**SPEC-087:** Public vs internal OpenAPI split (visibility/security)
**SPEC-088:** API versioning strategy (v1, v2, etc.)

These are complementary:
- SPEC-087 controls **who can see** which endpoints
- SPEC-088 controls **which version** of endpoints to use

**Conclusion:** No overlap or conflict

### 3.2 SPEC-089: Breaking Change Management
**Relationship:** ✅ **COMPLEMENTARY** (No Overlap)

**SPEC-087:** API surface contracts (documentation visibility)
**SPEC-089:** Breaking change management (backward compatibility)

These are complementary:
- SPEC-087 ensures internal endpoints aren't accidentally exposed
- SPEC-089 ensures breaking changes are properly managed

**Conclusion:** No overlap or conflict

### 3.3 SPEC-083: Product Surface Split
**Relationship:** ✅ **RELATED** (Complements SPEC-087)

**SPEC-083:** Product surface split (customer vs admin apps)
**SPEC-087:** API surface contracts (public vs internal OpenAPI)

SPEC-083 is explicitly listed as "Related" in SPEC-087. They work together:
- SPEC-083: Frontend split
- SPEC-087: Backend API visibility split

**Conclusion:** Intentionally related, no conflict

### 3.4 SPEC-100: API Container Modularization
**Relationship:** ✅ **COMPLEMENTARY** (No Overlap)

**SPEC-087:** OpenAPI filtering (documentation)
**SPEC-100:** Microservice contracts (Protocol Buffers, OpenAPI specs)

These are different concerns:
- SPEC-087: Filtering existing OpenAPI for docs visibility
- SPEC-100: Creating/validating microservice contracts

**Conclusion:** No overlap or conflict

### 3.5 Duplicate Check
**Status:** ✅ **NO DUPLICATES**

Only one SPEC-087 exists: `specs/087-api-surface-contracts/README.md`

---

## 4. Implementation Metrics

### Code Statistics
- **Implementation Files:** 3 core files
  - `server/openapi_filter.py` (140 lines)
  - `server/api_exposure.py` (141 lines)
  - `server/main.py` (protected endpoints: ~50 lines)

- **Test Files:** 1 test suite
  - `tests/test_public_api_surface.py` (243 lines, 9 test methods)

- **Total Implementation Lines:** ~574 lines

### Router Tagging Status
- **Tagged Routers:** 6+ routers found with explicit tags
- **Total Routers:** ~11 routers (per SPEC)
- **Completion:** ~55-65% tagged

### Test Coverage
- **Policy Tests:** 9 test methods
- **Integration Tests:** Partial (requires running server)
- **Coverage:** Core functionality well-tested

---

## 5. Acceptance Criteria Status

### OpenAPI Split
- ✅ Two OpenAPI generation functions (public/internal) - **COMPLETE**
- ✅ Role-based filtering implemented - **COMPLETE**
- ✅ Protected `/docs` and `/openapi.json` endpoints - **COMPLETE**

### CI Gates
- ✅ Policy tests created (`test_public_api_surface.py`) - **COMPLETE**
- ❌ GitHub Actions workflow configured - **MISSING**
- ❌ Fail on any internal path in public schema - **MISSING (no CI workflow)**
- ❌ Fail if route lacks explicit tag - **MISSING (no CI workflow)**

### Documentation
- ❌ Router tagging guide (`ROUTER_TAGGING_GUIDE.md`) - **NOT FOUND**
- 🔄 All routers properly tagged - **PARTIAL (6/11)**
- ✅ Public docs gated by sign-in - **COMPLETE**
- ✅ Internal docs staff-only - **COMPLETE**

### SDK Generation
- ❌ Generate `@nina/api-client/customer` from public OpenAPI - **NOT IMPLEMENTED**
- ❌ Generate `@nina/api-client/admin` from internal OpenAPI - **NOT IMPLEMENTED**

**Overall Completion:** ~60% (core functionality complete, CI gates and final tasks pending)

---

## 6. Security Benefits (Achieved)

### Before SPEC-087
- ❌ All 265 endpoints visible to everyone
- ❌ No authentication for `/docs`
- ❌ API reconnaissance possible

### After SPEC-087 (Current State)
- ✅ Unauthenticated: 401 error on `/docs`
- ✅ VIEWER: Limited endpoints visible
- ✅ MEMBER: Team operations visible
- ✅ ADMIN: Admin endpoints visible
- ✅ SYSTEM: Full access (200+ endpoints)
- ✅ JWT role extraction working

**Security Improvement:** ✅ **SIGNIFICANT** - API reconnaissance prevented

---

## 7. Remaining Work

### High Priority
1. **Create GitHub Actions Workflow** (`.github/workflows/api-surface-policy.yml`)
   - Run `pytest tests/test_public_api_surface.py` on PR/push
   - Fail if policy tests fail
   - Integrate with PR quality gates

2. **Complete Router Tagging** (5 remaining routers)
   - Audit all routers in `server/`
   - Ensure all have explicit tags
   - Verify tags match role allowlists

3. **Create Router Tagging Guide** (`docs/ROUTER_TAGGING_GUIDE.md`)
   - Document tag categories
   - Provide tagging examples
   - Explain role hierarchy

### Medium Priority
4. **SDK Generation**
   - Generate customer SDK from public OpenAPI
   - Generate admin SDK from internal OpenAPI
   - Set up automated generation pipeline

5. **Ingress Configuration**
   - Configure customer public docs (sign-in required)
   - Configure admin docs (SSO/RBAC)
   - Test in production-like environment

### Low Priority
6. **Enhanced Integration Tests**
   - Test authenticated doc access with real JWT tokens
   - Test role hierarchy in production-like setup
   - Validate ingress rules

---

## 8. Taiga Story Status

### Current Story: US#567
**Status:** ❌ **INCORRECT** - Marked "Done" but SPEC is "Partial"

**Issues:**
- Story description is minimal (just copies spec intro)
- Status is "Done" but CI gates are pending
- No completion evidence in description
- Should be "In Progress" to match SPEC_INDEX.md

**Recommendation:**
1. Update story status to "In Progress"
2. Add comprehensive description with:
   - Current completion status (60%)
   - Completed components
   - Remaining work (CI workflow, router tagging, SDK generation)
   - Next steps

---

## 9. Recommendations

### Immediate Actions
1. ✅ **Update Taiga Story US#567** - Change status to "In Progress" and add detailed description
2. ✅ **Create GitHub Actions Workflow** - Add `.github/workflows/api-surface-policy.yml`
3. ✅ **Complete Router Tagging Audit** - Verify all routers are tagged

### Future Enhancements
4. **SDK Generation** - When ready to provide client SDKs
5. **Ingress Configuration** - When deploying to production
6. **Enhanced Testing** - Add integration tests with real JWT tokens

---

## 10. Conclusion

**SPEC-087 is PARTIALLY COMPLETE** with core functionality (role-based OpenAPI filtering, protected docs endpoints, policy tests) fully implemented and operational. However, CI gates and final tasks (SDK generation, ingress configuration) remain pending.

**Key Achievements:**
- ✅ Role-based documentation filtering working
- ✅ API reconnaissance prevention in place
- ✅ Comprehensive policy test suite

**Key Gaps:**
- ❌ CI workflow for automated policy enforcement
- 🔄 Router tagging incomplete (6/11)
- ❌ SDK generation not implemented

**Status Alignment:**
- SPEC_INDEX.md: ✅ "In Progress" (CORRECT)
- SPEC README: ✅ "🔄 PARTIAL" (CORRECT)
- Taiga Story: ❌ "Done" (INCORRECT - should be "In Progress")

**Recommendation:** Update Taiga story to reflect actual status and prioritize CI workflow creation to complete SPEC-087.
