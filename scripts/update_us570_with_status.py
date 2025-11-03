#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#570 (SPEC-090) story with comprehensive status"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#570 story with comprehensive status"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story_ref = 570
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-090: Approval Chain Processing (ACP)")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    description = """**SPEC-090: Approval Chain Processing (ACP)**

**Status:** 🔄 IN PROGRESS (Implementation: ~35% complete)
**Phase:** Phase 3
**Completion:** Basic approvals complete, full ACP architecture missing

---

## ✅ Current Status

SPEC-090 has **PARTIAL IMPLEMENTATION**. Basic approval workflows are complete and production-ready, but the full ACP framework (workflow engine, role graph mapper, state machine, event store) is missing.

---

## ✅ What Exists (Basic Approvals - COMPLETE)

### 1. Approval Workflows System ✅
**File:** `server/approval_workflows.py` (457 lines)
- ✅ Submit memories for approval
- ✅ Approve/reject memories with review notes
- ✅ Track approval status and lifecycle
- ✅ Approval history (team and individual)
- ✅ Statistics and analytics
- ✅ Role-based permissions (team admin, global admin)
- ✅ Self-approval prevention
- ✅ Team scoping

**API Endpoints:**
- `/approval/submit` - Submit memory for approval
- `/approval/pending` - List pending approvals
- `/approval/{id}/approve` - Approve memory
- `/approval/{id}/reject` - Reject memory
- `/approval/{id}/status` - Get approval status
- `/approval/my-submissions` - User's submissions
- `/approval/team/{id}/history` - Team approval history
- `/approval/stats` - Approval statistics

### 2. Cross-Team Approval Workflow ✅
**File:** `server/approval_workflow.py` (~354 lines)
- ✅ Cross-team memory sharing approval requests
- ✅ Request management (create, approve, reject)
- ✅ Expiration handling (7 days default)
- ✅ Permission level management (read, write, admin)
- ✅ Database persistence (`CrossTeamApprovalRequest` model)
- ✅ Approval workflow manager

**Components:**
- `ApprovalWorkflowManager` class
- `CrossTeamApprovalRequest` database model
- Approval status enum (PENDING, APPROVED, REJECTED, EXPIRED)

### 3. Documentation ✅
**File:** `docs/APPROVAL-WORKFLOWS.md` (327 lines)
- ✅ Comprehensive feature documentation
- ✅ API usage examples
- ✅ Governance model
- ✅ Integration guides
- ✅ Testing instructions

**Status:** ✅ **PRODUCTION-READY** - Basic approval workflows fully implemented

---

## ❌ What's Missing (Full ACP Architecture)

### 1. Workflow Engine ❌
**Requirement:** Built atop async task queue layer
**Status:** ❌ **MISSING**
- Current implementation is synchronous
- No async task queue integration
- No workflow orchestration

### 2. Role Graph Mapper ❌
**Requirement:** Identifies approvers dynamically based on RBAC and project/team graphs
**Status:** ❌ **MISSING**
- Current: Simple role-based check (`team_admin`)
- Missing: Dynamic approver identification
- Missing: Graph-based routing
- Missing: Project/team graph integration

### 3. Full State Machine ❌
**Requirement:** Moves requests through `Draft → Pending → Approved → Rejected → Finalized`
**Status:** ⚠️ **PARTIAL**
- Current: `pending → approved/rejected` only
- Missing: `Draft` state
- Missing: `Finalized` state
- Missing: Formal state machine implementation

### 4. Event Store Persistence ❌
**Requirement:** Uses internal event store with rollback and journaling
**Status:** ❌ **MISSING**
- Current: Database persistence (SQLAlchemy)
- Missing: Event store integration
- Missing: Rollback mechanism
- Missing: Journaling/audit event store

### 5. Additional Missing Components
- ❌ `approval_chain_table` - No dedicated chain tracking table
- ❌ `event_hooks/approval_hooks.py` - No event hooks for post-approval reactions
- ❌ GraphQL APIs - Only REST APIs exist
- ❌ Approval dashboards UI - Frontend integration missing
- ❌ Retry logic - No automatic retry mechanism

---

## 📊 Implementation vs SPEC Alignment

**Overall Alignment:** ⚠️ **~35%**

| SPEC-090 Requirement | Current Implementation | Alignment |
|---------------------|----------------------|-----------|
| **Workflow Engine** (async task queue) | ❌ Missing | ❌ 0% |
| **Role Graph Mapper** (dynamic approvers) | ⚠️ Simple role check | ⚠️ 30% |
| **State Machine** (Draft→Pending→Approved→Rejected→Finalized) | ⚠️ Partial (Pending→Approved/Rejected) | ⚠️ 60% |
| **Event Store Persistence** | ⚠️ Database only | ⚠️ 40% |
| **REST APIs** | ✅ Complete | ✅ 100% |
| **GraphQL APIs** | ❌ Missing | ❌ 0% |
| **UI Integration** | ❌ Missing | ❌ 0% |
| **Audit Integration** | ⚠️ Partial | ⚠️ 50% |
| **Retry Logic** | ❌ Missing | ❌ 0% |
| **Approval Chain Table** | ❌ Missing | ❌ 0% |
| **Event Hooks** | ❌ Missing | ❌ 0% |

---

## 🚨 Critical Issues

### 1. Status Discrepancy
- **Taiga Story:** Marked "Done" (incorrect)
- **SPEC_INDEX.md:** Shows "Planned" (also incorrect)
- **Reality:** ~35% complete, should be "In Progress" or "Ready"

### 2. SPEC_INDEX.md Error
- **SPEC-099** incorrectly listed as "Approval Chain Processing (ACP)"
- **SPEC-099** actual content is "Rust Migration Strategy"
- **Issue:** Duplicate naming causing confusion

### 3. Implementation Gap
- **SPEC Vision:** Full ACP framework with workflow engine, role graph mapper, state machine
- **Current Reality:** Basic approval workflows (submit, approve, reject)
- **Gap:** Large gap between SPEC vision and current implementation

### 4. SPEC Directory Minimal
- **SPEC README:** Only 40 lines, minimal content
- **Missing:** Detailed design, acceptance criteria, implementation plan

---

## 📋 Implementation Evidence

### Files Created/Modified

**Approval Workflows:**
- `server/approval_workflows.py` (457 lines) - ✅ Complete
- `server/approval_workflow.py` (~354 lines) - ✅ Complete
- `server/routers/approvals.py` - ✅ Complete
- `docs/APPROVAL-WORKFLOWS.md` (327 lines) - ✅ Complete

**Database Models:**
- `CrossTeamApprovalRequest` model in `server/approval_workflow.py`

**Services Integration:**
- `services/core-api/lib/approval_workflow.py`
- `services/business-service/lib/approval_workflow.py`
- `services/graph-service/lib/approval_workflow.py`
- `services/admin-vendor-service/lib/approval_workflow.py`

**Total Implementation:** ~800 lines (basic approvals)

---

## 🎯 Acceptance Criteria Status

### SPEC-090 Deliverables

| Deliverable | Status | Notes |
|-------------|--------|-------|
| **Workflow Engine** | ❌ Not Started | Requires async task queue |
| **Role Graph Mapper** | ⚠️ Partial | Simple role check only |
| **State Machine** | ⚠️ Partial | Missing Draft, Finalized |
| **Event Store Persistence** | ❌ Not Started | Database only |
| **REST APIs** | ✅ Complete | All endpoints exist |
| **GraphQL APIs** | ❌ Not Started | Not implemented |
| **UI Integration** | ❌ Not Started | No dashboards |
| **Audit Integration** | ⚠️ Partial | Basic audit exists |
| **Approval Chain Table** | ❌ Not Started | No dedicated table |
| **Event Hooks** | ❌ Not Started | No hooks system |

**Overall Completion:** ⚠️ **~35%** (basic approvals done, ACP missing)

---

## 🔗 Coordination

### Related SPECs
- **SPEC-009** (Security Middleware Redaction) - ✅ Complementary, no overlap
- **SPEC-014** (Authentication and Authorization) - ✅ Complementary, uses RBAC
- **SPEC-025** (Vendor Admin Console) - ✅ Complementary, may use approvals
- **SPEC-040** (AI Feedback System) - ✅ Complementary, may integrate

### Duplication Check
- **SPEC-099:** Listed in SPEC_INDEX.md as "Approval Chain Processing (ACP)" but actual content is "Rust Migration Strategy"
- **Assessment:** ✅ NO ACTUAL DUPLICATION - Just SPEC_INDEX.md error

---

## 📝 Next Steps

### High Priority
1. **Fix SPEC_INDEX.md** - Correct SPEC-099 entry
2. **Enhance SPEC README** - Add detailed architecture design
3. **Design Workflow Engine** - Define async task queue integration

### Medium Priority
4. **Implement Role Graph Mapper** - Dynamic approver identification
5. **Add Event Store Integration** - Event persistence, rollback, journaling
6. **Complete State Machine** - Add Draft and Finalized states

### Low Priority
7. **GraphQL APIs** (if needed)
8. **UI Dashboards** (separate frontend work)
9. **Retry Logic** (enhancement)

---

## ⚠️ Important Notes

1. **Basic Approvals vs Full ACP:**
   - ✅ Basic approval workflows are COMPLETE and production-ready
   - ❌ Full ACP framework (workflow engine, role graph, state machine) is MISSING
   - **Gap:** Large architectural difference

2. **Status:**
   - Basic approvals: ✅ 100% complete
   - Full ACP: ⚠️ ~35% aligned with SPEC
   - **Overall SPEC-090:** ⚠️ ~35% complete

3. **Recommendation:**
   - Keep basic approvals as-is (they work)
   - Build full ACP framework on top
   - Document relationship between basic and full ACP

---

**Status:** 🔄 IN PROGRESS - Basic approvals complete (~800 lines), full ACP missing
**Completion:** ~35% (basic approvals done, ACP architecture missing)
**Next Steps:** Fix status discrepancies, enhance SPEC documentation, plan ACP implementation

---

**For detailed analysis, see**: `docs/spec-analysis/SPEC_090_COMPREHENSIVE_ANALYSIS.md`"""

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
            print(f"✅ Story US#{story_ref} updated successfully!")
            print(f"   New version: {result.get('version', 'Unknown')}")

            # Find and set status to "Ready" or "In Progress"
            import requests

            statuses_url = f"{taiga_url}/api/v1/userstory-statuses?project={story['project']}"
            headers = {"Authorization": f"Bearer {importer._auth_token}"}
            statuses_resp = requests.get(statuses_url, headers=headers)

            if statuses_resp.status_code == 200:
                statuses = statuses_resp.json()
                print(f"\n🔍 Available statuses:")
                for s in statuses:
                    print(f"   - {s.get('name')} (ID: {s.get('id')})")

                # Find "Ready" or "In Progress" status (prefer "Ready")
                ready_status = next((s for s in statuses if s.get("name", "").lower() == "ready"), None)
                if not ready_status:
                    ready_status = next(
                        (s for s in statuses if s.get("name", "").lower() in ["in progress", "new"]), None
                    )
                if ready_status:
                    status_id = ready_status["id"]
                    status_name = ready_status["name"]
                    print(f"\n📝 Setting status to '{status_name}'...")

                    status_update = {"version": result.get("version", story["version"]), "status": status_id}
                    update_url = f"{taiga_url}/api/v1/userstories/{story['id']}"
                    update_resp = requests.patch(update_url, json=status_update, headers=headers)

                    if update_resp.status_code == 200:
                        print(f"✅ Status updated to '{status_name}'!")
                    else:
                        print(f"⚠️  Failed to update status: {update_resp.status_code}")
            else:
                print(f"⚠️  Could not fetch statuses")

            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
        else:
            print(f"❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
