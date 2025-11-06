#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update ALL UI-related stories in Taiga with architecture notes.
Handles 85+ stories across all statuses (Done, In Progress, New, etc.)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import re

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

# Deprecated SPECs
DEPRECATED_SPECS = {
    "102": "SPEC-005, SPEC-146",
    "103": "SPEC-005, SPEC-146",
    "116": "SPEC-005, SPEC-146",
    "121": "SPEC-005, SPEC-146",
    "122": "SPEC-146",
    "123": "SPEC-005",
    "124": "SPEC-016",
}

ARCHITECTURE_NOTE = """
---

⚠️ **ARCHITECTURE UPDATE (2025-11-02):**

This story has been updated to reflect the current architecture: **FastAPI + Jinja2 templates**.

**Current Stack:**
- **Primary:** FastAPI + Jinja2 templates (server-rendered)
- **Styling:** TailwindCSS
- **Interactivity:** Alpine.js or HTMX
- **Optional:** React micro-widgets (Vite-built) for complex visualizations only

**References:**
- Customer UI: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
- Unified Plan: `docs/SPEC_TAIGA_UNIFORMITY_PLAN.md`

**Note:** Next.js/React examples are for historical reference only.
"""

DEPRECATION_NOTE_TEMPLATE = """
---

🚫 **SPEC DEPRECATED (2025-11-02):**

This story is linked to SPEC-{spec_num}, which is deprecated.

**Replacement SPECs:** {replacement}

**Current Direction:** FastAPI + Jinja2 templates for all UI (customer and admin).

**See:** `docs/SPEC_TAIGA_UPDATE_SUMMARY.md` for migration details.
"""


def get_spec_number(story):
    """Extract SPEC number from story."""
    subject = story.get("subject", "")
    description = story.get("description", "")
    tags = story.get("tags", [])

    combined = f"{subject} {description}"

    # Check tags
    for tag in tags:
        tag_name = tag if isinstance(tag, str) else (tag.get("name", "") if isinstance(tag, dict) else str(tag))
        match = re.search(r"spec[-\s]?(\d{2,3})", tag_name, re.IGNORECASE)
        if match:
            return match.group(1).zfill(3)

    # Check subject/description
    match = re.search(r"spec[-\s]?(\d{2,3})", combined, re.IGNORECASE)
    if match:
        return match.group(1).zfill(3)

    return None


def categorize_story(story):
    """Determine if story is deprecated and get replacement."""
    spec_num = get_spec_number(story)

    if spec_num and spec_num in DEPRECATED_SPECS:
        return {"deprecated": True, "spec_num": spec_num, "replacement": DEPRECATED_SPECS[spec_num]}

    # Check for deprecated keywords
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()
    combined = f"{subject} {description}"

    deprecated_keywords = [
        "spec-102",
        "spec-103",
        "spec-116",
        "spec-121",
        "spec-122",
        "spec-123",
        "spec-124",
        "next.js 15 bootstrap",
        "frontend migration preparation",
        "frontend shared library",
        "customer frontend rollout",
        "admin frontend rollout",
        "turborepo",
        "unified workspace",
    ]

    for keyword in deprecated_keywords:
        if keyword in combined:
            # Try to extract spec number
            match = re.search(r"spec[-\s]?(\d{2,3})", keyword, re.IGNORECASE)
            if match:
                spec_num = match.group(1).zfill(3)
                if spec_num in DEPRECATED_SPECS:
                    return {"deprecated": True, "spec_num": spec_num, "replacement": DEPRECATED_SPECS[spec_num]}

    return {"deprecated": False, "spec_num": spec_num, "replacement": None}


def update_story(importer, story, dry_run=False):
    """Update a story with appropriate note."""
    current_desc = story.get("description", "")

    # Check if already updated
    if "ARCHITECTURE UPDATE (2025-11-02)" in current_desc:
        return False, "already_updated"

    if "SPEC DEPRECATED (2025-11-02)" in current_desc:
        return False, "already_deprecated"

    # Categorize
    category = categorize_story(story)

    # Prepare update
    if category["deprecated"]:
        note = DEPRECATION_NOTE_TEMPLATE.format(spec_num=category["spec_num"], replacement=category["replacement"])
        note_type = "deprecation"
    else:
        note = ARCHITECTURE_NOTE
        note_type = "architecture"

    new_desc = current_desc + note

    # Update tags
    tags = story.get("tags", [])
    tag_names = []
    for tag in tags:
        if isinstance(tag, str):
            tag_names.append(tag)
        elif isinstance(tag, dict):
            tag_names.append(tag.get("name", ""))
        else:
            tag_names.append(str(tag))

    # Add required tags
    if category["deprecated"]:
        required_tags = ["deprecated", "fastapi", "jinja2"]
        if category["spec_num"]:
            required_tags.insert(0, f'spec-{category["spec_num"]}')
    else:
        required_tags = ["fastapi", "jinja2", "templates"]
        if category["spec_num"]:
            required_tags.insert(0, f'spec-{category["spec_num"]}')

    for tag in required_tags:
        if tag not in [t.lower() for t in tag_names]:
            tag_names.append(tag)

    # Remove Next.js tags
    tag_names = [t for t in tag_names if "nextjs" not in t.lower() and "next.js" not in t.lower()]

    if dry_run:
        return True, note_type

    updates = {"description": new_desc, "tags": tag_names}

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )
        return result is not None, note_type
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, "error"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Update all UI-related stories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--limit", type=int, help="Limit number of stories to update (for testing)")
    args = parser.parse_args()

    print("🔄 Updating ALL UI-related stories...\n")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    print("=" * 100)

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    # Get all stories
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"

    all_stories = []
    page = 1
    page_size = 100

    while True:
        params = {"project": project["id"], "page": page, "page_size": page_size}
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

    print(f"📊 Total stories in project: {len(all_stories)}\n")

    # Find UI-related stories
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

    ui_stories = []
    for story in all_stories:
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

        if any(kw in combined for kw in ui_keywords):
            # Check if needs update
            if "ARCHITECTURE UPDATE (2025-11-02)" not in story.get(
                "description", ""
            ) and "SPEC DEPRECATED (2025-11-02)" not in story.get("description", ""):
                ui_stories.append(story)

    print(f"✅ Found {len(ui_stories)} UI-related stories needing update\n")

    if args.limit:
        ui_stories = ui_stories[: args.limit]
        print(f"⚠️  Limited to first {args.limit} stories for testing\n")

    # Group by status
    by_status = {}
    for story in ui_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    # Update stories
    updated_count = 0
    skipped_count = 0
    error_count = 0
    deprecation_count = 0
    architecture_count = 0

    for status in sorted(by_status.keys()):
        stories = by_status[status]
        print(f"\n📋 {status}: {len(stories)} story/stories")
        print("-" * 100)

        for story in stories:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")

            success, note_type = update_story(importer, story, dry_run=args.dry_run)

            if success:
                if note_type == "deprecation":
                    print(f"US#{ref}: ✅ Updated with deprecation notice - {subject[:60]}...")
                    deprecation_count += 1
                elif note_type == "architecture":
                    print(f"US#{ref}: ✅ Updated with architecture note - {subject[:60]}...")
                    architecture_count += 1
                else:
                    print(f"US#{ref}: ✅ Updated - {subject[:60]}...")
                updated_count += 1
            elif note_type in ["already_updated", "already_deprecated"]:
                print(f"US#{ref}: ⏭️  Already updated - {subject[:60]}...")
                skipped_count += 1
            else:
                print(f"US#{ref}: ❌ Failed - {subject[:60]}...")
                error_count += 1

    print("\n" + "=" * 100)
    print(f"📊 Summary:")
    print(f"   ✅ Updated: {updated_count} stories")
    print(f"      - Architecture notes: {architecture_count}")
    print(f"      - Deprecation notices: {deprecation_count}")
    print(f"   ⏭️  Already updated: {skipped_count} stories")
    print(f"   ❌ Errors: {error_count} stories")
    print(f"   📋 Total processed: {len(ui_stories)} stories")
    print("=" * 100)

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to apply updates")


if __name__ == "__main__":
    main()
