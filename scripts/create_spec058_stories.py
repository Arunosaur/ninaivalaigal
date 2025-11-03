#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Taiga user stories for SPEC-058: Documentation Expansion.

Usage:
    python3 scripts/create_spec058_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "058"
SPEC_TITLE = "Documentation Expansion"


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

    # Define stories based on SPEC-058 (implementation is mostly complete)
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: OpenAPI/Swagger Documentation - Complete",
            "description": """**Objective**: Ensure all services have OpenAPI/Swagger documentation.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- OpenAPI specs exist for all services:
  - `api/docs/openapi.yaml`
  - `services/core-api/openapi.yaml`
  - `shared/contracts/*/v1/openapi.yaml` (5 services)
- Swagger UI endpoints at `/docs` for all services:
  - Core API: http://localhost:13390/docs
  - Business Service: http://localhost:13391/docs
  - Admin/Vendor Service: http://localhost:13392/docs
  - Graph/AI Service: http://localhost:13394/docs
- ReDoc endpoints at `/redoc` for all services
- FastAPI auto-generation working

**Key Features**:
- Auto-generated OpenAPI schemas
- Interactive Swagger UI
- ReDoc documentation
- Service-specific API documentation

**Deliverables**:
- ✅ OpenAPI specifications
- ✅ Swagger UI endpoints
- ✅ ReDoc endpoints
- ✅ FastAPI decorators for documentation""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Service Architecture Diagrams",
            "description": """**Objective**: Create visual service interaction and architecture diagrams.

**Status**: ✅ **COMPLETE** (Documentation exists, visual diagram format optional)

**Completed Work**:
- Architecture documentation exists:
  - `docs/architecture/ARCHITECTURE_OVERVIEW.md`
  - Multiple architecture documents in `docs/architecture/`
  - Service interactions documented in text/diagrams
- Service relationships documented
- Data flow diagrams included

**Remaining Work** (Optional):
- [ ] Create `docs/architecture/diagram.drawio` if visual format needed
- [ ] Enhance existing diagrams with drawio format
- [ ] Create service dependency diagrams

**Current Status**: Documentation covers diagrams in markdown format. Drawio format is optional enhancement.

**Deliverables**:
- ✅ Architecture documentation with diagrams
- ✅ Service interaction documentation
- ⚠️ Optional: drawio format diagram""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Deployment Guide Documentation",
            "description": """**Objective**: Comprehensive deployment guide covering Docker, GH Actions, CI runner, and Apple CLI.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- `deployment/README.md` exists ✅
- `docs/deployment/` directory with multiple guides ✅
- `docs/DEPLOYMENT.md` exists ✅
- Docker deployment documented ✅
- GitHub Actions workflows documented ✅
- CI runner documentation ✅
- Apple CLI integration documented ✅

**Key Documentation**:
- Deployment configuration guide
- Multi-environment deployment strategy
- Container deployment procedures
- CI/CD pipeline documentation
- Apple Container CLI setup

**Deliverables**:
- ✅ Deployment README
- ✅ Docker deployment guide
- ✅ GitHub Actions documentation
- ✅ CI runner setup
- ✅ Apple CLI integration guide""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Developer Documentation Suite",
            "description": """**Objective**: Comprehensive developer documentation for onboarding and contribution.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- `docs/ARCHITECTURE_OVERVIEW.md` - System architecture ✅
- `docs/API_DOCUMENTATION.md` - REST API reference ✅
- `docs/MEMORY_LIFECYCLE.md` - Memory management workflows ✅
- `docs/TESTING_GUIDE.md` - Testing and CI documentation ✅
- `docs/CONTRIBUTING.md` - Developer contribution guidelines ✅
- `docs/SPEC_REFERENCE_MAPPING.md` - SPEC to implementation mapping ✅

**Key Features**:
- Complete architecture documentation
- Comprehensive API reference
- Memory lifecycle workflows
- Testing strategies and CI integration
- Developer onboarding guides
- SPEC implementation mapping

**Deliverables**:
- ✅ Architecture documentation
- ✅ API documentation
- ✅ Memory lifecycle guide
- ✅ Testing guide
- ✅ Contribution guidelines
- ✅ SPEC reference mapping""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: User-Facing Documentation Enhancement",
            "description": """**Objective**: Enhance user-facing documentation for end users (not just developers).

**Background**:
- Developer documentation is complete
- User-facing guides could be enhanced
- COMPLETION_SUMMARY.md notes: `docs/USER_GUIDE.md` - User-facing documentation (planned)

**Tasks**:
- [ ] Create or enhance `docs/USER_GUIDE.md`
- [ ] Create user tutorials and walkthroughs
- [ ] Document end-user features and workflows
- [ ] Create getting started guide for end users
- [ ] Document user-facing features
- [ ] Create FAQ and troubleshooting for users

**Acceptance Criteria**:
- [ ] User guide created or enhanced
- [ ] Getting started guide available
- [ ] User workflows documented
- [ ] FAQ created
- [ ] Troubleshooting guide for users

**Priority**: Medium (complements developer documentation)""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Documentation Maintenance & Quality Review",
            "description": """**Objective**: Regular maintenance and quality review of documentation.

**Background**:
- Documentation is comprehensive and complete
- Regular updates needed as system evolves
- Quality review ensures accuracy

**Tasks**:
- [ ] Review all documentation for accuracy
- [ ] Update outdated information
- [ ] Verify all links are working
- [ ] Ensure code examples are current
- [ ] Update API documentation as APIs evolve
- [ ] Review and update architecture diagrams
- [ ] Ensure consistency across all docs

**Acceptance Criteria**:
- [ ] All documentation reviewed
- [ ] Outdated content updated
- [ ] All links verified
- [ ] Code examples tested
- [ ] Documentation consistency verified

**Priority**: Low (ongoing maintenance)""",
            "status": "New",
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
