#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga User Stories for SPEC-042: Auth-Aware Test Harness
"""

import json
import sys
from pathlib import Path

import requests

# Taiga Configuration
TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"

# Load story definitions from JSON file
STORIES_FILE = Path(__file__).parent / "spec042_stories.json"

EPIC_SUBJECT = "EPIC#025: Auth-Aware Test Harness (SPEC-042)"


def authenticate():
    """Authenticate with Taiga and return auth token"""
    url = f"{API_ENDPOINT}/auth"
    payload = {"type": "normal", "username": USERNAME, "password": PASSWORD}

    print(f"Authenticating with Taiga at {TAIGA_URL}...")
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    auth_data = response.json()
    print(f"✓ Authenticated as {auth_data.get('username')}")
    return auth_data["auth_token"]


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    print(f"Fetching project '{PROJECT_SLUG}'...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to get project: {response.status_code}")
        print(response.text)
        sys.exit(1)

    project = response.json()
    print(f"✓ Found project: {project['name']} (ID: {project['id']})")
    return project["id"]


def get_or_create_tags(auth_token, project_id, tag_names):
    """Get or create tags and return their colors"""
    url = f"{API_ENDPOINT}/projects/{project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get project details: {response.status_code}")
        return {}

    project = response.json()
    existing_tags_data = project.get("tags_colors", {})

    # Handle both dict and list formats
    if isinstance(existing_tags_data, dict):
        existing_tags = [[k, v] for k, v in existing_tags_data.items()]
        tag_colors = existing_tags_data.copy()
    elif isinstance(existing_tags_data, list):
        existing_tags = existing_tags_data
        tag_colors = {tag[0]: tag[1] for tag in existing_tags}
    else:
        existing_tags = []
        tag_colors = {}

    existing_tag_names = list(tag_colors.keys())

    # Add any missing tags with default colors
    new_tags = []
    color_palette = ["#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33", "#33FFF5", "#F533FF", "#FFA533"]
    color_idx = 0
    for tag_name in tag_names:
        if tag_name not in existing_tag_names:
            color = color_palette[color_idx % len(color_palette)]
            new_tags.append([tag_name, color])
            tag_colors[tag_name] = color
            color_idx += 1

    if new_tags:
        # Update project with new tags
        all_tags = existing_tags + new_tags
        # Convert to dict format for API
        tags_dict = {tag[0]: tag[1] for tag in all_tags}
        payload = {"tags_colors": tags_dict}
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✓ Created {len(new_tags)} new tags")
        else:
            print(f"⚠ Warning: Could not update tags: {response.status_code}")

    return tag_colors


def get_status_id(auth_token, project_id, status_name="New"):
    """Get the ID for a status name"""
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    statuses = response.json()
    for status in statuses:
        if status["name"].lower() == status_name.lower():
            return status["id"]

    # If status not found, return first status
    return statuses[0]["id"] if statuses else None


def get_or_create_epic(auth_token, project_id):
    """Get existing epic or create new one"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Check for existing epic
    url = f"{API_ENDPOINT}/epics?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get epics: {response.status_code}")
        return None

    epics = response.json()
    for epic in epics:
        if EPIC_SUBJECT.lower() in epic.get("subject", "").lower() or "spec-042" in epic.get("subject", "").lower():
            print(f"✓ Found existing epic: #{epic.get('ref')}: {epic.get('subject')}")
            return epic["id"]

    # Create new epic
    print(f"Creating epic: {EPIC_SUBJECT}...", end="")
    epic_data = {
        "project": project_id,
        "subject": EPIC_SUBJECT,
        "description": "Epic for SPEC-042: Auth-Aware Test Harness - Enterprise Readiness. Covers remaining enterprise integration features and completion of partial features for comprehensive auth-aware testing infrastructure.",
        "tags": [["spec-042", "#FF5733"], ["auth-aware", "#33FF57"], ["testing", "#3357FF"], ["enterprise", "#FF33F5"]],
    }
    url = f"{API_ENDPOINT}/epics"
    response = requests.post(url, headers=headers, json=epic_data)
    if response.status_code == 201:
        epic = response.json()
        print(f" ✓ Created epic: #{epic.get('ref')}")
        return epic["id"]
    else:
        print(f" ❌ Failed: {response.status_code}")
        print(response.text)
        return None


def create_user_story(auth_token, project_id, story_data, tag_colors, status_id, epic_id):
    """Create a single user story"""
    url = f"{API_ENDPOINT}/userstories"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Prepare tags with colors
    tags = [[tag, tag_colors.get(tag, "#CCCCCC")] for tag in story_data.get("tags", [])]

    # Add effort to description if available
    description = story_data.get("description", "")
    if "effort" in story_data:
        description += f"\n\n**Estimated Effort**: {story_data['effort']}"

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": description,
        "tags": tags,
        "status": status_id,
        "epic": epic_id,
    }

    print(f"Creating story: {story_data['subject']}...", end="")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        story = response.json()
        print(f" ✓ Created US#{story.get('ref')}")
        return story
    else:
        print(f" ❌ Failed: {response.status_code}")
        print(response.text)
        return None


def main():
    """Main function"""
    print("=" * 80)
    print("SPEC-042: Auth-Aware Test Harness - Taiga Story Creation")
    print("=" * 80)
    print()

    # Load stories from JSON
    if not STORIES_FILE.exists():
        print(f"❌ Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        stories_data = json.load(f)

    print(f"Loaded {len(stories_data)} stories from {STORIES_FILE}")
    print()

    # Authenticate
    auth_token = authenticate()

    # Get project
    project_id = get_project_id(auth_token)
    print()

    # Get or create epic
    epic_id = get_or_create_epic(auth_token, project_id)
    if not epic_id:
        print("❌ Failed to get or create epic")
        sys.exit(1)
    print()

    # Collect all tags from all stories
    all_tags = set()
    for story in stories_data:
        all_tags.update(story.get("tags", []))

    # Get or create tags
    tag_colors = get_or_create_tags(auth_token, project_id, list(all_tags))
    print()

    # Get status ID
    status_id = get_status_id(auth_token, project_id, "New")
    if not status_id:
        print("⚠ Warning: Could not get status ID, stories may not be created")
    print()

    # Create stories
    print("Creating user stories...")
    print()
    created_stories = []

    for i, story_data in enumerate(stories_data, 1):
        story = create_user_story(auth_token, project_id, story_data, tag_colors, status_id, epic_id)
        if story:
            created_stories.append(story)
        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Epic: EPIC#{epic_id}")
    print(f"Created {len(created_stories)}/{len(stories_data)} stories")
    print()

    if created_stories:
        print("Created Stories:")
        for story in created_stories:
            print(f"  - US#{story.get('ref')}: {story.get('subject')}")

    print()
    print("✅ Complete!")


if __name__ == "__main__":
    main()
