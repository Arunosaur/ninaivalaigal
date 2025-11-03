#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Find best unassigned task for Developer G and assign it
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


def authenticate():
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
    """Get all stories from project."""
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


def find_best_unassigned_story(stories):
    """Find best unassigned story to work on."""
    done_statuses = ["done", "closed", "archived", "cancelled"]

    # Priority order for statuses
    status_priority = {
        "ready": 1,
        "new": 2,
        "in progress": 3,
        "in-progress": 3,
        "testing": 4,
        "review": 5,
    }

    candidates = []

    for story in stories:
        assigned_to = story.get("assigned_to")
        if assigned_to:
            continue  # Skip assigned stories

        status_info = story.get("status_extra_info", {})
        status = status_info.get("name", "").lower() if status_info else ""

        if status in done_statuses:
            continue  # Skip done/archived

        subject = story.get("subject", "").lower()
        tags = story.get("tags", [])
        tag_names = [t[0] if isinstance(t, list) else str(t) for t in tags]

        # Calculate priority score
        priority_score = status_priority.get(status, 99)

        # Boost priority for certain keywords
        if any(kw in subject for kw in ["security", "compliance", "gdpr", "privacy"]):
            priority_score -= 10
        if any(kw in subject for kw in ["api", "endpoint", "integration"]):
            priority_score -= 5

        candidates.append((priority_score, story))

    # Sort by priority (lower is better)
    candidates.sort(key=lambda x: x[0])

    return candidates[0][1] if candidates else None


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
                if username.lower() in user_username:
                    return user.get("id")
        return None
    except Exception:
        return None


def get_project_members(auth_token, project_id):
    """Get project members."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/memberships?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def assign_and_start_story(auth_token, story_id, story_version, user_id, status_id=None):
    """Assign story to user and optionally set status."""
    headers = {"Authorization": f"Bearer {auth_token}"}
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


def main():
    """Find and assign best task to Developer G."""
    print("=" * 60)
    print("Finding Best Task for Developer G")
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

    # Get all stories
    print(f"\n🔍 Fetching all stories...")
    stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(stories)} total stories")

    # Find best unassigned story
    print(f"\n🔍 Finding best unassigned story...")
    best_story = find_best_unassigned_story(stories)

    if not best_story:
        print("❌ No suitable unassigned stories found")
        print("\n📋 All active stories are assigned or all unassigned are done/archived")
        return 1

    ref = best_story.get("ref")
    subject = best_story.get("subject")
    status_info = best_story.get("status_extra_info", {})
    status = status_info.get("name", "Unknown") if status_info else "Unknown"

    print(f"\n✅ Found best task: US#{ref}")
    print(f"   Subject: {subject}")
    print(f"   Status: {status}")
    print(f"   ID: {best_story.get('id')}")

    # Get Developer G
    print(f"\n🔍 Finding Developer G...")
    developer_g_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)

    if not developer_g_id:
        print(f"❌ Developer G not found")
        print(f"   Please create Developer G user first")
        return 1

    print(f"✅ Found Developer G (User ID: {developer_g_id})")

    # Check if Developer G is project member
    members = get_project_members(auth_token, project_id)
    is_member = False
    for member in members:
        member_user = member.get("user")
        if member_user:
            if isinstance(member_user, dict) and member_user.get("id") == developer_g_id:
                is_member = True
            elif isinstance(member_user, int) and member_user == developer_g_id:
                is_member = True

    if not is_member:
        print(f"\n⚠️  Developer G is not a project member")
        print(f"   Adding Developer G to project...")

        # Try to add to project
        user_url = f"{API_ENDPOINT}/users/{developer_g_id}"
        headers = {"Authorization": f"Bearer {auth_token}"}
        user_response = requests.get(user_url, headers=headers)
        username = DEVELOPER_G_USERNAME
        email = None

        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data.get("username", DEVELOPER_G_USERNAME)
            email = user_data.get("email")

        # Try adding membership
        membership_url = f"{API_ENDPOINT}/memberships"
        membership_data = {
            "project": project_id,
        }

        if email:
            membership_data["email"] = email
        if username:
            membership_data["username"] = username

        # Get role
        roles_url = f"{API_ENDPOINT}/roles?project={project_id}"
        roles_response = requests.get(roles_url, headers=headers)
        if roles_response.status_code == 200:
            roles = roles_response.json()
            if roles:
                membership_data["role"] = roles[0].get("id")

        membership_response = requests.post(membership_url, headers=headers, json=membership_data)
        if membership_response.status_code in [200, 201]:
            print(f"✅ Added Developer G to project")
            is_member = True
        else:
            print(f"⚠️  Could not add via API: {membership_response.status_code}")
            print(f"   Error: {membership_response.text[:200]}")
            print(f"\n   Please add Developer G manually:")
            print(f"   http://localhost:9000/project/ninaivalaigal/admin/project-profile/members")
            print(f"   Then run this script again")
            return 1

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("in-progress") or statuses.get("in_progress")

    # Assign and start story
    print(f"\n📝 Assigning US#{ref} to Developer G...")
    success, response_text = assign_and_start_story(
        auth_token,
        best_story["id"],
        best_story["version"],
        developer_g_id,
        status_id=in_progress_id if in_progress_id else None,
    )

    if success:
        print(f"✅ Successfully assigned US#{ref} to Developer G!")
        print(f"   Status set to: In Progress")
        print(f"\n📋 Story Details:")
        print(f"   Reference: US#{ref}")
        print(f"   Subject: {subject}")
        print(f"   URL: http://localhost:9000/project/ninaivalaigal/us/{ref}")
        return 0
    else:
        print(f"❌ Failed to assign story")
        print(f"   Response: {response_text[:200]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
