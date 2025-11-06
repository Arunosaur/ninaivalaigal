#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update Taiga stories that mention Next.js/React to reflect FastAPI templating direction"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import re

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

ARCHITECTURE_UPDATE_NOTE = """
---

⚠️ **ARCHITECTURE UPDATE (2025-11-02):**

This story originally described a Next.js/React implementation approach.

**Current Direction:** FastAPI + Jinja2 templates for all UI (customer and admin).

**References:**
- Customer UI: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`

**Status:** Story may need review to align with current architecture.
"""


def needs_update(story):
    """Check if story mentions Next.js, React, or frontend technologies"""
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()

    keywords = [
        "next.js",
        "nextjs",
        "react",
        "frontend",
        "spa",
        "single page",
        "vercel",
        "customer app",
        "admin app",
        "frontend-nextjs",
        "typescript frontend",
        "react app",
    ]

    combined = f"{subject} {description}"
    return any(kw in combined for kw in keywords)


def update_story_description(importer, story):
    """Add architecture update note to story description"""
    current_desc = story.get("description", "")

    # Check if already updated
    if "ARCHITECTURE UPDATE (2025-11-02)" in current_desc:
        return False

    new_desc = current_desc + ARCHITECTURE_UPDATE_NOTE

    updates = {"description": new_desc}

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )
        return result is not None
    except Exception as e:
        print(f"   ❌ Error updating: {e}")
        return False


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print("🔍 Searching for UI-related stories in Taiga...")
    print("=" * 70)

    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"
    params = {"project": project["id"]}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to fetch stories: {response.status_code}")
        return

    stories = response.json()
    ui_stories = [s for s in stories if needs_update(s)]

    print(f"\n📊 Found {len(ui_stories)} stories that may need updates:\n")

    updated = 0
    skipped = 0

    for story in ui_stories[:20]:  # Limit to first 20
        ref = story.get("ref")
        subject = story.get("subject", "N/A")
        status = story.get("status_extra_info", {}).get("name", "Unknown")

        print(f"US#{ref}: {subject} ({status})")

        # Check if already updated
        if "ARCHITECTURE UPDATE (2025-11-02)" in story.get("description", ""):
            print("   ⏭️  Already updated")
            skipped += 1
        else:
            if update_story_description(importer, story):
                print("   ✅ Updated with architecture note")
                updated += 1
            else:
                print("   ⚠️  Update failed")

        print()

    print("=" * 70)
    print(f"Summary:")
    print(f"  Updated: {updated} stories")
    print(f"  Already updated: {skipped} stories")
    print(f"  Total checked: {len(ui_stories[:20])} stories")

    if len(ui_stories) > 20:
        print(f"\n⚠️  {len(ui_stories) - 20} more stories found but not updated in this run")


if __name__ == "__main__":
    main()
