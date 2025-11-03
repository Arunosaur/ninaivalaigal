#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Mark US#463 (SPEC-086) as Done in Taiga"""

import os
import sys

import requests

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def get_status_id_by_name(importer, project_id, status_name):
    """Get status ID by name"""
    # Use the session from importer
    url = f"{importer.base_url}/userstory-statuses"
    params = {"project": project_id}
    headers = importer._get_headers()

    response = importer._session.get(url, headers=headers, params=params)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name", "").lower() == status_name.lower():
                return status.get("id")
    return None


def main():
    """Mark US#463 as Done"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # US#463
    story_ref = 463
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: {story.get('subject', 'N/A')}")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")

    # Get project ID
    project_id = story.get("project")

    # Find "Done" status
    print(f"\n🔍 Finding 'Done' status...")
    done_status_id = get_status_id_by_name(importer, project_id, "Done")

    if not done_status_id:
        # Try alternative names
        for status_name in ["done", "Done", "DONE", "Closed", "closed"]:
            done_status_id = get_status_id_by_name(importer, project_id, status_name)
            if done_status_id:
                print(f"✅ Found status ID {done_status_id} for '{status_name}'")
                break

    if not done_status_id:
        print(f"❌ Could not find 'Done' status. Available statuses:")
        # List all statuses
        url = f"{importer.base_url}/userstory-statuses"
        params = {"project": project_id}
        headers = importer._get_headers()
        response = importer._session.get(url, headers=headers, params=params)
        if response.status_code == 200:
            statuses = response.json()
            for status in statuses:
                print(f"   - {status.get('name')} (ID: {status.get('id')}, Closed: {status.get('is_closed')})")
        return

    # Update story status to Done
    updates = {
        "status": done_status_id,
    }

    print(f"\n📝 Updating US#{story_ref} status to Done...")

    try:
        updated_story = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if updated_story:
            print(f"✅ Story US#{story_ref} marked as Done successfully!")
            print(f"   New status: {updated_story.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
        else:
            print(f"❌ Failed to update story US#{story_ref}")

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
