#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Find and assign most pressing unassigned Taiga stories to Developer G.
Also shows stories already assigned to Developer G.
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
DEVELOPER_G_USERNAME = "developer-g"

# Priority keywords for pressing stories
PRIORITY_KEYWORDS = [
    "p0",
    "critical",
    "security",
    "blocker",
    "urgent",
    "high-priority",
    "compliance",
    "gdpr",
    "hipaa",
    "privacy",
    "data leak",
    "cross-org",
    "auth",
    "authentication",
    "authorization",
    "rate limit",
    "api",
    "endpoint",
    "integration",
    "refactor",
    "technical debt",
    "legacy",
]

# Status priority (lower number = higher priority)
STATUS_PRIORITY = {
    "ready": 1,
    "new": 2,
    "in progress": 3,
    "in-progress": 3,
    "testing": 4,
    "review": 5,
    "done": 99,
    "closed": 99,
    "archived": 99,
    "cancelled": 99,
}


def authenticate():
    """Authenticate with Taiga."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token"), response.json()
        return None, None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None, None


def get_project_id(auth_token):
    """Get project ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception:
        return None


def get_all_stories(auth_token, project_id):
    """Get all stories from project with pagination."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}

    all_stories = []
    page = 1
    while True:
        params["page"] = page
        params["page_size"] = 100
        try:
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
        except Exception:
            break

    return all_stories


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
    except Exception:
        return None


def get_statuses(auth_token, project_id):
    """Get all statuses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                name = status.get("name", "").lower()
                statuses[name] = status.get("id")
            return statuses
        return {}
    except Exception:
        return {}


def calculate_priority_score(story):
    """Calculate priority score for a story (lower = higher priority)."""
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()
    tags = story.get("tags", [])
    tag_names = [t[0] if isinstance(t, list) else str(t).lower() for t in tags]

    status_info = story.get("status_extra_info", {})
    status = status_info.get("name", "").lower() if status_info else "unknown"

    text = f"{subject} {description} {' '.join(tag_names)}"

    # Base priority from status
    priority_score = STATUS_PRIORITY.get(status, 50)

    # Boost priority for keywords
    for keyword in PRIORITY_KEYWORDS:
        if keyword.lower() in text:
            priority_score -= 10

    # Special boosts for critical keywords
    if any(kw in text for kw in ["p0", "critical", "security", "blocker"]):
        priority_score -= 20

    if any(kw in text for kw in ["gdpr", "compliance", "privacy", "data leak"]):
        priority_score -= 15

    if any(kw in text for kw in ["auth", "authentication", "cross-org"]):
        priority_score -= 12

    return priority_score


def find_pressing_unassigned_stories(stories):
    """Find most pressing unassigned stories."""
    done_statuses = ["done", "closed", "archived", "cancelled"]

    candidates = []
    for story in stories:
        assigned_to = story.get("assigned_to")
        if assigned_to:
            continue  # Skip assigned stories

        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "").lower() if status_info else ""

        if status in done_statuses:
            continue  # Skip done/archived

        priority_score = calculate_priority_score(story)
        candidates.append((priority_score, story))

    # Sort by priority (lower is better)
    candidates.sort(key=lambda x: x[0])

    return [story for _, story in candidates]


def find_developer_g_stories(stories, developer_g_id):
    """Find stories already assigned to Developer G."""
    developer_g_stories = []

    for story in stories:
        assigned_to = story.get("assigned_to")
        if assigned_to:
            # Handle different response formats
            if isinstance(assigned_to, dict):
                if assigned_to.get("id") == developer_g_id:
                    developer_g_stories.append(story)
            elif isinstance(assigned_to, int) and assigned_to == developer_g_id:
                developer_g_stories.append(story)

    return developer_g_stories


def assign_story(auth_token, story_id, story_version, user_id, status_id=None):
    """Assign story to user and optionally set status."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {
        "version": story_version,
        "assigned_to": user_id,
    }

    if status_id:
        data["status"] = status_id

    try:
        response = requests.patch(url, headers=headers, json=data)
        return response.status_code in [200, 204], response.text
    except Exception as e:
        return False, str(e)


def main():
    """Main function to find and assign pressing stories."""
    print("=" * 80)
    print("FINDING AND ASSIGNING PRESSING STORIES TO DEVELOPER G")
    print("=" * 80)
    print()

    # Authenticate
    auth_token, user_data = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print(f"✅ Authenticated as: {user_data.get('username')} (ID: {user_data.get('id')})")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")
    print()

    # Get Developer G user ID
    print(f"🔍 Finding Developer G...")
    developer_g_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)
    if not developer_g_id:
        print(f"⚠️  Developer G (username: {DEVELOPER_G_USERNAME}) not found")
        print("   Attempting to use admin account as Developer G...")
        admin_id = user_data.get("id")
        if admin_id:
            developer_g_id = admin_id
            print(f"✅ Using admin account (ID: {developer_g_id}) as Developer G")
            print("   NOTE: Please create Developer G user in Taiga UI and reassign later")
        else:
            print("❌ Could not find Developer G or admin account")
            return 1
    else:
        print(f"✅ Found Developer G (User ID: {developer_g_id})")
    print()

    # Get all stories
    print(f"🔍 Fetching all stories...")
    stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(stories)} total stories")
    print()

    # Find stories already assigned to Developer G
    print(f"🔍 Finding stories already assigned to Developer G...")
    dev_g_stories = find_developer_g_stories(stories, developer_g_id)
    print(f"✅ Found {len(dev_g_stories)} stories assigned to Developer G")
    print()

    if dev_g_stories:
        print("=" * 80)
        print("STORIES ALREADY ASSIGNED TO DEVELOPER G")
        print("=" * 80)
        print()

        # Filter out done stories
        active_dev_g_stories = []
        for story in dev_g_stories:
            status_info = story.get("status_extra_info", {})
            status = status_info.get("name", "").lower() if status_info else ""
            if status not in ["done", "closed", "archived", "cancelled"]:
                active_dev_g_stories.append(story)

        if active_dev_g_stories:
            for story in active_dev_g_stories[:10]:  # Show first 10
                ref = story.get("ref")
                subject = story.get("subject", "")[:65]
                status_info = story.get("status_extra_info", {})
                status = status_info.get("name", "Unknown") if status_info else "Unknown"

                print(f"  US#{ref}: {subject}")
                print(f"    Status: {status}")
                print(f"    URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
                print()

            if len(active_dev_g_stories) > 10:
                print(f"  ... and {len(active_dev_g_stories) - 10} more active stories")
                print()
        else:
            print("  All assigned stories are completed/archived.")
            print()
    else:
        print("  No stories currently assigned to Developer G.")
        print()

    # Find pressing unassigned stories
    print("=" * 80)
    print("FINDING MOST PRESSING UNASSIGNED STORIES")
    print("=" * 80)
    print()

    pressing_stories = find_pressing_unassigned_stories(stories)

    if not pressing_stories:
        print("❌ No unassigned active stories found.")
        print()
        print("All active stories are assigned or all unassigned are done/archived.")
        return 0

    print(f"✅ Found {len(pressing_stories)} pressing unassigned stories")
    print()

    # Show top stories
    print("=" * 80)
    print("TOP 10 MOST PRESSING UNASSIGNED STORIES")
    print("=" * 80)
    print()

    for i, story in enumerate(pressing_stories[:10], 1):
        ref = story.get("ref")
        subject = story.get("subject", "")[:65]
        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"
        priority_score = calculate_priority_score(story)

        print(f"{i}. US#{ref}: {subject}")
        print(f"   Status: {status} | Priority Score: {priority_score}")
        print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
        print()

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("in-progress") or statuses.get("working on it")

    # Assign top 3-5 stories
    print("=" * 80)
    print("ASSIGNING TOP PRESSING STORIES TO DEVELOPER G")
    print("=" * 80)
    print()

    stories_to_assign = pressing_stories[:5]  # Top 5
    assigned_count = 0

    for story in stories_to_assign:
        ref = story.get("ref")
        subject = story.get("subject", "")[:65]
        story_id = story.get("id")
        story_version = story.get("version", 1)

        print(f"📝 Assigning US#{ref}: {subject[:50]}...")

        success, response_text = assign_story(
            auth_token,
            story_id,
            story_version,
            developer_g_id,
            status_id=in_progress_id if in_progress_id else None,
        )

        if success:
            print(f"  ✅ Assigned to Developer G")
            if in_progress_id:
                print(f"  ✅ Status set to 'In Progress'")
            assigned_count += 1
        else:
            print(f"  ❌ Failed to assign")
            print(f"     Error: {response_text[:200]}")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Stories already assigned to Developer G: {len(dev_g_stories)}")
    print(f"✅ Newly assigned stories: {assigned_count}")
    print(f"✅ Total active stories for Developer G: {len(dev_g_stories) + assigned_count}")
    print()
    print(f"📋 View stories at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print()

    if active_dev_g_stories or assigned_count > 0:
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("1. Review the assigned stories above")
        print("2. Start working on the highest priority stories")
        print("3. Update story status as you make progress")
        print("4. Run this script again to get more stories when ready")
        print()

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
