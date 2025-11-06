#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find ALL UI-related stories in Taiga, including Done ones"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import re

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def find_all_ui_stories(importer, project_id):
    """Find all UI-related stories by searching comprehensively."""
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"

    # Get ALL stories (no status filter)
    params = {"project": project_id}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to fetch stories: {response.status_code}")
        return []

    all_stories = response.json()
    print(f"📊 Total stories in project: {len(all_stories)}\n")

    # Comprehensive search criteria
    ui_keywords = [
        # SPEC numbers
        r"spec[-\s]?(0{0,2}5|102|103|113|114|115|116|121|122|123|124)",
        # UI-related terms
        "admin dashboard",
        "admin ui",
        "admin console",
        "admin panel",
        "customer ui",
        "customer frontend",
        "customer app",
        "frontend",
        "next.js",
        "nextjs",
        "react",
        "spa",
        "single page",
        "vercel",
        "turborepo",
        "frontend-nextjs",
        "frontend-shared",
        "jinja2",
        "template",
        "templating",
        # Story references
        "us-98",
        "us-99",
        "us-100",
        "us-101",
        "us-102",
        "us-89",
        # UI components
        "component library",
        "ui components",
        "shared library",
        "profile page",
        "settings page",
        "auth integration",
        "realtime",
        "websocket",
        "sse",
    ]

    matching_stories = []

    for story in all_stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = story.get("tags", [])

        # Get tag names
        tag_names = []
        for tag in tags:
            if isinstance(tag, str):
                tag_names.append(tag.lower())
            elif isinstance(tag, dict):
                tag_names.append(tag.get("name", "").lower())

        # Combine all text
        combined = f'{subject} {description} {" ".join(tag_names)}'

        # Check for matches
        matched_keywords = []
        for keyword in ui_keywords:
            if isinstance(keyword, str):
                if keyword.lower() in combined:
                    matched_keywords.append(keyword)
            else:  # regex
                if re.search(keyword, combined, re.IGNORECASE):
                    matched_keywords.append(keyword.pattern if hasattr(keyword, "pattern") else str(keyword))

        if matched_keywords:
            story["_matched_keywords"] = matched_keywords
            matching_stories.append(story)

    return matching_stories


def categorize_story(story):
    """Categorize story by which SPEC it relates to."""
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

    spec_map = {
        "005": ["spec-005", "spec-5", "admin dashboard", "admin ui", "us-98", "us-99", "us-100", "us-101", "us-102"],
        "102": ["spec-102", "spec-102", "frontend migration preparation"],
        "103": ["spec-103", "spec-103", "next.js 15 bootstrap"],
        "113": ["spec-113", "spec-113", "profile", "settings page"],
        "114": ["spec-114", "spec-114", "auth integration", "jwt", "nextauth"],
        "115": ["spec-115", "spec-115", "realtime", "websocket", "sse"],
        "116": ["spec-116", "spec-116", "internal frontend migration"],
        "121": ["spec-121", "spec-121", "frontend shared library", "ui components"],
        "122": ["spec-122", "spec-122", "customer frontend rollout", "vercel", "us-89"],
        "123": ["spec-123", "spec-123", "admin frontend rollout"],
        "124": ["spec-124", "spec-124", "turborepo", "unified workspace"],
    }

    matched_specs = []
    for spec_num, keywords in spec_map.items():
        for keyword in keywords:
            if keyword.lower() in combined:
                matched_specs.append(spec_num)
                break

    return matched_specs if matched_specs else ["unknown"]


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print(f'✅ Connected to project: {project["name"]}\n')
    print("🔍 Searching for ALL UI-related stories (including Done)...\n")

    stories = find_all_ui_stories(importer, project["id"])

    print(f"✅ Found {len(stories)} UI-related stories:\n")
    print("=" * 100)

    # Group by SPEC
    stories_by_spec = {}
    for story in stories:
        specs = categorize_story(story)
        for spec in specs:
            if spec not in stories_by_spec:
                stories_by_spec[spec] = []
            stories_by_spec[spec].append(story)

    # Print by SPEC
    for spec_num in sorted(stories_by_spec.keys()):
        spec_stories = stories_by_spec[spec_num]
        print(f"\n📋 SPEC-{spec_num}: {len(spec_stories)} story/stories")
        print("-" * 100)

        for story in spec_stories:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            status_id = story.get("status")

            tags = story.get("tags", [])
            tag_names = []
            for tag in tags:
                if isinstance(tag, str):
                    tag_names.append(tag)
                elif isinstance(tag, dict):
                    tag_names.append(tag.get("name", ""))

            description = story.get("description", "")
            has_update = "ARCHITECTURE UPDATE (2025-11-02)" in description
            has_deprecation = "SPEC DEPRECATED (2025-11-02)" in description

            print(f"US#{ref}: {subject}")
            print(f"   Status: {status} (ID: {status_id})")
            print(f'   Tags: {", ".join(tag_names) if tag_names else "None"}')
            print(f'   Matched: {", ".join(story.get("_matched_keywords", []))[:3]}...')
            print(f'   Updated: {"✅ Yes" if (has_update or has_deprecation) else "❌ No"}')
            print()

    print("=" * 100)
    print(f"\n📊 Summary:")
    print(f"   Total UI-related stories: {len(stories)}")
    print(f"   Stories by SPEC:")
    for spec_num, spec_stories in sorted(stories_by_spec.items()):
        updated = sum(
            1
            for s in spec_stories
            if "ARCHITECTURE UPDATE (2025-11-02)" in s.get("description", "")
            or "SPEC DEPRECATED (2025-11-02)" in s.get("description", "")
        )
        print(f"      SPEC-{spec_num}: {len(spec_stories)} stories ({updated} updated)")

    # Count by status
    status_counts = {}
    for story in stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\n   Stories by Status:")
    for status, count in sorted(status_counts.items()):
        print(f"      {status}: {count} stories")


if __name__ == "__main__":
    main()
