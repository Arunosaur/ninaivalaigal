#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga story for SPEC-113: Profile & Settings Pages - Optional Enhancements

This script creates a story for the optional enhancements identified during SPEC-113 validation.
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

# SPEC-113 story for optional enhancements
STORY = {
    "subject": "SPEC-113: Profile & Settings Pages - Optional Enhancements",
    "description": """**Goal**: Add optional enhancements to complete SPEC-113 implementation

**Context**: SPEC-113 is 90% complete and functional. This story adds optional enhancements to reach 100% alignment with the specification.

**Current Status:**
- ✅ Backend API endpoints working (GET/PUT /users/me)
- ✅ Settings page with profile management working
- ✅ Theme preferences working
- ✅ Notification preferences working
- ✅ Password change working

**Optional Enhancements to Add:**

### 1. Avatar Upload Functionality
- [ ] Add avatar upload UI component to Settings page
- [ ] Implement avatar upload endpoint (`POST /users/me/avatar`)
- [ ] Configure file storage (S3/CloudFlare R2 or local storage)
- [ ] Add image validation (size, format, dimensions)
- [ ] Add avatar display in Settings page
- [ ] Add avatar preview before upload
- [ ] Handle avatar deletion/removal
- [ ] Add avatar URL to user profile response

**Technical Requirements:**
- Accept image formats: JPG, PNG, WebP
- Max file size: 5MB
- Recommended dimensions: 256x256px (square)
- Auto-resize/crop to square if needed
- Sanitize file names to prevent XSS

### 2. Separate Profile Page
- [ ] Create dedicated `/profile` page (separate from `/settings`)
- [ ] Move profile editing form to `/profile` page
- [ ] Keep `/settings` for preferences only
- [ ] Add navigation between profile and settings
- [ ] Ensure consistent styling and UX

**Alternative**: Keep current structure (single `/settings` page) but document deviation from SPEC.

### 3. Optimistic UI Updates
- [ ] Implement optimistic updates for profile edits
- [ ] Show immediate UI feedback on form submission
- [ ] Rollback on error with error message
- [ ] Use React Query or similar for cache invalidation
- [ ] Ensure smooth user experience

**Current**: Updates work but may not have optimistic updates.

### 4. Settings Layout with Sidebar Navigation
- [ ] Create settings layout component with sidebar
- [ ] Create `/settings` page (General)
- [ ] Create `/settings/security` page (if not exists)
- [ ] Create `/settings/notifications` page (if not exists)
- [ ] Create `/settings/billing` page (if not exists)
- [ ] Add sidebar navigation between settings pages
- [ ] Ensure active page highlighting in sidebar
- [ ] Add breadcrumbs if needed

**Current**: Single `/settings` page with all sections. This would split into separate pages.

### 5. Unit Tests
- [ ] Add unit tests for Settings page component
- [ ] Test profile display and editing
- [ ] Test theme preference changes
- [ ] Test notification preference toggles
- [ ] Test password change form
- [ ] Test error handling and validation
- [ ] Achieve >80% code coverage

**Test Framework**: Vitest or Jest

### 6. E2E Tests (Playwright)
- [ ] Add E2E test for profile editing flow
- [ ] Test theme preference change
- [ ] Test notification preference toggle
- [ ] Test password change flow
- [ ] Test avatar upload (if implemented)
- [ ] Test error scenarios (invalid inputs, network errors)
- [ ] Add to existing E2E test suite

**Reference**: SPEC-112 (E2E Tests with Playwright)

### 7. Update SPEC Document (If Desired)
- [ ] Note that implementation uses React (not Next.js)
- [ ] Note that structure uses `/settings` page (not separate `/profile` page)
- [ ] Mark avatar upload as implemented (if done)
- [ ] Document architectural differences from SPEC
- [ ] Update status if needed

**Acceptance Criteria:**
- ✅ Avatar upload functionality working (if implemented)
- ✅ Separate profile page OR documented deviation (if keeping single settings page)
- ✅ Optimistic UI updates working
- ✅ Settings sidebar navigation working (if implemented)
- ✅ Unit tests added with >80% coverage
- ✅ E2E tests added for profile/settings flows
- ✅ SPEC document updated (if needed)
- ✅ All enhancements documented

**Reference**: SPEC-113 Sections:
- Section 1: Profile page (`src/app/(customer)/profile/page.tsx`)
- Section 2: Backend API route (`server/api/users.py`)
- Section 4: Settings page with theme preferences
- Section 5: Layout with settings sidebar
- Section 8: Testing (unit + E2E)
- Section 9: Future Enhancements (avatar upload, etc.)

**Note**: These are optional enhancements. The current profile/settings implementation is functional and working. These additions improve alignment with the specification and add useful features.

**Related Story**: US#31 (Core API - User Profile Endpoints) covers the backend API portion.""",
    "tags": ["spec-113", "profile", "settings", "enhancement", "optional", "ui", "frontend"],
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

    print(f"\n📝 Creating SPEC-113 enhancement story...\n")

    try:
        created = create_story(headers, project_id, STORY, developer_c_id)
        print(f"✅ Created US#{created['ref']}: {created['subject']}")
        print(f"   URL: {TAIGA_URL}/project/ninaivalaigal/us/{created['ref']}")
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()




