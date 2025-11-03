#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Check for US story for SPEC-094 and create if missing"""

import json
import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

import requests
from taiga_import_tasks import TaigaImporter


def main():
    """Check for SPEC-094 story and create if missing"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project_slug = "ninaivalaigal"

    # Get project ID
    project_info = importer._make_request("GET", f"/projects/by_slug?slug={project_slug}")
    if not project_info:
        print("❌ Failed to get project info")
        return
    project_id = project_info["id"]

    # Search for stories with spec-094 tag
    print("Searching for stories with spec-094 tag...")
    stories = importer._make_request("GET", f"/userstories?project={project_id}")

    spec094_story = None
    if stories:
        for story in stories:
            tags = story.get("tags", [])
            tag_names = [t.get("name", t) if isinstance(t, dict) else str(t) for t in tags]
            if "spec-094" in [str(t).lower() for t in tag_names]:
                spec094_story = story
                break

    if spec094_story:
        print(f"✅ Found existing story: US#{spec094_story.get('ref')}: {spec094_story.get('subject')}")
        print(f"   Status: {spec094_story.get('status_extra_info', {}).get('name', 'Unknown')}")
        return spec094_story

    print("❌ No story found for SPEC-094")
    print("   Would need to create one, but skipping for now")
    return None


if __name__ == "__main__":
    main()
