#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update Taiga stories for UI-related SPECs to reflect FastAPI + Jinja2 architecture.

This script:
1. Finds all stories linked to UI-related SPECs (005, 102, 103, 113, 114, 115, 116, 121, 122, 123, 124)
2. Updates descriptions to reference FastAPI + Jinja2
3. Adds deprecation notices for deprecated SPEC stories
4. Updates tags appropriately
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

# UI-related SPECs to audit
UI_SPECS = {
    "005": {"deprecated": False, "replacement": None},
    "102": {"deprecated": True, "replacement": "SPEC-005, SPEC-146"},
    "103": {"deprecated": True, "replacement": "SPEC-005, SPEC-146"},
    "113": {"deprecated": False, "replacement": None},
    "114": {"deprecated": False, "replacement": None},
    "115": {"deprecated": False, "replacement": None},
    "116": {"deprecated": True, "replacement": "SPEC-005, SPEC-146"},
    "121": {"deprecated": True, "replacement": "SPEC-005, SPEC-146"},
    "122": {"deprecated": True, "replacement": "SPEC-146"},
    "123": {"deprecated": True, "replacement": "SPEC-005"},
    "124": {"deprecated": True, "replacement": "SPEC-016"},
}

ARCHITECTURE_UPDATE_NOTE = """
---

⚠️ **ARCHITECTURE UPDATE (2025-11-02):**

This story has been updated to reflect the current architecture decision: **FastAPI + Jinja2 templates**.

**Current Stack:**
- **Primary:** FastAPI + Jinja2 templates (server-rendered)
- **Styling:** TailwindCSS
- **Interactivity:** Alpine.js or HTMX
- **Optional:** React micro-widgets (Vite-built) for complex visualizations only

**References:**
- Customer UI: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
- Unified Plan: `docs/SPEC_TAIGA_UNIFORMITY_PLAN.md`

**Note:** Next.js/React examples in this story are for historical reference only.
"""

DEPRECATION_NOTE_TEMPLATE = """
---

🚫 **SPEC DEPRECATED (2025-11-02):**

This story is linked to a deprecated SPEC that described a Next.js/React implementation approach.

**Replacement SPECs:** {replacement}

**Current Direction:** FastAPI + Jinja2 templates for all UI (customer and admin).

**See:** `docs/SPEC_TAIGA_UPDATE_SUMMARY.md` for migration details.
"""


def get_stories_by_spec_tags(importer, project_id, spec_numbers):
    """Get all stories tagged with spec-XXX tags."""
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"

    all_stories = []

    # Get all stories for the project
    params = {"project": project_id}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to fetch stories: {response.status_code}")
        return []

    stories = response.json()

    # Filter stories by spec tags
    for story in stories:
        tags = story.get("tags", [])
        story_specs = set()

        # Extract spec numbers from tags
        for tag in tags:
            tag_name = tag if isinstance(tag, str) else (tag.get("name", "") if isinstance(tag, dict) else str(tag))
            match = re.search(r"spec[-\s]?(\d{2,3})", tag_name, re.IGNORECASE)
            if match:
                spec_num = match.group(1).zfill(3)  # Pad to 3 digits
                if spec_num in spec_numbers:
                    story_specs.add(spec_num)

        # Also check subject for SPEC-XXX
        subject = story.get("subject", "")
        for spec_num in spec_numbers:
            if re.search(rf"SPEC[-\s]?{spec_num}", subject, re.IGNORECASE):
                story_specs.add(spec_num)

        if story_specs:
            story["_matched_specs"] = story_specs
            all_stories.append(story)

    return all_stories


def needs_update(story, spec_info):
    """Check if story needs update based on SPEC status."""
    description = story.get("description", "")

    # Check if already updated
    if "ARCHITECTURE UPDATE (2025-11-02)" in description:
        return False

    if spec_info["deprecated"]:
        if "SPEC DEPRECATED (2025-11-02)" in description:
            return False

    return True


def update_story(importer, story, spec_num, spec_info):
    """Update story description with architecture note or deprecation notice."""
    current_desc = story.get("description", "")

    if spec_info["deprecated"]:
        # Add deprecation notice
        deprecation_note = DEPRECATION_NOTE_TEMPLATE.format(replacement=spec_info["replacement"])
        new_desc = current_desc + deprecation_note
    else:
        # Add architecture update note
        new_desc = current_desc + ARCHITECTURE_UPDATE_NOTE

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

    # Add/update tags
    if "fastapi" not in [t.lower() for t in tag_names]:
        tag_names.append("fastapi")
    if "jinja2" not in [t.lower() for t in tag_names]:
        tag_names.append("jinja2")
    if "templates" not in [t.lower() for t in tag_names]:
        tag_names.append("templates")

    # Remove Next.js tags if present
    tag_names = [t for t in tag_names if "nextjs" not in t.lower() and "next.js" not in t.lower()]

    # Add deprecated tag if needed
    if spec_info["deprecated"] and "deprecated" not in [t.lower() for t in tag_names]:
        tag_names.append("deprecated")

    updates = {"description": new_desc, "tags": tag_names}

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
    """Main execution function."""
    print("🔍 Auditing Taiga stories for UI-related SPECs...")
    print("=" * 80)

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    project_id = project["id"]
    print(f'✅ Connected to project: {project["name"]} (ID: {project_id})\n')

    # Get all UI-related spec numbers
    spec_numbers = list(UI_SPECS.keys())

    # Find stories
    print(f'📊 Searching for stories with SPEC tags: {", ".join(f"spec-{s}" for s in spec_numbers)}...')
    stories = get_stories_by_spec_tags(importer, project_id, spec_numbers)

    print(f"\n✅ Found {len(stories)} stories linked to UI-related SPECs\n")

    if not stories:
        print("No stories found. Exiting.")
        return

    # Group stories by SPEC
    stories_by_spec = {}
    for story in stories:
        for spec_num in story.get("_matched_specs", []):
            if spec_num not in stories_by_spec:
                stories_by_spec[spec_num] = []
            stories_by_spec[spec_num].append(story)

    # Process each SPEC
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for spec_num in sorted(spec_numbers):
        spec_info = UI_SPECS[spec_num]
        spec_stories = stories_by_spec.get(spec_num, [])

        if not spec_stories:
            print(f"SPEC-{spec_num}: No stories found")
            continue

        status = "DEPRECATED" if spec_info["deprecated"] else "ACTIVE"
        print(f"\n📋 SPEC-{spec_num} ({status}): {len(spec_stories)} story/stories")
        print("-" * 80)

        for story in spec_stories:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status_name = story.get("status_extra_info", {}).get("name", "Unknown")

            print(f"US#{ref}: {subject}")
            print(f"   Status: {status_name}")

            if not needs_update(story, spec_info):
                print("   ⏭️  Already updated")
                skipped_count += 1
            else:
                if update_story(importer, story, spec_num, spec_info):
                    action = "deprecation notice" if spec_info["deprecated"] else "architecture update"
                    print(f"   ✅ Updated with {action}")
                    updated_count += 1
                else:
                    print("   ⚠️  Update failed")
                    error_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print(f"   ✅ Updated: {updated_count} stories")
    print(f"   ⏭️  Already updated: {skipped_count} stories")
    print(f"   ❌ Errors: {error_count} stories")
    print(f"   📋 Total checked: {len(stories)} stories")
    print("=" * 80)


if __name__ == "__main__":
    main()
