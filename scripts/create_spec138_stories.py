#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-138: Custom Embedding Integration Hooks
Stories: US-280 through US-283 (4 stories)
Epic: EPIC#024 - Custom Embedding Integration Hooks
"""

import json
import sys
from typing import Any, Dict

import requests

# Taiga Configuration
TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"

# Epic Configuration
EPIC_NAME = "EPIC#024: Custom Embedding Integration Hooks (SPEC-138)"
EPIC_DESCRIPTION = """
EPIC#024: Custom Embedding Integration Hooks (SPEC-138)

**Objective:**
Implement a hook system allowing external or fine-tuned embedding models to replace the default pgvector pipeline.

**Scope:**
- Embedding hook API for model registration and execution
- Model registry system for managing embedding models
- Pipeline selection mechanism with preferences
- Comprehensive testing suite

**Related SPEC:**
- SPEC-138: Custom Embedding Integration Hooks (Planned, Phase 2C)
- Split from SPEC-039 to preserve lineage

**Stories:**
- US-280: Embedding Hook API Design and Implementation
- US-281: Embedding Model Registry System
- US-282: Embedding Pipeline Selection Mechanism
- US-283: Custom Embedding Integration Tests

**Total Points:** ≈ 13 points
"""


def authenticate() -> str:
    """Authenticate with Taiga and return auth token."""
    auth_response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if auth_response.status_code != 200:
        print(f"Authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        sys.exit(1)
    return auth_response.json()["auth_token"]


def get_project(auth_token: str) -> Dict[str, Any]:
    """Get project by slug."""
    project_response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    if project_response.status_code != 200:
        print(f"Failed to get project: {project_response.status_code}")
        sys.exit(1)
    return project_response.json()


def create_epic(auth_token: str, project_id: int) -> int | None:
    """Create epic for SPEC-138."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    epic_data = {
        "project": project_id,
        "subject": EPIC_NAME,
        "description": EPIC_DESCRIPTION,
        "tags": ["spec-138", "epic-024", "embedding", "hooks", "phase-2c"],
    }

    epic_response = requests.post(
        f"{API_ENDPOINT}/epics",
        headers=headers,
        json=epic_data,
    )

    if epic_response.status_code == 201:
        epic = epic_response.json()
        print(f"✅ Created Epic: {epic['subject']} (Epic #{epic['ref']})")
        return epic["id"]
    else:
        print(f"⚠️  Epic creation failed: {epic_response.status_code}")
        print(f"Response: {epic_response.text}")
        # Try to find existing epic
        epics_response = requests.get(
            f"{API_ENDPOINT}/epics?project={project_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        if epics_response.status_code == 200:
            epics = epics_response.json()
            for epic in epics:
                if "SPEC-138" in epic.get("subject", "") or "EPIC#024" in epic.get("subject", ""):
                    print(f"✅ Found existing Epic: {epic['subject']} (Epic #{epic['ref']})")
                    return epic["id"]
        return None


def create_user_story(
    auth_token: str, project_id: int, epic_id: int | None, story_data: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Create a user story in Taiga."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    story_payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": story_data["tags"],
    }

    if epic_id:
        story_payload["epic"] = epic_id

    story_response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers=headers,
        json=story_payload,
    )

    if story_response.status_code == 201:
        story = story_response.json()
        story_ref = story_data.get("story_ref", "N/A")
        print(f"✅ Created Story: {story['subject']} (US#{story['ref']}) - Expected: {story_ref}")
        return story
    else:
        print(f"❌ Failed to create story: {story_data['subject']}")
        print(f"Status: {story_response.status_code}")
        print(f"Response: {story_response.text}")
        return None


def main():
    """Main execution function."""
    print("=" * 60)
    print("Creating Taiga Stories for SPEC-138")
    print("Epic: EPIC#024 - Custom Embedding Integration Hooks")
    print("Stories: US-280 through US-283")
    print("=" * 60)

    # Authenticate
    print("\n1. Authenticating...")
    auth_token = authenticate()
    print("✅ Authentication successful")

    # Get project
    print("\n2. Getting project...")
    project = get_project(auth_token)
    project_id = project["id"]
    print(f"✅ Project found: {project['name']} (ID: {project_id})")

    # Create epic
    print("\n3. Creating/Verifying Epic...")
    epic_id = create_epic(auth_token, project_id)

    # Load stories from JSON
    print("\n4. Loading stories from JSON...")
    try:
        with open("scripts/spec138_stories.json", "r") as f:
            stories = json.load(f)
        print(f"✅ Loaded {len(stories)} stories")
    except FileNotFoundError:
        print("❌ Error: scripts/spec138_stories.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        sys.exit(1)

    # Create stories
    print("\n5. Creating user stories...")
    created_stories = []
    for i, story_data in enumerate(stories, start=1):
        print(f"\nCreating story {i}/{len(stories)}: {story_data['subject']}")
        story = create_user_story(auth_token, project_id, epic_id, story_data)
        if story:
            created_stories.append(story)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Epic: {EPIC_NAME}")
    print(f"Stories created: {len(created_stories)}/{len(stories)}")
    if created_stories:
        print("\nCreated Stories:")
        for story in created_stories:
            print(f"  - US#{story['ref']}: {story['subject']}")
    print("\n✅ SPEC-138 Taiga stories creation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()




