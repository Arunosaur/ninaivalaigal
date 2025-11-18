#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign an unassigned user story to Developer E and start working on it.
This script ensures we don't step on other developers' tasks.
"""

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

    # Try with large page size first
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    params = {"project": project_id, "page_size": 1000}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        # Handle both list and paginated response
        if isinstance(result, list):
            all_stories.extend(result)
        elif isinstance(result, dict):
            # Paginated response
            all_stories.extend(result.get("results", []))
            # If there are more pages, fetch them
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
        else:
            all_stories = result if isinstance(result, list) else []

    return all_stories


def get_project_members(auth_token, project_id):
    """Get all project members"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/{project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Get members from project
        members_url = f"{API_ENDPOINT}/memberships?project={project_id}"
        members_response = requests.get(members_url, headers=headers)
        if members_response.status_code == 200:
            return members_response.json()
    return []


def get_or_create_developer_e(auth_token, project_id):
    """Get Developer E user ID by exact username match"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Search all users for Developer E - use exact username match
    users_url = f"{API_ENDPOINT}/users"
    users_response = requests.get(users_url, headers=headers)
    if users_response.status_code == 200:
        users = users_response.json()
        for user in users:
            username = user.get("username", "")
            # Exact match for developer-e
            if username.lower() == "developer-e":
                return user.get("id")
            # Fallback: check full_name for "Developer E"
            full_name = user.get("full_name", "").lower() if user.get("full_name") else ""
            if full_name == "developer e":
                return user.get("id")

    # If not found, raise error instead of using admin as fallback
    print("❌ ERROR: Developer E user (username='developer-e') not found in Taiga")
    print("   Please create the user via:")
    print("   1. Taiga web UI: http://localhost:9000/admin/auth/user/add/")
    print("   2. Django shell: docker exec taiga-docker-taiga-back-1 python manage.py shell")
    raise ValueError("Developer E user not found. Create 'developer-e' user in Taiga first.")


def get_statuses(auth_token, project_id):
    """Get all story statuses"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def get_assigned_stories_by_developer(auth_token, project_id):
    """Get all assigned stories grouped by developer"""
    stories = get_all_stories(auth_token, project_id)
    assigned = {}

    for story in stories:
        assigned_to = story.get("assigned_to")
        if assigned_to:
            user_id = assigned_to
            if user_id not in assigned:
                assigned[user_id] = []
            assigned[user_id].append(story)

    return assigned


def update_story_description(auth_token, story_id, additional_text):
    """Append to story description"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    current_desc = story.get("description", "")
    new_desc = f"{current_desc}\n\n---\n\n{additional_text}"

    payload = {"description": new_desc, "version": story.get("version", 1)}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def assign_story(auth_token, story_id, user_id, status_id=None, developer_name="Developer E"):
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
    success = update_response.status_code in [200, 204]

    # Add note to description if successful
    if success:
        note = f"**Assigned to {developer_name}** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        update_story_description(auth_token, story_id, note)

    return success


def find_best_unassigned_story(stories):
    """Find the best unassigned story to work on"""
    # Priority order:
    # 1. P0/Critical unassigned stories
    # 2. Ready/New status stories
    # 3. Any other unassigned story

    unassigned = [s for s in stories if not s.get("assigned_to")]

    if not unassigned:
        return None

    # Filter out completed/archived
    active_unassigned = [
        s
        for s in unassigned
        if s.get("status_extra_info", {}).get("name", "").lower() not in ["done", "closed", "archived"]
    ]

    if not active_unassigned:
        return None

    # Check for P0/Critical
    for story in active_unassigned:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
        text = f"{subject} {description} {' '.join(tags)}"

        if any(kw in text for kw in ["p0", "critical", "security", "blocker", "urgent"]):
            return story

    # Check for Ready/New status
    for story in active_unassigned:
        status = story.get("status_extra_info", {}).get("name", "").lower()
        if status in ["ready", "new", "ready for development"]:
            return story

    # Return first available unassigned story
    return active_unassigned[0]


def main():
    print("=" * 70)
    print("Assign Story to Developer E")
    print("=" * 70)
    print()

    # Authenticate
    auth_token, user_data = authenticate()
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_data['id']})")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get all stories
    print("Fetching all user stories...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✓ Found {len(all_stories)} total stories")
    print()

    # Check existing assignments
    print("Checking existing developer assignments...")
    assigned_stories = get_assigned_stories_by_developer(auth_token, project_id)
    print(f"✓ Found {len(assigned_stories)} developers with assigned tasks")

    for user_id, stories in assigned_stories.items():
        in_progress = [
            s for s in stories if s.get("status_extra_info", {}).get("name", "").lower() in ["in progress", "working"]
        ]
        if in_progress:
            print(f"  • User ID {user_id}: {len(stories)} stories ({len(in_progress)} in progress)")
    print()

    # Find Developer E user ID
    print("Finding Developer E...")
    developer_e_id = get_or_create_developer_e(auth_token, project_id)
    print(f"✓ Developer E ID: {developer_e_id}")

    # Check if Developer E already has assignments
    dev_e_stories = []
    if developer_e_id in assigned_stories:
        dev_e_stories = assigned_stories[developer_e_id]
        in_progress = [
            s
            for s in dev_e_stories
            if s.get("status_extra_info", {}).get("name", "").lower() in ["in progress", "working"]
        ]
        print(f"✓ Developer E already has {len(dev_e_stories)} assigned stories ({len(in_progress)} in progress)")
        if in_progress:
            print("Current in-progress stories:")
            for story in in_progress:
                print(f"  • Ref #{story.get('ref')}: {story.get('subject', '')[:50]}")
            print()
    print()

    # Find best story to work on
    print("=" * 70)
    print("Finding Best Story to Work On")
    print("=" * 70)
    print()

    best_story = None

    # First priority: If Developer E has assigned stories but none in progress, pick the best one
    if dev_e_stories:
        # Filter out completed/archived stories
        active_statuses = ["ready", "new", "ready for development", "todo", "backlog"]
        done_statuses = ["done", "closed", "archived", "cancelled"]

        active_stories = [
            s
            for s in dev_e_stories
            if s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
            and s.get("status_extra_info", {}).get("name", "").lower() not in ["in progress", "working"]
        ]

        if active_stories:
            # Prioritize by status and tags
            ready_stories = [
                s for s in active_stories if s.get("status_extra_info", {}).get("name", "").lower() in active_statuses
            ]

            if ready_stories:
                best_story = ready_stories[0]
                print(f"Found active story already assigned to Developer E: Ref #{best_story.get('ref')}")
            else:
                # Pick first active story
                best_story = active_stories[0]
                print(f"Found assigned story for Developer E: Ref #{best_story.get('ref')}")

    # Second priority: Find best unassigned story using API filters
    if not best_story:
        print("Searching for unassigned active stories using API filters...")
        # Query with filters: unassigned (assigned_users=null) and active statuses
        filter_url = f"{API_ENDPOINT}/userstories?project={project_id}&assigned_users=null&page_size=1000"
        headers = {"Authorization": f"Bearer {auth_token}"}
        filter_response = requests.get(filter_url, headers=headers)

        if filter_response.status_code == 200:
            filter_result = filter_response.json()
            if isinstance(filter_result, dict):
                unassigned_stories = filter_result.get("results", [])
            else:
                unassigned_stories = filter_result

            # Filter out Done/Archived
            done_statuses = ["done", "closed", "archived", "cancelled"]
            active_unassigned = [
                s
                for s in unassigned_stories
                if s.get("status_extra_info", {}).get("name", "").lower() not in done_statuses
            ]

            if active_unassigned:
                # Prioritize by P0, security, critical keywords
                priority_keywords = ["p0", "critical", "security", "blocker", "urgent"]
                for story in active_unassigned:
                    subject = story.get("subject", "").lower()
                    description = story.get("description", "").lower()
                    tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
                    text = f"{subject} {description} {' '.join(tags)}"

                    if any(kw in text for kw in priority_keywords):
                        best_story = story
                        print(f"Found high-priority unassigned story: Ref #{story.get('ref')}")
                        break

                # If no high-priority found, pick first Ready/New story
                if not best_story:
                    ready_stories = [
                        s
                        for s in active_unassigned
                        if s.get("status_extra_info", {}).get("name", "").lower() in ["ready", "new"]
                    ]
                    if ready_stories:
                        best_story = ready_stories[0]
                        print(f"Found ready unassigned story: Ref #{best_story.get('ref')}")
                    else:
                        # Pick first active unassigned
                        best_story = active_unassigned[0]
                        print(f"Found active unassigned story: Ref #{best_story.get('ref')}")

        # Fallback to original method
        if not best_story:
            best_story = find_best_unassigned_story(all_stories)

    # Third priority: If no active stories, pick a high-priority Done story for validation/testing
    if not best_story:
        print("No active stories found. Looking for Done stories that might need follow-up work...")
        print()

        # Look for high-priority Done stories (P0, critical, security, auth-related)
        done_stories = [
            s
            for s in all_stories
            if not s.get("assigned_to")  # Unassigned
            and s.get("status_extra_info", {}).get("name", "").lower() in ["done", "closed"]
        ]

        # Prioritize by keywords
        priority_keywords = ["p0", "critical", "security", "auth", "signup", "login", "orm", "guardrail"]
        for story in done_stories:
            subject = story.get("subject", "").lower()
            description = story.get("description", "").lower()
            tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
            text = f"{subject} {description} {' '.join(tags)}"

            if any(kw in text for kw in priority_keywords):
                best_story = story
                print(f"Found high-priority Done story for validation: Ref #{story.get('ref')}")
                break

        # If still no story, pick the first unassigned Done story
        if not best_story and done_stories:
            best_story = done_stories[0]
            print(f"Selected Done story for follow-up work: Ref #{best_story.get('ref')}")

    if not best_story:
        print("✗ No suitable stories found to work on")
        print()
        print("All stories are either:")
        print("  • Already assigned (and not ready)")
        print("  • Completed/archived")
        print()

        # Show Developer E's assigned stories
        if dev_e_stories:
            print("Developer E's assigned stories:")
            for story in dev_e_stories[:5]:
                status = story.get("status_extra_info", {}).get("name", "Unknown")
                print(f"  • Ref #{story.get('ref')}: {story.get('subject', '')[:50]} (Status: {status})")
            print()

        print("You may want to:")
        print("  1. Check Developer E's assigned stories in Taiga UI")
        print("  2. Check for stories that need to be created")
        print("  3. Wait for new stories to be added")
        return

    # Display selected story
    ref = best_story.get("ref")
    subject = best_story.get("subject", "")
    status = best_story.get("status_extra_info", {}).get("name", "Unknown")
    tags = [t[0] if isinstance(t, list) else t for t in best_story.get("tags", [])]
    description = best_story.get("description", "")[:200]

    print("Selected Story:")
    print(f"  Ref: #{ref}")
    print(f"  Subject: {subject}")
    print(f"  Status: {status}")
    print(f"  Tags: {', '.join(tags[:5])}")
    if description:
        print(f"  Description: {description}...")
    print()

    # Get status IDs
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("working")

    # Assign and start
    print("=" * 70)
    print("Assigning and Starting Work")
    print("=" * 70)
    print()

    print(f"Assigning Ref #{ref} to Developer E...")
    if assign_story(auth_token, best_story["id"], developer_e_id, in_progress_id, DEVELOPER_E):
        print("  ✓ Assigned to Developer E")
        if in_progress_id:
            print("  ✓ Status updated to 'In Progress'")
        else:
            print("  ⚠ Could not update status (status ID not found)")
        print("  ✓ Added assignment note to story description")
    else:
        print("  ✗ Failed to assign story")
        return

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"✓ Story Ref #{ref} assigned to Developer E")
    print("✓ Status: In Progress")
    print()
    print(f"Story: {subject}")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{ref}")
    print("=" * 70)


if __name__ == "__main__":
    main()
