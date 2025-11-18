#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga User Stories for SPEC-031: Memory Relevance Ranking

Creates 5 detailed user stories to complete SPEC-031 implementation:
- US-270: Memory Relevance Ranking API Endpoint
- US-271: Memory API Relevance Score Integration
- US-272: Enhanced Context Matching
- US-273: Performance Testing and Validation
- US-274: Relevance Statistics API Endpoint
"""

import sys
from pathlib import Path

# Reuse the existing story creation infrastructure
sys.path.insert(0, str(Path(__file__).parent))

import json

from create_spec026_stories import (
    authenticate,
    create_user_story,
    get_or_create_tags,
    get_project_id,
    get_status_id,
)

# Configuration for SPEC-031
STORIES_FILE = Path(__file__).parent / "spec031_stories.json"


def load_stories():
    """Load story definitions from JSON file"""
    if not STORIES_FILE.exists():
        print(f"Error: Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("SPEC-031 Taiga Story Creator - Memory Relevance Ranking")
    print("=" * 70)
    print()
    print("This script will create 5 detailed user stories for SPEC-031:")
    print("  • US-270: Memory Relevance Ranking API Endpoint (P0)")
    print("  • US-271: Memory API Relevance Score Integration (P0)")
    print("  • US-272: Enhanced Context Matching (P1)")
    print("  • US-273: Performance Testing and Validation (P1)")
    print("  • US-274: Relevance Statistics API Endpoint (P2)")
    print()

    # Authenticate
    auth_token = authenticate()
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print()

    # Get status ID
    status_id = get_status_id(auth_token, project_id, "New")
    if not status_id:
        print("Error: Could not find 'New' status")
        sys.exit(1)
    print(f"✓ Using status ID: {status_id}")
    print()

    # Load stories
    stories = load_stories()
    print(f"✓ Loaded {len(stories)} story definitions from {STORIES_FILE.name}")
    print()

    # Display story summary
    print("Story Summary:")
    print("-" * 70)
    for i, story in enumerate(stories, 1):
        subject = story.get("subject", "Unknown")
        tags = story.get("tags", [])
        priority = next((tag for tag in tags if tag.startswith("p")), "Unknown")
        print(f"  {i}. {subject} ({priority.upper()})")
    print("-" * 70)
    print()

    # Get all unique tags
    all_tags = set()
    for story in stories:
        all_tags.update(story.get("tags", []))

    print(f"Creating/getting {len(all_tags)} tags...")
    # Create/get tags
    tag_colors = get_or_create_tags(auth_token, project_id, list(all_tags))
    print()

    # Create stories
    print("Creating user stories in Taiga...")
    print("-" * 70)

    created_count = 0
    failed_count = 0
    created_stories = []

    for story_data in stories:
        story_data["status_id"] = status_id
        result = create_user_story(auth_token, project_id, story_data, tag_colors)
        if result:
            created_count += 1
            created_stories.append({"ref": result.get("ref"), "subject": story_data["subject"], "id": result.get("id")})
        else:
            failed_count += 1

    print("-" * 70)
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  ✓ Created: {created_count} stories")
    if failed_count > 0:
        print(f"  ✗ Failed:  {failed_count} stories")
    print()

    if created_stories:
        print("Created Stories:")
        print("-" * 70)
        for story in created_stories:
            print(f"  #{story['ref']}: {story['subject']}")
            print(f"    URL: http://localhost:9000/project/ninaivalaigal/us/{story['ref']}")
        print("-" * 70)
        print()

    print("View all stories:")
    print(f"  • Backlog: http://localhost:9000/project/ninaivalaigal/backlog")
    print(f"  • Filter by tag 'spec-031' to see all SPEC-031 stories")
    print()
    print("Priority Breakdown:")
    print("  • P0 (Critical): US-270, US-271")
    print("  • P1 (High): US-272, US-273")
    print("  • P2 (Medium): US-274")
    print()
    print("=" * 70)
    print("✅ SPEC-031 Stories Created Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()




