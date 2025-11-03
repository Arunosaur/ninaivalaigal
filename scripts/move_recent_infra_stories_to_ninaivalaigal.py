#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Move all stories created in the last 3 days from infrastructure-tools to ninaivalaigal project.

Usage:
    python3 scripts/move_recent_infra_stories_to_ninaivalaigal.py [--days N] [--delete-old]
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
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
            project = response.json()
            return project.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project {project_slug}: {e}")
        return None


def get_stories_from_project(auth_token: str, project_id: int) -> List[Dict]:
    """Get all stories from a project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
        response = requests.get(url, headers=headers, params={"page_size": 500})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def filter_stories_by_date(stories: List[Dict], days: int = 3) -> List[Dict]:
    """Filter stories created in the last N days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_stories = []

    for story in stories:
        created_date_str = story.get("created_date", "")
        if created_date_str:
            try:
                # Parse ISO format: "2025-01-01T12:00:00.000Z"
                created_date = datetime.fromisoformat(created_date_str.replace("Z", "+00:00"))
                if created_date.replace(tzinfo=None) >= cutoff_date:
                    recent_stories.append(story)
            except (ValueError, AttributeError):
                # If date parsing fails, skip
                pass

    return recent_stories


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
            # If no "Done" status, return None and we'll use the story's existing status
            return None
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return None


def create_story_in_project(
    auth_token: str,
    target_project_id: int,
    source_story: Dict,
    done_status_id: Optional[int] = None,
) -> Optional[Dict]:
    """Create a story in the target project based on source story."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Prepare payload - preserve all important fields
    payload = {
        "project": target_project_id,
        "subject": source_story.get("subject", ""),
        "description": source_story.get("description", ""),
        "tags": source_story.get("tags", []),
    }

    # Use existing status if available, otherwise use Done
    source_status = source_story.get("status")
    if done_status_id:
        payload["status"] = done_status_id
    elif source_status:
        payload["status"] = source_status

    # Preserve assignee if exists
    assigned_to = source_story.get("assigned_to")
    if assigned_to:
        payload["assigned_to"] = assigned_to

    try:
        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)

        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def delete_story(auth_token: str, story_id: int) -> bool:
    """Delete a story."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    try:
        response = requests.delete(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"  ❌ Error deleting: {e}")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Move recent infrastructure-tools stories to ninaivalaigal")
    parser.add_argument("--days", type=int, default=3, help="Number of days to look back (default: 3)")
    parser.add_argument(
        "--delete-old", action="store_true", help="Delete old stories from infrastructure-tools after moving"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    args = parser.parse_args()

    print("=" * 80)
    print(f"🔄 Moving Stories Created in Last {args.days} Days")
    print(f"   From: infrastructure-tools → To: ninaivalaigal")
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

    # Get Done status for ninaivalaigal
    print("3️⃣  Getting Done status for ninaivalaigal...")
    done_status_id = get_done_status_id(auth_token, nina_id)
    if done_status_id:
        print(f"✅ Done status ID: {done_status_id}")
    else:
        print("⚠️  No Done status found, will preserve source story status")
    print()

    # Get stories from infrastructure-tools
    print(f"4️⃣  Getting stories from infrastructure-tools...")
    infra_stories = get_stories_from_project(auth_token, infra_id)
    print(f"✅ Found {len(infra_stories)} total stories")
    print()

    # Filter by date
    print(f"5️⃣  Filtering stories created in last {args.days} days...")
    recent_stories = filter_stories_by_date(infra_stories, args.days)
    print(f"✅ Found {len(recent_stories)} stories created in last {args.days} days")
    print()

    if not recent_stories:
        print("🎉 No recent stories to move!")
        return

    # Display what will be moved
    print("=" * 80)
    print(f"📋 Stories to move ({len(recent_stories)}):")
    print("=" * 80)
    for story in recent_stories[:20]:
        created = story.get("created_date", "")[:10]  # Just the date part
        print(f"  US#{story.get('ref')}: {story.get('subject', '')[:55]} (Created: {created})")
    if len(recent_stories) > 20:
        print(f"  ... and {len(recent_stories) - 20} more")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No stories will be moved")
        return

    # Check for duplicates in ninaivalaigal
    print("6️⃣  Checking for duplicates in ninaivalaigal...")
    nina_stories = get_stories_from_project(auth_token, nina_id)
    nina_subjects = {s.get("subject", "").lower().strip() for s in nina_stories}

    stories_to_move = []
    duplicates = []

    for story in recent_stories:
        subject = story.get("subject", "").lower().strip()
        if subject not in nina_subjects:
            stories_to_move.append(story)
        else:
            duplicates.append(story)

    print(f"✅ Stories to move: {len(stories_to_move)}")
    if duplicates:
        print(f"⚠️  Duplicates found: {len(duplicates)} (will skip)")
        if len(duplicates) <= 10:
            print("   Duplicates:")
            for story in duplicates:
                print(f"     US#{story.get('ref')}: {story.get('subject', '')[:50]}")
        else:
            print("   Sample duplicates:")
            for story in duplicates[:3]:
                print(f"     US#{story.get('ref')}: {story.get('subject', '')[:50]}")
            print(f"     ... and {len(duplicates) - 3} more")
    print()

    if not stories_to_move:
        print("🎉 All recent stories already exist in ninaivalaigal!")
        if duplicates:
            print(f"   (Skipped {len(duplicates)} duplicate stories)")
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
    deleted_stories = []

    for idx, story in enumerate(stories_to_move, 1):
        story_ref = story.get("ref")
        story_subject = story.get("subject", "")[:60]

        if idx % 10 == 0 or idx <= 5:
            print(f"[{idx}/{len(stories_to_move)}] US#{story_ref}: {story_subject}")

        # Create in ninaivalaigal
        new_story = create_story_in_project(
            auth_token,
            nina_id,
            story,
            done_status_id,
        )

        if new_story:
            created_stories.append(
                {"old_ref": story_ref, "new_ref": new_story.get("ref"), "subject": story.get("subject", "")}
            )
            if idx <= 5:
                print(f"  ✅ Created US#{new_story.get('ref')} in ninaivalaigal")

            # Optionally delete old story
            if args.delete_old:
                if delete_story(auth_token, story.get("id")):
                    deleted_stories.append(story_ref)
                    if idx <= 5:
                        print(f"  ✅ Deleted US#{story_ref} from infrastructure-tools")
        else:
            failed_stories.append(story)
            if idx <= 5:
                print(f"  ❌ Failed to create")

    # Summary
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Created in ninaivalaigal: {len(created_stories)} stories")
    print(f"❌ Failed: {len(failed_stories)} stories")
    if args.delete_old:
        print(f"🗑️  Deleted from infrastructure-tools: {len(deleted_stories)} stories")
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
