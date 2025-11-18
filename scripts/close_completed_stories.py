#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Close completed stories in Taiga
"""

import os
import sys

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Stories to close (completed)
COMPLETED_STORIES = [743, 792, 321, 322, 327, 328, 329]


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


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    url = f"{API_ENDPOINT}/userstories/by_ref"
    params = {"project": project_id, "ref": story_ref}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

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


def close_story(auth_token, story_id, story_version, status_id):
    """Close story by setting status to done/closed."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {
        "version": story_version,
        "status": status_id,
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        return response.status_code in [200, 204], response.text
    except Exception as e:
        return False, str(e)


def main():
    """Close completed stories."""
    print("=" * 80)
    print("CLOSING COMPLETED STORIES")
    print("=" * 80)
    print()

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")
    print()

    # Get project ID
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    project_response = requests.get(project_url, headers=headers)

    if project_response.status_code != 200:
        print("❌ Failed to get project")
        return 1

    project_id = project_response.json().get("id")
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")
    print()

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_status_id = (
        statuses.get("done") or statuses.get("completed") or statuses.get("complete") or statuses.get("closed")
    )

    if done_status_id:
        print(f"✅ Found 'Done' status (ID: {done_status_id})")
    else:
        print("❌ 'Done' status not found")
        return 1
    print()

    # Close stories
    success_count = 0
    for story_ref in COMPLETED_STORIES:
        print(f"📝 Closing US#{story_ref}...")

        # Find story
        story = find_story_by_ref(auth_token, project_id, story_ref)
        if not story:
            print(f"  ❌ Story US#{story_ref} not found")
            continue

        story_id = story.get("id")
        story_version = story.get("version", 1)
        subject = story.get("subject", "")
        current_status = story.get("status_extra_info", {}).get("name", "unknown")

        print(f"  ✅ Found: {subject}")
        print(f"     Current status: {current_status}")
        print(f"     Story ID: {story_id}, Version: {story_version}")

        # Close story
        success, response_text = close_story(auth_token, story_id, story_version, done_status_id)

        if success:
            print(f"  ✅ Story closed (status: Done)")
            success_count += 1
        else:
            print(f"  ❌ Failed to close: {response_text[:200]}")

        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully closed: {success_count}/{len(COMPLETED_STORIES)} stories")
    print()
    print(f"📋 Stories closed:")
    for story_ref in COMPLETED_STORIES:
        print(f"   - US#{story_ref}: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_ref}")
    print()

    return 0 if success_count == len(COMPLETED_STORIES) else 1


if __name__ == "__main__":
    sys.exit(main())




