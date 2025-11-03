#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga User Stories for SPEC-026: Standalone Teams and Billing
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
STORIES_FILE = Path(__file__).parent / "spec026_stories.json"


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
        # Convert dict to list format
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


def create_user_story(auth_token, project_id, story_data, tag_colors):
    """Create a single user story"""
    url = f"{API_ENDPOINT}/userstories"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Prepare tags with colors
    tags = [[tag, tag_colors.get(tag, "#CCCCCC")] for tag in story_data.get("tags", [])]

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": tags,
        "status": story_data.get("status_id"),  # Will be set after getting status ID
    }

    print(f"Creating story: {story_data['subject']}...", end="")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        story = response.json()
        print(f" ✓ Created (ID: {story['id']}, Ref: #{story['ref']})")
        return story
    else:
        print(f" ✗ Failed ({response.status_code})")
        print(f"  Error: {response.text}")
        return None


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

    # Return first status if not found
    return statuses[0]["id"] if statuses else None


def load_stories():
    """Load story definitions from JSON file"""
    if not STORIES_FILE.exists():
        print(f"Error: Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("SPEC-026 Taiga Story Creator")
    print("=" * 60)
    print()

    # Authenticate
    auth_token = authenticate()
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print()

    # Get status ID
    status_id = get_status_id(auth_token, project_id, "New")
    if not status_id:
        print("Error: Could not find 'New' status")
        sys.exit(1)
    print(f"✓ Using status ID: {status_id}")
    print()

    # Load stories
    stories = load_stories()
    print(f"Loaded {len(stories)} story definitions")
    print()

    # Get all unique tags
    all_tags = set()
    for story in stories:
        all_tags.update(story.get("tags", []))

    # Create/get tags
    tag_colors = get_or_create_tags(auth_token, project_id, list(all_tags))
    print()

    # Create stories
    print("Creating user stories...")
    print("-" * 60)

    created_count = 0
    failed_count = 0

    for story_data in stories:
        story_data["status_id"] = status_id
        result = create_user_story(auth_token, project_id, story_data, tag_colors)
        if result:
            created_count += 1
        else:
            failed_count += 1

    print("-" * 60)
    print()
    print("Summary:")
    print(f"  ✓ Created: {created_count} stories")
    if failed_count > 0:
        print(f"  ✗ Failed:  {failed_count} stories")
    print()
    print(f"View stories at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 60)


if __name__ == "__main__":
    main()
