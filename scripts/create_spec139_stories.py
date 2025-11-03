#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Create Taiga user stories for SPEC-139: Audit Reconciliation & Rust Integration Readiness.
Assigns all stories to Developer A.
"""

import os
import sys

import requests

# Taiga API Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "139"

# Story definitions
STORIES = [
    {
        "subject": f"SPEC-{SPEC_NUMBER}: Audit Artifact Reconciliation Plan",
        "description": """**Objective**: Create comprehensive plan to normalize audit-import artifacts and restore repository to maintainable state.

**Deliverable**: `AUDIT_RECONCILIATION_PLAN.md`

**Tasks**:
- Inventory audit additions (specs, tasks, scripts, tests)
- Classify artifacts (keep / archive / trim / delete)
- Update SPEC index entries for audit-introduced drift
- Ensure Taiga automation scripts are credential-safe
- Create documentation alignment strategy
- Document test & CI strategy updates
- Record decisions and link commits

**Success Criteria**:
- [ ] Audit-produced files categorized with plan documented
- [ ] SPEC index reflects accurate statuses after reconciliation
- [ ] Taiga scripts reviewed for credential safety
- [ ] Plan approved by Platform Architect""",
        "tags": [f"spec-{SPEC_NUMBER}", "audit-reconciliation", "documentation"],
    },
    {
        "subject": f"SPEC-{SPEC_NUMBER}: Rust Memory Service Readiness & Gating",
        "description": """**Objective**: Fix Python <-> Rust interface blockers and establish gating strategy for Rust integration.

**Deliverable**: `RUST_INTEGRATION_GATE.md`

**Tasks**:
- Fix Python <-> Rust interface blockers (provider defaults, request signatures)
- Establish gating strategy for Rust integration tests and CI opt-in
- Apply pytest markers (`@pytest.mark.rust_integration`) to Rust-dependent tests
- Update `pytest.ini` and CI scripts to exclude gated suites by default
- Document operational checklist for enabling Rust memory provider
- Create feature flag system for Rust provider activation
- Document activation steps and rollback plan

**Success Criteria**:
- [ ] Memory API signatures fixed and provider defaults gated by feature flag
- [ ] Rust integration pytest suite marked and excluded by default in CI
- [ ] Rust activation gate checklist approved by platform and Rust owners
- [ ] Feature flag system implemented and tested""",
        "tags": [f"spec-{SPEC_NUMBER}", "rust-integration", "gating"],
    },
    {
        "subject": f"SPEC-{SPEC_NUMBER}: Post-Audit Validation & CI Health",
        "description": """**Objective**: Confirm FastAPI boot, smoke tests, and targeted pytest suites are green after audit reconciliation.

**Deliverable**: `VERIFICATION_2025-11-AUDIT.md`

**Tasks**:
- Confirm FastAPI boot is successful
- Run smoke tests and verify they pass
- Execute targeted pytest suites (excluding Rust integration)
- Verify CI pipeline health
- Document verification results in evidence log
- Update runbooks for future large-scale imports/audits
- Capture long-lived CI guardrails

**Success Criteria**:
- [ ] Verification report logged with passing FastAPI boot
- [ ] Targeted pytest run passes (non-Rust tests)
- [ ] CI pipeline status verified and documented
- [ ] Runbook updates completed
- [ ] Sign-off from Platform Architect, Rust Lead, DevOps Lead""",
        "tags": [f"spec-{SPEC_NUMBER}", "validation", "ci-health"],
    },
]


def authenticate():
    """Authenticate with Taiga and return auth token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        return response.json().get("auth_token")
    return None


def get_project_id(auth_token):
    """Get project ID by slug."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    return None


def get_developer_a_id(auth_token):
    """Get Developer A user ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            username = user.get("username", "").lower()
            full_name = user.get("full_name_display", "").lower()
            if "developer-a" in username or "developer a" in username or "developer a" in full_name:
                return user.get("id")
    return None


def get_status_id(auth_token, project_id, status_name):
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstory-statuses?project={project_id}", headers=headers)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name", "").lower() == status_name.lower():
                return status.get("id")
    return None


def create_story(auth_token, project_id, story_data, developer_a_id, status_id):
    """Create a user story in Taiga."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    story_data.update(
        {
            "project": project_id,
            "assigned_to": developer_a_id,
            "status": status_id,
        }
    )
    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)
    if response.status_code == 201:
        story = response.json()
        return story.get("ref"), story.get("id")
    return None, None


def main():
    """Main function."""
    print("=" * 80)
    print(f"Creating Taiga stories for SPEC-{SPEC_NUMBER}")
    print("=" * 80)
    print()

    # Authenticate
    print("Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project ID
    print(f"Getting project ID for '{PROJECT_SLUG}'...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Failed to get project ID")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer A ID
    print("Getting Developer A user ID...")
    developer_a_id = get_developer_a_id(auth_token)
    if not developer_a_id:
        print("❌ Developer A not found")
        sys.exit(1)
    print(f"✅ Developer A ID: {developer_a_id}")
    print()

    # Get "New" or "Ready" status ID
    print("Getting status ID...")
    status_id = get_status_id(auth_token, project_id, "New")
    if not status_id:
        status_id = get_status_id(auth_token, project_id, "Ready")
    if not status_id:
        print("⚠️  Could not find 'New' or 'Ready' status, using first available")
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_ENDPOINT}/userstory-statuses?project={project_id}", headers=headers)
        if response.status_code == 200:
            statuses = response.json()
            if statuses:
                status_id = statuses[0].get("id")
    if status_id:
        print(f"✅ Status ID: {status_id}")
    print()

    # Create stories
    print("Creating stories...")
    created_stories = []
    for story_data in STORIES:
        print(f'  Creating: {story_data["subject"]}...')
        ref, story_id = create_story(auth_token, project_id, story_data, developer_a_id, status_id)
        if ref and story_id:
            created_stories.append((ref, story_data["subject"]))
            print(f"    ✅ Created US#{ref}")
        else:
            print(f"    ❌ Failed to create story")

    print()
    print("=" * 80)
    print(f"✅ Created {len(created_stories)} stories for SPEC-{SPEC_NUMBER}:")
    print("=" * 80)
    for ref, subject in created_stories:
        print(f"  US#{ref}: {subject}")
    print()
    print(f"All stories assigned to Developer A (ID: {developer_a_id})")


if __name__ == "__main__":
    main()
