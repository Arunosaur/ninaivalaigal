#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Delete duplicate Taiga user stories.

This script identifies and deletes duplicate stories, keeping only the
first created story (primary) in each duplicate group.
"""

import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

import requests


def get_auth_token() -> str:
    """Get authentication token from Taiga API."""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    api_endpoint = f"{taiga_url}/api/v1"
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    auth_response = requests.post(
        f"{api_endpoint}/auth",
        json={"type": "normal", "username": username, "password": password},
    )

    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        sys.exit(1)

    return auth_response.json()["auth_token"]


def get_project_id(headers: Dict[str, str]) -> int:
    """Get project ID for ninaivalaigal project."""
    api_endpoint = f"{os.getenv('TAIGA_URL', 'http://localhost:9000')}/api/v1"
    project_response = requests.get(f"{api_endpoint}/projects/by_slug?slug=ninaivalaigal", headers=headers)

    if project_response.status_code != 200:
        print(f"❌ Failed to get project: {project_response.status_code}")
        sys.exit(1)

    return project_response.json()["id"]


def normalize_tags(tags: List) -> List[str]:
    """Normalize tags to list of strings."""
    normalized = []
    for tag in tags:
        if isinstance(tag, str):
            normalized.append(tag)
        elif isinstance(tag, list) and len(tag) > 0:
            normalized.append(str(tag[0]))
        elif isinstance(tag, dict):
            normalized.append(tag.get("name", str(tag)))
    return sorted(normalized)


def normalize_description(desc: str) -> str:
    """Normalize description for comparison."""
    if not desc:
        return ""
    return desc.strip().replace("\r\n", "\n").replace("\r", "\n")


def get_all_stories(headers: Dict[str, str], project_id: int) -> List[Dict]:
    """Get all user stories from the project."""
    api_endpoint = f"{os.getenv('TAIGA_URL', 'http://localhost:9000')}/api/v1"
    all_stories = []
    page = 1
    page_size = 500

    while True:
        stories_response = requests.get(
            f"{api_endpoint}/userstories",
            headers=headers,
            params={"project": project_id, "page": page, "page_size": page_size},
        )

        if stories_response.status_code != 200:
            break

        stories = stories_response.json()
        if not stories:
            break

        all_stories.extend(stories)

        if len(stories) < page_size:
            break

        page += 1

    return all_stories


def find_duplicates(stories: List[Dict]) -> List[Tuple[List[Dict], str]]:
    """Find duplicate stories based on subject, description, and tags."""
    groups = defaultdict(list)

    for story in stories:
        subject = story.get("subject", "").strip()
        description = normalize_description(story.get("description", "") or "")
        tags = normalize_tags(story.get("tags", []))

        key = (subject.lower(), description, tuple(tags))
        groups[key].append(story)

    duplicates = []
    for key, group_stories in groups.items():
        if len(group_stories) > 1:
            group_stories.sort(key=lambda s: s.get("created_date", ""), reverse=False)
            duplicates.append((group_stories, key[0]))

    return duplicates


def delete_story(headers: Dict[str, str], story: Dict) -> bool:
    """Delete a story."""
    story_id = story.get("id")
    ref = story.get("ref")
    subject = story.get("subject", "")[:50]

    delete_response = requests.delete(
        f"{os.getenv('TAIGA_URL', 'http://localhost:9000')}/api/v1/userstories/{story_id}",
        headers=headers,
    )

    if delete_response.status_code == 204:
        print(f"  ✅ Deleted US#{ref}: {subject}...")
        return True
    else:
        print(f"  ⚠️  Failed to delete US#{ref}: {delete_response.status_code}")
        return False


def main():
    """Main function to delete duplicates."""
    import argparse

    parser = argparse.ArgumentParser(description="Delete duplicate Taiga user stories")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates without deleting",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Delete Duplicate Taiga User Stories")
    print("=" * 80)

    # Authenticate
    auth_token = get_auth_token()
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get project ID
    project_id = get_project_id(headers)
    print(f"✅ Connected to project (ID: {project_id})")

    # Get all stories
    print("📥 Fetching all user stories...")
    all_stories = get_all_stories(headers, project_id)
    print(f"✅ Found {len(all_stories)} total stories")

    # Find duplicates
    print("\n🔍 Analyzing for duplicates...")
    duplicates = find_duplicates(all_stories)

    if not duplicates:
        print("\n✅ No duplicates found!")
        return

    print(f"\n⚠️  Found {len(duplicates)} groups of duplicate stories")

    # Collect all duplicate stories (excluding primary)
    stories_to_delete = []
    for group, subject in duplicates:
        primary = group[0]
        duplicates_list = group[1:]
        for dup in duplicates_list:
            stories_to_delete.append((dup, primary, subject))

    print(f"\n📋 Found {len(stories_to_delete)} duplicate stories to delete\n")

    if args.dry_run:
        print("DRY RUN - Stories that would be deleted:\n")
        for dup, primary, subject in stories_to_delete:
            print(f"  US#{dup.get('ref')}: {subject[:60]}... (keep US#{primary.get('ref')})")
        return

    # Show summary
    print("Duplicates to delete:\n")
    for dup, primary, subject in stories_to_delete[:10]:
        print(f"  US#{dup.get('ref')}: {subject[:60]}... (keep US#{primary.get('ref')})")
    if len(stories_to_delete) > 10:
        print(f"  ... and {len(stories_to_delete) - 10} more")

    # Confirm
    if not args.confirm:
        response = input(f"\n⚠️  Delete {len(stories_to_delete)} duplicate stories? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Cancelled")
            return

    # Delete duplicates
    print(f"\n🗑️  Deleting {len(stories_to_delete)} duplicate stories...\n")
    deleted = 0
    failed = 0

    for dup, primary, subject in stories_to_delete:
        if delete_story(headers, dup):
            deleted += 1
        else:
            failed += 1

    print(f"\n{'=' * 80}")
    print(f"Summary: {deleted} deleted, {failed} failed")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
