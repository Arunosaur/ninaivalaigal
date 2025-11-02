#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Create Taiga stories for SPEC-100 missing next steps"""

import json
import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

import requests  # noqa: E402
from taiga_import_tasks import TaigaImporter  # noqa: E402

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"


def get_status_id(auth_token: str, project_id: int, status_name: str) -> int:
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name", "").lower() == status_name.lower():
                return status["id"]
    print(f"⚠️  Status '{status_name}' not found.")
    return -1


def get_available_ref(importer, start_ref=652):
    """Find next available story ref."""
    for ref in range(start_ref, start_ref + 50):
        try:
            story = importer.get_user_story(PROJECT_SLUG, ref)
            if not story:
                return ref
        except Exception:
            return ref
    return None


def create_story(importer, project_id, story_data, status_id):
    """Create a user story in Taiga."""
    headers = {
        "Authorization": f"Bearer {importer._auth_token}",
        "Content-Type": "application/json",
    }

    if status_id:
        story_data["status"] = status_id

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def main():
    """Create Taiga stories for SPEC-100 missing next steps"""
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(API_ENDPOINT, username=username, password=password)
    importer._get_auth_token()

    project_info = importer.get_project(PROJECT_SLUG)
    if not project_info:
        print("❌ Failed to get project info")
        return

    project_id = project_info["id"]

    # Get status IDs
    ready_id = get_status_id(importer._auth_token, project_id, "Ready")
    status_id = ready_id if ready_id != -1 else 2  # Default to Ready

    # Find next available refs
    next_ref = 652  # Start after US#651

    # Story 1: Verify Service Deployment
    story1_ref = next_ref
    next_ref += 1

    story1_data = {
        "subject": ("SPEC-100: Verify Service Deployment Model (Independent vs Monolithic)"),
        "description": """**SPEC-100 Next Step: Service Deployment Verification**

**Related to:** US#651 (SPEC-100: API Container Modularization)
**Priority:** High
**Status:** Ready

---

## Objective

Verify and document the actual service deployment model. Determine if services are
deployed independently as microservices or still bundled as a monolithic container.

---

## Current Status

✅ **Service Directories:** Created with substantial code (40,000+ lines)
✅ **Dockerfiles:** Independent Dockerfiles exist per service
⚠️ **Deployment Model:** Unclear - conflicting evidence in documentation

---

## Required Work

### 1. Deployment Model Investigation
- Check actual running containers/services
- Verify if services run independently or bundled
- Document current deployment architecture
- Compare with SPEC-100 target architecture

### 2. Service Independence Validation
- Test if services can be deployed independently
- Verify service-to-service communication
- Check if services share resources or are isolated
- Validate port allocation (SPEC-086 compliance)

### 3. Documentation Update
- Document actual deployment model
- Update SPEC-100 status based on findings
- Create deployment architecture diagram
- Update gap analysis documents

---

## Reference Documentation

- `services/` - Service directories with code
- `docs/SPEC_099_100_GAP_ANALYSIS_OCT20.md` - Claims "monolithic container"
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Claims "services deployed"
- `specs/100-api-container-modularization/README.md` - Target architecture

---

## Acceptance Criteria

- [ ] Deployment model verified (independent vs monolithic)
- [ ] Findings documented
- [ ] SPEC-100 status updated based on findings
- [ ] Gap analysis documents reconciled
- [ ] Deployment architecture diagram created

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_100_COMPREHENSIVE_ANALYSIS.md`
(Section 3.2, Service Decomposition)""",
        "project": project_id,
        "tags": ["spec-100", "deployment-verification", "service-decomposition", "next-step"],
    }

    # Story 2: Aggregator Layer
    story2_ref = next_ref
    next_ref += 1

    story2_data = {
        "subject": "SPEC-100: Implement Aggregator Layer (BFF Pattern)",
        "description": """**SPEC-100 Next Step: Aggregator Layer Implementation**

**Related to:** US#651 (SPEC-100: API Container Modularization)
**Priority:** Medium
**Status:** Ready

---

## Objective

Implement Backend-for-Frontend (BFF) pattern for service composition. Enable parallel
service execution and response merging for multi-service API calls.

---

## Current Status

❌ **Aggregator Layer:** Not implemented
❌ **BFF Pattern:** Missing
❌ **Parallel Execution:** Not implemented
❌ **Response Merging:** Not implemented

---

## Required Work

### 1. BFF Pattern Implementation
- Implement Backend-for-Frontend aggregator service
- Create composition endpoints that call multiple services
- Implement parallel service execution (asyncio.gather)
- Add response merging logic

### 2. Service Composition Endpoints
- Create endpoints that aggregate data from multiple services
- Example: `/context/{id}/analyze` → Memory + Graph/AI services
- Handle partial failures gracefully
- Implement timeout and fallback logic

### 3. Performance Optimization
- Parallel execution for concurrent service calls
- Response caching where appropriate
- Error handling and degradation
- Load balancing considerations

---

## Reference Documentation

- `specs/100-api-container-modularization/README.md` - Section 4.4 (Aggregator Layer)
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Aggregator missing
- BFF Pattern: https://microservices.io/patterns/data/backend-for-frontend.html

---

## Acceptance Criteria

- [ ] BFF aggregator service implemented
- [ ] Multi-service composition endpoints created
- [ ] Parallel execution working
- [ ] Response merging logic complete
- [ ] Error handling and fallbacks implemented
- [ ] Performance validated

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_100_COMPREHENSIVE_ANALYSIS.md`
(Section 3.2, Aggregator Layer)""",
        "project": project_id,
        "tags": ["spec-100", "aggregator", "bff", "service-composition", "next-step"],
    }

    # Story 3: Independent CI Workflows
    story3_ref = next_ref
    next_ref += 1

    story3_data = {
        "subject": "SPEC-100: Independent CI Workflows Per Service",
        "description": """**SPEC-100 Next Step: Independent CI Workflows**

**Related to:** US#651 (SPEC-100: API Container Modularization)
**Priority:** Medium
**Status:** Ready

---

## Objective

Create independent CI/CD workflows for each Python service, enabling parallel builds and service-specific deployments.

---

## Current Status

✅ **Rust/Go Services:** Separate builds exist
✅ **Contract Validation:** CI workflow exists
🟡 **Python Services:** Partial (some workflows, not per-service)
❌ **Parallel Builds:** Docker buildx bake not configured
❌ **Service Triggers:** No service-specific file change triggers

---

## Required Work

### 1. Per-Service CI Workflows
- Create `.github/workflows/build-{service}.yml` for each service
  - `build-core-api.yml`
  - `build-graph-service.yml`
  - `build-business-service.yml`
  - `build-admin-vendor-service.yml`
- Configure service-specific triggers (file path filters)
- Independent build, test, and deploy steps

### 2. Parallel Build Configuration
- Configure `docker buildx bake` for parallel builds
- Create `docker-bake.hcl` with all service targets
- Optimize build time (<10 minutes aggregate target)
- Enable layer caching and optimization

### 3. Service-Specific Triggers
- Configure GitHub Actions path filters
- Trigger only on relevant file changes per service
- Avoid cross-service rebuild cascades
- Reduce CI time from 30+ min to <10 min aggregate

---

## Reference Documentation

- `specs/100-api-container-modularization/README.md` - Section 5.1 (Independent CI Pipelines)
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - CI workflows partial
- `.github/workflows/` - Existing workflows

---

## Acceptance Criteria

- [ ] Independent CI workflow per service
- [ ] Parallel build configuration (docker buildx bake)
- [ ] Service-specific file change triggers
- [ ] Build time <10 minutes aggregate
- [ ] Independent deployment per service

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_100_COMPREHENSIVE_ANALYSIS.md`
(Section 3.2, Independent CI Workflows)""",
        "project": project_id,
        "tags": ["spec-100", "ci-workflows", "docker-buildx", "parallel-builds", "next-step"],
    }

    # Story 4: Schema Separation
    story4_ref = next_ref

    story4_data = {
        "subject": "SPEC-100: Schema Separation (Phase 2)",
        "description": """**SPEC-100 Next Step: Schema Separation**

**Related to:** US#651 (SPEC-100: API Container Modularization)
**Priority:** Low
**Status:** Ready

---

## Objective

Migrate from shared PostgreSQL schema to service-specific schemas for better isolation and resilience.

---

## Current Status

❌ **Current:** Shared PostgreSQL schema (all services in `public` schema)
❌ **Target:** Service-specific schemas (Phase 2)
❌ **Migration:** Not started

---

## Required Work

### 1. Schema Design
- Design service-specific schemas
  - `core_api.users`, `core_api.teams`
  - `memory_service.memories`, `memory_service.contexts`
  - `graph_ai.nodes`, `graph_ai.edges`
  - `business.billing`, `business.analytics`
  - `admin_vendor.portals`
- Define cross-service query patterns
- Plan migration strategy

### 2. Migration Implementation
- Create Alembic migrations for schema separation
- Migrate existing data to service schemas
- Update service code to use new schemas
- Test cross-service queries (via API calls)

### 3. Validation
- Verify schema isolation
- Test service independence
- Validate API-based cross-service access
- Performance impact assessment

---

## Reference Documentation

- `specs/100-api-container-modularization/README.md` - Section 6.5 (Database Strategy, Phase 2)
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Schema separation not started
- `alembic/versions/` - Migration patterns

---

## Acceptance Criteria

- [ ] Service-specific schemas designed
- [ ] Alembic migrations created
- [ ] Data migrated to service schemas
- [ ] Services updated to use new schemas
- [ ] Cross-service queries validated (API-based)

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_100_COMPREHENSIVE_ANALYSIS.md`
(Section 3.2, Schema Separation)""",
        "project": project_id,
        "tags": ["spec-100", "schema-separation", "database", "phase-2", "next-step"],
    }

    stories = [
        (story1_ref, story1_data, status_id, "Service Deployment Verification"),
        (story2_ref, story2_data, status_id, "Aggregator Layer (BFF)"),
        (story3_ref, story3_data, status_id, "Independent CI Workflows"),
        (story4_ref, story4_data, status_id, "Schema Separation"),
    ]

    created_stories = []

    for ref, story_data, status_id, name in stories:
        # Check if story already exists
        existing = importer.get_user_story(PROJECT_SLUG, ref)
        if existing:
            print(f"⚠️  US#{ref} already exists: {existing.get('subject')}")
            continue

        print(f"📝 Creating US#{ref}: {name}...")
        story = create_story(importer, project_id, story_data, status_id)

        if story:
            created_stories.append((ref, story))
            print(f"✅ Created US#{story.get('ref')}: {story.get('subject')}")
        else:
            print(f"❌ Failed to create US#{ref}")

    # Update US#651 to reference these stories
    print("\n📝 Updating US#651 to reference new stories...")
    story_651 = importer.get_user_story(PROJECT_SLUG, 651)
    if story_651:
        current_desc = story_651.get("description", "")

        # Check if next steps section already exists
        if "## 📋 Next Steps (Related Stories)" not in current_desc:
            new_section = f"""

---

## 📋 Next Steps (Related Stories)

The following stories track SPEC-100 implementation progress:

**Existing Task Stories:**
- **US #79:** P0: Shared Contracts Layer (SPEC-100 Phase 0) - **In Progress** (~90% complete)
- **US #83:** P0: API Gateway Path Routing (Traefik) - **Ready**
- **US #82:** Deploy Event Bus (Redis Streams or NATS) - **Ready** (optional)
- **US #87:** P1: Schema Drift Prevention CI - **Ready**
- **US #88:** P1: Core API Decomposition - **Ready**

**New Next Steps Stories:**
- **US#{story1_ref}:** Verify Service Deployment Model (Independent vs Monolithic)
- **US#{story2_ref}:** Implement Aggregator Layer (BFF Pattern)
- **US#{story3_ref}:** Independent CI Workflows Per Service
- **US#{story4_ref}:** Schema Separation (Phase 2)

See individual stories for detailed requirements and acceptance criteria.
"""

            new_desc = current_desc + new_section
            updates = {"description": new_desc}
            updated = importer.update_user_story(story_651["id"], story_651["version"], updates)
            if updated:
                print("✅ Updated US#651 with next steps references")
            else:
                print("⚠️  Failed to update US#651")
        else:
            print("⚠️  US#651 already has next steps section")

    # Save created stories
    if created_stories:
        output_file = "docs/spec-analysis/SPEC_100_NEXT_STEPS_STORIES.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(
                [{"ref": ref, "id": s.get("id"), "subject": s.get("subject")} for ref, s in created_stories],
                f,
                indent=2,
            )
        print(f"\n💾 Created stories details saved to: {output_file}")

    print(f"\n✅ Summary: Created {len(created_stories)} stories for SPEC-100 missing next steps")


if __name__ == "__main__":
    main()
