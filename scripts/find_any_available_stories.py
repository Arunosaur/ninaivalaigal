#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find any available stories that could be worked on, including those in various statuses"""

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

    # Get all stories
    all_stories = get_all_user_stories(importer, project["id"])

    print(f"Total stories in project: {len(all_stories)}")
    print()

    # Group by status
    by_status = {}
    by_assignment = {"unassigned": [], "assigned": []}

    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        assigned_to = story.get("assigned_to")

        if status_name not in by_status:
            by_status[status_name] = []
        by_status[status_name].append(story)

        if assigned_to:
            by_assignment["assigned"].append(story)
        else:
            by_assignment["unassigned"].append(story)

    print("=" * 80)
    print("STORIES BY STATUS")
    print("=" * 80)
    for status in sorted(by_status.keys()):
        count = len(by_status[status])
        print(f"{status:20s}: {count:3d} stories")
    print()

    print("=" * 80)
    print("UNASSIGNED STORIES (by status)")
    print("=" * 80)
    for status in sorted(by_status.keys()):
        unassigned = [s for s in by_status[status] if not s.get("assigned_to")]
        if unassigned:
            print(f"\n{status} ({len(unassigned)} unassigned):")
            for story in unassigned[:10]:  # Show first 10
                ref = story.get("ref", "N/A")
                subject = story.get("subject", "N/A")[:60]
                priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
                print(f"  US#{ref:3d} [{priority:6s}] - {subject}")
            if len(unassigned) > 10:
                print(f"  ... and {len(unassigned) - 10} more")
    print()

    # Look for stories in "New" or "Ready" status
    actionable_statuses = ["New", "Ready", "In Progress", "In progress", "Review/QA"]
    actionable = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        if status_name in actionable_statuses and not story.get("assigned_to"):
            actionable.append(story)

    if actionable:
        print("=" * 80)
        print(f"ACTIONABLE UNASSIGNED STORIES ({len(actionable)} found)")
        print("=" * 80)
        for story in sorted(actionable, key=lambda x: x.get("ref", 9999)):
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            print(f"US#{ref:3d} [{status:15s}] [{priority:6s}] - {subject}")
    else:
        print("=" * 80)
        print("NO ACTIONABLE UNASSIGNED STORIES FOUND")
        print("=" * 80)
        print()
        print("All stories are either:")
        print("  - Assigned to other developers")
        print("  - Completed (Done/Archived)")
        print("  - In other statuses")
        print()
        print("Consider:")
        print("  - Checking for stories that need follow-up work")
        print("  - Creating new stories in Taiga")
        print("  - Reviewing completed stories for enhancements")


if __name__ == "__main__":
    main()
