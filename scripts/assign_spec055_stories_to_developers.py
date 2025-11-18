#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign SPEC-055 stories to Developer F, G, H after they are created.

Usage:
    python3 scripts/assign_spec055_stories_to_developers.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "055"


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


def get_user_id(headers, username):
    """Get user ID by username."""
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username", "").lower() == username.lower():
                return user.get("id")
    return None


def get_stories_by_tag(headers, project_id, tag):
    """Get stories by tag."""
    response = requests.get(
        f"{API_ENDPOINT}/userstories",
        headers=headers,
        params={"project": project_id, "tags": tag},
    )
    if response.status_code == 200:
        return response.json()
    return []


def update_story_assignment(headers, story_id, version, assigned_to):
    """Update story assignment."""
    payload = {
        "version": version,
        "assigned_to": assigned_to,
    }

    response = requests.patch(
        f"{API_ENDPOINT}/userstories/{story_id}",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    return response.status_code == 200


def main():
    """Main function."""
    print("=" * 80)
    print("👥 Assigning SPEC-055 Stories to Developers F, G, H")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": PROJECT_SLUG},
    )
    if response.status_code != 200:
        print(f"❌ Failed to get project: {response.status_code}")
        sys.exit(1)

    project_id = response.json().get("id")
    print(f"\n2️⃣  Project ID: {project_id}")

    # Get developer IDs
    print("\n3️⃣  Getting developer IDs...")
    developers = {}
    for dev_name in ["developer-f", "developer-g", "developer-h"]:
        dev_id = get_user_id(headers, dev_name)
        if dev_id:
            developers[dev_name] = dev_id
            print(f"✅ {dev_name}: ID={dev_id}")
        else:
            print(f"⚠️  {dev_name}: Not found")

    if not developers:
        print("\n❌ No developers found. Please create them in Taiga UI first.")
        print("   Then run this script again.")
        sys.exit(1)

    # Get SPEC-055 stories
    print(f"\n4️⃣  Getting SPEC-{SPEC_NUMBER} stories...")
    tag = f"SPEC-{SPEC_NUMBER}"
    stories = get_stories_by_tag(headers, project_id, tag)
    print(f"✅ Found {len(stories)} stories with tag {tag}")

    if not stories:
        print("⚠️  No stories found. Stories may not be created yet.")
        sys.exit(0)

    # Define assignments
    assignments = {
        "SPEC-055: Verify MCP Server Modularization": "developer-f",
        "SPEC-055: Database.py Legacy Cleanup Verification": "developer-g",
        "SPEC-055: Module Documentation & README Completion": "developer-h",
        "SPEC-055: Final Modularization Verification & Testing": "developer-f",
    }

    # Assign stories
    print("\n5️⃣  Assigning stories...")
    assigned_count = 0
    failed_count = 0

    for story in stories:
        subject = story.get("subject", "")
        story_id = story.get("id")
        version = story.get("version", 1)

        # Find matching assignment
        assigned_dev = None
        for pattern, dev_name in assignments.items():
            if pattern in subject:
                assigned_dev = dev_name
                break

        if assigned_dev and assigned_dev in developers:
            dev_id = developers[assigned_dev]
            ref = story.get("ref")

            if update_story_assignment(headers, story_id, version, dev_id):
                print(f"   ✅ US#{ref}: Assigned to {assigned_dev}")
                assigned_count += 1
            else:
                print(f"   ❌ US#{ref}: Failed to assign")
                failed_count += 1
        else:
            print(f"   ⚠️  {subject[:50]}: No assignment mapping found")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Assigned: {assigned_count}")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count}")
    print("=" * 80)


if __name__ == "__main__":
    main()




