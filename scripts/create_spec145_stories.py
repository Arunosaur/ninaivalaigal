#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga stories for SPEC-145: Multi-Runtime Multi-Architecture Builds
# Assigns stories to Developer D

import os
import sys
from pathlib import Path

# Add tasks/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tasks" / "scripts"))

try:
    from taiga_import_tasks import TaigaImporter
except ImportError:
    print("❌ Failed to import TaigaImporter")
    sys.exit(1)

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"
DEVELOPER_D_USERNAME = "developer-d"

# SPEC-145 stories to create
STORIES = [
    {
        "subject": "SPEC-145: Update ports.nv.yaml with all microservice ports",
        "description": """**Goal**: Ensure port matrix covers all runtime/architecture/environment combinations

**Tasks**:
- [ ] Verify Docker dev/test/prod microservice ports
- [ ] Verify Colima dev/test/prod microservice ports
- [ ] Verify Apple test/prod microservice ports
- [ ] Validate no port collisions
- [ ] Update port documentation

**Acceptance Criteria**:
- All 18 combinations have ports (3 runtimes × 3 envs × 6 services)
- Ports follow SPEC-086 formula
- No collisions detected
- Documentation updated""",
        "tags": ["spec-145", "ports", "infrastructure"],
    },
    {
        "subject": "SPEC-145: Create Docker build scripts (ARM64 + x86-64)",
        "description": """**Goal**: Build scripts for Docker runtime supporting both architectures

**Tasks**:
- [ ] Create `scripts/build-docker-service.sh` (single service)
- [ ] Create `scripts/build-docker-all.sh` (all services)
- [ ] Support ARM64 builds (`--platform linux/arm64`)
- [ ] Support x86-64 builds (`--platform linux/amd64`)
- [ ] Support multi-arch builds (buildx)
- [ ] Test all 6 services

**Acceptance Criteria**:
- Scripts build all services for ARM64
- Scripts build all services for x86-64
- Multi-arch builds work with buildx
- All builds succeed
- Images tagged correctly""",
        "tags": ["spec-145", "docker", "build-scripts", "arm64", "x86-64"],
    },
    {
        "subject": "SPEC-145: Create Colima build scripts (ARM64 + x86-64)",
        "description": """**Goal**: Build scripts for Colima runtime supporting both architectures

**Tasks**:
- [ ] Create `scripts/build-colima-service.sh` (single service)
- [ ] Create `scripts/build-colima-all.sh` (all services)
- [ ] Support ARM64 builds
- [ ] Support x86-64 builds
- [ ] Test all 6 services
- [ ] Verify Colima compatibility

**Acceptance Criteria**:
- Scripts build all services for ARM64
- Scripts build all services for x86-64
- All builds succeed
- Images work with Colima runtime
- Images tagged correctly""",
        "tags": ["spec-145", "colima", "build-scripts", "arm64", "x86-64"],
    },
    {
        "subject": "SPEC-145: Create unified multi-runtime build script",
        "description": """**Goal**: Single script that builds for all runtimes and architectures

**Tasks**:
- [ ] Create `scripts/build-all-runtimes.sh`
- [ ] Support Docker (ARM64 + x86-64)
- [ ] Support Colima (ARM64 + x86-64)
- [ ] Support Apple Container CLI (ARM64)
- [ ] Command-line options for runtime/arch selection
- [ ] Comprehensive logging and reporting

**Acceptance Criteria**:
- Script builds for all requested runtimes
- Script builds for all requested architectures
- Clear output and error handling
- Supports selective builds (--runtime, --arch)
- All builds succeed""",
        "tags": ["spec-145", "build-scripts", "automation"],
    },
    {
        "subject": "SPEC-145: Create Docker documentation (ARM64 + x86-64)",
        "description": """**Goal**: Complete documentation for Docker builds

**Tasks**:
- [ ] Update `how-to/container-builds/docker/00-OVERVIEW.md`
- [ ] Create service-specific guides with ARM64 + x86-64 instructions
- [ ] Document architecture-specific considerations
- [ ] Include troubleshooting for both architectures
- [ ] Add examples for both architectures

**Acceptance Criteria**:
- All 6 services documented
- ARM64 build instructions complete
- x86-64 build instructions complete
- Architecture differences documented
- Examples work for both architectures""",
        "tags": ["spec-145", "docker", "documentation", "arm64", "x86-64"],
    },
    {
        "subject": "SPEC-145: Create Colima documentation (ARM64 + x86-64)",
        "description": """**Goal**: Complete documentation for Colima builds

**Tasks**:
- [ ] Update `how-to/container-builds/colima/00-OVERVIEW.md`
- [ ] Create service-specific guides with ARM64 + x86-64 instructions
- [ ] Document Colima-specific considerations
- [ ] Include troubleshooting for both architectures
- [ ] Add examples for both architectures

**Acceptance Criteria**:
- All 6 services documented
- ARM64 build instructions complete
- x86-64 build instructions complete
- Colima-specific notes included
- Examples work for both architectures""",
        "tags": ["spec-145", "colima", "documentation", "arm64", "x86-64"],
    },
    {
        "subject": "SPEC-145: Test and validate all build combinations",
        "description": """**Goal**: Comprehensive testing of all runtime/architecture combinations

**Tasks**:
- [ ] Test Docker ARM64 builds for all 6 services
- [ ] Test Docker x86-64 builds for all 6 services
- [ ] Test Colima ARM64 builds for all 6 services
- [ ] Test Colima x86-64 builds for all 6 services
- [ ] Test Apple Container CLI ARM64 builds (already working)
- [ ] Validate port assignments work correctly
- [ ] Test cross-runtime compatibility

**Acceptance Criteria**:
- All 18 combinations tested (3 runtimes × 3 envs × 2 archs)
- All builds succeed
- All services can run simultaneously
- No port conflicts
- Health checks pass for all combinations""",
        "tags": ["spec-145", "testing", "validation"],
    },
]


def get_user_id(importer, username):
    """Get user ID by username."""
    # Try to get from project members
    project = importer.get_project(PROJECT_SLUG)
    if not project:
        return None

    # Get project members via API
    import requests

    headers = importer._get_headers()
    members_url = f"{importer.base_url}/projects/{project['id']}/members"

    try:
        response = requests.get(members_url, headers=headers)
        if response.status_code == 200:
            members = response.json()
            for member in members:
                user = member.get("user", {})
                if user.get("username", "").lower() == username.lower():
                    return user.get("id")
    except Exception as e:
        print(f"⚠️  Error getting members: {e}")

    return None


def create_story(importer, story_data, developer_d_id, project_id, status_id):
    """Create a user story in Taiga."""
    story_url = f"{importer.base_url}/userstories"
    headers = importer._get_headers()

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "assigned_to": developer_d_id,
        "status": status_id,
        "tags": story_data["tags"],
    }

    import requests

    response = requests.post(story_url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 80)
    print("Creating SPEC-145 Taiga Stories")
    print("=" * 80)
    print()

    # Initialize importer
    importer = TaigaImporter(API_ENDPOINT, username=TAIGA_USERNAME, password=TAIGA_PASSWORD)
    print("✅ Authenticated with Taiga")

    # Get project
    project = importer.get_project(PROJECT_SLUG)
    if not project:
        print(f"❌ Project not found: {PROJECT_SLUG}")
        return 1

    project_id = project["id"]
    print(f"✅ Found project: {project.get('name')} (ID: {project_id})")

    # Get Developer D user ID
    developer_d_id = get_user_id(importer, DEVELOPER_D_USERNAME)
    if not developer_d_id:
        print(f"⚠️  Developer D ({DEVELOPER_D_USERNAME}) not found, will use admin")
        # Get admin user ID as fallback
        import requests

        headers = importer._get_headers()
        me_url = f"{importer.base_url}/users/me"
        response = requests.get(me_url, headers=headers)
        if response.status_code == 200:
            developer_d_id = response.json().get("id")
            print(f"   Using admin user ID: {developer_d_id}")
        else:
            print("❌ Could not get user ID")
            return 1
    else:
        print(f"✅ Found Developer D: {developer_d_id}")

    # Get "New" or "Ready" status ID
    import requests

    headers = importer._get_headers()
    statuses_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
    response = requests.get(statuses_url, headers=headers)

    if response.status_code != 200:
        print("❌ Failed to get statuses")
        return 1

    statuses = response.json()
    status_id = None
    for status in statuses:
        name_lower = status.get("name", "").lower()
        if name_lower in ["new", "ready"]:
            status_id = status["id"]
            break

    if not status_id and statuses:
        status_id = statuses[0]["id"]  # Use first available

    print(f"✅ Using status ID: {status_id}")
    print()

    # Create stories
    print("Creating stories...")
    print("=" * 80)

    created = []
    failed = []

    for i, story_data in enumerate(STORIES, 1):
        print(f"\n{i}. Creating: {story_data['subject']}")

        story = create_story(importer, story_data, developer_d_id, project_id, status_id)

        if story:
            ref = story.get("ref", "N/A")
            print(f"   ✅ Created US#{ref}")
            created.append((ref, story_data["subject"]))
        else:
            print(f"   ❌ Failed to create")
            failed.append(story_data["subject"])

    # Summary
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\n✅ Created: {len(created)}")
    for ref, subject in created:
        print(f"   US#{ref}: {subject[:60]}...")

    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for subject in failed:
            print(f"   {subject[:60]}...")

    print()
    print(f"View stories at: {TAIGA_URL}/project/{PROJECT_SLUG}/backlog")
    print("=" * 80)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
