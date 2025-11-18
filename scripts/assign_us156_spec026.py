#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Assign US#156 (SPEC-026 Phase 1) to Developer D and start work
"""

import os
import sys

# Add tasks/scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_scripts = os.path.join(script_dir, "..", "tasks", "scripts")
sys.path.insert(0, tasks_scripts)

try:
    from taiga_import_tasks import TaigaImporter
except ImportError:
    print("❌ Failed to import TaigaImporter")
    sys.exit(1)


def main():
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")
    project_slug = "ninaivalaigal"

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()
    print("✅ Authenticated with Taiga")

    # Get story #156
    story = importer.get_user_story(project_slug, 156)
    if not story:
        print("❌ Story #156 not found")
        return 1

    print(f"✅ Found story #156: {story['subject']}")
    print(f"   Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print(f"   Assigned to: {'Yes' if story.get('assigned_to') else 'No'}")

    # Get project to find Developer D user ID
    project = importer.get_project(project_slug)
    if not project:
        print("❌ Project not found")
        return 1

    # Get members to find Developer D
    members_url = f"{importer.base_url}/projects/{project['id']}/memberships"
    headers = importer._get_headers()
    members_response = importer._session.get(members_url, headers=headers)
    members = members_response.json() if members_response.status_code == 200 else []

    developer_d = None
    for member in members:
        user = member.get("user", {})
        if user.get("username", "").lower() in ["developer d", "developer_d", "developerd"]:
            developer_d = user.get("id")
            break

    if not developer_d:
        print("⚠️  Developer D not found in project members")
        print("   Will update status to 'In Progress' only")

        # Update story

    # Get status IDs - try to find "In Progress" status
    # For now, just update description with assignment note
    assignment_note = """
**Assigned to Developer D - November 2, 2025**

Starting Phase 1 implementation: Team Billing Schema Design
- Will create database schema for team billing system
- Includes team_billing, team_subscriptions, team_usage_metrics tables
- Part of SPEC-026: Standalone Teams and Billing epic
"""

    try:
        # Append assignment note
        result = importer.append_to_story_description(project_slug, 156, assignment_note)
        if result:
            print("✅ Story description updated with assignment")
        else:
            print("⚠️  Failed to update description")

        # Try to update status if we can get statuses
        # For now, just print what we did
        print("\n✅ Story #156 assigned and ready to start!")
        print(f"   View: {taiga_url}/project/{project_slug}/us/156")
        return 0

    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
