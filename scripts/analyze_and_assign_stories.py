#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Analyze all Taiga stories and assign most pressing ones
"""

import sys

import requests

# Taiga Configuration
TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"


def authenticate():
    """Authenticate with Taiga and return auth token"""
    url = f"{API_ENDPOINT}/auth"
    payload = {"type": "normal", "username": USERNAME, "password": PASSWORD}

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Authentication failed: {response.status_code}")
        sys.exit(1)

    auth_data = response.json()
    return auth_data["auth_token"], auth_data


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        sys.exit(1)

    project = response.json()
    return project["id"]


def get_all_user_stories(auth_token, project_id):
    """Get all user stories"""
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    return response.json()


def get_user_id(auth_token, username):
    """Get user ID by username"""
    url = f"{API_ENDPOINT}/users/me"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["id"]
    return None


def get_status_info(auth_token, project_id):
    """Get all status information"""
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"]: s for s in response.json()}
    return {}


def assign_story(auth_token, story_id, user_id):
    """Assign a story to a user"""
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Get current story
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()

    # Update assignment
    payload = {"assigned_to": user_id, "version": story.get("version", 1)}

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def update_story_status(auth_token, story_id, status_id):
    """Update story status"""
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Get current story
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()

    # Update status
    payload = {"status": status_id, "version": story.get("version", 1)}

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def analyze_and_prioritize_stories(stories):
    """Analyze stories and prioritize them"""
    priority_keywords = {
        "P0": ["critical", "blocker", "security", "p0", "high-priority", "urgent"],
        "P1": ["high", "important", "p1", "priority"],
        "P2": ["medium", "normal", "p2"],
        "P3": ["low", "nice-to-have", "p3"],
    }

    # Categorize stories
    prioritized = {"unassigned_p0": [], "unassigned_p1": [], "ready_to_start": [], "in_progress": [], "governance": []}

    for story in stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        assigned_to = story.get("assigned_to")
        status_name = story.get("status_extra_info", {}).get("name", "")
        tags = [tag[0] if isinstance(tag, list) else tag for tag in story.get("tags", [])]

        # Check if governance related
        is_governance = any(
            keyword in subject + " " + description
            for keyword in ["governance", "spec-", "deprecate", "boundary", "status"]
        )

        # Check priority
        priority = "P3"
        for p_level, keywords in priority_keywords.items():
            if any(kw in subject + " " + description + " " + " ".join(tags) for kw in keywords):
                priority = p_level
                break

        story_info = {
            "id": story["id"],
            "ref": story.get("ref"),
            "subject": story.get("subject"),
            "status": status_name,
            "priority": priority,
            "assigned_to": assigned_to,
            "tags": tags,
            "is_governance": is_governance,
        }

        # Categorize
        if not assigned_to:
            if priority == "P0":
                prioritized["unassigned_p0"].append(story_info)
            elif priority == "P1":
                prioritized["unassigned_p1"].append(story_info)

        if is_governance:
            prioritized["governance"].append(story_info)

        if status_name.lower() in ["ready", "new", "ready for development"]:
            prioritized["ready_to_start"].append(story_info)
        elif status_name.lower() in ["in progress", "working"]:
            prioritized["in_progress"].append(story_info)

    return prioritized


def main():
    print("=" * 70)
    print("Analyze and Assign Most Pressing Taiga Stories")
    print("=" * 70)
    print()

    # Authenticate
    auth_token, user_data = authenticate()
    user_id = user_data["id"]
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_id})")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get all stories
    print("Fetching all user stories...")
    stories = get_all_user_stories(auth_token, project_id)
    print(f"✓ Found {len(stories)} total stories")
    print()

    # Get status info
    status_info = get_status_info(auth_token, project_id)
    in_progress_status_id = None

    for status_name, status_data in status_info.items():
        if status_name.lower() in ["in progress", "working"]:
            in_progress_status_id = status_data["id"]

    # Analyze and prioritize
    print("Analyzing stories...")
    prioritized = analyze_and_prioritize_stories(stories)
    print()

    # Display analysis
    print("=" * 70)
    print("STORY ANALYSIS RESULTS")
    print("=" * 70)
    print()

    print("📊 Summary:")
    print(f"  • Total Stories: {len(stories)}")
    print(f"  • Unassigned P0: {len(prioritized['unassigned_p0'])}")
    print(f"  • Unassigned P1: {len(prioritized['unassigned_p1'])}")
    print(f"  • Governance Stories: {len(prioritized['governance'])}")
    print(f"  • Ready to Start: {len(prioritized['ready_to_start'])}")
    print()

    # Identify most pressing stories
    most_pressing = []

    # First priority: Unassigned P0 governance stories
    for story in prioritized["unassigned_p0"]:
        if story["is_governance"] and story["id"] not in [s["id"] for s in most_pressing]:
            most_pressing.append(story)

    # Second priority: Unassigned P1 governance stories
    for story in prioritized["unassigned_p1"]:
        if story["is_governance"] and story["id"] not in [s["id"] for s in most_pressing]:
            most_pressing.append(story)

    # Third priority: Any unassigned P0
    for story in prioritized["unassigned_p0"]:
        if story["id"] not in [s["id"] for s in most_pressing]:
            most_pressing.append(story)

    # Limit to top 5
    most_pressing = most_pressing[:5]

    print("=" * 70)
    print("MOST PRESSING STORIES")
    print("=" * 70)
    print()

    if not most_pressing:
        print("No unassigned high-priority stories found.")
        print("Checking ready-to-start stories...")
        most_pressing = prioritized["ready_to_start"][:5]

    if most_pressing:
        for i, story in enumerate(most_pressing, 1):
            print(f"{i}. Ref #{story['ref']}: {story['subject']}")
            print(f"   Priority: {story['priority']} | Governance: {story['is_governance']}")
            print(f"   Status: {story['status']}")
            print()

    print("=" * 70)
    print("ASSIGNING AND STARTING WORK")
    print("=" * 70)
    print()

    assigned_count = 0
    started_count = 0

    for story in most_pressing:
        print(f"Processing Ref #{story['ref']}: {story['subject']}")

        # Assign to myself
        if assign_story(auth_token, story["id"], user_id):
            print(f"  ✓ Assigned to {user_data.get('username')}")
            assigned_count += 1
        else:
            print("  ✗ Failed to assign")
            continue

        # Move to In Progress if ready
        if story["status"].lower() in ["ready", "new"] and in_progress_status_id:
            if update_story_status(auth_token, story["id"], in_progress_status_id):
                print("  ✓ Status updated to 'In Progress'")
                started_count += 1
            else:
                print("  ⚠ Could not update status")

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"✓ Assigned: {assigned_count} stories")
    print(f"✓ Started: {started_count} stories")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 70)


if __name__ == "__main__":
    main()
