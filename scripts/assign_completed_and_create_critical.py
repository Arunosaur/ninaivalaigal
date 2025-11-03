#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
1. Assign completed work (US#237-242) to Developer D
2. Create missing critical stories
3. Assign and start next priorities
"""

import json
import sys
from datetime import datetime

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_D = "Developer D"


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        sys.exit(1)
    return auth.json()["auth_token"], auth.json()


def get_project_id(auth_token):
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    return response.json()["id"]


def get_user_id_by_username(auth_token, username):
    """Find user ID by username"""
    url = f"{API_ENDPOINT}/users"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if (
                username.lower() in user.get("username", "").lower()
                or username.lower() in user.get("full_name", "").lower()
            ):
                return user["id"]
    return None


def get_or_create_epic(auth_token, project_id, epic_name):
    """Get or create epic"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Search existing epics
    url = f"{API_ENDPOINT}/epics?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        epics = response.json()
        for epic in epics:
            if epic_name.lower() in epic.get("subject", "").lower():
                return epic["id"]

    # Create new epic
    url = f"{API_ENDPOINT}/epics"
    payload = {
        "project": project_id,
        "subject": epic_name,
        "tags": [[tag, "#CCCCCC"] for tag in ["security", "critical"]],
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()["id"]
    return None


def get_statuses(auth_token, project_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def find_story_by_pattern(auth_token, project_id, patterns):
    """Find story by search patterns"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stories = response.json()
        for story in stories:
            subject = story.get("subject", "").lower()
            description = story.get("description", "").lower()
            text = f"{subject} {description}"
            for pattern in patterns:
                if any(p.lower() in text for p in pattern):
                    return story
    return None


def create_user_story(auth_token, project_id, story_data, epic_id=None):
    """Create user story"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    tags = [[tag, "#CCCCCC"] for tag in story_data.get("tags", [])]

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": tags,
    }

    if epic_id:
        payload["epics"] = [epic_id]

    url = f"{API_ENDPOINT}/userstories"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()
    return None


def assign_and_update_story(auth_token, story_id, user_id, status_id=None):
    """Assign story and optionally update status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    payload = {"assigned_to": user_id, "version": story.get("version", 1)}

    if status_id:
        payload["status"] = status_id

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def update_story_description(auth_token, story_id, additional_text):
    """Append to story description"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"
    story = requests.get(url, headers=headers).json()

    current_desc = story.get("description", "")
    new_desc = f"{current_desc}\n\n---\n\n{additional_text}"

    payload = {"description": new_desc, "version": story.get("version", 1)}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def main():
    print("=" * 70)
    print("Assign Completed Work & Create Critical Stories")
    print("=" * 70)
    print()

    auth_token, user_data = authenticate()
    admin_id = user_data["id"]
    print(f"✓ Authenticated as: {user_data.get('username')} (ID: {admin_id})")
    print()

    # Get or create Developer D user (use admin for now, or find/create)
    developer_d_id = admin_id  # Will assign to admin as Developer D

    project_id = get_project_id(auth_token)
    statuses = get_statuses(auth_token, project_id)
    done_status_id = statuses.get("done") or statuses.get("closed")
    in_progress_id = statuses.get("in progress") or statuses.get("working")
    ready_status_id = statuses.get("ready") or statuses.get("new")

    print(f"✓ Project ID: {project_id}")
    print(f"✓ Developer D ID: {developer_d_id}")
    print()

    # Step 1: Try to find and update completed stories (US#237-242)
    print("=" * 70)
    print("STEP 1: Assign Completed Work (US#237-242) to Developer D")
    print("=" * 70)
    print()

    completed_stories = {
        "237": {"patterns": [("237", "invoicing"), ("invoicing", "service")]},
        "238": {"patterns": [("238", "tax"), ("tax", "calculator")]},
        "239": {"patterns": [("239", "spec-027"), ("refactor", "spec-027")]},
        "240": {"patterns": [("240", "spec-028"), ("refactor", "spec-028")]},
        "241": {"patterns": [("241", "pdf", "comparison"), ("compare", "invoice")]},
        "242": {"patterns": [("242", "test"), ("test", "suite", "invoicing")]},
    }

    completion_text_template = """## ✅ COMPLETED by Developer D - November 1, 2025

**Status**: All deliverables complete
**Impact**: Eliminated ~250 lines of duplicate code across SPEC-027/028

**Files Created/Modified**:
- server/services/invoicing_service.py
- server/services/tax_calculator.py
- server/tests/services/ (90+ tests)
- scripts/compare_invoice_pdfs.py

**See**: governance/reports/US237_241_242_COMPLETION_SUMMARY.md for full details"""

    completed_count = 0
    for ref_num, info in completed_stories.items():
        story = find_story_by_pattern(auth_token, project_id, info["patterns"])
        if story:
            print(f"✓ Found US#{ref_num}: {story.get('subject', '')[:50]}")
            if assign_and_update_story(auth_token, story["id"], developer_d_id, done_status_id):
                print(f"  ✓ Assigned to Developer D and marked Done")
                update_story_description(auth_token, story["id"], completion_text_template)
                completed_count += 1
        else:
            print(f"✗ US#{ref_num} not found in Taiga (work completed but story may not exist)")

    print()
    print(f"Updated {completed_count} completed stories")
    print()

    # Step 2: Create critical stories if they don't exist
    print("=" * 70)
    print("STEP 2: Create Missing Critical Stories")
    print("=" * 70)
    print()

    # Get or create Security Epic
    security_epic_id = get_or_create_epic(auth_token, project_id, "Critical Security & Production Blockers")

    critical_stories = [
        {
            "subject": "US#117: ORM Guardrails & Multi-Tenant Isolation",
            "description": """As a security engineer, I want database-level access controls that automatically filter queries by organization, so that cross-org data leaks are prevented in our multi-tenant SaaS.

**Priority**: P0 - CRITICAL SECURITY
**Risk**: HIGH - Potential cross-org data leaks
**Impact**: Multi-tenant SaaS security requirement

**Acceptance Criteria:**
- ✅ Database-level access controls implemented
- ✅ Automatic query filtering by organization
- ✅ ORM guardrails prevent cross-org data access
- ✅ Unit tests for isolation (95%+ coverage)
- ✅ Integration tests verify multi-tenant security

**Technical Notes:**
- Prevent cross-org data leaks
- Database-level access controls
- Automatic query filtering by organization
- **HIGHEST PRIORITY - START IMMEDIATELY**

**Effort**: 4 days
**Dependencies**: None""",
            "tags": ["p0", "security", "critical", "orm", "multi-tenant", "guardrails"],
        },
        {
            "subject": "US#20: User Signup with bcrypt",
            "description": """As a user, I want to sign up for an account with secure password hashing, so that I can create an account on the platform.

**Priority**: P0 - BLOCKING PRODUCTION
**Impact**: **BLOCKS EVERYTHING** - Users cannot sign up without this

**Acceptance Criteria:**
- ✅ User signup endpoint implemented
- ✅ Password hashing with bcrypt
- ✅ Email validation
- ✅ Duplicate email prevention
- ✅ Secure password requirements
- ✅ Integration with SPEC-006 (User Management)

**Technical Notes:**
- Use passlib with bcrypt
- Implement secure password requirements
- Email uniqueness validation
- Return JWT token on successful signup

**Effort**: 4-6 hours
**Dependencies**: SPEC-006""",
            "tags": ["p0", "critical", "auth", "signup", "bcrypt", "production-blocker"],
        },
        {
            "subject": "US#21: User Login with Password Verification",
            "description": """As a user, I want to log in with my email and password, so that I can access my account.

**Priority**: P0 - BLOCKING PRODUCTION
**Impact**: **BLOCKS EVERYTHING** - Users cannot log in without this

**Acceptance Criteria:**
- ✅ User login endpoint implemented
- ✅ Password verification with bcrypt
- ✅ JWT token generation on success
- ✅ Invalid credentials handling
- ✅ Account lockout after failed attempts
- ✅ Integration with existing JWT auth

**Technical Notes:**
- Use passlib.verify for password checking
- Generate JWT tokens
- Implement rate limiting for login attempts
- Secure error messages

**Effort**: 4-6 hours
**Dependencies**: US#20, SPEC-006""",
            "tags": ["p0", "critical", "auth", "login", "password", "production-blocker"],
        },
        {
            "subject": "Rate Limiting Implementation",
            "description": """As a security engineer, I want API rate limiting to prevent abuse and ensure fair resource usage, so that the platform remains secure and available.

**Priority**: P0 - SECURITY
**Impact**: High - Prevents abuse and DoS attacks

**Acceptance Criteria:**
- ✅ Rate limiting middleware implemented
- ✅ Configurable rate limits per endpoint
- ✅ Per-user and per-IP limiting
- ✅ Rate limit headers in responses
- ✅ Graceful error handling (429 status)
- ✅ Integration with Redis for distributed limiting

**Technical Notes:**
- Use slowapi or similar
- Redis-backed for distributed systems
- Different limits for auth vs API endpoints
- Whitelist for internal services

**Effort**: 2 days
**Dependencies**: None""",
            "tags": ["p0", "security", "rate-limiting", "api", "middleware"],
        },
    ]

    created_stories = []
    for story_data in critical_stories:
        # Check if story exists
        existing = find_story_by_pattern(
            auth_token,
            project_id,
            (
                [(story_data["subject"].split(":")[0].replace("US#", ""),)]
                if "US#" in story_data["subject"]
                else [(story_data["subject"].lower().split()[0],)]
            ),
        )

        if existing:
            print(f"⏭️  Story exists: {story_data['subject'][:50]}")
            created_stories.append(existing)
        else:
            story = create_user_story(auth_token, project_id, story_data, security_epic_id)
            if story:
                print(f"✓ Created: {story_data['subject'][:50]} (Ref: #{story.get('ref')})")
                created_stories.append(story)
            else:
                print(f"✗ Failed to create: {story_data['subject'][:50]}")

    print()

    # Step 3: Assign and start highest priority stories
    print("=" * 70)
    print("STEP 3: Assign and Start Highest Priority Stories")
    print("=" * 70)
    print()

    # Prioritize: US#117 (Security) > US#20 (Signup) > US#21 (Login) > Rate Limiting
    priority_order = ["117", "20", "21", "Rate Limiting"]

    assigned_count = 0
    for priority in priority_order:
        # Find story matching priority
        story = None
        for s in created_stories:
            if priority in s.get("subject", ""):
                story = s
                break

        if not story:
            # Try to find existing
            patterns = {
                "117": [("117", "orm"), ("guardrails")],
                "20": [("20", "signup"), ("signup", "bcrypt")],
                "21": [("21", "login"), ("login", "password")],
                "Rate Limiting": [("rate", "limit")],
            }
            story = find_story_by_pattern(auth_token, project_id, patterns.get(priority, []))

        if story and not story.get("assigned_to"):
            print(f"📝 Assigning: {story.get('subject', '')[:55]}")
            if assign_and_update_story(auth_token, story["id"], developer_d_id, in_progress_id):
                print(f"  ✓ Assigned to Developer D and moved to 'In Progress'")
                assigned_count += 1
            else:
                print(f"  ✗ Failed to assign")
            print()

            if assigned_count >= 2:  # Start with top 2
                break

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Completed stories updated: {completed_count}")
    print(f"✓ Critical stories created/found: {len(created_stories)}")
    print(f"✓ Assigned & started: {assigned_count} stories")
    print()
    print(f"View at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 70)


if __name__ == "__main__":
    main()
