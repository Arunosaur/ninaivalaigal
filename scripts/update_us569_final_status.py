#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#569 (SPEC-089) story with final status after directory creation"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#569 story with final status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story_ref = 569
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-089: Breaking Change Management")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    description = """**SPEC-089: Breaking Change Management**

**Status:** 📋 PLANNED (Implementation: ~70% complete, SPEC directory created)
**Phase:** Phase 3
**Completion:** ~75%

---

## ✅ Current Status

SPEC-089 is **PARTIALLY COMPLETE** with implementation done and SPEC directory structure now created. Breaking change detection and policy documentation are complete, and cross-references with SPEC-088 are established.

---

## ✅ What Exists

### 1. SPEC Directory Structure ✅
**Directory:** `specs/089-breaking-change-management/`
- ✅ `README.md` - Complete SPEC documentation with:
  - Definition of breaking changes
  - 8-step process for breaking changes
  - Breaking change detection details
  - Examples and review checklist
  - Coordination with SPEC-088
- ✅ `migration-guide-template.md` - Template for migration guides
- ✅ Cross-references with SPEC-088 established

### 2. Breaking Change Detection Script ✅
**File:** `ci/check-breaking-changes.py` (175 lines)
- ✅ Detects breaking changes in OpenAPI specifications
- ✅ Compares contracts between git refs
- ✅ Checks for removed endpoints, methods, required parameters, schemas
- ✅ Creates CI marker file
- ✅ Integrated with `.github/workflows/contract-validation.yml`

### 3. Breaking Change Documentation ✅
**File:** `shared/contracts/docs/BREAKING_CHANGES.md` (98 lines)
- ✅ Comprehensive 8-step process
- ✅ Definition and examples
- ✅ Review checklist
- ✅ Policy and guidelines

### 4. CI Integration ✅
**File:** `.github/workflows/contract-validation.yml`
- ✅ Breaking change detection runs on PR/push
- ✅ Fails build on breaking changes without version bump

### 5. Cross-References Established ✅
- ✅ SPEC-089 references SPEC-088 for versioning scheme
- ✅ SPEC-088 references SPEC-089 for breaking change process
- ✅ `specs/088-api-versioning-strategy/breaking-changes.md` updated to reference SPEC-089
- ✅ `specs/088-api-versioning-strategy/README.md` updated with cross-references

---

## ❌ What's Missing

### 1. Directory Mismatch Resolved ✅
- ✅ SPEC directory created: `specs/089-breaking-change-management/`
- ⚠️ Old directory `specs/089-white-label-platform/` still exists (should be removed - contains SPEC-140 content)

### 2. Enhanced Detection 🔄
- 🔄 Database schema breaking change detection
- 🔄 Protocol Buffer breaking change detection
- 🔄 Additional breaking change patterns

### 3. Migration Tools ❌
- ❌ Automated migration script generation
- ❌ Client SDK migration helpers

---

## 📋 Implementation Evidence

### Files Created
- `specs/089-breaking-change-management/README.md` - Complete SPEC documentation
- `specs/089-breaking-change-management/migration-guide-template.md` - Migration template

### Files Updated
- `specs/088-api-versioning-strategy/README.md` - Added cross-references to SPEC-089
- `specs/088-api-versioning-strategy/breaking-changes.md` - Now references SPEC-089

### Implementation
- **Script:** `ci/check-breaking-changes.py` (175 lines, complete)
- **Workflow:** `.github/workflows/contract-validation.yml` (integrated)
- **Documentation:** `shared/contracts/docs/BREAKING_CHANGES.md` (98 lines, complete)

**Total Implementation:** ~273 lines (script + doc) + SPEC documentation

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
- ✅ SPEC directory - CREATED
- ✅ SPEC README - COMPLETE
- ✅ Cross-references - ESTABLISHED

**Overall Completion:** ~75% (implementation complete, SPEC structure complete, enhancements pending)

---

## 🔗 Coordination with SPEC-088

**Cross-References Established:**
- ✅ SPEC-089 references SPEC-088 for versioning scheme
- ✅ SPEC-088 references SPEC-089 for breaking change process
- ✅ Clear boundaries defined:
  - **SPEC-088:** Versioning scheme and infrastructure (HOW to version)
  - **SPEC-089:** Breaking change detection and management process (WHEN and HOW to manage changes)

**Files Updated:**
- `specs/088-api-versioning-strategy/README.md` - Sections now reference SPEC-089
- `specs/088-api-versioning-strategy/breaking-changes.md` - Updated to reference SPEC-089

---

## 🎯 Next Steps

### High Priority
1. ✅ **SPEC Directory Created** - COMPLETE
2. ✅ **Cross-References Established** - COMPLETE
3. ⚠️ **Remove Misnumbered Directory** - Remove `specs/089-white-label-platform/` (contains SPEC-140 content)

### Medium Priority
4. **Enhanced Detection**
   - Database schema breaking change detection
   - Protocol Buffer breaking change detection
   - Additional breaking change patterns

5. **Migration Tools**
   - Automated migration script generation
   - Client SDK migration helpers

---

## 📝 Files Created/Updated

### Created
- `specs/089-breaking-change-management/README.md` - Complete SPEC documentation
- `specs/089-breaking-change-management/migration-guide-template.md` - Migration template

### Updated
- `specs/088-api-versioning-strategy/README.md` - Cross-references added
- `specs/088-api-versioning-strategy/breaking-changes.md` - References SPEC-089

---

## ⚠️ Important Notes

1. **Directory Status:**
   - ✅ `specs/089-breaking-change-management/` - CREATED (correct)
   - ⚠️ `specs/089-white-label-platform/` - Still exists (should be removed - misnumbered)

2. **Coordination:**
   - ✅ Cross-references established between SPEC-088 and SPEC-089
   - ✅ Clear boundaries defined
   - ✅ Both SPECs reference each other appropriately

3. **Implementation:**
   - ✅ Breaking change detection script is COMPLETE and working
   - ✅ Documentation is COMPLETE in SPEC structure
   - ✅ CI integration is COMPLETE

---

**Status:** 📋 Planned - Implementation ~75% complete, SPEC structure created
**Next Steps:** Remove misnumbered directory, enhance detection capabilities

---

**For detailed analysis, see**: `docs/spec-analysis/SPEC_089_COMPREHENSIVE_ANALYSIS.md`"""

    print(f"\n📝 Updating US#{story_ref} with final status...")

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
            print(f"✅ Story US#{story_ref} updated successfully!")
            print(f"   New version: {result.get('version', 'Unknown')}")
            print(f"   Status: {result.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
        else:
            print(f"❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
