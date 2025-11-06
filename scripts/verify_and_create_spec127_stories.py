#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Verify and create/update Taiga stories for SPEC-127: Context Bridge & Memory Federation System

This script:
1. Checks if SPEC-127 stories exist in Taiga
2. Creates stories for each implementation phase if they don't exist
3. Updates existing stories if needed
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


# SPEC-127 Story Definitions
STORIES = [
    {
        "subject": "SPEC-127 Phase 1: Foundation - Database Schema & Trust Scoring",
        "description": """**Goal**: Implement foundation infrastructure for Context Bridge system

**Phase 1 Tasks:**
- Create database schema (context_bridges, trust_scores, bridge_access_history, sync_policies)
- Implement TrustScoreCalculator class
- Implement basic ReferenceLink class (reference mode)
- Implement audit logging system

**Technical Requirements:**
- Alembic migration (use next available number, 0128 already used)
- SQLAlchemy models for all tables
- Trust score calculation with 4 components (org reputation, access history, policy alignment, recency decay)
- Basic reference mode with trust score checking (≥70)

**Acceptance Criteria:**
- ✅ All 4 database tables created and migrated
- ✅ Trust score calculator working (>90% test coverage)
- ✅ Reference mode can create bridges and resolve references
- ✅ Audit logging logs all bridge actions
- ✅ API endpoint POST /context-bridge/share works for reference mode

**Dependencies:**
- SPEC-043 (ACL) - Complete ✅
- SPEC-061 (GraphOps) - Complete ✅

**Estimated Effort:** 2 weeks
**Status:** Not Implemented (0%)
""",
        "tags": ["spec-127", "phase-1", "foundation", "database", "trust-scoring", "reference-mode"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-127 Phase 2: Clone & Hybrid Modes",
        "description": """**Goal**: Implement Clone and Hybrid sharing modes

**Phase 2 Tasks:**
- Implement MemoryClone class (clone mode)
- Implement HybridSync class (hybrid mode)
- Add mode switching capabilities (reference ↔ clone ↔ hybrid)
- Implement bridge lifecycle management (active/revoked/expired)

**Technical Requirements:**
- Clone mode: Deep copy with derived_from tracking
- Hybrid mode: Clone with sync triggers (on_update, scheduled, manual)
- Graph edge creation (DERIVES_FROM for clones)
- Conflict detection and resolution for hybrid sync
- PATCH /context-bridge/share/{bridge_id} endpoint

**Acceptance Criteria:**
- ✅ Clone mode creates isolated copies
- ✅ Hybrid mode syncs based on triggers
- ✅ Mode switching works (reference → clone → hybrid)
- ✅ Bridge lifecycle management (status, expiry, revocation)
- ✅ All modes have comprehensive test coverage

**Dependencies:**
- Phase 1 complete

**Estimated Effort:** 2 weeks
**Status:** Not Implemented (0%)
""",
        "tags": ["spec-127", "phase-2", "clone-mode", "hybrid-mode", "mode-switching"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-127 Phase 3: GraphOps Federation",
        "description": """**Goal**: Integrate with GraphOps for federated queries

**Phase 3 Tasks:**
- Extend GraphOps schema (REFERENCES, DERIVES_FROM, SHARES_WITH, TRUSTS edges)
- Auto-create graph edges on bridge creation
- Implement federated query engine (POST /context-bridge/federated-query)
- Implement federation topology (peer-to-peer, hub-mediated, hybrid)
- Performance optimization (caching, connection pooling)

**Technical Requirements:**
- Apache AGE integration for graph edges
- Trust-based filtering in federated queries
- Cross-context graph traversal
- Query result caching (Redis, 5min TTL)
- Performance targets: <200ms p95 latency

**Acceptance Criteria:**
- ✅ Graph edges created automatically on bridge creation
- ✅ Federated queries work across multiple contexts
- ✅ Trust-based filtering enforces security
- ✅ Performance targets met (<200ms p95)
- ✅ Supports 1000+ concurrent bridges

**Dependencies:**
- Phase 1 complete
- Phase 2 complete
- SPEC-061 (GraphOps) - Complete ✅

**Estimated Effort:** 2 weeks
**Status:** Not Implemented (0%)
""",
        "tags": ["spec-127", "phase-3", "graphops", "federation", "federated-query"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-127 Phase 4: Trust System Enhancement",
        "description": """**Goal**: Implement advanced trust scoring and dynamic trust adjustment

**Phase 4 Tasks:**
- Implement TrustAdjuster class (automatic trust increment/decrement)
- Implement TrustBasedACL class (trust-based access control)
- Integrate with SPEC-043 (ACL)
- Implement trust score API (GET /context-bridge/trust-score)
- Add trust score history tracking

**Technical Requirements:**
- Automatic trust adjustment based on access patterns
- Security incident handling (trust decrement)
- Daily trust score recalculation job
- Trust score breakdown API (4 components)
- Trust recommendations (e.g., "Enable MFA for +3 points")

**Acceptance Criteria:**
- ✅ Trust scores adjust automatically based on access patterns
- ✅ Trust-based ACL enforced for all bridge actions
- ✅ Trust score API provides breakdown and recommendations
- ✅ Trust score history tracked and queryable
- ✅ Integration with SPEC-043 working

**Dependencies:**
- Phase 1 complete
- SPEC-043 (ACL) - Complete ✅

**Estimated Effort:** 1 week
**Status:** Not Implemented (0%)
""",
        "tags": ["spec-127", "phase-4", "trust-system", "trust-adjustment", "trust-acl"],
        "priority": "P2",
    },
    {
        "subject": "SPEC-127 Phase 5: API & Testing",
        "description": """**Goal**: Complete API implementation and comprehensive testing

**Phase 5 Tasks:**
- Complete all API endpoints (federated embedding search, batch operations, statistics)
- Extend e*M Memory Provider interface (fetch_cross_context method)
- Integration with existing memory endpoints
- Comprehensive testing (unit, integration, E2E, performance, security)
- Documentation and deployment

**Technical Requirements:**
- All API endpoints from api-contracts.md implemented
- e*M integration: Transparent resolution in GET /memories/:id
- >90% test coverage
- Performance tests (latency targets)
- Security tests (penetration testing)
- Load tests (1000 concurrent users)

**Acceptance Criteria:**
- ✅ All API endpoints implemented and documented
- ✅ e*M integration seamless (transparent cross-context resolution)
- ✅ >90% test coverage
- ✅ All performance targets met
- ✅ Security audit passed
- ✅ Documentation complete (user docs, API reference, migration guide)

**Dependencies:**
- All previous phases complete

**Estimated Effort:** 1 week
**Status:** Not Implemented (0%)
""",
        "tags": ["spec-127", "phase-5", "api", "testing", "integration", "documentation"],
        "priority": "P1",
    },
]


def main():
    print("🔍 SPEC-127: Context Bridge & Memory Federation System - Story Verification\n")

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
    updated_count = 0
    existing_count = 0

    for story_def in STORIES:
        subject = story_def["subject"]
        search_terms = ["spec-127", subject.split(":")[0].lower()]  # Search by "spec-127" and phase name

        print(f"🔍 Checking for: {subject}")

        # Find existing story
        existing_story = find_story_by_subject_or_tags(token, project_id, search_terms)

        if existing_story:
            story_id = existing_story.get("id")
            story_ref = existing_story.get("ref", "N/A")
            print(f"   ✅ Found existing story: US#{story_ref} (ID: {story_id})")

            # Check if update needed
            current_desc = existing_story.get("description", "")
            if "Status: Not Implemented (0%)" not in current_desc:
                print(f"   📝 Updating story with implementation status...")
                update_data = {"description": story_def["description"]}
                if update_story(token, story_id, update_data):
                    print(f"   ✅ Story updated")
                    updated_count += 1
                else:
                    print(f"   ❌ Failed to update story")
            else:
                print(f"   ℹ️  Story already up to date")
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
    print(f"📝 Updated: {updated_count} stories")
    print(f"ℹ️  Already exists: {existing_count} stories")
    print(f"📋 Total: {len(STORIES)} stories")
    print()

    if created_count > 0 or updated_count > 0:
        print("✅ SPEC-127 stories ready for implementation!")
    else:
        print("ℹ️  All stories already exist and are up to date")


if __name__ == "__main__":
    main()
