#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Get US#575 (SPEC-097) story details from Taiga"""

import json
import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Get US#575 story details"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # Try US#575 first, then check for duplicates
    story_refs = [575, 465, 493, 521]  # Known duplicates from analysis

    for story_ref in story_refs:
        story = importer.get_user_story("ninaivalaigal", story_ref)
        if story:
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
            print(f"  {description[:300]}{'...' if len(description) > 300 else ''}")

            # Save first story found
            if story_ref == story_refs[0]:
                output_file = "docs/spec-analysis/US575_STORY_DETAILS.json"
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "w") as f:
                    json.dump(story, f, indent=2, default=str)
                print(f"\n💾 Full story details saved to: {output_file}")
            break
    else:
        print(f"❌ No SPEC-097 stories found in Taiga")


if __name__ == "__main__":
    main()
