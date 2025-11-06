#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""View backlog stories matching Taiga backlog filter"""

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

    # Filter: exclude_status=5,6 (Done, Archived) and exclude_assigned_users=null (assigned only)
    # This means: show assigned stories that are NOT Done/Archived
    actionable_statuses = ["New", "Ready", "In progress", "In Progress", "Review/QA"]

    assigned_actionable = []
    for story in all_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        assigned_to = story.get("assigned_to")

        if status in actionable_statuses and assigned_to:
            assigned_actionable.append(story)

    print("=" * 80)
    print("BACKLOG STORIES (Assigned, excluding Done/Archived)")
    print("=" * 80)
    print()
    print(f"Found {len(assigned_actionable)} assigned actionable stories")
    print()

    if not assigned_actionable:
        print("No assigned actionable stories found")
        print()
        print("💡 This matches the backlog filter:")
        print("   - exclude_status=5,6 (excludes Done/Archived)")
        print("   - exclude_assigned_users=null (shows only assigned)")
        return

    # Group by assignee
    by_assignee = {}
    for story in assigned_actionable:
        assigned_info = story.get("assigned_to_extra_info", {})
        assignee = assigned_info.get("full_name", "Unknown") if assigned_info else "Unknown"
        if assignee not in by_assignee:
            by_assignee[assignee] = []
        by_assignee[assignee].append(story)

    # Sort by assignee name
    for assignee, stories in sorted(by_assignee.items()):
        print(f"{assignee} ({len(stories)} stories):")
        print("-" * 80)

        # Sort by status priority, then by ref
        status_order = {"New": 1, "Ready": 2, "In progress": 3, "In Progress": 3, "Review/QA": 4}
        stories.sort(
            key=lambda x: (status_order.get(x.get("status_extra_info", {}).get("name", ""), 99), x.get("ref", 9999))
        )

        for story in stories:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"

            print(f"  US#{ref:3d} [{status:15s}] [{priority:6s}] {created}")
            print(f"     {subject}")

            # Show description preview
            desc = story.get("description", "")
            if desc:
                desc_preview = desc.replace("\n", " ")[:100]
                print(f"     {desc_preview}...")
            print()

    print("=" * 80)
    print(f"Total: {len(assigned_actionable)} assigned actionable stories")
    print("=" * 80)


if __name__ == "__main__":
    main()
