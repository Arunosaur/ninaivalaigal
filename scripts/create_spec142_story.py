#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga story for SPEC-142: Offline Mode
#
# Usage:
#     python3 scripts/create_spec142_story.py

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
    """Get project ID for ninaivalaigal project."""
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


def get_status_id(auth_token, project_id, status_name):
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = response.json()
            for status in statuses:
                if status.get("name", "").lower() == status_name.lower():
                    return status.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return None


def create_story(auth_token, project_id, ready_status_id):
    """Create Taiga story for SPEC-142: Offline Mode."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"

    story_data = {
        "project": project_id,
        "subject": "SPEC-142: Offline Mode",
        "description": (
            "Comprehensive offline mode support enabling the platform to function "
            "seamlessly without network connectivity. This SPEC provides offline-first "
            "architecture for web, desktop, and mobile applications.\n\n"
            "**Key Features:**\n"
            "- Offline-First Architecture: Local-first data storage and operations\n"
            "- Local Data Storage: Encrypted local database (IndexedDB/SQLite)\n"
            "- Operation Queue: Queue all mutations while offline, sync when connected\n"
            "- Conflict Resolution: Intelligent conflict detection and resolution\n"
            "- Background Sync: Automatic synchronization when connectivity restored\n"
            "- Offline Indicators: Clear UI indicators showing offline status\n\n"
            "**Status:** Planned\n"
            "**Phase:** Phase 4\n"
            "**Category:** Infrastructure\n"
            "**Priority:** High\n\n"
            "**Dependencies:** SPEC-001 (Core Memory System), SPEC-042 (Memory "
            "Synchronization), SPEC-044 (Cross-Device Session Continuity), SPEC-075 "
            "(Unified Frontend Architecture), SPEC-081 (Progressive Web App), SPEC-141 "
            "(Mobile App Support)"
        ),
        "status": ready_status_id,
        "tags": [
            ["spec-142", None],
            ["offline-mode", None],
            ["offline", None],
            ["infrastructure", None],
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=story_data)
        if response.status_code == 201:
            story = response.json()
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            print(f"✅ Successfully created story US#{ref}: {subject}")
            return story
        else:
            print(f"❌ Failed to create story: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        return None


def main():
    """Main execution."""
    print("🚀 Creating Taiga story for SPEC-142: Offline Mode")
    print("=" * 60)

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed")
        sys.exit(1)

    # Get project ID
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Failed to get project ID")
        sys.exit(1)

    # Get "Ready" or "New" status ID
    ready_status_id = get_status_id(auth_token, project_id, "Ready")
    if not ready_status_id:
        ready_status_id = get_status_id(auth_token, project_id, "New")

    if not ready_status_id:
        print("❌ Failed to get Ready/New status ID")
        sys.exit(1)

    # Create story
    story = create_story(auth_token, project_id, ready_status_id)
    if story:
        print("\n✅ Story creation complete!")
        sys.exit(0)
    else:
        print("\n❌ Story creation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
