#!/usr/bin/env python3
"""
Verify and create/update Taiga story for SPEC-128: Memory Sharing & Transfer Architecture

This script:
1. Checks if US#599 exists in Taiga
2. Updates it if it exists (adds implementation status)
3. Creates a new story if it doesn't exist
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


def get_story_by_ref(token: str, project_id: int, ref: int) -> Optional[Dict]:
    """Get story by reference number"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_ENDPOINT}/userstories",
            headers=headers,
            params={"project": project_id, "ref": ref},
        )
        if response.status_code == 200:
            stories = response.json()
            if stories:
                return stories[0]
        return None
    except Exception as e:
        print(f"❌ Error getting story by ref: {e}")
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


def update_story(token: str, story_id: int, updates: Dict) -> bool:
    """Update an existing story"""
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.patch(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers, json=updates)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Failed to update story: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


SPEC_128_DESCRIPTION = """**Goal**: Implement Memory Sharing & Transfer Architecture (SPEC-128)

**Implementation Status:** ⚠️ Partially Implemented (30%)

**What Exists:**
- ✅ Basic sharing via ACL (SPEC-043) - Complete
- ✅ Sharing Contracts (SPEC-049) - Partially implemented
- ✅ Visibility levels: PRIVATE, TEAM, ORGANIZATION, PUBLIC

**What's Missing (70%):**
- ❌ Transfer ownership functionality
- ❌ Copy operation (duplicate creation)
- ❌ Approval workflows (Personal → Team, Team → External, Org → External)
- ❌ Rate limits (sharing/transfer limits, abuse prevention)
- ❌ Comprehensive audit trail
- ❌ M&A scenario support (org-to-org transfer, bulk operations)

**Technical Requirements:**

**Phase 1: Transfer & Copy (High Priority)**
- Implement POST `/memory/{id}/transfer` endpoint
- Implement POST `/memory/{id}/copy` endpoint
- Create `memory_transfers` table (immutable)
- Transfer history tracking
- Ownership change functionality

**Phase 2: Approval Workflows**
- Approval system for Personal → Team
- Approval system for Team → External entity
- Approval system for Org → External org
- Transfer acceptance/rejection workflow

**Phase 3: Rate Limits & Audit**
- Rate limit enforcement (10/100/unlimited per tier for sharing, 5/day for transfers)
- Abuse prevention monitoring
- Comprehensive audit trail (GET `/memory/audit`)
- Automatic suspension for abuse

**Phase 4: M&A Support**
- Org-to-org transfer functionality
- Bulk transfer operations
- Team migration support
- Organization dissolution handling

**Database Schema:**
- `memory_visibility` table
- `memory_shares` table
- `memory_transfers` table (immutable)
- `sharing_audit_log` table

**Dependencies:**
- SPEC-043 (ACL) - Complete ✅
- SPEC-026 (Standalone Teams) - Needs verification
- SPEC-002 (Multi-User Auth) - Needs verification

**Acceptance Criteria:**
- ✅ Transfer ownership works (POST `/memory/{id}/transfer`)
- ✅ Copy operation works (POST `/memory/{id}/copy`)
- ✅ Approval workflows functional
- ✅ Rate limits enforced
- ✅ Comprehensive audit trail available
- ✅ M&A scenarios supported

**Estimated Effort:** 6-8 weeks (30-40 working days)

**Status:** Not Implemented (70% missing)
"""


def main():
    print("🔍 SPEC-128: Memory Sharing & Transfer Architecture - Story Verification\n")

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

    # Search for US#599
    print("🔍 Searching for US#599...")
    story = get_story_by_ref(token, project_id, 599)

    if not story:
        print("   ❌ US#599 not found by reference number")
        print("   🔍 Searching by subject/tags...")
        story = find_story_by_subject_or_tags(token, project_id, ["spec-128", "memory sharing", "transfer"])

    if story:
        story_id = story.get("id")
        story_ref = story.get("ref", "N/A")
        print(f"   ✅ Found story: US#{story_ref} (ID: {story_id})")

        # Check if update needed
        current_desc = story.get("description", "")
        if "Status: Not Implemented (70% missing)" not in current_desc:
            print(f"   📝 Updating story with implementation status...")
            update_data = {"description": SPEC_128_DESCRIPTION}
            if update_story(token, story_id, update_data):
                print(f"   ✅ Story updated")
            else:
                print(f"   ❌ Failed to update story")
        else:
            print(f"   ℹ️  Story already up to date")
    else:
        print("   ❌ Story not found, creating new story...")

        # Create new story
        story_data = {
            "project": project_id,
            "subject": "SPEC-128: Memory Sharing & Transfer Architecture",
            "description": SPEC_128_DESCRIPTION,
            "tags": ["spec-128", "memory-sharing", "transfer", "copy", "approval-workflows", "rate-limits"],
            "status": project.get("us_statuses", [{}])[0].get("id") if project.get("us_statuses") else None,
        }

        new_story = create_story(token, project_id, story_data)
        if new_story:
            story_ref = new_story.get("ref", "N/A")
            story_id = new_story.get("id")
            print(f"   ✅ Created: US#{story_ref} (ID: {story_id})")
            print(f"   🔗 URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_id}")
        else:
            print("   ❌ Failed to create story")

    print("\n✅ SPEC-128 story verification complete!")


if __name__ == "__main__":
    main()
