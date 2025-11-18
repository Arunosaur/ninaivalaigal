#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Assign active unassigned stories to Developer H and start work"""

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


def get_project_statuses(importer, project_id):
    """Get status definitions for the project"""
    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/userstory-statuses"
    params = {"project": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        statuses = response.json()
        return {s["id"]: s for s in statuses}
    return {}


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

    # Also find stories assigned to Developer H that are active
    active_assigned_to_h = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        assigned_to = story.get("assigned_to")

        if status_name not in ["Done", "Archived"] and assigned_to == developer_h_id:
            active_assigned_to_h.append(story)

    print("=" * 70)
    print("ACTIVE STORIES ASSIGNMENT")
    print("=" * 70)
    print()

    # Assign unassigned stories
    if active_unassigned:
        print(f"📌 Found {len(active_unassigned)} unassigned active stories:")
        print()

        assigned_count = 0
        for story in active_unassigned:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")

            try:
                result = importer.assign_story(
                    story_id=story["id"], assigned_to_id=developer_h_id, version=story["version"]
                )
                if result:
                    print(f"✅ Assigned US#{ref} - {subject} [{status_name}]")
                    assigned_count += 1

                    # Add comment
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    comment = f"Developer H assigned to this story. Starting work. {timestamp}"
                    importer.create_comment(story["id"], comment)
                else:
                    print(f"❌ Failed to assign US#{ref}")
            except Exception as e:
                print(f"❌ US#{ref} - Error: {e}")

        print(f"\n📊 Assigned {assigned_count} stories to Developer H")
        print()

    # Show Developer H's active stories
    if active_assigned_to_h:
        print(f"👤 Developer H's active stories ({len(active_assigned_to_h)}):")
        print()
        for story in active_assigned_to_h:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")

            print(f"  US#{ref} [{status_name}] [{priority}] - {subject}")
        print()

    print("=" * 70)
    print("✅ Assignment complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
