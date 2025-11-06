#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga stories for SPEC-110: Release Workflow — Multi-Arch Build & Publish to GHCR
# Assigns stories to Developer C

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
DEVELOPER_C_USERNAME = "developer-c"

# SPEC-110 stories to create
STORIES = [
    {
        "subject": "SPEC-110: Add Trivy security scanning to release workflow",
        "description": """**Goal**: Integrate Trivy security scanning into GitHub Actions release workflow

**Context**: SPEC-110 requires Trivy scan that fails on HIGH/CRITICAL vulnerabilities before publishing to GHCR.

**Tasks**:
- [ ] Add Trivy action to `.github/workflows/release-containers.yml`
- [ ] Configure Trivy to scan container images after build
- [ ] Set failure threshold to HIGH/CRITICAL vulnerabilities
- [ ] Configure Trivy to scan both amd64 and arm64 images
- [ ] Add Trivy scan results to release summary
- [ ] Test Trivy scanning in workflow
- [ ] Document Trivy configuration

**Acceptance Criteria**:
- ✅ Trivy scan runs in release workflow
- ✅ Workflow fails on HIGH or CRITICAL vulnerabilities
- ✅ Trivy scans both amd64 and arm64 images
- ✅ Scan results included in release summary
- ✅ Workflow tested and working

**Reference**: SPEC-110 Section 1 (Pipeline Stages)""",
        "tags": ["spec-110", "trivy", "security-scanning", "ci-cd", "github-actions"],
    },
    {
        "subject": "SPEC-110: Add Cosign signing and SBOM attestation to release workflow",
        "description": """**Goal**: Sign container images and generate SBOM attestations using Cosign

**Context**: SPEC-110 requires Cosign signing and SBOM attestation via syft for supply chain security.

**Tasks**:
- [ ] Install Cosign in GitHub Actions workflow
- [ ] Install syft for SBOM generation
- [ ] Generate SBOM for each container image using syft
- [ ] Sign container images with Cosign (keyless or key-based)
- [ ] Attach SBOM as Cosign attestation
- [ ] Push signed images and attestations to GHCR
- [ ] Configure COSIGN_KEY secret or keyless fulcio
- [ ] Test Cosign signing and attestation
- [ ] Document signing process

**Acceptance Criteria**:
- ✅ Cosign installed and configured in workflow
- ✅ syft generates SBOM for all images
- ✅ Images signed with Cosign
- ✅ SBOM attached as Cosign attestation
- ✅ Signed images and attestations pushed to GHCR
- ✅ Workflow tested and working

**Reference**: SPEC-110 Section 1 (Pipeline Stages), Section 3 (Required Secrets)""",
        "tags": ["spec-110", "cosign", "sbom", "syft", "signing", "attestation", "ci-cd"],
    },
    {
        "subject": "SPEC-110: Update release workflow to use SPEC-109 tagging conventions",
        "description": """**Goal**: Ensure release workflow uses SPEC-109 tagging strategy (semver, channel, meta tags)

**Context**: SPEC-110 requires tags from SPEC-109 (semantic versioning, channel tags, meta tags).

**Tasks**:
- [ ] Update workflow to extract semantic version from git tag
- [ ] Tag images with semantic version (vX.Y.Z)
- [ ] Tag images with channel tags (dev/test/prod/latest)
- [ ] Tag images with meta tags (sha-{short_sha}_{date})
- [ ] Ensure PRs produce `:dev` + `:sha-*` tags
- [ ] Ensure `:latest` only on protected branch
- [ ] Test tagging strategy in workflow
- [ ] Document tagging workflow

**Acceptance Criteria**:
- ✅ Images tagged with semantic version (vX.Y.Z)
- ✅ Images tagged with channel tags (dev/test/prod/latest)
- ✅ Images tagged with meta tags (sha-{short_sha}_{date})
- ✅ PRs produce `:dev` and `:sha-*` tags
- ✅ `:latest` only on protected branch
- ✅ All tags pushed to GHCR
- ✅ Tagging strategy matches SPEC-109

**Reference**: SPEC-110 Section 1 (Pipeline Stages), Section 4 (Acceptance), SPEC-109""",
        "tags": ["spec-110", "tagging", "spec-109", "semantic-versioning", "ci-cd"],
    },
    {
        "subject": "SPEC-110: Enhance release notes with image digests per architecture",
        "description": """**Goal**: Include image digests per architecture in release notes

**Context**: SPEC-110 requires release notes to include image digests per arch for traceability.

**Tasks**:
- [ ] Extract image digests after build
- [ ] Extract digests for both amd64 and arm64 architectures
- [ ] Format digests in release summary
- [ ] Include digests in GitHub release notes
- [ ] Test digest extraction and formatting
- [ ] Document digest format

**Acceptance Criteria**:
- ✅ Release notes include image digests
- ✅ Digests shown for both amd64 and arm64
- ✅ Digest format is clear and readable
- ✅ Release summary includes digests
- ✅ GitHub release notes include digests

**Reference**: SPEC-110 Section 4 (Acceptance)""",
        "tags": ["spec-110", "release-notes", "digests", "traceability", "ci-cd"],
    },
]


def get_user_id(importer, username):
    """Get user ID by username - checks project members first, then global users."""
    print(f"   Looking up user: {username}")
    import requests

    headers = importer._get_headers()

    # First, try to get from project members
    project = importer.get_project(PROJECT_SLUG)
    if project:
        members_url = f"{importer.base_url}/projects/{project['id']}/members"
        try:
            response = requests.get(members_url, headers=headers)
            if response.status_code == 200:
                members = response.json()
                for member in members:
                    user = member.get("user", {})
                    if user.get("username", "").lower() == username.lower():
                        user_id = user.get("id")
                        print(f"   ✅ Found user in project members: {user.get('username')} (ID: {user_id})")
                        return user_id
        except Exception as e:
            print(f"⚠️  Error getting project members: {e}")

    # Fallback: search global users list
    print(f"   User not in project members, searching global users...")
    users_url = f"{importer.base_url}/users"
    try:
        response = requests.get(users_url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("username", "").lower() == username.lower():
                    user_id = user.get("id")
                    print(f"   ✅ Found user in global users: {user.get('username')} (ID: {user_id})")
                    print(f"   ⚠️  Note: User exists but may not be a project member")
                    return user_id
    except Exception as e:
        print(f"⚠️  Error getting global users: {e}")

    print(f"   ❌ User '{username}' not found")
    return None


def create_story(importer, story_data, developer_c_id, project_id, status_id):
    """Create a user story in Taiga."""
    story_url = f"{importer.base_url}/userstories"
    headers = importer._get_headers()

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "assigned_to": developer_c_id,
        "status": status_id,
        "tags": story_data.get("tags", []),
    }

    import requests

    response = requests.post(story_url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        story = response.json()
        print(f"   ✅ Created story: US#{story.get('ref', '?')} - {story.get('subject', '')}")
        return story
    else:
        print(f"   ❌ Failed to create story: {response.status_code}")
        print(response.text)
        return None


def main():
    print("🚀 Creating Taiga stories for SPEC-110: Release Workflow — Multi-Arch Build & Publish to GHCR")
    print("=" * 80)

    # Initialize importer
    importer = TaigaImporter(API_ENDPOINT, username=TAIGA_USERNAME, password=TAIGA_PASSWORD)
    print("✅ Authenticated with Taiga")

    # Get project
    project = importer.get_project(PROJECT_SLUG)
    if not project:
        print(f"❌ Project not found: {PROJECT_SLUG}")
        sys.exit(1)

    project_id = project["id"]
    print(f"✅ Found project: {project.get('name')} (ID: {project_id})")

    # Get Developer C user ID
    developer_c_id = get_user_id(importer, DEVELOPER_C_USERNAME)
    if not developer_c_id:
        print(f"⚠️  Developer C ({DEVELOPER_C_USERNAME}) not found, will use admin")
        # Get admin user ID as fallback
        import requests

        headers = importer._get_headers()
        me_url = f"{importer.base_url}/users/me"
        response = requests.get(me_url, headers=headers)
        if response.status_code == 200:
            developer_c_id = response.json().get("id")
            print(f"   Using admin user ID: {developer_c_id}")
        else:
            print("❌ Could not get user ID")
            sys.exit(1)
    else:
        print(f"✅ Found Developer C: {developer_c_id}")

    # Get "New" or "Ready" status ID
    import requests

    headers = importer._get_headers()
    statuses_url = f"{importer.base_url}/userstory-statuses?project={project_id}"
    response = requests.get(statuses_url, headers=headers)

    if response.status_code != 200:
        print("❌ Failed to get statuses")
        sys.exit(1)

    statuses = response.json()
    status_id = None
    for status in statuses:
        if status["name"].lower() in ["new", "ready", "in progress"]:
            status_id = status["id"]
            print(f"✅ Using status: {status['name']} (ID: {status_id})")
            break

    if not status_id:
        print("⚠️  No suitable status found, using first available")
        status_id = statuses[0]["id"] if statuses else None

    # Create stories
    created_stories = []
    for story_data in STORIES:
        story = create_story(importer, story_data, developer_c_id, project_id, status_id)
        if story:
            created_stories.append(story)

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Created {len(created_stories)}/{len(STORIES)} stories for SPEC-110")

    if created_stories:
        print("\n📋 Created Stories:")
        for story in created_stories:
            story_ref = story.get("ref", "?")
            story_subject = story.get("subject", "")
            print(f"   - US#{story_ref}: {story_subject}")

    print("\n🎯 Next Steps:")
    print("   1. Update SPEC-110 README.md to reference these stories")
    print("   2. Update SPEC-110 status (currently Draft, should be In Progress)")
    print("   3. Assign stories to Developer C (already done)")
    print("   4. Begin implementation work")


if __name__ == "__main__":
    main()
