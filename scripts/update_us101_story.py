#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update US#101 (SPEC-122 related) with deprecation notice"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

DEPRECATION_NOTE = """
---

🚫 **SPEC DEPRECATED (2025-11-02):**

This story is linked to SPEC-122 (Customer Frontend Rollout), which is deprecated.

**Replacement SPEC:** SPEC-146 (Customer UI - FastAPI templating)

**Current Direction:** FastAPI + Jinja2 templates for customer UI (not Next.js + Vercel).

**See:**
- `docs/FRONTEND_ARCHITECTURE_DECISION.md` for customer UI architecture
- `docs/SPEC_TAIGA_UPDATE_SUMMARY.md` for migration details
- `specs/122-customer-frontend-rollout/README.md` (deprecated)

**Note:** This story may need review to align with FastAPI templating approach.
"""


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story = importer.get_user_story("ninaivalaigal", 101)

    if not story:
        print("US#101: ❌ Not found")
        return

    current_desc = story.get("description", "")
    subject = story.get("subject", "N/A")

    print(f"US#101: {subject}")

    # Check if already updated
    if "SPEC DEPRECATED (2025-11-02)" in current_desc:
        print("   ⏭️  Already updated")
        return

    # Add deprecation note
    new_desc = current_desc + DEPRECATION_NOTE

    # Update tags
    tags = story.get("tags", [])
    tag_names = []
    for tag in tags:
        if isinstance(tag, str):
            tag_names.append(tag)
        elif isinstance(tag, dict):
            tag_names.append(tag.get("name", ""))

    # Add required tags
    required_tags = ["spec-122", "deprecated", "fastapi", "jinja2"]
    for tag in required_tags:
        if tag not in [t.lower() for t in tag_names]:
            tag_names.append(tag)

    # Remove Next.js/Vercel tags if present
    tag_names = [
        t for t in tag_names if "nextjs" not in t.lower() and "next.js" not in t.lower() and "vercel" not in t.lower()
    ]

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
            print("   ✅ Updated with deprecation notice")
        else:
            print("   ❌ Update failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    main()
