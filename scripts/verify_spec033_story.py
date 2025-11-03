#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Verify US#269 story status in Taiga for SPEC-033
"""

import sys
from pathlib import Path

import requests

# Taiga Configuration
TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"
STORY_REF = 269


def authenticate():
    """Authenticate with Taiga and return auth token"""
    url = f"{API_ENDPOINT}/auth"
    payload = {"type": "normal", "username": USERNAME, "password": PASSWORD}

    print(f"Authenticating with Taiga at {TAIGA_URL}...")
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    auth_data = response.json()
    print(f"✓ Authenticated as {auth_data.get('username')}")
    return auth_data["auth_token"]


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to get project: {response.status_code}")
        sys.exit(1)

    project = response.json()
    print(f"✓ Found project: {project['name']} (ID: {project['id']})")
    return project["id"]


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number using Taiga API"""
    url = f"{API_ENDPOINT}/userstories/by_ref"
    params = {"ref": story_ref, "project__slug": PROJECT_SLUG}
    headers = {"Authorization": f"Bearer {auth_token}"}

    print(f"\nSearching for story #{story_ref}...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        story = response.json()
        return story
    elif response.status_code == 404:
        return None
    else:
        print(f"⚠ API error: {response.status_code}")
        return None


def search_stories_by_keyword(auth_token, project_id, keyword):
    """Search stories by keyword in subject or description"""
    url = f"{API_ENDPOINT}/userstories"
    params = {"project": project_id}
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return []

    stories = response.json()
    keyword_lower = keyword.lower()

    matching = []
    for story in stories:
        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()
        if keyword_lower in subject or keyword_lower in description:
            matching.append(story)

    return matching


def main():
    print("=" * 70)
    print("SPEC-033 Taiga Story Verification - US#269")
    print("=" * 70)
    print()

    # Authenticate
    auth_token = authenticate()

    # Get project
    project_id = get_project_id(auth_token)

    # Try to find story by reference number
    story = find_story_by_ref(auth_token, project_id, STORY_REF)

    if story:
        print(f"\n✅ Found story #{story.get('ref')}: {story.get('subject')}")
        print(f"\nStory Details:")
        print(f"  - ID: {story.get('id')}")
        print(f"  - Ref: #{story.get('ref')}")
        print(f"  - Subject: {story.get('subject')}")
        print(f"  - Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
        print(f"  - URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story.get('ref')}")
        print(f"\nTags: {', '.join([t[0] if isinstance(t, list) else t for t in story.get('tags', [])])}")

        # Check if related to SPEC-033
        tags = [t[0] if isinstance(t, list) else t for t in story.get("tags", [])]
        description = story.get("description", "").lower()

        is_spec033_related = "spec-033" in tags or "redis" in description or "redis" in story.get("subject", "").lower()

        if is_spec033_related:
            print(f"\n✓ Story appears to be related to SPEC-033 (Redis Integration)")
        else:
            print(f"\n⚠ Story may not be related to SPEC-033")
            print(f"   Consider checking if this is the correct story")

        return 0
    else:
        print(f"\n❌ Story #{STORY_REF} not found in Taiga")

        # Search for related stories
        print(f"\nSearching for stories related to 'redis' or 'spec-033'...")
        redis_stories = search_stories_by_keyword(auth_token, project_id, "redis")
        spec033_stories = search_stories_by_keyword(auth_token, project_id, "spec-033")

        all_related = {s.get("ref"): s for s in redis_stories + spec033_stories}.values()

        if all_related:
            print(f"\nFound {len(all_related)} potentially related story/stories:")
            for s in sorted(all_related, key=lambda x: x.get("ref", 0))[:10]:
                print(f"  - #{s.get('ref')}: {s.get('subject')}")
                print(f"    URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{s.get('ref')}")

        print(f"\n📋 Recommendation:")
        print(f"  1. Story #{STORY_REF} does not exist in Taiga")
        print(f"  2. SPEC-033 README mentions 'Tracking: ⚠️ Retrospective (US#269)'")
        print(f"  3. Options:")
        print(f"     a. Remove mention from README (if story was never created)")
        print(f"     b. Create retrospective story documenting SPEC-033 completion")
        print(f"     c. Mark as 'completed without formal story'")

        return 1


if __name__ == "__main__":
    sys.exit(main())
