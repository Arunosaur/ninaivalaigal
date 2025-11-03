#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign US#558 to Developer G
"""

import os
import sys
from datetime import datetime

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
DEVELOPER_G_USERNAME = "developer-g"


def authenticate():
    """Authenticate with Taiga."""
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
    """Get project ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_user_id(auth_token, username):
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                user_username = user.get("username", "").lower()
                full_name = user.get("full_name", "").lower() if user.get("full_name") else ""

                if username.lower() in user_username or username.lower() in full_name:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Try direct fetch by ref first
    url = f"{API_ENDPOINT}/userstories/by_ref"
    params = {"project": project_id, "ref": story_ref}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            story = response.json()
            return story
    except Exception:
        pass

    # Fallback: List all stories and search
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            stories = response.json()
            for story in stories:
                if story.get("ref") == story_ref or str(story.get("ref")) == str(story_ref):
                    return story
        return None
    except Exception as e:
        print(f"❌ Error finding story: {e}")
        return None


def get_project_members(auth_token, project_id):
    """Get all project members."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/memberships?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Error getting project members: {e}")
        return []


def get_roles(auth_token, project_id):
    """Get project roles."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/roles?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            roles = response.json()
            # Return first role ID (usually "Member" or similar)
            if roles:
                return roles[0].get("id")
        return None
    except Exception as e:
        print(f"⚠️  Error getting roles: {e}")
        return None


def add_user_to_project(auth_token, project_id, user_id, username=None):
    """Add user to project as a member."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/memberships"

    # Get a role ID (use default member role)
    role_id = get_roles(auth_token, project_id)
    if not role_id:
        print("⚠️  Could not get role ID - will try without it")

    # Check if user is already a member
    members = get_project_members(auth_token, project_id)
    for member in members:
        member_user = member.get("user")
        if member_user:
            # Handle different response formats
            if isinstance(member_user, dict):
                if member_user.get("id") == user_id:
                    print(f"✅ User is already a project member (Membership ID: {member.get('id')})")
                    return True
            elif isinstance(member_user, int) and member_user == user_id:
                print(f"✅ User is already a project member (Membership ID: {member.get('id')})")
                return True

    # Add user to project
    # Taiga API requires email or username to add a member
    # We'll use the username we found
    data = {
        "project": project_id,
        "role": role_id,
    }

    # Try with username first (more reliable)
    if username:
        # Get user details to find email
        user_url = f"{API_ENDPOINT}/users/{user_id}"
        user_response = requests.get(user_url, headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            # Try using username in the membership request
            # Some Taiga versions accept username instead of email
            try:
                # Try username first
                membership_data = {
                    "project": project_id,
                    "username": username,
                    "role": role_id,
                }
                response = requests.post(url, headers=headers, json=membership_data)
                if response.status_code in [200, 201]:
                    print(f"✅ Added user to project via username")
                    return True
            except:
                pass

            # Try email with username if available
            email = user_data.get("email")
            if email:
                membership_data = {
                    "project": project_id,
                    "email": email,
                    "username": username,  # Include username as required by API
                    "role": role_id,
                }
                response = requests.post(url, headers=headers, json=membership_data)
                if response.status_code in [200, 201]:
                    print(f"✅ Added user to project via email+username")
                    return True
                else:
                    print(f"⚠️  Failed to add via email+username: {response.status_code} - {response.text[:200]}")

    print("⚠️  Could not add user to project via API")
    return False


def assign_story(auth_token, story_id, story_version, assignee_id):
    """Assign story to user."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {
        "version": story_version,
        "assigned_to": assignee_id,
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code in [200, 204]:
            return True
        else:
            error_text = response.text
            print(f"   Response status: {response.status_code}")
            print(f"   Response body: {error_text[:200]}")

            # Check if error is about project membership
            if "project member" in error_text.lower():
                print("\n⚠️  Developer G is not a project member.")
                print("   To fix this:")
                print("   1. Go to Taiga project settings")
                print("   2. Add Developer G as a project member")
                print("   3. Run this script again")
                print("\n   OR manually assign in Taiga UI:")
                print(f"   http://localhost:9000/project/ninaivalaigal/us/558")

            return False
    except Exception as e:
        print(f"❌ Error assigning story: {e}")
        return False


def main():
    """Assign US#558 to Developer G."""
    print("=" * 60)
    print("Assigning US#558 to Developer G")
    print("=" * 60)

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")

    # Get project
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")

    # Find story
    print(f"🔍 Searching for story US#558...")
    story = find_story_by_ref(auth_token, project_id, 558)
    if not story:
        print("❌ Story US#558 not found")
        return 1
    print(f"✅ Found story: {story.get('subject', 'N/A')} (ID: {story['id']}, Ref: {story.get('ref')})")

    # Get Developer G user ID
    print(f"🔍 Searching for user '{DEVELOPER_G_USERNAME}'...")
    developer_g_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)

    if not developer_g_id:
        print(f"⚠️  User '{DEVELOPER_G_USERNAME}' not found")
        print("   Attempting to find by alternative methods...")

        # Try common variations
        alternatives = ["developer_g", "developerG", "Developer G", "developer g"]
        for alt in alternatives:
            dev_id = get_user_id(auth_token, alt)
            if dev_id:
                developer_g_id = dev_id
                print(f"✅ Found user by alternative name: '{alt}'")
                break

        if not developer_g_id:
            print("❌ Developer G user not found")
            print("   Story will not be assigned (but story exists and can be manually assigned)")
            print(f"   Current assignee: {story.get('assigned_to')}")
            return 1

    print(f"✅ Found Developer G (User ID: {developer_g_id})")

    # Check if Developer G is a project member, add if not
    print(f"\n🔍 Checking if Developer G is a project member...")
    members = get_project_members(auth_token, project_id)
    is_member = False
    for member in members:
        # Handle different response formats
        member_user = member.get("user")
        if member_user:
            # If user is a dict, get id from it
            if isinstance(member_user, dict):
                if member_user.get("id") == developer_g_id:
                    is_member = True
                    print(f"✅ Developer G is already a project member")
                    break
            # If user is an int (user ID directly)
            elif isinstance(member_user, int) and member_user == developer_g_id:
                is_member = True
                print(f"✅ Developer G is already a project member")
                break

    if not is_member:
        print(f"⚠️  Developer G is not a project member. Adding now...")
        # Get username for membership creation
        user_url = f"{API_ENDPOINT}/users/{developer_g_id}"
        headers = {"Authorization": f"Bearer {auth_token}"}
        user_response = requests.get(user_url, headers=headers)
        username = DEVELOPER_G_USERNAME
        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data.get("username", DEVELOPER_G_USERNAME)

        member_added = add_user_to_project(auth_token, project_id, developer_g_id, username)
        if not member_added:
            print("\n⚠️  Could not add Developer G to project via API.")
            print("   Please add Developer G to the project manually:")
            print(f"   1. Go to: http://localhost:9000/project/ninaivalaigal/admin/project-profile/members")
            print(f"   2. Add Developer G as a member")
            print(f"   3. Then run this script again or assign manually")
            return 1

    # Assign story
    print(f"\n📝 Assigning story to Developer G...")
    success = assign_story(auth_token, story["id"], story["version"], developer_g_id)

    if success:
        print("✅ Story US#558 successfully assigned to Developer G!")
        print(f"   Story ID: {story['id']}")
        print(f"   Assigned to User ID: {developer_g_id}")
        return 0
    else:
        print("❌ Failed to assign story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
