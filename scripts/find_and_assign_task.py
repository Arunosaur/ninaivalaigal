#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Find unassigned task and assign it to Developer F, then start working on it
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
DEVELOPER_F_USERNAME = "admin"  # Using admin as Developer F


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


def get_project_id(auth_token: str) -> Optional[int]:
    """Get project ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug"
    params = {"slug": PROJECT_SLUG}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_user_id(auth_token: str, username: str) -> Optional[int]:
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_id = get_project_id(auth_token)

    # Try project members first
    url = f"{API_ENDPOINT}/projects/{project_id}/members"
    members = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            members = response.json()
            for member in members:
                if member.get("user", {}).get("username") == username:
                    return member.get("user", {}).get("id")
    except Exception:
        pass

    # Fallback to admin if developer-f not found
    if username == "developer-f" and members:
        for member in members:
            if member.get("user", {}).get("username") == "admin":
                print(f"⚠️  Developer F not found, using admin")
                return member.get("user", {}).get("id")

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


def prioritize_story(story: Dict) -> int:
    """Return priority score (higher = more pressing)."""
    score = 0

    status_name = story.get("status_extra_info", {}).get("name", "").lower()
    if status_name in ["new", "ready"]:
        score += 10
    elif status_name in ["in progress", "working"]:
        score += 5

    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()
    text = f"{subject} {description}"

    if any(kw in text for kw in ["critical", "blocker", "security", "urgent", "p0"]):
        score += 20
    elif any(kw in text for kw in ["high", "important", "p1", "priority"]):
        score += 10

    ref = story.get("ref", 9999)
    if ref < 300:
        score += 5

    return score


def assign_story(auth_token: str, story_id: int, user_id: int, version: int) -> bool:
    """Assign story to user."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {"assigned_to": user_id, "version": version}

    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Assignment response: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error assigning story: {e}")
        return False


def main():
    """Find unassigned task, assign it, and start working."""
    print("=" * 70)
    print("Finding and Assigning Unassigned Task")
    print("=" * 70)
    print()

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
    print()

    # Get user ID
    print(f"🔍 Looking for user: {DEVELOPER_F_USERNAME}")
    user_id = get_user_id(auth_token, DEVELOPER_F_USERNAME)
    if not user_id:
        print("❌ User not found")
        return 1
    print(f"✅ Found user (ID: {user_id})")
    print()

    # Get all stories
    print("📋 Fetching all stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(all_stories)} total stories")
    print()

    # Find unassigned stories
    unassigned = []
    for story in all_stories:
        assigned_to = story.get("assigned_to")
        if not assigned_to or assigned_to == 0:
            status_name = story.get("status_extra_info", {}).get("name", "").lower()
            if status_name not in ["done", "closed", "archived", "cancelled"]:
                unassigned.append(story)

    if not unassigned:
        print("❌ No unassigned stories found")
        return 1

    print(f"✅ Found {len(unassigned)} unassigned stories")
    print()

    # Sort by priority
    unassigned.sort(key=lambda s: prioritize_story(s), reverse=True)

    # Show top 3
    print("Top 3 most pressing unassigned stories:")
    print("-" * 70)
    for i, story in enumerate(unassigned[:3], 1):
        ref = story.get("ref", "N/A")
        subject = story.get("subject", "No subject")
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"
        priority_score = prioritize_story(story)

        print(f"{i}. US#{ref}: {subject}")
        print(f"   Status: {status} | Priority Score: {priority_score}")
        print()

    # Assign the most pressing one
    selected = unassigned[0]
    ref = selected.get("ref")
    story_id = selected.get("id")
    version = selected.get("version", 1)

    print("=" * 70)
    print(f"🎯 ASSIGNING US#{ref} TO DEVELOPER F")
    print("=" * 70)
    print(f"Subject: {selected.get('subject')}")
    print(f"Status: {selected.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"Description: {selected.get('description', 'No description')[:200]}...")
    print()

    # Assign story
    if assign_story(auth_token, story_id, user_id, version):
        print(f"✅ Successfully assigned US#{ref} to Developer F")
        print(f"   View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
        print()
        print("=" * 70)
        print("📝 NEXT STEPS:")
        print("=" * 70)
        print(f"1. Review US#{ref}: {selected.get('subject')}")
        print(f"2. Start working on it")
        print(f"3. Update status to 'In Progress' if needed")
        print()
        return 0
    else:
        print(f"❌ Failed to assign US#{ref}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
