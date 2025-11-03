#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga stories for all SPECs that don't have any stories,
even if marked as Complete. Assign to Developer C and mark as Done.

Usage:
    python3 scripts/create_missing_spec_stories.py
"""

import os
import re
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_C_USERNAME = "developer-c"


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": project_slug},
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_user_id(headers, username):
    """Get user ID by username."""
    response = requests.get(f"{API_ENDPOINT}/users/me", headers=headers)
    if response.status_code == 200:
        me = response.json()
        if me.get("username") == username:
            return me.get("id")

    # Try to get all users
    response = requests.get(
        f"{API_ENDPOINT}/users", headers=headers, params={"project": get_project_id(headers, PROJECT_SLUG)}
    )
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username") == username:
                return user.get("id")

    return None


def get_status_id(headers, project_id, status_name):
    """Get status ID by name."""
    response = requests.get(
        f"{API_ENDPOINT}/userstory-statuses",
        headers=headers,
        params={"project": project_id},
    )
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def get_existing_stories_with_specs(headers, project_id):
    """Get all existing stories and extract SPEC numbers."""
    all_stories = []
    page = 1
    page_size = 500

    while True:
        response = requests.get(
            f"{API_ENDPOINT}/userstories",
            headers=headers,
            params={"project": project_id, "page": page, "page_size": page_size},
        )
        if response.status_code == 200:
            stories = response.json()
            if not stories:
                break
            all_stories.extend(stories)
            if len(stories) < page_size:
                break
            page += 1
        else:
            break

    # Extract SPEC numbers from stories
    spec_numbers_with_stories = set()
    for story in all_stories:
        subject = story.get("subject", "")
        tags = story.get("tags", [])

        # Check subject for SPEC-XXX pattern
        spec_match = re.search(r"SPEC-(\d{3})", subject, re.IGNORECASE)
        if spec_match:
            spec_numbers_with_stories.add(spec_match.group(1))

        # Check tags
        if isinstance(tags, list):
            for tag in tags:
                tag_name = tag if isinstance(tag, str) else (tag.get("name", "") if isinstance(tag, dict) else str(tag))
                spec_match = re.search(r"SPEC-(\d{3})", tag_name, re.IGNORECASE)
                if spec_match:
                    spec_numbers_with_stories.add(spec_match.group(1))

    return spec_numbers_with_stories


def parse_spec_index():
    """Parse SPEC_INDEX.md to get all SPECs."""
    spec_index_path = "specs/SPEC_INDEX.md"
    if not os.path.exists(spec_index_path):
        print(f"❌ SPEC_INDEX.md not found at {spec_index_path}")
        sys.exit(1)

    specs = []
    with open(spec_index_path, "r") as f:
        lines = f.readlines()

    # Parse table rows (format: | 001 | Title | Status | Phase |)
    for line in lines:
        if not line.strip().startswith("|") or line.strip().startswith("|---"):
            continue

        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            spec_num_match = re.search(r"(\d{3})", parts[0])
            if spec_num_match:
                spec_num = spec_num_match.group(1)
                title = parts[1]
                status = parts[2] if len(parts) > 2 else ""
                phase = parts[3] if len(parts) > 3 else ""

                specs.append(
                    {
                        "number": spec_num,
                        "title": title,
                        "status": status,
                        "phase": phase,
                    }
                )

    return specs


def get_spec_readme(spec_num, spec_title):
    """Get SPEC README content if it exists."""
    # Try to find the SPEC directory
    spec_dir_patterns = [
        f"specs/{spec_num}-*",
        f"specs/*{spec_num}*",
    ]

    spec_dirs = []
    for pattern in spec_dir_patterns:
        import glob

        spec_dirs.extend(glob.glob(pattern))

    if not spec_dirs:
        return None

    spec_dir = spec_dirs[0]
    readme_path = os.path.join(spec_dir, "README.md")

    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            return f.read()

    return None


def create_story(headers, project_id, spec_num, spec_title, spec_status, description, assignee_id, status_id):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": f"SPEC-{spec_num}: {spec_title}",
        "description": description,
        "tags": [f"SPEC-{spec_num}"],
    }

    if assignee_id:
        payload["assigned_to"] = assignee_id

    if status_id:
        payload["status"] = status_id

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code} - {response.text[:200]}")
        return None


def main():
    """Main function."""
    print("=" * 80)
    print("📋 Creating Taiga Stories for SPECs Without Stories")
    print(f"   Project: {PROJECT_SLUG}")
    print(f"   Assignee: {DEVELOPER_C_USERNAME}")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting project...")
    project_id = get_project_id(headers, PROJECT_SLUG)
    print(f"✅ Project ID: {project_id}")

    # Get user ID for Developer C
    print(f"\n3️⃣  Getting user ID for {DEVELOPER_C_USERNAME}...")
    assignee_id = get_user_id(headers, DEVELOPER_C_USERNAME)
    if assignee_id:
        print(f"✅ Developer C ID: {assignee_id}")
    else:
        print(f"⚠️  Developer C not found, stories will be unassigned")
        assignee_id = None

    # Get status IDs
    print("\n4️⃣  Getting status IDs...")
    done_status_id = get_status_id(headers, project_id, "Done")
    print(f"✅ Done status ID: {done_status_id}")

    # Get existing stories and their SPEC numbers
    print("\n5️⃣  Getting existing stories...")
    existing_specs = get_existing_stories_with_specs(headers, project_id)
    print(f"✅ Found {len(existing_specs)} SPECs with existing stories")

    # Parse SPEC_INDEX.md
    print("\n6️⃣  Parsing SPEC_INDEX.md...")
    all_specs = parse_spec_index()
    print(f"✅ Found {len(all_specs)} SPECs in index")

    # Find SPECs without stories
    missing_specs = []
    for spec in all_specs:
        if spec["number"] not in existing_specs:
            missing_specs.append(spec)

    print(f"\n7️⃣  Found {len(missing_specs)} SPECs without stories")
    if not missing_specs:
        print("✅ All SPECs already have stories!")
        return

    # Create stories
    print("\n8️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, spec in enumerate(missing_specs, 1):
        spec_num = spec["number"]
        spec_title = spec["title"]
        spec_status = spec["status"]

        print(f"\n   [{idx}/{len(missing_specs)}] Creating story for SPEC-{spec_num}: {spec_title[:50]}...")

        # Generate description
        readme_content = get_spec_readme(spec_num, spec_title)

        description = f"""**SPEC-{spec_num}: {spec_title}**

**Status in SPEC_INDEX.md**: {spec_status}
**Phase**: {spec["phase"]}

**Objective**: {spec_title}

"""

        if readme_content:
            # Extract key information from README
            description += "**Details**: See SPEC documentation for full details.\n\n"
            # Limit README content to avoid overly long descriptions
            readme_lines = readme_content.split("\n")[:50]
            description += "```\n" + "\n".join(readme_lines) + "\n```"
        else:
            description += "**Details**: SPEC documentation may be in development or archived."

        # Create story (always mark as Done)
        created = create_story(
            headers,
            project_id,
            spec_num,
            spec_title,
            spec_status,
            description,
            assignee_id,
            done_status_id,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, spec_num, spec_title))
            print(f"   ✅ Created US#{ref}")
        else:
            failed_stories.append((spec_num, spec_title))
            print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")

    if created_stories:
        print("\nCreated stories:")
        for ref, spec_num, spec_title in created_stories:
            print(f"  US#{ref}: SPEC-{spec_num}: {spec_title[:60]}")

    if failed_stories:
        print("\nFailed stories:")
        for spec_num, spec_title in failed_stories:
            print(f"  SPEC-{spec_num}: {spec_title[:60]}")

    print("=" * 80)


if __name__ == "__main__":
    main()
