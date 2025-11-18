#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-055: Codebase Refactor & Modularization.

Usage:
    python3 scripts/create_spec055_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "055"
SPEC_TITLE = "Codebase Refactor & Modularization"


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": project_slug},
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_user_id(headers, username):
    """Get user ID by username."""
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username", "").lower() == username.lower():
                return user.get("id")
    return None


def get_status_id(headers, project_id, status_name):
    """Get status ID by name."""
    response = requests.get(
        f"{API_ENDPOINT}/userstory-statuses",
        headers=headers,
        params={"project": project_id},
    )
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def create_story(headers, project_id, subject, description, status_id=None, assigned_to=None):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": [f"SPEC-{SPEC_NUMBER}"],
    }

    if status_id:
        payload["status"] = status_id

    if assigned_to:
        payload["assigned_to"] = assigned_to

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code} - {response.text[:200]}")
        return None


def main():
    """Main function."""
    print("=" * 80)
    print(f"📋 Creating Taiga Stories for SPEC-{SPEC_NUMBER}")
    print(f"   Project: {PROJECT_SLUG}")
    print(f"   SPEC: {SPEC_TITLE}")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting project...")
    project_id = get_project_id(headers, PROJECT_SLUG)
    print(f"✅ Project ID: {project_id}")

    # Get status IDs
    print("\n3️⃣  Getting status IDs...")
    new_status_id = get_status_id(headers, project_id, "New")
    in_progress_status_id = get_status_id(headers, project_id, "In progress")
    print(f"✅ New status ID: {new_status_id}")
    print(f"✅ In progress status ID: {in_progress_status_id}")

    # Get user IDs for Developer F, G, H
    print("\n4️⃣  Getting developer IDs...")
    developers = {}
    for dev_name in ["developer-f", "developer-g", "developer-h"]:
        dev_id = get_user_id(headers, dev_name)
        if dev_id:
            developers[dev_name] = dev_id
            print(f"✅ {dev_name}: ID={dev_id}")
        else:
            print(f"⚠️  {dev_name}: Not found")

    if not developers:
        print("⚠️  No developers found. Stories will be unassigned.")

    # Define stories based on SPEC-055 remaining work
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Verify MCP Server Modularization",
            "description": """**Objective**: Verify if MCP server has been modularized according to SPEC-055 requirements.

**Background**:
- SPEC-055 targets modularization of monolithic files (main.py, database.py, mcp_server.py)
- Main.py and database.py modularization are complete
- MCP server modularization status needs verification

**Tasks**:
- [ ] Check if mcp_server.py (880 lines target) has been split into modules
- [ ] Verify MCP server directory structure in `server/mcp/`
- [ ] Document current modularization status
- [ ] If not modularized, create plan for modularization
- [ ] Update SPEC-055 documentation with findings

**Acceptance Criteria**:
- [ ] MCP server modularization status documented
- [ ] Plan created if modularization needed
- [ ] SPEC-055 documentation updated""",
            "status": "New",
            "assignee": "developer-f" if "developer-f" in developers else None,
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Database.py Legacy Cleanup Verification",
            "description": """**Objective**: Verify and clean up legacy database.py file after modularization.

**Background**:
- Database operations have been modularized into `server/database/operations/`
- Legacy database.py (1209 lines) may still exist
- Need to verify if legacy file can be removed or needs migration

**Tasks**:
- [ ] Verify current database.py file status
- [ ] Check if all operations have been migrated to modular structure
- [ ] Identify any remaining dependencies on legacy file
- [ ] Create migration plan for remaining dependencies
- [ ] Remove or deprecate legacy file once migration complete
- [ ] Update all imports across codebase

**Acceptance Criteria**:
- [ ] Legacy database.py status verified
- [ ] All dependencies identified and migrated
- [ ] Legacy file removed or properly deprecated
- [ ] All imports updated to use modular structure""",
            "status": "New",
            "assignee": "developer-g" if "developer-g" in developers else None,
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Module Documentation & README Completion",
            "description": """**Objective**: Complete documentation for all modularized components.

**Background**:
- SPEC-055 modularization is mostly complete (~60-70%)
- Module documentation needs completion
- README files needed for each module explaining responsibilities

**Tasks**:
- [ ] Document router module responsibilities
- [ ] Document database operations module structure
- [ ] Create README for each major module directory
- [ ] Document module dependencies and relationships
- [ ] Update SPEC-055 README with final status
- [ ] Create module organization guide

**Acceptance Criteria**:
- [ ] All major modules have README documentation
- [ ] Module responsibilities clearly documented
- [ ] Dependencies and relationships documented
- [ ] SPEC-055 README updated with completion status
- [ ] Module organization guide created""",
            "status": "New",
            "assignee": "developer-h" if "developer-h" in developers else None,
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Final Modularization Verification & Testing",
            "description": """**Objective**: Final verification that all modularization work is complete and tested.

**Background**:
- Phase 1 (main.py modularization) - ✅ Complete
- Phase 2 (database operations) - ✅ Complete
- Phase 3 (MCP server, cleanup, documentation) - In progress

**Tasks**:
- [ ] Verify all modularization work is complete
- [ ] Run comprehensive test suite
- [ ] Verify no broken imports or dependencies
- [ ] Performance testing to ensure no regression
- [ ] Integration testing across modules
- [ ] Code review of modularization changes
- [ ] Update SPEC-055 status to Complete

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] No broken imports or dependencies
- [ ] Performance metrics maintained
- [ ] Integration tests pass
- [ ] Code review completed
- [ ] SPEC-055 marked as Complete""",
            "status": "New",
            "assignee": "developer-f" if "developer-f" in developers else None,
        },
    ]

    # Create stories
    print("\n5️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: {story_data['subject'][:60]}...")

        status_id = new_status_id if story_data["status"] == "New" else in_progress_status_id
        assigned_to = (
            developers.get(story_data["assignee"])
            if story_data["assignee"] and story_data["assignee"] in developers
            else None
        )

        created = create_story(
            headers,
            project_id,
            story_data["subject"],
            story_data["description"],
            status_id=status_id,
            assigned_to=assigned_to,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, story_data["subject"]))
            assignee_info = f" (assigned to {story_data['assignee']})" if assigned_to else " (unassigned)"
            print(f"   ✅ Created US#{ref}{assignee_info}")
        else:
            failed_stories.append(story_data["subject"])
            print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")

    if created_stories:
        print("\nCreated stories:")
        for ref, subject in created_stories:
            print(f"  US#{ref}: {subject[:65]}")

    print("=" * 80)


if __name__ == "__main__":
    main()




