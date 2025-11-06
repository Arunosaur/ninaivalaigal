#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Create Taiga stories for SPEC-139 remaining work"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    project = importer.get_project("ninaivalaigal")

    if not project:
        print("Project not found")
        return

    project_id = project["id"]

    # Stories to create based on SPEC-139 README
    stories = [
        {
            "subject": "SPEC-139: Rust Memory Service Runbook - Operational Playbook",
            "description": """# SPEC-139: Rust Memory Service Runbook

**SPEC**: SPEC-139 (Audit Reconciliation & Rust Integration Readiness)

## Objective
Create operational playbook covering deployment, validation, and rollback for the Rust memory provider.

## Requirements
- Deployment procedures for Rust memory provider
- Validation steps to verify Rust provider is working
- Rollback procedures if issues occur
- Monitoring and alerting setup
- Operational checklist

## Deliverable
- `RUST_MEMORY_RUNBOOK.md` - Operational playbook

## Acceptance Criteria
- [ ] Deployment procedures documented
- [ ] Validation steps documented
- [ ] Rollback procedures documented
- [ ] Monitoring setup documented
- [ ] Operational checklist approved by Platform/Rust/DevOps stakeholders

## Related
- SPEC-139: Audit Reconciliation & Rust Integration Readiness
- SPEC-131: Memory Router Rationalization
""",
            "priority": "Normal",
            "tags": ["spec-139", "rust", "runbook", "operational"],
        },
        {
            "subject": "SPEC-139: Rust Integration Gate Checklist - Decision Framework",
            "description": """# SPEC-139: Rust Integration Gate Checklist

**SPEC**: SPEC-139 (Audit Reconciliation & Rust Integration Readiness)

## Objective
Create decision framework and readiness checklist for flipping the default memory provider to Rust.

## Requirements
- Decision framework for enabling Rust memory provider
- Readiness checklist with all criteria
- Approval process documentation
- Risk assessment framework

## Deliverable
- `RUST_INTEGRATION_GATE.md` - Decision framework and readiness checklist

## Acceptance Criteria
- [ ] Decision framework documented
- [ ] Readiness checklist complete
- [ ] Approval process documented
- [ ] Risk assessment framework included
- [ ] Checklist approved by platform and Rust owners

## Related
- SPEC-139: Audit Reconciliation & Rust Integration Readiness
""",
            "priority": "Normal",
            "tags": ["spec-139", "rust", "integration", "gating"],
        },
        {
            "subject": "SPEC-139: Fix Python-Rust MemoryProvider Interface",
            "description": """# SPEC-139: Fix Python-Rust MemoryProvider Interface

**SPEC**: SPEC-139 (Audit Reconciliation & Rust Integration Readiness)

## Objective
Fix Python <-> Rust interface blockers (provider defaults, request signatures) for MemoryProvider factory.

## Requirements
- Fix MemoryProvider factory interface
- Ensure provider defaults work correctly
- Fix request signatures compatibility
- Add feature flag gating (USE_RUST_MEMORY)
- Test Python <-> Rust integration

## Files to Modify
- `server/memory/factory.py` - Provider factory
- `services/*/lib/memory/factory.py` - Service factories
- Add feature flag gating

## Acceptance Criteria
- [ ] MemoryProvider factory interface fixed
- [ ] Provider defaults working
- [ ] Request signatures compatible
- [ ] Feature flag gating implemented
- [ ] Integration tests passing

## Related
- SPEC-139: Audit Reconciliation & Rust Integration Readiness
- SPEC-131: Memory Router Rationalization
""",
            "priority": "High",
            "tags": ["spec-139", "rust", "python", "memory-provider", "integration"],
        },
        {
            "subject": "SPEC-139: CI Markers and Rust Integration Test Setup",
            "description": """# SPEC-139: CI Markers and Rust Integration Test Setup

**SPEC**: SPEC-139 (Audit Reconciliation & Rust Integration Readiness)

## Objective
Establish gating strategy for Rust integration tests and CI opt-in. Update CI workflows to quarantine optional Rust integration tests until ready.

## Requirements
- Add pytest markers for Rust integration tests
- Update CI workflows to exclude Rust tests by default
- Add opt-in mechanism for Rust tests
- Document CI gating strategy
- Ensure Rust tests can run when enabled

## Acceptance Criteria
- [ ] Pytest markers added for Rust integration tests
- [ ] CI workflows updated to exclude Rust tests by default
- [ ] Opt-in mechanism working
- [ ] CI gating strategy documented
- [ ] Rust tests can run when enabled

## Related
- SPEC-139: Audit Reconciliation & Rust Integration Readiness
""",
            "priority": "Normal",
            "tags": ["spec-139", "rust", "ci", "testing", "pytest"],
        },
    ]

    print("=" * 80)
    print("CREATING SPEC-139 STORIES IN TAIGA")
    print("=" * 80)
    print()

    created_count = 0
    for story_data in stories:
        try:
            result = importer.create_user_story(
                project_id=project_id,
                subject=story_data["subject"],
                description=story_data["description"],
                priority=story_data["priority"],
                tags=story_data["tags"],
            )

            if result:
                ref = result.get("ref", "N/A")
                print(f"✅ Created US#{ref} - {story_data['subject']}")
                created_count += 1
            else:
                print(f"❌ Failed to create: {story_data['subject']}")
        except Exception as e:
            print(f"❌ Error creating story: {e}")
            print(f"   Story: {story_data['subject']}")

    print()
    print("=" * 80)
    print(f"✅ Created {created_count} stories for SPEC-139")
    print("=" * 80)

    if created_count > 0:
        print()
        print("📋 Next steps:")
        print("   1. Assign stories to Developer H")
        print("   2. Review and prioritize stories")
        print("   3. Start working on highest priority story")


if __name__ == "__main__":
    main()
