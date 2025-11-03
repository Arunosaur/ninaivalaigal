#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create SPEC-027/028 Refactoring Tasks in Taiga
Uses Taiga API to create Epic and User Stories programmatically
"""

import json
import sys

import requests

# Taiga Configuration
TAIGA_URL = "http://localhost:9000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"

# Color codes for labels
TAG_COLORS = {
    "technical-debt": "#FF6B6B",  # Red-orange
    "refactoring": "#4ECDC4",  # Cyan
    "spec-027": "#9B59B6",  # Purple
    "spec-028": "#9B59B6",  # Purple
    "invoicing": "#2ECC71",  # Green
    "pdf-generation": "#2ECC71",  # Green
    "tax-calculation": "#2ECC71",  # Green
    "high-priority": "#E74C3C",  # Red
    "testing": "#3498DB",  # Blue
    "documentation": "#95A5A6",  # Gray
}


def authenticate():
    """Authenticate with Taiga and get auth token"""
    url = f"{TAIGA_URL}/auth"
    payload = {"type": "normal", "username": USERNAME, "password": PASSWORD}

    print(f"🔐 Authenticating with Taiga...")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print(f"✅ Authenticated successfully")
        return auth_token
    else:
        print(f"❌ Authentication failed: {response.text}")
        sys.exit(1)


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{TAIGA_URL}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    print(f"📁 Getting project ID for '{PROJECT_SLUG}'...")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        project = response.json()
        project_id = project["id"]
        print(f"✅ Project ID: {project_id}")
        return project_id, project
    else:
        print(f"❌ Failed to get project: {response.text}")
        sys.exit(1)


def create_epic(auth_token, project_id):
    """Create the main Epic for refactoring"""
    url = f"{TAIGA_URL}/epics"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    epic_data = {
        "project": project_id,
        "subject": "Technical Debt: Eliminate SPEC-027/028 Invoice Duplication",
        "description": """SPEC-027 (Billing Engine) and SPEC-028 (Invoice Management) have ~250 lines of duplicated code for PDF generation and tax calculation. This creates maintenance burden and risk of inconsistency.

**Goal**: Create shared InvoicingService to eliminate duplication while preserving distinct SPEC responsibilities.

**Business Value:**
• Reduce maintenance burden (1 place to update vs 2)
• Ensure invoice consistency across all touchpoints
• Enable faster feature development
• Reduce technical debt

**Acceptance Criteria:**
☐ invoicing_service.py created with 80%+ test coverage
☐ SPEC-027 refactored to use shared service (-100 LOC)
☐ SPEC-028 refactored to use shared service (-150 LOC)
☐ All existing tests passing
☐ PDF output identical before/after (SHA256 verified)
☐ Documentation updated in both SPECs
☐ Pre-commit hook added
☐ Production deployment successful

**Links:**
• docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md
• docs/refactoring/SPEC_027_028_IMPLEMENTATION_CHECKLIST.md
• SPEC_027_028_REFACTORING_SUMMARY.md""",
        "tags": ["technical-debt", "refactoring", "spec-027", "spec-028", "invoicing"],
    }

    print(f"\n📋 Creating Epic: {epic_data['subject']}...")
    response = requests.post(url, json=epic_data, headers=headers)

    if response.status_code == 201:
        epic = response.json()
        print(f"✅ Epic created successfully! ID: {epic['id']}")
        return epic
    else:
        print(f"❌ Failed to create epic: {response.status_code}")
        print(response.text)
        return None


def create_user_story(auth_token, project_id, epic_id, project_info, story_data):
    """Create a user story"""
    url = f"{TAIGA_URL}/userstories"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Get default status (first one in project)
    default_status = project_info.get("us_statuses", [{}])[0].get("id")

    # Add required fields
    story_data["project"] = project_id
    story_data["status"] = default_status
    if epic_id:
        story_data["epics"] = [epic_id]

    # Handle points field
    if "points" in story_data:
        # Get the default role points
        default_role_points = project_info.get("roles", [{}])[0].get("id")
        if default_role_points:
            story_data["points"] = {str(default_role_points): story_data["points"]}

    print(f"  Creating: {story_data['subject']}...")
    response = requests.post(url, json=story_data, headers=headers)

    if response.status_code == 201:
        story = response.json()
        print(f"  ✅ Story created! ID: {story['id']}, Ref: #{story['ref']}")
        return story
    else:
        print(f"  ❌ Failed to create story: {response.status_code}")
        print(f"  {response.text}")
        return None


def create_task(auth_token, project_id, story_id, task_subject):
    """Create a task for a user story"""
    url = f"{TAIGA_URL}/tasks"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    task_data = {
        "project": project_id,
        "user_story": story_id,
        "subject": task_subject,
        "status": 1,  # Default status
    }

    response = requests.post(url, json=task_data, headers=headers)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"    ⚠️  Failed to create task: {task_subject}")
        return None


def get_user_stories():
    """Define all user stories for the refactoring"""
    return [
        {
            "subject": "US#237 - Create Shared InvoicingService Module",
            "description": """As a developer, I want a single InvoicingService that handles PDF generation and tax calculation, so that invoice logic is consistent across all SPECs.

**Acceptance Criteria:**
☐ server/services/invoicing_service.py created (400 lines)
☐ InvoicingService class with generate_pdf() method
☐ Dependency injection for TaxCalculator and Mailer
☐ Structured logging (invoice_id, team_id, duration_ms)
☐ Feature flag USE_INVOICING_SERVICE implemented
☐ Unit tests written (50+ tests, 80%+ coverage)

**Technical Notes:**
Use SPEC-028's create_pdf_invoice() as base (more comprehensive)""",
            "tags": ["invoicing", "pdf-generation", "high-priority"],
            "points": 5,
            "tasks": [
                "Create server/services/invoicing_service.py skeleton",
                "Copy SPEC-028's PDF generation code",
                "Add dependency injection",
                "Add structured logging",
                "Add docstrings and type hints",
                "Create USE_INVOICING_SERVICE feature flag",
                "Write 50+ unit tests",
                "Verify 80%+ coverage",
            ],
        },
        {
            "subject": "US#238 - Create Shared TaxCalculator Module",
            "description": """As a developer, I want a single TaxCalculator that handles all tax logic, so that tax calculations are consistent across billing and invoice management.

**Acceptance Criteria:**
☐ server/services/tax_calculator.py created (200 lines)
☐ TaxCalculator class with calculate() method
☐ @lru_cache on _get_tax_rate() (>80% cache hit rate)
☐ Support tax-inclusive and tax-exclusive models
☐ Jurisdiction lookup (US states, countries)
☐ Unit tests written (30+ tests)

**Technical Notes:**
Consolidate tax logic from both SPEC-027 and SPEC-028""",
            "tags": ["tax-calculation", "invoicing", "high-priority"],
            "points": 3,
            "tasks": [
                "Create server/services/tax_calculator.py",
                "Consolidate tax logic from SPEC-027 and SPEC-028",
                "Add @lru_cache to _get_tax_rate()",
                "Support tax-inclusive/exclusive calculations",
                "Add jurisdiction lookup",
                "Add structured logging",
                "Write 30+ unit tests",
                "Test cache hit rate (>80%)",
            ],
        },
        {
            "subject": "US#239 - Refactor SPEC-027 to Use InvoicingService",
            "description": """As a developer, I want SPEC-027 to use the shared InvoicingService instead of its own generate_invoice_pdf() function.

**Acceptance Criteria:**
☐ billing_engine_integration_api.py updated (-100 lines)
☐ generate_invoice_pdf() removed
☐ InvoicingService imported and used
☐ Feature flag check implemented
☐ All SPEC-027 tests passing
☐ Stripe webhook flow verified

**Dependencies:** US#237, US#238""",
            "tags": ["spec-027", "billing-engine", "refactoring", "high-priority"],
            "points": 2,
            "tasks": [
                "Import InvoicingService",
                "Replace generate_invoice_pdf() calls",
                "Add feature flag check",
                "Update webhook handlers",
                "Run integration tests",
                "Verify Stripe flow",
                "Test subscription → invoice → PDF",
            ],
        },
        {
            "subject": "US#240 - Refactor SPEC-028 to Use InvoicingService",
            "description": """As a developer, I want SPEC-028 to use the shared InvoicingService so that customer portal invoices are consistent with billing invoices.

**Acceptance Criteria:**
☐ invoice_management_api.py updated (-150 lines)
☐ create_pdf_invoice() removed
☐ InvoicingService imported and used
☐ Feature flag check implemented
☐ All SPEC-028 tests passing
☐ Customer portal displays correctly
☐ Accounting exports working

**Dependencies:** US#237, US#238""",
            "tags": ["spec-028", "invoice-management", "refactoring", "high-priority"],
            "points": 2,
            "tasks": [
                "Import InvoicingService",
                "Replace create_pdf_invoice() calls",
                "Add feature flag check",
                "Update customer portal endpoints",
                "Run integration tests",
                "Verify portal display",
                "Test accounting exports",
            ],
        },
        {
            "subject": "US#241 - Parallel Run PDF Comparison",
            "description": """As a QA engineer, I want to compare PDFs generated by old and new services to ensure byte-identical output.

**Acceptance Criteria:**
☐ Generate 100 invoices with both services
☐ Compare SHA256 hashes
☐ Log any differences
☐ 100% match rate achieved
☐ Script documented

**Dependencies:** US#239, US#240""",
            "tags": ["testing", "validation", "pdf-generation", "high-priority"],
            "points": 1,
            "tasks": [
                "Create scripts/compare_invoice_pdfs.py",
                "Generate 100 sample invoices on staging",
                "Run both old and new PDF generation",
                "Compare SHA256 hashes",
                "Log any mismatches",
                "Investigate and fix differences",
                "Document comparison process",
            ],
        },
        {
            "subject": "US#242 - Complete Test Suite and Documentation",
            "description": """As a developer, I want comprehensive tests and documentation for InvoicingService.

**Acceptance Criteria:**
☐ test_invoicing_service.py with 50+ unit tests
☐ test_tax_calculator.py with 30+ unit tests
☐ test_invoice_integration.py with 10+ tests
☐ Snapshot tests for PDF byte equality
☐ 80%+ test coverage
☐ API documentation complete
☐ SPEC-027 and SPEC-028 updated with delegation notes

**Dependencies:** US#237, US#238, US#239, US#240""",
            "tags": ["testing", "documentation", "coverage", "high-priority"],
            "points": 3,
            "tasks": [
                "Write test_invoicing_service.py (50+ tests)",
                "Write test_tax_calculator.py (30+ tests)",
                "Write test_invoice_integration.py (10+ tests)",
                "Add snapshot tests",
                "Run pytest-cov (verify 80%+)",
                "Create API documentation",
                "Update SPEC-027 spec.md",
                "Update SPEC-028 spec.md",
                "Update architecture diagrams",
            ],
        },
        {
            "subject": "US#243 - Remove Legacy Code and Deploy to Production",
            "description": """As a developer, I want to remove legacy PDF generation code and deploy the refactored service to production.

**Acceptance Criteria:**
☐ USE_INVOICING_SERVICE=true in production
☐ Monitor for 24 hours (error rate <0.1%)
☐ generate_invoice_pdf_legacy() removed from SPEC-027
☐ create_pdf_invoice() removed from SPEC-028
☐ Feature flag code removed
☐ Coverage report pushed
☐ CHANGELOG.md updated
☐ Deployment successful

**Dependencies:** US#241, US#242""",
            "tags": ["deployment", "production", "cleanup", "high-priority"],
            "points": 2,
            "tasks": [
                "Enable flag on staging (10% traffic)",
                "Monitor for errors",
                "Increase to 50% traffic",
                "Monitor performance",
                "Enable 100% production traffic",
                "Monitor for 24 hours",
                "Remove legacy code from SPEC-027",
                "Remove legacy code from SPEC-028",
                "Remove feature flag code",
                "Push coverage report",
                "Update CHANGELOG.md",
            ],
        },
    ]


def main():
    """Main execution"""
    print("=" * 60)
    print("SPEC-027/028 Refactoring - Taiga Task Creation")
    print("=" * 60)

    # Authenticate
    auth_token = authenticate()

    # Get project
    project_id, project = get_project_id(auth_token)

    # Create Epic
    epic = create_epic(auth_token, project_id)
    if not epic:
        print("❌ Failed to create epic, aborting")
        sys.exit(1)

    epic_id = epic["id"]

    # Create User Stories
    print(f"\n📝 Creating 7 User Stories...")
    user_stories = get_user_stories()
    created_stories = []

    for story_data in user_stories:
        # Extract tasks before creating story
        tasks = story_data.pop("tasks", [])

        # Create user story
        story = create_user_story(auth_token, project_id, epic_id, project, story_data)
        if story:
            created_stories.append(story)

            # Create tasks for this story
            if tasks:
                print(f"    Adding {len(tasks)} tasks...")
                for task_subject in tasks:
                    create_task(auth_token, project_id, story["id"], task_subject)

    # Summary
    print("\n" + "=" * 60)
    print("✅ Task Creation Complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"  • Epic created: {epic['subject']}")
    print(f"  • User stories created: {len(created_stories)}")
    print(f"  • Total story points: 18 (5+3+2+2+1+3+2)")
    print(f"\n🔗 View in Taiga:")
    print(f"  http://localhost:9000/project/ninaivalaigal/backlog")
    print(f"  http://localhost:9000/project/ninaivalaigal/epic/{epic['ref']}")
    print()


if __name__ == "__main__":
    main()
