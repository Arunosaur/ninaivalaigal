#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-057: Microservice & Config Architecture.

Usage:
    python3 scripts/create_spec057_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "057"
SPEC_TITLE = "Microservice & Config Architecture"


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
    print(f"✅ New status ID: {new_status_id}")

    # Define stories based on SPEC-057 remaining work
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Verify & Upgrade Config Validation to Pydantic",
            "description": """**Objective**: Verify if all service config modules use Pydantic validation, and upgrade if needed.

**Background**:
- SPEC-057 requires Pydantic or similar for config validation
- Current implementation uses dict-based config loading
- Need to verify and upgrade to Pydantic for better validation

**Tasks**:
- [ ] Review all service config modules:
  - `services/core-api/lib/config.py`
  - `services/graph-service/lib/config.py`
  - `services/business-service/lib/config.py`
  - `services/admin-vendor-service/lib/config.py`
- [ ] Verify if Pydantic models are used for config validation
- [ ] If not, create Pydantic models for each service config
- [ ] Add validation rules (required fields, types, ranges)
- [ ] Update config loading to use Pydantic models
- [ ] Test config validation with invalid inputs
- [ ] Update documentation

**Acceptance Criteria**:
- [ ] All service configs use Pydantic BaseModel
- [ ] Config validation catches invalid inputs
- [ ] Error messages are clear and actionable
- [ ] All services start successfully with validated config
- [ ] Documentation updated""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Verify MCP Service Extraction",
            "description": """**Objective**: Verify if MCP logic has been extracted into a standalone service.

**Background**:
- SPEC-057 task: "Extract MCP logic into a service (if not already)"
- Need to verify current MCP service structure
- Check if standalone service entrypoint exists

**Tasks**:
- [ ] Review MCP service directories:
  - `server/mcp/` - Check modular structure
  - `mcp_server/` - Check standalone entrypoint
  - `services/*/lib/mcp/` - Check service-specific MCP
- [ ] Verify if MCP is extracted as standalone service
- [ ] Check for standalone MCP service entrypoint (`mcp_server/main.py`)
- [ ] Verify MCP service can run independently
- [ ] Document current MCP architecture
- [ ] If extraction incomplete, create plan for extraction
- [ ] Update SPEC-057 documentation

**Acceptance Criteria**:
- [ ] MCP service extraction status documented
- [ ] Standalone entrypoint verified or created
- [ ] MCP service can run independently
- [ ] Architecture documented
- [ ] SPEC-057 README updated""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Create Service Relationship Diagram",
            "description": """**Objective**: Create a diagram showing service relationships and dependencies.

**Background**:
- SPEC-057 deliverable: "Diagram of service relationships"
- Needed to visualize microservice architecture
- Helps understand service dependencies and communication patterns

**Tasks**:
- [ ] Identify all microservices:
  - Core API Service
  - Memory Service
  - Graph/AI Service
  - Business Service
  - Admin/Vendor Service
- [ ] Map service dependencies
- [ ] Document communication patterns (HTTP, message bus, etc.)
- [ ] Create diagram showing:
  - Service boundaries
  - Dependencies between services
  - Shared components
  - Configuration flow
- [ ] Include in SPEC-057 documentation
- [ ] Update architecture documentation

**Acceptance Criteria**:
- [ ] Service relationship diagram created
- [ ] All services identified and mapped
- [ ] Dependencies clearly shown
- [ ] Diagram included in SPEC-057 README
- [ ] Architecture documentation updated""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Centralized Config Architecture Documentation",
            "description": """**Objective**: Document the centralized configuration architecture.

**Background**:
- SPEC-057 config infrastructure is mostly complete
- Need comprehensive documentation of:
  - Config loading hierarchy
  - Environment variable precedence
  - Service-specific config patterns
  - Fallback mechanisms

**Tasks**:
- [ ] Document config loading hierarchy:
  - Environment variables (highest priority)
  - Config files
  - Default values (lowest priority)
- [ ] Document service-specific config patterns
- [ ] Create config examples for each service
- [ ] Document fallback mechanisms
- [ ] Create troubleshooting guide
- [ ] Update SPEC-057 README with complete documentation

**Acceptance Criteria**:
- [ ] Config architecture documented
- [ ] Loading hierarchy clearly explained
- [ ] Service-specific patterns documented
- [ ] Examples provided for each service
- [ ] Troubleshooting guide created
- [ ] SPEC-057 README updated""",
            "status": "New",
        },
    ]

    # Create stories
    print("\n4️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: {story_data['subject'][:60]}...")

        status_id = new_status_id if story_data["status"] == "New" else None

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




