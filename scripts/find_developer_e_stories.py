#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Find all stories assigned to Developer E and identify the most pressing one"""

import json
import sys
from datetime import datetime

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_E = "Developer E"


def authenticate():
    """Authenticate with Taiga and return auth token"""
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        print(f"Authentication failed: {auth.status_code}")
        sys.exit(1)
    return auth.json()["auth_token"], auth.json()


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get project: {response.status_code}")
        sys.exit(1)
    return response.json()["id"]


def get_all_stories(auth_token, project_id):
    """Get all user stories with pagination"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    all_stories = []

    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    params = {"project": project_id, "page_size": 1000}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list):
            all_stories.extend(result)
        elif isinstance(result, dict):
            all_stories.extend(result.get("results", []))
            if result.get("next"):
                page = 2
                while True:
                    next_url = f"{url}&page={page}"
                    next_response = requests.get(next_url, headers=headers)
                    if next_response.status_code == 200:
                        next_result = next_response.json()
                        if isinstance(next_result, dict):
                            all_stories.extend(next_result.get("results", []))
                            if not next_result.get("next"):
                                break
                        else:
                            break
                        page += 1
                    else:
                        break

    return all_stories


def get_developer_e_id(auth_token):
    """Get Developer E user ID"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    users_url = f"{API_ENDPOINT}/users"
    users_response = requests.get(users_url, headers=headers)
    if users_response.status_code == 200:
        users = users_response.json()
        for user in users:
            username = user.get("username", "")
            if username.lower() == "developer-e":
                return user.get("id")
            full_name = user.get("full_name", "").lower() if user.get("full_name") else ""
            if full_name == "developer e":
                return user.get("id")
    return None


def prioritize_stories(stories):
    """Prioritize stories based on status, tags, and keywords"""
    priority_keywords = {
        "p0": 100,
        "critical": 90,
        "security": 85,
        "blocker": 80,
        "urgent": 75,
        "auth": 70,
        "orm": 65,
        "guardrail": 60,
        "high-priority": 55,
    }

    status_priority = {
        "in progress": 100,
        "working": 100,
        "ready": 80,
        "new": 70,
        "ready for development": 75,
        "todo": 60,
        "backlog": 50,
        "done": 10,
        "closed": 5,
        "archived": 0,
        "cancelled": 0,
    }

    prioritized = []
    for story in stories:
        score = 0
        status = story.get("status_extra_info", {}).get("name", "").lower()
        score += status_priority.get(status, 50)

        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = [t[0] if isinstance(t, list) else t.lower() for t in story.get("tags", [])]
        text = f"{subject} {description} {' '.join(tags)}"

        for keyword, weight in priority_keywords.items():
            if keyword in text:
                score += weight

        prioritized.append((score, story))

    return sorted(prioritized, key=lambda x: x[0], reverse=True)


def main():
    print("=" * 80)
    print("Finding Stories Assigned to Developer E")
    print("=" * 80)
    print()

    # Authenticate
    auth_token, user_data = authenticate()
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_data['id']})")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get Developer E ID
    developer_e_id = get_developer_e_id(auth_token)
    if not developer_e_id:
        print("❌ ERROR: Developer E user not found")
        print("   Please create the user via Taiga web UI or Django shell")
        sys.exit(1)
    print(f"✓ Developer E ID: {developer_e_id}")
    print()

    # Get all stories
    print("Fetching all user stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✓ Found {len(all_stories)} total stories")
    print()

    # Filter stories assigned to Developer E
    dev_e_stories = [s for s in all_stories if s.get("assigned_to") == developer_e_id]
    print(f"✓ Found {len(dev_e_stories)} stories assigned to Developer E")
    print()

    if not dev_e_stories:
        print("No stories assigned to Developer E")
        print()
        print("Would you like to:")
        print("  1. Find unassigned stories to assign")
        print("  2. Check for stories in other statuses")
        return

    # Categorize stories
    done_statuses = ["done", "closed", "archived", "cancelled"]
    active_stories = [
        s for s in dev_e_stories if s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
    ]
    in_progress_stories = [
        s
        for s in active_stories
        if s.get("status_extra_info", {}).get("name", "").lower() in ["in progress", "working"]
    ]
    done_stories = [s for s in dev_e_stories if s.get("status_extra_info", {}).get("name", "").lower() in done_statuses]

    print("=" * 80)
    print("STORY BREAKDOWN")
    print("=" * 80)
    print(f"  Total assigned: {len(dev_e_stories)}")
    print(f"  Active (not done): {len(active_stories)}")
    print(f"  In Progress: {len(in_progress_stories)}")
    print(f"  Done/Closed: {len(done_stories)}")
    print()

    # Prioritize active stories
    if active_stories:
        prioritized = prioritize_stories(active_stories)
        most_pressing = prioritized[0][1]

        print("=" * 80)
        print("MOST PRESSING STORY")
        print("=" * 80)
        print()
        print(f"Ref: #{most_pressing.get('ref')}")
        print(f"Subject: {most_pressing.get('subject')}")
        print(f"Status: {most_pressing.get('status_extra_info', {}).get('name', 'Unknown')}")
        tags = [t[0] if isinstance(t, list) else t for t in most_pressing.get("tags", [])]
        print(f"Tags: {', '.join(tags[:5])}")
        description = most_pressing.get("description", "")
        if description:
            print(f"Description: {description[:300]}...")
        print()
        print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{most_pressing.get('ref')}")
        print()

        # Show other active stories
        if len(prioritized) > 1:
            print("=" * 80)
            print("OTHER ACTIVE STORIES (Priority Order)")
            print("=" * 80)
            print()
            for i, (score, story) in enumerate(prioritized[1:6], 2):  # Show next 5
                print(f"{i}. Ref #{story.get('ref')}: {story.get('subject')[:60]}")
                print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')} | Score: {score}")
                print()
    else:
        print("No active stories found for Developer E")
        print()
        if done_stories:
            print("Recent completed stories:")
            for story in sorted(done_stories, key=lambda x: x.get("ref", 0), reverse=True)[:5]:
                print(f"  • Ref #{story.get('ref')}: {story.get('subject')[:50]}")

    print("=" * 80)


if __name__ == "__main__":
    main()
