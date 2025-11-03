#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#462 (SPEC-085) story in Taiga with comprehensive status information"""

import os
import sys
from datetime import datetime

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def get_updated_description():
    """Get comprehensive description for US#462"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
# SPEC-085: Staff Management - Current Status

**Last Updated**: {timestamp}
**Status**: ⚠️ **IN PROGRESS** (Not Complete - Ready for Pickup)

---

## 📋 Executive Summary

SPEC-085 (Staff Management System) has **significant implementation** but is **NOT FUNCTIONAL** due to critical integration issues. The code exists, but the API endpoints are not accessible because routers are not registered in the main application.

**Ready for someone to pick up?** ✅ **YES** - Clear tasks, well-defined scope, estimated 4-8 hours to complete.

---

## ✅ What EXISTS (Complete Implementation)

### 1. Database Schema ✅
- **Migration**: `alembic/versions/0112_staff_management.py`
- **Tables**: `staff`, `staff_activity_log`, `staff_permissions`
- **Status**: Migration exists and appears complete

### 2. API Implementation ✅
**Staff Management API** (`server/staff_management_api.py`):
- ✅ POST `/admin/staff` - Create staff account
- ✅ GET `/admin/staff` - List staff (with filters)
- ✅ GET `/admin/staff/{{id}}` - Get staff details
- ✅ PUT `/admin/staff/{{id}}/role` - Update role
- ✅ DELETE `/admin/staff/{{id}}` - Deactivate staff
- ✅ GET `/admin/staff/{{id}}/activity` - View activity log

**Staff Authentication API** (`server/staff_auth_api.py`):
- ✅ POST `/auth/staff/login` - Staff login with JWT
- ⚠️ POST `/auth/staff/reset-password` - **NOT IMPLEMENTED** (returns 501)
- ✅ POST `/auth/staff/logout` - Logout endpoint

### 3. UI Components ✅
- ✅ `frontend/admin/staff-login.html` - Complete staff login page
- ✅ `frontend/admin/staff-management.html` - Staff management interface

### 4. Supporting Files ✅
- ✅ `scripts/seed_initial_staff.py` - Seed script for initial admin
- ✅ Role-based permissions system (code-level)

---

## ❌ Critical Issues (Blocking Functionality)

### Issue #1: Routers NOT Registered ⚠️ **BLOCKER**
**Problem**: Staff routers are never included in FastAPI app
**Location**: `server/main.py` - Missing imports and `app.include_router()` calls
**Impact**: **ALL staff API endpoints are completely inaccessible**

**Expected Fix** (around line 399-404):
```python
# SPEC-085: Staff Management System
from staff_management_api import router as staff_management_router
from staff_auth_api import router as staff_auth_router

app.include_router(staff_management_router)
app.include_router(staff_auth_router)
```

### Issue #2: Router Prefix Typo ⚠️ **BLOCKER**
**Problem**: Staff management router has incorrect prefix
**File**: `server/staff_management_api.py:29`
**Current**: `router = APIRouter(prefix="/admin/sta", ...)`
**Should be**: `router = APIRouter(prefix="/admin/staff", ...)`
**Impact**: Even if registered, endpoints would be at wrong URLs

### Issue #3: Code Quality Issues
**Location**: `server/staff_management_api.py`
- Multiple "sta" typos that should be "staff" in comments and log messages
- Cosmetic but should be fixed for consistency

### Issue #4: Incomplete Password Reset
**Location**: `server/staff_auth_api.py:265-285`
- Password reset endpoint returns `501 NOT IMPLEMENTED`
- Authentication dependency missing (TODO comment exists)

### Issue #5: Authentication Dependency Mock
**Location**: `server/staff_management_api.py:34-38`
- `require_admin_role()` function is a mock that always returns admin
- TODO comment: "Add proper RBAC integration later"
- Needs real JWT token verification and role checking

---

## 📋 Remaining Work Checklist

### Critical (Must Fix - 30-60 minutes)
- [ ] **Fix router prefix typo** in `staff_management_api.py:29`
  - Change `/admin/sta` → `/admin/staff`
  - **Estimated**: 2 minutes

- [ ] **Register routers in `server/main.py`**
  - Add imports for `staff_management_api` and `staff_auth_api`
  - Add `app.include_router()` calls for both routers
  - Place after other admin routers (around line 400-410)
  - **Estimated**: 5 minutes

- [ ] **Test router registration**
  - Verify endpoints accessible via FastAPI `/docs` or `/redoc`
  - Check `/admin/staff` and `/auth/staff` endpoints appear
  - **Estimated**: 10 minutes

- [ ] **Fix code quality issues** (cosmetic)
  - Replace all "sta" references with "staff" in comments and logs
  - **Estimated**: 15 minutes

### Important (Should Fix - 2-4 hours)
- [ ] **Implement proper JWT authentication**
  - Replace mock `require_admin_role()` with real JWT verification
  - Integrate with existing auth system
  - Add role-based access checks
  - **Estimated**: 2-3 hours

- [ ] **Complete password reset endpoint**
  - Implement JWT token extraction from request
  - Add current password verification
  - Implement password update with hash
  - Add audit logging
  - **Estimated**: 1-2 hours

- [ ] **Test database migration**
  - Verify migration 0112 has been run
  - Check tables exist: `staff`, `staff_activity_log`, `staff_permissions`
  - **Estimated**: 10 minutes

### Nice to Have (Optional - 2-4 hours)
- [ ] **Email notification implementation**
  - Send welcome email with temporary password
  - Send password expiry warnings
  - **Estimated**: 2-3 hours

- [ ] **Integration testing**
  - End-to-end test: Create staff → Login → Access management UI
  - Test all CRUD operations
  - Test role-based access control
  - **Estimated**: 1-2 hours

- [ ] **Documentation updates**
  - Verify SPEC_INDEX.md status is correct
  - Update any outdated documentation
  - **Estimated**: 15 minutes

---

## 📊 Estimated Time to Completion

| Task Category | Estimated Time |
|--------------|----------------|
| **Critical Fixes** (router registration, prefix fix, testing) | 30 minutes - 1 hour |
| **Authentication Implementation** | 2-3 hours |
| **Password Reset Completion** | 1-2 hours |
| **Code Quality Fixes** | 15-30 minutes |
| **Integration Testing** | 1-2 hours |
| **Documentation/Story Updates** | 30-45 minutes |
| **Total (All Tasks)** | **4-8 hours** |
| **Total (Critical Only)** | **30 minutes - 1 hour** |

---

## 🎯 Recommended Approach

### Phase 1: Make It Work (30-60 minutes) - **START HERE**
1. Fix router prefix typo
2. Register routers in main.py
3. Test endpoints are accessible
4. Run database migration if needed
5. Test basic login flow

**Result**: System becomes functional (even with mock auth)

### Phase 2: Make It Secure (2-4 hours)
1. Implement real JWT authentication
2. Add role-based access control
3. Complete password reset endpoint
4. Test authentication flow

**Result**: Production-ready authentication

### Phase 3: Polish & Document (1-2 hours)
1. Fix code quality issues
2. Update documentation
3. Integration testing

**Result**: Complete, documented implementation

---

## 📝 Files to Modify

### High Priority
1. `server/main.py` - Add router registration (2-5 lines)
2. `server/staff_management_api.py` - Fix prefix typo and "sta" references
3. `server/staff_auth_api.py` - Implement password reset (if doing Phase 2)

### Medium Priority
4. `server/staff_management_api.py` - Implement real JWT auth (if doing Phase 2)
5. Documentation updates

---

## 🔗 Related Files & References

### Implementation Files
- `server/staff_management_api.py` - Staff CRUD operations
- `server/staff_auth_api.py` - Staff authentication
- `alembic/versions/0112_staff_management.py` - Database migration
- `frontend/admin/staff-login.html` - Login UI
- `frontend/admin/staff-management.html` - Management UI
- `scripts/seed_initial_staff.py` - Seed script

### Documentation
- `specs/085-staff-management/README.md` - Full specification
- `docs/spec-analysis/SPEC_085_CURRENT_STATUS_AND_NEXT_STEPS.md` - Detailed status document

### Related SPECs
- **SPEC-006**: User Management (for customers) - Complementary
- **SPEC-005**: Admin Dashboard - Uses staff management
- **SPEC-025**: Vendor Admin Console - Uses staff management
- **SPEC-083**: Product Surface Split - Admin console separation

---

## ✅ Success Criteria

SPEC-085 will be considered **COMPLETE** when:

1. ✅ All API endpoints are accessible and functional
2. ✅ Staff can log in via `/auth/staff/login`
3. ✅ Admins can create staff via `/admin/staff` POST
4. ✅ Admins can view staff list via `/admin/staff` GET
5. ✅ Staff management UI works end-to-end
6. ✅ Authentication uses real JWT tokens (not mocks)
7. ✅ Password reset works (if implementing Phase 2)
8. ✅ Database migration has been applied
9. ✅ Taiga story updated with completion status

---

## ⚠️ Important Notes

1. **Status Discrepancy**: Some documentation says SPEC-085 is "Complete" or story is "Done", but the actual implementation is incomplete. This story correctly shows "In Progress".

2. **Previous Fix Attempt**: There's a document (`SPEC_085_FIXES_APPLIED.md`) that claims fixes were applied on 2025-01-27, but those fixes were **NOT actually applied to the codebase**.

3. **Mock Authentication**: The current implementation uses a mock authentication function. This is acceptable for Phase 1 (making it work), but Phase 2 requires real JWT authentication integration.

4. **Database Migration**: Verify the migration has been run. If not, run:
   ```bash
   alembic upgrade head
   ```

---

**For detailed information, see**: `docs/spec-analysis/SPEC_085_CURRENT_STATUS_AND_NEXT_STEPS.md`
"""


def main():
    """Update US#462 story in Taiga"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#462
    story_ref = 462
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: {story.get('subject', 'N/A')}")
    print(f"   Current version: {story.get('version')}")

    # Get updated description
    new_description = get_updated_description()

    # Update story
    updates = {
        "description": new_description,
    }

    print(f"\n📝 Updating US#{story_ref} with comprehensive status information...")

    try:
        updated_story = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if updated_story:
            print(f"✅ Story US#{story_ref} updated successfully!")
            print(f"   New version: {updated_story.get('version')}")
            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
        else:
            print(f"❌ Failed to update story US#{story_ref}")

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return

    print(f"\n📋 Summary:")
    print(f"   - Status remains: In Progress")
    print(f"   - Description updated with comprehensive status")
    print(f"   - Ready for developer pickup")


if __name__ == "__main__":
    main()
