#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga story for SPEC-112: E2E Tests with Playwright - Optional Enhancements

This script creates a story for the optional enhancements identified during SPEC-112 validation.
"""

import os
import sys
from typing import Dict, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer assignments
DEVELOPER_C_USERNAME = "developer-c"

# SPEC-112 story for optional enhancements
STORY = {
    "subject": "SPEC-112: E2E Tests with Playwright - Optional Enhancements",
    "description": """**Goal**: Add optional enhancements to complete SPEC-112 implementation

**Context**: SPEC-112 is 85% complete and functional. This story adds optional enhancements to reach 100% alignment with the specification.

**Current Status:**
- ✅ Playwright configuration working (3 browsers)
- ✅ E2E test suite comprehensive (14 test files)
- ✅ CI integration working
- ✅ Package scripts working

**Optional Enhancements to Add:**

### 1. Makefile Target
- [ ] Add `make e2e` target to root Makefile
- [ ] Add `make e2e-ui` for UI mode
- [ ] Add `make e2e-debug` for debug mode
- [ ] Ensure Makefile targets call appropriate npm scripts

**Example Makefile addition:**
```makefile
e2e:
	cd frontend-nextjs-customer && npm run test:e2e

e2e-ui:
	cd frontend-nextjs-customer && npm run test:e2e:ui

e2e-debug:
	cd frontend-nextjs-customer && npm run test:e2e:debug
```

### 2. Dedicated E2E Workflow with Database Services
- [ ] Create `.github/workflows/e2e.yml` as specified in SPEC-112
- [ ] Add PostgreSQL service (postgres:15) with health checks
- [ ] Add Redis service (redis:7-alpine) with health checks
- [ ] Configure DATABASE_URL and REDIS_URL environment variables
- [ ] Ensure backend API starts before E2E tests
- [ ] Upload Playwright HTML report as artifact
- [ ] Configure retention-days: 30 for reports

**Workflow should include:**
- PostgreSQL service on port 5432
- Redis service on port 6379
- Backend API startup (uvicorn)
- Playwright browser installation
- E2E test execution
- Report artifact upload

### 3. Database Seeding for Tests
- [ ] Create `scripts/db-seed-test.ts` (or equivalent)
- [ ] Add `db:seed:test` script to package.json
- [ ] Ensure test user creation (`test@ninaivalaigal.com`)
- [ ] Ensure test memories creation
- [ ] Document test data structure
- [ ] Verify test isolation (database reset between tests)

**Test seed script should:**
- Create test user with known credentials
- Create test memories for test user
- Use Prisma or appropriate ORM
- Handle errors gracefully

### 4. Test Metrics/Monitoring Integration
- [ ] Create `tests/e2e/utils/metrics.ts`
- [ ] Implement `reportTestMetrics()` function
- [ ] Report test name, duration, status, timestamp
- [ ] Integrate with monitoring service (or logging)
- [ ] Add metrics reporting to test hooks
- [ ] Document metrics endpoint/format

**Metrics should track:**
- Test pass/fail rate (target: > 95%)
- Flakiness rate (target: < 5%)
- Average duration per test
- Browser compatibility matrix

### 5. Coverage Verification
- [ ] Verify coverage targets are met:
  - Authentication: 100% (login, logout, signup)
  - Dashboard: 90% (analytics, memory list)
  - Memory CRUD: 95% (create, read, update, delete)
  - Profile: 80% (view, edit settings)
- [ ] Document actual coverage vs targets
- [ ] Add coverage reporting if gaps found

### 6. Performance Budget Verification
- [ ] Verify test suite duration < 5 minutes (CI)
- [ ] Verify single test timeout < 30 seconds
- [ ] Verify page load time < 2 seconds
- [ ] Verify API response time < 500ms
- [ ] Document performance metrics
- [ ] Add performance alerts if budgets exceeded

**Acceptance Criteria:**
- ✅ `make e2e` target works in root Makefile
- ✅ Dedicated `.github/workflows/e2e.yml` exists with PostgreSQL/Redis services
- ✅ Database seeding script exists and works
- ✅ Test metrics integration implemented (optional: can use logging)
- ✅ Coverage targets verified (or documented gaps)
- ✅ Performance budgets verified
- ✅ All enhancements documented

**Reference**: SPEC-112 Sections:
- Section 3: `make e2e` target
- Section 4: GitHub Actions workflow (`.github/workflows/e2e.yml`)
- Section 6: Test Data Management (database seeding)
- Section 9: Monitoring (test metrics)
- Section 8: Coverage Targets
- Section 9: Performance Budgets

**Note**: These are optional enhancements. The current E2E test suite is functional and working. These additions improve alignment with the specification and add useful tooling.""",
    "tags": ["spec-112", "e2e", "playwright", "enhancement", "optional", "testing", "ci-cd"],
}


def authenticate() -> str:
    """Authenticate with Taiga and return auth token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    )
    response.raise_for_status()
    return response.json()["auth_token"]


def get_project_id(headers: Dict[str, str]) -> int:
    """Get ninaivalaigal project ID."""
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug=ninaivalaigal", headers=headers)
    response.raise_for_status()
    return response.json()["id"]


def get_user_id(headers: Dict[str, str], username: str) -> Optional[int]:
    """Get user ID by username."""
    # Try global user search
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    response.raise_for_status()
    users = response.json()

    for user in users:
        if user.get("username") == username:
            return user["id"]

    return None


def create_story(headers: Dict[str, str], project_id: int, story: Dict, assignee_id: Optional[int]) -> Dict:
    """Create a Taiga user story."""
    story_data = {
        "project": project_id,
        "subject": story["subject"],
        "description": story["description"],
        "tags": story["tags"],
        "status": 1,  # New
    }

    if assignee_id:
        story_data["assigned_to"] = assignee_id

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)
    response.raise_for_status()
    return response.json()


def main():
    """Main function."""
    print("🔐 Authenticating with Taiga...")
    auth_token = authenticate()
    headers = {"Authorization": f"Bearer {auth_token}"}

    print("📦 Getting project ID...")
    project_id = get_project_id(headers)

    print(f"👤 Getting Developer C user ID...")
    developer_c_id = get_user_id(headers, DEVELOPER_C_USERNAME)
    if not developer_c_id:
        print(f"⚠️  Warning: {DEVELOPER_C_USERNAME} not found, story will be unassigned")

    print(f"\n📝 Creating SPEC-112 enhancement story...\n")

    try:
        created = create_story(headers, project_id, STORY, developer_c_id)
        print(f"✅ Created US#{created['ref']}: {created['subject']}")
        print(f"   URL: {TAIGA_URL}/project/ninaivalaigal/us/{created['ref']}")
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
