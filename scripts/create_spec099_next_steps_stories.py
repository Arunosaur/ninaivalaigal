#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create Taiga stories for SPEC-099 next steps"""

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


def get_available_ref(importer, start_ref=640):
    """Find next available story ref."""
    for ref in range(start_ref, start_ref + 50):
        try:
            story = importer.get_user_story(PROJECT_SLUG, ref)
            if not story:
                return ref
        except:
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
    """Create Taiga stories for SPEC-099 next steps"""
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
    new_id = get_status_id(importer._auth_token, project_id, "New")

    # Find next available refs
    next_ref = 647  # Start after US#646

    # Story 1: Performance Validation
    story1_ref = next_ref
    next_ref += 1

    story1_data = {
        "subject": "SPEC-099: Complete Performance Validation & Benchmarking",
        "description": """**SPEC-099 Next Step: Performance Validation**

**Related to:** US#646 (SPEC-099: Rust + Go Migration Strategy)
**Priority:** High
**Status:** Ready

---

## Objective

Complete comprehensive performance validation to validate ROI claims made in SPEC-099. Tools are ready, but comprehensive benchmarks have not been run.

---

## Current Status

✅ **Load Testing Tools:** Complete (Go load tester operational)
✅ **Benchmark Suite:** Ready
⏳ **Comprehensive Benchmarks:** Not run
⏳ **ROI Validation:** Not quantified

---

## Required Work

### 1. Run Comprehensive Benchmarks
- Execute Python vs Rust comparison tests
- Measure actual latency improvements
- Measure actual throughput improvements
- Collect resource usage metrics (CPU, memory)

### 2. Validate ROI Claims
- **GraphOps:** Target 50-90% latency reduction (250ms → 25ms)
- **Memory Service:** Target 83% latency reduction (180ms → 30ms)
- **Throughput:** Validate 6-10x improvement claims
- **Infrastructure Cost:** Measure actual cost savings (target 30-60%)

### 3. Generate Performance Report
- Create comparison report (Python vs Rust)
- Document actual vs projected improvements
- Provide recommendations based on results

---

## Reference Documentation

- `docs/DEVELOPER_A_RETEST_RESULTS.md` - Initial POC results (exceeded targets)
- `specs/099-rust-migration-strategy/README.md` - ROI matrix and targets
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Gap analysis
- `go-services/load-tester/` - Load testing tools

---

## Acceptance Criteria

- [ ] Comprehensive benchmarks executed
- [ ] Python vs Rust comparison data collected
- [ ] ROI claims validated or adjusted based on results
- [ ] Performance report generated
- [ ] Cost analysis completed (if possible)

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md` (Section 3.2, Phase 4)""",
        "project": project_id,
        "tags": ["spec-099", "performance", "benchmark", "roi-validation", "next-step"],
    }

    # Story 2: Graph/AI Service Completion
    story2_ref = next_ref
    next_ref += 1

    story2_data = {
        "subject": "SPEC-099: Complete Graph/AI Service (50% → 100%)",
        "description": """**SPEC-099 Next Step: Graph/AI Service Completion**

**Related to:** US#646 (SPEC-099: Rust + Go Migration Strategy)
**Priority:** High
**Status:** Ready

---

## Objective

Complete the Graph/AI Service implementation. Currently 50% complete with Apache AGE integration working, but AI layer is pending.

---

## Current Status

✅ **Apache AGE Integration:** Complete and working
✅ **Graph Traversal:** Operational
❌ **AI Inference Layer:** Not started
❌ **Full Service Extraction:** Not complete

---

## Required Work

### 1. AI Inference Layer
- Extract AI intelligence components from Python Graph Service
- Implement Rust-native AI inference layer
- Integrate with existing Apache AGE queries
- Maintain compatibility with existing intelligence features

### 2. Service Extraction
- Complete extraction from Python Graph Service
- Ensure all graph intelligence features are preserved
- Maintain API compatibility
- Update routing and service discovery

### 3. Integration Testing
- Test AI layer integration
- Validate feature parity with Python version
- Performance benchmarking
- Error handling and edge cases

---

## Reference Documentation

- `specs/099-rust-migration-strategy/README.md` - Migration strategy (Phase 2B)
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Current status (50% complete)
- `rust-services/graphops/` - Reference implementation (GraphOps Rust service)

---

## Acceptance Criteria

- [ ] AI inference layer implemented in Rust
- [ ] Service fully extracted from Python
- [ ] Feature parity with Python Graph Service verified
- [ ] Performance improvements validated
- [ ] Integration tests passing

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md` (Section 3.2, Phase 2B)""",
        "project": project_id,
        "tags": ["spec-099", "graph-ai-service", "rust", "ai-inference", "next-step"],
    }

    # Story 3: Production Hardening
    story3_ref = next_ref
    next_ref += 1

    story3_data = {
        "subject": "SPEC-099: Production Hardening (Schema Drift & Contract Testing)",
        "description": """**SPEC-099 Next Step: Production Hardening**

**Related to:** US#646 (SPEC-099: Rust + Go Migration Strategy)
**Priority:** Medium
**Status:** Ready

---

## Objective

Implement production hardening measures to prevent schema drift, enable contract testing, and ensure long-term maintainability of the Rust/Go migration.

---

## Current Status

❌ **Schema Drift Prevention:** Not implemented
❌ **Contract Testing:** Not implemented
⏳ **Unified Build Templates:** Partial (Dockerfiles exist but not standardized)
❌ **Developer Training:** Not established

---

## Required Work

### 1. Schema Drift Prevention
- Implement automated contract diff check in CI
- Centralize OpenAPI/Pydantic models in `shared/contracts/`
- Fail build on schema mismatch
- Weekly schema review process

### 2. Contract Testing
- Set up Pact or similar contract testing framework
- Create contract test suite
- Integrate into CI/CD pipeline
- Document contract testing guidelines

### 3. Unified Build Templates
- Standardize Dockerfile patterns
- Create shared build configurations
- Document build patterns in developer guide
- Ensure consistent health endpoint structure

### 4. Developer Training
- Create Rust training materials
- Establish knowledge transfer plan
- Allocate training budget if needed
- Document Rust development guidelines

---

## Reference Documentation

- `specs/099-rust-migration-strategy/README.md` - Risk mitigation (Section 6)
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Production hardening gaps
- `specs/100-api-container-modularization/` - Related contract work

---

## Acceptance Criteria

- [ ] Automated schema drift detection in CI
- [ ] Contract testing framework implemented
- [ ] Unified build templates documented
- [ ] Developer training plan created
- [ ] Weekly schema review process established

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md` (Section 3.2, Phase 5)""",
        "project": project_id,
        "tags": ["spec-099", "production-hardening", "schema-drift", "contract-testing", "next-step"],
    }

    # Story 4: Cost Savings Quantification
    story4_ref = next_ref

    story4_data = {
        "subject": "SPEC-099: Quantify Infrastructure Cost Savings",
        "description": """**SPEC-099 Next Step: Cost Savings Quantification**

**Related to:** US#646 (SPEC-099: Rust + Go Migration Strategy)
**Priority:** Medium
**Status:** Ready

---

## Objective

Quantify actual infrastructure cost savings from the Rust/Go migration to validate ROI projections.

---

## Current Status

✅ **Performance Improvements:** Validated (100-250x latency, 10-47x throughput)
❌ **Cost Savings:** Not quantified
❌ **ROI Calculation:** Not completed

---

## Required Work

### 1. Infrastructure Cost Analysis
- Compare Python vs Rust service resource usage
- Measure actual CPU, memory, and network usage
- Calculate cost per request/service
- Project scaling cost implications

### 2. Cost Savings Calculation
- Validate 30-60% infrastructure cost reduction claim
- Calculate payback period (<12 months target)
- Model scaling scenarios
- Generate ROI spreadsheet

### 3. Finance Team Review
- Present cost analysis to finance team
- Review ROI calculation
- Get approval for cost projections
- Document cost savings methodology

---

## Reference Documentation

- `specs/099-rust-migration-strategy/README.md` - ROI matrix and cost targets
- `docs/DEVELOPER_A_RETEST_RESULTS.md` - Performance validation
- `docs/SPEC_099_100_GAP_ANALYSIS.md` - Gap analysis

---

## Acceptance Criteria

- [ ] Infrastructure cost comparison completed
- [ ] Cost savings quantified (target 30-60%)
- [ ] Payback period calculated (<12 months)
- [ ] Finance team review completed
- [ ] ROI report generated

---

**For detailed requirements, see:** `docs/spec-analysis/SPEC_099_COMPREHENSIVE_ANALYSIS.md` (Section 7.2)""",
        "project": project_id,
        "tags": ["spec-099", "cost-analysis", "roi", "infrastructure", "next-step"],
    }

    stories = [
        (story1_ref, story1_data, ready_id, "Performance Validation"),
        (story2_ref, story2_data, ready_id, "Graph/AI Service Completion"),
        (story3_ref, story3_data, ready_id, "Production Hardening"),
        (story4_ref, story4_data, ready_id, "Cost Savings Quantification"),
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

    # Update US#646 to reference these stories
    print(f"\n📝 Updating US#646 to reference new stories...")
    story_646 = importer.get_user_story(PROJECT_SLUG, 646)
    if story_646:
        current_desc = story_646.get("description", "")
        new_section = f"""

---

## 📋 Next Steps (Related Stories)

The following stories track SPEC-099 implementation progress:

- **US#{story1_ref}:** Complete Performance Validation & Benchmarking
- **US#{story2_ref}:** Complete Graph/AI Service (50% → 100%)
- **US#{story3_ref}:** Production Hardening (Schema Drift & Contract Testing)
- **US#{story4_ref}:** Quantify Infrastructure Cost Savings

See individual stories for detailed requirements and acceptance criteria.
"""

        if "## 📋 Next Steps (Related Stories)" not in current_desc:
            new_desc = current_desc + new_section
            updated = importer.update_user_story(story_646["id"], story_646["version"], {"description": new_desc})
            if updated:
                print(f"✅ Updated US#646 with next steps references")
            else:
                print(f"⚠️  Failed to update US#646")

    # Save created stories
    if created_stories:
        output_file = "docs/spec-analysis/SPEC_099_NEXT_STEPS_STORIES.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(
                [{"ref": ref, "id": s.get("id"), "subject": s.get("subject")} for ref, s in created_stories],
                f,
                indent=2,
            )
        print(f"\n💾 Created stories details saved to: {output_file}")

    print(f"\n✅ Summary: Created {len(created_stories)} stories for SPEC-099 next steps")


if __name__ == "__main__":
    main()
