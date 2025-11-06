#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Check actual content of a specific story"""

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

    # Check US#112 (Done story we updated)
    story = importer.get_user_story("ninaivalaigal", 112)

    if not story:
        print("US#112: ❌ Not found")
        return

    ref = story.get("ref")
    subject = story.get("subject", "N/A")
    status = story.get("status_extra_info", {}).get("name", "Unknown")
    description = story.get("description", "")
    tags = story.get("tags", [])

    print(f"US#{ref}: {subject}")
    print(f"Status: {status}")
    print(f"Tags: {tags}")
    print(f"\nDescription length: {len(description)} chars")
    print(f'\nHas "ARCHITECTURE UPDATE": {"✅" if "ARCHITECTURE UPDATE (2025-11-02)" in description else "❌"}')
    print(f'Has "SPEC DEPRECATED": {"✅" if "SPEC DEPRECATED (2025-11-02)" in description else "❌"}')
    print(f'Has "FastAPI + Jinja2": {"✅" if "FastAPI + Jinja2" in description else "❌"}')
    print(
        f'Has docs reference: {"✅" if "docs/ADMIN_UI_FASTAPI_ANALYSIS.md" in description or "docs/FRONTEND_ARCHITECTURE_DECISION.md" in description else "❌"}'
    )

    # Show last 500 chars of description
    print(f"\nLast 500 characters of description:")
    print("-" * 80)
    print(description[-500:] if len(description) > 500 else description)
    print("-" * 80)

    # Check US#101 (Done story we updated)
    print("\n" + "=" * 80)
    story2 = importer.get_user_story("ninaivalaigal", 101)

    if story2:
        ref2 = story2.get("ref")
        subject2 = story2.get("subject", "N/A")
        status2 = story2.get("status_extra_info", {}).get("name", "Unknown")
        description2 = story2.get("description", "")

        print(f"US#{ref2}: {subject2}")
        print(f"Status: {status2}")
        print(f'\nHas "ARCHITECTURE UPDATE": {"✅" if "ARCHITECTURE UPDATE (2025-11-02)" in description2 else "❌"}')
        print(f'Has "SPEC DEPRECATED": {"✅" if "SPEC DEPRECATED (2025-11-02)" in description2 else "❌"}')
        print(f'Has "FastAPI + Jinja2": {"✅" if "FastAPI + Jinja2" in description2 else "❌"}')
        print(f'Has docs reference: {"✅" if "docs/" in description2 else "❌"}')

        # Show last 500 chars
        print(f"\nLast 500 characters of description:")
        print("-" * 80)
        print(description2[-500:] if len(description2) > 500 else description2)
        print("-" * 80)


if __name__ == "__main__":
    main()
