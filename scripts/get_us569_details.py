#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Get US#569 (SPEC-089) story details from Taiga"""

import json
import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Get US#569 story details"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#569 is the story for SPEC-089
    story_ref = 569
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print("=" * 80)
    print(f"US#{story.get('ref')}: {story.get('subject')}")
    print("=" * 80)
    print(f"\n📊 Status:")
    print(f"  Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"  Assigned to: {story.get('assigned_to_extra_info', {}).get('full_name_display', 'Unassigned')}")
    print(f"  Created: {story.get('created_date', 'Unknown')}")
    print(f"  Modified: {story.get('modified_date', 'Unknown')}")

    print(f"\n🏷️  Tags:")
    tags = story.get("tags", [])
    tag_names = []
    for tag in tags:
        if isinstance(tag, dict):
            tag_names.append(str(tag.get("name", "")))
        else:
            tag_names.append(str(tag))
    print(f"  {', '.join(tag_names) if tag_names else 'No tags'}")

    print(f"\n📝 Description:")
    description = story.get("description", "No description")
    print(f"  {description[:500]}{'...' if len(description) > 500 else ''}")

    print(f"\n📋 Story Details:")
    print(f"  ID: {story.get('id')}")
    print(f"  Version: {story.get('version')}")
    print(f"  Project: {story.get('project_extra_info', {}).get('name', 'Unknown')}")

    # Save full story to JSON for reference
    output_file = "docs/spec-analysis/US569_STORY_DETAILS.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(story, f, indent=2, default=str)
    print(f"\n💾 Full story details saved to: {output_file}")

    return story


if __name__ == "__main__":
    main()
