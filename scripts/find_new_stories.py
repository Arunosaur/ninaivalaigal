#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find new stories in Taiga and assign to Developer H"""

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


def is_recent_story(story, days=7):
    """Check if story was created or modified recently"""
    created_date = story.get("created_date")
    modified_date = story.get("modified_date")

    if not created_date:
        return False

    try:
        # Parse ISO format date
        if "T" in created_date:
            created = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
        else:
            return False

        # Check if created in last N days
        cutoff = datetime.now(created.tzinfo) - timedelta(days=days)
        return created >= cutoff
    except:
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
    print(f"✅ Developer H: {developer_h.get('full_name', developer_h_username)} (ID: {developer_h_id})")
    print()

    # Get all stories
    all_stories = get_all_user_stories(importer, project["id"])

    # Find "New" status stories
    new_stories = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        if status_name == "New":
            new_stories.append(story)

    # Also find recently created stories (last 7 days) that might be new
    recent_stories = [s for s in all_stories if is_recent_story(s, days=7)]

    print("=" * 80)
    print("NEW STORIES IN TAIGA")
    print("=" * 80)
    print()

    # Show "New" status stories
    if new_stories:
        print(f"📌 Stories with 'New' Status ({len(new_stories)}):")
        print("-" * 80)

        for story in sorted(new_stories, key=lambda x: x.get("ref", 9999)):
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"

            if not story.get("assigned_to"):
                print(f"  ⭐ US#{ref:3d} [{priority:6s}] [{assigned_to:20s}] Created: {created}")
                print(f"     {subject}")
            else:
                print(f"     US#{ref:3d} [{priority:6s}] [{assigned_to:20s}] Created: {created}")
                print(f"     {subject}")
            print()
    else:
        print("📌 No stories with 'New' status found")
        print()

    # Show recently created stories
    if recent_stories:
        print(f"🆕 Recently Created Stories (last 7 days, {len(recent_stories)}):")
        print("-" * 80)

        for story in sorted(recent_stories, key=lambda x: x.get("created_date", ""), reverse=True)[:10]:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
            created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"

            if status not in ["Done", "Archived"]:
                marker = "⭐" if not story.get("assigned_to") else "  "
                print(f"{marker} US#{ref:3d} [{status:15s}] [{assigned_to:20s}] Created: {created}")
                print(f"     {subject[:70]}")
                print()

    # Find unassigned "New" stories
    unassigned_new = [s for s in new_stories if not s.get("assigned_to")]

    if unassigned_new:
        print("=" * 80)
        print(f"ASSIGNING {len(unassigned_new)} UNASSIGNED 'NEW' STORIES TO DEVELOPER H")
        print("=" * 80)
        print()

        assigned_count = 0
        for story in sorted(unassigned_new, key=lambda x: x.get("ref", 9999)):
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")

            try:
                result = importer.assign_story(
                    story_id=story["id"], assigned_to_id=developer_h_id, version=story["version"]
                )
                if result:
                    print(f"✅ Assigned US#{ref} - {subject}")
                    assigned_count += 1

                    # Add comment
                    comment = f"Developer H assigned to this new story. Starting work. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    try:
                        importer.create_comment(story["id"], comment)
                    except:
                        pass
                else:
                    print(f"❌ Failed to assign US#{ref}")
            except Exception as e:
                print(f"❌ US#{ref} - Error: {e}")

        print()
        print(f"📊 Assigned {assigned_count} new stories to Developer H")
        print()

        if assigned_count > 0:
            print("📋 Next steps:")
            print("   1. Review assigned stories: python3 scripts/get_story_details.py <ref>")
            print("   2. Start working on the highest priority story")
            print()
    else:
        print("✅ No unassigned 'New' stories found")
        print()
        print("💡 All 'New' stories are already assigned or there are none")

    print("=" * 80)


if __name__ == "__main__":
    main()
