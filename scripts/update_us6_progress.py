#!/usr/bin/env python3
"""
Update US#6 (US-92: Comprehensive API Test Suite) with progress
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "taiga", "scripts"))
from example_update_story import (
    authenticate,
    get_project_id,
    get_story_by_id,
    get_story_by_ref,
    update_story,
)

# Configuration
STORY_REF = 6


def main():
    """Update story with initial progress."""
    print("=" * 80)
    print("Updating US#6: Comprehensive API Test Suite - Starting Work")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed")
        return 1
    print("✅ Authenticated")
    print()

    # Get project
    print("2️⃣  Getting project...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Project not found")
        return 1
    print(f"✅ Project ID: {project_id}")
    print()

    # Get story
    print(f"3️⃣  Getting story #{STORY_REF}...")
    story = get_story_by_ref(auth_token, project_id, STORY_REF)
    if not story:
        print(f"❌ Story #{STORY_REF} not found")
        return 1

    story_id = story.get("id")
    story_version = story.get("version", 1)

    print(f"✅ Found story: {story.get('subject', 'N/A')}")
    print(f"   Story ID: {story_id}, Version: {story_version}")
    print()

    # Get current description
    print("4️⃣  Getting current story description...")
    story_full = get_story_by_id(auth_token, story_id)
    current_desc = story_full.get("description", "")
    print(f"   Current description length: {len(current_desc)} characters")
    print()

    # Add initial progress
    print("5️⃣  Adding initial progress...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    progress = f"""

---

## 🚀 Starting Work - {timestamp}

**Assigned to**: Developer H
**Status**: In Progress

### Current State Analysis

**Existing Test Suite Found:**
- ✅ `tests/integration/test_comprehensive_api_suite.py` - 39 test cases
- ✅ Test coverage for: Health, Auth, User, Team, Context, Memory, Organization
- ✅ Error handling and performance tests included
- ✅ CI/CD integration exists

### Acceptance Criteria Review

**AC1**: Unit tests for all 277 API endpoints
- ⏳ Current: 39 integration tests
- 📋 Need: Unit tests for all endpoints

**AC2**: Integration tests for critical user flows
- ✅ Partial: Some integration tests exist
- 📋 Need: Complete critical flow coverage

**AC3**: Contract tests for service boundaries
- ❌ Missing: Need contract tests

**AC4**: Test coverage > 80% for API routers
- ⏳ Need to measure current coverage

**AC5**: All tests pass in CI pipeline
- ⏳ Need to verify CI integration

**AC6**: Performance regression tests
- ✅ Partial: Some performance tests exist

**AC7**: Security tests (SQL injection, XSS, auth bypass)
- ❌ Missing: Need security test suite

**AC8**: Error handling tests (4xx, 5xx responses)
- ✅ Partial: Some error handling tests exist

**AC9**: Test execution time < 5 minutes
- ⏳ Need to measure and optimize

**AC10**: Test reports generated and published
- ⏳ Need to verify report generation

### Next Steps

1. ✅ Review existing test suite
2. ⏳ Run existing tests and verify they pass
3. ⏳ Identify all API endpoints (277 total)
4. ⏳ Create unit tests for missing endpoints
5. ⏳ Add contract tests
6. ⏳ Add security tests
7. ⏳ Measure and improve coverage
8. ⏳ Verify CI/CD integration
9. ⏳ Generate test reports
10. ⏳ Complete comprehensive testing

**Starting comprehensive analysis and implementation...**
"""

    new_desc = current_desc + progress if current_desc else progress.strip()

    # Update story
    print("6️⃣  Updating story...")
    success, message = update_story(
        auth_token=auth_token, story_id=story_id, story_version=story_version, description=new_desc
    )

    if success:
        print("✅ Story updated with initial progress!")
        print(f"   Story: http://localhost:9000/project/ninaivalaigal/us/{STORY_REF}")
        return 0
    else:
        print(f"❌ {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
