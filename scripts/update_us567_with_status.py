#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#567 (SPEC-087) story with comprehensive status information"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#567 story with comprehensive SPEC-087 status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#567 is the story for SPEC-087
    story_ref = 567
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-087: API Surface Contracts")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    # Create comprehensive description
    description = """**SPEC-087: API Surface Contracts**

**Status:** 🔄 PARTIAL (role-scoped docs implemented, CI gates pending)
**Phase:** Phase 2B
**Completion:** ~60%

---

## ✅ Completed Components (Core Implementation)

### 1. Role-Based OpenAPI Filtering ✅
- **File:** `server/openapi_filter.py`
- Role-based schema filtering implemented
- Tag-based endpoint visibility control
- Empty schema for unauthenticated users

### 2. Tag Allowlists by Role ✅
- **File:** `server/api_exposure.py`
- Role hierarchy: public < external < member < admin < staff
- Tag hierarchy validation on import
- `PUBLIC_TAGS`, `DOCS_TAG_ALLOWLIST` defined

### 3. Protected Documentation Endpoints ✅
- **File:** `server/main.py`
- `/docs` - Protected Swagger UI (401 if unauthenticated)
- `/openapi.json` - Returns role-filtered OpenAPI schema
- JWT role extraction working

### 4. Policy Tests ✅
- **File:** `tests/test_public_api_surface.py`
- 9 test methods covering all critical scenarios
- Role hierarchy validation
- Sensitive paths validation
- Public tag validation

### 5. Router Tagging (Partial) 🔄
- 6+ routers tagged with explicit tags
- ~55-65% completion
- Examples: auth, health, billing, compliance tags

---

## ❌ Missing Components

### 1. GitHub Actions Workflow for CI Gates ❌
- **File:** `.github/workflows/api-surface-policy.yml` - MISSING
- Expected: Run `pytest tests/test_public_api_surface.py` on PR/push
- Expected: Fail if policy tests fail
- Note: `contract-validation.yml` exists but validates syntax, not surface policy

### 2. Router Tagging Guide ❌
- **File:** `docs/ROUTER_TAGGING_GUIDE.md` - NOT FOUND
- Should document tag categories and role hierarchy

### 3. Complete Router Tagging 🔄
- 5+ routers still need tagging verification
- Need audit of all routers in `server/`

### 4. SDK Generation ❌
- Generate `@nina/api-client/customer` from public OpenAPI - NOT IMPLEMENTED
- Generate `@nina/api-client/admin` from internal OpenAPI - NOT IMPLEMENTED

### 5. Ingress Configuration ❌
- Customer public docs (sign-in required) - NOT CONFIGURED
- Admin docs (SSO/RBAC) - NOT CONFIGURED

---

## 📊 Acceptance Criteria Status

### OpenAPI Split
- ✅ Two OpenAPI generation functions (public/internal) - COMPLETE
- ✅ Role-based filtering implemented - COMPLETE
- ✅ Protected `/docs` and `/openapi.json` endpoints - COMPLETE

### CI Gates
- ✅ Policy tests created - COMPLETE
- ❌ GitHub Actions workflow configured - MISSING
- ❌ Fail on any internal path in public schema - MISSING (no CI workflow)
- ❌ Fail if route lacks explicit tag - MISSING (no CI workflow)

### Documentation
- ❌ Router tagging guide - NOT FOUND
- 🔄 All routers properly tagged - PARTIAL (6/11)
- ✅ Public docs gated by sign-in - COMPLETE
- ✅ Internal docs staff-only - COMPLETE

### SDK Generation
- ❌ Generate customer SDK - NOT IMPLEMENTED
- ❌ Generate admin SDK - NOT IMPLEMENTED

**Overall Completion:** ~60%

---

## 🔒 Security Benefits (Achieved)

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

**Security Improvement:** ✅ SIGNIFICANT - API reconnaissance prevented

---

## 🎯 Next Steps (Priority Order)

### High Priority
1. **Create GitHub Actions Workflow** - `.github/workflows/api-surface-policy.yml`
   - Run policy tests on PR/push
   - Integrate with PR quality gates

2. **Complete Router Tagging** - Audit and tag all remaining routers

3. **Create Router Tagging Guide** - `docs/ROUTER_TAGGING_GUIDE.md`

### Medium Priority
4. **SDK Generation** - Generate client SDKs from OpenAPI specs
5. **Ingress Configuration** - Configure customer/admin docs access

---

## 📋 Related SPECs

- **SPEC-083:** Product Surface Split (Complements frontend split)
- **SPEC-088:** API Versioning Strategy (Complements - different concern)
- **SPEC-089:** Breaking Change Management (Complements - different concern)
- **SPEC-100:** API Container Modularization (Complements - different concern)

**No Overlaps:** All relationships are complementary, no conflicts identified.

---

## 📝 Implementation Evidence

**Core Files:**
- `server/openapi_filter.py` (140 lines)
- `server/api_exposure.py` (141 lines)
- `server/main.py` (protected endpoints: ~50 lines)
- `tests/test_public_api_surface.py` (243 lines, 9 test methods)

**Total Implementation:** ~574 lines

---

**Status Alignment:**
- SPEC_INDEX.md: ✅ "In Progress" (CORRECT)
- SPEC README: ✅ "🔄 PARTIAL" (CORRECT)
- This Story: Should be "In Progress" (not "Done")

**Recommendation:** Prioritize CI workflow creation to complete SPEC-087."""

    # Update story description
    print(f"\n📝 Updating US#{story_ref} with comprehensive status...")

    updates = {
        "description": description,
    }

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if result:
            print(f"✅ Story US#{story_ref} description updated successfully!")
            print(f"   New version: {result.get('version', 'Unknown')}")

            # Try to find "In Progress" status
            print(f"\n🔍 Finding 'In Progress' status...")
            project_id = story.get("project")

            # Get statuses using requests directly
            import requests

            status_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
            headers = importer._get_headers()
            status_response = requests.get(status_url, headers=headers)

            in_progress_status_id = None
            if status_response.status_code == 200:
                statuses = status_response.json()
                for status in statuses:
                    if isinstance(status, dict):
                        status_name = status.get("name", "").lower()
                        if "progress" in status_name or status_name == "in progress":
                            in_progress_status_id = status.get("id")
                            print(f"   Found: {status.get('name')} (ID: {in_progress_status_id})")
                            break

            if in_progress_status_id:
                print(f"\n📝 Updating status to 'In Progress'...")
                status_updates = {
                    "status": in_progress_status_id,
                }

                result2 = importer.update_user_story(
                    story_id=story["id"],
                    version=result.get("version", story.get("version", 1)),
                    updates=status_updates,
                    retry_on_version_conflict=True,
                    max_retries=3,
                )

                if result2:
                    print(f"✅ Status updated to 'In Progress'!")
                    print(f"   New version: {result2.get('version', 'Unknown')}")
                else:
                    print(f"⚠️  Status update may have failed")
            else:
                print(f"⚠️  Could not find 'In Progress' status")
                print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
                print(f"   Recommended: Manually change status to 'In Progress' in Taiga UI")
        else:
            print(f"❌ Failed to update story US#{story_ref}")

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n📋 Summary:")
    print(f"   - Description updated with comprehensive status")
    print(f"   - Status should be changed to 'In Progress'")
    print(f"   - Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")


if __name__ == "__main__":
    main()
