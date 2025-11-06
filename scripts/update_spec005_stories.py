#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update SPEC-005 stories (US#110-114) with FastAPI + Jinja2 architecture notes"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

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
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
- SPEC-005: `specs/005-admin-dashboard/spec.md`
- Unified Plan: `docs/SPEC_TAIGA_UNIFORMITY_PLAN.md`

**Note:** Next.js/React examples are for historical reference only.
"""


def update_story(importer, story_ref, story_subject):
    """Update a story with architecture note."""
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"US#{story_ref}: ❌ Not found")
        return False

    current_desc = story.get("description", "")

    # Check if already updated
    if "ARCHITECTURE UPDATE (2025-11-02)" in current_desc:
        print(f"US#{story_ref}: ⏭️  Already updated")
        return True

    # Add architecture note
    new_desc = current_desc + ARCHITECTURE_NOTE

    # Update tags
    tags = story.get("tags", [])
    tag_names = []
    for tag in tags:
        if isinstance(tag, str):
            tag_names.append(tag)
        elif isinstance(tag, dict):
            tag_names.append(tag.get("name", ""))

    # Add required tags
    required_tags = ["spec-005", "fastapi", "jinja2", "templates", "admin"]
    for tag in required_tags:
        if tag not in [t.lower() for t in tag_names]:
            tag_names.append(tag)

    # Remove Next.js tags if present
    tag_names = [t for t in tag_names if "nextjs" not in t.lower() and "next.js" not in t.lower()]

    updates = {"description": new_desc, "tags": tag_names}

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )
        if result:
            print(f"US#{story_ref}: ✅ Updated - {story_subject}")
            return True
        else:
            print(f"US#{story_ref}: ❌ Update failed")
            return False
    except Exception as e:
        print(f"US#{story_ref}: ❌ Error: {e}")
        return False


def main():
    """Update SPEC-005 stories."""
    print("🔄 Updating SPEC-005 stories with FastAPI + Jinja2 architecture notes...\n")
    print("=" * 80)

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # SPEC-005 stories
    stories = [
        (110, "US-98: Admin User Management API"),
        (111, "US-99: Admin UI Integration & Polish"),
        (112, "US-100: Admin Activity Logging System"),
        (113, "US-101: Context Admin Management API"),
        (114, "US-102: System Dashboard & Monitoring"),
    ]

    updated = 0
    skipped = 0
    errors = 0

    for ref, subject in stories:
        if update_story(importer, ref, subject):
            updated += 1
        else:
            errors += 1
        print()

    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   ✅ Updated: {updated} stories")
    print(f"   ❌ Errors: {errors} stories")
    print("=" * 80)


if __name__ == "__main__":
    main()
