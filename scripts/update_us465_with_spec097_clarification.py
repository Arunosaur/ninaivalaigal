#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#465 (SPEC-097) story with clarification and SPEC-144 reference"""

import os
import sys

import requests

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#465 story with clarification"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story_ref = 465
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-097: Feedback Loop for AI Context")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    description = """**SPEC-097: Feedback Loop for AI Context**

**Status:** ⚠️ **NEEDS CLARIFICATION** (Implementation: 0% - No distinct implementation found)
**Phase:** Phase 3
**Priority:** Medium (depends on clarification)

---

## 🚨 Critical Finding: Duplicate/Unclear Scope

SPEC-097 has **NO DISTINCT IMPLEMENTATION** found. Analysis indicates it may be:
1. **Duplicate of SPEC-040** (likely) - SPEC-040 already implements comprehensive feedback loops
2. **Merged into SPEC-040** - Functionality absorbed during implementation
3. **Different scope** - Needs clear definition to distinguish from SPEC-040

**Evidence:**
- SPEC-097 README: Placeholder only (25 lines, "Planned")
- SPEC_INDEX.md: Shows "Complete" (inconsistent with README)
- Implementation: ❌ 0% - No SPEC-097-specific code found
- SPEC-040: ✅ Complete (861 lines) - Comprehensive feedback loop system

---

## 📋 SPEC-097 vs Related SPECs

### SPEC-040: Feedback Loop System ✅ COMPLETE
- **Focus:** Memory-centric feedback (users score individual memories)
- **Scope:** Memory relevance and accuracy signals
- **Status:** Complete (861 lines of implementation)
- **Location:** `specs/040-feedback-loop-system/`
- **Implementation:** `server/feedback_engine.py`, `server/feedback_api.py`

**Features:**
- ✅ Implicit feedback (dwell time, click-through, navigation)
- ✅ Explicit feedback (thumbs up/down, quality notes)
- ✅ Memory score adjustment
- ✅ Redis integration
- ✅ Relevance engine integration

### SPEC-097: Feedback Loop for AI Context ⚠️ UNCLEAR
- **Focus:** AI context feedback (unclear scope)
- **Status:** Placeholder (no implementation)
- **Issue:** Unclear relationship to SPEC-040

### SPEC-144: Context-Aware Feedback System 📋 PLANNED (NEW)
- **Focus:** Context composition and reasoning quality feedback
- **Scope:** Meta-feedback layer above memory-centric feedback
- **Status:** Planned (newly created to address context-aware feedback needs)
- **Location:** `specs/144-context-aware-feedback-system/`

**Purpose:**
- Learn how context composition affects AI reasoning quality
- Feedback on context length, relevance, tone alignment, retrieval bias
- Adaptive context gating and optimization
- GraphOps node prioritization learning
- Reasoner prompt window auto-tuning

**This is the Phase 3+ natural successor to SPEC-040 for context-aware feedback.**

---

## ❌ What's Missing (SPEC-097)

### No Implementation Found
- ❌ No SPEC-097-specific endpoints
- ❌ No `ai_context_feedback.py` or similar files
- ❌ No SPEC-097 database schemas
- ❌ No distinct code for "AI Context" feedback

**All feedback functionality appears to be in SPEC-040.**

---

## 🎯 Recommended Resolution

### Option 1: Mark as Duplicate (RECOMMENDED)
If SPEC-097 was intended to be the same as SPEC-040:
- Update SPEC_INDEX.md to mark as "Duplicate" or remove
- Update all references to point to SPEC-040
- Close this Taiga story with note about duplication

### Option 2: Define Clear Scope
If SPEC-097 has a different scope:
- Define what "AI Context" feedback means
- Distinguish from SPEC-040 (memory feedback)
- Determine if it aligns with SPEC-144 (context-aware feedback)
- If aligns with SPEC-144, consider merging/renumbering

### Option 3: Mark as Merged
If SPEC-097 functionality was merged into SPEC-040:
- Update SPEC_INDEX.md to note merged status
- Add note in SPEC-040 about merged scope
- Close this Taiga story with merge note

---

## 🔗 Related Documentation

- **SPEC-040:** `specs/040-feedback-loop-system/README.md` - Feedback Loop System (Complete)
- **SPEC-144:** `specs/144-context-aware-feedback-system/README.md` - Context-Aware Feedback System (Planned)
- **Analysis:** `docs/spec-analysis/SPEC_097_COMPREHENSIVE_ANALYSIS.md` - Comprehensive analysis

---

## 📊 Taiga Story Status

**Duplicates Found:**
- US#465: Primary story (this one)
- US#493: Duplicate (should be closed/deleted)
- US#521: Duplicate (should be closed/deleted)

**Recommendation:**
- Keep US#465 for tracking clarification
- Close/delete US#493 and US#521 as duplicates

---

**Status:** ⚠️ NEEDS CLARIFICATION - 0% implementation, unclear scope vs SPEC-040
**Next Steps:** Determine if duplicate, merged, or define clear scope
**Related:** SPEC-144 created for Context-Aware Feedback System (distinct from memory-centric feedback)"""

    # Get status ID for "New" or "Planned"
    api_endpoint = f"{taiga_url}/api/v1"
    headers = {"Authorization": f"Bearer {importer._auth_token}", "Content-Type": "application/json"}

    project_info = requests.get(f"{api_endpoint}/projects/by_slug?slug=ninaivalaigal", headers=headers).json()
    project_id = project_info["id"]

    statuses = requests.get(f"{api_endpoint}/userstory-statuses?project={project_id}", headers=headers).json()
    new_status_id = None
    for status in statuses:
        if status.get("name", "").lower() in ["new", "planned"]:
            new_status_id = status["id"]
            break

    update_payload = {"description": description, "version": story.get("version", 1)}

    if new_status_id and story.get("status_extra_info", {}).get("name", "").lower() not in ["new", "planned"]:
        update_payload["status"] = new_status_id

    response = requests.patch(f"{api_endpoint}/userstories/{story['id']}", headers=headers, json=update_payload)

    if response.status_code == 200:
        print("✅ Story description updated with clarification")
        if new_status_id:
            print(f"   Status changed to '{status.get('name') if status else 'New/Planned'}'")
    else:
        print(f"❌ Failed to update story: {response.status_code}")
        print(f"   Response: {response.text[:200]}")


if __name__ == "__main__":
    main()
