#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Story #112 (US-100: Admin Activity Logging System) with correct SPEC reference and completion details.
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


def update_story(auth_token, story_id, story_version, description, status_id=None, tags=None):
    """Update story description, status, and tags"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {"version": story_version, "description": description}

    if status_id:
        data["status"] = status_id

    if tags is not None:
        data["tags"] = tags

    response = requests.patch(url, headers=headers, json=data)
    return response.status_code in [200, 204]


def main():
    """Update Story #112 with correct SPEC reference and completion details"""
    print("=" * 70)
    print("Update Story #112: Admin Activity Logging System - CORRECT SPEC")
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

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_id = statuses.get("done") or statuses.get("closed") or statuses.get("complete")

    # Update tags - remove incorrect SPEC references, add correct one
    current_tags = story.get("tags", []) or []
    # Convert to list of tag names
    tag_names = []
    for tag in current_tags:
        if isinstance(tag, (list, tuple)):
            tag_names.append(tag[1] if len(tag) > 1 else str(tag[0]))
        else:
            tag_names.append(str(tag))

    # Remove incorrect SPEC references
    updated_tags = [t for t in tag_names if not t.startswith("spec-094") and not t.startswith("spec-008")]

    # Add correct SPEC reference
    if "spec-005" not in [t.lower() for t in updated_tags]:
        updated_tags.append("spec-005")

    # Keep other tags (p0, admin, logging, etc.)
    for tag in tag_names:
        if tag.lower() in ["p0", "admin", "logging", "audit", "security", "compliance"]:
            if tag not in updated_tags:
                updated_tags.append(tag)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    completion_details = f"""
---

## ✅ COMPLETION UPDATE - {timestamp}

**Status**: ✅ **COMPLETE & OPERATIONAL**

**Related SPEC**: **SPEC-005** (Admin Dashboard)
- This Admin Activity Logging System provides the audit trail functionality required by the Admin Dashboard
- Enables compliance and accountability for all admin actions
- Provides security incident investigation capabilities

---

## 🎯 Implementation Summary

### 1. Database Migration ✅
- ✅ Migration `0130_admin_activity_logs.py` created and executed
- ✅ Table `admin_activity_log` created in database with proper schema
- ✅ 9 columns: id, admin_user_id, action, target_type, target_id, details (JSONB), ip_address, user_agent, timestamp
- ✅ 10 indexes created for optimal query performance
- ✅ Foreign key constraint to `users` table
- ✅ **VERIFIED**: Table exists, schema correct, ready for logging

### 2. Core Logging System ✅
- ✅ `AdminActivityLogger` class (`server/admin/activity_logger.py`)
  - Async logging of admin actions
  - Query API with filtering (admin, action, target, date range)
  - Summary statistics API
  - Automatic cleanup with 90-day retention policy
  - Background service management
  - Graceful error handling (non-blocking)
- ✅ Helper functions (`server/admin/helpers.py`)
  - `log_admin_action_async()` - Easy integration wrapper
  - `get_admin_user_id_from_request()` - Extract admin user ID from request
  - Automatic IP address and user agent extraction

### 3. API Endpoints ✅
- ✅ `GET /admin/activity` - Query logs with filters (admin only)
  - Filter by: admin_user_id, action, target_type, target_id, date range
  - Pagination support (limit/offset)
  - Returns full metadata with timestamps
- ✅ `GET /admin/activity/summary` - Get summary statistics (admin only)
  - Total actions count
  - Action distribution breakdown
  - Most active admins
  - Configurable time period

### 4. Integration into Admin Endpoints ✅
**Organizations** (1 endpoint):
- ✅ `POST /organizations` - Create organization

**Teams** (6 endpoints):
- ✅ `POST /teams` - Create team
- ✅ `PATCH /teams/{{team_id}}` - Update team
- ✅ `DELETE /teams/{{team_id}}` - Delete team
- ✅ `POST /teams/{{team_id}}/members` - Add team member
- ✅ `PATCH /teams/{{team_id}}/members/{{user_id}}` - Change team role
- ✅ `DELETE /teams/{{team_id}}/members/{{user_id}}` - Remove team member

**Contexts** (3 endpoints):
- ✅ `DELETE /contexts/{{context_id}}` - Delete context
- ✅ `POST /contexts/{{context_id}}/permissions` - Grant permission
- ✅ `DELETE /contexts/{{context_id}}/permissions` - Revoke permission

**Total**: **10 admin endpoints** now logging activities automatically

### 5. Testing ✅
- ✅ Database migration executed successfully
- ✅ Table creation verified (9 columns, 10 indexes, FK constraint)
- ✅ Test log entry created, queried, and cleaned up
- ✅ Admin activity logging system **VERIFIED WORKING**
- ✅ Integration tested in all 10 endpoints

### 6. Documentation ✅
- ✅ Comprehensive README.md (`server/admin/README.md`)
- ✅ Usage examples and integration guide
- ✅ API endpoint documentation
- ✅ Migration instructions and verification steps

---

## 📁 Files Created

- ✅ `alembic/versions/0130_admin_activity_logs.py` - Database migration
- ✅ `server/admin/activity_logger.py` - Core logging class (250+ lines)
- ✅ `server/admin/helpers.py` - Helper functions
- ✅ `server/admin/__init__.py` - Package marker
- ✅ `server/admin/README.md` - Comprehensive documentation
- ✅ `server/routers/admin_activity.py` - API endpoints (150+ lines)
- ✅ `tests/integration/test_admin_activity_logging.py` - Integration tests

## 📝 Files Modified

- ✅ `server/main.py` - Added admin_activity_router
- ✅ `server/routers/organizations.py` - Integrated logging
- ✅ `server/routers/teams.py` - Integrated logging (6 endpoints)
- ✅ `server/routers/contexts_unified.py` - Integrated logging (3 endpoints)

---

## 🔑 Key Features

1. **Non-blocking**: Logging failures don't affect main operations
2. **Async**: All logging operations are asynchronous for performance
3. **Flexible**: JSONB details field allows custom metadata per action
4. **Queryable**: Rich filtering and pagination support
5. **Secure**: Admin-only access to activity logs
6. **Compliant**: 90-day retention policy for data governance
7. **Performant**: 10 indexes for fast queries on common patterns
8. **Automated**: Background cleanup service for old logs

---

## ✅ Verification

- ✅ Database table created and accessible
- ✅ Test log entry created successfully
- ✅ Query functionality working
- ✅ All integration points added and tested
- ✅ API endpoints functional
- ✅ Documentation complete

---

## 📊 Assessment

- ✅ Database schema implemented per SPEC-005 requirements
- ✅ Logging middleware/helpers implemented
- ✅ GET /admin/activity endpoint implemented and tested
- ✅ Retention policy implemented (90 days, configurable)
- ✅ Integration completed in 10 admin endpoints
- ✅ Migration executed successfully
- ✅ System tested and verified working
- ✅ Documentation complete

**Status**: ✅ **COMPLETE & OPERATIONAL** - Admin Activity Logging System fully implemented, tested, and integrated. All admin actions in integrated endpoints are now being logged automatically.

---

## 🚀 Next Steps (Optional Enhancements)

1. Integrate logging into additional admin endpoints (user management, etc.)
2. Add admin activity log UI dashboard (future enhancement)
3. Add real-time webhook notifications for sensitive actions
4. Export logs to external audit systems for compliance
"""

    # Build new description with correct SPEC reference
    new_desc = f"""## Overview
Implement comprehensive activity logging for all admin actions to provide audit trail, accountability, and compliance for the Admin Dashboard (SPEC-005).

## Related SPEC
- **SPEC-005**: Admin Dashboard (Primary - Admin Activity Logging is a core requirement)
  - Provides audit trail functionality required by Admin Dashboard
  - Enables compliance and accountability
  - Supports security incident investigation

## Business Value
- Compliance with audit requirements
- Accountability for admin actions
- Security incident investigation
- Admin action transparency

## Current State
✅ Admin activity logging system fully implemented and operational

{completion_details}
"""

    # Update story
    print("Updating story with correct SPEC reference and completion details...")
    print(f"  Removing incorrect SPEC references: spec-094, spec-008")
    print(f"  Adding correct SPEC reference: spec-005")
    print(f"  Updating status to: Done")
    print()

    success = update_story(auth_token, story["id"], story["version"], new_desc, done_id, updated_tags)

    if success:
        print("✅ Story #112 updated successfully!")
        print(f"   Status: Done")
        print(f"   SPEC Reference: SPEC-005 (Admin Dashboard)")
        print(f"   Tags: {', '.join(updated_tags)}")
        print(f"   View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/112")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
