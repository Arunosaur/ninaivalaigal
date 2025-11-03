#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#568 (SPEC-088) story status to Ready"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#568 story status to Ready"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#568 is the story for SPEC-088
    story_ref = 568
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: {story.get('subject', 'N/A')}")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Current version: {story.get('version')}")

    # Use "Ready" status (ID: 2) - closest to "Planned"
    ready_status_id = 2

    print(f"\n📝 Updating status to 'Ready' (closest to 'Planned')...")

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates={"status": ready_status_id},
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if result:
            print(f"✅ Status updated to 'Ready' successfully!")
            print(f"   New version: {result.get('version', 'Unknown')}")
            print(f"   New status: {result.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
        else:
            print(f"❌ Failed to update story status")
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
