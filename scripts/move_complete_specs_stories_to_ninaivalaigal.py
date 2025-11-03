#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Move Complete SPEC stories from infrastructure-tools project to ninaivalaigal project.

Since Taiga API doesn't support moving stories between projects, this script will:
1. Read all Complete SPEC stories from infrastructure-tools
2. Recreate them in ninaivalaigal project
3. Optionally delete the old stories from infrastructure-tools

Usage:
    python3 scripts/move_complete_specs_stories_to_ninaivalaigal.py [--delete-old]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG_NINAIVALAIGAL = "ninaivalaigal"
PROJECT_SLUG_INFRA_TOOLS = "infrastructure-tools"

# Get credentials from environment
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer C
DEVELOPER_C_USERNAME = os.getenv("DEVELOPER_C_USERNAME", "developer-c")


def authenticate() -> Optional[str]:
    """Authenticate with Taiga and return auth token."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token: str, project_slug: str) -> Optional[int]:
    """Get project ID by slug."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Use by_slug endpoint for accurate project lookup
    url = f"{API_ENDPOINT}/projects/by_slug?slug={project_slug}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            project = response.json()
            return project.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project {project_slug}: {e}")
        return None


def get_user_id(auth_token: str, username: str) -> Optional[int]:
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users?username={username}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting user {username}: {e}")
        return None


def get_done_status_id(auth_token: str, project_id: int) -> Optional[int]:
    """Get the 'Done' status ID for user stories."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = response.json()
            # Find "Done" status (case-insensitive)
            for status in statuses:
                if "done" in status.get("name", "").lower():
                    return status["id"]
            # If no "Done" status, use the last one
            if statuses:
                return statuses[-1]["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return None


def get_complete_spec_stories_from_project(auth_token: str, project_id: int) -> List[Dict]:
    """Get all Complete SPEC stories from a project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
        response = requests.get(url, headers=headers, params={"page_size": 300})
        if response.status_code == 200:
            all_stories = response.json()
            complete_spec_stories = [
                s for s in all_stories if "Complete" in s.get("subject", "") and "SPEC-" in s.get("subject", "").upper()
            ]
            return complete_spec_stories
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def create_story_in_project(
    auth_token: str,
    project_id: int,
    story_data: Dict,
    done_status_id: int,
    developer_c_id: Optional[int],
) -> Optional[Dict]:
    """Create a story in the target project."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Extract SPEC number from subject
    subject = story_data.get("subject", "")
    spec_match = re.search(r"SPEC[-\s]?(\d{2,3})", subject, re.IGNORECASE)
    spec_num = None
    if spec_match:
        try:
            spec_num = int(spec_match.group(1))
        except ValueError:
            pass

    # Prepare payload
    payload = {
        "project": project_id,
        "subject": story_data.get("subject", ""),
        "description": story_data.get("description", ""),
        "tags": story_data.get("tags", []),
        "status": done_status_id,
    }

    if developer_c_id:
        payload["assigned_to"] = developer_c_id

    try:
        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)

        if response.status_code == 201:
            story = response.json()
            return story
        else:
            print(f"  ❌ Failed to create: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error creating story: {e}")
        return None


def delete_story(auth_token: str, story_id: int) -> bool:
    """Delete a story."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    try:
        response = requests.delete(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"  ❌ Error deleting story: {e}")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Move Complete SPEC stories to ninaivalaigal project")
    parser.add_argument(
        "--delete-old", action="store_true", help="Delete old stories from infrastructure-tools after moving"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    args = parser.parse_args()

    print("=" * 80)
    print("🔄 Moving Complete SPEC Stories to ninaivalaigal Project")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get projects
    print("2️⃣  Getting projects...")
    nina_id = get_project_id(auth_token, PROJECT_SLUG_NINAIVALAIGAL)
    infra_id = get_project_id(auth_token, PROJECT_SLUG_INFRA_TOOLS)

    if not nina_id:
        print(f"❌ Project '{PROJECT_SLUG_NINAIVALAIGAL}' not found. Exiting.")
        sys.exit(1)
    if not infra_id:
        print(f"❌ Project '{PROJECT_SLUG_INFRA_TOOLS}' not found. Exiting.")
        sys.exit(1)

    print(f"✅ ninaivalaigal project ID: {nina_id}")
    print(f"✅ infrastructure-tools project ID: {infra_id}")
    print()

    # Get Developer C
    print("3️⃣  Getting Developer C user ID...")
    developer_c_id = get_user_id(auth_token, DEVELOPER_C_USERNAME)
    if developer_c_id:
        print(f"✅ Developer C ID: {developer_c_id}")
    else:
        print(f"⚠️  Developer C ({DEVELOPER_C_USERNAME}) not found. Stories will be unassigned.")
    print()

    # Get Done status for ninaivalaigal
    print("4️⃣  Getting Done status for ninaivalaigal...")
    done_status_id = get_done_status_id(auth_token, nina_id)
    if not done_status_id:
        print("❌ Could not find Done status. Exiting.")
        sys.exit(1)
    print(f"✅ Done status ID: {done_status_id}")
    print()

    # Get stories from infrastructure-tools
    print("5️⃣  Getting Complete SPEC stories from infrastructure-tools...")
    infra_stories = get_complete_spec_stories_from_project(auth_token, infra_id)
    print(f"✅ Found {len(infra_stories)} Complete SPEC stories in infrastructure-tools")
    print()

    if not infra_stories:
        print("🎉 No stories to move!")
        return

    # Check if stories already exist in ninaivalaigal
    print("6️⃣  Checking existing stories in ninaivalaigal...")
    nina_stories = get_complete_spec_stories_from_project(auth_token, nina_id)

    # Extract SPEC numbers from existing stories
    existing_specs = set()
    for story in nina_stories:
        subject = story.get("subject", "")
        match = re.search(r"SPEC[-\s]?(\d{2,3})", subject, re.IGNORECASE)
        if match:
            try:
                existing_specs.add(int(match.group(1)))
            except ValueError:
                pass

    # Filter stories that need to be moved (not duplicates)
    stories_to_move = []
    for story in infra_stories:
        subject = story.get("subject", "")
        match = re.search(r"SPEC[-\s]?(\d{2,3})", subject, re.IGNORECASE)
        if match:
            try:
                spec_num = int(match.group(1))
                if spec_num not in existing_specs:
                    stories_to_move.append(story)
            except ValueError:
                pass

    print(f"✅ Found {len(nina_stories)} existing Complete SPEC stories in ninaivalaigal")
    print(f"✅ Need to move {len(stories_to_move)} stories (avoiding duplicates)")
    print()

    if not stories_to_move:
        print("🎉 All stories already exist in ninaivalaigal!")
        return

    # Display what will be moved
    print("=" * 80)
    print(f"📋 Stories to move ({len(stories_to_move)}):")
    print("=" * 80)
    for story in stories_to_move[:20]:
        print(f"  - {story.get('subject', '')[:60]}")
    if len(stories_to_move) > 20:
        print(f"  ... and {len(stories_to_move) - 20} more")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No stories will be moved")
        return

    # Confirm
    response = input(f"Move {len(stories_to_move)} stories to ninaivalaigal? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("⏭️  Cancelled.")
        return

    # Move stories
    print()
    print("=" * 80)
    print(f"7️⃣  Moving {len(stories_to_move)} stories...")
    print("=" * 80)
    print()

    created_stories = []
    failed_stories = []

    for idx, story in enumerate(stories_to_move, 1):
        print(f"[{idx}/{len(stories_to_move)}] {story.get('subject', '')[:60]}")

        new_story = create_story_in_project(
            auth_token,
            nina_id,
            story,
            done_status_id,
            developer_c_id,
        )

        if new_story:
            created_stories.append(
                {"old_ref": story.get("ref"), "new_ref": new_story.get("ref"), "subject": story.get("subject", "")}
            )
            print(f"  ✅ Created US#{new_story.get('ref')} in ninaivalaigal")

            # Optionally delete old story
            if args.delete_old:
                if delete_story(auth_token, story.get("id")):
                    print(f"  ✅ Deleted US#{story.get('ref')} from infrastructure-tools")
                else:
                    print(f"  ⚠️  Failed to delete US#{story.get('ref')} from infrastructure-tools")
        else:
            failed_stories.append(story)

        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {len(created_stories)} stories in ninaivalaigal")
    print(f"❌ Failed: {len(failed_stories)} stories")
    if args.delete_old:
        print(f"🗑️  Deleted: {len(created_stories)} stories from infrastructure-tools")
    print()

    if created_stories:
        print("✅ Successfully Moved:")
        for story in created_stories[:10]:
            print(f"   US#{story['old_ref']} → US#{story['new_ref']}: {story['subject'][:50]}")
        if len(created_stories) > 10:
            print(f"   ... and {len(created_stories) - 10} more")
        print()


if __name__ == "__main__":
    main()
