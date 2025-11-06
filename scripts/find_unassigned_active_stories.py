#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find all unassigned active stories and assign to Developer H"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")
developer_h_username = os.getenv("DEVELOPER_H_USERNAME", "developer-h")


def get_user_by_username(importer, username):
    """Get user ID by username"""
    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/users"
    params = {"username": username}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]
    return None


def get_all_user_stories(importer, project_id):
    """Get all user stories for a project"""
    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/userstories"
    params = {"project": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []


def prioritize_stories(stories):
    """Prioritize stories by status and priority"""
    status_priority = {
        "New": 1,
        "Ready": 1,
        "In progress": 2,
        "In Progress": 2,
        "Review/QA": 3,
    }

    def get_priority(story):
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        status_prio = status_priority.get(status_name, 99)

        # Priority: High > Normal > Low
        priority_order = {3: 1, 2: 2, 1: 3}  # High=3, Normal=2, Low=1
        priority_prio = priority_order.get(story.get("priority", 2), 2)

        # Reference number (lower = older, potentially more pressing)
        ref = story.get("ref", 9999)

        return (status_prio, priority_prio, ref)

    return sorted(stories, key=get_priority)


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    project = importer.get_project("ninaivalaigal")

    if not project:
        print("Project not found")
        return

    # Get Developer H
    developer_h = get_user_by_username(importer, developer_h_username)
    if not developer_h:
        print(f"Developer H user '{developer_h_username}' not found")
        return

    developer_h_id = developer_h["id"]
    print(f"✅ Developer H: {developer_h.get('full_name', developer_h_username)} (ID: {developer_h_id})")
    print()

    # Get all stories
    all_stories = get_all_user_stories(importer, project["id"])

    # Find active unassigned stories
    active_unassigned = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        assigned_to = story.get("assigned_to")

        if status_name not in ["Done", "Archived"] and not assigned_to:
            active_unassigned.append(story)

    if not active_unassigned:
        print("✅ No unassigned active stories found")
        return

    # Prioritize
    prioritized = prioritize_stories(active_unassigned)

    print("=" * 70)
    print(f"FOUND {len(prioritized)} UNASSIGNED ACTIVE STORIES")
    print("=" * 70)
    print()

    for i, story in enumerate(prioritized, 1):
        ref = story.get("ref", "N/A")
        subject = story.get("subject", "N/A")
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
        print(f"{i:2d}. US#{ref:3d} [{status:15s}] [{priority:6s}] - {subject}")

    print()
    print("=" * 70)
    print("ASSIGNING TO DEVELOPER H")
    print("=" * 70)
    print()

    assigned_count = 0
    for story in prioritized:
        ref = story.get("ref", "N/A")
        subject = story.get("subject", "N/A")
        status = story.get("status_extra_info", {}).get("name", "Unknown")

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
                try:
                    importer.create_comment(story["id"], comment)
                except:
                    pass  # Comment creation is optional
            else:
                print(f"❌ Failed to assign US#{ref}")
        except Exception as e:
            print(f"❌ US#{ref} - Error: {e}")

    print()
    print("=" * 70)
    print(f"✅ Assigned {assigned_count} stories to Developer H")
    print("=" * 70)

    if assigned_count > 0:
        print()
        print("📋 Next: Review assigned stories and start working on them")
        print("   Use: python3 scripts/get_story_details.py <story_ref>")


if __name__ == "__main__":
    main()
