#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Verify Complete SPECs stories were created in Taiga.

Usage:
    python3 scripts/verify_complete_specs_stories.py
"""

import os
import re
import sys
from pathlib import Path

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"

# Get credentials from environment
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
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


def get_project_id(auth_token):
    """Get project ID for ninaivalaigal project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            projects = response.json()
            if projects:
                return projects[0]["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_all_stories(auth_token, project_id):
    """Get all user stories for the project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def main():
    """Main verification function."""
    print("=" * 80)
    print("🔍 Verifying Complete SPECs Stories in Taiga")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project
    print("2️⃣  Getting project...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get all stories
    print("3️⃣  Fetching all user stories...")
    stories = get_all_stories(auth_token, project_id)
    print(f"✅ Found {len(stories)} total stories")
    print()

    # Filter stories by tags/subject
    print("4️⃣  Filtering Complete SPECs stories...")
    complete_specs_stories = []
    for story in stories:
        tags = story.get("tags", [])
        subject = story.get("subject", "")

        # Extract SPEC number from subject (most reliable)
        spec_num = None
        spec_match = re.search(r"SPEC[-\s]?(\d{2,3})", subject, re.IGNORECASE)
        if spec_match:
            try:
                spec_num = int(spec_match.group(1))
            except ValueError:
                pass

        # Check if story is about a Complete SPEC
        # Criteria: Subject contains "Complete" OR tags contain "complete" OR status is "Done"
        is_complete_spec_story = (
            "complete" in subject.lower()
            or any("complete" in str(tag).lower() for tag in tags)
            or "done" in story.get("status_extra_info", {}).get("name", "").lower()
        )

        # Also check for SPEC pattern in subject
        has_spec_pattern = "SPEC-" in subject.upper()

        if (is_complete_spec_story and has_spec_pattern) or spec_num:
            # Try to extract spec_num from tags if not found in subject
            if not spec_num:
                for tag in tags:
                    tag_str = (
                        tag if isinstance(tag, str) else (tag.get("name", "") if isinstance(tag, dict) else str(tag))
                    )
                    if tag_str and isinstance(tag_str, str) and tag_str.startswith("spec-"):
                        try:
                            spec_num = int(tag_str.replace("spec-", "").strip())
                            break
                        except ValueError:
                            pass

            complete_specs_stories.append(
                {
                    "id": story.get("id"),
                    "ref": story.get("ref"),
                    "subject": subject,
                    "status": story.get("status_extra_info", {}).get("name", "Unknown"),
                    "tags": tags,
                    "assigned_to": story.get("assigned_to"),
                    "spec_num": spec_num,
                }
            )

    print(f"✅ Found {len(complete_specs_stories)} Complete SPECs stories")
    print()

    # Display results
    print("=" * 80)
    print("📊 Complete SPECs Stories Found:")
    print("=" * 80)
    print()

    if not complete_specs_stories:
        print("⚠️  No Complete SPECs stories found!")
        print()
        print("Possible reasons:")
        print("  1. Stories weren't created yet")
        print("  2. Stories have different tags/subjects")
        print("  3. Stories are in a different project")
        print()
        print("Recent stories (last 20):")
        for story in stories[-20:]:
            print(f"  - US#{story.get('ref')}: {story.get('subject')[:60]}...")
        return

    # Sort by ref
    complete_specs_stories.sort(key=lambda x: x.get("ref", 0))

    # Display
    for story in complete_specs_stories:
        spec_info = f"SPEC-{story['spec_num']:03d}" if story["spec_num"] else "SPEC-???"
        print(f"US#{story['ref']:3d} | {spec_info:12s} | {story['subject'][:50]:50s} | {story['status']:15s}")

    print()
    print(f"Total: {len(complete_specs_stories)} stories found")
    print()

    # Check Developer C assignment
    print("5️⃣  Checking Developer C assignments...")
    developer_c_stories = [s for s in complete_specs_stories if s.get("assigned_to")]
    print(f"✅ {len(developer_c_stories)} stories have assignments")
    if len(developer_c_stories) < len(complete_specs_stories):
        print(f"⚠️  {len(complete_specs_stories) - len(developer_c_stories)} stories not assigned")


if __name__ == "__main__":
    main()
