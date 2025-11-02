# US#159/US#203: Standalone Team CRUD APIs - Implementation Status

**Date:** November 1, 2025  
**Status:** In Progress  
**Story:** US#159/US#203 - Standalone Team CRUD APIs (SPEC-026 Phase 2)

---

## Requirements Summary

### API Endpoints Required:
1. ✅ POST /auth/signup/team-create - Create team during signup
2. ✅ POST /team/create-standalone - Create team from dashboard
3. ✅ GET /team/my - Get current user's team info
4. ⚠️ POST /team/invite - Send team invitation (needs team_id-less version)
5. ✅ POST /team/{id}/upgrade-to-org - Upgrade to organization

### Acceptance Criteria:
- [ ] All 5 endpoints implemented
- [ ] Request validation with Pydantic
- [ ] RBAC enforcement (team admin only)
- [ ] JWT authentication required
- [ ] Error handling (400, 401, 403, 404, 500)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Integration tests (100% endpoint coverage)
- [ ] Response times <200ms P95

---

## Current Implementation Status

### ✅ Already Implemented:

1. **POST /auth/signup/team-create**
   - **Location:** `server/enhanced_signup_api.py:115`
   - **Status:** Complete
   - **Features:**
     - Creates user account and team in one request
     - Pydantic validation
     - Email verification
     - Error handling

2. **POST /team/create-standalone**
   - **Location:** `server/standalone_teams_api.py:216`**
   - **Status:** Complete
   - **Features:**
     - JWT authentication ✅
     - Pydantic validation ✅
     - Checks for existing team ✅
     - Error handling ✅
   - **Needs:** RBAC decorator (currently manual checks)

3. **GET /team/my**
   - **Location:** `server/standalone_teams_api.py:270`
   - **Status:** Complete
   - **Features:**
     - JWT authentication ✅
     - Returns user's standalone team ✅
     - Handles both created teams and memberships ✅
   - **Needs:** None (looks good)

4. **POST /team/{team_id}/invite**
   - **Location:** `server/standalone_teams_api.py:318`
   - **Status:** Partial (exists with team_id)
   - **Features:**
     - JWT authentication ✅
     - RBAC check (manual) ✅
     - Email sending ✅
     - Error handling ✅
   - **Needs:** POST /team/invite (without team_id - uses user's current team)

5. **POST /team/{id}/upgrade-to-org**
   - **Location:** `server/standalone_teams_api.py:501`
   - **Status:** Complete
   - **Features:**
     - JWT authentication ✅
     - RBAC check (manual) ✅
     - Error handling ✅
   - **Needs:** RBAC decorator

---

## Implementation Tasks

### 1. Add POST /team/invite (team_id-less version)
- Use user's current team automatically
- Same logic as existing endpoint but without team_id parameter

### 2. Enhance RBAC Enforcement
- Add `@require_permission` decorators where appropriate
- Ensure team admin role is properly enforced
- Update manual checks to use decorators

### 3. Write Integration Tests
- Test all 5 endpoints
- Test authentication/authorization
- Test error cases (400, 401, 403, 404, 500)
- Test response times
- Achieve 100% endpoint coverage

### 4. Enhance API Documentation
- Ensure OpenAPI/Swagger docs are complete
- Add example requests/responses
- Document error responses

### 5. Performance Validation
- Verify response times <200ms P95

---

## Next Steps

1. Add POST /team/invite endpoint
2. Enhance existing endpoints with proper RBAC decorators
3. Write comprehensive integration tests
4. Update Taiga story with completion details

