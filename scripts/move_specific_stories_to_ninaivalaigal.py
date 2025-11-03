#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Move specific user stories by reference number from infrastructure-tools to ninaivalaigal.

Usage:
    python3 scripts/move_specific_stories_to_ninaivalaigal.py --refs 5,6,7 [--delete-old]
"""

import argparse
import os
import sys
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
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token: str, project_slug: str) -> Optional[int]:
    """Get project ID by slug."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={project_slug}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        else:
            print(f"❌ Failed to get project {project_slug}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting project {project_slug}: {e}")
        return None


def get_story_by_ref(auth_token: str, project_id: int, ref: int) -> Optional[Dict]:
    """Get a story by its reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/by_ref"

    try:
        response = requests.get(url, headers=headers, params={"project": project_id, "ref": ref})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Story US#{ref} not found in project {project_id}")
            return None
    except Exception as e:
        print(f"❌ Error getting story US#{ref}: {e}")
        return None


def get_status_id(auth_token: str, project_id: int, status_name: str) -> Optional[int]:
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses"

    try:
        response = requests.get(url, headers=headers, params={"project": project_id})
        if response.status_code == 200:
            statuses = response.json()
            for status in statuses:
                if status.get("name") == status_name:
                    return status.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return None


def get_existing_stories(auth_token: str, project_id: int) -> Dict[str, Dict]:
    """Get all existing stories in destination project to check for duplicates."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    existing = {}

    page = 1
    page_size = 500

    while True:
        try:
            response = requests.get(
                f"{API_ENDPOINT}/userstories",
                headers=headers,
                params={"project": project_id, "page": page, "page_size": page_size},
            )
            if response.status_code == 200:
                stories = response.json()
                if not stories:
                    break

                for story in stories:
                    subject = story.get("subject", "").strip()
                    if subject:
                        existing[subject.lower()] = story

                if len(stories) < page_size:
                    break
                page += 1
            else:
                break
        except Exception as e:
            print(f"⚠️  Error getting existing stories: {e}")
            break

    return existing


def create_story_in_project(
    auth_token: str, project_id: int, story_data: Dict, status_id: Optional[int] = None
) -> Optional[Dict]:
    """Create a story in the destination project."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Prepare story payload
    payload = {
        "subject": story_data.get("subject", ""),
        "project": project_id,
        "description": story_data.get("description", ""),
    }

    # Add tags if present
    tags = story_data.get("tags", [])
    if tags:
        # Handle different tag formats
        tag_names = []
        for tag in tags:
            if isinstance(tag, str):
                tag_names.append(tag)
            elif isinstance(tag, dict):
                tag_names.append(tag.get("name", ""))
        if tag_names:
            payload["tags"] = tag_names

    # Add status if provided
    if status_id:
        payload["status"] = status_id

    try:
        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"❌ Failed to create story: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        return None


def delete_story(auth_token: str, story_id: int, version: int) -> bool:
    """Delete a story."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    try:
        response = requests.delete(
            f"{API_ENDPOINT}/userstories/{story_id}", headers=headers, params={"version": version}
        )
        return response.status_code == 204
    except Exception as e:
        print(f"❌ Error deleting story: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Move specific user stories from infrastructure-tools to ninaivalaigal"
    )
    parser.add_argument(
        "--refs", type=str, required=True, help="Comma-separated list of story reference numbers (e.g., 5,6,7)"
    )
    parser.add_argument(
        "--delete-old", action="store_true", help="Delete original stories from infrastructure-tools after moving"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be moved without actually moving")

    args = parser.parse_args()

    # Parse refs
    try:
        refs = [int(ref.strip()) for ref in args.refs.split(",")]
    except ValueError:
        print("❌ Invalid refs format. Use comma-separated numbers (e.g., 5,6,7)")
        sys.exit(1)

    print("=" * 80)
    print(f"🔄 Moving Specific Stories")
    print(f"   From: infrastructure-tools → To: ninaivalaigal")
    print(f"   Stories: US#{', US#'.join(map(str, refs))}")
    print("=" * 80)

    # Authenticate
    print("\n1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        sys.exit(1)
    print("✅ Authenticated")

    # Get project IDs
    print("\n2️⃣  Getting projects...")
    ninaivalaigal_id = get_project_id(auth_token, PROJECT_SLUG_NINAIVALAIGAL)
    infra_tools_id = get_project_id(auth_token, PROJECT_SLUG_INFRA_TOOLS)

    if not ninaivalaigal_id or not infra_tools_id:
        sys.exit(1)

    print(f"✅ ninaivalaigal project ID: {ninaivalaigal_id}")
    print(f"✅ infrastructure-tools project ID: {infra_tools_id}")

    # Get existing stories in destination to check for duplicates
    print("\n3️⃣  Checking for duplicates in ninaivalaigal...")
    existing_stories = get_existing_stories(auth_token, ninaivalaigal_id)
    print(f"✅ Found {len(existing_stories)} existing stories")

    # Get stories from infrastructure-tools
    print("\n4️⃣  Getting stories from infrastructure-tools...")
    stories_to_move = []
    for ref in refs:
        story = get_story_by_ref(auth_token, infra_tools_id, ref)
        if story:
            stories_to_move.append(story)
            print(f"   ✅ Found US#{ref}: {story.get('subject', '')[:60]}")
        else:
            print(f"   ❌ Story US#{ref} not found")

    if not stories_to_move:
        print("\n❌ No stories found to move")
        sys.exit(1)

    # Filter out duplicates
    print("\n5️⃣  Checking for duplicates...")
    stories_to_create = []
    duplicates = []

    for story in stories_to_move:
        subject = story.get("subject", "").strip()
        subject_lower = subject.lower()

        if subject_lower in existing_stories:
            duplicates.append(story)
            existing_ref = existing_stories[subject_lower].get("ref")
            print(f"   ⚠️  US#{story.get('ref')} duplicate of US#{existing_ref}: {subject[:50]}")
        else:
            stories_to_create.append(story)

    if not stories_to_create:
        print("\n🎉 All stories already exist in ninaivalaigal!")
        if duplicates:
            print(f"   (Found {len(duplicates)} duplicates)")
        return

    print(f"   ✅ Stories to move: {len(stories_to_create)}")
    if duplicates:
        print(f"   ⚠️  Duplicates: {len(duplicates)} (will skip)")

    # Get status ID for "New" status in ninaivalaigal
    print("\n6️⃣  Getting status information...")
    new_status_id = get_status_id(auth_token, ninaivalaigal_id, "New")
    if new_status_id:
        print(f"✅ New status ID: {new_status_id}")
    else:
        print("⚠️  Could not find 'New' status, story will be created without status")

    if args.dry_run:
        print("\n" + "=" * 80)
        print("📋 Stories to move:")
        print("=" * 80)
        for story in stories_to_create:
            print(f"  US#{story.get('ref')}: {story.get('subject', '')}")
        print("\n🔍 DRY RUN MODE - No stories will be moved")
        return

    # Create stories in ninaivalaigal
    print("\n7️⃣  Creating stories in ninaivalaigal...")
    created_stories = []
    failed_stories = []

    for story in stories_to_create:
        new_story = create_story_in_project(auth_token, ninaivalaigal_id, story, status_id=new_status_id)

        if new_story:
            created_stories.append(new_story)
            print(f"   ✅ Created US#{new_story.get('ref')}: {story.get('subject', '')[:50]}")
        else:
            failed_stories.append(story)
            print(f"   ❌ Failed to create: {story.get('subject', '')[:50]}")

    # Delete old stories if requested
    if args.delete_old and created_stories:
        print("\n8️⃣  Deleting original stories from infrastructure-tools...")
        deleted_count = 0

        for story in created_stories:
            # Find corresponding original story
            subject = story.get("subject", "").strip().lower()
            for orig_story in stories_to_create:
                if orig_story.get("subject", "").strip().lower() == subject:
                    story_id = orig_story.get("id")
                    version = orig_story.get("version", 1)
                    if delete_story(auth_token, story_id, version):
                        deleted_count += 1
                        print(f"   ✅ Deleted US#{orig_story.get('ref')} from infrastructure-tools")
                    break

        print(f"   ✅ Deleted {deleted_count} original stories")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Created in ninaivalaigal: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")
    if duplicates:
        print(f"⚠️  Duplicates skipped: {len(duplicates)}")
    if args.delete_old:
        print(f"🗑️  Deleted from infrastructure-tools: {len(created_stories)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
