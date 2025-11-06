#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""List all active (non-Done) stories in Taiga"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def get_all_user_stories(importer, project_id):
    """Get all user stories for a project"""
    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/userstories"
    params = {"project": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    project = importer.get_project("ninaivalaigal")

    if not project:
        print("Project not found")
        return

    all_stories = get_all_user_stories(importer, project["id"])

    # Filter out Done and Archived
    active_stories = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        if status_name not in ["Done", "Archived"]:
            active_stories.append(story)

    # Sort by status, then by ref
    status_order = {"New": 1, "Ready": 2, "In progress": 3, "In Progress": 3, "Review/QA": 4}
    active_stories.sort(
        key=lambda x: (status_order.get(x.get("status_extra_info", {}).get("name", ""), 99), x.get("ref", 9999))
    )

    print("=" * 80)
    print(f"ACTIVE STORIES (Total: {len(active_stories)})")
    print("=" * 80)
    print()

    if not active_stories:
        print("No active stories found")
        return

    # Group by status
    by_status = {}
    for story in active_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    for status in ["New", "Ready", "In progress", "In Progress", "Review/QA"]:
        if status in by_status:
            stories = by_status[status]
            print(f"{status.upper()} ({len(stories)} stories):")
            print("-" * 80)
            for story in stories:
                ref = story.get("ref", "N/A")
                subject = story.get("subject", "N/A")
                assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
                priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")

                print(f"  US#{ref:3d} [{priority:6s}] [{assigned_to:20s}] - {subject}")
            print()


if __name__ == "__main__":
    main()
