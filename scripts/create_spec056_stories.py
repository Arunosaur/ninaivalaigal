#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-056: Dependency & Testing Improvements.

Usage:
    python3 scripts/create_spec056_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "056"
SPEC_TITLE = "Dependency & Testing Improvements"


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": project_slug},
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_status_id(headers, project_id, status_name):
    """Get status ID by name."""
    response = requests.get(
        f"{API_ENDPOINT}/userstory-statuses",
        headers=headers,
        params={"project": project_id},
    )
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def create_story(headers, project_id, subject, description, status_id=None):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": [f"SPEC-{SPEC_NUMBER}"],
    }

    if status_id:
        payload["status"] = status_id

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code} - {response.text[:200]}")
        return None


def main():
    """Main function."""
    print("=" * 80)
    print(f"📋 Creating Taiga Stories for SPEC-{SPEC_NUMBER}")
    print(f"   Project: {PROJECT_SLUG}")
    print(f"   SPEC: {SPEC_TITLE}")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting project...")
    project_id = get_project_id(headers, PROJECT_SLUG)
    print(f"✅ Project ID: {project_id}")

    # Get status IDs
    print("\n3️⃣  Getting status IDs...")
    new_status_id = get_status_id(headers, project_id, "New")
    done_status_id = get_status_id(headers, project_id, "Done")
    print(f"✅ New status ID: {new_status_id}")
    print(f"✅ Done status ID: {done_status_id}")

    # Define stories based on SPEC-056 (implementation is complete, but stories document the work)
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Modern Dependency Management with pip-tools",
            "description": """**Objective**: Implement pip-tools for unified, reproducible dependency management.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- Created `requirements/` directory structure:
  - `base.in` - Production dependencies with version ranges
  - `dev.in` - Development tools (testing, linting, type checking)
  - `test.in` - Testing-specific dependencies
- Implemented version pinning with compatibility ranges
- Created `scripts/manage-deps.sh` for dependency management
- Integrated with Makefile targets

**Key Features**:
- Reproducible builds with `pip-compile` and `pip-sync`
- Separated concerns: base/dev/test environments
- Version compatibility ranges (e.g., `fastapi>=0.114.0,<0.115.0`)

**Deliverables**:
- ✅ Unified `requirements/` directory structure
- ✅ Dependency management script
- ✅ Makefile integration
- ✅ Documentation""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Comprehensive Test Fixtures & Mocks",
            "description": """**Objective**: Replace heavy integration tests with mocks and fixtures for faster, more reliable testing.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- Created `tests/fixtures.py` with comprehensive mock infrastructure:
  - `MockDatabaseManager` - Complete database operations simulation
  - `MockRedisClient` - Redis operations with TTL simulation
  - `MockHttpClient` - External API call mocking with history tracking
  - `TestDataFactory` - Standardized test data creation
- Replaced live integration tests with mocks
- Created `MockContext` for comprehensive mocking context manager
- Added performance testing utilities with pytest-benchmark

**Key Features**:
- Fast, deterministic tests without requiring real services
- Custom assertions (`assert_memory_valid`, `assert_user_valid`)
- Async test support with proper event loop management
- Performance testing capabilities

**Deliverables**:
- ✅ Comprehensive test fixtures
- ✅ Mock infrastructure for all services
- ✅ Example test implementations
- ✅ Performance testing utilities""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Enhanced Makefile Targets for Dependency Management",
            "description": """**Objective**: Provide convenient Makefile targets for dependency management and testing.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- Added Makefile targets:
  - `make deps-compile` - Compile requirements files
  - `make deps-install-dev` - Install development dependencies
  - `make deps-check` - Check for dependency conflicts
  - `make test-with-mocks` - Run tests with comprehensive mocks
  - `make test-fixtures` - Validate test fixtures
- Integrated with `scripts/manage-deps.sh`

**Key Features**:
- Easy-to-use commands for developers
- Consistent workflow across the team
- Automated dependency conflict detection

**Deliverables**:
- ✅ Enhanced Makefile targets
- ✅ Integration with dependency management script
- ✅ Documentation""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Dependency & Testing Improvements Documentation",
            "description": """**Objective**: Document the dependency management and testing improvements.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- Created implementation summary document
- Documented dependency management script usage
- Documented test fixture usage and examples
- Created Makefile command documentation

**Key Documentation**:
- `docs/SPEC_054_056_IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `scripts/manage-deps.sh` - Script usage and examples
- `tests/fixtures.py` - Mock infrastructure documentation
- Example test implementations demonstrating best practices

**Deliverables**:
- ✅ Implementation summary
- ✅ Script documentation
- ✅ Usage examples
- ✅ Best practices guide""",
            "status": "Done",
        },
    ]

    # Create stories
    print("\n4️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: {story_data['subject'][:60]}...")

        status_id = done_status_id if story_data["status"] == "Done" else new_status_id

        created = create_story(
            headers,
            project_id,
            story_data["subject"],
            story_data["description"],
            status_id=status_id,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, story_data["subject"]))
            print(f"   ✅ Created US#{ref}")
        else:
            failed_stories.append(story_data["subject"])
            print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")

    if created_stories:
        print("\nCreated stories:")
        for ref, subject in created_stories:
            print(f"  US#{ref}: {subject[:65]}")

    print("=" * 80)


if __name__ == "__main__":
    main()
