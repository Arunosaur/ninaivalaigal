#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Fixed helper script for Developer A to update US#295

This script addresses the issues Developer A encountered:
1. Proper TaigaImporter class usage
2. Version conflict handling
3. Reliable description updates
"""

import os
import sys
from datetime import datetime

# Add current directory to path (taiga_import_tasks is in same directory)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#295 with storage backend completion details"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    # Initialize importer with full API URL
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    # Get story
    story = importer.get_user_story("ninaivalaigal", 295)
    if not story:
        print("❌ Story #295 not found")
        return 1

    print(f"✅ Found story #{story['ref']}: {story['subject']}")

    # Original description
    original_description = story.get("description") or ""

    # Completion summary
    summary = """✅ Storage backend foundation landed.

• Created shared Python package `shared/storage/ninaivalaigal_storage` with S3/MinIO abstraction (config loader, factory, boto3 backend, typed exceptions). Services can now call `create_storage_backend()` to upload/download/delete and mint pre-signed URLs.

• Added developer docs (`shared/storage/README.md`) plus packaging metadata (`setup.py`) so we can install it via `pip install -e shared/storage`.

• Seeded unit tests (`shared/storage/tests/`) covering env config parsing and the S3 backend using moto; updated dev requirements for boto3 + moto.

• Expanded `.env.dev` and `config/ninaivalaigal.config.json.template` to expose STORAGE_* variables (bucket, prefix, endpoint, credentials, SSL flags). Defaults target local MinIO (`ninaivalaigal-dev-attachments`) and auto-create the bucket.

Blocked only on running the new tests inside the `nina` conda env—the `pip install -e shared/storage` step hit an exit code 1 in `conda run`. Need to rerun inside the env (e.g. `conda activate nina; pip install -e shared/storage`) before executing `pytest shared/storage/tests`. Everything else is ready for Multipart (US#296) to build on."""

    # Check if already present
    if summary.strip() in original_description:
        print("✅ Update already present in description")
        return 0

    # Append with timestamp
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n---\n**Update {stamp}**\n{summary}\n"
    new_desc = original_description + entry

    # Update story (with automatic version conflict handling)
    result = importer.update_user_story(
        story["id"], story["version"], {"description": new_desc}, retry_on_version_conflict=True, max_retries=3
    )

    if result:
        print("✅ Description updated successfully")
        print(f"   Story version: {result['version']}")
        return 0
    else:
        print("❌ Failed to update description")
        print("   The update may have failed due to version conflicts.")
        print("   Please try running the script again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
