#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga User Stories for SPEC-027: Billing Engine Integration Testing

Uses the same infrastructure as SPEC-026 story creation.
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

# Update configuration for SPEC-027
STORIES_FILE = Path(__file__).parent / "spec027_stories.json"


def load_stories():
    """Load story definitions from JSON file"""
    if not STORIES_FILE.exists():
        print(f"Error: Stories file not found: {STORIES_FILE}")
        sys.exit(1)

    with open(STORIES_FILE, "r") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("SPEC-027 Taiga Story Creator (Testing Focus)")
    print("=" * 60)
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
    print(f"Loaded {len(stories)} testing story definitions")
    print()

    # Get all unique tags
    all_tags = set()
    for story in stories:
        all_tags.update(story.get("tags", []))

    # Create/get tags
    tag_colors = get_or_create_tags(auth_token, project_id, list(all_tags))
    print()

    # Create stories
    print("Creating user stories...")
    print("-" * 60)

    created_count = 0
    failed_count = 0

    for story_data in stories:
        story_data["status_id"] = status_id
        result = create_user_story(auth_token, project_id, story_data, tag_colors)
        if result:
            created_count += 1
        else:
            failed_count += 1

    print("-" * 60)
    print()
    print("Summary:")
    print(f"  ✓ Created: {created_count} testing stories")
    if failed_count > 0:
        print(f"  ✗ Failed:  {failed_count} stories")
    print()
    print(f"View stories at: http://localhost:9000/project/ninaivalaigal/backlog")
    print("Filter by: spec-027 or testing")
    print("=" * 60)


if __name__ == "__main__":
    main()
