#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find UI-related stories in Taiga by searching subject and description"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def find_stories_by_keywords(importer, project_id):
    """Find stories by searching keywords in subject and description."""
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"
    params = {"project": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to fetch stories: {response.status_code}")
        return []

    all_stories = response.json()

    # Keywords to search for
    keywords = [
        "spec-005",
        "spec-102",
        "spec-103",
        "spec-113",
        "spec-114",
        "spec-115",
        "spec-116",
        "spec-121",
        "spec-122",
        "spec-123",
        "spec-124",
        "SPEC-005",
        "SPEC-102",
        "SPEC-103",
        "SPEC-113",
        "SPEC-114",
        "SPEC-115",
        "SPEC-116",
        "SPEC-121",
        "SPEC-122",
        "SPEC-123",
        "SPEC-124",
        "admin dashboard",
        "admin ui",
        "customer ui",
        "frontend",
        "next.js",
        "nextjs",
        "US-98",
        "US-99",
        "US-100",
        "US-101",
        "US-102",  # SPEC-005 stories
        "US-89",  # SPEC-122 story
    ]

    matching_stories = []

    for story in all_stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = story.get("tags", [])

        # Check tags
        tag_names = []
        for tag in tags:
            if isinstance(tag, str):
                tag_names.append(tag.lower())
            elif isinstance(tag, dict):
                tag_names.append(tag.get("name", "").lower())

        combined = f'{subject} {description} {" ".join(tag_names)}'

        # Check if any keyword matches
        for keyword in keywords:
            if keyword.lower() in combined:
                story["_matched_keyword"] = keyword
                matching_stories.append(story)
                break

    return matching_stories


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print(f'✅ Connected to project: {project["name"]}\n')
    print("🔍 Searching for UI-related stories...\n")

    stories = find_stories_by_keywords(importer, project["id"])

    print(f"Found {len(stories)} matching stories:\n")

    for story in stories:
        ref = story.get("ref")
        subject = story.get("subject", "N/A")
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        tags = story.get("tags", [])

        tag_names = []
        for tag in tags:
            if isinstance(tag, str):
                tag_names.append(tag)
            elif isinstance(tag, dict):
                tag_names.append(tag.get("name", ""))

        print(f"US#{ref}: {subject}")
        print(f"   Status: {status}")
        print(f'   Tags: {", ".join(tag_names) if tag_names else "None"}')
        print(f'   Matched: {story.get("_matched_keyword", "Unknown")}')
        print()


if __name__ == "__main__":
    main()
