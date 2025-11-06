#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Get detailed information about a Taiga story"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import json

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_story_details.py <story_ref>")
        print("Example: python3 get_story_details.py 6")
        return

    story_ref = int(sys.argv[1])

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"Story #{story_ref} not found")
        return

    print("=" * 70)
    print(f"Story #{story['ref']}: {story['subject']}")
    print("=" * 70)
    print()
    priority_map = {1: "Low", 2: "Normal", 3: "High"}
    print(f"Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"Priority: {priority_map.get(story.get('priority', 2), 'Normal')}")
    assigned_info = story.get("assigned_to_extra_info")
    if assigned_info:
        print(f"Assigned to: {assigned_info.get('full_name', 'Unassigned')}")
    else:
        print(f"Assigned to: Unassigned")
    print()
    print("Description:")
    print("-" * 70)
    print(story.get("description", "No description"))
    print()
    tags = story.get("tags", [])
    if tags:
        # Tags might be a list of strings or a list of lists
        tag_strs = [str(t) if isinstance(t, str) else str(t[0]) if isinstance(t, list) and t else "" for t in tags]
        tag_strs = [t for t in tag_strs if t]
        print("Tags:", ", ".join(tag_strs) if tag_strs else "None")
    else:
        print("Tags: None")
    print()
    print("Full JSON:")
    print("-" * 70)
    print(json.dumps(story, indent=2, default=str))


if __name__ == "__main__":
    main()
