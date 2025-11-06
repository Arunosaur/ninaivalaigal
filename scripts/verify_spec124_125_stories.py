#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Verify and update Taiga stories for SPEC-124 and SPEC-125

This script:
1. Checks if US#79, US#596 (SPEC-124) exist and marks them obsolete
2. Checks if US#80, US#597 (SPEC-125) exist and updates their status
"""

import os
import sys
from typing import Dict, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"


def get_auth_token() -> Optional[str]:
    """Authenticate with Taiga and get auth token"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
        )
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error authenticating: {e}")
        return None


def get_project(token: str) -> Optional[Dict]:
    """Get project by slug"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Project not found: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_story_by_ref(token: str, project_id: int, story_ref: int) -> Optional[Dict]:
    """Get story by reference number"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_ENDPOINT}/userstories", headers=headers, params={"project": project_id, "ref": story_ref}
        )
        if response.status_code == 200:
            stories = response.json()
            if stories:
                return stories[0]
        return None
    except Exception as e:
        print(f"❌ Error getting story #{story_ref}: {e}")
        return None


def get_statuses(token: str, project_id: int) -> Dict[str, int]:
    """Get all statuses for the project"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/userstory-statuses", headers=headers, params={"project": project_id})
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                statuses[status["name"].lower()] = status["id"]
            return statuses
        return {}
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def update_story_obsolete(token: str, story: Dict, deprecation_note: str) -> bool:
    """Update story to mark as obsolete"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        # Get current description
        current_desc = story.get("description", "")

        # Add deprecation note
        new_desc = current_desc
        if current_desc and not current_desc.endswith("\n"):
            new_desc += "\n"
        new_desc += f"\n\n---\n**DEPRECATED - {deprecation_note}**\n"

        # Try to find "Obsolete" or "Cancelled" status
        project_id = story.get("project")
        statuses = get_statuses(token, project_id)

        # Update story
        update_data = {"description": new_desc, "version": story.get("version", 1)}

        # Try to set status to obsolete/cancelled if available
        for status_name in ["obsolete", "cancelled", "closed", "archived"]:
            if status_name in statuses:
                update_data["status"] = statuses[status_name]
                break

        response = requests.patch(f'{API_ENDPOINT}/userstories/{story["id"]}', headers=headers, json=update_data)

        if response.status_code in [200, 204]:
            print(f"✅ Story #{story['ref']} updated successfully")
            return True
        else:
            print(f"⚠️  Failed to update story #{story['ref']}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error updating story #{story['ref']}: {e}")
        return False


def add_comment(token: str, story: Dict, comment: str) -> bool:
    """Add comment to story"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f'{API_ENDPOINT}/userstories/{story["id"]}/comments', headers=headers, json={"comment": comment}
        )
        if response.status_code in [200, 201]:
            print(f"✅ Comment added to story #{story['ref']}")
            return True
        else:
            print(f"⚠️  Failed to add comment: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error adding comment: {e}")
        return False


def verify_spec124_stories(token: str, project_id: int):
    """Verify and update SPEC-124 stories (US#79, US#596)"""
    print("\n" + "=" * 70)
    print("SPEC-124 Stories (Deprecation)")
    print("=" * 70)

    deprecation_note = "SPEC-124 deprecated (November 2025). Superseded by SPEC-016 (CI/CD Pipeline Architecture)."
    comment = "SPEC-124 deprecated; CI/CD covered by SPEC-016 (2025-11-05 architectural decision)."

    stories_to_check = [79, 596]

    for story_ref in stories_to_check:
        print(f"\n📋 Checking US#{story_ref}...")
        story = get_story_by_ref(token, project_id, story_ref)

        if story:
            print(f"✅ Found US#{story['ref']}: {story.get('subject', 'No subject')}")
            print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")

            # Check if already marked obsolete
            desc = story.get("description", "")
            if "DEPRECATED" in desc or "deprecated" in desc:
                print(f"   ⚠️  Story already marked as deprecated")
                response = input("   Update anyway? (y/N): ")
                if response.lower() != "y":
                    continue

            # Update story
            if update_story_obsolete(token, story, deprecation_note):
                add_comment(token, story, comment)
        else:
            print(f"❌ Story US#{story_ref} not found")


def verify_spec125_stories(token: str, project_id: int):
    """Verify SPEC-125 stories (US#80, US#597)"""
    print("\n" + "=" * 70)
    print("SPEC-125 Stories (Verification)")
    print("=" * 70)

    stories_to_check = [80, 597]

    for story_ref in stories_to_check:
        print(f"\n📋 Checking US#{story_ref}...")
        story = get_story_by_ref(token, project_id, story_ref)

        if story:
            print(f"✅ Found US#{story['ref']}: {story.get('subject', 'No subject')}")
            print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"   Assigned to: {story.get('assigned_to_extra_info', {}).get('full_name_display', 'Unassigned')}")
            print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story['ref']}")
        else:
            print(f"❌ Story US#{story_ref} not found")
            print(f"   Note: Story may need to be created for SPEC-125 implementation")


def main():
    """Main function"""
    print("=" * 70)
    print("SPEC-124 & SPEC-125 Story Verification")
    print("=" * 70)

    # Authenticate
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Exiting.")
        return 1

    print("✅ Authenticated successfully")

    # Get project
    print(f"\n📁 Getting project '{PROJECT_SLUG}'...")
    project = get_project(token)
    if not project:
        print("❌ Project not found. Exiting.")
        return 1

    project_id = project["id"]
    print(f"✅ Project found: {project.get('name', 'Unknown')}")

    # Verify SPEC-124 stories
    verify_spec124_stories(token, project_id)

    # Verify SPEC-125 stories
    verify_spec125_stories(token, project_id)

    print("\n" + "=" * 70)
    print("✅ Verification Complete!")
    print("=" * 70)
    print("\n📋 Summary:")
    print("   - SPEC-124 stories (US#79, US#596): Marked as obsolete if found")
    print("   - SPEC-125 stories (US#80, US#597): Verified status")
    print("\n💡 Next Steps:")
    print("   - If SPEC-125 stories don't exist, create them using create_spec125_stories.py")
    print("   - Create frontend documentation structure (docs/frontend/)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
