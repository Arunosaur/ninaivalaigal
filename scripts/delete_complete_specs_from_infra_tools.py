#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Delete Complete SPEC stories from infrastructure-tools project.

These stories were moved to ninaivalaigal and should be cleaned up from
infrastructure-tools to avoid duplicates.
"""

import os
import sys
from datetime import datetime, timedelta

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug", headers=headers, params={"slug": project_slug})
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_stories(headers, project_id):
    """Get all stories from a project."""
    stories = []
    page = 1
    page_size = 500

    while True:
        response = requests.get(
            f"{API_ENDPOINT}/userstories",
            headers=headers,
            params={"project": project_id, "page": page, "page_size": page_size},
        )
        if response.status_code == 200:
            page_stories = response.json()
            if not page_stories:
                break
            stories.extend(page_stories)
            if len(page_stories) < page_size:
                break
            page += 1
        else:
            print(f"❌ Failed to get stories: {response.status_code}")
            break

    return stories


def filter_complete_spec_stories(stories, days=None):
    """Filter Complete SPEC stories, optionally by creation date."""
    complete_specs = []

    cutoff_date = None
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)

    for story in stories:
        subject = story.get("subject", "")
        # Check if it's a Complete SPEC story
        if "Complete" in subject and "SPEC-" in subject.upper():
            # Optionally filter by date
            if cutoff_date:
                created_date_str = story.get("created_date", "")
                if created_date_str:
                    try:
                        created_date = datetime.fromisoformat(created_date_str.replace("Z", "+00:00"))
                        if created_date.replace(tzinfo=None) >= cutoff_date:
                            complete_specs.append(story)
                    except:
                        pass
            else:
                complete_specs.append(story)

    return complete_specs


def delete_story(headers, story_id, version):
    """Delete a story."""
    response = requests.delete(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers, params={"version": version})
    return response.status_code == 204


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Delete Complete SPEC stories from infrastructure-tools")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only delete stories created in last N days (default: all Complete SPEC stories)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    print("=" * 80)
    if args.days:
        print(f"🗑️  Deleting Complete SPEC Stories (Last {args.days} Days)")
    else:
        print("🗑️  Deleting All Complete SPEC Stories")
    print("   From: infrastructure-tools")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting infrastructure-tools project...")
    infra_project_id = get_project_id(headers, "infrastructure-tools")
    print(f"✅ infrastructure-tools project ID: {infra_project_id}")

    # Get stories
    print("\n3️⃣  Getting stories from infrastructure-tools...")
    all_stories = get_stories(headers, infra_project_id)
    print(f"✅ Found {len(all_stories)} total stories")

    # Filter Complete SPEC stories
    print("\n4️⃣  Filtering Complete SPEC stories...")
    if args.days:
        complete_specs = filter_complete_spec_stories(all_stories, days=args.days)
        print(f"✅ Found {len(complete_specs)} Complete SPEC stories (last {args.days} days)")
    else:
        complete_specs = filter_complete_spec_stories(all_stories)
        print(f"✅ Found {len(complete_specs)} Complete SPEC stories")

    if not complete_specs:
        print("\n🎉 No Complete SPEC stories to delete!")
        return

    # Show stories to delete
    print("\n" + "=" * 80)
    print(f"📋 Stories to delete ({len(complete_specs)}):")
    print("=" * 80)
    for story in complete_specs[:20]:
        created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"
        print(f"  US#{story.get('ref')}: {story.get('subject', '')[:65]} (Created: {created})")
    if len(complete_specs) > 20:
        print(f"  ... and {len(complete_specs) - 20} more")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No stories will be deleted")
        return

    # Confirm
    if not args.yes:
        print("\n" + "=" * 80)
        print("⚠️  WARNING: This will permanently delete these stories!")
        print("=" * 80)
        response = input("\nAre you sure you want to delete these stories? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("\n❌ Deletion cancelled")
            return

    # Delete stories
    print("\n5️⃣  Deleting stories...")
    deleted = 0
    failed = 0

    for story in complete_specs:
        story_id = story.get("id")
        story_ref = story.get("ref")
        version = story.get("version", 1)

        if delete_story(headers, story_id, version):
            deleted += 1
            if deleted % 10 == 0:
                print(f"   ✅ Deleted {deleted}/{len(complete_specs)}...")
        else:
            failed += 1
            print(f"   ❌ Failed to delete US#{story_ref}")

    print("\n" + "=" * 80)
    print(f"✅ Successfully deleted: {deleted}")
    if failed > 0:
        print(f"❌ Failed to delete: {failed}")
    print("=" * 80)


if __name__ == "__main__":
    main()
