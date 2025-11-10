#!/usr/bin/env python3
"""
Create Taiga stories for SPEC-129: External AI Memory API Integration

This script creates 4 stories covering all phases of SPEC-129 implementation:
- Phase 1: Adapter Layer (Claude + OpenAI)
- Phase 2: Federation & Origin Tagging
- Phase 3: Governance & Admin UI
- Phase 4: Security Infrastructure & Expansion
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


# SPEC-129 Story Definitions
STORIES = [
    {
        "subject": "SPEC-129 Phase 1: Adapter Layer (Claude + OpenAI)",
        "description": """**Goal**: Implement adapter layer for external AI vendor memory APIs

**Phase 1 Tasks:**
- Implement `ExternalMemoryAdapter` base class (ABC)
- Implement `ClaudeMemoryAdapter` for Anthropic Claude Memory Tool
- Implement `OpenAIThreadsAdapter` for OpenAI Persistent Threads / Assistants API
- Normalize vendor responses to Memory Substrate (SPEC-012)
- Basic trust score calculation (0.0-1.0) for vendors

**Technical Requirements:**
- Base adapter with abstract methods: `fetch_memories()`, `normalize_to_substrate()`, `get_trust_score()`
- Claude adapter: Call Claude Memory Tool API, mark as external=True, apply trust score
- OpenAI adapter: Call OpenAI Assistants API, extract thread context, normalize to Memory Substrate
- Normalization: Convert vendor format to Nina Memory Substrate format
- Trust scoring: Basic 0.0-1.0 score based on vendor reliability (can be enhanced later with SPEC-080)

**Acceptance Criteria:**
- ✅ `ExternalMemoryAdapter` base class exists
- ✅ `ClaudeMemoryAdapter` can fetch memories from Claude Memory Tool
- ✅ `OpenAIThreadsAdapter` can fetch memories from OpenAI Threads
- ✅ Vendor memories are normalized to Memory Substrate format
- ✅ Basic trust scores are assigned to vendor memories
- ✅ All operations logged in audit trail
- ✅ >90% test coverage

**Dependencies:**
- SPEC-012 (Memory Substrate) - Complete ✅
- SPEC-020 (Memory Provider) - Complete ✅

**Estimated Effort:** 3 weeks (15 story points)
**Priority:** HIGH
**Status:** Not Implemented
""",
        "tags": ["spec-129", "phase-1", "adapter-layer", "claude", "openai"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-129 Phase 2: Federation & Origin Tagging",
        "description": """**Goal**: Implement federated query function and origin tagging

**Phase 2 Tasks:**
- Implement `query_federated_memories()` function
- Origin tagging (`source=external`, `vendor=claude`, `vendor=openai`)
- Integrate vendor memory into Graph Intelligence (SPEC-060/061)
- Trust-based ranking (`rank_by_relevance_and_trust()`)
- Combine Nina-native and external memories

**Technical Requirements:**
- Federated query: Query both Nina-native and external memories
- Origin tags: Clear distinction between Nina-native vs vendor-sourced memories
- Graph Intelligence integration: Vendor memories queryable alongside native memories
- Trust-based ranking: Rank by relevance + trust score (Nina memories prioritized)
- Memory combination: Merge results from multiple sources

**Acceptance Criteria:**
- ✅ `query_federated_memories()` function works
- ✅ Origin tags are applied correctly (`source=external`, `vendor=claude`)
- ✅ Vendor memories are queryable alongside Nina memories
- ✅ Trust-based ranking works (relevance + trust score)
- ✅ Graph Intelligence integration works (SPEC-060/061)
- ✅ All operations logged in audit trail
- ✅ >90% test coverage

**Dependencies:**
- Phase 1 complete (adapter layer)
- SPEC-060/061 (Graph Intelligence) - Complete ✅

**Estimated Effort:** 2 weeks (10 story points)
**Priority:** HIGH
**Status:** Not Implemented
""",
        "tags": ["spec-129", "phase-2", "federation", "origin-tagging", "graph-intelligence"],
        "priority": "P1",
    },
    {
        "subject": "SPEC-129 Phase 3: Governance & Admin UI",
        "description": """**Goal**: Apply governance policies and create admin UI

**Phase 3 Tasks:**
- Apply RBAC policies (SPEC-009) to vendor memory
- Apply Security Middleware (SPEC-008) to vendor data
- Assign Trust Scores (SPEC-080) to vendor data (basic implementation, can enhance later)
- Admin UI toggle for vendor connectors per tenant
- Analytics dashboard updates (origin tracking)

**Technical Requirements:**
- RBAC: Vendor memory subject to same RBAC policies as Nina memories
- Security middleware: All vendor data flows through redaction, encryption, audit pipeline
- Trust scores: Assign trust scores to vendor data (basic 0.0-1.0, can enhance with SPEC-080 later)
- Admin UI: Toggle to enable/disable vendor connectors per tenant (SPEC-025, SPEC-068)
- Analytics: Origin tracking in logs/analytics (use SPEC-030 for basic analytics, SPEC-082 later)

**Acceptance Criteria:**
- ✅ RBAC policies apply to vendor memory
- ✅ Security middleware applies to vendor data
- ✅ Trust scores assigned to vendor data
- ✅ Admin UI allows toggling vendor connectors per tenant
- ✅ Origin tracking visible in logs/analytics
- ✅ All operations logged in audit trail
- ✅ >90% test coverage

**Dependencies:**
- Phase 1 and Phase 2 complete
- SPEC-009 (RBAC) - Complete ✅
- SPEC-008 (Security Middleware) - Complete ✅
- SPEC-030 (Admin Analytics) - Complete ✅ (for basic analytics)
- SPEC-080 (Trust Score) - Planned (can use basic trust scoring)
- SPEC-082 (Narrative Analytics) - Planned (can use SPEC-030 for now)

**Estimated Effort:** 3 weeks (15 story points)
**Priority:** MEDIUM
**Status:** Not Implemented
""",
        "tags": ["spec-129", "phase-3", "governance", "admin-ui", "rbac", "security"],
        "priority": "P2",
    },
    {
        "subject": "SPEC-129 Phase 4: Security Infrastructure & Expansion",
        "description": """**Goal**: Implement security infrastructure and expand to additional vendors

**Phase 4 Tasks:**
- API key management in secure vault (SPEC-054)
- Per-tenant API key configuration
- Rate limiting per vendor
- Audit trail for all external API calls
- GitHub Copilot adapter
- Additional vendor support (optional)

**Technical Requirements:**
- API key management: Store vendor API keys in secure vault (SPEC-054)
- Per-tenant configuration: Each tenant can configure their own API keys
- Rate limiting: Enforce rate limits per vendor to prevent abuse
- Audit trail: Complete logging of all external API calls
- GitHub Copilot adapter: Implement adapter for GitHub Copilot context memory
- Additional vendors: Support for other vendor memory APIs (optional)

**Acceptance Criteria:**
- ✅ API keys stored securely in vault (SPEC-054)
- ✅ Per-tenant API key configuration works
- ✅ Rate limiting enforced per vendor
- ✅ Complete audit trail for external API calls
- ✅ GitHub Copilot adapter implemented
- ✅ All operations logged in audit trail
- ✅ >90% test coverage

**Dependencies:**
- Phase 1, 2, 3 complete
- SPEC-054 (Secret Management) - Complete ✅

**Estimated Effort:** 2 weeks (10 story points)
**Priority:** MEDIUM
**Status:** Not Implemented
""",
        "tags": ["spec-129", "phase-4", "security", "api-keys", "rate-limiting", "github-copilot"],
        "priority": "P2",
    },
]


def main():
    print("🔍 SPEC-129: External AI Memory API Integration - Story Creation\n")

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
        search_terms = ["spec-129", subject.split(":")[0].lower()]

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
        print("✅ SPEC-129 stories created successfully!")
        print("\n📋 Story Breakdown:")
        print("   Phase 1: Adapter Layer (3 weeks, HIGH)")
        print("   Phase 2: Federation & Origin Tagging (2 weeks, HIGH)")
        print("   Phase 3: Governance & Admin UI (3 weeks, MEDIUM)")
        print("   Phase 4: Security Infrastructure & Expansion (2 weeks, MEDIUM)")
        print("\n   Total: 10 weeks (50 story points)")
    else:
        print("ℹ️  All stories already exist")


if __name__ == "__main__":
    main()
