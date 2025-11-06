#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create new Taiga stories for migrating React/Vite screens to Jinja2 templates.

Identifies React/Vite implementations and creates migration stories under SPEC-005 (admin)
and appropriate SPEC (customer).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import json

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

# React/Vite implementations to migrate
ADMIN_SCREENS = [
    {
        "name": "Analytics Dashboard",
        "file": "apps/admin-console/src/pages/Analytics.tsx",
        "spec": "005",
        "description": "Convert React Analytics dashboard to Jinja2 template with Chart.js",
        "effort": "3-4 hours",
        "priority": "P1",
    },
    {
        "name": "User Management",
        "file": "apps/admin-console/src/pages/Users.tsx",
        "spec": "005",
        "description": "Convert React User Management page to Jinja2 template with Alpine.js interactivity",
        "effort": "4-6 hours",
        "priority": "P0",
    },
    {
        "name": "Team Management",
        "file": "apps/admin-console/src/pages/Teams.tsx",
        "spec": "005",
        "description": "Convert React Team Management page to Jinja2 template with HTMX for CRUD operations",
        "effort": "4-6 hours",
        "priority": "P0",
    },
    {
        "name": "Admin Login",
        "file": "apps/admin-console/src/pages/Login.tsx",
        "spec": "005",
        "description": "Convert React Login page to Jinja2 template with FastAPI auth integration",
        "effort": "2-3 hours",
        "priority": "P0",
    },
]

CUSTOMER_SCREENS = [
    {
        "name": "Team Billing",
        "file": "apps/customer/src/pages/TeamBilling.tsx",
        "spec": "146",  # Customer UI SPEC (if exists, otherwise use generic)
        "description": "Convert React Team Billing page to Jinja2 template",
        "effort": "4-6 hours",
        "priority": "P1",
    },
    {
        "name": "Team Dashboard",
        "file": "apps/customer/src/pages/TeamDashboard.tsx",
        "spec": "146",
        "description": "Convert React Team Dashboard to Jinja2 template",
        "effort": "4-6 hours",
        "priority": "P1",
    },
    {
        "name": "Team Invoice List",
        "file": "apps/customer/src/pages/TeamInvoiceList.tsx",
        "spec": "146",
        "description": "Convert React Invoice List to Jinja2 template",
        "effort": "3-4 hours",
        "priority": "P1",
    },
    {
        "name": "Memory Browser",
        "file": "apps/customer/src/pages/MemoryBrowser.tsx",
        "spec": "146",
        "description": "Convert React Memory Browser to Jinja2 template (may need React widget for complex interactions)",
        "effort": "6-8 hours",
        "priority": "P2",
    },
]


def create_migration_story(importer, project_id, story_data, dry_run=False):
    """Create a migration story."""
    subject = f"Migrate {story_data['name']} from React/Vite to Jinja2"

    description = f"""## Objective

Convert {story_data['name']} from React/Vite implementation to FastAPI + Jinja2 templates.

## Current Implementation

**Location:** `{story_data['file']}`
**Technology:** React + TypeScript + Vite
**Status:** Active React/Vite implementation

## Target Implementation

**Technology:** FastAPI + Jinja2 templates
- Server-side rendering (Jinja2)
- Client interactivity: Alpine.js or HTMX
- Styling: TailwindCSS (reuse existing styles)
- Optional: React micro-widget if complex interactions needed

## Migration Steps

1. **Create Jinja2 Template**
   - Create `templates/admin/{story_data['name'].lower().replace(' ', '_')}.html` or `templates/customer/...`
   - Base on existing React component structure
   - Reuse TailwindCSS classes from React implementation

2. **Create FastAPI Route**
   - Add route in appropriate router (admin or customer)
   - Connect to existing API endpoints
   - Return Jinja2 template response

3. **Add Interactivity**
   - Use Alpine.js for client-side state
   - Use HTMX for server-side interactions (forms, pagination)
   - Keep React widget only if complex visualization needed

4. **Test**
   - Verify all functionality works
   - Test with real API data
   - Ensure visual parity with React version

5. **Archive React Implementation**
   - Move React file to `/legacy/` directory
   - Update documentation
   - Remove from active codebase

## Acceptance Criteria

- [ ] Jinja2 template created and functional
- [ ] FastAPI route serves template correctly
- [ ] All functionality from React version works
- [ ] Visual parity maintained (same TailwindCSS classes)
- [ ] React file archived
- [ ] Documentation updated

## References

- Architecture Decision: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
- SPEC-005: `specs/005-admin-dashboard/spec.md`

## Estimated Effort

{story_data['effort']}

## Priority

{story_data['priority']}
"""

    tags = [f"spec-{story_data['spec']}", "migration", "react-to-jinja2", "fastapi", "jinja2", "templates"]

    if "admin" in story_data["file"].lower():
        tags.append("admin")
    else:
        tags.append("customer")

    if dry_run:
        print(f"  [DRY RUN] Would create: {subject}")
        print(f"  Spec: SPEC-{story_data['spec']}")
        print(f"  Tags: {', '.join(tags)}")
        print(f"  Priority: {story_data['priority']}")
        print(f"  Effort: {story_data['effort']}")
        return None

    # Get project
    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return None

    # Get status IDs (need "New" status)
    headers = importer._get_headers()
    status_url = f'{taiga_url}/api/v1/userstory-statuses?project={project["id"]}'
    status_response = importer._session.get(status_url, headers=headers)

    if status_response.status_code != 200:
        print(f"❌ Failed to get statuses: {status_response.status_code}")
        return None

    statuses = status_response.json()
    new_status_id = None
    for status in statuses:
        if status.get("name", "").lower() == "new":
            new_status_id = status["id"]
            break

    if not new_status_id:
        print('❌ Could not find "New" status')
        return None

    payload = {
        "project": project["id"],
        "subject": subject,
        "description": description,
        "tags": tags,
        "status": new_status_id,
    }

    try:
        response = importer._session.post(f"{taiga_url}/api/v1/userstories", headers=headers, json=payload)

        if response.status_code == 201:
            story = response.json()
            ref = story.get("ref", "N/A")
            print(f"  ✅ Created: {subject} (US#{ref})")
            return story
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create migration stories for React/Vite to Jinja2")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without creating")
    parser.add_argument("--admin-only", action="store_true", help="Only create admin stories")
    parser.add_argument("--customer-only", action="store_true", help="Only create customer stories")
    args = parser.parse_args()

    print("🔄 Creating migration stories for React/Vite → Jinja2 conversion...\n")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No stories will be created\n")
    print("=" * 100)

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print(f'✅ Connected to project: {project["name"]}\n')

    all_stories = []

    # Admin screens
    if not args.customer_only:
        print("📋 Admin Screens (SPEC-005):")
        print("-" * 100)
        for screen in ADMIN_SCREENS:
            print(f'\n{screen["name"]}:')
            story = create_migration_story(importer, project["id"], screen, dry_run=args.dry_run)
            if story:
                all_stories.append(story)

    # Customer screens
    if not args.admin_only:
        print("\n\n📋 Customer Screens (SPEC-146):")
        print("-" * 100)
        for screen in CUSTOMER_SCREENS:
            print(f'\n{screen["name"]}:')
            story = create_migration_story(importer, project["id"], screen, dry_run=args.dry_run)
            if story:
                all_stories.append(story)

    print("\n" + "=" * 100)
    print(f"📊 Summary:")
    print(f"   Stories created: {len(all_stories)}")
    print(f"   Admin screens: {len(ADMIN_SCREENS) if not args.customer_only else 0}")
    print(f"   Customer screens: {len(CUSTOMER_SCREENS) if not args.admin_only else 0}")
    print("=" * 100)

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no stories were created")
        print("   Run without --dry-run to create stories")
    elif all_stories:
        print(f"\n✅ Created {len(all_stories)} migration stories")
        print('   Stories are in "New" status and ready for assignment')


if __name__ == "__main__":
    main()
