#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Analyze UI stories in Taiga to identify customer vs admin/internal stories"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
importer._get_auth_token()

# Get project
project = importer.get_project("ninaivalaigal")
if not project:
    print("❌ Project not found")
    sys.exit(1)

print("🔍 Searching for UI-related stories...")
print("=" * 70)

# Search for stories
headers = {"Authorization": f"Bearer {importer._auth_token}"}
url = f"{taiga_url}/api/v1/userstories"
params = {"project": project["id"]}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    stories = response.json()
    ui_stories = []

    keywords = ["ui", "frontend", "admin", "customer", "dashboard", "console", "interface", "web", "page"]

    for story in stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()

        if any(kw in subject or kw in description for kw in keywords):
            ui_stories.append(
                {
                    "ref": story.get("ref"),
                    "subject": story.get("subject"),
                    "status": story.get("status_extra_info", {}).get("name", "Unknown"),
                    "tags": story.get("tags", []),
                    "description": story.get("description", "")[:200],
                }
            )

    # Sort by ref
    ui_stories.sort(key=lambda x: x["ref"] or 0)

    print(f"\n📊 Found {len(ui_stories)} UI-related stories:\n")

    customer_stories = []
    admin_stories = []
    other_ui = []

    for story in ui_stories:
        subject_lower = story["subject"].lower()
        desc_lower = story["description"].lower()
        tags_list = story.get("tags", [])
        tags_lower = " ".join(
            [
                str(t).lower() if isinstance(t, str) else str(t.get("name", "")).lower() if isinstance(t, dict) else ""
                for t in tags_list
            ]
        )

        combined = f"{subject_lower} {desc_lower} {tags_lower}"

        if "customer" in combined or "public" in combined or "user-facing" in combined:
            customer_stories.append(story)
        elif "admin" in combined or "internal" in combined or "console" in combined or "ops" in combined:
            admin_stories.append(story)
        else:
            other_ui.append(story)

    print("🎯 Customer-Facing UI Stories:")
    print("-" * 70)
    for s in customer_stories:
        print(f'  US#{s["ref"]}: {s["subject"]} ({s["status"]})')
        if s["tags"]:
            print(f'    Tags: {", ".join(s["tags"])}')

    print("\n🔧 Admin/Internal UI Stories:")
    print("-" * 70)
    for s in admin_stories:
        print(f'  US#{s["ref"]}: {s["subject"]} ({s["status"]})')
        if s["tags"]:
            print(f'    Tags: {", ".join(s["tags"])}')

    print("\n📱 Other UI Stories (first 15):")
    print("-" * 70)
    for s in other_ui[:15]:
        print(f'  US#{s["ref"]}: {s["subject"]} ({s["status"]})')

    if len(other_ui) > 15:
        print(f"  ... and {len(other_ui) - 15} more")

    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  Customer-facing: {len(customer_stories)} stories")
    print(f"  Admin/Internal: {len(admin_stories)} stories")
    print(f"  Other UI: {len(other_ui)} stories")
    print(f"  Total: {len(ui_stories)} stories")

    # Save to file for analysis
    with open("/tmp/ui_stories_analysis.txt", "w") as f:
        f.write("CUSTOMER-FACING UI STORIES\n")
        f.write("=" * 70 + "\n")
        for s in customer_stories:
            f.write(f'US#{s["ref"]}: {s["subject"]} ({s["status"]})\n')
            f.write(f'  Tags: {", ".join(s["tags"])}\n')
            f.write(f'  Description: {s["description"]}\n\n')

        f.write("\n\nADMIN/INTERNAL UI STORIES\n")
        f.write("=" * 70 + "\n")
        for s in admin_stories:
            f.write(f'US#{s["ref"]}: {s["subject"]} ({s["status"]})\n')
            f.write(f'  Tags: {", ".join(s["tags"])}\n')
            f.write(f'  Description: {s["description"]}\n\n')

    print("\n📄 Detailed analysis saved to: /tmp/ui_stories_analysis.txt")
else:
    print(f"❌ Failed to fetch stories: {response.status_code}")
