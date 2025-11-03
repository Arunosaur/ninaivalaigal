#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Find duplicate Taiga user stories across the project.

This script identifies stories with identical subjects, descriptions, and tags
that were likely created in batch operations.
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
    # Remove whitespace and normalize
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
            print(f"⚠️  Failed to fetch stories page {page}: {stories_response.status_code}")
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
    # Group by normalized key (subject + description + tags)
    groups = defaultdict(list)

    for story in stories:
        subject = story.get("subject", "").strip()
        description = normalize_description(story.get("description", "") or "")
        tags = normalize_tags(story.get("tags", []))

        # Create a key for grouping
        key = (
            subject.lower(),
            description,
            tuple(tags),
        )

        groups[key].append(story)

    # Find groups with duplicates (more than one story)
    duplicates = []
    for key, group_stories in groups.items():
        if len(group_stories) > 1:
            # Sort by creation date to identify the "primary" (first created)
            group_stories.sort(key=lambda s: s.get("created_date", ""), reverse=False)
            duplicates.append((group_stories, key[0]))  # Use subject as identifier

    return duplicates


def format_story_info(story: Dict) -> str:
    """Format story information for display."""
    ref = story.get("ref", "N/A")
    subject = story.get("subject", "N/A")[:60]
    status_info = story.get("status_extra_info")
    status = status_info.get("name", "Unknown") if status_info else "Unknown"
    created = story.get("created_date", "")[:19] if story.get("created_date") else "N/A"
    assigned_info = story.get("assigned_to_extra_info")
    assigned = assigned_info.get("full_name_display", "Unassigned") if assigned_info else "Unassigned"
    tags = normalize_tags(story.get("tags", []))
    tags_str = ", ".join(tags[:3]) + ("..." if len(tags) > 3 else "")

    return f"  US#{ref}: {subject} | Status: {status} | Created: {created} | Assigned: {assigned} | Tags: {tags_str}"


def main():
    """Main function to find and report duplicates."""
    print("=" * 80)
    print("Finding Duplicate Taiga User Stories")
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

    print(f"\n⚠️  Found {len(duplicates)} groups of duplicate stories:\n")

    total_duplicates = 0
    for group, subject in duplicates:
        if len(group) > 1:
            total_duplicates += len(group) - 1  # Count extras (not primary)
            print(f"\n{'=' * 80}")
            print(f"Duplicate Group: {subject[:70]}")
            print(f"{'=' * 80}")
            print(f"Found {len(group)} identical stories:\n")

            for i, story in enumerate(group):
                if i == 0:
                    print("✅ PRIMARY (keep this one):")
                else:
                    print(f"❌ DUPLICATE #{i}:")
                print(format_story_info(story))
                print()

    print(f"\n{'=' * 80}")
    print(f"Summary: {len(duplicates)} duplicate groups, {total_duplicates} duplicate stories to close/delete")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
