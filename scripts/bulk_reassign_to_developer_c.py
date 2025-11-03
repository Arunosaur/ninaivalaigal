#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Bulk reassign Complete SPEC stories to Developer C in ninaivalaigal project.

Usage:
    python3 scripts/bulk_reassign_to_developer_c.py [--dry-run]
"""

import argparse
import os
import sys

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"

# Get credentials from environment
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer C
DEVELOPER_C_USERNAME = os.getenv("DEVELOPER_C_USERNAME", "developer-c")


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
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token):
    """Get project ID by slug."""
    headers = {"Authorization": f"Bearer {auth_token}"}
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


def get_user_id(auth_token, username):
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # First try direct username lookup
    url = f"{API_ENDPOINT}/users?username={username}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            # Filter to exact match
            for user in users:
                if user.get("username") == username:
                    return user["id"]
    except Exception:
        pass

    # If not found, get all users and search
    try:
        all_users_response = requests.get(f"{API_ENDPOINT}/users", headers=headers, params={"page_size": 100})
        if all_users_response.status_code == 200:
            all_users = all_users_response.json()
            for user in all_users:
                if user.get("username") == username:
                    return user["id"]
    except Exception as e:
        print(f"❌ Error getting user {username}: {e}")

    return None


def get_complete_spec_stories(auth_token, project_id):
    """Get all Complete SPEC stories from project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
        response = requests.get(url, headers=headers, params={"page_size": 500})
        if response.status_code == 200:
            all_stories = response.json()
            complete_spec_stories = [
                s for s in all_stories if "Complete" in s.get("subject", "") and "SPEC-" in s.get("subject", "").upper()
            ]
            return complete_spec_stories
        return []
    except Exception as e:
        print(f"❌ Error getting stories: {e}")
        return []


def reassign_story(auth_token, story_id, user_id, dry_run=False):
    """Reassign a story to a user."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Get current story to get version
    story_url = f"{API_ENDPOINT}/userstories/{story_id}"
    story_response = requests.get(story_url, headers=headers)

    if story_response.status_code != 200:
        return False

    story = story_response.json()
    version = story.get("version", 1)

    if dry_run:
        print(f"  [DRY RUN] Would reassign US#{story.get('ref')} to Developer C")
        return True

    # Update assignment
    patch_data = {"assigned_to": user_id, "version": version}

    patch_response = requests.patch(story_url, headers=headers, json=patch_data)
    return patch_response.status_code in [200, 204]


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Bulk reassign Complete SPEC stories to Developer C")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    args = parser.parse_args()

    print("=" * 80)
    print("🔄 Bulk Reassign Complete SPEC Stories to Developer C")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project
    print("2️⃣  Getting ninaivalaigal project...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print(f"❌ Project '{PROJECT_SLUG}' not found. Exiting.")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer C - try both username formats and verify
    print("3️⃣  Getting Developer C user ID...")
    developer_c_id = None

    # Try developer-c first
    for username_variant in ["developer-c", "developer_c"]:
        found_id = get_user_id(auth_token, username_variant)
        if found_id:
            # Verify it's actually Developer C
            user_response = requests.get(
                f"{API_ENDPOINT}/users", headers={"Authorization": f"Bearer {auth_token}"}, params={"page_size": 100}
            )
            if user_response.status_code == 200:
                all_users = user_response.json()
                for user in all_users:
                    if user.get("id") == found_id:
                        if user.get("username") == username_variant:
                            developer_c_id = found_id
                            print(f"✅ Found Developer C: {username_variant} (ID {found_id})")
                            break
                if developer_c_id:
                    break

    if not developer_c_id:
        # Last resort: directly use ID 8 (known Developer C ID)
        print("⚠️  Could not find via username lookup, using known Developer C ID: 8")
        developer_c_id = 8

    print(f"✅ Using Developer C ID: {developer_c_id}")
    print()

    # Get Complete SPEC stories
    print("4️⃣  Getting Complete SPEC stories...")
    complete_spec_stories = get_complete_spec_stories(auth_token, project_id)
    print(f"✅ Found {len(complete_spec_stories)} Complete SPEC stories")
    print()

    if not complete_spec_stories:
        print("🎉 No Complete SPEC stories to reassign!")
        return

    # Filter stories that need reassignment (not already assigned to Developer C)
    stories_to_reassign = [s for s in complete_spec_stories if s.get("assigned_to") != developer_c_id]

    print(f"5️⃣  Stories needing reassignment: {len(stories_to_reassign)}")
    if len(stories_to_reassign) < len(complete_spec_stories):
        already_assigned = len(complete_spec_stories) - len(stories_to_reassign)
        print(f"   Already assigned to Developer C: {already_assigned}")
    print()

    if not stories_to_reassign:
        print("🎉 All Complete SPEC stories are already assigned to Developer C!")
        return

    # Display sample
    print("=" * 80)
    print(f"📋 Stories to reassign ({len(stories_to_reassign)}):")
    print("=" * 80)
    for story in stories_to_reassign[:10]:
        print(f"  US#{story.get('ref')}: {story.get('subject', '')[:60]}")
    if len(stories_to_reassign) > 10:
        print(f"  ... and {len(stories_to_reassign) - 10} more")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No stories will be reassigned")
        return

    # Confirm
    response = input(f"Reassign {len(stories_to_reassign)} stories to Developer C? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("⏭️  Cancelled.")
        return

    # Reassign stories
    print()
    print("=" * 80)
    print(f"6️⃣  Reassigning {len(stories_to_reassign)} stories...")
    print("=" * 80)
    print()

    reassigned = 0
    failed = 0

    for idx, story in enumerate(stories_to_reassign, 1):
        story_ref = story.get("ref")
        story_id = story.get("id")

        if idx % 10 == 0 or idx <= 5:
            print(f"[{idx}/{len(stories_to_reassign)}] US#{story_ref}")

        if reassign_story(auth_token, story_id, developer_c_id, dry_run=False):
            reassigned += 1
            if idx <= 5:
                print(f"  ✅ Reassigned")
        else:
            failed += 1
            if idx <= 5:
                print(f"  ❌ Failed")

    # Summary
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Reassigned: {reassigned} stories")
    print(f"❌ Failed: {failed} stories")
    print()

    if reassigned > 0:
        print(f"🎉 {reassigned} Complete SPEC stories are now assigned to Developer C!")
        print("   Filter by 'Developer C' in ninaivalaigal to see them all.")


if __name__ == "__main__":
    main()
