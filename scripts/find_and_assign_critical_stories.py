#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Find and assign most pressing stories based on priority analysis
"""

import json
import sys

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        sys.exit(1)
    return auth.json()["auth_token"], auth.json()


def get_all_stories(auth_token, project_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []


def get_statuses(auth_token, project_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def assign_and_start(auth_token, story_id, user_id, status_id):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    payload = {"assigned_to": user_id, "status": status_id, "version": story.get("version", 1)}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def main():
    print("=" * 70)
    print("Find and Assign Most Pressing Stories")
    print("=" * 70)
    print()

    auth_token, user_data = authenticate()
    user_id = user_data["id"]
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {user_id})")
    print()

    project_id = 1  # From previous runs
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("working")

    all_stories = get_all_stories(auth_token, project_id)
    print(f"✓ Found {len(all_stories)} total stories")
    print()

    # Critical priorities based on codebase analysis
    critical_patterns = {
        "p0_security": [
            ("117", "orm", "guardrails", "security", "multi-tenant"),
            ("security", "cross-org", "data leak"),
        ],
        "p0_auth": [
            ("20", "signup", "bcrypt"),
            ("21", "login", "password"),
            ("auth", "user management"),
        ],
        "p0_rate_limiting": [
            ("rate", "limit", "security"),
        ],
        "p1_governance": [
            ("291", "deprecate"),
            ("292", "verify", "boundaries"),
            ("293", "standardize"),
        ],
        "p1_refactoring": [
            ("243", "legacy", "remove", "code"),
            ("refactor", "cleanup"),
        ],
    }

    # Analyze stories
    categorized = {category: [] for category in critical_patterns.keys()}

    for story in all_stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
        text = f"{subject} {description} {' '.join(tags)}"
        status = story.get("status_extra_info", {}).get("name", "").lower()
        assigned = story.get("assigned_to")

        # Skip completed
        if status in ["done", "closed", "archived"]:
            continue

        story_info = {
            "id": story["id"],
            "ref": story.get("ref"),
            "subject": story.get("subject"),
            "status": status,
            "assigned": assigned,
        }

        # Categorize
        for category, patterns in critical_patterns.items():
            for pattern in patterns:
                if all(keyword.lower() in text for keyword in pattern):
                    if not assigned:  # Only unassigned
                        categorized[category].append(story_info)
                    break

    # Display findings
    print("=" * 70)
    print("MOST PRESSING STORIES BY CATEGORY")
    print("=" * 70)
    print()

    for category, stories in categorized.items():
        if stories:
            print(f"\n{category.upper().replace('_', ' ')}:")
            print("-" * 70)
            for s in stories[:3]:
                print(f"  Ref #{s['ref']}: {s['subject'][:55]}")
                print(f"    Status: {s['status']}")

    # Prioritize: P0 Security > P0 Auth > P0 Rate Limiting > P1
    priority_order = [
        ("p0_security", "🔴 P0 CRITICAL SECURITY"),
        ("p0_auth", "🔴 P0 BLOCKING PRODUCTION"),
        ("p0_rate_limiting", "🔴 P0 SECURITY"),
        ("p1_governance", "🟡 P1 GOVERNANCE"),
        ("p1_refactoring", "🟡 P1 TECHNICAL DEBT"),
    ]

    next_stories = []
    for category, label in priority_order:
        stories = categorized.get(category, [])
        if stories:
            next_stories.extend(stories[:2])  # Top 2 from each category
            if len(next_stories) >= 5:
                break

    # Limit to top 5
    next_stories = next_stories[:5]

    print()
    print("=" * 70)
    print("TOP 5 MOST PRESSING UNASSIGNED STORIES")
    print("=" * 70)
    print()

    if next_stories:
        for i, story in enumerate(next_stories, 1):
            print(f"{i}. Ref #{story['ref']}: {story['subject'][:55]}")
            print(f"   Status: {story['status']}")
            print()
    else:
        print("No unassigned high-priority stories found.")
        print("Checking all unassigned ready stories...")
        all_unassigned = [
            s
            for s in all_stories
            if not s.get("assigned_to") and s.get("status_extra_info", {}).get("name", "").lower() in ["ready", "new"]
        ]
        next_stories = all_unassigned[:5]

        if next_stories:
            print(f"\nFound {len(next_stories)} unassigned ready stories:")
            for i, story in enumerate(next_stories, 1):
                print(f"{i}. Ref #{story.get('ref')}: {story.get('subject', '')[:55]}")

    print()
    print("=" * 70)
    print("ASSIGNING AND STARTING MOST PRESSING STORIES")
    print("=" * 70)
    print()

    assigned_count = 0
    for story in next_stories[:3]:  # Assign top 3
        if story.get("assigned"):
            print(f"⏭️  Ref #{story['ref']}: Already assigned")
            continue

        print(f"📝 Ref #{story['ref']}: {story['subject'][:55]}")

        if assign_and_start(auth_token, story["id"], user_id, in_progress_id):
            print(f"  ✓ Assigned and moved to 'In Progress'")
            assigned_count += 1
        else:
            print(f"  ✗ Failed to assign")

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Assigned & Started: {assigned_count} stories")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 70)


if __name__ == "__main__":
    main()
