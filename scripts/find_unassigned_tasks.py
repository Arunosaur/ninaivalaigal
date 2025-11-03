#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Find unassigned tasks/stories in Taiga for Developer G
"""

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


def get_unassigned_stories(auth_token, project_id):
    """Get all unassigned user stories."""
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
                # Check if unassigned (None or empty)
                if not assigned_to:
                    unassigned.append(story)
            return unassigned
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def main():
    """Find and display unassigned tasks."""
    print("=" * 60)
    print("Finding Unassigned Tasks for Developer G")
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
    print(f"\n🔍 Searching for unassigned stories...")
    unassigned = get_unassigned_stories(auth_token, project_id)

    if not unassigned:
        print("❌ No unassigned stories found")
        return 1

    print(f"\n✅ Found {len(unassigned)} unassigned stories:")
    print("=" * 60)

    # Sort by reference number
    unassigned.sort(key=lambda x: x.get("ref", 0))

    for i, story in enumerate(unassigned[:20], 1):  # Show first 20
        ref = story.get("ref", "N/A")
        subject = story.get("subject", "No subject")
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"

        print(f"\n{i}. US#{ref}: {subject}")
        print(f"   Status: {status}")
        print(f"   ID: {story.get('id')}")

    if len(unassigned) > 20:
        print(f"\n... and {len(unassigned) - 20} more")

    print("\n" + "=" * 60)
    print("Recommendations for Developer G:")
    print("=" * 60)

    # Suggest a good task (prefer "New" or "Ready" status)
    suggested = None
    for story in unassigned:
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "").lower() if status_info else ""
        if status in ["new", "ready", "in progress", "in-progress"]:
            suggested = story
            break

    if not suggested and unassigned:
        suggested = unassigned[0]

    if suggested:
        ref = suggested.get("ref", "N/A")
        subject = suggested.get("subject", "No subject")
        print(f"\n✅ Suggested: US#{ref}")
        print(f"   Subject: {subject}")
        print(f"\n   To assign and start:")
        print(f"   python3 scripts/assign_and_start_task.py {ref}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
