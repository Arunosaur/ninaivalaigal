#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#210 in Taiga with completion details
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

**US#210: Team Creation Flow UI (SPEC-026 Phase 4)**

**Pages Created:**
1. ✅ `/team/create` - 3-step team creation wizard
   - Step 1: Team Information (name, description, max members)
   - Step 2: Invite Members (optional email invitations with role selection)
   - Step 3: Review & Create
   - Progress indicator showing current step
   - Form validation and error handling

2. ✅ `/team/dashboard` - Team overview dashboard
   - Memory count and usage statistics
   - Active members list with roles
   - Team information display (invite code, created date, status)
   - Upgrade to organization CTA banner

3. ✅ `/team/[teamId]/invite` - Member invitation UI
   - Email input with role selection (admin, contributor, viewer)
   - Role descriptions for clarity
   - Pending invitations list
   - Error handling and success messages

4. ✅ `/team/[teamId]/upgrade` - Upgrade to organization form
   - Organization name (required)
   - Domain (optional)
   - Organization size selection
   - Industry field (optional)
   - Benefits display

**Technical Implementation:**
- Next.js 15 with App Router
- React Server Components (where applicable)
- TailwindCSS for styling
- TypeScript for type safety
- apiClient for API integration
- Form validation with error handling
- Loading states for async operations

**API Integration:**
- ✅ POST /teams/create-standalone (team creation)
- ✅ GET /teams/my (get current user's team)
- ✅ POST /teams/invite (send invitation)
- ✅ POST /teams/{id}/upgrade-to-org (upgrade to organization)

**Features:**
- ✅ Responsive design (mobile + desktop)
- ✅ Form validation with real-time feedback
- ✅ Error handling with user-friendly messages
- ✅ Loading states for all async operations
- ✅ Progress indicators in wizard
- ✅ Role descriptions for clarity
- ✅ Success/error toast messages

**Acceptance Criteria Met:**
- [x] Team creation form validates input
- [x] Wizard guides user through 3 steps
- [x] Member invitation sends emails (via API)
- [x] Role management interface (role selection in invite form)
- [x] Dashboard displays real-time data (via API)
- [x] Responsive design (mobile + desktop)
- [x] Loading states and error handling
- [x] Integration with US#159 backend APIs

**Accessibility:**
- Semantic HTML elements
- Form labels and error messages
- Keyboard navigation support
- ARIA attributes where needed

**Git Commit:** `feat(spec-026): implement US#210 Team Creation Flow UI`

**Blocks:** Ready for E2E testing (US#215) or proceed with US#211 (Team Billing Pages UI)
"""

    story = importer.get_user_story(project_slug, 210)
    if not story:
        print("❌ Story #210 not found")
        return 1

    print(f"✅ Found story #210: {story['subject']}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    completion = completion_details.replace("{{timestamp}}", timestamp)

    result = importer.append_to_story_description(project_slug, 210, completion)
    if result:
        print("✅ Story description updated with completion details")
        print(f"   View: {taiga_url}/project/{project_slug}/us/210")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(update_story())

