#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Manual update for Story #413 - Update via Taiga API directly
"""

import sys

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
STORY_REF = 413


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        print(f"❌ Authentication failed: {auth.status_code}")
        sys.exit(1)
    return auth.json()["auth_token"]


def get_story(auth_token, story_ref):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project=1&ref={story_ref}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get story: {response.status_code}")
        sys.exit(1)
    stories = response.json()
    if not stories:
        print(f"❌ Story #{story_ref} not found")
        sys.exit(1)
    return stories[0]


def update_story(auth_token, story_id, description, version):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    payload = {"description": description, "version": version}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def main():
    print("=" * 80)
    print("Updating Story #413 - Java/JetBrains Plugin Test Coverage Progress")
    print("=" * 80)
    print()

    auth_token = authenticate()
    print("✓ Authenticated")

    story = get_story(auth_token, STORY_REF)
    print(f"✓ Found story #{STORY_REF}: {story.get('subject', 'N/A')}")
    print()

    current_desc = story.get("description", "")

    progress_update = """

---

**📊 Progress Update - January 2025**

**Current Status:**
- ✅ **Enhanced Test Suite**: Created 6 comprehensive test files
- ✅ **Tests Added**: ~130+ comprehensive tests
- ⚠️ **Coverage**: Estimated 50-60%+ (needs measurement)
- ⚠️ **Target**: 70%+ (needs ~10-20% more)

**Work Completed:**

1. **Enhanced Test Files Created (6 files)**
   - ✅ `NinaivalaigalClientEnhancedTest.java` - 30+ tests
   - ✅ `RememberActionEnhancedTest.java` - 25+ tests
   - ✅ `RecallActionEnhancedTest.java` - 20+ tests
   - ✅ `ContextStartActionEnhancedTest.java` - 20+ tests
   - ✅ `ContextMenuActionEnhancedTest.java` - 18+ tests
   - ✅ `NinaivalaigalSettingsEnhancedTest.java` - 15+ tests

2. **Test Coverage Improvements**
   - ✅ Client creation with various configurations
   - ✅ Context management (detection, setting, switching)
   - ✅ Action execution with edge cases
   - ✅ Settings persistence and validation
   - ✅ Error handling throughout
   - ✅ Edge cases (empty/null values, special characters, long content)

3. **Test Quality**
   - ✅ Comprehensive functionality testing (not just structure)
   - ✅ Error handling tests
   - ✅ Edge case coverage
   - ✅ Mock-based testing for MCP protocol

**Test Files:**
- Original: 6 minimal test files (~5-10% coverage)
- Enhanced: 6 new comprehensive test files
- **Total**: 11 test files with ~130+ tests

**Coverage Areas:**
- ✅ Client creation and configuration
- ✅ Context management
- ✅ Action execution
- ✅ Settings persistence
- ✅ Error handling
- ⚠️ MCP protocol (requires running server for full coverage)
- ⚠️ UI interactions (requires IntelliJ Platform)

**Next Steps:**
1. Run coverage report to measure actual coverage
2. Add MCP protocol integration tests (if needed for 70%+)
3. Consider IntelliJ Platform integration tests (optional)

**Status**: ⚠️ **IN PROGRESS** - Significant progress made, needs coverage measurement
"""

    new_desc = current_desc + progress_update

    if update_story(auth_token, story["id"], new_desc, story.get("version", 1)):
        print("✅ Story #413 updated successfully!")
        print(f"   - Enhanced test files: 6")
        print(f"   - Tests added: ~130+")
        print(f"   - Estimated coverage: 50-60%+")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
