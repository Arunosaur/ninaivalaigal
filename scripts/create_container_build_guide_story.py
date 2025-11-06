#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga story for Container Build Guide enhancement

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
                if username.lower() in user_username:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def get_statuses(auth_token, project_id):
    """Get status IDs."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            statuses = response.json()
            return {s.get("name", "").lower(): s.get("id") for s in statuses}
        return {}
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def check_existing_story(auth_token, project_id):
    """Check if story already exists."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            stories = response.json()
            keywords = ["container", "build", "guide", "documentation"]
            for story in stories:
                subject = story.get("subject", "").lower()
                if any(kw in subject for kw in keywords):
                    if "build" in subject and "guide" in subject:
                        return story
        return None
    except Exception as e:
        print(f"⚠️  Error checking existing stories: {e}")
        return None


def create_story(auth_token, project_id, user_id, status_id):
    """Create user story."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"

    subject = "Enhance Container Build Guide Documentation"
    description = """
## Container Build Guide Enhancement - COMPLETE ✅

**Task**: Enhance `docs/QUICK_CONTAINER_BUILD_GUIDE.md` with comprehensive service examples and troubleshooting

### Completed Enhancements:

1. ✅ **Added Service Examples**:
   - Admin Vendor Service build command
   - Graph Service build command
   - gRPC Gateway (Go) build command

2. ✅ **Added Port Numbers**:
   - Health check examples with correct ports for all 6 services
   - Core API (13390), Business (13391), Admin Vendor (13392)
   - Memory (13393), Graph (13394), gRPC Gateway (13395)

3. ✅ **Service-Specific Troubleshooting**:
   - Core API: Database connection, memory browser API, JWT errors
   - Memory Service (Rust): Build failures, port conflicts
   - gRPC Gateway (Go): Build failures, gRPC connection errors

4. ✅ **Improved Quick Reference Card**:
   - Added all service ports in one place
   - Better formatting for quick lookup

### Files Modified:
- `docs/QUICK_CONTAINER_BUILD_GUIDE.md` (287 lines, up from ~256)

### Status: ✅ COMPLETE

The guide now includes all 6 microservices with examples, troubleshooting, and verification steps.
"""

    notes = """
<h2>Container Build Guide Enhancement Complete</h2>

<p>✅ <strong>Documentation improvement completed</strong></p>

<h3>What Was Added:</h3>
<ul>
<li>✅ Complete service examples for all 6 microservices</li>
<li>✅ Port numbers for all services (13390-13395)</li>
<li>✅ Service-specific troubleshooting guides</li>
<li>✅ Enhanced quick reference card with all ports</li>
</ul>

<h3>Service Coverage:</h3>
<ul>
<li>✅ Core API (Python) - Port 13390</li>
<li>✅ Business Service (Python) - Port 13391</li>
<li>✅ Admin Vendor Service (Python) - Port 13392</li>
<li>✅ Memory Service (Rust) - Port 13393</li>
<li>✅ Graph Service (Python) - Port 13394</li>
<li>✅ gRPC Gateway (Go) - Port 13395</li>
</ul>

<h3>Impact:</h3>
<p>Team members can now quickly build and troubleshoot any service container with comprehensive examples and troubleshooting steps.</p>

<p><strong>Status:</strong> ✅ Complete and ready for team use</p>
"""

    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "description_html": notes,
        "assigned_to": user_id,
        "status": status_id,
        "tags": ["documentation", "container", "build-guide", "enhancement"],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ Failed to create story: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        return None


def update_story_status(auth_token, story_id, status_id):
    """Update story status to Done."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    # Get current story to preserve version
    get_response = requests.get(url, headers=headers)
    if get_response.status_code != 200:
        print(f"⚠️  Could not get story version: {get_response.status_code}")
        return False

    current_story = get_response.json()
    version = current_story.get("version", 1)

    payload = {
        "version": version,
        "status": status_id,
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


def main():
    """Create and complete the story."""
    print("=" * 60)
    print("📝 Creating Container Build Guide Story")
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

    # Check if story already exists
    print("\n🔍 Checking for existing story...")
    existing = check_existing_story(auth_token, project_id)
    if existing:
        ref = existing.get("ref", "N/A")
        subject = existing.get("subject", "Unknown")
        print(f"✅ Found existing story: US#{ref}: {subject}")
        story_id = existing.get("id")
    else:
        print("✅ No existing story found, creating new one...")

        # Get Developer G
        user_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)
        if not user_id:
            print("❌ Developer G not found")
            return 1
        print(f"✅ Found Developer G (ID: {user_id})")

        # Get statuses
        statuses = get_statuses(auth_token, project_id)
        ready_id = statuses.get("ready") or statuses.get("new")
        done_id = statuses.get("done") or statuses.get("closed")

        # Create story
        print("\n📝 Creating story...")
        story = create_story(auth_token, project_id, user_id, ready_id)

        if not story:
            print("❌ Failed to create story")
            return 1

        story_id = story.get("id")
        ref = story.get("ref", "N/A")
        print(f"✅ Created story: US#{ref}")

        # Update to Done
        if done_id:
            print(f"\n✅ Updating story status to Done...")
            if update_story_status(auth_token, story_id, done_id):
                print(f"✅ Story US#{ref} marked as Done")
            else:
                print(f"⚠️  Could not update status (story created: US#{ref})")

    print("\n" + "=" * 60)
    print("✅ Task Complete!")
    print("=" * 60)
    if existing:
        print(f"Story: US#{existing.get('ref')}")
    else:
        print(f"Story: US#{ref}")
    print(f"Documentation: docs/QUICK_CONTAINER_BUILD_GUIDE.md")
    print(f"Status: ✅ Complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
