#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Automated version of create_complete_specs_stories.py that doesn't require user input.
Creates stories for all Complete SPECs that don't have stories yet.
"""

import sys
from pathlib import Path

# Import all functions from the main script
sys.path.insert(0, str(Path(__file__).parent))

import os

# Import the main script's functions by executing it as a module
from scripts.create_complete_specs_stories import (
    authenticate,
    create_story,
    get_done_status_id,
    get_existing_stories,
    get_project_id,
    get_user_id,
    parse_spec_index,
)

# Configuration
DEVELOPER_C_USERNAME = os.getenv("DEVELOPER_C_USERNAME", "developer_c")
API_ENDPOINT = os.getenv("TAIGA_URL", "http://localhost:9000") + "/api/v1"


def main():
    """Main execution - automatically creates stories without prompts."""
    print("=" * 80)
    print("🚀 Complete SPECs Story Creator (AUTO MODE)")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating with Taiga...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project
    print("2️⃣  Getting project...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found. Exiting.")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer C
    print("3️⃣  Getting Developer C user ID...")
    developer_c_id = get_user_id(auth_token, DEVELOPER_C_USERNAME)
    if developer_c_id:
        print(f"✅ Developer C ID: {developer_c_id}")
    else:
        print(f"⚠️  Developer C ({DEVELOPER_C_USERNAME}) not found. Stories will be unassigned.")
    print()

    # Get Done status
    print("4️⃣  Getting Done status...")
    done_status_id = get_done_status_id(auth_token, project_id)
    if not done_status_id:
        print("❌ Could not find Done status. Exiting.")
        sys.exit(1)
    print(f"✅ Done status ID: {done_status_id}")
    print()

    # Parse SPEC Index
    print("5️⃣  Parsing SPEC_INDEX.md...")
    complete_specs = parse_spec_index()
    print(f"✅ Found {len(complete_specs)} Complete SPECs")
    print()

    # Get existing stories
    print("6️⃣  Checking existing stories...")
    existing_specs = get_existing_stories(auth_token, project_id)
    print(f"✅ Found stories for {len(existing_specs)} SPECs: {sorted(list(existing_specs))[:10]}")
    print()

    # Filter specs that need stories
    print("7️⃣  Identifying SPECs that need stories...")
    specs_needing_stories = [spec for spec in complete_specs if spec["number"] not in existing_specs]

    print(f"✅ {len(specs_needing_stories)} SPECs need stories created")
    print()

    if not specs_needing_stories:
        print("🎉 All Complete SPECs already have stories!")
        return

    # Display what will be created
    print("=" * 80)
    print(f"📋 SPECs that will get stories ({len(specs_needing_stories)}):")
    print("=" * 80)
    for spec in specs_needing_stories[:20]:
        print(f"  - SPEC-{spec['number']:03d}: {spec['title']}")
    if len(specs_needing_stories) > 20:
        print(f"  ... and {len(specs_needing_stories) - 20} more")
    print()

    # Create stories (NO DRY RUN - actually create them)
    print("=" * 80)
    print(f"8️⃣  Creating {len(specs_needing_stories)} stories...")
    print("=" * 80)
    print()

    created_stories = []
    failed_stories = []

    for idx, spec in enumerate(specs_needing_stories, 1):
        print(f"[{idx}/{len(specs_needing_stories)}] SPEC-{spec['number']:03d}: {spec['title']}")

        story = create_story(
            auth_token,
            project_id,
            spec["number"],
            spec["title"],
            done_status_id,
            developer_c_id,
            dry_run=False,  # Actually create!
        )

        if story:
            created_stories.append(
                {
                    "spec": spec["number"],
                    "title": spec["title"],
                    "story_ref": story.get("ref", "N/A"),
                    "story_id": story.get("id", 0),
                }
            )
        else:
            failed_stories.append({"spec": spec["number"], "title": spec["title"]})

        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {len(created_stories)} stories")
    print(f"❌ Failed: {len(failed_stories)} stories")
    print()

    if created_stories:
        print("✅ Successfully Created:")
        for story in created_stories[:20]:
            print(f"   - US#{story['story_ref']}: SPEC-{story['spec']:03d} - {story['title']}")
        if len(created_stories) > 20:
            print(f"   ... and {len(created_stories) - 20} more")
        print()

    if failed_stories:
        print("❌ Failed:")
        for story in failed_stories:
            print(f"   - SPEC-{story['spec']:03d}: {story['title']}")
        print()

    # Save results
    results_file = Path(__file__).parent.parent / "docs" / "spec-analysis" / "COMPLETE_SPECS_STORIES_CREATED.md"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        f.write("# Complete SPECs Stories - Creation Results\n\n")
        f.write(f"**Date**: Auto-run\n\n")
        f.write(f"**Total SPECs Processed**: {len(complete_specs)}\n")
        f.write(f"**SPECs Needing Stories**: {len(specs_needing_stories)}\n")
        f.write(f"**Stories Created**: {len(created_stories)}\n")
        f.write(f"**Stories Failed**: {len(failed_stories)}\n\n")

        if created_stories:
            f.write("## ✅ Successfully Created Stories\n\n")
            for story in created_stories:
                f.write(f"- **US#{story['story_ref']}**: SPEC-{story['spec']:03d} - {story['title']}\n")

        if failed_stories:
            f.write("\n## ❌ Failed Stories\n\n")
            for story in failed_stories:
                f.write(f"- **SPEC-{story['spec']:03d}**: {story['title']}\n")

    print(f"💾 Results saved to: {results_file}")
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()




