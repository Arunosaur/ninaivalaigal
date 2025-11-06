#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Create Taiga stories for SPEC-107: Unified Runtime Parity & Deployment Standard
# Assigns stories to Developer F

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
DEVELOPER_F_USERNAME = "developer-f"

# SPEC-107 stories to create
STORIES = [
    {
        "subject": "SPEC-107: Implement gunicorn.conf.py with environment-based configuration",
        "description": """**Goal**: Create gunicorn configuration that provides TRUE runtime parity across dev/test/prod

**Context**: SPEC-107 requires same process manager (gunicorn + uvicorn workers) in ALL environments. Only worker count and reload differ.

**Tasks**:
- [ ] Create/update `gunicorn.conf.py` in each FastAPI service
- [ ] Configure worker count by environment:
  - Dev: 1 worker, `reload=True`
  - Test: 1 worker, `reload=False`
  - Prod: 4+ workers (CPU-based), `reload=False`
- [ ] Read `ENV` environment variable to determine settings
- [ ] Set worker_class to `uvicorn.workers.UvicornWorker`
- [ ] Configure timeout, log level, bind address

**Acceptance Criteria**:
- ✅ `gunicorn.conf.py` exists in all FastAPI services
- ✅ Worker count automatically adjusts based on `ENV` variable
- ✅ Reload enabled only in dev environment
- ✅ Same command works in all environments: `gunicorn main:app -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py`
- ✅ Configuration tested in dev/test/prod

**Reference**: `specs/107-unified-runtime-parity/gunicorn.conf.py` (reference implementation)""",
        "tags": ["spec-107", "gunicorn", "runtime-parity", "process-manager"],
    },
    {
        "subject": "SPEC-107: Update all FastAPI services to use gunicorn in all environments",
        "description": """**Goal**: Ensure all FastAPI services use gunicorn + uvicorn workers in dev/test/prod

**Context**: SPEC-107 requires TRUE PARITY - same process manager everywhere. No more `uvicorn` in dev, `gunicorn` in prod.

**Tasks**:
- [ ] Update Core API service startup scripts
- [ ] Update Graph Service startup scripts
- [ ] Update Business Service startup scripts
- [ ] Update Admin Vendor Service startup scripts
- [ ] Remove any `uvicorn` direct usage in production
- [ ] Update Dockerfiles to use gunicorn
- [ ] Update Docker Compose files to use gunicorn
- [ ] Update startup scripts to use gunicorn

**Services to Update**:
- `services/core-api/`
- `services/graph-service/`
- `services/business-service/`
- `services/admin-vendor-service/`

**Acceptance Criteria**:
- ✅ All FastAPI services use `gunicorn main:app -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py`
- ✅ No service uses `uvicorn` directly in any environment
- ✅ Same startup command works in dev/test/prod
- ✅ Services start correctly in all environments
- ✅ Health checks pass in all environments

**Reference**: SPEC-107 Section 2 (Standard)""",
        "tags": ["spec-107", "gunicorn", "fastapi", "runtime-parity", "services"],
    },
    {
        "subject": "SPEC-107: Enforce container naming convention (ninaivalaigal-{{env}}-{{service}})",
        "description": """**Goal**: Standardize container names across all environments

**Context**: SPEC-107 requires container naming: `ninaivalaigal-{{env}}-{{service}}`

**Tasks**:
- [ ] Update Docker Compose files to use naming convention
- [ ] Update Docker run commands to use naming convention
- [ ] Update Colima startup scripts
- [ ] Update Apple Container CLI startup scripts
- [ ] Verify naming in all runtime environments (Docker/Colima/Apple)
- [ ] Document naming convention

**Examples**:
- `ninaivalaigal-dev-api`
- `ninaivalaigal-test-graph-service`
- `ninaivalaigal-prod-memory-service`

**Acceptance Criteria**:
- ✅ All containers follow `ninaivalaigal-{{env}}-{{service}}` pattern
- ✅ Environment variable `{{env}}` is correctly substituted
- ✅ Service name `{{service}}` matches service identifier
- ✅ Naming consistent across Docker/Colima/Apple
- ✅ Documentation updated

**Reference**: SPEC-107 Section 2 (Standard)""",
        "tags": ["spec-107", "container-naming", "naming-convention", "infrastructure"],
    },
    {
        "subject": "SPEC-107: Enforce network naming convention ({{env}}-ninaivalaigal-net)",
        "description": """**Goal**: Standardize network names across all environments

**Context**: SPEC-107 requires network naming: `{{env}}-ninaivalaigal-net`

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

**Reference**: SPEC-107 Section 2 (Standard)""",
        "tags": ["spec-107", "network-naming", "naming-convention", "infrastructure"],
    },
    {
        "subject": "SPEC-107: Update Dockerfiles to use gunicorn for all environments",
        "description": """**Goal**: Ensure Dockerfiles use gunicorn in all environments

**Tasks**:
- [ ] Update `Dockerfile` files in all FastAPI services
- [ ] Change CMD from `uvicorn` to `gunicorn`
- [ ] Ensure `gunicorn.conf.py` is copied into image
- [ ] Ensure `ENV` environment variable is available
- [ ] Test Docker builds for dev/test/prod
- [ ] Verify images work correctly

**Acceptance Criteria**:
- ✅ All Dockerfiles use `gunicorn main:app -k uvicorn.workers.UvicornWorker -c gunicorn.conf.py`
- ✅ `gunicorn.conf.py` is included in Docker images
- ✅ `ENV` variable is set in Dockerfiles or passed at runtime
- ✅ Docker images build successfully
- ✅ Containers start correctly with gunicorn

**Reference**: SPEC-107 Section 2 (Standard), `specs/107-unified-runtime-parity/Dockerfile`""",
        "tags": ["spec-107", "dockerfile", "gunicorn", "docker", "containerization"],
    },
    {
        "subject": "SPEC-107: Update Docker Compose files for runtime parity",
        "description": """**Goal**: Ensure Docker Compose uses gunicorn and follows naming conventions

**Tasks**:
- [ ] Update `docker-compose.yml` files to use gunicorn
- [ ] Set container names using `ninaivalaigal-{{env}}-{{service}}`
- [ ] Set network names using `{{env}}-ninaivalaigal-net`
- [ ] Ensure `ENV` variable is passed to containers
- [ ] Remove any environment-specific command differences
- [ ] Test in dev/test/prod

**Acceptance Criteria**:
- ✅ All docker-compose files use gunicorn command
- ✅ Container names follow naming convention
- ✅ Network names follow naming convention
- ✅ Same compose file works in dev/test/prod (only ENV differs)
- ✅ Services start correctly

**Reference**: SPEC-107 Section 2 (Standard), `specs/107-unified-runtime-parity/docker-compose.yml`""",
        "tags": ["spec-107", "docker-compose", "runtime-parity", "containerization"],
    },
    {
        "subject": "SPEC-107: Verify dev/test/prod runtime parity",
        "description": """**Goal**: Test and verify that same code runs identically in dev/test/prod

**Context**: SPEC-107's core goal is TRUE PARITY - same process manager, same code path, same behavior.

**Tasks**:
- [ ] Test service startup in dev environment
- [ ] Test service startup in test environment
- [ ] Test service startup in prod environment
- [ ] Verify health endpoints work in all environments
- [ ] Verify metrics endpoints work in all environments
- [ ] Compare behavior across environments
- [ ] Document any differences found
- [ ] Fix any parity issues

**Test Cases**:
- [ ] Service starts with same command in all envs
- [ ] Health check `/health` responds in all envs
- [ ] Metrics `/metrics` responds in all envs
- [ ] API endpoints work identically
- [ ] Worker count matches environment (1 for dev/test, 4+ for prod)
- [ ] Reload works in dev, disabled in test/prod

**Acceptance Criteria**:
- ✅ Same startup command works in all environments
- ✅ Health endpoints respond identically
- ✅ Metrics endpoints respond identically
- ✅ API behavior is identical across environments
- ✅ Only differences are worker count and reload (as specified)
- ✅ No "works on my machine" issues

**Reference**: SPEC-107 Section 5 (Acceptance)""",
        "tags": ["spec-107", "testing", "runtime-parity", "validation", "dev", "test", "prod"],
    },
    {
        "subject": "SPEC-107: Update Makefile for runtime selection (RUNTIME={docker|colima|apple})",
        "description": """**Goal**: Provide single Makefile switch to choose runtime

**Context**: SPEC-107 requires "One Makefile switch to choose runtime: `RUNTIME={docker|colima|apple}`"

**Tasks**:
- [ ] Create/update root `Makefile`
- [ ] Add `RUNTIME` variable with default
- [ ] Add targets for dev/test/prod
- [ ] Support Docker, Colima, and Apple Container CLI
- [ ] Ensure gunicorn is used regardless of runtime
- [ ] Test all runtime combinations

**Example**:
```makefile
RUNTIME ?= docker

dev:
	@if [ "$(RUNTIME)" = "docker" ]; then \
		docker compose -f docker-compose.dev.yml up; \
	elif [ "$(RUNTIME)" = "colima" ]; then \
		./scripts/nv-colima-start.sh; \
	else \
		./scripts/nv-apple-start.sh; \
	fi
```

**Acceptance Criteria**:
- ✅ Makefile supports `RUNTIME={docker|colima|apple}`
- ✅ `make dev`, `make test`, `make prod` work with all runtimes
- ✅ Runtime selection works correctly
- ✅ All services start with gunicorn
- ✅ Documentation updated

**Reference**: SPEC-107 Section 5 (Acceptance), `specs/107-unified-runtime-parity/Makefile`""",
        "tags": ["spec-107", "makefile", "runtime-selection", "automation"],
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


def create_story(importer, story_data, developer_f_id, project_id, status_id):
    """Create a user story in Taiga."""
    story_url = f"{importer.base_url}/userstories"
    headers = importer._get_headers()

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "assigned_to": developer_f_id,
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
    print("🚀 Creating Taiga stories for SPEC-107: Unified Runtime Parity & Deployment Standard")
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

    # Get Developer F user ID
    developer_f_id = get_user_id(importer, DEVELOPER_F_USERNAME)
    if not developer_f_id:
        print(f"⚠️  Developer F ({DEVELOPER_F_USERNAME}) not found, will use admin")
        # Get admin user ID as fallback
        import requests

        headers = importer._get_headers()
        me_url = f"{importer.base_url}/users/me"
        response = requests.get(me_url, headers=headers)
        if response.status_code == 200:
            developer_f_id = response.json().get("id")
            print(f"   Using admin user ID: {developer_f_id}")
        else:
            print("❌ Could not get user ID")
            sys.exit(1)
    else:
        print(f"✅ Found Developer F: {developer_f_id}")

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
        story = create_story(importer, story_data, developer_f_id, project_id, status_id)
        if story:
            created_stories.append(story)

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Created {len(created_stories)}/{len(STORIES)} stories for SPEC-107")

    if created_stories:
        print("\n📋 Created Stories:")
        for story in created_stories:
            story_ref = story.get("ref", "?")
            story_subject = story.get("subject", "")
            print(f"   - US#{story_ref}: {story_subject}")

    print("\n🎯 Next Steps:")
    print("   1. Update SPEC-107 README.md to reference these stories")
    print("   2. Assign stories to Developer F (if not already assigned)")
    print("   3. Begin implementation work")


if __name__ == "__main__":
    main()
