#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Find all stories related to SPEC-139"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import re

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def get_all_user_stories(importer, project_id):
    """Get all user stories for a project"""
    headers = importer._get_headers()
    url = f"{taiga_url}/api/v1/userstories"
    params = {"project": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []


def matches_spec139(story):
    """Check if story matches SPEC-139"""
    tags = story.get("tags", [])
    description = story.get("description", "").lower()
    subject = story.get("subject", "").lower()

    # Check tags
    for tag in tags:
        tag_str = str(tag).lower()
        if isinstance(tag, list) and len(tag) > 0:
            tag_str = str(tag[0]).lower()

        if "spec-139" in tag_str or "spec139" in tag_str or "139" in tag_str:
            return True

    # Check text content
    text = f"{subject} {description}"
    if re.search(r"spec[-_]?139|spec\s*139|139", text, re.IGNORECASE):
        return True

    # Check for keywords
    keywords = [
        "rust integration",
        "memory provider",
        "factory",
        "audit reconciliation",
        "rust readiness",
        "memoryprovider",
        "use_rust_memory",
    ]

    for keyword in keywords:
        if keyword in text:
            return True

    return False


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    project = importer.get_project("ninaivalaigal")

    if not project:
        print("Project not found")
        return

    all_stories = get_all_user_stories(importer, project["id"])

    # Find SPEC-139 related stories
    spec139_stories = []
    for story in all_stories:
        if matches_spec139(story):
            spec139_stories.append(story)

    print("=" * 80)
    print("SPEC-139 RELATED STORIES")
    print("=" * 80)
    print()

    if not spec139_stories:
        print("No stories found explicitly tagged with SPEC-139")
        print()
        print("💡 SPEC-139 is about: Audit Reconciliation & Rust Integration Readiness")
        print("   - Python <-> Rust interface fixes (MemoryProvider factory)")
        print("   - Feature flag gating (USE_RUST_MEMORY)")
        print("   - CI markers and integration test setup")
        print("   - Operational readiness")
        print()
        print("Checking for stories that might relate...")
        return

    # Group by status
    by_status = {}
    for story in spec139_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

    # Show by status
    status_order = ["New", "Ready", "In progress", "In Progress", "Review/QA", "Done", "Archived"]
    for status in status_order:
        if status in by_status:
            stories = by_status[status]
            print(f"{status.upper()} ({len(stories)} stories):")
            print("-" * 80)

            for story in sorted(stories, key=lambda x: x.get("ref", 9999)):
                ref = story.get("ref", "N/A")
                subject = story.get("subject", "N/A")
                assigned_info = story.get("assigned_to_extra_info")
                assigned = assigned_info.get("full_name", "Unassigned") if assigned_info else "Unassigned"
                priority = {1: "Low", 2: "Normal", 3: "High"}.get(story.get("priority", 2), "Normal")
                created = story.get("created_date", "")[:10] if story.get("created_date") else "Unknown"

                print(f"  US#{ref:3d} [{priority:6s}] [{assigned:20s}] {created}")
                print(f"     {subject}")

                # Show description preview
                desc = story.get("description", "")
                if desc:
                    desc_preview = desc.replace("\n", " ")[:100]
                    print(f"     {desc_preview}...")
                print()

    print("=" * 80)
    print(f"Total: {len(spec139_stories)} SPEC-139 related stories")
    print("=" * 80)


if __name__ == "__main__":
    main()
