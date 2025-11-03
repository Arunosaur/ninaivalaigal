#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Update Taiga story US#565 for SPEC-083

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


def update_story(auth_token, project_id, story_id, version, new_status_id):
    """Update Taiga story US#565 for SPEC-083."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    new_subject = "SPEC-083: Product Surface Split and Naming"
    new_description = (
        "Product surface split and naming specification for separating Customer App and "
        "Admin Console, establishing canonical naming conventions, and defining clear "
        "boundaries between public and internal surfaces.\n\n"
        "**Key Features:**\n"
        "- Two Separate Apps: Customer App (end-user) and Admin Console (internal/operational)\n"
        "- Canonical Naming: Standardized naming conventions across code, URLs, and documentation\n"
        "- Clear Scope Boundaries: Customer App vs Admin Console responsibilities and non-goals\n"
        "- Routing & URLs: Separate hosts (app.<domain> vs admin.<domain>) with distinct routing\n"
        "- Monorepo Structure: Separate apps with shared packages (UI, charts, auth, API clients)\n"
        "- OpenAPI Split: Public API (customer) vs Internal API (admin) with proper gating\n"
        "- Auth & RBAC: Distinct OAuth clients and JWT audiences for each surface\n"
        "- Deployment Isolation: Customer App exposed publicly, Admin Console on Tailnet/SSO only\n"
        "- CI Guardrails: Policy tests to prevent public/internal surface drift\n\n"
        "**Canonical Names:**\n"
        '- **Customer App**: End-user experience (formerly "UI," "public app")\n'
        '- **Admin Console**: Internal/operational surface (replaces "Vendor Console")\n\n'
        "**Status:** Planned\n"
        "**Phase:** Phase 3\n"
        "**Category:** Architecture & Organization\n"
        "**Priority:** Medium\n\n"
        "**Dependencies:** SPEC-087 (API Surface Contracts), SPEC-084 (Agentic UI Testing)\n\n"
        '**Historical Note:** The original SPEC-083 "Predictive Analytics / AI Middleware" '
        "functionality was merged into SPEC-038 (Memory Token Preloading System). "
        "This SPEC-083 now covers Product Surface Split and Naming."
    )

    update_data = {
        "version": version,
        "subject": new_subject,
        "description": new_description,
        "status": new_status_id,
    }

    try:
        response = requests.patch(url, headers=headers, json=update_data)
        if response.status_code == 200:
            story = response.json()
            ref = story.get("ref", "N/A")
            subject = story.get("subject", "N/A")
            status_info = story.get("status_extra_info", {})
            status = status_info.get("name", "Unknown") if status_info else "Unknown"
            print(f"✅ Successfully updated story US#{ref}: {subject}")
            print(f"   Status: {status}")
            return story
        else:
            print(f"❌ Failed to update story: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return None


def main():
    """Main execution."""
    print("🚀 Updating Taiga story US#565 for SPEC-083")
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

    # Get US#565
    headers = {"Authorization": f"Bearer {auth_token}"}
    stories_response = requests.get(
        f"{API_ENDPOINT}/userstories?project={project_id}",
        headers=headers,
        params={"page_size": 1000},
    )
    if stories_response.status_code != 200:
        print("❌ Failed to get stories")
        sys.exit(1)

    all_stories = stories_response.json()
    story_565 = next((s for s in all_stories if s.get("ref") == 565), None)

    if not story_565:
        print("❌ US#565 not found")
        sys.exit(1)

    story_id = story_565.get("id")
    version = story_565.get("version", 1)
    current_subject = story_565.get("subject", "")
    current_status_id = story_565.get("status", "")

    print(f"📋 Current: {current_subject}")
    print(f"   Story ID: {story_id}, Version: {version}")
    print(f"   Current Status ID: {current_status_id}")
    print()

    # Get "Ready" or "New" status ID
    ready_status_id = get_status_id(auth_token, project_id, "Ready")
    new_status_id = get_status_id(auth_token, project_id, "New")
    update_status_id = new_status_id or ready_status_id

    if current_status_id == 5:  # Done status
        print('⚠️  Story is marked "Done" but SPEC is Planned')
        print('   Updating status to "Ready/New" and correcting subject...')
    else:
        update_status_id = current_status_id

    if not update_status_id:
        print("❌ Failed to get Ready/New status ID")
        sys.exit(1)

    # Update story
    story = update_story(auth_token, project_id, story_id, version, update_status_id)
    if story:
        print("\n✅ Story update complete!")
        sys.exit(0)
    else:
        print("\n❌ Story update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
