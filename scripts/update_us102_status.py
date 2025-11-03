#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update US#102 status to Done"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

from tasks.scripts.taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
importer._get_auth_token()

story = importer.get_user_story("ninaivalaigal", 102)
if not story:
    print("❌ Story US#102 not found")
    sys.exit(1)

print(f'✅ Found story: {story.get("subject", "N/A")}')
print(f'   Current status: {story.get("status_extra_info", {}).get("name", "N/A")}')
print(f'   Story ID: {story["id"]}')
print(f'   Version: {story["version"]}')

# Get statuses
headers = {"Authorization": f"Bearer {importer._auth_token}"}
statuses_url = f'{taiga_url}/api/v1/userstory-statuses?project={story["project"]}'
statuses_resp = requests.get(statuses_url, headers=headers)

if statuses_resp.status_code == 200:
    statuses = statuses_resp.json()
    print(f"\nAvailable statuses:")
    for s in statuses:
        is_done = "done" in s["name"].lower() or "complete" in s["name"].lower()
        marker = "✅" if is_done else "  "
        print(f'{marker} {s["id"]}: {s["name"]} (slug: {s["slug"]})')

    done_status = next((s for s in statuses if "done" in s["name"].lower() or "complete" in s["name"].lower()), None)
    if done_status:
        print(f'\n📝 Updating to: {done_status["name"]} (ID: {done_status["id"]})')
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates={"status": done_status["id"]},
            retry_on_version_conflict=True,
            max_retries=3,
        )
        if result:
            print("✅ Status updated successfully!")
            print(f'   New version: {result.get("version", "Unknown")}')
            print(f"   Story URL: {taiga_url}/project/ninaivalaigal/us/102")
        else:
            print("❌ Failed to update status")
    else:
        print('⚠️  No "Done" status found')
else:
    print(f"❌ Failed to fetch statuses: {statuses_resp.status_code} - {statuses_resp.text}")
    sys.exit(1)
