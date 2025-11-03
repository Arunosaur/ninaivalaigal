#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Improved helper for Developer A - US#295 Update

This version includes better error handling and multiple fallback methods.
Addresses common issues:
- Authentication problems
- Story not found
- Version conflicts
- Network issues
"""

import os
import sys
from datetime import datetime

# Ensure we can import taiga_import_tasks
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_script_dir = os.path.join(script_dir, "..", "tasks", "tmp", "scripts")
sys.path.insert(0, tasks_script_dir)

try:
    from taiga_import_tasks import TaigaImporter
except ImportError as e:
    print(f"❌ Failed to import TaigaImporter: {e}")
    print(f"   Expected location: {tasks_script_dir}/taiga_import_tasks.py")
    sys.exit(1)


def update_story_295():
    """Update US#295 with storage backend completion details"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    print(f"Connecting to Taiga at {taiga_url}...")
    print(f"Username: {username}")

    try:
        # Initialize importer
        importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

        # Verify project exists
        project = importer.get_project("ninaivalaigal")
        if not project:
            print("❌ Project 'ninaivalaigal' not found")
            print("   Available projects:")
            # Try to list projects (if API supports it)
            return 1
        print(f"✅ Found project: {project.get('name', 'ninaivalaigal')}")

        # Get story
        print("Looking for story #295...")
        story = importer.get_user_story("ninaivalaigal", 295)
        if not story:
            print("❌ Story #295 not found")
            print("\nTrying to find stories with 'storage' in subject...")

            # Search for similar stories
            url = f"{importer.base_url}/userstories"
            params = {"project": project["id"]}
            headers = importer._get_headers()

            try:
                response = importer._session.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    stories = response.json()
                    matching = [s for s in stories if "storage" in s.get("subject", "").lower()]
                    if matching:
                        print(f"   Found {len(matching)} story/stories with 'storage':")
                        for s in matching[:5]:
                            print(f"   - #{s.get('ref')}: {s.get('subject')}")
                    else:
                        print("   No stories found with 'storage' in subject")
            except Exception as e:
                print(f"   Could not search stories: {e}")

            return 1

        story_ref = story.get("ref", "N/A")
        print(f"✅ Found story #{story_ref}: {story['subject']}")

        # Original description
        original_description = story.get("description") or ""

        # Completion summary
        summary = """✅ Storage backend foundation landed.

• Created shared Python package `shared/storage/ninaivalaigal_storage` with S3/MinIO abstraction (config loader, factory, boto3 backend, typed exceptions). Services can now call `create_storage_backend()` to upload/download/delete and mint pre-signed URLs.

• Added developer docs (`shared/storage/README.md`) plus packaging metadata (`setup.py`) so we can install it via `pip install -e shared/storage`.

• Seeded unit tests (`shared/storage/tests/`) covering env config parsing and the S3 backend using moto; updated dev requirements for boto3 + moto.

• Expanded `.env.dev` and `config/ninaivalaigal.config.json.template` to expose STORAGE_* variables (bucket, prefix, endpoint, credentials, SSL flags). Defaults target local MinIO (`ninaivalaigal-dev-attachments`) and auto-create the bucket.

Blocked only on running the new tests inside the `nina` conda env—the `pip install -e shared/storage` step hit an exit code 1 in `conda run`. Need to rerun inside the env (e.g. `conda activate nina; pip install -e shared/storage`) before executing `pytest shared/storage/tests`. Everything else is ready for Multipart (US#296) to build on."""

        # Check if already present
        if summary.strip() in original_description:
            print("✅ Update already present in description")
            return 0

        # Append with timestamp
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n---\n**Update {stamp}**\n{summary}\n"
        new_desc = original_description + entry

        print(f"Updating description (version {story['version']})...")

        # Update story (with automatic version conflict handling)
        result = importer.update_user_story(
            story["id"], story["version"], {"description": new_desc}, retry_on_version_conflict=True, max_retries=3
        )

        if result:
            print("✅ Description updated successfully")
            print(f"   New version: {result['version']}")
            print(f"   Story link: {taiga_url}/project/ninaivalaigal/us/{story_ref}")
            return 0
        else:
            print("❌ Failed to update description")
            print("   Possible causes:")
            print("   - Version conflict (try again)")
            print("   - Permission issue")
            print("   - Network error")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(update_story_295())
