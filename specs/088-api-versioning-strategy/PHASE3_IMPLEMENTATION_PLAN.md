# SPEC-088 Phase 3: Systematic Implementation Plan

**Date**: November 2, 2025
**Status**: Ready for implementation
**Scope**: Apply `/api/v1/` prefix to all existing endpoints

---

## Current Situation

**Discovery**: The codebase has **50+ API routers** currently registered without version prefixes.

**Main Application**: `/server/main.py` (744 lines)
- 50+ router imports
- No versioning middleware currently applied
- Routers registered directly without prefixes

---

## Implementation Strategy

### Option 1: Gradual Migration (RECOMMENDED)

**Approach**: Add versioning infrastructure without breaking existing endpoints

**Steps**:
1. Add versioning middleware (non-breaking)
2. Create v1 versions of critical endpoints
3. Keep unversioned endpoints working (backward compatibility)
4. Gradually migrate clients to v1
5. Eventually deprecate unversioned endpoints

**Pros**:
- ✅ Zero downtime
- ✅ Backward compatible
- ✅ Can test incrementally
- ✅ Safe for production

**Cons**:
- ⏱️ Takes longer
- 📝 More documentation needed

---

### Option 2: Big Bang Migration (NOT RECOMMENDED)

**Approach**: Apply `/api/v1/` prefix to all endpoints at once

**Pros**:
- ✅ Clean and consistent immediately
- ✅ Faster implementation

**Cons**:
- ❌ Breaks all existing clients
- ❌ Requires coordinated deployment
- ❌ High risk
- ❌ Not suitable for production

---

## Recommended Approach: Gradual Migration

### Phase 3A: Infrastructure Setup (30 minutes)

1. **Add versioning middleware to main.py**
   ```python
   from lib.middleware.api_versioning import APIVersioningMiddleware

   app.add_middleware(APIVersioningMiddleware)
   ```

2. **Configure middleware to allow unversioned endpoints**
   - Modify middleware to skip non-`/api/` paths
   - Already implemented in current middleware

3. **Test middleware doesn't break existing endpoints**

---

### Phase 3B: Create V1 Routers for Critical Endpoints (2-3 hours)

**Priority 1: Authentication & Core** (30 min)
- `/auth/` → `/api/v1/auth/`
- `/users` → `/api/v1/users`
- `/health` → Keep unversioned (monitoring)
- `/metrics` → Keep unversioned (monitoring)

**Priority 2: Memory System** (1 hour)
- `/memory/` → `/api/v1/memory/`
- `/contexts` → `/api/v1/contexts`
- `/memories` → `/api/v1/memories`

**Priority 3: Teams & Organizations** (1 hour)
- `/teams` → `/api/v1/teams`
- `/organizations` → `/api/v1/organizations`

**Priority 4: Business APIs** (30 min)
- `/billing` → `/api/v1/billing`
- `/invoices` → `/api/v1/invoices`

---

### Phase 3C: Documentation & Testing (1 hour)

1. **Update OpenAPI documentation**
   - Generate separate schemas for v1
   - Update Swagger UI to show v1 endpoints

2. **Create migration guide for clients**
   - Document new v1 endpoints
   - Provide migration timeline
   - Share code examples

3. **Test all v1 endpoints**
   - Verify functionality
   - Check response formats
   - Test error handling

---

### Phase 3D: Deprecation Notice (ongoing)

1. **Add deprecation warnings to unversioned endpoints**
   - Custom middleware or decorator
   - Return deprecation headers
   - Log usage for monitoring

2. **Monitor usage**
   - Track which clients still use unversioned endpoints
   - Reach out to heavy users
   - Provide migration support

3. **Set sunset date**
   - 60-90 days after v1 launch
   - Communicate clearly
   - Send reminders

---

## Implementation Code

### Step 1: Add Middleware

```python
# In server/main.py, after CORS middleware (line ~213)

# Add API versioning middleware
from lib.middleware.api_versioning import APIVersioningMiddleware
app.add_middleware(APIVersioningMiddleware)
logger.info("✅ API versioning middleware installed")
```

### Step 2: Create V1 Router Example

```python
# Example: Create v1 auth router
from lib.routing.version_router import create_v1_router

# Create v1 version of auth router
v1_auth_router = create_v1_router(prefix="/auth", tags=["v1", "auth"])

# Copy endpoints from existing auth_working_router to v1_auth_router
# ... (endpoint definitions)

# Include both routers (for backward compatibility)
app.include_router(auth_working_router)  # Unversioned (deprecated)
app.include_router(v1_auth_router)  # V1 (current)
```

### Step 3: Add Deprecation Warning

```python
# Create deprecation middleware for unversioned endpoints
from lib.versioning.deprecation import deprecate_version, DeprecationTimeline

# Deprecate unversioned endpoints
deprecate_version(
    version="unversioned",
    timeline=DeprecationTimeline.EXTENDED,  # 90 days
    replacement_version="1",
    reason="Moving to versioned API for better stability"
)
```

---

## Router Inventory

### Critical Routers (Must migrate first)

1. `auth_working_router` - Authentication
2. `users_router` - User management
3. `memory_router` - Memory CRUD
4. `memory_system_router` - Memory system
5. `contexts_router` - Context management
6. `teams_router` - Team management
7. `organizations_router` - Organization management

### Business Routers (High priority)

8. `billing_console_router` - Billing
9. `invoice_management_router` - Invoices
10. `usage_analytics_router` - Analytics
11. `team_billing_portal_router` - Team billing

### Feature Routers (Medium priority)

12. `dashboard_router` - Dashboard widgets
13. `insights_router` - Insights
14. `gamification_router` - Gamification
15. `ai_feedback_router` - AI feedback
16. `memory_suggestions_router` - Suggestions

### Admin Routers (Lower priority)

17. `vendor_admin_router` - Vendor admin
18. `admin_analytics_router` - Admin analytics
19. `admin_activity_router` - Admin activity

### Specialized Routers (Can wait)

20-50. Various specialized routers (graph, compliance, etc.)

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_api_versioning.py
def test_v1_endpoint_accessible():
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert response.headers["X-API-Version"] == "v1"

def test_unversioned_endpoint_deprecated():
    response = client.get("/users")
    assert response.status_code == 200
    assert "X-API-Deprecated" in response.headers
```

### Integration Tests

```python
# tests/integration/test_versioned_api.py
def test_auth_flow_v1():
    # Test complete auth flow with v1 endpoints
    signup_response = client.post("/api/v1/auth/signup", json={...})
    login_response = client.post("/api/v1/auth/login", json={...})
    assert login_response.status_code == 200
```

---

## Timeline

### Week 1: Infrastructure & Critical Endpoints
- **Day 1**: Add middleware, create v1 auth/users (2-3 hours)
- **Day 2**: Create v1 memory/contexts (2-3 hours)
- **Day 3**: Create v1 teams/organizations (2-3 hours)
- **Day 4**: Testing and documentation (2-3 hours)
- **Day 5**: Deploy to staging, monitor (1 hour)

### Week 2: Business & Feature Endpoints
- **Day 1-2**: Create v1 billing/analytics routers
- **Day 3-4**: Create v1 feature routers
- **Day 5**: Testing and deployment

### Week 3: Remaining Endpoints & Cleanup
- **Day 1-3**: Create v1 for remaining routers
- **Day 4**: Final testing
- **Day 5**: Production deployment

### Week 4-12: Deprecation Period
- Monitor usage of unversioned endpoints
- Support client migrations
- Send deprecation reminders

### Week 13: Sunset Unversioned Endpoints
- Remove unversioned endpoints
- All clients must use v1

---

## Rollback Plan

If issues arise:

1. **Immediate**: Disable versioning middleware
   ```python
   # Comment out in main.py
   # app.add_middleware(APIVersioningMiddleware)
   ```

2. **Short-term**: Keep both versioned and unversioned endpoints
   - No breaking changes
   - Clients can use either

3. **Long-term**: Fix issues, re-enable gradually

---

## Success Metrics

- ✅ All critical endpoints have v1 versions
- ✅ No breaking changes to existing clients
- ✅ 100% test coverage for v1 endpoints
- ✅ Documentation updated
- ✅ Migration guide published
- ✅ Zero production incidents

---

## Next Steps

1. **Review this plan** with team
2. **Get approval** for gradual migration approach
3. **Start Phase 3A**: Add middleware (30 min)
4. **Continue Phase 3B**: Create v1 routers (incremental)

---

**Status**: Ready for implementation
**Estimated Time**: 2-3 weeks for complete migration
**Risk Level**: Low (gradual approach)
**Backward Compatibility**: Maintained throughout

---

**Questions?** Review:
- [SPEC-088 README](./README.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [Examples](../lib/versioning/examples.py)
