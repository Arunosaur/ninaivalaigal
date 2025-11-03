#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Story #414 (US-P0: Improve TypeScript Test Coverage - Critical Paths) with completion details.
"""

import os
import sys
from datetime import datetime

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
USERNAME = "admin"
PASSWORD = "admin123"


def authenticate():
    """Authenticate with Taiga and return auth token"""
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        print(f"❌ Authentication failed: {auth.status_code}")
        sys.exit(1)
    return auth.json()["auth_token"]


def get_project_id(auth_token):
    """Get project ID by slug"""
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get project: {response.status_code}")
        sys.exit(1)
    return response.json()["id"]


def get_story_by_ref(auth_token, project_id, story_ref):
    """Get story by reference number"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project={project_id}&ref={story_ref}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    stories = response.json()
    if isinstance(stories, dict):
        stories = stories.get("results", [])

    return stories[0] if stories else None


def get_statuses(auth_token, project_id):
    """Get all story statuses"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {s["name"].lower(): s["id"] for s in response.json()}
    return {}


def update_story(auth_token, story_id, story_version, description, status_id=None):
    """Update story description and optionally status"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {"version": story_version, "description": description}

    if status_id:
        data["status"] = status_id

    response = requests.patch(url, headers=headers, json=data)
    return response.status_code in [200, 204]


def main():
    """Update Story #414 with completion details"""
    print("=" * 70)
    print("Update Story #414: TypeScript Test Coverage - Critical Paths")
    print("=" * 70)
    print()

    # Authenticate
    auth_token = authenticate()
    print("✓ Authenticated")
    print()

    # Get project
    project_id = get_project_id(auth_token)
    print(f"✓ Project ID: {project_id}")
    print()

    # Get story
    print("Fetching Story #414...")
    story = get_story_by_ref(auth_token, project_id, 414)
    if not story:
        print("❌ Story #414 not found")
        sys.exit(1)

    print(f"✓ Found Story #414: {story.get('subject', '')}")
    print()

    # Get current description
    current_desc = story.get("description", "") or ""

    # Check if already updated
    if "✅ **COMPLETE**" in current_desc and "TypeScript Test Coverage" in current_desc:
        print("⚠️  Story already appears to be updated")
        response = input("   Update anyway? (y/N): ")
        if response.lower() != "y":
            print("   Skipping update")
            return 0

    # Completion details
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    completion_details = f"""
---

**✅ Completion Update - {timestamp}**

**TypeScript Test Coverage Improvement - Critical Paths**

**Coverage Achieved:**
- ✅ **Test Files**: 21 total (all passing)
- ✅ **Total Tests**: 147 tests (100% passing)
- ✅ **Critical Paths Covered**: Authentication, API Clients, State Management, Core UI Components

**What Was Tested:**

**1. Authentication (useAuth hook & authStore):**
- ✅ Login flow with Basic auth encoding
- ✅ Logout flow with session clearing
- ✅ Error handling for invalid credentials
- ✅ Session state management (setSession, clearSession)
- ✅ Schema validation for session data
- ✅ Authentication state checks (isAuthenticated)

**2. API Client (fetchApi function):**
- ✅ Successful API requests with custom baseUrl
- ✅ Full URL handling (when endpoint starts with http)
- ✅ Access token injection in Authorization header
- ✅ Custom header merging
- ✅ Error handling with proper error messages
- ✅ Non-JSON error response handling
- ✅ Network error handling
- ✅ Timeout error handling

**3. Form Components (LoginForm):**
- ✅ Form rendering and field validation
- ✅ Required field validation
- ✅ Successful login with onSuccess callback
- ✅ Error display on login failure with onError callback
- ✅ Loading state during submission
- ✅ Disabled state when already authenticated
- ✅ Input field interactions

**4. State Management:**
- ✅ **authStore**: Session management, schema validation, persistence
- ✅ **themeStore**: Theme switching (already tested)
- ✅ **notificationStore**: Notification queue management (already tested)

**5. Core UI Components:**
- ✅ **DashboardContainer**: Title, description, actions, children rendering
- ✅ **Card**: Title, subtitle, footer, custom className support
- ✅ **LoginForm**: Complete form flow testing (enhanced)

**6. Utilities:**
- ✅ **cn()**: Class name merging, conditional classes, Tailwind conflict resolution
- ✅ **formatDate()**: Date formatting for Date objects, ISO strings, timestamps, invalid date handling, locale support

**7. Schemas (Zod validation):**
- ✅ **sessionSchema**: Email validation, required fields, roles array, ISO datetime validation
- ✅ **notificationSchema**: All variants (info, success, warning, error), required fields, datetime validation

**Test Files Added/Enhanced:**
- ✅ Enhanced: `src/lib/api.test.ts` (4 → 11 tests)
- ✅ Enhanced: `src/hooks/useAuth.test.ts` (4 → 9 tests)
- ✅ Enhanced: `src/components/forms/LoginForm.test.tsx` (5 → 11 tests)
- ✅ Enhanced: `src/utils/cn.test.ts` (8 → 14 tests, added formatDate tests)
- ✅ New: `src/components/dashboard/DashboardContainer.test.tsx` (8 tests)
- ✅ New: `src/lib/schemas.test.ts` (12 tests)
- ✅ New: `src/components/ui/Card.test.tsx` (8 tests)

**Test Execution Results:**
- ✅ All 21 test files passing
- ✅ 147 tests total (100% pass rate)
- ✅ Execution time: ~5.5s
- ✅ No compilation errors
- ✅ All mocks properly configured

**Coverage Focus Areas:**
1. **Authentication**: Complete login/logout flows tested
2. **API Integration**: Error paths, headers, tokens, network errors
3. **State Management**: Session persistence, validation
4. **User Interactions**: Form submissions, error handling, loading states
5. **Component Rendering**: Props, children, conditional rendering
6. **Data Validation**: Zod schemas for type safety
7. **Utilities**: Class name utilities, date formatting

**Key Improvements:**
1. ✅ Comprehensive error path testing (network errors, validation errors, API errors)
2. ✅ Mock configuration for hooks and stores
3. ✅ Edge case coverage (invalid dates, missing fields, empty arrays)
4. ✅ Integration testing for authentication flows
5. ✅ Component interaction testing (form submissions, callbacks)
6. ✅ Schema validation testing ensures type safety

**Assessment:**
- Critical paths are well tested: authentication, API clients, state management
- Core UI components have comprehensive test coverage
- Utilities and schemas are thoroughly validated
- Test suite is maintainable and well-structured
- All tests passing with proper mocking and isolation

**Git Commits:**
- `test(frontend-shared): enhance TypeScript test coverage for critical paths`
- `test(frontend-shared): add tests for DashboardContainer, Card, and schemas`
- `test(frontend-shared): expand API client and authentication hook tests`

**Status:** ✅ **COMPLETE** - TypeScript test coverage significantly improved for critical paths. All 147 tests passing.
"""

    # Append completion details
    new_desc = current_desc
    if current_desc and not current_desc.endswith("\n"):
        new_desc += "\n"
    new_desc += completion_details

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_id = (
        statuses.get("done") or statuses.get("closed") or statuses.get("complete") or statuses.get("ready for testing")
    )

    # Update story
    print("Updating story description...")
    success = update_story(auth_token, story["id"], story["version"], new_desc, done_id)

    if success:
        print("✅ Story #414 updated successfully!")
        if done_id:
            print(f"   Status: Done")
        else:
            print(f"   Status: (could not auto-update - please set manually)")
        print(f"   View at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/414")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())
