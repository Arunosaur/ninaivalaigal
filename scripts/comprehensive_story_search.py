#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Comprehensive search for all actionable stories in Taiga"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime, timedelta

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


def is_recent(story, days=30):
    """Check if story was created or modified recently"""
    created_date = story.get("created_date")
    modified_date = story.get("modified_date")

    if not created_date:
        return False

    try:
        if "T" in created_date:
            created = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
            cutoff = datetime.now(created.tzinfo) - timedelta(days=days)
            return created >= cutoff
    except:
        pass

    return False


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

    # Get all stories
    all_stories = get_all_user_stories(importer, project["id"])

    print("=" * 80)
    print("COMPREHENSIVE STORY SEARCH - Developer H")
    print("=" * 80)
    print()

    # Find all actionable stories
    actionable_statuses = ["New", "Ready", "In progress", "In Progress", "Review/QA"]
    actionable = []

    for story in all_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status in actionable_statuses:
            actionable.append(story)

    # Group by status
    by_status = {}
    for story in actionable:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    # Show by status
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
                    assigned_info = story.get("assigned_to_extra_info")
                    assigned = assigned_info.get("full_name", "Unassigned") if assigned_info else "Unassigned"
                    priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
                    created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"

                    if not story.get("assigned_to"):
                        print(f"  ⭐ US#{ref:3d} [{priority:6s}] [{assigned:20s}] {created} - {subject}")
                    else:
                        print(f"     US#{ref:3d} [{priority:6s}] [{assigned:20s}] {created} - {subject}")
                print()

    # Find unassigned actionable stories
    unassigned_actionable = [s for s in actionable if not s.get("assigned_to")]

    if unassigned_actionable:
        print("=" * 80)
        print(f"FOUND {len(unassigned_actionable)} UNASSIGNED ACTIONABLE STORIES")
        print("=" * 80)
        print()

        # Prioritize: High priority first, then by ref number
        unassigned_actionable.sort(
            key=lambda x: (
                -x.get("priority", 2),  # Higher priority first (3=High, 2=Normal, 1=Low)
                x.get("ref", 9999),  # Then by ref number
            )
        )

        for story in unassigned_actionable:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            print(f"  US#{ref:3d} [{status:15s}] [{priority:6s}] - {subject}")

        print()
        print("=" * 80)
        print("ASSIGNING TO DEVELOPER H")
        print("=" * 80)
        print()

        assigned_count = 0
        for story in unassigned_actionable:
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

                    comment = f"Developer H assigned to this story. Starting work. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    try:
                        importer.create_comment(story["id"], comment)
                    except:
                        pass
                else:
                    print(f"❌ Failed to assign US#{ref}")
            except Exception as e:
                print(f"❌ US#{ref} - Error: {e}")

        print()
        print(f"📊 Assigned {assigned_count} stories to Developer H")

        if assigned_count > 0:
            print()
            print("📋 Next steps:")
            print("   Review assigned stories and start working on them")
            print("   Use: python3 scripts/get_story_details.py <ref>")
    else:
        print("✅ No unassigned actionable stories found")
        print()
        print("💡 All actionable stories are assigned or completed")
        print("   Check back later for new stories, or create new ones in Taiga")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
