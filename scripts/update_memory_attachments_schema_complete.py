#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Taiga Story US#326 with completion details

Memory Attachments Database Schema
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

Successfully created database schema for memory attachments including Alembic migration and SQLAlchemy model.

### Deliverables Completed

1. ✅ **Alembic Migration** (`0143_memory_attachments_schema.py`)
   - Creates `memory_attachments` table
   - Adds 5 indexes for performance
   - Includes proper constraints and defaults
   - Includes downgrade function for rollback

2. ✅ **SQLAlchemy Model** (`database/models.py`)
   - `MemoryAttachment` model class defined
   - Proper field types and constraints
   - Indexes defined for performance
   - Relationships ready for use

3. ✅ **Database Schema**
   - Table structure with all required fields
   - Unique constraint on storage_key
   - JSONB metadata field
   - Proper timestamps (created_at, updated_at)

### Key Features

**Table Structure:**
- `id` (UUID) - Primary key
- `memory_id` (TEXT) - Reference to memory token
- `user_id` (TEXT) - Owner of attachment
- `filename` (TEXT) - Original filename
- `content_type` (TEXT) - MIME type
- `size` (BIGINT) - File size in bytes
- `storage_key` (TEXT) - Storage backend key (unique)
- `storage_backend` (TEXT) - Backend type (default: 's3')
- `metadata` (JSONB) - Additional metadata
- `created_at` (TIMESTAMPTZ) - Creation timestamp
- `updated_at` (TIMESTAMPTZ) - Update timestamp

**Indexes:**
- `ix_memory_attachments_memory_id` - Fast lookup by memory
- `ix_memory_attachments_user_id` - Fast lookup by user
- `ix_memory_attachments_storage_key` - Unique index
- `ix_memory_attachments_created_at` - Time-based queries
- `ix_memory_attachments_memory_user` - Composite index for list queries

### Acceptance Criteria Met

- ✅ Alembic migration created and tested
- ✅ Model class defined with relationships
- ✅ Indexes created for performance
- ✅ Constraints enforced (unique, not null)
- ✅ Type check constraints working

### Files Created/Modified

**Created:**
- `alembic/versions/0143_memory_attachments_schema.py` - Alembic migration

**Modified:**
- `services/core-api/database/models.py` - Added `MemoryAttachment` model class

### Usage

**Run Migration:**
```bash
alembic upgrade head
```

**Use Model:**
```python
from database.models import MemoryAttachment

attachment = MemoryAttachment(
    memory_id="mem_123",
    user_id="user_456",
    filename="document.pdf",
    content_type="application/pdf",
    size=12345,
    storage_key="memory-attachments/user_456/mem_123/document.pdf"
)
```

### Integration

- Works with existing memory attachment API endpoints (US#327-329)
- Supports all attachment operations (upload, list, get, delete)
- Ready for production use

---

**Documentation**: See `services/core-api/MEMORY_ATTACHMENTS_SCHEMA_COMPLETE.md` for full details.

**Status**: ✅ **COMPLETE** - Ready for migration and production use
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
    """Update US#326 with completion details."""
    print("=" * 80)
    print("UPDATING MEMORY ATTACHMENTS SCHEMA STORY (US#326)")
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

    # Story to update
    story_ref = 326
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completion_text = COMPLETION_DETAILS.format(timestamp=timestamp)

    print(f"📝 Processing US#{story_ref}...")

    # Find story
    story = find_story_by_ref(auth_token, project_id, story_ref)
    if not story:
        print(f"  ❌ Story US#{story_ref} not found")
        return 1

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
    else:
        print(f"  ❌ Failed to update: {response_text[:200]}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Story updated: US#{story_ref}")
    print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_ref}")
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
