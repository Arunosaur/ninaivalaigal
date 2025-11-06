#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Manual update for Story #412 - Update via Taiga API directly
"""

import sys

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
PROJECT_SLUG = "ninaivalaigal"
STORY_REF = 412


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
    print("Updating Story #412 - Test Coverage Progress")
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
- ✅ **load-tester**: 82.8% (EXCEEDED 80% target!) 🎉
- ⚠️ **grpc-gateway**: 79.1% (needs +0.9% to reach 80%)
- ⚠️ **cli-tools**: 44.1% (making good progress, +2.2% this session)

**Work Completed This Session:**

1. **Load-Tester (82.8% ✅ COMPLETE)**
   - Added comprehensive execution tests for metrics, server, and WebSocket commands
   - Added extensive buildOptions tests covering all configuration paths
   - Added tests for init quick command behavior
   - **Status**: Exceeded target, can be marked complete

2. **CLI-Tools (44.1% ⚠️ IN PROGRESS)**
   - Enhanced profile command tests (list, show, use subcommands)
   - Added graph schema, index, and constraints command tests
   - Added tests for display helper functions
   - **Progress**: +2.2% improvement this session
   - **Note**: 80% target may be challenging - interactive commands (0% coverage) are complex to test

3. **gRPC-Gateway (79.1% ⚠️ NEARLY COMPLETE)**
   - Already at 79.1% from previous work
   - Needs only +0.9% to reach 80%
   - **Quick win opportunity** for next session

**Test Files Added:**
- `go-services/load-tester/commands_low_coverage_test.go`
- `go-services/load-tester/grpc_tester_build_options_test.go`
- `go-services/cli-tools/config_profile_execution_comprehensive_test.go`
- `go-services/cli-tools/graph_commands_execution_enhanced_test.go`
- `go-services/cli-tools/graph_index_constraints_execution_test.go`

**Recommendations:**
1. ✅ **Mark load-tester as complete** (82.8% > 80% target)
2. ⚠️ **gRPC-gateway**: Quick win - only needs 2-3 more edge case tests
3. ⚠️ **CLI-tools**: Consider pragmatic approach - 70-75% may be more realistic target
   - Interactive commands (0% coverage) require complex mocking
   - May benefit from split into follow-up story for advanced coverage

**Next Steps:**
- Complete gRPC-gateway quick win (+0.9%)
- Continue CLI-tools core command coverage (target 60%+)
- Consider splitting CLI-tools advanced coverage into separate story

**Status**: ⚠️ **IN PROGRESS** - 1 of 3 services complete, significant progress on all
"""

    new_desc = current_desc + progress_update

    if update_story(auth_token, story["id"], new_desc, story.get("version", 1)):
        print("✅ Story #412 updated successfully!")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
