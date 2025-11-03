#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Find all unassigned active stories in Taiga"""

import json

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        return None, None
    return auth.json()["auth_token"], auth.json()


def get_project_id(auth_token):
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["id"]
    return None


def get_all_stories(auth_token, project_id):
    """Get all user stories with pagination"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    all_stories = []

    # Use large page size to get all stories
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    params = {"project": project_id, "page_size": 1000}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        # Handle both list and paginated response
        if isinstance(result, list):
            all_stories.extend(result)
        elif isinstance(result, dict):
            # Paginated response
            all_stories.extend(result.get("results", []))
            # If there are more pages, fetch them
            if result.get("next"):
                page = 2
                while True:
                    next_url = f"{url}&page={page}"
                    next_response = requests.get(next_url, headers=headers)
                    if next_response.status_code == 200:
                        next_result = next_response.json()
                        if isinstance(next_result, dict):
                            all_stories.extend(next_result.get("results", []))
                            if not next_result.get("next"):
                                break
                        else:
                            break
                        page += 1
                    else:
                        break
        else:
            all_stories = result if isinstance(result, list) else []

    return all_stories


def main():
    print("=" * 80)
    print("Finding All Unassigned Active Stories")
    print("=" * 80)
    print()

    auth_token, user_data = authenticate()
    if not auth_token:
        print("Failed to authenticate")
        return

    project_id = get_project_id(auth_token)
    if not project_id:
        print("Failed to get project ID")
        return

    print(f"Fetching all stories from project {project_id}...")
    all_stories = get_all_stories(auth_token, project_id)
    print(f"✓ Found {len(all_stories)} total stories")
    print()

    # Filter for unassigned, active stories
    done_statuses = ["done", "closed", "archived", "cancelled"]
    unassigned_active = []

    for story in all_stories:
        assigned = story.get("assigned_to")
        status_name = story.get("status_extra_info", {}).get("name", "").lower()

        if not assigned and status_name not in done_statuses:
            unassigned_active.append(story)

    print(f"Found {len(unassigned_active)} unassigned active stories:")
    print("=" * 80)
    print()

    if unassigned_active:
        # Sort by ref number
        unassigned_active.sort(key=lambda x: x.get("ref", 0))

        # Show first 20
        for story in unassigned_active[:20]:
            ref = story.get("ref")
            subject = story.get("subject", "")[:70]
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
            tag_str = ", ".join(tags[:3]) if tags else "no tags"

            print(f"Ref #{ref}: {subject}")
            print(f"  Status: {status} | Tags: {tag_str}")
            print()

        if len(unassigned_active) > 20:
            print(f"... and {len(unassigned_active) - 20} more unassigned active stories")
            print()

        # Prioritize stories
        priority_keywords = ["p0", "critical", "security", "blocker", "urgent", "high-priority"]
        high_priority = []

        for story in unassigned_active:
            subject = story.get("subject", "").lower()
            description = story.get("description", "").lower()
            tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
            text = f"{subject} {description} {' '.join(tags)}"

            if any(kw in text for kw in priority_keywords):
                high_priority.append(story)

        if high_priority:
            print()
            print("=" * 80)
            print(f"HIGH PRIORITY UNASSIGNED STORIES ({len(high_priority)}):")
            print("=" * 80)
            print()

            for story in high_priority[:10]:
                ref = story.get("ref")
                subject = story.get("subject", "")[:70]
                status = story.get("status_extra_info", {}).get("name", "Unknown")
                print(f"Ref #{ref}: {subject}")
                print(f"  Status: {status}")
                print()
    else:
        print("No unassigned active stories found.")
        print()
        print("All unassigned stories are in Done/Archived status.")


if __name__ == "__main__":
    main()
