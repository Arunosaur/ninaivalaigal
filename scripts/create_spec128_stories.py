#!/usr/bin/env python3
"""
Create Taiga stories for SPEC-128: Memory Sharing & Transfer Architecture

This script creates 5 stories covering all phases of SPEC-128 implementation:
- Phase 1: Transfer & Copy Operations
- Phase 2: Approval Workflows
- Phase 3: Rate Limits & Audit
- Phase 4: M&A Support
- Phase 5: Visibility Enhancement
"""

import os
import sys
from typing import Dict, List, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"


def get_auth_token() -> Optional[str]:
    """Authenticate with Taiga and get auth token"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
        )
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error authenticating: {e}")
        return None


def get_project(token: str) -> Optional[Dict]:
    """Get project by slug"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Project lookup failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def find_story_by_subject_or_tags(token: str, project_id: int, search_terms: list) -> Optional[Dict]:
    """Find story by subject or tags"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/userstories", headers=headers, params={"project": project_id})
        if response.status_code == 200:
            stories = response.json()
            for story in stories:
                subject = story.get("subject", "").lower()
                tags = []
                for tag in story.get("tags", []):
                    if isinstance(tag, str):
                        tags.append(tag.lower())
                    elif isinstance(tag, dict):
                        tags.append(tag.get("name", "").lower())

                for term in search_terms:
                    term_lower = term.lower()
                    if term_lower in subject or any(term_lower in tag for tag in tags):
                        return story
        return None
    except Exception as e:
        print(f"❌ Error searching stories: {e}")
        return None


def create_story(token: str, project_id: int, story_data: Dict) -> Optional[Dict]:
    """Create a new user story in Taiga"""
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"❌ Failed to create story: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        return None


# SPEC-128 Story Definitions
STORIES = [
    {
        "subject": "SPEC-128 Phase 1: Transfer & Copy Operations",
        "description": """**Goal**: Implement memory transfer and copy operations

**Phase 1 Tasks:**
- Implement POST `/memory/{id}/transfer` endpoint
- Implement POST `/memory/{id}/copy` endpoint
- Create `memory_transfers` table (immutable)
- Create `memory_copies` table
- Transfer history tracking
- Ownership change functionality
- Copy creation with independent management

**Technical Requirements:**
- Transfer endpoint: Change ownership, original owner loses access
- Copy endpoint: Create duplicate, both parties retain independent copies
- Immutable transfer history (cannot be modified)
- Transfer acceptance/rejection workflow
- Copy metadata tracking (derived_from, copied_at)

**Acceptance Criteria:**
- ✅ POST `/memory/{id}/transfer` works (ownership change)
- ✅ POST `/memory/{id}/copy` works (duplicate creation)
- ✅ Transfer history is immutable and queryable
- ✅ Copy operations create independent copies
- ✅ All operations logged in audit trail
- ✅ >90% test coverage

**Dependencies:**
- SPEC-043 (ACL) - Complete ✅

**Estimated Effort:** 3 weeks (15 story points)
**Priority:** HIGH
**Status:** Not Implemented
""",
        "tags": ["spec-128", "phase-1", "transfer", "copy", "ownership"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-128 Phase 2: Approval Workflows",
        "description": """**Goal**: Implement approval workflows for memory sharing/transfer

**Phase 2 Tasks:**
- Approval system for Personal → Team
- Approval system for Team → External entity
- Approval system for Org → External org
- Transfer acceptance/rejection workflow
- Approval state management
- Notification system for approvals

**Technical Requirements:**
- Personal → Team: Auto-approved if member, admin can accept/reject
- Team → External: Team admin approval (org admin if within org)
- Org → External Org: Org admin approval + recipient acceptance
- Transfer (Any): Recipient acceptance required
- Approval state: PENDING, APPROVED, REJECTED
- Approval notifications (email/in-app)

**Acceptance Criteria:**
- ✅ Personal → Team approval workflow works
- ✅ Team → External approval workflow works
- ✅ Org → External approval workflow works
- ✅ Transfer acceptance/rejection works
- ✅ Approval notifications sent
- ✅ Approval history tracked
- ✅ >90% test coverage

**Dependencies:**
- Phase 1 complete (transfer/copy operations)
- SPEC-090 (Approval Chain Processing) - Needs verification

**Estimated Effort:** 2 weeks (10 story points)
**Priority:** MEDIUM
**Status:** Not Implemented
""",
        "tags": ["spec-128", "phase-2", "approval-workflows", "approvals"],
        "priority": "P2",
    },
    {
        "subject": "SPEC-128 Phase 3: Rate Limits & Audit",
        "description": """**Goal**: Implement rate limits and comprehensive audit trail

**Phase 3 Tasks:**
- Rate limit enforcement (sharing: 10/100/unlimited per tier)
- Rate limit enforcement (transfer: 5/day all tiers)
- Abuse prevention monitoring
- Comprehensive audit trail (GET `/memory/audit`)
- Rate limit violation alerts
- Automatic suspension for abuse

**Technical Requirements:**
- Sharing rate limits: Free (10/day), Paid (100/day), Enterprise (unlimited)
- Transfer rate limits: 5/day (all tiers), 24h cooldown between transfers
- Abuse detection: Mass sharing to external orgs, suspicious patterns
- Audit trail: Complete logging for share/transfer/copy actions
- Audit endpoint: GET `/memory/audit` with filtering (by user, date, action)
- Alert system: Platform staff notified on violations

**Acceptance Criteria:**
- ✅ Rate limits enforced correctly
- ✅ Abuse patterns detected and flagged
- ✅ Comprehensive audit trail available (GET `/memory/audit`)
- ✅ Audit logs include all required fields
- ✅ Rate limit violations trigger alerts
- ✅ Automatic suspension works for abuse
- ✅ >90% test coverage

**Dependencies:**
- Phase 1 complete (transfer/copy operations)
- Phase 2 complete (approval workflows)

**Estimated Effort:** 2 weeks (8 story points)
**Priority:** MEDIUM
**Status:** Not Implemented
""",
        "tags": ["spec-128", "phase-3", "rate-limits", "audit", "abuse-prevention"],
        "priority": "P2",
    },
    {
        "subject": "SPEC-128 Phase 4: M&A Support",
        "description": """**Goal**: Support M&A scenarios (organization-to-organization transfers)

**Phase 4 Tasks:**
- Org-to-org transfer functionality
- Bulk transfer operations
- Team migration support
- Organization dissolution handling
- M&A scenario testing

**Technical Requirements:**
- Org-to-org transfer: Company A → Company B (all org memory)
- Bulk transfer: Transfer multiple memories at once
- Team migration: Teams within Company B become teams within Company A
- Organization dissolution: 90-day grace period for enterprise
- M&A audit trail: Complete history of all transfers
- Transfer validation: Compliance checks, data integrity

**Acceptance Criteria:**
- ✅ Org-to-org transfer works
- ✅ Bulk transfer operations work
- ✅ Team migration works correctly
- ✅ Organization dissolution handled properly
- ✅ M&A audit trail complete
- ✅ Compliance checks pass
- ✅ End-to-end M&A scenario tested

**Dependencies:**
- Phase 1 complete (transfer operations)
- Phase 2 complete (approval workflows)
- Phase 3 complete (audit trail)

**Estimated Effort:** 2 weeks (8 story points)
**Priority:** LOW
**Status:** Not Implemented
""",
        "tags": ["spec-128", "phase-4", "m&a", "bulk-transfer", "org-transfer"],
        "priority": "P3",
    },
    {
        "subject": "SPEC-128 Phase 5: Visibility Enhancement",
        "description": """**Goal**: Enhance visibility rules and database schema

**Phase 5 Tasks:**
- Create `memory_visibility` table
- Create `memory_shares` table
- Enhance visibility rules (Personal, Team, Org, Public)
- Public/Unlisted memory classification
- Visibility rule enforcement improvements

**Technical Requirements:**
- `memory_visibility` table: Track visibility levels per memory
- `memory_shares` table: Track active shares (replacing ACL-only approach)
- Public memory: Searchable and discoverable
- Unlisted memory: Accessible via link but not searchable
- Visibility rule enforcement: Consistent with SPEC-043 ACL

**Acceptance Criteria:**
- ✅ `memory_visibility` table created and migrated
- ✅ `memory_shares` table created and migrated
- ✅ Public/Unlisted classification works
- ✅ Visibility rules enforced correctly
- ✅ Integration with SPEC-043 ACL working
- ✅ >90% test coverage

**Dependencies:**
- All previous phases complete
- SPEC-043 (ACL) - Complete ✅

**Estimated Effort:** 1 week (5 story points)
**Priority:** LOW
**Status:** Not Implemented
""",
        "tags": ["spec-128", "phase-5", "visibility", "database-schema"],
        "priority": "P3",
    },
]


def main():
    print("🔍 SPEC-128: Memory Sharing & Transfer Architecture - Story Creation\n")

    # Authenticate
    print("🔐 Authenticating with Taiga...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated\n")

    # Get project
    print(f"📁 Getting project: {PROJECT_SLUG}...")
    project = get_project(token)
    if not project:
        print("❌ Failed to get project")
        sys.exit(1)
    project_id = project["id"]
    print(f"✅ Project found: {project['name']} (ID: {project_id})\n")

    # Process each story
    created_count = 0
    existing_count = 0

    for story_def in STORIES:
        subject = story_def["subject"]
        search_terms = ["spec-128", subject.split(":")[0].lower()]

        print(f"🔍 Checking for: {subject}")

        # Find existing story
        existing_story = find_story_by_subject_or_tags(token, project_id, search_terms)

        if existing_story:
            story_id = existing_story.get("id")
            story_ref = existing_story.get("ref", "N/A")
            print(f"   ✅ Found existing story: US#{story_ref} (ID: {story_id})")
            print(f"   ℹ️  Skipping (story already exists)")
            existing_count += 1
        else:
            print(f"   ❌ Story not found, creating new story...")

            # Create new story
            story_data = {
                "project": project_id,
                "subject": subject,
                "description": story_def["description"],
                "tags": story_def["tags"],
                "status": project.get("us_statuses", [{}])[0].get("id") if project.get("us_statuses") else None,
            }

            new_story = create_story(token, project_id, story_data)
            if new_story:
                story_ref = new_story.get("ref", "N/A")
                story_id = new_story.get("id")
                print(f"   ✅ Created: US#{story_ref} (ID: {story_id})")
                print(f"   🔗 URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_id}")
                created_count += 1
            else:
                print(f"   ❌ Failed to create story")

        print()

    # Summary
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"✅ Created: {created_count} stories")
    print(f"ℹ️  Already exists: {existing_count} stories")
    print(f"📋 Total: {len(STORIES)} stories")
    print()

    if created_count > 0:
        print("✅ SPEC-128 stories created successfully!")
        print("\n📋 Story Breakdown:")
        print("   Phase 1: Transfer & Copy Operations (3 weeks, HIGH)")
        print("   Phase 2: Approval Workflows (2 weeks, MEDIUM)")
        print("   Phase 3: Rate Limits & Audit (2 weeks, MEDIUM)")
        print("   Phase 4: M&A Support (2 weeks, LOW)")
        print("   Phase 5: Visibility Enhancement (1 week, LOW)")
        print("\n   Total: 10 weeks (46 story points)")
    else:
        print("ℹ️  All stories already exist")


if __name__ == "__main__":
    main()

