#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Story #112 (US-100: Admin Activity Logging System) with completion details.
"""

import os
import sys
from datetime import datetime

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
USERNAME = "admin"
PASSWORD = "admin123"


def authenticate():
    """Authenticate with Taiga and return auth token"""
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        print(f"❌ Authentication failed: {auth.status_code}")
        sys.exit(1)
    return auth.json()["auth_token"]


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get project: {response.status_code}")
        sys.exit(1)
    return response.json()["id"]


def get_story_by_ref(auth_token, project_id, story_ref):
    """Get story by reference number"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}&ref={story_ref}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    stories = response.json()
    if isinstance(stories, dict):
        stories = stories.get("results", [])

    return stories[0] if stories else None


def get_statuses(auth_token, project_id):
    """Get all story statuses"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def update_story(auth_token, story_id, story_version, description, status_id=None):
    """Update story description and optionally status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {"version": story_version, "description": description}

    if status_id:
        data["status"] = status_id

    response = requests.patch(url, headers=headers, json=data)
    return response.status_code in [200, 204]


def main():
    """Update Story #112 with completion details"""
    print("=" * 70)
    print("Update Story #112: Admin Activity Logging System")
    print("=" * 70)
    print()

    # Authenticate
    auth_token = authenticate()
    print("✓ Authenticated")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get story
    print("Fetching Story #112...")
    story = get_story_by_ref(auth_token, project_id, 112)
    if not story:
        print("❌ Story #112 not found")
        sys.exit(1)

    print(f"✓ Found Story #112: {story.get('subject', '')}")
    print()

    # Get current description
    current_desc = story.get("description", "") or ""

    # Completion details
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    completion_details = f"""
---

**✅ Completion Update - {timestamp}**

**Admin Activity Logging System - COMPLETE**

**What Was Implemented:**

**1. Database Schema (Migration 0130_admin_activity_logs):**
- ✅ Created `admin_activity_log` table with UUID primary keys
- ✅ Foreign key to `users` table (admin_user_id)
- ✅ Action, target_type, target_id fields for resource tracking
- ✅ JSONB details field for flexible metadata
- ✅ IP address and user agent fields for audit metadata
- ✅ Comprehensive indexes for query performance
- ✅ Partial indexes for security monitoring

**2. AdminActivityLogger Class (server/admin/activity_logger.py):**
- ✅ Async logging of admin actions
- ✅ Query API with filtering (by admin, action, target, date range)
- ✅ Summary statistics API (total actions, action distribution, most active admins)
- ✅ Automatic cleanup with retention policy (default 90 days)
- ✅ Background service management (start/stop)
- ✅ Graceful error handling (doesn't break main operations)

**3. API Endpoints (server/routers/admin_activity.py):**
- ✅ `GET /admin/activity` - Query logs with filters (admin only)
  - Filter by: admin_user_id, action, target_type, target_id, date range
  - Pagination support (limit/offset)
  - Returns logs with full metadata
- ✅ `GET /admin/activity/summary` - Get summary statistics (admin only)
  - Total actions count
  - Action distribution
  - Most active admins
  - Configurable time period (default 30 days)

**4. Helper Functions (server/admin/helpers.py):**
- ✅ `log_admin_action_async()` - Easy-to-use helper for logging
- ✅ `get_admin_user_id_from_request()` - Extract admin user ID from request
- ✅ Automatic IP address and user agent extraction
- ✅ Graceful handling of missing logger (non-blocking)

**5. Integration Example:**
- ✅ Integrated into `POST /organizations` endpoint as example
- ✅ Demonstrates pattern for integrating into other admin endpoints
- ✅ Non-blocking logging (doesn't affect main operation performance)

**6. Documentation:**
- ✅ Created comprehensive README.md in `server/admin/`
- ✅ Usage examples and integration guide
- ✅ API endpoint documentation
- ✅ Migration instructions

**7. Testing:**
- ✅ Integration test suite created (`tests/integration/test_admin_activity_logging.py`)
- ✅ Tests for logging, querying, summary, cleanup
- ✅ Tests for helper functions
- ✅ Graceful error handling tests

**Files Created:**
- ✅ `alembic/versions/0130_admin_activity_logs.py` - Database migration
- ✅ `server/admin/activity_logger.py` - Core logging class
- ✅ `server/admin/helpers.py` - Helper functions
- ✅ `server/admin/__init__.py` - Package marker
- ✅ `server/admin/README.md` - Documentation
- ✅ `server/routers/admin_activity.py` - API endpoints
- ✅ `tests/integration/test_admin_activity_logging.py` - Integration tests

**Files Modified:**
- ✅ `server/main.py` - Added admin_activity_router
- ✅ `server/routers/organizations.py` - Integrated logging example

**Key Features:**
1. **Non-blocking**: Logging failures don't affect main operations
2. **Async**: All logging operations are asynchronous
3. **Flexible**: JSONB details field allows custom metadata
4. **Queryable**: Rich filtering and pagination support
5. **Secure**: Admin-only access to activity logs
6. **Compliant**: Retention policy for data governance
7. **Performant**: Indexed for fast queries

**Migration:**
- Migration file created: `0130_admin_activity_logs.py`
- Ready to run: `python3 -m alembic upgrade head`
- Note: Requires database to be running

**Next Steps:**
1. Run migration when database is available
2. Integrate logging into additional admin endpoints:
   - User management (create/update/delete user)
   - Team management (create/update/delete team)
   - Context management (transfer ownership, permissions)
3. Add admin activity log UI (future enhancement)

**Assessment:**
- ✅ Database schema implemented per SPEC-005
- ✅ Logging middleware/helpers implemented
- ✅ GET /admin/activity endpoint implemented
- ✅ Retention policy implemented (90 days, configurable)
- ✅ Integration example provided
- ✅ Documentation complete
- ✅ Tests created

**Status:** ✅ **COMPLETE** - Admin Activity Logging System fully implemented. Ready for migration and integration into additional endpoints.
"""

    # Append completion details
    new_desc = current_desc
    if current_desc and not current_desc.endswith("\n"):
        new_desc += "\n"
    new_desc += completion_details

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_id = (
        statuses.get("done") or statuses.get("closed") or statuses.get("complete") or statuses.get("ready for testing")
    )

    # Update story
    print("Updating story description...")
    success = update_story(auth_token, story["id"], story["version"], new_desc, done_id)

    if success:
        print("✅ Story #112 updated successfully!")
        if done_id:
            print(f"   Status: Done")
        else:
            print(f"   Status: (could not auto-update - please set manually)")
        print(f"   View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/112")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
