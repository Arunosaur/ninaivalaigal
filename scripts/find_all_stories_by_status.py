#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find all stories by status, including New and Ready"""

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

    # Group by status
    by_status = {}
    for story in all_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    # Focus on actionable statuses
    actionable_statuses = ["New", "Ready", "In progress", "In Progress", "Review/QA"]

    print("=" * 80)
    print("ALL STORIES BY STATUS (Actionable Statuses)")
    print("=" * 80)
    print()

    total_unassigned = 0

    for status in actionable_statuses:
        if status in by_status:
            stories = by_status[status]
            unassigned = [s for s in stories if not s.get("assigned_to")]

            if stories:
                print(f"{status.upper()} ({len(stories)} total, {len(unassigned)} unassigned):")
                print("-" * 80)

                for story in sorted(stories, key=lambda x: x.get("ref", 9999)):
                    ref = story.get("ref", "N/A")
                    subject = story.get("subject", "N/A")[:60]
                    assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
                    priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")

                    if not story.get("assigned_to"):
                        print(f"  ⭐ US#{ref:3d} [{priority:6s}] [{assigned_to:20s}] - {subject}")
                        total_unassigned += 1
                    else:
                        print(f"     US#{ref:3d} [{priority:6s}] [{assigned_to:20s}] - {subject}")
                print()

    print("=" * 80)
    print(f"Summary: {total_unassigned} unassigned stories in actionable statuses")
    print("=" * 80)

    if total_unassigned > 0:
        print()
        print("💡 Run: python3 scripts/find_unassigned_active_stories.py")
        print("   To assign all unassigned stories to Developer H")


if __name__ == "__main__":
    main()
