#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Assign unassigned Taiga stories to Developer H and list all Developer H tasks"""

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


def prioritize_stories(stories, statuses):
    """Prioritize stories by status and priority"""
    # Status priority: New/Ready > In Progress > Done (exclude done)
    status_priority = {"New": 1, "Ready": 1, "In Progress": 2, "Review/QA": 3, "Done": 99, "Archived": 99}

    def get_priority(story):
        status_name = story.get("status_extra_info", {}).get("name", "Unknown")
        status_prio = status_priority.get(status_name, 50)

        # Priority: High > Normal > Low
        priority_order = {3: 1, 2: 2, 1: 3}  # High=3, Normal=2, Low=1
        priority_prio = priority_order.get(story.get("priority", 2), 2)

        # Reference number (lower = older, potentially more pressing)
        ref = story.get("ref", 9999)

        return (status_prio, priority_prio, ref)

    # Filter out done stories
    active_stories = [s for s in stories if s.get("status_extra_info", {}).get("name", "") not in ["Done", "Archived"]]

    return sorted(active_stories, key=get_priority)


def main():
    print("=" * 70)
    print("Taiga Task Assignment - Developer H")
    print("=" * 70)
    print()

    # Initialize importer
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # Get project
    project = importer.get_project("ninaivalaigal")
    if not project:
        print('❌ Project "ninaivalaigal" not found')
        return

    print(f"✅ Found project: {project['name']} (ID: {project['id']})")
    print()

    # Get Developer H user
    developer_h = get_user_by_username(importer, developer_h_username)
    if not developer_h:
        print(f"⚠️  Developer H user '{developer_h_username}' not found")
        print("   Creating user...")
        # Try to create user (this might require admin access)
        # For now, we'll use admin as fallback
        developer_h = get_user_by_username(importer, "admin")
        if developer_h:
            print(f"   Using 'admin' user instead (ID: {developer_h['id']})")
        else:
            print("   ❌ Could not find or create Developer H user")
            return
    else:
        print(f"✅ Found Developer H: {developer_h['full_name']} (ID: {developer_h['id']})")
        print()

    developer_h_id = developer_h["id"]

    # Get all stories
    print("📋 Fetching all user stories...")
    all_stories = get_all_user_stories(importer, project["id"])
    print(f"   Found {len(all_stories)} total stories")

    # Get status definitions
    statuses = get_project_statuses(importer, project["id"])

    # Categorize stories
    unassigned_stories = [s for s in all_stories if not s.get("assigned_to")]
    assigned_to_h_stories = [s for s in all_stories if s.get("assigned_to") == developer_h_id]

    print(f"   Unassigned: {len(unassigned_stories)}")
    print(f"   Assigned to Developer H: {len(assigned_to_h_stories)}")
    print()

    # Show raw unassigned stories first (for debugging)
    if unassigned_stories:
        print("=" * 70)
        print("📌 ALL UNASSIGNED STORIES (raw)")
        print("=" * 70)
        for i, story in enumerate(unassigned_stories[:10], 1):
            status_info = story.get("status_extra_info", {})
            status_name = status_info.get("name", "Unknown")
            status_id = story.get("status", "N/A")
            priority_name = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            print(f"{i:2d}. US#{ref} [Status ID: {status_id}, Name: {status_name}] [{priority_name}] - {subject}")
        print()

    # Prioritize unassigned stories
    prioritized_unassigned = prioritize_stories(unassigned_stories, statuses)

    # Show unassigned stories
    if prioritized_unassigned:
        print("=" * 70)
        print("📌 UNASSIGNED STORIES (prioritized)")
        print("=" * 70)
        for i, story in enumerate(prioritized_unassigned[:20], 1):  # Show top 20
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")
            priority_name = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            print(f"{i:2d}. US#{ref} [{status_name}] [{priority_name}] - {subject}")
        print()

        # Assign top pressing stories to Developer H
        print("=" * 70)
        print("🔨 ASSIGNING TOP PRESSING STORIES TO DEVELOPER H")
        print("=" * 70)

        assigned_count = 0
        max_assign = min(5, len(prioritized_unassigned))  # Assign top 5 most pressing

        for story in prioritized_unassigned[:max_assign]:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")

            try:
                result = importer.assign_story(
                    story_id=story["id"], assigned_to_id=developer_h_id, version=story["version"]
                )
                if result:
                    print(f"✅ US#{ref} - {subject} [{status_name}]")
                    assigned_count += 1
                else:
                    print(f"❌ US#{ref} - Failed to assign")
            except Exception as e:
                print(f"❌ US#{ref} - Error: {e}")

        print(f"\n📊 Assigned {assigned_count} stories to Developer H")
        print()
    else:
        print("✅ No unassigned stories found")
        print()

    # Show Developer H's assigned stories
    if assigned_to_h_stories:
        prioritized_assigned = prioritize_stories(assigned_to_h_stories, statuses)

        print("=" * 70)
        print("👤 DEVELOPER H'S ASSIGNED STORIES (prioritized)")
        print("=" * 70)
        for i, story in enumerate(prioritized_assigned, 1):
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")
            priority_name = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            print(f"{i:2d}. US#{ref} [{status_name}] [{priority_name}] - {subject}")
        print()

        # Update status to "In Progress" for top stories if they're "Ready" or "New"
        print("=" * 70)
        print("🚀 STARTING WORK ON TOP PRESSING STORIES")
        print("=" * 70)

        # Find "Ready" or "New" status stories
        in_progress_status_id = None

        for status_id, status in statuses.items():
            status_name = status.get("name", "")
            if status_name == "In Progress":
                in_progress_status_id = status_id

        started_count = 0
        for story in prioritized_assigned[:3]:  # Start top 3
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")

            if status_name in ["Ready", "New"] and in_progress_status_id:
                try:
                    result = importer.update_story_status(
                        story_id=story["id"], status_id=in_progress_status_id, version=story["version"]
                    )
                    if result:
                        print(f"✅ Started US#{ref} - {subject}")
                        started_count += 1

                        # Add a comment
                        comment = (
                            f"Developer H starting work on this story. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        importer.create_comment(story["id"], comment)
                except Exception as e:
                    print(f"❌ US#{ref} - Failed to start: {e}")
            elif status_name == "In Progress":
                print(f"⏳ US#{ref} - Already in progress")

        print(f"\n📊 Started work on {started_count} stories")
        print()

    print("=" * 70)
    print("✅ Task assignment and work initiation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
