#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-113: Profile & Settings Pages

This script creates stories for the missing implementation items identified
during SPEC-113 validation.
"""

import os
import sys
from typing import Dict, List, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer assignments
DEVELOPER_C_USERNAME = "developer-c"

# SPEC-113 stories to create
STORIES = [
    {
        "subject": "SPEC-113: Implement avatar upload functionality",
        "description": """**Goal**: Add avatar upload and display functionality to profile/settings

**Context**: SPEC-113 requires editable avatar functionality. Currently, avatar upload is not implemented.

**Tasks**:
- [ ] Create avatar upload UI component for Settings page
- [ ] Implement backend endpoint `POST /users/me/avatar` for avatar upload
- [ ] Configure file storage (S3/CloudFlare R2 or local storage)
- [ ] Add image validation (size: max 5MB, formats: JPG/PNG/WebP, dimensions: square preferred)
- [ ] Add image resize/crop functionality (auto-resize to square if needed)
- [ ] Add avatar display in Settings page
- [ ] Add avatar preview before upload
- [ ] Handle avatar deletion/removal
- [ ] Add avatar URL to user profile response (`GET /users/me`)
- [ ] Sanitize file names to prevent XSS
- [ ] Add error handling for upload failures
- [ ] Update user model to include avatar field (if not exists)

**Acceptance Criteria**:
- ✅ Users can upload avatar image from Settings page
- ✅ Avatar displays in Settings page after upload
- ✅ Avatar URL included in profile API response
- ✅ Image validation works (size, format, dimensions)
- ✅ Avatar deletion works
- ✅ File names sanitized
- ✅ Error handling for upload failures
- ✅ Tests pass

**Reference**: SPEC-113 Section 1 (Profile page with avatar), Section 9 (Future Enhancements - Avatar upload)""",
        "tags": ["spec-113", "avatar", "upload", "profile", "file-upload"],
    },
    {
        "subject": "SPEC-113: Create separate profile page",
        "description": """**Goal**: Create dedicated `/profile` page separate from `/settings` page

**Context**: SPEC-113 specifies a separate `/profile` page (`src/app/(customer)/profile/page.tsx`) for profile editing, with `/settings` for preferences only. Currently, both are combined in a single Settings page.

**Tasks**:
- [ ] Create `apps/customer/src/pages/Profile.tsx` (or equivalent based on routing structure)
- [ ] Move profile editing form from Settings to Profile page
- [ ] Keep Settings page for preferences only (theme, notifications, privacy)
- [ ] Add navigation link between Profile and Settings pages
- [ ] Ensure consistent styling and UX between pages
- [ ] Update routing configuration
- [ ] Test navigation flow
- [ ] Update documentation

**Alternative**: If keeping single Settings page is preferred, document the deviation from SPEC.

**Acceptance Criteria**:
- ✅ Separate `/profile` page exists (or deviation documented)
- ✅ Profile editing form on Profile page
- ✅ Settings page contains only preferences
- ✅ Navigation between pages works
- ✅ Consistent styling
- ✅ Tests pass

**Reference**: SPEC-113 Section 1 (`src/app/(customer)/profile/page.tsx`)""",
        "tags": ["spec-113", "profile", "page", "routing", "ui"],
    },
    {
        "subject": "SPEC-113: Implement settings layout with sidebar navigation",
        "description": """**Goal**: Create settings layout with sidebar navigation for multiple settings pages

**Context**: SPEC-113 specifies a settings layout with sidebar navigation (`src/app/(customer)/settings/layout.tsx`) with separate pages: General, Security, Notifications, Billing. Currently, all settings are on a single page.

**Tasks**:
- [ ] Create settings layout component with sidebar
- [ ] Create `/settings` page (General settings)
- [ ] Create `/settings/security` page (if not exists)
- [ ] Create `/settings/notifications` page (if not exists)
- [ ] Create `/settings/billing` page (if not exists)
- [ ] Add sidebar navigation between settings pages
- [ ] Ensure active page highlighting in sidebar
- [ ] Add breadcrumbs if needed
- [ ] Move existing settings sections to appropriate pages
- [ ] Test navigation flow
- [ ] Ensure responsive design

**Acceptance Criteria**:
- ✅ Settings layout with sidebar exists
- ✅ Multiple settings pages exist (General, Security, Notifications, Billing)
- ✅ Sidebar navigation works
- ✅ Active page highlighted in sidebar
- ✅ Content organized correctly across pages
- ✅ Responsive design works
- ✅ Tests pass

**Reference**: SPEC-113 Section 5 (`src/app/(customer)/settings/layout.tsx`)""",
        "tags": ["spec-113", "settings", "sidebar", "navigation", "layout", "ui"],
    },
    {
        "subject": "SPEC-113: Implement optimistic UI updates for profile edits",
        "description": """**Goal**: Add optimistic UI updates for instant feedback on profile changes

**Context**: SPEC-113 specifies optimistic UI updates via React Query for instant feedback. Current implementation may not have optimistic updates.

**Tasks**:
- [ ] Implement optimistic updates for profile name edits
- [ ] Implement optimistic updates for avatar changes
- [ ] Show immediate UI feedback on form submission
- [ ] Rollback on error with error message
- [ ] Use React Query or similar for cache invalidation
- [ ] Ensure smooth user experience
- [ ] Test optimistic update flow
- [ ] Test error rollback flow

**Acceptance Criteria**:
- ✅ Profile edits show immediate UI feedback
- ✅ Updates appear instantly before API response
- ✅ Error rollback works correctly
- ✅ Error messages displayed on failure
- ✅ Cache invalidation works
- ✅ Tests pass

**Reference**: SPEC-113 Section 1 (Optimistic UI updates via React Query)""",
        "tags": ["spec-113", "optimistic-updates", "ui", "react-query", "ux"],
    },
    {
        "subject": "SPEC-113: Add unit tests for profile and settings pages",
        "description": """**Goal**: Add comprehensive unit tests for profile and settings functionality

**Context**: SPEC-113 specifies unit tests for profile page. Currently, unit tests are not verified.

**Tasks**:
- [ ] Add unit tests for Settings page component
- [ ] Test profile display and editing
- [ ] Test theme preference changes
- [ ] Test notification preference toggles
- [ ] Test password change form
- [ ] Test avatar upload (if implemented)
- [ ] Test error handling and validation
- [ ] Test optimistic updates (if implemented)
- [ ] Achieve >80% code coverage
- [ ] Add tests to CI pipeline

**Test Framework**: Vitest or Jest

**Acceptance Criteria**:
- ✅ Unit tests for Settings page exist
- ✅ Unit tests for Profile page exist (if separate)
- ✅ >80% code coverage achieved
- ✅ Tests run in CI pipeline
- ✅ Tests pass consistently

**Reference**: SPEC-113 Section 8 (Testing - Unit Tests)""",
        "tags": ["spec-113", "unit-tests", "testing", "coverage"],
    },
    {
        "subject": "SPEC-113: Add E2E tests for profile and settings flows",
        "description": """**Goal**: Add E2E tests for profile editing and settings management

**Context**: SPEC-113 specifies E2E tests for profile editing. Currently, E2E tests are not verified.

**Tasks**:
- [ ] Add E2E test for profile editing flow
- [ ] Test theme preference change
- [ ] Test notification preference toggle
- [ ] Test password change flow
- [ ] Test avatar upload (if implemented)
- [ ] Test error scenarios (invalid inputs, network errors)
- [ ] Test navigation between profile and settings
- [ ] Add to existing E2E test suite
- [ ] Ensure tests run in CI

**Reference**: SPEC-112 (E2E Tests with Playwright)

**Acceptance Criteria**:
- ✅ E2E tests for profile editing exist
- ✅ E2E tests for settings changes exist
- ✅ Error scenarios tested
- ✅ Tests run in CI pipeline
- ✅ Tests pass consistently

**Reference**: SPEC-113 Section 8 (Testing - E2E Tests)""",
        "tags": ["spec-113", "e2e-tests", "playwright", "testing"],
    },
]


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
        print(f"⚠️  Warning: {DEVELOPER_C_USERNAME} not found, stories will be unassigned")

    print(f"\n📝 Creating {len(STORIES)} SPEC-113 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        print(f"{i}. Creating: {story['subject'][:60]}...")
        try:
            created = create_story(headers, project_id, story, developer_c_id)
            created_stories.append(created)
            print(f"   ✅ Created US#{created['ref']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()
