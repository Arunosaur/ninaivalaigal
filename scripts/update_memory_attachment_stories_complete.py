#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Taiga Stories US#327, US#328, US#329 with completion details

Memory Attachment API Endpoints
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
**Status**: ✅ COMPLETE

### Implementation Summary

Successfully implemented Memory Attachment API endpoints for uploading, retrieving, and deleting attachments to memories.

### Deliverables Completed

1. ✅ **Memory Attachment Upload Endpoint** (`POST /memory/{{memory_id}}/attachments`)
   - Accepts multipart/form-data file uploads
   - Validates file type and size (max 100MB)
   - Stores files in storage backend
   - Stores attachment metadata in database
   - Generates pre-signed download URLs

2. ✅ **Memory Attachment Retrieval Endpoints**
   - `GET /memory/{{memory_id}}/attachments` - List all attachments
   - `GET /memory/{{memory_id}}/attachments/{{attachment_id}}` - Get specific attachment
   - Supports pagination
   - Returns pre-signed download URLs (1-hour expiry)

3. ✅ **Memory Attachment Deletion Endpoint** (`DELETE /memory/{{memory_id}}/attachments/{{attachment_id}}`)
   - Deletes file from storage backend
   - Removes attachment record from database
   - Enforces ACL permission checks
   - Idempotent operation

### Key Features

**Database Schema:**
- `memory_attachments` table with indexes
- Metadata stored as JSONB
- Automatic table creation

**Security:**
- ACL permission checks (users can only access their own attachments)
- File validation (size, type)
- Memory existence verification
- Pre-signed URLs with expiry

**Storage Integration:**
- Uses storage backend for file storage
- Supports S3-compatible backends
- Graceful fallback if storage unavailable

### Acceptance Criteria Met

**US#327:**
- ✅ Endpoint accepts multipart file uploads
- ✅ Files stored in storage backend
- ✅ File type and size validation
- ✅ Attachment metadata stored in database
- ✅ Pre-signed URLs generated
- ✅ ACL permission checks enforced

**US#328:**
- ✅ List endpoint returns attachments
- ✅ Single attachment endpoint working
- ✅ Pre-signed URLs generated
- ✅ ACL checks enforced
- ✅ Pagination supported

**US#329:**
- ✅ Endpoint deletes attachment
- ✅ File removed from storage
- ✅ ACL checks enforced
- ✅ Error handling
- ✅ Idempotent operation

### Files Created

**Created:**
- `services/core-api/lib/memory_attachments_api.py` - Memory attachment API endpoints
- `services/core-api/MEMORY_ATTACHMENTS_API_COMPLETE.md` - Documentation

### Usage Example

```python
# Upload attachment
files = {{'file': open('document.pdf', 'rb')}}
POST /memory/{{memory_id}}/attachments
Response: {{
  "id": "uuid",
  "filename": "document.pdf",
  "download_url": "https://presigned-url...",
  ...
}}

# List attachments
GET /memory/{{memory_id}}/attachments?limit=10
Response: {{
  "items": [...],
  "total": 10,
  "memory_id": "..."
}}

# Delete attachment
DELETE /memory/{{memory_id}}/attachments/{{attachment_id}}
Response: 204 No Content
```

### Integration Notes

- Storage backend required for file uploads
- Database table created automatically
- Pre-signed URLs expire after 1 hour
- File size limit: 100MB per attachment
- Supports multiple storage backends

---

**Documentation**: See `services/core-api/MEMORY_ATTACHMENTS_API_COMPLETE.md` for full details.

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
    """Update US#327, US#328, US#329 with completion details."""
    print("=" * 80)
    print("UPDATING MEMORY ATTACHMENT STORIES (US#327, US#328, US#329)")
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
    stories_to_update = [327, 328, 329]
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




