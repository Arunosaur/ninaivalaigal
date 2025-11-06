#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Update US#6 with accessibility implementation progress
#

import os
import sys
from datetime import datetime

# Add tasks/scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_dir = os.path.join(script_dir, "..", "tasks", "scripts")
sys.path.insert(0, tasks_dir)

from taiga_import_tasks import TaigaImporter


def update_story_progress(progress_text: str):
    """Update US#6 with progress update."""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    try:
        importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

        story = importer.get_user_story("ninaivalaigal", 6)
        if not story:
            print("❌ Story #6 not found")
            return False

        # Append progress update
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        update = f"\n\n---\n**Progress Update {timestamp}**\n{progress_text}\n"

        original_description = story.get("description") or ""

        # Check if this update is already present
        if progress_text.strip() in original_description:
            print("⚠️  Update already present in description")
            return True

        new_description = original_description + update

        result = importer.update_user_story(story["id"], story["version"], {"description": new_description})

        if result:
            print(f"✅ Updated US#6: {progress_text[:60]}...")
            return True
        else:
            print("❌ Failed to update story")
            return False
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        progress_text = " ".join(sys.argv[1:])
        update_story_progress(progress_text)
    else:
        print("Usage: python3 update_us6_progress.py 'Progress text here'")
