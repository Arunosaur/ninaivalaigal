#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Check SPEC-005 stories (US#110-114) directly"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    # SPEC-005 stories mentioned in spec.md
    story_refs = [110, 111, 112, 113, 114]

    print("🔍 Checking SPEC-005 stories (US#110-114)...\n")

    for ref in story_refs:
        story = importer.get_user_story("ninaivalaigal", ref)
        if story:
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")
            description = story.get("description", "")
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

            # Check if needs update
            needs_update = False
            if "ARCHITECTURE UPDATE (2025-11-02)" not in description:
                needs_update = True

            # Check for Next.js references
            has_nextjs = (
                "next.js" in description.lower() or "nextjs" in description.lower() or "react" in description.lower()
            )

            print(f'   Needs update: {"Yes" if needs_update else "No"}')
            print(f'   Has Next.js refs: {"Yes" if has_nextjs else "No"}')
            print()
        else:
            print(f"US#{ref}: ❌ Not found\n")


if __name__ == "__main__":
    main()
