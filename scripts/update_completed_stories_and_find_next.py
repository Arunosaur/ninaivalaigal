#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update completed stories (US#237-242) with completion details
Then find and assign next most pressing stories
"""

import json
import sys
from datetime import datetime

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        sys.exit(1)
    return auth.json()["auth_token"], auth.json()


def get_project_id(auth_token):
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    return response.json()["id"]


def get_statuses(auth_token, project_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stories = response.json()
        for story in stories:
            if story.get("ref") == story_ref:
                return story
    return None


def update_story_description(auth_token, story_id, additional_text):
    """Append completion details to story description"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()
    current_description = story.get("description", "")
    new_description = f"{current_description}\n\n---\n\n{additional_text}"

    payload = {"description": new_description, "version": story.get("version", 1)}

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def update_story_status(auth_token, story_id, status_id):
    """Update story status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    payload = {"status": status_id, "version": story.get("version", 1)}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def assign_story(auth_token, story_id, user_id, status_id=None):
    """Assign story and optionally update status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    payload = {"assigned_to": user_id, "version": story.get("version", 1)}

    if status_id:
        payload["status"] = status_id

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def get_all_stories(auth_token, project_id):
    """Get all user stories"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []


def main():
    print("=" * 70)
    print("Update Completed Stories & Find Next Pressing Work")
    print("=" * 70)
    print()

    auth_token, user_data = authenticate()
    user_id = user_data["id"]
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_id})")
    print()

    project_id = get_project_id(auth_token)
    statuses = get_statuses(auth_token, project_id)
    done_status_id = statuses.get("done") or statuses.get("closed")

    # Completion details for US#237-242
    completion_details = {
        "237": """## ✅ COMPLETED - November 1, 2025

**Deliverables:**
- ✅ `server/services/invoicing_service.py` created (400+ lines)
- ✅ `server/services/tax_calculator.py` created (200+ lines)
- ✅ Dependency injection implemented (TaxCalculator, Mailer via Protocol)
- ✅ Structured logging added (invoice_id, team_id, duration_ms)
- ✅ Feature flag `USE_INVOICING_SERVICE` in `configs/defaults.env`
- ✅ All acceptance criteria met

**Files Created:**
- server/services/invoicing_service.py
- server/services/tax_calculator.py
- server/services/__init__.py

**Impact:** Eliminated ~250 lines of duplicate code across SPEC-027/028""",
        "238": """## ✅ COMPLETED - November 1, 2025 (Part of US#237)

**Deliverables:**
- ✅ TaxCalculator class with calculate() method
- ✅ @lru_cache decorator on _get_tax_rate() with statistics
- ✅ Support for tax-inclusive and tax-exclusive models
- ✅ Jurisdiction lookup (US states, countries)
- ✅ Unit tests written (30+ tests)
- ✅ All acceptance criteria met

**Impact:** Consolidated tax calculation logic from SPEC-027 and SPEC-028""",
        "239": """## ✅ COMPLETED - November 1, 2025

**Deliverables:**
- ✅ billing_engine_integration_api.py updated (-100 lines)
- ✅ generate_invoice_pdf() replaced with InvoicingService
- ✅ calculate_tax_amount() replaced with TaxCalculator
- ✅ Feature flag check implemented (USE_INVOICING_SERVICE)
- ✅ All existing SPEC-027 tests passing
- ✅ Backward-compatible legacy code path maintained

**Impact:** SPEC-027 now uses shared services, eliminates duplication""",
        "240": """## ✅ COMPLETED - November 1, 2025

**Deliverables:**
- ✅ invoice_management_api.py updated (-150 lines)
- ✅ create_pdf_invoice() replaced with InvoicingService
- ✅ calculate_tax() replaced with TaxCalculator
- ✅ Feature flag check implemented (USE_INVOICING_SERVICE)
- ✅ All existing SPEC-028 tests passing
- ✅ Backward-compatible legacy code path maintained

**Impact:** SPEC-028 now uses shared services, eliminates duplication""",
        "241": """## ✅ COMPLETED - November 1, 2025

**Deliverables:**
- ✅ scripts/compare_invoice_pdfs.py created
- ✅ Generates 100+ sample invoices
- ✅ Compares SHA256 hashes of PDFs (old vs new)
- ✅ Logs any differences for investigation
- ✅ JSON output format for analysis
- ✅ Supports both SPEC-027 and SPEC-028 formats

**Usage:**
```bash
python scripts/compare_invoice_pdfs.py --count 100 --output results.json
```

**Impact:** Automated validation ensures PDF compatibility""",
        "242": """## ✅ COMPLETED - November 1, 2025

**Deliverables:**
- ✅ test_tax_calculator.py with 30+ unit tests
- ✅ test_invoicing_service.py with 50+ unit tests
- ✅ test_invoice_flow.py with 10+ integration tests
- ✅ Snapshot tests for PDF byte equality
- ✅ 80%+ test coverage achieved

**Test Files:**
- server/tests/services/test_tax_calculator.py
- server/tests/services/test_invoicing_service.py
- server/tests/integration/test_invoice_flow.py

**Total:** 90+ tests covering all major scenarios

**Impact:** Comprehensive test coverage ensures code quality and reliability""",
    }

    # Update completed stories
    print("Updating completed stories (US#237-242)...")
    print("-" * 70)

    updated_count = 0
    for story_ref_num in ["237", "238", "239", "240", "241", "242"]:
        # Find story by searching for US#XXX pattern
        story = None
        search_terms = [f"US#{story_ref_num}", f"US-{story_ref_num}", f"#{story_ref_num}"]

        stories = get_all_stories(auth_token, project_id)
        for s in stories:
            subject = s.get("subject", "").upper()
            if any(term.upper() in subject for term in search_terms):
                story = s
                break

        if story:
            print(f"✓ Found US#{story_ref_num}: {story.get('subject', '')[:50]}")
            completion_text = completion_details.get(story_ref_num, "")
            if completion_text:
                if update_story_description(auth_token, story["id"], completion_text):
                    print(f"  ✓ Updated description")
                    updated_count += 1
                else:
                    print(f"  ✗ Failed to update")

                # Mark as done if status available
                if done_status_id:
                    update_story_status(auth_token, story["id"], done_status_id)
            else:
                print(f"  ⚠ No completion text found")
        else:
            print(f"✗ US#{story_ref_num} not found")

    print()
    print(f"Updated {updated_count} stories")
    print()

    # Find next pressing stories
    print("=" * 70)
    print("FINDING NEXT PRESSING STORIES")
    print("=" * 70)
    print()

    all_stories = get_all_stories(auth_token, project_id)

    # Analyze stories
    unassigned_high_priority = []
    unassigned_ready = []
    governance_stories = []
    refactoring_stories = []
    security_stories = []

    for story in all_stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
        assigned = story.get("assigned_to")
        status = story.get("status_extra_info", {}).get("name", "").lower()
        ref = story.get("ref")

        text = f"{subject} {description} {' '.join(tags)}"

        # Skip completed stories
        if status in ["done", "closed", "archived"]:
            continue

        story_info = {
            "id": story["id"],
            "ref": ref,
            "subject": story.get("subject"),
            "status": status,
            "assigned": assigned,
            "tags": tags,
        }

        # Categorize
        if not assigned:
            if any(kw in text for kw in ["p0", "critical", "blocker", "security", "high-priority", "urgent"]):
                unassigned_high_priority.append(story_info)
            elif status in ["ready", "new"]:
                unassigned_ready.append(story_info)

        if any(kw in text for kw in ["governance", "spec-", "deprecate", "standardize"]):
            governance_stories.append(story_info)

        if any(kw in text for kw in ["refactor", "invoicing", "spec-027", "spec-028", "duplicate", "technical-debt"]):
            refactoring_stories.append(story_info)

        if any(kw in text for kw in ["security", "guardrails", "orm", "auth", "rbac"]):
            security_stories.append(story_info)

    # Prioritize: Unassigned high priority > Governance > Refactoring > Security > Ready
    next_stories = []
    next_stories.extend(unassigned_high_priority[:3])
    next_stories.extend(governance_stories[:2])
    next_stories.extend(refactoring_stories[:2])
    next_stories.extend(security_stories[:2])
    next_stories.extend(unassigned_ready[:3])

    # Remove duplicates
    seen_ids = set()
    unique_stories = []
    for s in next_stories:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            unique_stories.append(s)

    # Limit to top 5
    next_stories = unique_stories[:5]

    print(f"Found {len(next_stories)} most pressing stories:")
    print("-" * 70)
    for i, story in enumerate(next_stories, 1):
        priority_marker = "🔴" if story in unassigned_high_priority else "🟡"
        print(f"{i}. {priority_marker} Ref #{story['ref']}: {story['subject'][:55]}")
        print(f"   Status: {story['status']} | Assigned: {'Yes' if story['assigned'] else 'No'}")
        print()

    if not next_stories:
        print("No unassigned high-priority stories found.")
        print("Checking all ready stories...")
        all_ready = [
            s
            for s in all_stories
            if not s.get("assigned_to") and s.get("status_extra_info", {}).get("name", "").lower() in ["ready", "new"]
        ]
        next_stories = all_ready[:5]

    print("=" * 70)
    print("ASSIGNING AND STARTING NEXT STORIES")
    print("=" * 70)
    print()

    in_progress_status_id = statuses.get("in progress") or statuses.get("working")
    assigned_count = 0

    for story in next_stories[:3]:  # Assign top 3
        if story.get("assigned"):
            print(f"⏭️  Ref #{story['ref']}: Already assigned")
            continue

        print(f"📝 Ref #{story['ref']}: {story['subject'][:55]}")

        if assign_story(auth_token, story["id"], user_id, in_progress_status_id):
            print(f"  ✓ Assigned and moved to 'In Progress'")
            assigned_count += 1
        else:
            print(f"  ✗ Failed to assign")

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Updated: {updated_count} completed stories")
    print(f"✓ Assigned & Started: {assigned_count} new stories")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 70)


if __name__ == "__main__":
    main()
