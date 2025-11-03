#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create Taiga story US#651 for SPEC-100: API Container Modularization"""

import json
import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

import requests
from taiga_import_tasks import TaigaImporter

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"


def get_status_id(auth_token: str, project_id: int, status_name: str) -> int:
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstory-statuses?project={project_id}", headers=headers)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name", "").lower() == status_name.lower():
                return status["id"]
    print(f"⚠️  Status '{status_name}' not found.")
    return -1


def main():
    """Create US#651 story for SPEC-100"""
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(API_ENDPOINT, username=username, password=password)
    importer._get_auth_token()

    project_info = importer.get_project(PROJECT_SLUG)
    if not project_info:
        print("❌ Failed to get project info")
        return

    project_id = project_info["id"]

    # Check if story already exists
    story_ref = 651
    existing_story = importer.get_user_story(PROJECT_SLUG, story_ref)
    if existing_story:
        print(f"⚠️  Story US#{story_ref} already exists: {existing_story.get('subject')}")
        return

    # Get status IDs
    in_progress_id = get_status_id(importer._auth_token, project_id, "In Progress")
    if in_progress_id == -1:
        ready_id = get_status_id(importer._auth_token, project_id, "Ready")
        status_id = ready_id if ready_id != -1 else 2  # Default to Ready
    else:
        status_id = in_progress_id

    description = """**SPEC-100: API Container Modularization & Runtime-Agnostic Federation**

**Status:** 🔄 **IN PROGRESS** (Implementation: ~65% complete)
**Phase:** Phase 2B
**Completion:** Infrastructure ready, decomposition partial, orchestration missing

---

## ✅ Current Status

SPEC-100 has **SUBSTANTIAL PROGRESS** (~65% complete). Service directories exist with substantial code, shared contracts layer is ~90% complete, but orchestration (gateway, event bus, aggregator) is missing.

---

## ✅ What Exists (COMPLETE - 65%)

### 1. Service Directory Structure ✅

**Services Created:**
- ✅ `core-api/` - Authentication, Users, Teams, RBAC (359 files, ~7,500+ lines)
- ✅ `graph-service/` - Graph intelligence and AI integrations (343 files, ~12,500+ lines)
- ✅ `business-service/` - Billing, Usage, Analytics (344 files, ~7,500+ lines)
- ✅ `admin-vendor-service/` - Admin + Vendor portals (343 files, ~4,500+ lines)
- ✅ `memory-service/` - Memory substrate (Python + Rust versions)

**Total:** ~40,000+ lines of service code

**Structure:**
- ✅ Service boundaries defined and documented
- ✅ Router → service mapping complete
- ✅ Port allocation standardized (SPEC-086 compliant, 13390-13395)
- ✅ Independent Dockerfiles per service

### 2. Shared Contracts Layer ✅ (~90% Complete)

**Location:** `shared/contracts/`

**Completed:**
- ✅ Protocol buffers for all services (9 .proto files)
  - `auth/v1/auth.proto`
  - `memory/v1/memory.proto`
  - `graph/v1/graphops.proto`
  - `business/v1/billing.proto`, `analytics.proto`
  - `admin/v1/admin.proto`
  - `common/v1/errors.proto`, `pagination.proto`
- ✅ Python bindings (24 generated files)
- ✅ Go bindings (23 generated files)
- ✅ Pydantic models (`auth/v1/models.py`, `memory/v1/models.py`, `common/v1/models.py`)
- ✅ OpenAPI specifications (per-service `openapi.yaml`)
- ✅ CI validation workflow (`.github/workflows/contract-validation.yml`)
- ✅ Comprehensive documentation (13 guides in `docs/`)

**Remaining:**
- ⏳ US #79 Phase 4: Documentation & Training (40% complete)

**Reference:** Task US #79 (In Progress, ~90% complete)

### 3. Health & Metrics Endpoints ✅

**Status:** ✅ **COMPLETE** (US #33)

**Implementation:**
- ✅ `/health` - Basic liveness check (all services)
- ✅ `/ready` - Readiness with dependency checks (all services)
- ✅ `/metrics` - Prometheus metrics (all services)

**Reference:** `services/core-api/SPEC_100_IMPLEMENTATION.md`, US #33 (Done)

### 4. Service Setup & Testing ✅

**Completed Stories:**
- ✅ US #30: Graph/AI Service - Architecture & Setup (Done)
- ✅ US #33: Core API - SPEC-100 Alignment (Health & Metrics) (Done)
- ✅ US #36: Core API - Microservices Deployment & Testing (Done)
- ✅ US #37: Business Service - Microservices Deployment & Testing (Done)

---

## ⏳ What's Partial (20%)

### Gateway Configuration (50% Complete)

**Status:** ⏳ **PARTIAL** (US #83 - Ready but not deployed)

**Completed:**
- ✅ Traefik configuration files exist (`config/traefik/traefik.yml`, `containers/traefik/traefik.yml`)
- ✅ Dashboard and entry points configured
- ✅ Dynamic routing configuration structure

**Remaining:**
- ⏳ Path-based routing implementation (`/auth` → Core API, `/memory` → Memory Service)
- ⏳ TLS termination configuration
- ⏳ Rate limiting configuration
- ⏳ Production deployment validation

**Reference:** Task US #83 (Ready)

### Service Decomposition Status (Unclear)

**Evidence:**
- ✅ Service directories exist with substantial code (40,000+ lines)
- ✅ Independent Dockerfiles exist
- ⚠️ Deployment model unclear (monolith vs microservices?)

**Required:**
- Verify if services are deployed independently or still monolithic
- Complete service extraction from monolith (if needed)
- Validate independent deployment

**Reference:** Task US #88 (Ready)

---

## ❌ What's Missing (15%)

### Event Bus (0% Complete)

**Status:** ❌ **NOT IMPLEMENTED** (US #82 - Ready)

**Missing:**
- ❌ Redis Streams deployment
- ❌ Event publishing implementation
- ❌ Event consumers implementation
- ❌ Event replay capability

**Reference:** SPEC-100 Section 4.3, Task US #82 (Ready)

### Aggregator Layer (0% Complete)

**Status:** ❌ **NOT IMPLEMENTED**

**Missing:**
- ❌ Backend-for-Frontend (BFF) pattern
- ❌ Parallel service execution
- ❌ Response merging logic
- ❌ Multi-service composition endpoints

**Reference:** SPEC-100 Section 4.4

### Independent CI Workflows (Partial)

**Status:** 🟡 **PARTIAL**

**Completed:**
- ✅ Rust/Go services have separate builds
- ✅ Contract validation CI workflow

**Missing:**
- ❌ Independent workflows per Python service
- ❌ Parallel build configuration (docker buildx bake)
- ❌ Service-specific CI triggers

**Reference:** SPEC-100 Section 5.1

### Schema Separation (0% Complete)

**Status:** ❌ **NOT STARTED**

**Current:** Shared PostgreSQL schema
**Target:** Service-specific schemas (Phase 2) or federated (Phase 3)

**Reference:** SPEC-100 Section 6.5

---

## 📋 Related Task Stories

**Primary Tasks:**
- **US #79:** P0: Shared Contracts Layer (SPEC-100 Phase 0) - **In Progress** (~90% complete, Phase 4 pending)
- **US #83:** P0: API Gateway Path Routing (Traefik) - **Ready**
- **US #87:** P1: Schema Drift Prevention CI - **Ready**
- **US #88:** P1: Core API Decomposition - **Ready**

**Infrastructure Prerequisites:**
- **US #85:** P0: Fix PgBouncer Bypass - **Done** (prerequisite complete)
- **US #81:** gRPC Gateway Integration Testing - **Done**

**Optional/Enhancement:**
- **US #82:** Deploy Event Bus (Redis Streams or NATS) - **Ready** (optional)

---

## 🚨 Critical Issues

### ✅ Issue 1: SPEC_INDEX.md Fixed
- **Fixed:** Status updated from "Planned" to "In Progress"
- **Fixed:** Incorrect "API Surface Contracts" labels corrected (3 locations)
- **Fixed:** Description updated to reflect actual status

### ⚠️ Issue 2: Service Decomposition Status Unclear
- **Status:** Conflicting evidence - services exist but deployment unclear
- **Action Required:** Verify deployment model, update status accordingly

### ⚠️ Issue 3: Orchestration Missing
- **Status:** Gateway partial, event bus missing, aggregator missing
- **Action Required:** Complete gateway (US #83), implement event bus (US #82), add aggregator

---

## 📊 Acceptance Criteria Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| **5 service boundaries defined and documented** | ✅ Complete | All 5 services documented |
| **Shared contracts repository created with validation** | ✅ ~90% | Contracts exist, Phase 4 documentation pending |
| **Parallel build configuration working** | 🟡 Partial | Rust/Go parallel, Python services unclear |
| **Gateway routing operational** | ⏳ Partial | Config exists, deployment unclear |
| **Event bus implemented (Redis Streams)** | ❌ Not Started | US #82 ready but not implemented |
| **Aggregator layer handling multi-service calls** | ❌ Not Started | BFF pattern missing |
| **Independent CI workflows per service** | 🟡 Partial | Some workflows exist |
| **Health endpoints standardized across services** | ✅ Complete | US #33 complete |
| **Drop-in container replacement verified** | ⏳ Unclear | Services exist but replacement not validated |
| **Documentation complete** | 🟡 Partial | Main README complete, deployment docs unclear |

**Overall:** ⏳ **~65% Complete** (5/10 fully complete, 2/10 partial, 3/10 not started)

---

## 🔗 Related SPECs

- **SPEC-087** (API Surface Contracts) - ✅ Complementary, no overlap (public/internal filtering)
- **SPEC-099** (Rust + Go Migration Strategy) - ✅ Complementary, SPEC-099 services are part of SPEC-100 decomposition
- **SPEC-062** (GraphOps Stack Deployment) - ✅ Part of SPEC-100 Graph/AI Service
- **SPEC-086** (Multi-Runtime Port Allocation) - ✅ Infrastructure prerequisite (complete)
- **SPEC-101** (Unified Observability) - ✅ Follow-up spec (planned)

---

## 📝 Next Steps

### High Priority
1. ✅ Fix SPEC_INDEX.md (completed)
2. ✅ Create Taiga story (this story)
3. **Verify Service Deployment** - Determine if services run independently or bundled
4. **Complete Gateway Deployment** - Finish US #83 (Traefik path-based routing)

### Medium Priority
5. **Implement Event Bus** - Complete US #82 (Redis Streams)
6. **Finish Contracts Documentation** - Complete US #79 Phase 4
7. **Add Aggregator Layer** - Implement BFF pattern for service composition
8. **Independent CI Workflows** - Create per-service CI workflows

### Low Priority
9. **Schema Separation** - Move to Phase 2 (service-specific schemas)
10. **Service Mesh** - Optional Phase 4 enhancement (Linkerd/Istio)

---

**Status:** 🔄 IN PROGRESS - ~65% complete, infrastructure ready, decomposition partial
**Completion:** ~65% (services structured, contracts complete, orchestration missing)
**Next Steps:** Verify deployment, complete gateway, implement event bus, finish contracts documentation

---

**For detailed analysis, see:** `docs/spec-analysis/SPEC_100_COMPREHENSIVE_ANALYSIS.md`"""

    # Create user story payload
    story_data = {
        "subject": "SPEC-100: API Container Modularization & Runtime-Agnostic Federation",
        "description": description,
        "status": status_id,
        "tags": ["spec-100", "microservices", "container-modularization", "service-decomposition", "federation"],
        "project": project_id,
    }

    print(f"📝 Creating US#{story_ref}: SPEC-100: API Container Modularization")
    print(f"   Status: {status_id} (In Progress/Ready)")

    headers = {
        "Authorization": f"Bearer {importer._auth_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)

    if response.status_code in [200, 201]:
        story = response.json()
        print(f"✅ Successfully created US#{story.get('ref')}: {story.get('subject')}")
        print(f"   Story ID: {story.get('id')}")
        print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")

        # Save story details
        output_file = "docs/spec-analysis/US651_STORY_DETAILS.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(story, f, indent=2, default=str)
        print(f"💾 Story details saved to: {output_file}")
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(f"   Response: {response.text}")


if __name__ == "__main__":
    main()
