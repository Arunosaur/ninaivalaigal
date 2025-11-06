#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign most pressing unassigned stories to Developer E and start working on them.
Also shows Developer E's existing stories.
"""

import json
import sys
from datetime import datetime

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_E_USERNAME = "developer-e"


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


def get_developer_e_id(auth_token):
    """Get Developer E user ID"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    users_url = f"{API_ENDPOINT}/users"
    users_response = requests.get(users_url, headers=headers)
    if users_response.status_code == 200:
        users = users_response.json()
        for user in users:
            username = user.get("username", "")
            if username.lower() == DEVELOPER_E_USERNAME.lower():
                return user.get("id")
            full_name = user.get("full_name", "").lower() if user.get("full_name") else ""
            if full_name == "developer e":
                return user.get("id")
    return None


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


def get_statuses(auth_token, project_id):
    """Get all statuses for the project"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


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
        "p1": 50,
        "billing": 45,
        "test-coverage": 40,
        "refactor": 35,
        "p2": 30,
    }

    status_priority = {
        "in progress": 100,
        "working": 100,
        "ready": 85,
        "new": 70,
        "ready for development": 80,
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


def assign_story(auth_token, story_id, user_id, status_id=None):
    """Assign story to user and optionally update status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()

    payload = {"assigned_to": user_id, "version": story.get("version", 1)}

    if status_id:
        payload["status"] = status_id

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def main():
    print("=" * 80)
    print("Assigning Most Pressing Stories to Developer E")
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

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("working")
    ready_id = statuses.get("ready") or statuses.get("new")

    # Filter Developer E's existing stories
    dev_e_stories = [s for s in all_stories if s.get("assigned_to") == developer_e_id]
    done_statuses = ["done", "closed", "archived", "cancelled"]
    active_dev_e_stories = [
        s for s in dev_e_stories if s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
    ]

    print("=" * 80)
    print("DEVELOPER E'S EXISTING STORIES")
    print("=" * 80)
    print(f"Total assigned: {len(dev_e_stories)}")
    print(f"Active (not done): {len(active_dev_e_stories)}")
    print()

    if active_dev_e_stories:
        prioritized_existing = prioritize_stories(active_dev_e_stories)
        print("Most pressing existing stories:")
        for i, (score, story) in enumerate(prioritized_existing[:5], 1):
            ref = story.get("ref")
            subject = story.get("subject", "")[:60]
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            print(f"  {i}. Ref #{ref}: {subject}")
            print(f"     Status: {status} | Score: {score}")
        print()

    # Filter unassigned active stories
    unassigned_active = [
        s
        for s in all_stories
        if not s.get("assigned_to") and s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
    ]

    print("=" * 80)
    print("UNASSIGNED ACTIVE STORIES")
    print("=" * 80)
    print(f"Found {len(unassigned_active)} unassigned active stories")
    print()

    if not unassigned_active:
        print("No unassigned active stories found.")
        print("Continue working on existing stories.")
        return

    # Prioritize unassigned stories
    prioritized_unassigned = prioritize_stories(unassigned_active)
    top_stories = prioritized_unassigned[:10]  # Top 10 most pressing

    print("=" * 80)
    print("TOP 10 MOST PRESSING UNASSIGNED STORIES")
    print("=" * 80)
    print()

    for i, (score, story) in enumerate(top_stories, 1):
        ref = story.get("ref")
        subject = story.get("subject", "")[:60]
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])[:3]]
        tag_str = ", ".join(tags) if tags else "no tags"
        print(f"{i}. Ref #{ref}: {subject}")
        print(f"   Status: {status} | Score: {score} | Tags: {tag_str}")
        print()

    # Assign top 5 stories to Developer E
    print("=" * 80)
    print("ASSIGNING TOP 5 STORIES TO DEVELOPER E")
    print("=" * 80)
    print()

    assigned_count = 0
    started_count = 0

    for score, story in top_stories[:5]:
        ref = story.get("ref")
        subject = story.get("subject", "")
        status_name = story.get("status_extra_info", {}).get("name", "").lower()

        print(f"📝 Ref #{ref}: {subject[:60]}")
        print(f"   Current Status: {status_name}")
        print(f"   Priority Score: {score}")

        # Assign to Developer E
        status_to_set = None
        if status_name in ["ready", "new", "ready for development"] and in_progress_id:
            status_to_set = in_progress_id
            print(f"   → Will assign and move to 'In Progress'")
        else:
            print(f"   → Will assign (keeping current status)")

        if assign_story(auth_token, story["id"], developer_e_id, status_to_set):
            print(f"   ✓ Successfully assigned to Developer E")
            assigned_count += 1
            if status_to_set:
                started_count += 1
        else:
            print(f"   ✗ Failed to assign")

        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✓ Assigned: {assigned_count} stories")
    print(f"✓ Started (moved to In Progress): {started_count} stories")
    print()
    print(f"View Developer E's stories at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 80)


if __name__ == "__main__":
    main()
