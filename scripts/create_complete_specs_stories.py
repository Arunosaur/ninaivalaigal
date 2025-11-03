#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga stories for all Complete SPECs that don't have stories yet.

This script:
1. Reads SPEC_INDEX.md to find all Complete SPECs
2. Checks which ones already have stories
3. Creates stories for complete SPECs without stories
4. Associates them with Developer C
5. Marks them as Done
6. Can be run going forward to catch new complete SPECs

Usage:
    python3 scripts/create_complete_specs_stories.py [--dry-run]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"

# Get credentials from environment
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer C assignment
# Note: Developer C username is "developer-c" (with hyphen), not "developer_c"
DEVELOPER_C_USERNAME = os.getenv("DEVELOPER_C_USERNAME", "developer-c")


def authenticate() -> Optional[str]:
    """Authenticate with Taiga and return auth token."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token: str) -> Optional[int]:
    """Get project ID for ninaivalaigal project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Use by_slug endpoint for accurate project lookup
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            project = response.json()
            return project.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_user_id(auth_token: str, username: str) -> Optional[int]:
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users?username={username}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting user {username}: {e}")
        return None


def get_project_info(auth_token: str, project_id: int) -> Optional[Dict]:
    """Get project information including statuses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/{project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting project info: {e}")
        return None


def get_done_status_id(auth_token: str, project_id: int) -> Optional[int]:
    """Get the 'Done' status ID for user stories."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = response.json()
            # Find "Done" status (case-insensitive)
            for status in statuses:
                if "done" in status.get("name", "").lower():
                    return status["id"]
            # If no "Done" status, use the last one (usually closed/done equivalent)
            if statuses:
                return statuses[-1]["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return None


def parse_spec_index() -> List[Dict]:
    """Parse SPEC_INDEX.md to extract all Complete SPECs."""
    spec_index_path = Path(__file__).parent.parent / "specs" / "SPEC_INDEX.md"

    if not spec_index_path.exists():
        print(f"❌ SPEC_INDEX.md not found at {spec_index_path}")
        return []

    complete_specs = []

    with open(spec_index_path, "r") as f:
        content = f.read()

        # Pattern to match SPEC table rows: | 000 | Title | Complete | Phase |
        # This regex handles various "Complete" statuses
        pattern = (
            r"\|\s*(\d{3}|\d{2,3})\s*\|\s*([^|]+?)\s*\|\s*(Complete|✅\s*Complete|✅|COMPLETE)\s*\|\s*([^|]*?)\s*\|"
        )

        for match in re.finditer(pattern, content, re.IGNORECASE):
            spec_num = match.group(1).strip()
            title = match.group(2).strip()
            status = match.group(3).strip()
            phase = match.group(4).strip()

            # Skip deprecated, reserved, or template SPECs
            if any(x in title.lower() for x in ["deprecated", "reserved", "template", "reference"]):
                continue

            # Skip if status explicitly says not complete
            if "deprecated" in status.lower() or "in progress" in status.lower():
                continue

            complete_specs.append(
                {"number": int(spec_num), "title": title, "phase": phase, "full_title": f"SPEC-{spec_num}: {title}"}
            )

    return sorted(complete_specs, key=lambda x: x["number"])


def get_existing_stories(auth_token: str, project_id: int) -> Set[int]:
    """Get all existing user stories and extract SPEC numbers from tags/subjects."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    existing_specs = set()

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            stories = response.json()
            for story in stories:
                # Check tags for spec-X format
                tags = story.get("tags", [])
                if tags:
                    # Handle both list of strings and list of tag objects
                    for tag_item in tags:
                        if isinstance(tag_item, str):
                            tag = tag_item
                        elif isinstance(tag_item, dict):
                            tag = tag_item.get("name", "")
                        elif isinstance(tag_item, list):
                            # Skip nested lists
                            continue
                        else:
                            tag = str(tag_item)

                        if tag and isinstance(tag, str) and tag.startswith("spec-"):
                            spec_num = tag.replace("spec-", "").strip()
                            try:
                                existing_specs.add(int(spec_num))
                            except ValueError:
                                pass

                # Check subject for SPEC-XXX format
                subject = story.get("subject", "")
                if subject:
                    spec_match = re.search(r"SPEC[-\s]?(\d{2,3})", subject, re.IGNORECASE)
                    if spec_match:
                        try:
                            existing_specs.add(int(spec_match.group(1)))
                        except ValueError:
                            pass

        return existing_specs
    except Exception as e:
        print(f"⚠️  Error getting existing stories: {e}")
        import traceback

        traceback.print_exc()
        return set()


def get_spec_description(spec_num: int, spec_title: str) -> str:
    """Generate a description for the SPEC story."""
    spec_dir = Path(__file__).parent.parent / "specs" / f"{spec_num:03d}-*"

    # Try to find the SPEC directory
    spec_dirs = list(Path(__file__).parent.parent.glob(f"specs/{spec_num:03d}-*"))

    description_parts = [
        f"## SPEC-{spec_num:03d}: {spec_title}",
        "",
        "**Status**: ✅ Complete",
        "",
        f"This SPEC has been marked as Complete in the SPEC Index.",
    ]

    if spec_dirs:
        spec_dir = spec_dirs[0]
        readme_path = spec_dir / "README.md"

        if readme_path.exists():
            try:
                with open(readme_path, "r") as f:
                    readme_content = f.read()
                    # Extract first meaningful paragraph
                    lines = readme_content.split("\n")
                    for line in lines:
                        if line.strip() and not line.startswith("#") and not line.startswith("---"):
                            if len(line.strip()) > 50:  # Meaningful content
                                description_parts.append(f"\n**Overview**: {line.strip()}")
                                break
            except Exception:
                pass

        # Check for completion summary
        completion_path = spec_dir / "COMPLETION_SUMMARY.md"
        if completion_path.exists():
            description_parts.append("\n**Completion**: See COMPLETION_SUMMARY.md in SPEC directory.")

    description_parts.extend(
        [
            "",
            "**Implementation**:",
            "- This SPEC has been fully implemented and is operational",
            "- All acceptance criteria have been met",
            "- Testing and validation completed",
            "",
            "**Created**: Retrospective story for completed work",
            "**Assigned**: Developer C",
            "**Status**: Done",
        ]
    )

    return "\n".join(description_parts)


def create_story(
    auth_token: str,
    project_id: int,
    spec_num: int,
    spec_title: str,
    done_status_id: int,
    developer_c_id: Optional[int],
    dry_run: bool = False,
) -> Optional[Dict]:
    """Create a Taiga story for a complete SPEC."""
    subject = f"SPEC-{spec_num:03d}: {spec_title} (Complete)"
    description = get_spec_description(spec_num, spec_title)
    tags = [f"spec-{spec_num:03d}", "complete", "retrospective", "developer-c"]

    if dry_run:
        print(f"  [DRY RUN] Would create: {subject}")
        print(f"  Tags: {', '.join(tags)}")
        print(f"  Status: Done (ID: {done_status_id})")
        if developer_c_id:
            print(f"  Assignee: Developer C (ID: {developer_c_id})")
        return {"ref": "DRY-RUN", "id": 0, "subject": subject}

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": tags,
        "status": done_status_id,
    }

    if developer_c_id:
        payload["assigned_to"] = developer_c_id

    try:
        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)

        if response.status_code == 201:
            story = response.json()
            print(f"  ✅ Created: {subject} (US#{story.get('ref', 'N/A')})")
            return story
        else:
            print(f"  ❌ Failed to create story: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error creating story: {e}")
        return None


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Create Taiga stories for complete SPECs without stories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating")
    parser.add_argument("--auto", action="store_true", help="Automatically create stories without confirmation prompt")
    args = parser.parse_args()

    print("=" * 80)
    print("🚀 Complete SPECs Story Creator")
    print("=" * 80)
    print()

    # Step 1: Authenticate
    print("1️⃣  Authenticating with Taiga...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Step 2: Get project
    print("2️⃣  Getting project...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found. Exiting.")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Step 3: Get Developer C user ID
    print("3️⃣  Getting Developer C user ID...")
    developer_c_id = get_user_id(auth_token, DEVELOPER_C_USERNAME)
    if developer_c_id:
        print(f"✅ Developer C ID: {developer_c_id}")
    else:
        print(f"⚠️  Developer C ({DEVELOPER_C_USERNAME}) not found. Stories will be unassigned.")
    print()

    # Step 4: Get Done status ID
    print("4️⃣  Getting Done status...")
    done_status_id = get_done_status_id(auth_token, project_id)
    if not done_status_id:
        print("❌ Could not find Done status. Exiting.")
        sys.exit(1)
    print(f"✅ Done status ID: {done_status_id}")
    print()

    # Step 5: Parse SPEC Index
    print("5️⃣  Parsing SPEC_INDEX.md...")
    complete_specs = parse_spec_index()
    print(f"✅ Found {len(complete_specs)} Complete SPECs")
    print()

    # Step 6: Get existing stories
    print("6️⃣  Checking existing stories...")
    existing_specs = get_existing_stories(auth_token, project_id)
    print(f"✅ Found stories for {len(existing_specs)} SPECs")
    print()

    # Step 7: Filter specs that need stories
    print("7️⃣  Identifying SPECs that need stories...")
    specs_needing_stories = [spec for spec in complete_specs if spec["number"] not in existing_specs]

    print(f"✅ {len(specs_needing_stories)} SPECs need stories created")
    print()

    if not specs_needing_stories:
        print("🎉 All Complete SPECs already have stories!")
        return

    # Step 8: Display what will be created
    print("=" * 80)
    print(f"📋 SPECs that will get stories ({len(specs_needing_stories)}):")
    print("=" * 80)
    for spec in specs_needing_stories[:20]:  # Show first 20
        print(f"  - SPEC-{spec['number']:03d}: {spec['title']}")
    if len(specs_needing_stories) > 20:
        print(f"  ... and {len(specs_needing_stories) - 20} more")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No stories will be created")
        print()

    # Step 9: Confirm (unless auto mode)
    if not args.dry_run and not args.auto:
        response = input(f"Create {len(specs_needing_stories)} stories? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("⏭️  Cancelled.")
            return
    elif args.auto:
        print(f"🚀 AUTO MODE: Creating {len(specs_needing_stories)} stories automatically...")
        print()

    # Step 10: Create stories
    print()
    print("=" * 80)
    print(f"8️⃣  Creating {len(specs_needing_stories)} stories...")
    print("=" * 80)
    print()

    created_stories = []
    failed_stories = []

    for idx, spec in enumerate(specs_needing_stories, 1):
        print(f"[{idx}/{len(specs_needing_stories)}] SPEC-{spec['number']:03d}: {spec['title']}")

        story = create_story(
            auth_token, project_id, spec["number"], spec["title"], done_status_id, developer_c_id, dry_run=args.dry_run
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
        for story in created_stories[:10]:
            print(f"   - US#{story['story_ref']}: SPEC-{story['spec']:03d} - {story['title']}")
        if len(created_stories) > 10:
            print(f"   ... and {len(created_stories) - 10} more")
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
        f.write(f"**Date**: {Path(__file__).stat().st_mtime}\n\n")
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
