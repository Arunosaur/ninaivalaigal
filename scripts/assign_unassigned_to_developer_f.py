#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign unassigned stories to Developer F and start working on them
"""

import argparse
import os
import sys
from pathlib import Path

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
DEVELOPER_F_USERNAME = "developer-f"

REPO_ROOT = Path(__file__).parent.parent


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
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def get_unassigned_stories(auth_token, project_id, limit=10):
    """Get unassigned stories, prioritizing recently reopened ones."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"

    all_stories = []
    page = 1

    while len(all_stories) < limit * 2:  # Get more to filter
        params = {"project": project_id, "page": page, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            break

        result = response.json()
        if isinstance(result, list):
            stories = result
        elif isinstance(result, dict):
            stories = result.get("results", [])
        else:
            break

        if not stories:
            break

        all_stories.extend(stories)

        if isinstance(result, dict) and not result.get("next"):
            break

        page += 1

    # Filter: unassigned, not Done/Archived, preferably recently reopened
    unassigned = []
    reopened = []

    for story in all_stories:
        assigned_to = story.get("assigned_to")
        status_name = story.get("status_extra_info", {}).get("name", "").lower()

        if not assigned_to and status_name not in ["done", "archived"]:
            # Check if it was recently reopened
            description = story.get("description", "")
            if "Story Reopened" in description:
                reopened.append(story)
            else:
                unassigned.append(story)

    # Prioritize reopened stories
    selected = reopened[:limit] + unassigned[: limit - len(reopened)]
    return selected[:limit]


def assign_and_start_story(auth_token, story_id, user_id, status_id, dry_run=False):
    """Assign story and set status to In Progress."""
    if dry_run:
        print(f"  [DRY RUN] Would assign story {story_id} to Developer F and set to In Progress")
        return True

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    # Get current story to get version
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()

    payload = {
        "assigned_to": user_id,
        "status": status_id,
        "version": story.get("version", 1),
    }

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def add_start_note(auth_token, story_id, dry_run=False):
    """Add a note that Developer F started working on this story."""
    if dry_run:
        return True

    from datetime import datetime

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()
    current_description = story.get("description", "")

    start_note = f"""

---
**🚀 Work Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

*Developer F has started working on this story.*

**Next Steps:**
- Review story requirements
- Check existing implementation (if any)
- Begin implementation
"""
    new_description = f"{current_description}{start_note}"

    payload = {
        "description": new_description,
        "version": story.get("version", 1),
    }

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def main():
    parser = argparse.ArgumentParser(description="Assign unassigned stories to Developer F")
    parser.add_argument("--limit", type=int, default=5, help="Number of stories to assign (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Don't make changes, just report")

    args = parser.parse_args()

    print("=" * 80)
    print("ASSIGNING UNASSIGNED STORIES TO DEVELOPER F")
    print("=" * 80)
    print()

    # Authenticate
    print("Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project ID
    print(f"Getting project ID for '{PROJECT_SLUG}'...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Failed to get project ID")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer F user ID
    print(f"Getting user ID for '{DEVELOPER_F_USERNAME}'...")
    developer_f_id = get_user_id(auth_token, DEVELOPER_F_USERNAME)
    if not developer_f_id:
        print(f"⚠️  Developer F (username: {DEVELOPER_F_USERNAME}) not found")
        print("   Attempting to use admin account as Developer F...")
        admin_id = get_user_id(auth_token, "admin")
        if admin_id:
            developer_f_id = admin_id
            print(f"✅ Using admin account (ID: {developer_f_id}) as Developer F")
        else:
            print("❌ Could not find admin account either")
            sys.exit(1)
    else:
        print(f"✅ Developer F ID: {developer_f_id}")
    print()

    # Get statuses
    print("Getting statuses...")
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("working on it") or statuses.get("ready")
    if not in_progress_id:
        print("❌ Could not find 'In Progress' status")
        print(f"   Available statuses: {list(statuses.keys())}")
        sys.exit(1)
    print(f"✅ In Progress status ID: {in_progress_id}")
    print()

    # Get unassigned stories
    print(f"Finding unassigned stories (limit: {args.limit})...")
    unassigned = get_unassigned_stories(auth_token, project_id, args.limit)
    print(f"✅ Found {len(unassigned)} unassigned stories")
    print()

    if not unassigned:
        print("⚠️  No unassigned stories found")
        return

    # Display stories
    print("=" * 80)
    print("STORIES TO ASSIGN")
    print("=" * 80)
    print()

    for i, story in enumerate(unassigned, 1):
        story_ref = story.get("ref")
        subject = story.get("subject", "")
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        print(f"[{i}] US#{story_ref}: {subject[:70]}")
        print(f"    Status: {status}")
        print()

    # Confirm (unless dry-run)
    if not args.dry_run:
        print("=" * 80)
        print("ASSIGNING AND STARTING WORK")
        print("=" * 80)
        print()

    # Assign and start stories
    assigned_count = 0
    failed_count = 0

    for story in unassigned:
        story_id = story.get("id")
        story_ref = story.get("ref")
        subject = story.get("subject", "")

        if assign_and_start_story(auth_token, story_id, developer_f_id, in_progress_id, args.dry_run):
            add_start_note(auth_token, story_id, args.dry_run)
            assigned_count += 1
            print(f"✅ {'[DRY RUN] ' if args.dry_run else ''}Assigned and started US#{story_ref}: {subject[:60]}")
        else:
            failed_count += 1
            print(f"❌ Failed to assign US#{story_ref}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ {'Would assign' if args.dry_run else 'Assigned'}: {assigned_count} stories")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} stories")


if __name__ == "__main__":
    main()
