#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Move stories from infrastructure-tools project to ninaivalaigal project
# Only moves stories created in the last 3 days

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

SOURCE_PROJECT_SLUG = "infrastructure-tools"
TARGET_PROJECT_SLUG = "ninaivalaigal"
DAYS_TO_CHECK = 3


def authenticate() -> Optional[str]:
    """Authenticate with Taiga and return auth token."""
    print("🔐 Authenticating with Taiga...")
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            auth_token = response.json().get("auth_token")
            print("✅ Authenticated")
            return auth_token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token: str, project_slug: str) -> Optional[int]:
    """Get project ID by slug."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={project_slug}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            project = response.json()
            project_id = project.get("id")
            project_name = project.get("name")
            print(f"✅ Found project: {project_name} (ID: {project_id})")
            return project_id
        else:
            print(f"❌ Project not found: {project_slug} (status: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_recent_stories(auth_token: str, project_id: int, days: int = 3) -> List[Dict]:
    """Get stories created or modified in the last N days."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_timestamp = cutoff_date.timestamp()

    print(f"\n📅 Looking for stories created/modified after {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}...")

    # Get all user stories for the project
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get stories: {response.status_code}")
            return []

        all_stories = response.json()
        print(f"   Found {len(all_stories)} total stories in project")

        # Filter stories created or modified in last N days
        recent_stories = []
        for story in all_stories:
            story_ref = story.get("ref", "?")
            story_subject = story.get("subject", "N/A")

            # Check created_date
            created_date_str = story.get("created_date")
            modified_date_str = story.get("modified_date")

            is_recent = False
            date_type = None

            if created_date_str:
                try:
                    # Parse ISO format: "2025-11-02T12:34:56.789Z"
                    created_clean = created_date_str.replace("Z", "").split(".")[0]
                    created_date = datetime.fromisoformat(created_clean)
                    created_timestamp = created_date.timestamp()

                    if created_timestamp >= cutoff_timestamp:
                        is_recent = True
                        date_type = "created"
                        print(f"   ✅ Found recent story (created): US#{story_ref} - {story_subject[:60]}...")
                        print(f"      Created: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    pass

            # Also check modified_date if not already found
            if not is_recent and modified_date_str:
                try:
                    modified_clean = modified_date_str.replace("Z", "").split(".")[0]
                    modified_date = datetime.fromisoformat(modified_clean)
                    modified_timestamp = modified_date.timestamp()

                    if modified_timestamp >= cutoff_timestamp:
                        is_recent = True
                        date_type = "modified"
                        print(f"   ✅ Found recent story (modified): US#{story_ref} - {story_subject[:60]}...")
                        print(f"      Modified: {modified_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    pass

            if is_recent:
                recent_stories.append(story)

        return recent_stories
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def move_story(auth_token: str, story: Dict, target_project_id: int) -> bool:
    """Move a story to target project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    story_id = story.get("id")
    story_ref = story.get("ref")
    story_subject = story.get("subject", "N/A")

    print(f"\n📦 Moving US#{story_ref}: {story_subject[:60]}...")

    # Update story to change project
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    payload = {
        "project": target_project_id,
        # Keep all other fields
        "subject": story.get("subject"),
        "description": story.get("description"),
        "status": story.get("status"),
        "assigned_to": story.get("assigned_to"),
        "tags": story.get("tags", []),
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code in [200, 204]:
            print(f"   ✅ Successfully moved US#{story_ref} to ninaivalaigal project")
            return True
        else:
            print(f"   ❌ Failed to move story: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error moving story: {e}")
        return False


def main():
    print("=" * 80)
    print("🔄 Moving Stories from infrastructure-tools to ninaivalaigal")
    print("=" * 80)
    print(f"📅 Checking stories created in the last {DAYS_TO_CHECK} days...")

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        sys.exit(1)

    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get project IDs
    print(f"\n📋 Getting project information...")
    source_project_id = get_project_id(auth_token, SOURCE_PROJECT_SLUG)
    if not source_project_id:
        print(f"❌ Source project '{SOURCE_PROJECT_SLUG}' not found")
        sys.exit(1)

    target_project_id = get_project_id(auth_token, TARGET_PROJECT_SLUG)
    if not target_project_id:
        print(f"❌ Target project '{TARGET_PROJECT_SLUG}' not found")
        sys.exit(1)

    # Get recent stories
    recent_stories = get_recent_stories(auth_token, source_project_id, DAYS_TO_CHECK)

    if not recent_stories:
        print(f"\n✅ No stories found created in the last {DAYS_TO_CHECK} days")
        print("   Nothing to move.")
        return

    print(f"\n📊 Found {len(recent_stories)} stories to move")

    # Confirm before moving
    print(f"\n⚠️  About to move {len(recent_stories)} stories:")
    for story in recent_stories:
        print(f"   - US#{story.get('ref')}: {story.get('subject', 'N/A')[:70]}")

    response = input(f"\n❓ Proceed with moving these {len(recent_stories)} stories? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("❌ Cancelled by user")
        return

    # Move stories
    print(f"\n🚀 Moving stories...")
    moved_count = 0
    failed_count = 0

    for story in recent_stories:
        if move_story(auth_token, story, target_project_id):
            moved_count += 1
        else:
            failed_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"   ✅ Successfully moved: {moved_count}/{len(recent_stories)}")
    if failed_count > 0:
        print(f"   ❌ Failed to move: {failed_count}/{len(recent_stories)}")
    print(f"\n✅ Stories moved from '{SOURCE_PROJECT_SLUG}' to '{TARGET_PROJECT_SLUG}'")
    print("   (Stories are automatically removed from source project when moved)")


if __name__ == "__main__":
    main()
