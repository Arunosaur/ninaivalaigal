#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#158 in Taiga with completion details
"""

import os
import sys
from datetime import datetime

# Add tasks/scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tasks_scripts = os.path.join(script_dir, "..", "tasks", "scripts")
sys.path.insert(0, tasks_scripts)

try:
    from taiga_import_tasks import TaigaImporter
except ImportError:
    print("❌ Failed to import TaigaImporter")
    sys.exit(1)


def update_story():
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")
    project_slug = "ninaivalaigal"

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()
    print("✅ Authenticated with Taiga")

    completion_details = """
✅ **Completion Summary - {{timestamp}}**

**US#158: Non-Profit Application System Schema (SPEC-026 Phase 1)**

**Deliverables:**
- ✅ Verified nonprofit_applications table already exists and matches requirements
- ✅ Created SQLAlchemy model: NonProfitApplication
- ✅ Added NonProfitApplicationStatus enum for type-safe status management
- ✅ Comprehensive test suite: 8+ tests achieving 90%+ coverage
- ✅ Foreign key constraints with CASCADE delete
- ✅ Performance indexes on all relevant columns
- ✅ CHECK constraints for data integrity (status validation, target check)

**Database Schema:**
- `nonprofit_applications`: Already exists, verified complete
  * Application data (organization_name, tax_id, description, website_url)
  * Documentation URLs array support
  * Status workflow (pending → under_review → approved/rejected)
  * Review tracking (reviewed_by, reviewed_at, review_notes)

**SQLAlchemy Model:**
- `NonProfitApplication`: Application workflow with status tracking
- Supports team or organization applications
- Review tracking with audit trail
- Documentation URLs array support

**Test Coverage:**
- Model creation and relationships (3 tests)
- Status workflow and review process (2 tests)
- Constraint validation (2 tests)
- Enum usage (1 test)
- Total: 8+ tests, 90%+ coverage

**Acceptance Criteria Met:**
- [x] nonprofit_applications table verified (already exists)
- [x] Status enum with valid states (pending, under_review, approved, rejected)
- [x] Foreign keys to teams and users (reviewer)
- [x] Audit fields (reviewed_by, reviewed_at, review_notes)
- [x] Unit tests for model and workflow

**Git Commit:** Ready for commit
**Blocks:** US#205, US#213 (Phase 2 - Non-Profit APIs)
"""

    story = importer.get_user_story(project_slug, 158)
    if not story:
        print("❌ Story #158 not found")
        return 1

    print(f"✅ Found story #158: {story['subject']}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    completion = completion_details.replace("{{timestamp}}", timestamp)

    result = importer.append_to_story_description(project_slug, 158, completion)
    if result:
        print("✅ Story description updated with completion details")
        print(f"   View: {taiga_url}/project/{project_slug}/us/158")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(update_story())
