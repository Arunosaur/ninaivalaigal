#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Find stories assigned to Developer F, or find the most pressing unassigned story
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
DEVELOPER_F_USERNAME = "developer-f"


def authenticate() -> Optional[str]:
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
    # Try to get user by username
    url = f"{API_ENDPOINT}/users"
    params = {"username": username}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("username") == username:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"⚠️  Error getting user ID: {e}")
        # Try alternative: get project members
        url = f"{API_ENDPOINT}/projects/{get_project_id(auth_token)}/members"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            members = response.json()
            for member in members:
                if member.get("user", {}).get("username") == username:
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


def get_status_info(auth_token: str, project_id: int) -> Dict[str, Dict]:
    """Get all status information."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return {s["name"]: s for s in response.json()}
        return {}
    except Exception as e:
        print(f"⚠️  Error getting status info: {e}")
        return {}


def prioritize_story(story: Dict) -> int:
    """Return priority score (higher = more pressing)."""
    score = 0

    # Status priority
    status_name = story.get("status_extra_info", {}).get("name", "").lower()
    if status_name in ["new", "ready"]:
        score += 10
    elif status_name in ["in progress", "working"]:
        score += 5

    # Subject/description keywords
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()
    text = f"{subject} {description}"

    # Critical keywords
    if any(kw in text for kw in ["critical", "blocker", "security", "urgent", "p0"]):
        score += 20
    elif any(kw in text for kw in ["high", "important", "p1", "priority"]):
        score += 10
    elif any(kw in text for kw in ["spec-", "governance", "deprecate"]):
        score += 5

    # Tags
    tags = story.get("tags", [])
    tag_text = " ".join([str(t) for t in tags]).lower()
    if "p0" in tag_text or "critical" in tag_text:
        score += 15
    elif "p1" in tag_text or "high" in tag_text:
        score += 8

    # Reference number (lower = older, might be more pressing)
    ref = story.get("ref", 9999)
    if ref < 200:
        score += 5

    return score


def main():
    """Find Developer F stories or most pressing unassigned story."""
    print("=" * 70)
    print("Finding Stories for Developer F")
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

    # Get Developer F user ID
    print(f"🔍 Looking for user: {DEVELOPER_F_USERNAME}")
    developer_f_id = get_user_id(auth_token, DEVELOPER_F_USERNAME)

    # Get all stories
    print("📋 Fetching all stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(all_stories)} total stories")
    print()

    # Filter stories assigned to Developer F
    developer_f_stories = []
    if developer_f_id:
        for story in all_stories:
            assigned_to = story.get("assigned_to")
            if assigned_to == developer_f_id:
                developer_f_stories.append(story)

    if developer_f_stories:
        print("=" * 70)
        print(f"✅ Found {len(developer_f_stories)} stories assigned to Developer F")
        print("=" * 70)
        print()

        # Sort by priority
        developer_f_stories.sort(key=lambda s: prioritize_story(s), reverse=True)

        for i, story in enumerate(developer_f_stories[:5], 1):
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "No subject")
            status_info = story.get("status_extra_info", {})
            status = status_info.get("name", "Unknown") if status_info else "Unknown"
            priority_score = prioritize_story(story)

            print(f"{i}. US#{ref}: {subject}")
            print(f"   Status: {status} | Priority Score: {priority_score}")
            print(f"   ID: {story.get('id')}")
            print(f"   View: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
            print()

        # Return the most pressing one
        most_pressing = developer_f_stories[0]
        print("=" * 70)
        print("🎯 MOST PRESSING STORY FOR DEVELOPER F:")
        print("=" * 70)
        print(f"US#{most_pressing.get('ref')}: {most_pressing.get('subject')}")
        print(f"Status: {most_pressing.get('status_extra_info', {}).get('name', 'Unknown')}")
        print(f"Description: {most_pressing.get('description', 'No description')[:200]}...")
        print(f"\nView at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{most_pressing.get('ref')}")
        return 0

    else:
        print(f"⚠️  No stories found assigned to Developer F")
        if not developer_f_id:
            print(f"   (User '{DEVELOPER_F_USERNAME}' not found)")
        print()
        print("=" * 70)
        print("🔍 Looking for most pressing UNASSIGNED story")
        print("=" * 70)
        print()

        # Get unassigned stories
        unassigned = []
        for story in all_stories:
            assigned_to = story.get("assigned_to")
            # Check if truly unassigned (None, 0, or empty)
            if not assigned_to or assigned_to == 0:
                # Exclude Done/Closed stories
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

        # Show top 5
        print("Top 5 most pressing unassigned stories:")
        print("-" * 70)
        for i, story in enumerate(unassigned[:5], 1):
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "No subject")
            status_info = story.get("status_extra_info", {})
            status = status_info.get("name", "Unknown") if status_info else "Unknown"
            priority_score = prioritize_story(story)

            print(f"{i}. US#{ref}: {subject}")
            print(f"   Status: {status} | Priority Score: {priority_score}")
            print(f"   ID: {story.get('id')}")
            print(f"   View: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
            print()

        # Return the most pressing one
        most_pressing = unassigned[0]
        print("=" * 70)
        print("🎯 MOST PRESSING UNASSIGNED STORY:")
        print("=" * 70)
        print(f"US#{most_pressing.get('ref')}: {most_pressing.get('subject')}")
        print(f"Status: {most_pressing.get('status_extra_info', {}).get('name', 'Unknown')}")
        description = most_pressing.get("description", "No description")
        if description:
            print(f"\nDescription:\n{description[:500]}")
            if len(description) > 500:
                print("...")
        print(f"\nView at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{most_pressing.get('ref')}")
        print()
        print("=" * 70)
        print("📝 NEXT STEPS:")
        print("=" * 70)
        print(f"1. Review the story: US#{most_pressing.get('ref')}")
        print(f"2. Start working on it")
        print(f"3. Update status to 'In Progress' if needed")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
