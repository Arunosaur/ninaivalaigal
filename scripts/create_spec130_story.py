#!/usr/bin/env python3
"""
Create Taiga story for SPEC-130: Terminal/CLI Auto Context Capture

This script creates a story for SPEC-130 documentation and enhancements.
"""

import os
import sys
from typing import Dict, Optional

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


SPEC_130_DESCRIPTION = """**Goal**: Complete SPEC-130: Terminal/CLI Auto Context Capture documentation and enhancements

**Implementation Status:** ⚠️ Partially Implemented (60%)

**What's Implemented (60%):**
- ✅ Shell Hooks (SPEC-001 FR-010) - Production ready (`adapters/shell_hooks/store_memory.sh`)
- ✅ AutoRecorder Class - CCTV-style recording (`services/*/lib/auto_recording.py`)
- ✅ VS Code Integration - Workspace context detection (implemented)
- ✅ Auto-capture terminal commands with metadata
- ✅ Camera off protection (token/context checks)
- ✅ Multi-shell support (zsh, bash)
- ✅ Context-aware command grouping
- ✅ Secret filtering

**What's Missing (40%):**
- ❌ SPEC-130 Document - Design doc, API contracts, test cases not documented
- ❌ Comprehensive CLI tool (beyond shell hooks)
- ❌ Advanced context detection
- ❌ Command pattern analysis
- ❌ Integration with other IDEs (beyond VS Code)

**Technical Requirements:**

**Phase 1: Documentation (HIGH Priority)**
- Document shell hooks in SPEC-130 (reference SPEC-001 FR-010)
- Document AutoRecorder in SPEC-130
- Document VS Code integration in SPEC-130
- Create comprehensive API contracts
- Document test cases
- Document integration points

**Phase 2: Enhancements (MEDIUM Priority)**
- Create comprehensive CLI tool (beyond shell hooks)
- Implement advanced context detection (auto-detect project context)
- Add command pattern analysis
- Integrate with additional IDEs (JetBrains, etc.)
- Batch command processing
- Command suggestions based on context

**Dependencies:**
- SPEC-001 (Core Memory System) - Complete ✅
- SPEC-007 (Unified Context Scope System) - Complete ✅
- SPEC-012 (Memory Substrate) - Complete ✅

**Acceptance Criteria:**
- ✅ SPEC-130 document complete with all existing implementations documented
- ✅ API contracts documented
- ✅ Test cases documented
- ✅ Integration points documented
- ✅ Comprehensive CLI tool created (optional enhancement)

**Estimated Effort:** 2-3 weeks (10-15 story points)

**Status:** Partially Implemented (60%)
"""


def main():
    print("🔍 SPEC-130: Terminal/CLI Auto Context Capture - Story Creation\n")

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

    # Check for existing story
    print("🔍 Checking for existing SPEC-130 story...")
    existing_story = find_story_by_subject_or_tags(token, project_id, ["spec-130", "terminal cli", "auto context"])

    if existing_story:
        story_id = existing_story.get("id")
        story_ref = existing_story.get("ref", "N/A")
        print(f"   ✅ Found existing story: US#{story_ref} (ID: {story_id})")
        print(f"   ℹ️  Skipping (story already exists)")
    else:
        print("   ❌ Story not found, creating new story...")

        # Create new story
        story_data = {
            "project": project_id,
            "subject": "SPEC-130: Terminal/CLI Auto Context Capture - Documentation & Enhancements",
            "description": SPEC_130_DESCRIPTION,
            "tags": ["spec-130", "terminal-cli", "auto-context", "cli-capture", "shell-hooks"],
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

    print("\n✅ SPEC-130 story creation complete!")


if __name__ == "__main__":
    main()

