#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find critical stories in Taiga that need work"""

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

    # Look for critical stories by ref number or keywords
    critical_refs = [20, 21, 45, 117]
    critical_keywords = ["signup", "login", "auth", "bcrypt", "jwt", "orm", "multi-tenant", "security", "guardrails"]

    print("=" * 70)
    print("Searching for Critical Stories")
    print("=" * 70)
    print()

    found_stories = []

    # Search by ref
    for ref in critical_refs:
        story = importer.get_user_story("ninaivalaigal", ref)
        if story:
            found_stories.append(story)

    # Search by keywords
    for story in all_stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        combined = f"{subject} {description}"

        if any(kw in combined for kw in critical_keywords):
            if story not in found_stories:
                found_stories.append(story)

    if found_stories:
        print(f"Found {len(found_stories)} critical stories:\n")
        for story in found_stories:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
            priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")

            print(f"US#{ref}: {subject}")
            print(f"  Status: {status}")
            print(f"  Assigned to: {assigned_to}")
            print(f"  Priority: {priority}")
            print()
    else:
        print("No critical stories found with those refs or keywords")
        print()
        print("All stories in project:")
        for story in sorted(all_stories, key=lambda x: x.get("ref", 0))[:20]:
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")[:60]
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            assigned_to = story.get("assigned_to_extra_info", {}).get("full_name", "Unassigned")
            print(f"  US#{ref:3d} [{status:15s}] [{assigned_to:20s}] - {subject}")


if __name__ == "__main__":
    main()
