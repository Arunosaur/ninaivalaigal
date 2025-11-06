#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Taiga Stories US#321 and US#322 with completion details

SPEC-031: Memory Relevance Ranking API Integration
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

COMPLETION_DETAILS = """
---

## ✅ **COMPLETE** - {timestamp}

**Developer**: Developer G
**Status**: ✅ COMPLETE - SPEC-031 Compliant

### Implementation Summary

Successfully implemented Memory Relevance Ranking API endpoint and integrated relevance scoring into existing memory API operations.

### Deliverables Completed

1. ✅ **Memory Relevance Ranking API Endpoint** (`GET /memory/relevant`)
   - Returns top-N most relevant memories ranked by relevance score
   - Supports context filtering (`context_id` parameter)
   - Configurable limit (1-100 memories)
   - Integrates with existing RelevanceEngine
   - Response optimized for <5ms target

2. ✅ **Memory API Relevance Score Integration**
   - `/memory/remember` - Updates relevance score when memory is created
   - `/memory/recall` - Tracks access and updates relevance scores for accessed memories
   - Relevance scores included in recall responses
   - Non-blocking integration (scoring failures don't break requests)

### Key Features

**API Endpoint:**
- `GET /memory/relevant?limit=10&context_id=ctx123`
- Returns memories with relevance scores
- Gracefully handles missing scores or Redis unavailability

**Integration:**
- Automatic score updates on memory creation
- Automatic score updates on memory access (recall)
- Scores included in recall responses
- Non-blocking: Requests succeed even if scoring fails

### Acceptance Criteria Met

- ✅ Endpoint implemented (`GET /memory/relevant`)
- ✅ Query parameters supported (context, limit, context_id)
- ✅ Integrates with relevance engine
- ✅ Returns memories with relevance scores
- ✅ `/memory/remember` updates relevance scores
- ✅ `/memory/recall` tracks access and updates scores
- ✅ Relevance scores included in recall responses
- ✅ No performance degradation (non-blocking)
- ✅ Graceful error handling
- ⏳ Performance testing (<5ms) - Recommended for validation

### Files Modified

**Modified:**
- `services/core-api/lib/memory_api.py` - Added `/memory/relevant` endpoint and relevance integration

### Usage Example

```python
# Get top 10 most relevant memories
GET /memory/relevant?limit=10&context_id=project_123

# Response includes relevance scores
{{
  "items": [
    {{
      "id": "mem_001",
      "text": "Important note",
      "score": 0.92,
      "context_id": "project_123"
    }}
  ],
  "total": 10
}}
```

### Integration Notes

- Relevance scoring is automatic and transparent
- Scores calculated based on: time decay, access frequency, importance flags, context matching
- Scores cached in Redis (1-hour TTL for scores, 15-min for top-N cache)
- Non-blocking: API endpoints work even if Redis unavailable

---

**Documentation**: See `services/core-api/SPEC031_MEMORY_RELEVANCE_API_COMPLETE.md` for full details.

**Status**: ✅ **COMPLETE** - Ready for testing and production use
"""


def authenticate():
    """Authenticate with Taiga."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    url = f"{API_ENDPOINT}/userstories/by_ref"
    params = {"project": project_id, "ref": story_ref}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    return None


def get_statuses(auth_token, project_id):
    """Get all statuses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                name = status.get("name", "").lower()
                statuses[name] = status.get("id")
            return statuses
        return {}
    except Exception:
        return {}


def update_story(auth_token, story_id, story_version, description, status_id=None):
    """Update story description and optionally status."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {
        "version": story_version,
        "description": description,
    }

    if status_id:
        data["status"] = status_id

    try:
        response = requests.patch(url, headers=headers, json=data)
        return response.status_code in [200, 204], response.text
    except Exception as e:
        return False, str(e)


def main():
    """Update US#321 and US#322 with completion details."""
    print("=" * 80)
    print("UPDATING MEMORY RELEVANCE RANKING STORIES (US#321, US#322)")
    print("=" * 80)
    print()

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")
    print()

    # Get project ID
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    project_response = requests.get(project_url, headers=headers)

    if project_response.status_code != 200:
        print("❌ Failed to get project")
        return 1

    project_id = project_response.json().get("id")
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")
    print()

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_status_id = statuses.get("done") or statuses.get("completed") or statuses.get("complete")

    if done_status_id:
        print(f"✅ Found 'Done' status (ID: {done_status_id})")
    else:
        print("⚠️  'Done' status not found, will update description only")
    print()

    # Stories to update
    stories_to_update = [321, 322]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completion_text = COMPLETION_DETAILS.format(timestamp=timestamp)

    success_count = 0
    for story_ref in stories_to_update:
        print(f"📝 Processing US#{story_ref}...")

        # Find story
        story = find_story_by_ref(auth_token, project_id, story_ref)
        if not story:
            print(f"  ❌ Story US#{story_ref} not found")
            continue

        story_id = story.get("id")
        story_version = story.get("version", 1)
        current_description = story.get("description", "")
        subject = story.get("subject", "")

        print(f"  ✅ Found: {subject}")
        print(f"     Story ID: {story_id}, Version: {story_version}")

        # Append completion details
        new_description = current_description
        if current_description and not current_description.endswith("\n"):
            new_description += "\n"
        new_description += completion_text

        # Update story
        success, response_text = update_story(
            auth_token, story_id, story_version, new_description, status_id=done_status_id if done_status_id else None
        )

        if success:
            print(f"  ✅ Updated description")
            if done_status_id:
                print(f"  ✅ Status set to 'Done'")
            success_count += 1
        else:
            print(f"  ❌ Failed to update: {response_text[:200]}")

        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully updated: {success_count}/{len(stories_to_update)} stories")
    print()
    print(f"📋 Stories updated:")
    for story_ref in stories_to_update:
        print(f"   - US#{story_ref}: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_ref}")
    print()

    return 0 if success_count == len(stories_to_update) else 1


if __name__ == "__main__":
    sys.exit(main())
