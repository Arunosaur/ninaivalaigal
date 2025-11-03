#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create SPEC-027/028 refactoring stories (US#237-243) and start working on them
"""

import json
import sys
from pathlib import Path

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


def get_or_create_epic(auth_token, project_id):
    """Get or create the refactoring epic"""
    url = f"{API_ENDPOINT}/epics?project={project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        epics = response.json()
        for epic in epics:
            if "refactor" in epic.get("subject", "").lower() or "duplication" in epic.get("subject", "").lower():
                return epic["id"]

    # Create epic if not found
    url = f"{API_ENDPOINT}/epics"
    payload = {
        "project": project_id,
        "subject": "Eliminate SPEC-027/028 Invoice Duplication",
        "description": "Technical debt: ~250 lines of duplicate code between SPEC-027 and SPEC-028. Create shared InvoicingService and TaxCalculator modules.",
        "tags": ["technical-debt", "refactoring", "spec-027", "spec-028", "invoicing", "high-priority"],
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json()["id"]
    return None


def get_status_id(auth_token, project_id, status_name):
    """Get status ID by name"""
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for status in response.json():
            if status_name.lower() in status["name"].lower():
                return status["id"]
    return None


def create_user_story(auth_token, project_id, epic_id, story_data, ready_status_id):
    """Create a user story"""
    url = f"{API_ENDPOINT}/userstories"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    tags = [[tag, "#CCCCCC"] for tag in story_data.get("tags", [])]

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": tags,
        "status": ready_status_id,
    }

    if epic_id:
        payload["epics"] = [epic_id]

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()
    return None


def assign_and_start(auth_token, story_id, user_id, in_progress_status_id):
    """Assign story and move to In Progress"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    payload = {"assigned_to": user_id, "status": in_progress_status_id, "version": story.get("version", 1)}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


# Story definitions
STORIES = [
    {
        "subject": "US#237: Create Shared InvoicingService Module",
        "description": """As a developer, I want a single InvoicingService that handles PDF generation and tax calculation, so that invoice logic is consistent across all SPECs.

**Acceptance Criteria:**
- server/services/invoicing_service.py created (400 lines)
- InvoicingService class with generate_pdf() method
- Dependency injection for TaxCalculator and Mailer
- Structured logging (invoice_id, team_id, duration_ms)
- Feature flag USE_INVOICING_SERVICE implemented
- Unit tests written (50+ tests, 80%+ coverage)

**Technical Notes:**
- Use SPEC-028's create_pdf_invoice() as base (more comprehensive)
- Add optional dependency injection for easier testing
- Keep ReportLab for Phase 1

**Effort**: 5 story points (Day 1 Morning)""",
        "tags": [
            "spec-027",
            "spec-028",
            "invoicing",
            "pdf-generation",
            "high-priority",
            "technical-debt",
            "refactoring",
        ],
    },
    {
        "subject": "US#238: Create Shared TaxCalculator Module",
        "description": """As a developer, I want a single TaxCalculator that handles all tax logic, so that tax calculations are consistent across billing and invoice management.

**Acceptance Criteria:**
- server/services/tax_calculator.py created (200 lines)
- TaxCalculator class with calculate() method
- @lru_cache decorator on _get_tax_rate() (>80% cache hit rate)
- Support for tax-inclusive and tax-exclusive models
- Jurisdiction lookup (US states, countries)
- Unit tests written (30+ tests)

**Effort**: 3 story points (Day 1 Afternoon)""",
        "tags": ["spec-027", "spec-028", "tax-calculation", "high-priority", "technical-debt", "refactoring"],
    },
    {
        "subject": "US#239: Refactor SPEC-027 to Use InvoicingService",
        "description": """As a developer, I want SPEC-027 to use the shared InvoicingService instead of its own generate_invoice_pdf() function.

**Acceptance Criteria:**
- billing_engine_integration_api.py updated (-100 lines)
- generate_invoice_pdf() removed
- InvoicingService imported and used
- Feature flag check implemented
- All existing SPEC-027 tests passing
- Stripe webhook flow verified

**Dependencies:** US#237, US#238
**Effort**: 2 story points (Day 2 Morning)""",
        "tags": ["spec-027", "refactoring", "invoicing", "technical-debt"],
    },
    {
        "subject": "US#240: Refactor SPEC-028 to Use InvoicingService",
        "description": """As a developer, I want SPEC-028 to use the shared InvoicingService instead of its own create_pdf_invoice() function.

**Acceptance Criteria:**
- invoice_management_api.py updated (-150 lines)
- create_pdf_invoice() removed
- InvoicingService imported and used
- Feature flag check implemented
- All existing SPEC-028 tests passing
- Customer portal displays correctly

**Dependencies:** US#237, US#238
**Effort**: 2 story points (Day 2 Afternoon)""",
        "tags": ["spec-028", "refactoring", "invoicing", "technical-debt"],
    },
]


def main():
    print("=" * 70)
    print("Create SPEC-027/028 Refactoring Stories & Start Work")
    print("=" * 70)
    print()

    auth_token, user_data = authenticate()
    user_id = user_data["id"]
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_id})")
    print()

    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get or create epic
    epic_id = get_or_create_epic(auth_token, project_id)
    if epic_id:
        print(f"✓ Epic ID: {epic_id}")
    print()

    # Get status IDs
    ready_status_id = get_status_id(auth_token, project_id, "ready") or get_status_id(auth_token, project_id, "new")
    in_progress_status_id = get_status_id(auth_token, project_id, "in progress") or get_status_id(
        auth_token, project_id, "working"
    )

    print("Creating stories...")
    print("-" * 70)

    created_stories = []

    for story_data in STORIES:
        story = create_user_story(auth_token, project_id, epic_id, story_data, ready_status_id)
        if story:
            print(f"✓ Created: {story['subject']} (Ref: #{story.get('ref')})")
            created_stories.append(story)
        else:
            print(f"✗ Failed: {story_data['subject']}")

    print()
    print("=" * 70)
    print("ASSIGNING AND STARTING FIRST STORY (US#237)")
    print("=" * 70)
    print()

    if created_stories and in_progress_status_id:
        first_story = created_stories[0]
        if first_story:
            print(f"Starting: {first_story['subject']}")
            if assign_and_start(auth_token, first_story["id"], user_id, in_progress_status_id):
                print(f"✓ Assigned and moved to 'In Progress'")
                print()
                print(f"🔗 View: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{first_story.get('ref')}")
            else:
                print(f"✗ Failed to assign/update")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Created: {len(created_stories)} stories")
    print(f"✓ Ready to work on: US#237 (InvoicingService)")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 70)


if __name__ == "__main__":
    main()
