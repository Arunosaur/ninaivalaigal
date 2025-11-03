#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#568 (SPEC-088) story status to Planned"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#568 story status to Planned"""
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

    # Find "Planned" status
    print(f"\n🔍 Finding 'Planned' status...")
    project_id = story.get("project")

    import requests

    status_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
    headers = importer._get_headers()
    status_response = requests.get(status_url, headers=headers)

    planned_status_id = None
    if status_response.status_code == 200:
        statuses = status_response.json()
        print(f"\n📋 Available statuses:")
        for status in statuses:
            if isinstance(status, dict):
                status_name = status.get("name", "")
                status_id = status.get("id")
                is_current = status_id == story.get("status")
                marker = "← Current" if is_current else ""
                print(f"   - {status_name} (ID: {status_id}) {marker}")

                status_name_lower = status_name.lower()
                if "planned" in status_name_lower or status_name_lower == "planned":
                    planned_status_id = status_id
        print()

    if planned_status_id:
        print(f"✅ Found 'Planned' status (ID: {planned_status_id})")
        print(f"\n📝 Updating status to 'Planned'...")

        try:
            result = importer.update_user_story(
                story_id=story["id"],
                version=story["version"],
                updates={"status": planned_status_id},
                retry_on_version_conflict=True,
                max_retries=3,
            )

            if result:
                print(f"✅ Status updated to 'Planned' successfully!")
                print(f"   New version: {result.get('version', 'Unknown')}")
                print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
            else:
                print(f"❌ Failed to update story status")
        except Exception as e:
            print(f"❌ Error updating story: {e}")
            import traceback

            traceback.print_exc()
    else:
        print(f"⚠️  Could not find 'Planned' status")
        print(f"   Available statuses listed above")
        print(f"   Please manually change status in Taiga UI")
        print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")


if __name__ == "__main__":
    main()
