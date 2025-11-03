#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#568 (SPEC-088) story with comprehensive status information"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#568 story with comprehensive SPEC-088 status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#568 is the story for SPEC-088
    story_ref = 568
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-088: API Versioning Strategy")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    # Create comprehensive description
    description = """**SPEC-088: API Versioning Strategy**

**Status:** 📋 PLANNED/DRAFT (Documentation incomplete, partial implementation)
**Phase:** Phase 3
**Completion:** ~10-15%

---

## 📊 Current Status Summary

SPEC-088 is **INCOMPLETE** with mostly empty documentation (stubs only), partial ad-hoc implementation, and no versioning infrastructure. There is comprehensive versioning documentation elsewhere, but SPEC-088 itself is not complete.

---

## ✅ What Exists (Partial)

### 1. Documentation Files (Stubs)
- **README.md**: Contains only section headers (no content)
- **format.md**: Partial content (request/response examples)
- **breaking-changes.md**: Headers only
- **deprecation-policy.md**: Headers only
- **CHANGELOG-template.md**: Exists
- **migration-guide-template.md**: Exists

### 2. Partial Implementation
- **Some `/api/v1/` endpoints exist:**
  - `server/compliance/api_hipaa.py`: `prefix="/api/v1/compliance/hipaa"`
  - `server/compliance/api.py`: `prefix="/api/v1/compliance"`
- **Ad-hoc versioning:** Not systematic

### 3. Related Documentation (External)
- **`shared/contracts/docs/VERSIONING_STRATEGY.md`**: Comprehensive versioning strategy
  - 194 lines of complete versioning strategy
  - Path-based versioning: `/api/v1/users`, `/api/v2/users`
  - Support policy, lifecycle, deprecation, etc.
  - **Note:** This appears to be the actual strategy, but it's not in SPEC-088

---

## ❌ What's Missing

### 1. Documentation Gaps
- ❌ **SPEC README content** - Only headers, no actual content
- ❌ **Breaking changes content** - Stub only
- ❌ **Deprecation policy content** - Stub only
- ❌ **Format recommendations** - Partial

### 2. Implementation Gaps
- ❌ **Versioning infrastructure** - No `server/versioning/` module
- ❌ **Version routing middleware** - Not implemented
- ❌ **Version detection logic** - Not implemented
- ❌ **Deprecation warnings** - Not implemented
- ❌ **Migration tools** - Not implemented
- ❌ **Compatibility tests** - Not implemented

### 3. Status Mismatches
- ❌ **README frontmatter** claims `status: Complete` (should be `Planned`)
- ❌ **Taiga story** marked "Done" (should be "Planned")
- ✅ **SPEC_INDEX.md** correctly shows "Planned"

### 4. Documentation Consolidation Needed
- ⚠️ **Duplication concern:** `shared/contracts/docs/VERSIONING_STRATEGY.md` contains comprehensive versioning strategy
- **Question:** Which is authoritative - SPEC-088 or the external doc?
- **Recommendation:** Consolidate or cross-reference appropriately

---

## 📋 Acceptance Criteria Status

### Define Versioning Scheme
- ✅ Decision made: URL path versioning (documented elsewhere)
- ❌ Not documented in SPEC-088 README

### Implement Version Negotiation
- ❌ Not implemented (no middleware/routing)

### Create Deprecation Policy
- ✅ Policy exists (in external doc)
- ❌ Not documented in SPEC-088 deprecation-policy.md

### Document Migration Guides
- ✅ Template exists
- ❌ No actual migration guides

### Set Up Automated Compatibility Tests
- ❌ Not implemented

**Overall Completion:** ~10-15%

---

## 🎯 Next Steps (Priority Order)

### High Priority
1. **Complete SPEC README** - Fill in all section content
2. **Complete Supporting Docs** - Fill in breaking-changes.md and deprecation-policy.md
3. **Fix Status Mismatches** - Update README frontmatter and Taiga story
4. **Consolidate Documentation** - Decide authoritative source, cross-reference

### Medium Priority
5. **Implement Versioning Infrastructure** - Create `server/versioning/` module
6. **Systematize `/api/v1/` Usage** - Audit and ensure consistency

### Low Priority
7. **Migration Tools** - Compatibility checker, migration scripts

---

## 📝 Files That Need Work

### Documentation Files (Fill Content)
- `specs/088-api-versioning-strategy/README.md` - Main spec (headers only)
- `specs/088-api-versioning-strategy/breaking-changes.md` - Headers only
- `specs/088-api-versioning-strategy/deprecation-policy.md` - Headers only
- `specs/088-api-versioning-strategy/format.md` - Partial (complete recommendations)

### Implementation Files (Create)
- `server/versioning/` - Module for versioning infrastructure
- `server/versioning/router.py` - Version routing
- `server/versioning/middleware.py` - Version detection and deprecation warnings

---

## 🔗 Related SPECs

- **SPEC-087:** API Surface Contracts - Complementary (different concern)
- **SPEC-089:** Breaking Change Management - Related (may overlap on deprecation)
- **SPEC-003:** Core API Architecture - Complementary (foundation)
- **SPEC-100:** API Container Modularization - Complementary (different concern)

**Potential Overlap:** SPEC-089 may duplicate deprecation/migration content. Should coordinate.

---

## ⚠️ Important Notes

1. **Status Discrepancies:**
   - README frontmatter: Claims "Complete" (incorrect)
   - SPEC_INDEX.md: Shows "Planned" (correct)
   - Taiga story: Marked "Done" (incorrect)
   - **All should be "Planned"**

2. **Documentation Duplication:**
   - `shared/contracts/docs/VERSIONING_STRATEGY.md` has comprehensive versioning strategy
   - This creates confusion about which is authoritative
   - Need to consolidate or cross-reference

3. **Implementation Status:**
   - Some endpoints use `/api/v1/` but this is ad-hoc
   - No systematic versioning infrastructure
   - No deprecation warnings or migration tools

---

**Status Alignment:**
- SPEC_INDEX.md: ✅ "Planned" (CORRECT)
- SPEC README: ❌ "Complete" (INCORRECT - should be "Planned")
- This Story: ❌ "Done" (INCORRECT - should be "Planned")

**Recommendation:** Update all statuses to "Planned", complete documentation, then prioritize infrastructure implementation.

---

**For detailed analysis, see**: `docs/spec-analysis/SPEC_088_COMPREHENSIVE_ANALYSIS.md`"""

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

            # Try to find "Planned" status
            print(f"\n🔍 Finding 'Planned' status...")
            project_id = story.get("project")

            # Get statuses using requests directly
            import requests

            status_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
            headers = importer._get_headers()
            status_response = requests.get(status_url, headers=headers)

            planned_status_id = None
            if status_response.status_code == 200:
                statuses = status_response.json()
                for status in statuses:
                    if isinstance(status, dict):
                        status_name = status.get("name", "").lower()
                        if "planned" in status_name or status_name == "planned":
                            planned_status_id = status.get("id")
                            print(f"   Found: {status.get('name')} (ID: {planned_status_id})")
                            break

            if planned_status_id:
                print(f"\n📝 Updating status to 'Planned'...")
                status_updates = {
                    "status": planned_status_id,
                }

                result2 = importer.update_user_story(
                    story_id=story["id"],
                    version=result.get("version", story.get("version", 1)),
                    updates=status_updates,
                    retry_on_version_conflict=True,
                    max_retries=3,
                )

                if result2:
                    print(f"✅ Status updated to 'Planned'!")
                    print(f"   New version: {result2.get('version', 'Unknown')}")
                else:
                    print(f"⚠️  Status update may have failed")
            else:
                print(f"⚠️  Could not find 'Planned' status")
                print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
                print(f"   Recommended: Manually change status to 'Planned' in Taiga UI")
        else:
            print(f"❌ Failed to update story US#{story_ref}")

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n📋 Summary:")
    print(f"   - Description updated with comprehensive status")
    print(f"   - Status should be changed to 'Planned'")
    print(f"   - Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")


if __name__ == "__main__":
    main()
