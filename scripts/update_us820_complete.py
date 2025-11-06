#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Update US#820 with completion status for CI markers and Rust integration test setup"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
from datetime import datetime

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    story = importer.get_user_story("ninaivalaigal", 820)
    if not story:
        print("Story #820 not found")
        return

    print(f"Current story: {story['subject']}")
    print(f"Current status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
    print()

    # Get project statuses to find "Done" status
    headers = importer._get_headers()
    project_id = story["project"]
    url = f"{taiga_url}/api/v1/userstory-statuses"
    params = {"project": project_id}
    response = requests.get(url, headers=headers, params=params)

    done_status_id = None
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == "Done":
                done_status_id = status["id"]
                break

    # Update description with completion
    completion_update = f"""

---
**Completion Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

## ✅ US#820 COMPLETE - CI Markers and Rust Integration Test Setup

**Developer**: Developer H
**Status**: ✅ All acceptance criteria met

### Completed Work:

1. **✅ Pytest Marker Registration**
   - `rust_integration` marker registered in `pytest.ini`
   - Marker description: "Tests that exercise the Rust memory provider integration"

2. **✅ Test Gating Logic** (`tests/conftest.py`)
   - `--run-rust-integration` CLI option added
   - Environment variable support: `PYTEST_RUN_RUST_INTEGRATION`
   - Feature flag support: `USE_RUST_MEMORY`
   - Automatic skipping of rust_integration tests unless explicitly enabled
   - Clear skip reason message

3. **✅ Test Files Marked**
   - ✅ `tests/integration/test_memory_service_rust.py` - Added `pytestmark = pytest.mark.rust_integration`
   - ✅ `tests/integration/test_memory_service_rust_standalone.py` - Added marker
   - ✅ `services/core-api/tests/test_rust_memory_provider.py` - Already marked

4. **✅ CI Workflow Integration**
   - ✅ Verified CI workflows exclude rust_integration by default (via `tests/conftest.py`)
   - ✅ Created optional CI job: `.github/workflows/rust-integration-tests.yml`
   - ✅ Documented CI gating strategy: `docs/RUST_INTEGRATION_CI_STRATEGY.md`

### CI Workflow Features:

**New Workflow**: `.github/workflows/rust-integration-tests.yml`
- **Triggers**: Nightly (3 AM UTC), manual dispatch, push to Rust-related files
- **Features**:
  - Builds Rust Memory Service from source
  - Starts PostgreSQL, Redis, Rust service, and Core API
  - Runs all Rust integration tests with `PYTEST_RUN_RUST_INTEGRATION=1`
  - Generates test reports (JUnit XML, HTML)
  - Uploads artifacts and comments on PRs
  - Creates GitHub issues on failure

### Gating Mechanism:

Tests are skipped unless one of:
- `PYTEST_RUN_RUST_INTEGRATION=1` environment variable
- `USE_RUST_MEMORY=1` feature flag
- `--run-rust-integration` CLI flag

### Default CI Workflows Verified:

All standard CI workflows exclude Rust integration tests by default:
- ✅ `comprehensive-api-test-suite.yml` - No Rust tests
- ✅ `pr-quality-gates.yml` - No Rust tests
- ✅ `ci-lint.yml` - No Rust tests
- ✅ `foundation-tests.yml` - No Rust tests

### Documentation Created:

1. ✅ `docs/RUST_INTEGRATION_CI_STRATEGY.md` - Comprehensive CI gating strategy
2. ✅ `docs/CI_INTEGRATION_TESTING_COMPLETE.md` - Completion summary
3. ✅ Updated `docs/US820_CI_MARKERS_RUST_INTEGRATION.md` - Marked as complete
4. ✅ Updated `specs/139-audit-reconciliation-rust-readiness/RUST_INTEGRATION_GATE.md` - CI requirement marked complete

### Acceptance Criteria: ✅ All Met

- [x] Pytest markers added for Rust integration tests
- [x] CI workflows updated to exclude Rust tests by default (via conftest.py)
- [x] Opt-in mechanism working (CLI flag, env vars, feature flag)
- [x] CI gating strategy documented in workflow files
- [x] Optional CI job runs full suite with Rust service (nightly or on-demand)
- [x] Rust tests can run when enabled

### Files Created/Modified:

1. ✅ `.github/workflows/rust-integration-tests.yml` - CREATED (new CI workflow)
2. ✅ `docs/RUST_INTEGRATION_CI_STRATEGY.md` - CREATED
3. ✅ `docs/CI_INTEGRATION_TESTING_COMPLETE.md` - CREATED
4. ✅ `docs/US820_CI_MARKERS_RUST_INTEGRATION.md` - UPDATED (marked complete)
5. ✅ `specs/139-audit-reconciliation-rust-readiness/RUST_INTEGRATION_GATE.md` - UPDATED

### Verification:

- ✅ Default pytest runs exclude Rust tests (13 tests deselected)
- ✅ Tests can be enabled via flags/env vars
- ✅ CI workflow ready for nightly/on-demand runs

**Status**: ✅ **COMPLETE** - All acceptance criteria met. CI workflow integration complete.
"""

    current_desc = story.get("description", "")
    new_desc = current_desc + completion_update

    updates = {"description": new_desc.strip()}

    # Update status to Done if available
    if done_status_id:
        updates["status"] = done_status_id

    try:
        result = importer.update_user_story(
            story_id=story["id"],
            version=story["version"],
            updates=updates,
            retry_on_version_conflict=True,
            max_retries=3,
        )

        if result:
            print("✅ Story updated successfully")
            if done_status_id:
                print("   - Status updated to 'Done'")
            print("   - Completion details added")
            print("   - All acceptance criteria marked complete")
        else:
            print("❌ Failed to update story")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
