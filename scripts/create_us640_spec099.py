#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create Taiga story US#640 for SPEC-099: Rust + Go Migration Strategy"""

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
    print(f"❌ Status '{status_name}' not found.")
    return -1


def main():
    """Create US#640 story for SPEC-099"""
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
    story_ref = 640
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

    # Read comprehensive description from analysis document
    analysis_path = "docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md"
    description_section = """**SPEC-099: Rust + Go Migration Strategy**

**Status:** 🔄 **IN PROGRESS** (Implementation: ~75% complete)
**Phase:** Phase 3
**Completion:** Major services deployed and operational

---

## ✅ Current Status

SPEC-099 has **SUBSTANTIAL IMPLEMENTATION** (~75% complete). Major Rust and Go services are deployed and operational, with performance validation exceeding original ROI targets.

---

## ✅ What Exists (COMPLETE - 75%)

### 1. Rust Services ✅

#### GraphOps Service (100% Complete)
- ✅ gRPC service (port 13398, tonic-based)
- ✅ Apache AGE Cypher query parsing
- ✅ Graph traversal engine
- ✅ Vector similarity operations
- ✅ Prometheus metrics and health endpoints
- ✅ OpenTelemetry instrumentation
- ✅ **Performance:** 100-250x latency improvement (EXCEEDED targets)
- ✅ **Throughput:** 10-47x improvement (EXCEEDED targets)
- ✅ **Success Rate:** 99.96-100% under load

#### Memory Service (90% Complete)
- ✅ REST API (Axum framework, port 13393)
- ✅ Memory CRUD operations
- ✅ PostgreSQL + pgvector integration
- ✅ Redis caching (1-hour TTL)
- ✅ OpenTelemetry instrumentation
- ✅ **Performance:** Sub-ms latency, 25.4k RPS, 100% success rate

**Remaining:**
- ⏳ Fix PgBouncer prepared statement issue (Task #85)
- ⏳ Complete Redis Streams integration

### 2. Go Infrastructure Services ✅

#### gRPC Gateway (100% Complete)
- ✅ REST ↔ gRPC translation (port 13395)
- ✅ Health check endpoints
- ✅ CORS and logging middleware
- ✅ OpenTelemetry instrumentation
- ✅ Memory service routing
- ✅ GraphOps service routing
- ✅ Core API proxy routes

#### Load Testing Tools (100% Complete)
- ✅ Concurrent benchmarking (goroutines)
- ✅ HTTP and gRPC load testing
- ✅ Metrics reporting and analysis
- ✅ Scenario-based testing

#### CLI Tools (100% Complete)
- ✅ Unified `nina` CLI
- ✅ Health, memory, graph, config commands
- ✅ Multi-platform support (Linux, macOS, Windows)
- ✅ Distribution ready (Task #77)

### 3. Infrastructure & Observability (95% Complete)

- ✅ Apple Container CLI integration (native ARM64, 3-5x faster)
- ✅ OpenTelemetry end-to-end (Python, Rust, Go)
- ✅ Jaeger v1.51 operational (port 16686)
- ✅ W3C Trace Context propagation
- ✅ Port allocation standardized (133XX series)
- ✅ Health monitoring (all services)

**Remaining:**
- ⏳ Fix PgBouncer session mode (Task #85)
- ⏳ Add persistent storage for Jaeger

---

## ⏳ What's Missing (25% Remaining)

### Phase 2B: Graph/AI Service (50% In Progress)
- ✅ Apache AGE integration working
- ❌ AI inference layer integration
- ❌ Full service extraction from Python

### Phase 3: Real-Time Services (Not Started)
- ❌ Real-time telemetry daemon
- ❌ Token + Security middleware
- ❌ Background workers/Cron tasks

### Phase 4: Performance Validation (Partial)
- ✅ Load testing tools ready
- ❌ Comprehensive benchmarks (Python vs Rust comparison)
- ❌ ROI cost analysis (infrastructure cost savings)

### Phase 5: Production Hardening (Minimal)
- ❌ Schema drift prevention (CI contract diff check)
- ❌ Contract testing (Pact integration)
- ❌ Developer training program

---

## 📊 Performance Validation

### Load Test POC Results (Oct 20, 2025)

**GraphOps Service:**
- **Latency:** 100-250x improvement (target was 50-90%) - **EXCEEDED**
- **Throughput:** 10-47x improvement (target was 6-10x) - **EXCEEDED**
- **P95 Latency:** 0.27ms (target <50ms) - **185x better**
- **Success Rate:** 99.96% under load

**Memory Service:**
- **P95 Latency:** 0.97ms (sub-ms restored)
- **Throughput:** 25.4k RPS (5x improvement)
- **Success Rate:** 100%

**Reference:** `docs/DEVELOPER_A_RETEST_RESULTS.md`

---

## 🚨 Critical Issues Fixed

### ✅ Issue 1: SPEC_INDEX.md Corrected
- **Fixed:** SPEC-099 entry now correctly shows "Rust + Go Migration Strategy" (was incorrectly "Approval Chain Processing")
- **Status:** Updated from "Proposed" to "In Progress"

### ⚠️ Issue 2: Performance Validation Incomplete
- **Status:** Tools ready, comprehensive benchmarks pending
- **Action Required:** Run comprehensive performance validation suite

---

## 📋 Implementation Evidence

**Rust Services:**
- `rust-services/graphops/` - ✅ Complete (1,000+ lines)
- `rust-services/memory-service/` - ✅ Complete (800+ lines)

**Go Services:**
- `go-services/grpc-gateway/` - ✅ Complete (3,000+ lines)
- `go-services/load-tester/` - ✅ Complete (1,500+ lines)
- `go-services/cli-tools/` - ✅ Complete (2,000+ lines)

**Documentation:**
- `docs/SPEC_099_100_GAP_ANALYSIS.md`
- `docs/SPEC_099_100_GAP_ANALYSIS_OCT20.md`
- `docs/DEVELOPER_A_RETEST_RESULTS.md`
- `specs/099-rust-migration-strategy/README.md` (685 lines)

**Total:** ~8,300+ lines of code, comprehensive documentation

---

## 🔗 Related SPECs

- **SPEC-062** (GraphOps Stack Deployment) - ✅ Foundational, GraphOps Rust service
- **SPEC-100** (API Container Modularization) - ✅ Complementary, services ready for modularization
- **SPEC-072** (Apple Container CLI) - ✅ Infrastructure, deployment mechanism
- **SPEC-101** (Unified Observability) - ✅ Observability integration
- **SPEC-131** (Memory Router Rationalization) - ✅ Memory Service supports SPEC-131

---

## 📝 Next Steps

### High Priority
1. ✅ Fix SPEC_INDEX.md (completed)
2. ✅ Create Taiga story (this story)
3. **Run Performance Validation** - Complete comprehensive benchmarks
4. **Fix PgBouncer Issue** - Resolve Task #85

### Medium Priority
5. Complete Graph/AI Service (finish remaining 50%)
6. Implement Contracts Layer (SPEC-100 Phase 0)
7. Production Hardening (schema drift prevention, contract testing)

### Low Priority
8. Real-Time Telemetry Daemon
9. Token + Security Middleware
10. Cost Analysis (quantify infrastructure savings)

---

**Status:** 🔄 IN PROGRESS - 75% complete, major services deployed
**Completion:** ~75% (Rust/Go services complete, integration and validation pending)
**Next Steps:** Complete performance validation, fix PgBouncer, finish Graph/AI Service

---

**For detailed analysis, see:** `docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md`"""

    # Create user story payload
    story_data = {
        "subject": "SPEC-099: Rust + Go Migration Strategy",
        "description": description_section,
        "status": status_id,
        "tags": ["spec-099", "rust", "go", "performance", "migration"],
        "project": project_id,
    }

    print(f"📝 Creating US#{story_ref}: SPEC-099: Rust + Go Migration Strategy")
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
        output_file = "docs/spec-analysis/US640_STORY_DETAILS.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(story, f, indent=2, default=str)
        print(f"💾 Story details saved to: {output_file}")
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(f"   Response: {response.text}")


if __name__ == "__main__":
    main()
