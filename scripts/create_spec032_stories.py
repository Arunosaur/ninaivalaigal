#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga User Stories for SPEC-032: Memory Attachments

Creates 9 detailed user stories to implement SPEC-032:
- US-275: Memory Attachments Database Schema (P0)
- US-276: Memory Attachment Upload Endpoint (P0)
- US-277: Memory Attachment Retrieval Endpoints (P0)
- US-278: Memory Attachment Deletion Endpoint (P0)
- US-279: File Type Validation and Size Limits (P1)
- US-280: ACL Integration for Memory Attachments (P1)
- US-281: Memory Attachment UI Components (P2)
- US-282: Memory Attachment CLI Commands (P2)
- US-283: MCP Integration for Memory Attachments (P2)
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

# Configuration for SPEC-032
STORIES_FILE = Path(__file__).parent / "spec032_stories.json"


def load_stories():
    """Load story definitions from JSON file"""
    if not STORIES_FILE.exists():
        print(f"Error: Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("SPEC-032 Taiga Story Creator - Memory Attachments")
    print("=" * 70)
    print()
    print("This script will create 9 detailed user stories for SPEC-032:")
    print("  • US-275: Memory Attachments Database Schema (P0)")
    print("  • US-276: Memory Attachment Upload Endpoint (P0)")
    print("  • US-277: Memory Attachment Retrieval Endpoints (P0)")
    print("  • US-278: Memory Attachment Deletion Endpoint (P0)")
    print("  • US-279: File Type Validation and Size Limits (P1)")
    print("  • US-280: ACL Integration for Memory Attachments (P1)")
    print("  • US-281: Memory Attachment UI Components (P2)")
    print("  • US-282: Memory Attachment CLI Commands (P2)")
    print("  • US-283: MCP Integration for Memory Attachments (P2)")
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
    print(f"  • Filter by tag 'spec-032' to see all SPEC-032 stories")
    print()
    print("Priority Breakdown:")
    print("  • P0 (Critical): US-275, US-276, US-277, US-278")
    print("  • P1 (High): US-279, US-280")
    print("  • P2 (Medium): US-281, US-282, US-283")
    print()
    print("Note: These stories depend on EPIC#022 infrastructure (US#295-296).")
    print("      Verify EPIC#022 completion before starting SPEC-032 work.")
    print()
    print("=" * 70)
    print("✅ SPEC-032 Stories Created Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()




