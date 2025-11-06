#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga stories for SPEC-109: Environment Naming, Tagging & Versioning
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

# SPEC-109 stories to create
STORIES = [
    {
        "subject": "SPEC-109: Enforce network naming convention ({{env}}-ninaivalaigal-net)",
        "description": """**Goal**: Ensure all networks follow the SPEC-109 naming pattern

**Context**: SPEC-109 requires network naming: `{{env}}-ninaivalaigal-net`

**Tasks**:
- [ ] Update Docker Compose files to use network naming
- [ ] Update Docker network creation commands
- [ ] Update Colima network setup
- [ ] Update Apple Container CLI network setup
- [ ] Verify network naming in all runtime environments
- [ ] Document network naming convention

**Examples**:
- `dev-ninaivalaigal-net`
- `test-ninaivalaigal-net`
- `prod-ninaivalaigal-net`

**Acceptance Criteria**:
- ✅ All networks follow `{{env}}-ninaivalaigal-net` pattern
- ✅ Environment variable `{{env}}` is correctly substituted
- ✅ Network naming consistent across Docker/Colima/Apple
- ✅ Services can communicate on same network
- ✅ Documentation updated

**Reference**: SPEC-109 Section 1 (Naming)""",
        "tags": ["spec-109", "network-naming", "naming-convention", "infrastructure"],
    },
    {
        "subject": "SPEC-109: Enforce volume naming convention (ninaivalaigal-{{env}}-{{service}}-data)",
        "description": """**Goal**: Standardize volume names across all environments

**Context**: SPEC-109 requires volume naming: `ninaivalaigal-{{env}}-{{service}}-data`

**Tasks**:
- [ ] Update Docker Compose files to use volume naming
- [ ] Update Docker volume creation commands
- [ ] Update Colima volume setup
- [ ] Update Apple Container CLI volume setup
- [ ] Verify volume naming in all runtime environments
- [ ] Document volume naming convention

**Examples**:
- `ninaivalaigal-dev-db-data`
- `ninaivalaigal-test-redis-data`
- `ninaivalaigal-prod-api-data`

**Acceptance Criteria**:
- ✅ All volumes follow `ninaivalaigal-{{env}}-{{service}}-data` pattern
- ✅ Environment variable `{{env}}` is correctly substituted
- ✅ Service name `{{service}}` matches service identifier
- ✅ Volume naming consistent across Docker/Colima/Apple
- ✅ Documentation updated

**Reference**: SPEC-109 Section 1 (Naming)""",
        "tags": ["spec-109", "volume-naming", "naming-convention", "infrastructure"],
    },
    {
        "subject": "SPEC-109: Ensure all containers report SERVICE_NAME, SERVICE_VERSION, SERVICE_ENV env vars",
        "description": """**Goal**: Every running container reports standardized environment variables

**Context**: SPEC-109 requires all containers to report `SERVICE_NAME`, `SERVICE_VERSION`, `SERVICE_ENV` for audit and monitoring.

**Tasks**:
- [ ] Update all Dockerfiles to set SERVICE_NAME env var
- [ ] Update all Dockerfiles to set SERVICE_VERSION env var
- [ ] Update all Dockerfiles to set SERVICE_ENV env var
- [ ] Update all startup scripts to pass these env vars
- [ ] Verify containers report these variables
- [ ] Update health check endpoints to include version info
- [ ] Test across all services (Core API, Memory Service, Graph Service, etc.)

**Acceptance Criteria**:
- ✅ All containers have `SERVICE_NAME` environment variable set
- ✅ All containers have `SERVICE_VERSION` environment variable set
- ✅ All containers have `SERVICE_ENV` environment variable set
- ✅ Variables are correctly set in all runtime environments
- ✅ Health endpoints can report version information
- ✅ Audit script can read these variables

**Reference**: SPEC-109 Section 5 (Acceptance)""",
        "tags": ["spec-109", "environment-variables", "service-version", "monitoring"],
    },
    {
        "subject": "SPEC-109: Implement semantic versioning tags (vMAJOR.MINOR.PATCH)",
        "description": """**Goal**: Tag container images with semantic version numbers

**Context**: SPEC-109 requires semantic versioning tags: `vMAJOR.MINOR.PATCH`

**Tasks**:
- [ ] Update build scripts to generate semantic version tags
- [ ] Integrate version tagging with CI/CD pipeline
- [ ] Tag images with version from package.json/pyproject.toml/Cargo.toml
- [ ] Ensure version tags are pushed to GHCR
- [ ] Test version tagging in build pipeline
- [ ] Document version tagging process

**Examples**:
- `ghcr.io/medhasys/ninaivalaigal-api:v1.4.2`
- `ghcr.io/medhasys/ninaivalaigal-memory-service:v0.1.0`

**Acceptance Criteria**:
- ✅ All images tagged with semantic version (vX.Y.Z)
- ✅ Version extracted from project files automatically
- ✅ Version tags pushed to GHCR registry
- ✅ Build scripts support version tagging
- ✅ CI/CD pipeline generates version tags

**Reference**: SPEC-109 Section 2 (Tags)""",
        "tags": ["spec-109", "semantic-versioning", "tags", "ci-cd", "ghcr"],
    },
    {
        "subject": "SPEC-109: Implement channel tags (latest, dev, test, prod)",
        "description": """**Goal**: Tag container images with channel tags for promotion workflow

**Context**: SPEC-109 requires channel tags: `latest`, `dev`, `test`, `prod`

**Tasks**:
- [ ] Update build scripts to tag with channel tags
- [ ] Implement promotion workflow (dev → test → prod)
- [ ] Tag images with `dev` on PR builds
- [ ] Tag images with `test` after testing
- [ ] Tag images with `prod` after production deployment
- [ ] Tag images with `latest` for most recent stable version
- [ ] Update CI/CD pipeline to handle channel tagging
- [ ] Document promotion workflow

**Examples**:
- `ghcr.io/medhasys/ninaivalaigal-api:dev`
- `ghcr.io/medhasys/ninaivalaigal-api:test`
- `ghcr.io/medhasys/ninaivalaigal-api:prod`
- `ghcr.io/medhasys/ninaivalaigal-api:latest`

**Acceptance Criteria**:
- ✅ Images tagged with channel tags (dev/test/prod/latest)
- ✅ Promotion workflow implemented (dev → test → prod)
- ✅ CI/CD pipeline handles channel tagging
- ✅ Channel tags pushed to GHCR registry
- ✅ Documentation updated with promotion workflow

**Reference**: SPEC-109 Section 2 (Tags), Section 4 (Promotion Workflow)""",
        "tags": ["spec-109", "channel-tags", "promotion-workflow", "ci-cd"],
    },
    {
        "subject": "SPEC-109: Implement meta tags (sha-{short_sha}_{date})",
        "description": """**Goal**: Tag container images with metadata tags for traceability

**Context**: SPEC-109 requires meta tags: `sha-{short_sha}_{date}`

**Tasks**:
- [ ] Update build scripts to generate meta tags
- [ ] Extract short SHA from git commit
- [ ] Format date as YYYY-MM-DD
- [ ] Tag images with meta tag format
- [ ] Ensure meta tags are pushed to GHCR
- [ ] Test meta tag generation
- [ ] Document meta tag format

**Examples**:
- `ghcr.io/medhasys/ninaivalaigal-api:sha-1a2b3c4_2025-10-10`
- `ghcr.io/medhasys/ninaivalaigal-memory-service:sha-abc123f_2025-11-04`

**Acceptance Criteria**:
- ✅ Images tagged with meta tags (sha-{short_sha}_{date})
- ✅ Short SHA extracted from git commit (7 characters)
- ✅ Date formatted as YYYY-MM-DD
- ✅ Meta tags pushed to GHCR registry
- ✅ Build scripts generate meta tags automatically
- ✅ Documentation updated

**Reference**: SPEC-109 Section 2 (Tags)""",
        "tags": ["spec-109", "meta-tags", "traceability", "git-sha", "tags"],
    },
    {
        "subject": "SPEC-109: Create audit script to map running containers to GHCR tags",
        "description": """**Goal**: Create script to audit running containers and map them to GHCR image tags

**Context**: SPEC-109 requires an audit script that can map running pods/containers to GHCR tags.

**Tasks**:
- [ ] Create `/scripts/audit-container-tags.sh` script
- [ ] Query running containers for image names
- [ ] Extract SERVICE_NAME, SERVICE_VERSION, SERVICE_ENV from containers
- [ ] Map container images to GHCR tags
- [ ] Generate audit report (JSON/text)
- [ ] Support Docker, Colima, and Apple Container CLI
- [ ] Test audit script across all runtimes
- [ ] Document audit script usage

**Acceptance Criteria**:
- ✅ Audit script exists in `/scripts/audit-container-tags.sh`
- ✅ Script can list all running containers
- ✅ Script can extract image tags and metadata
- ✅ Script can map containers to GHCR tags
- ✅ Script generates human-readable report
- ✅ Script works with Docker, Colima, and Apple Container CLI
- ✅ Documentation updated

**Reference**: SPEC-109 Section 5 (Acceptance)""",
        "tags": ["spec-109", "audit-script", "container-mapping", "ghcr", "scripts"],
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
    print("🚀 Creating Taiga stories for SPEC-109: Environment Naming, Tagging & Versioning")
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
    print(f"✅ Created {len(created_stories)}/{len(STORIES)} stories for SPEC-109")

    if created_stories:
        print("\n📋 Created Stories:")
        for story in created_stories:
            story_ref = story.get("ref", "?")
            story_subject = story.get("subject", "")
            print(f"   - US#{story_ref}: {story_subject}")

    print("\n🎯 Next Steps:")
    print("   1. Update SPEC-109 README.md to reference these stories")
    print("   2. Update SPEC-109 status (currently Draft, should be In Progress)")
    print("   3. Assign stories to Developer C (already done)")
    print("   4. Begin implementation work")


if __name__ == "__main__":
    main()
