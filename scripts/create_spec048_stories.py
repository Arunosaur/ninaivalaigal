#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-048: Memory Intent Classifier

This script creates stories for the memory intent classifier system including:
- Classification pipeline
- Repetition detection
- Audio/narrative signals
- ML model integration
- User prompting for ambiguity
- CLI feedback
- Auto-tagging
- Metadata and audit trail
- Reclassification
- API endpoints
- Integration tests
"""

import json
import os
import sys

import requests

# Taiga configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = os.getenv("TAIGA_PROJECT_SLUG", "ninaivalaigal")

# Epic configuration
EPIC_SUBJECT = "EPIC#027: Memory Intent Classifier (SPEC-048)"
STORIES_FILE = "scripts/spec048_stories.json"

# Priority mapping
PRIORITY_MAP = {
    "High": 400,
    "Medium": 300,
    "Low": 200,
}


def authenticate():
    """Authenticate with Taiga and return auth token"""
    print(f"🔐 Authenticating with Taiga at {TAIGA_URL}...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    auth_token = response.json()["auth_token"]
    print("✅ Authentication successful")
    return auth_token


def get_project(auth_token):
    """Get project by slug"""
    print(f"📁 Getting project: {PROJECT_SLUG}...")
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    if response.status_code != 200:
        print(f"❌ Failed to get project: {response.status_code}")
        print(response.text)
        sys.exit(1)
    project = response.json()
    print(f"✅ Found project: {project['name']} (ID: {project['id']})")
    return project


def get_or_create_epic(auth_token, project_id):
    """Get or create epic for SPEC-048"""
    print(f"📚 Getting or creating epic: {EPIC_SUBJECT}...")
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get existing epics
    response = requests.get(
        f"{API_ENDPOINT}/epics?project={project_id}",
        headers=headers,
    )
    if response.status_code == 200:
        epics = response.json()
        for epic in epics:
            if epic["subject"] == EPIC_SUBJECT:
                print(f"✅ Found existing epic: {EPIC_SUBJECT} (Epic #{epic['ref']})")
                return epic

    # Create new epic
    print(f"➕ Creating new epic: {EPIC_SUBJECT}...")
    response = requests.post(
        f"{API_ENDPOINT}/epics",
        headers=headers,
        json={
            "project": project_id,
            "subject": EPIC_SUBJECT,
            "description": "Epic for SPEC-048: Memory Intent Classifier - Automatically classify user-recorded memory into contextual, procedural (macro), or narrative types using heuristics and ML classification, reducing user friction.",
            "tags": ["spec-048", "classification", "ml", "intent-classifier", "memory-intelligence"],
        },
    )
    if response.status_code == 201:
        epic = response.json()
        print(f"✅ Created epic: {EPIC_SUBJECT} (Epic #{epic['ref']})")
        return epic
    else:
        print(f"❌ Failed to create epic: {response.status_code}")
        print(response.text)
        sys.exit(1)


def create_story(auth_token, project_id, epic_id, story_data, story_number):
    """Create a user story in Taiga"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    story_payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": story_data.get("tags", []),
        "epic": epic_id,
        "priority": PRIORITY_MAP.get(story_data.get("priority", "Medium"), 300),
    }

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers=headers,
        json=story_payload,
    )

    if response.status_code == 201:
        created_story = response.json()
        print(f"✅ Created Story #{story_number}: {story_data['subject']} (US#{created_story['ref']})")
        return created_story
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(response.text)
        print(f"Story data: {json.dumps(story_payload, indent=2)}")
        return None


def main():
    """Main execution"""
    print("=" * 80)
    print("SPEC-048: Memory Intent Classifier - Taiga Story Creation")
    print("=" * 80)
    print()

    # Authenticate
    auth_token = authenticate()
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get project
    project = get_project(auth_token)
    project_id = project["id"]

    # Get or create epic
    epic = get_or_create_epic(auth_token, project_id)
    epic_id = epic["id"]

    print()
    print(f"📖 Epic: {EPIC_SUBJECT} (Epic #{epic['ref']})")
    print()

    # Load stories from JSON
    print(f"📄 Loading stories from {STORIES_FILE}...")
    if not os.path.exists(STORIES_FILE):
        print(f"❌ Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        stories_data = json.load(f)

    print(f"✅ Loaded {len(stories_data)} stories")
    print()

    # Create user stories
    print("📝 Creating user stories...")
    print()
    created_stories = []
    failed_stories = []

    for i, story_data in enumerate(stories_data, 1):
        story = create_story(auth_token, project_id, epic_id, story_data, i)
        if story:
            created_stories.append(story)
        else:
            failed_stories.append((i, story_data["subject"]))

    print()
    print("=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)} stories")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)} stories")
        for num, subject in failed_stories:
            print(f"   - Story #{num}: {subject}")

    if created_stories:
        print()
        print("Created Stories:")
        for story in created_stories:
            print(f"  - US#{story['ref']}: {story['subject']}")

    print()
    print(f"Epic: {EPIC_SUBJECT} (Epic #{epic['ref']})")
    print("=" * 80)


if __name__ == "__main__":
    main()
