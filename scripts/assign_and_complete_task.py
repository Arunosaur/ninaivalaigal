#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Find an unassigned task, assign it to Developer G, and complete it

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
        else:
            print(f"❌ Authentication failed: {response.status_code}")
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
                full_name = user.get("full_name", "").lower() if user.get("full_name") else ""

                if username.lower() in user_username or username.lower() in full_name:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def get_unassigned_stories(auth_token, project_id):
    """Get unassigned stories, prioritizing 'New' or 'Ready' status."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            stories = response.json()
            unassigned = []

            for story in stories:
                assigned_to = story.get("assigned_to")
                status_info = story.get("status_extra_info", {})
                status_name = status_info.get("name", "").lower() if status_info else ""

                # Only get unassigned, active stories
                if not assigned_to and status_name not in ["done", "archived", "closed", "cancelled"]:
                    unassigned.append(story)

            # Prioritize: New, Ready, In Progress, then others
            priority_order = ["new", "ready", "in progress", "in-progress"]
            unassigned.sort(
                key=lambda x: (
                    (
                        priority_order.index(status_info.get("name", "").lower())
                        if status_info.get("name", "").lower() in priority_order
                        else 999
                    ),
                    x.get("ref", 0),
                )
            )

            return unassigned
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


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


def assign_story(auth_token, story_id, user_id, status_id=None):
    """Assign story to user and optionally set status."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    payload = {"assigned_to": user_id}
    if status_id:
        payload["status"] = status_id

    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error assigning story: {e}")
        return False


def main():
    """Find, assign, and complete a task."""
    print("=" * 60)
    print("🔍 Finding Unassigned Task to Complete")
    print("=" * 60)

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")

    # Get project
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")

    # Get unassigned stories
    print("\n🔍 Searching for unassigned stories...")
    unassigned = get_unassigned_stories(auth_token, project_id)

    if not unassigned:
        print("❌ No unassigned stories found")
        return 1

    print(f"✅ Found {len(unassigned)} unassigned stories")
    print("\n📋 Top candidates:")
    for i, story in enumerate(unassigned[:5], 1):
        ref = story.get("ref", "N/A")
        subject = story.get("subject", "No subject")
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"
        print(f"  {i}. US#{ref}: {subject} [{status}]")

    # Select the first one
    selected = unassigned[0]
    ref = selected.get("ref", "N/A")
    subject = selected.get("subject", "No subject")

    print(f"\n✅ Selected: US#{ref}: {subject}")

    # Get Developer G user ID
    print("\n👤 Getting Developer G user ID...")
    user_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)
    if not user_id:
        print("❌ Developer G not found")
        return 1
    print(f"✅ Found Developer G (ID: {user_id})")

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("in-progress")

    # Assign story
    print(f"\n📝 Assigning US#{ref} to Developer G...")
    success = assign_story(auth_token, selected.get("id"), user_id, in_progress_id)

    if success:
        print(f"✅ Successfully assigned US#{ref} to Developer G")
        print(f"\n📋 Task Details:")
        print(f"   Story: US#{ref}")
        print(f"   Subject: {subject}")
        print(f"   Assigned to: Developer G")
        print(f"   Status: In Progress")
        print(f"\n💡 Next steps: Complete the task implementation")
        return 0
    else:
        print(f"❌ Failed to assign story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
