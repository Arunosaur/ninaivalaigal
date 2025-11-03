#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#569 (SPEC-089) story with comprehensive status information"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#569 story with comprehensive SPEC-089 status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#569 is the story for SPEC-089
    story_ref = 569
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-089: Breaking Change Management")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    # Create comprehensive description
    description = """**SPEC-089: Breaking Change Management**

**Status:** 🚨 CRITICAL MISMATCH (Implementation complete, SPEC directory missing)
**Phase:** Phase 3
**Completion:** ~70%

---

## 🚨 CRITICAL ISSUE: Directory Mismatch

**SPEC_INDEX.md says:** "Breaking Change Management"
**Directory exists:** `specs/089-white-label-platform/` (contains White-Label Platform content)
**Expected directory:** `specs/089-breaking-change-management/` (DOES NOT EXIST)

**Issue:** The directory `089-white-label-platform/` was incorrectly assigned to SPEC-089. This needs to be resolved.

---

## ✅ What Exists (Implementation Complete)

### 1. Breaking Change Detection Script ✅
**File:** `ci/check-breaking-changes.py` (175 lines)
- ✅ Detects breaking changes in OpenAPI specifications
- ✅ Compares contracts between git refs (base vs head)
- ✅ Checks for removed endpoints, methods, required parameters, schemas
- ✅ Creates CI marker file
- ✅ Integrated with `.github/workflows/contract-validation.yml`

**Features:**
- Detects removed endpoints
- Detects removed HTTP methods
- Detects new required parameters (breaking)
- Detects removed schemas
- Comprehensive error reporting

### 2. Breaking Change Documentation ✅
**File:** `shared/contracts/docs/BREAKING_CHANGES.md` (98 lines)
- ✅ Definition of breaking changes
- ✅ When breaking changes are allowed
- ✅ 8-step process for breaking changes:
  1. Justify
  2. Create New Version
  3. Write Migration Guide
  4. Get Approval
  5. Deploy Both Versions
  6. Communicate
  7. Monitor Migration
  8. Remove Old Version
- ✅ Review checklist
- ✅ Examples (good vs bad breaking changes)
- ✅ References to related docs

### 3. CI Integration ✅
**File:** `.github/workflows/contract-validation.yml`
- ✅ Breaking change detection runs on PR/push
- ✅ Fails build on breaking changes without version bump
- ✅ Comprehensive error reporting

---

## ❌ What's Missing

### 1. SPEC Directory Structure ❌
**Expected:** `specs/089-breaking-change-management/`
**Status:** DOES NOT EXIST

**Issue:** All implementation and documentation exists in external locations, not in SPEC directory structure.

### 2. Directory Mismatch 🚨
**Directory exists:** `specs/089-white-label-platform/`
**Content:** White-Label Platform (not Breaking Change Management)
**Issue:** This directory should be renumbered or replaced

### 3. Status Mismatches
- ❌ **Taiga story** marked "Done" (should be "Ready")
- ✅ **SPEC_INDEX.md** correctly shows "Planned"
- ❌ **Directory** contains wrong content

### 4. Documentation Consolidation Needed
- ⚠️ **Location mismatch:** Breaking change docs are in `shared/contracts/docs/` not in SPEC directory
- **Question:** Should docs stay in shared/contracts or move to SPEC?
- **Recommendation:** Create SPEC directory and cross-reference

---

## 📋 Implementation Evidence

### Breaking Change Detection
- **Script:** `ci/check-breaking-changes.py` (175 lines, complete)
- **Workflow:** `.github/workflows/contract-validation.yml` (integrated)
- **Coverage:** OpenAPI contract validation

### Documentation
- **Policy:** `shared/contracts/docs/BREAKING_CHANGES.md` (98 lines, comprehensive)
- **Related:** Referenced in VERSIONING.md, DEPRECATION.md, COMPATIBILITY.md

**Total Implementation:** ~273 lines (script + doc)

---

## 📊 Acceptance Criteria Status

### Breaking Change Detection
- ✅ Automated detection script - COMPLETE
- ✅ CI integration - COMPLETE
- ✅ Error reporting - COMPLETE

### Breaking Change Policy
- ✅ Definition of breaking changes - COMPLETE
- ✅ Process documentation - COMPLETE
- ✅ Review checklist - COMPLETE
- ✅ Examples - COMPLETE

### SPEC Structure
- ❌ SPEC directory - MISSING
- ❌ SPEC README - MISSING
- ❌ Cross-references - MISSING

**Overall Completion:** ~70% (implementation complete, SPEC structure missing)

---

## 🎯 Next Steps (Priority Order)

### Critical (Resolve First)
1. **Resolve Directory Mismatch** 🚨
   - Verify: Is `089-white-label-platform/` correctly numbered?
   - Verify: Is SPEC-140 correctly White-Label Platform?
   - Decision: Renumber directory or create correct one

2. **Create SPEC Directory**
   - Create `specs/089-breaking-change-management/`
   - Move or copy content from `shared/contracts/docs/BREAKING_CHANGES.md`
   - Create proper SPEC structure with README

3. **Update Taiga Story**
   - Change status from "Done" to "Ready"
   - Add comprehensive description with implementation evidence

### High Priority
4. **Consolidate Documentation**
   - Decide authoritative location (SPEC vs shared/contracts)
   - Cross-reference appropriately
   - Ensure single source of truth

5. **Coordinate with SPEC-088**
   - Ensure clear boundaries:
     - SPEC-088: Versioning scheme and infrastructure
     - SPEC-089: Breaking change detection and management process
   - Cross-reference appropriately

### Medium Priority
6. **Enhance Detection**
   - Add database schema breaking change detection
   - Add Protocol Buffer breaking change detection
   - Add more breaking change patterns

---

## 📝 Files That Need Work

### Critical (Directory Structure)
- Create `specs/089-breaking-change-management/` directory
- Create `specs/089-breaking-change-management/README.md` (SPEC doc)
- Resolve `specs/089-white-label-platform/` mismatch

### Documentation (Consolidation)
- Decide if `shared/contracts/docs/BREAKING_CHANGES.md` should:
  - Stay in shared/contracts (as reference)
  - Move to SPEC directory (as authoritative)
  - Both (with cross-references)

---

## 🔗 Related SPECs

- **SPEC-088:** API Versioning Strategy - Related (overlaps on deprecation/migration)
  - **Coordination needed:** Define clear boundaries
  - **SPEC-088:** Versioning scheme and infrastructure
  - **SPEC-089:** Breaking change detection and management process

- **SPEC-087:** API Surface Contracts - Complementary (different concern)
- **SPEC-003:** Core API Architecture - Complementary (foundation)
- **SPEC-100:** API Container Modularization - Complementary (different concern)

**Potential Overlap:** SPEC-088 and SPEC-089 both address deprecation/migration. Should coordinate.

---

## ⚠️ Important Notes

1. **Directory Mismatch:**
   - `specs/089-white-label-platform/` exists but contains White-Label Platform
   - SPEC_INDEX.md says SPEC-089 is "Breaking Change Management"
   - This is a CRITICAL mismatch that must be resolved

2. **Implementation Status:**
   - Breaking change detection script is COMPLETE and working
   - Documentation is COMPLETE in `shared/contracts/docs/`
   - SPEC directory structure is MISSING

3. **Status Discrepancies:**
   - Taiga story: Marked "Done" (incorrect)
   - SPEC_INDEX.md: Shows "Planned" (correct)
   - Directory: Wrong content (mismatch)

---

**Status Alignment:**
- SPEC_INDEX.md: ✅ "Breaking Change Management" (CORRECT)
- Directory: ❌ White-Label Platform content (MISMATCH)
- Taiga Story: ❌ "Done" (INCORRECT - should be "Ready")
- Implementation: ✅ Complete (detection script + docs)

**Recommendation:**
1. Resolve directory mismatch first (critical)
2. Create `089-breaking-change-management/` directory
3. Update Taiga story to "Ready" with comprehensive status
4. Coordinate with SPEC-088 to define boundaries

---

**For detailed analysis, see**: `docs/spec-analysis/SPEC_089_COMPREHENSIVE_ANALYSIS.md`

---

## ✅ SPEC Directory Created

**Directory:** `specs/089-breaking-change-management/`
**Status:** ✅ Created with comprehensive documentation
**Cross-References:** ✅ Established with SPEC-088

**Files Created:**
- `specs/089-breaking-change-management/README.md` - Complete SPEC documentation
- `specs/089-breaking-change-management/migration-guide-template.md` - Migration guide template

**SPEC-088 Updated:**
- `specs/088-api-versioning-strategy/breaking-changes.md` - Now references SPEC-089

**Coordination:**
- ✅ SPEC-089 references SPEC-088 for versioning scheme
- ✅ SPEC-088 references SPEC-089 for breaking change process
- ✅ Clear boundaries established between the two SPECs"""

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

            # Try to find "Ready" status (closest to "Planned")
            print(f"\n🔍 Finding 'Ready' status...")
            project_id = story.get("project")

            import requests

            status_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
            headers = importer._get_headers()
            status_response = requests.get(status_url, headers=headers)

            ready_status_id = None
            if status_response.status_code == 200:
                statuses = status_response.json()
                for status in statuses:
                    if isinstance(status, dict):
                        status_name = status.get("name", "").lower()
                        if "ready" in status_name or status_name == "ready":
                            ready_status_id = status.get("id")
                            print(f"   Found: {status.get('name')} (ID: {ready_status_id})")
                            break

            if ready_status_id:
                print(f"\n📝 Updating status to 'Ready'...")
                status_updates = {
                    "status": ready_status_id,
                }

                result2 = importer.update_user_story(
                    story_id=story["id"],
                    version=result.get("version", story.get("version", 1)),
                    updates=status_updates,
                    retry_on_version_conflict=True,
                    max_retries=3,
                )

                if result2:
                    print(f"✅ Status updated to 'Ready'!")
                    print(f"   New version: {result2.get('version', 'Unknown')}")
                else:
                    print(f"⚠️  Status update may have failed")
            else:
                print(f"⚠️  Could not find 'Ready' status")
                print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
                print(f"   Recommended: Manually change status to 'Ready' in Taiga UI")
        else:
            print(f"❌ Failed to update story US#{story_ref}")

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n📋 Summary:")
    print(f"   - Description updated with comprehensive status")
    print(f"   - Status should be changed to 'Ready'")
    print(f"   - Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")


if __name__ == "__main__":
    main()
