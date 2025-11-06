#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Unassign all tasks from user_id = 5 (admin)
#

import os
import sys
from typing import Dict, List, Optional

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
TARGET_USER_ID = 5


def authenticate() -> Optional[str]:
    """Authenticate with Taiga."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_all_stories(auth_token: str, project_id: int) -> List[Dict]:
    """Get all user stories."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def unassign_story(auth_token: str, story_id: int, version: int) -> bool:
    """Unassign story (set assigned_to to None)."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {"assigned_to": None, "version": version}

    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Unassignment response: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error unassigning story: {e}")
        return False


def main():
    """Unassign all tasks from user_id = 5."""
    print("=" * 70)
    print("Unassigning All Tasks from User ID 5 (admin)")
    print("=" * 70)
    print()

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")

    # Get project ID
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_response = requests.get(f"{API_ENDPOINT}/projects/by_slug", headers=headers, params={"slug": PROJECT_SLUG})
    if project_response.status_code != 200:
        print("❌ Project not found")
        return 1
    project_id = project_response.json().get("id")
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")
    print()

    # Get all stories
    print("📋 Fetching all stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(all_stories)} total stories")
    print()

    # Find stories assigned to user_id = 5
    assigned_to_5 = []
    for story in all_stories:
        assigned_to = story.get("assigned_to")
        if assigned_to == TARGET_USER_ID:
            assigned_to_5.append(story)

    if not assigned_to_5:
        print(f"✅ No stories found assigned to user_id {TARGET_USER_ID}")
        return 0

    print(f"📋 Found {len(assigned_to_5)} stories assigned to user_id {TARGET_USER_ID}")
    print()
    print("Stories to unassign:")
    print("-" * 70)
    for story in assigned_to_5:
        ref = story.get("ref")
        subject = story.get("subject", "No subject")
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"
        print(f"  US#{ref}: {subject[:60]}... | Status: {status}")
    print()

    # Confirm
    print("=" * 70)
    print(f"⚠️  About to unassign {len(assigned_to_5)} stories")
    print("=" * 70)

    # Unassign all
    unassigned_count = 0
    failed_count = 0

    for story in assigned_to_5:
        ref = story.get("ref")
        story_id = story.get("id")
        version = story.get("version", 1)

        if unassign_story(auth_token, story_id, version):
            print(f"✅ Unassigned US#{ref}")
            unassigned_count += 1
        else:
            print(f"❌ Failed to unassign US#{ref}")
            failed_count += 1

    print()
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"✅ Successfully unassigned: {unassigned_count}")
    if failed_count > 0:
        print(f"❌ Failed to unassign: {failed_count}")
    print()

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
