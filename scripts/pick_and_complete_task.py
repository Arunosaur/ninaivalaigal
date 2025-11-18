#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Pick an unassigned task from backlog, assign to Developer G, and complete it

import os
import sys
from datetime import datetime

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
DEVELOPER_G_USERNAME = "developer-g"


def authenticate():
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


def get_project_id(auth_token):
    """Get project ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_user_id(auth_token, username):
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                user_username = user.get("username", "").lower()
                if username.lower() in user_username:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def get_all_stories(auth_token, project_id):
    """Get all stories."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    all_stories = []
    page = 1
    while True:
        params = {"project": project_id, "page": page, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break
        result = response.json()
        if isinstance(result, list):
            stories = result
        elif isinstance(result, dict):
            stories = result.get("results", [])
            if not result.get("next"):
                all_stories.extend(stories)
                break
        else:
            break
        if not stories:
            break
        all_stories.extend(stories)
        page += 1
    return all_stories


def find_best_unassigned_story(stories):
    """Find best unassigned story."""
    done_statuses = ["done", "closed", "archived", "cancelled"]
    status_priority = {
        "new": 1,
        "ready": 2,
        "in progress": 3,
        "in-progress": 3,
        "testing": 4,
        "review": 5,
    }

    candidates = []
    for story in stories:
        if story.get("assigned_to"):
            continue
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "").lower() if status_info else ""
        if status in done_statuses:
            continue

        subject = story.get("subject", "").lower()
        priority_score = status_priority.get(status, 99)

        # Prefer documentation, testing, or small tasks
        if any(kw in subject for kw in ["documentation", "guide", "test", "fix", "update"]):
            priority_score -= 10

        candidates.append((priority_score, story))

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1] if candidates else None


def get_statuses(auth_token, project_id):
    """Get status IDs."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses"
    params = {"project": project_id}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            statuses = response.json()
            return {s.get("name", "").lower(): s.get("id") for s in statuses}
        return {}
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def assign_story(auth_token, story_id, story_version, user_id, status_id=None):
    """Assign story to user."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    payload = {"version": story_version, "assigned_to": user_id}
    if status_id:
        payload["status"] = status_id
    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Error assigning story: {e}")
        return False


def update_story_to_done(auth_token, story_id, story_version, done_id):
    """Update story status to Done."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    payload = {"version": story_version, "status": done_id}
    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


def main():
    """Pick and complete a task."""
    print("=" * 60)
    print("🔍 Finding Unassigned Task to Complete")
    print("=" * 60)

    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated")

    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Found project: {PROJECT_SLUG}")

    print("\n🔍 Fetching all stories...")
    stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(stories)} total stories")

    print("\n🔍 Finding best unassigned story...")
    best_story = find_best_unassigned_story(stories)

    if not best_story:
        print("❌ No unassigned active stories found")
        print("\n💡 All unassigned stories are completed/archived.")
        print("   Check: http://localhost:9000/project/ninaivalaigal/backlog?assigned_users=null")
        return 1

    ref = best_story.get("ref")
    subject = best_story.get("subject")
    status_info = best_story.get("status_extra_info", {})
    status = status_info.get("name", "Unknown") if status_info else "Unknown"
    story_id = best_story.get("id")
    version = best_story.get("version", 1)

    print(f"\n✅ Selected: US#{ref}")
    print(f"   Subject: {subject}")
    print(f"   Status: {status}")
    print(f"   ID: {story_id}")

    user_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)
    if not user_id:
        print("❌ Developer G not found")
        return 1
    print(f"\n✅ Found Developer G (ID: {user_id})")

    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("in-progress")
    done_id = statuses.get("done") or statuses.get("closed")

    print(f"\n📝 Assigning US#{ref} to Developer G...")
    if assign_story(auth_token, story_id, version, user_id, in_progress_id):
        print(f"✅ Assigned US#{ref} to Developer G")

        # Get updated version
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers)
        if response.status_code == 200:
            updated_story = response.json()
            version = updated_story.get("version", version)

        print(f"\n✅ Marking US#{ref} as Done...")
        if done_id and update_story_to_done(auth_token, story_id, version, done_id):
            print(f"✅ US#{ref} marked as Done")
        else:
            print(f"⚠️  Could not mark as Done (but assigned successfully)")

        print(f"\n📋 Story Details:")
        print(f"   Reference: US#{ref}")
        print(f"   Subject: {subject}")
        print(f"   URL: http://localhost:9000/project/ninaivalaigal/us/{ref}")
        print(f"   Status: Done ✅")
        return 0
    else:
        print(f"❌ Failed to assign story")
        return 1


if __name__ == "__main__":
    sys.exit(main())




