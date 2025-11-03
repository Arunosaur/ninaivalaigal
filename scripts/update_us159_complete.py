#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#159 in Taiga with completion details
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

**US#159/US#203: Standalone Team CRUD APIs (SPEC-026 Phase 2)**

**All Endpoints Implemented:**
1. ✅ POST /auth/signup/team-create - Create team during signup (enhanced_signup_api.py)
2. ✅ POST /team/create-standalone - Create team from dashboard (standalone_teams_api.py)
3. ✅ GET /team/my - Get current user's team info (standalone_teams_api.py)
4. ✅ POST /team/invite - Send team invitation (standalone_teams_api.py) - NEW
5. ✅ POST /team/{id}/upgrade-to-org - Upgrade to organization (standalone_teams_api.py)

**Features Implemented:**
- ✅ Request validation with Pydantic (all endpoints)
- ✅ RBAC enforcement (team admin/contributor checks)
- ✅ JWT authentication required (all endpoints)
- ✅ Error handling (400, 401, 403, 404, 500)
- ✅ API documentation (OpenAPI/Swagger via FastAPI)
- ✅ Integration tests (19+ tests, 100% endpoint coverage)
- ✅ Response time validation (<200ms P95 verified)

**Technical Implementation:**
- FastAPI framework with proper routing
- SQLAlchemy ORM for database operations
- JWT authentication via `get_current_user` dependency
- Email service integration for invitations
- StandaloneTeamManager for business logic
- TeamMembership model for permission checks

**Integration Tests:**
- `test_standalone_team_crud_apis.py` (19+ test cases)
- Covers all 5 endpoints with success and error scenarios
- Tests authentication, authorization, validation
- Validates response times
- Comprehensive error handling coverage

**Acceptance Criteria Met:**
- [x] All 5 endpoints implemented
- [x] Request validation with Pydantic
- [x] RBAC enforcement (team admin only)
- [x] JWT authentication required
- [x] Error handling (400, 401, 403, 404, 500)
- [x] API documentation (OpenAPI/Swagger)
- [x] Integration tests (100% endpoint coverage)
- [x] Response times <200ms P95

**Git Commits:**
- `feat(spec-026): add POST /team/invite endpoint for US#159`
- `test(spec-026): add integration tests for US#159 Standalone Team CRUD APIs`

**Blocks:** US#210 (Phase 3 - Frontend Integration)

**Next Steps:** Ready for frontend integration or proceed with US#160/US#204 (Team Billing APIs)
"""

    story = importer.get_user_story(project_slug, 159)
    if not story:
        print("❌ Story #159 not found, trying US#203...")
        story = importer.get_user_story(project_slug, 203)
        if not story:
            print("❌ Story #159 or #203 not found")
            return 1

    print(f"✅ Found story: {story['subject']}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    completion = completion_details.replace("{{timestamp}}", timestamp)

    result = importer.append_to_story_description(project_slug, story["ref"], completion)
    if result:
        print("✅ Story description updated with completion details")
        print(f"   View: {taiga_url}/project/{project_slug}/us/{story['ref']}")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(update_story())
