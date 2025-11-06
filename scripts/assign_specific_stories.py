#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Assign specific stories to Developer H"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")
developer_h_username = os.getenv("DEVELOPER_H_USERNAME", "developer-h")


def get_user_by_username(importer, username):
    """Get user ID by username"""
    import requests

    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/users"
    params = {"username": username}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 assign_specific_stories.py <story_ref1> [story_ref2] ...")
        print("Example: python3 assign_specific_stories.py 19 22")
        return

    story_refs = [int(ref) for ref in sys.argv[1:]]

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    # Get Developer H
    developer_h = get_user_by_username(importer, developer_h_username)
    if not developer_h:
        print(f"Developer H user '{developer_h_username}' not found")
        return

    developer_h_id = developer_h["id"]
    print(f"✅ Developer H: {developer_h.get('full_name', developer_h_username)} (ID: {developer_h_id})")
    print()

    print("=" * 70)
    print("ASSIGNING STORIES TO DEVELOPER H")
    print("=" * 70)
    print()

    assigned_count = 0
    for ref in story_refs:
        story = importer.get_user_story("ninaivalaigal", ref)
        if not story:
            print(f"❌ Story #{ref} not found")
            continue

        subject = story.get("subject", "N/A")
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        current_assigned = story.get("assigned_to")

        if current_assigned == developer_h_id:
            print(f"⏭️  US#{ref} - {subject} (already assigned to Developer H)")
            continue

        try:
            result = importer.assign_story(
                story_id=story["id"], assigned_to_id=developer_h_id, version=story["version"]
            )
            if result:
                print(f"✅ Assigned US#{ref} - {subject} [{status}]")
                assigned_count += 1

                # Add comment
                comment = (
                    f"Developer H assigned to this story. Starting work. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                importer.create_comment(story["id"], comment)
            else:
                print(f"❌ Failed to assign US#{ref}")
        except Exception as e:
            print(f"❌ US#{ref} - Error: {e}")

    print()
    print(f"📊 Assigned {assigned_count} stories to Developer H")


if __name__ == "__main__":
    main()
