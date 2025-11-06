#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Get ALL stories and check for UI-related ones"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def get_all_stories(importer, project_id):
    """Get ALL stories regardless of status."""
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"

    all_stories = []
    page = 1
    page_size = 100

    while True:
        params = {"project": project_id, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            break

        stories = response.json()
        if not stories:
            break

        all_stories.extend(stories)

        if len(stories) < page_size:
            break

        page += 1

    return all_stories


def check_story_needs_update(story):
    """Check if story needs update based on content."""
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()
    tags = story.get("tags", [])

    tag_names = []
    for tag in tags:
        if isinstance(tag, str):
            tag_names.append(tag.lower())
        elif isinstance(tag, dict):
            tag_names.append(tag.get("name", "").lower())

    combined = f'{subject} {description} {" ".join(tag_names)}'

    # Check if already updated
    if "ARCHITECTURE UPDATE (2025-11-02)" in story.get("description", ""):
        return False, "already_updated"

    if "SPEC DEPRECATED (2025-11-02)" in story.get("description", ""):
        return False, "already_deprecated"

    # UI-related keywords
    ui_keywords = [
        "next.js",
        "nextjs",
        "react",
        "frontend",
        "spa",
        "vercel",
        "admin ui",
        "admin dashboard",
        "customer ui",
        "customer frontend",
        "frontend-nextjs",
        "frontend-shared",
        "turborepo",
        "jinja2",
        "template",
        "templating",
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
        "us-98",
        "us-99",
        "us-100",
        "us-101",
        "us-102",
        "us-89",
        "profile page",
        "settings page",
        "auth integration",
        "realtime",
        "websocket",
        "sse",
    ]

    for keyword in ui_keywords:
        if keyword in combined:
            return True, keyword

    return False, None


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print(f'✅ Connected to project: {project["name"]}\n')
    print("🔍 Fetching ALL stories...\n")

    all_stories = get_all_stories(importer, project["id"])
    print(f"📊 Total stories: {len(all_stories)}\n")

    # Check each story
    ui_stories = []
    needs_update = []

    for story in all_stories:
        needs_upd, reason = check_story_needs_update(story)
        if needs_upd or reason == "already_updated" or reason == "already_deprecated":
            story["_needs_update"] = needs_upd
            story["_reason"] = reason
            ui_stories.append(story)
            if needs_upd:
                needs_update.append(story)

    print(f"✅ Found {len(ui_stories)} UI-related stories ({len(needs_update)} need update)\n")
    print("=" * 100)

    # Group by status
    by_status = {}
    for story in ui_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    for status in sorted(by_status.keys()):
        stories = by_status[status]
        print(f"\n📋 {status}: {len(stories)} story/stories")
        print("-" * 100)

        for story in stories:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status_id = story.get("status")
            reason = story.get("_reason", "unknown")
            needs_upd = story.get("_needs_update", False)

            tags = story.get("tags", [])
            tag_names = []
            for tag in tags:
                if isinstance(tag, str):
                    tag_names.append(tag)
                elif isinstance(tag, dict):
                    tag_names.append(tag.get("name", ""))

            print(f"US#{ref}: {subject}")
            print(f"   Status ID: {status_id}")
            print(f'   Tags: {", ".join(tag_names) if tag_names else "None"}')
            if needs_upd:
                print(f"   Needs update: ✅ Yes (matched: {reason})")
            else:
                print(
                    f'   Status: {"✅ Already updated" if reason in ["already_updated", "already_deprecated"] else "❌ Unknown"}'
                )
            print()

    print("=" * 100)
    print(f"\n📊 Summary:")
    print(f"   Total stories: {len(all_stories)}")
    print(f"   UI-related stories: {len(ui_stories)}")
    print(f"   Need update: {len(needs_update)}")
    print(f"   Already updated: {len(ui_stories) - len(needs_update)}")

    # List stories that need update
    if needs_update:
        print(f"\n📝 Stories needing update:")
        for story in sorted(needs_update, key=lambda x: x.get("ref", 0)):
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            print(f"   US#{ref}: {subject} ({status})")


if __name__ == "__main__":
    main()
