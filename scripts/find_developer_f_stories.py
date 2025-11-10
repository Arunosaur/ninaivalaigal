#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Find stories assigned to Developer F

import os
import sys

import requests

# Taiga Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = os.getenv("TAIGA_PROJECT_SLUG", "ninaivalaigal")
DEVELOPER_F_USERNAME = "developer-f"


def authenticate():
    """Authenticate with Taiga API"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth",
            json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"⚠️  Authentication failed: {e}")
        return None


def get_project_id(auth_token):
    """Get project ID by slug"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        response = requests.get(
            f"{API_ENDPOINT}/projects/by_slug", headers=headers, params={"slug": PROJECT_SLUG}, timeout=10
        )
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"⚠️  Error getting project: {e}")
        return None


def get_user_id(auth_token, username, project_id):
    """Get user ID by username"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        response = requests.get(f"{API_ENDPOINT}/users", headers=headers, params={"project": project_id}, timeout=10)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("username") == username:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"⚠️  Error getting user: {e}")
        return None


def get_all_stories(auth_token, project_id):
    """Get all user stories from project"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    stories = []
    offset = 0
    page_size = 100

    while True:
        try:
            response = requests.get(
                f"{API_ENDPOINT}/userstories",
                headers=headers,
                params={"project": project_id, "offset": offset, "limit": page_size},
                timeout=30,
            )
            if response.status_code != 200:
                break
            data = response.json()
            if not data:
                break
            stories.extend(data)
            if len(data) < page_size:
                break
            offset += page_size
        except Exception as e:
            print(f"⚠️  Error fetching stories: {e}")
            break

    return stories


def main():
    print("=" * 80)
    print("Finding Stories Assigned to Developer F")
    print("=" * 80)
    print()

    # Authenticate
    print("🔐 Authenticating with Taiga...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed")
        return 1
    print("✅ Authenticated")
    print()

    # Get project
    print(f"📁 Getting project: {PROJECT_SLUG}...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer F user ID
    print(f"👤 Looking for user: {DEVELOPER_F_USERNAME}...")
    developer_f_id = get_user_id(auth_token, DEVELOPER_F_USERNAME, project_id)
    if not developer_f_id:
        print(f"❌ Developer F ({DEVELOPER_F_USERNAME}) not found")
        return 1
    print(f"✅ Developer F ID: {developer_f_id}")
    print()

    # Get all stories
    print("📋 Fetching all stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(all_stories)} total stories")
    print()

    # Filter stories assigned to Developer F
    developer_f_stories = []
    for story in all_stories:
        assigned_to = story.get("assigned_to")
        if assigned_to == developer_f_id:
            developer_f_stories.append(story)

    if not developer_f_stories:
        print("❌ No stories assigned to Developer F")
        print()
        print("Checking for unassigned stories...")

        # Find unassigned active stories
        unassigned = []
        for story in all_stories:
            assigned_to = story.get("assigned_to")
            status_info = story.get("status_extra_info", {})
            status_name = status_info.get("name", "").lower() if status_info else ""

            if assigned_to is None and status_name not in ["done", "archived", "closed", "cancelled"]:
                unassigned.append(story)

        if unassigned:
            print(f"✅ Found {len(unassigned)} unassigned active stories")
            print()
            print("Top 5 unassigned stories:")
            for i, story in enumerate(unassigned[:5], 1):
                status = story.get("status_extra_info", {}).get("name", "Unknown")
                print(f"  {i}. US#{story.get('ref')}: {story.get('subject')} ({status})")
                print(f"     URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story.get('ref')}")

        return 1

    print(f"✅ Found {len(developer_f_stories)} stories assigned to Developer F")
    print()

    # Categorize stories
    done_statuses = ["done", "closed", "archived", "cancelled"]
    active_stories = [
        s for s in developer_f_stories if s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
    ]
    in_progress = [
        s
        for s in active_stories
        if s.get("status_extra_info", {}).get("name", "").lower() in ["in progress", "working"]
    ]
    ready = [s for s in active_stories if s.get("status_extra_info", {}).get("name", "").lower() in ["ready", "new"]]

    print("=" * 80)
    print("STORY BREAKDOWN")
    print("=" * 80)
    print(f"  Total assigned: {len(developer_f_stories)}")
    print(f"  Active: {len(active_stories)}")
    print(f"  In Progress: {len(in_progress)}")
    print(f"  Ready/New: {len(ready)}")
    print(f"  Done: {len(developer_f_stories) - len(active_stories)}")
    print()

    if active_stories:
        print("=" * 80)
        print("ACTIVE STORIES (Priority Order)")
        print("=" * 80)
        print()

        # Sort by priority (In Progress first, then Ready)
        sorted_stories = sorted(
            active_stories,
            key=lambda s: (
                0 if s.get("status_extra_info", {}).get("name", "").lower() == "in progress" else 1,
                s.get("ref", 0),
            ),
        )

        for i, story in enumerate(sorted_stories, 1):
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            priority_map = {1: "Low", 2: "Normal", 3: "High"}
            priority = priority_map.get(story.get("priority", 2), "Normal")

            print(f"{i}. US#{ref}: {subject}")
            print(f"   Status: {status}")
            print(f"   Priority: {priority}")
            print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
            print()

        # Return the first active story for processing
        if sorted_stories:
            first_story = sorted_stories[0]
            print("=" * 80)
            print(f"🎯 NEXT STORY TO WORK ON: US#{first_story.get('ref')}")
            print("=" * 80)
            print(f"Subject: {first_story.get('subject')}")
            print(f"Status: {first_story.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{first_story.get('ref')}")
            print()
            return first_story.get("ref")

    return 0


if __name__ == "__main__":
    story_ref = main()
    if story_ref:
        sys.exit(0)
    else:
        sys.exit(1)
