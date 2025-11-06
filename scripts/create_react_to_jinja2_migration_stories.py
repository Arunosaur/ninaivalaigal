#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for migrating React/Vite screens to Jinja2 templates.

Identifies all React/Vite implementations and creates migration stories.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import subprocess

from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")

# Admin screens (SPEC-005)
ADMIN_SCREENS = [
    {
        "name": "Admin Login",
        "file": "apps/admin-console/src/pages/Login.tsx",
        "spec": "005",
        "priority": "P0",
        "effort": "2-3 hours",
        "description": "Convert React Login page to Jinja2 template with FastAPI JWT auth integration",
    },
    {
        "name": "Analytics Dashboard",
        "file": "apps/admin-console/src/pages/Analytics.tsx",
        "spec": "005",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Analytics dashboard to Jinja2 template with Chart.js for visualizations",
    },
    {
        "name": "User Management",
        "file": "apps/admin-console/src/pages/Users.tsx",
        "spec": "005",
        "priority": "P0",
        "effort": "4-6 hours",
        "description": "Convert React User Management page to Jinja2 template with Alpine.js for search/filter and HTMX for CRUD operations",
    },
    {
        "name": "Team Management",
        "file": "apps/admin-console/src/pages/Teams.tsx",
        "spec": "005",
        "priority": "P0",
        "effort": "4-6 hours",
        "description": "Convert React Team Management page to Jinja2 template with HTMX for inline edits and Alpine.js for interactivity",
    },
]

# Customer screens (SPEC-146)
CUSTOMER_SCREENS = [
    {
        "name": "Customer Login",
        "file": "apps/customer/src/pages/Login.tsx",
        "spec": "146",
        "priority": "P0",
        "effort": "2-3 hours",
        "description": "Convert React Login page to Jinja2 template with FastAPI JWT auth",
    },
    {
        "name": "Customer Signup",
        "file": "apps/customer/src/pages/Signup.tsx",
        "spec": "146",
        "priority": "P0",
        "effort": "3-4 hours",
        "description": "Convert React Signup page to Jinja2 template with form validation",
    },
    {
        "name": "Dashboard",
        "file": "apps/customer/src/pages/Dashboard.tsx",
        "spec": "146",
        "priority": "P0",
        "effort": "4-6 hours",
        "description": "Convert React Dashboard to Jinja2 template with real-time data from API",
    },
    {
        "name": "Memory Browser",
        "file": "apps/customer/src/pages/MemoryBrowser.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "6-8 hours",
        "description": "Convert React Memory Browser to Jinja2 template (may need React micro-widget for complex interactions)",
    },
    {
        "name": "Team Dashboard",
        "file": "apps/customer/src/pages/TeamDashboard.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "4-6 hours",
        "description": "Convert React Team Dashboard to Jinja2 template",
    },
    {
        "name": "Team Billing",
        "file": "apps/customer/src/pages/TeamBilling.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "4-6 hours",
        "description": "Convert React Team Billing page to Jinja2 template with Stripe integration",
    },
    {
        "name": "Team Invoice List",
        "file": "apps/customer/src/pages/TeamInvoiceList.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Invoice List to Jinja2 template with pagination",
    },
    {
        "name": "Team Payment Method",
        "file": "apps/customer/src/pages/TeamPaymentMethod.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Payment Method page to Jinja2 template",
    },
    {
        "name": "Team Usage",
        "file": "apps/customer/src/pages/TeamUsage.tsx",
        "spec": "146",
        "priority": "P2",
        "effort": "4-6 hours",
        "description": "Convert React Team Usage analytics to Jinja2 template with Chart.js",
    },
    {
        "name": "Settings",
        "file": "apps/customer/src/pages/Settings.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Settings page to Jinja2 template with Alpine.js for form interactions",
    },
    {
        "name": "Team Create",
        "file": "apps/customer/src/pages/TeamCreate.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Team Create page to Jinja2 template",
    },
    {
        "name": "Team Invite",
        "file": "apps/customer/src/pages/TeamInvite.tsx",
        "spec": "146",
        "priority": "P1",
        "effort": "3-4 hours",
        "description": "Convert React Team Invite page to Jinja2 template",
    },
    {
        "name": "Team Upgrade",
        "file": "apps/customer/src/pages/TeamUpgrade.tsx",
        "spec": "146",
        "priority": "P2",
        "effort": "3-4 hours",
        "description": "Convert React Team Upgrade page to Jinja2 template",
    },
    {
        "name": "Discount Non-Profit",
        "file": "apps/customer/src/pages/DiscountNonProfit.tsx",
        "spec": "146",
        "priority": "P2",
        "effort": "3-4 hours",
        "description": "Convert React Discount/Non-Profit page to Jinja2 template",
    },
    {
        "name": "Injection Analytics",
        "file": "apps/customer/src/pages/InjectionAnalytics.tsx",
        "spec": "146",
        "priority": "P2",
        "effort": "4-6 hours",
        "description": "Convert React Injection Analytics to Jinja2 template (may need Chart.js widget)",
    },
]


def create_migration_story(importer, project, screen_data, dry_run=False):
    """Create a migration story for a React/Vite screen."""
    subject = f"Migrate {screen_data['name']} from React/Vite to Jinja2"

    spec_ref = f"SPEC-{screen_data['spec']}"
    is_admin = screen_data["spec"] == "005"

    description = f"""## Objective

Convert {screen_data['name']} from React/Vite implementation to FastAPI + Jinja2 templates.

## Current Implementation

**Location:** `{screen_data['file']}`
**Technology:** React + TypeScript + Vite
**Status:** Active React/Vite implementation

## Target Implementation

**Technology:** FastAPI + Jinja2 templates
- **Server-side rendering:** Jinja2 templates
- **Client interactivity:** Alpine.js or HTMX
- **Styling:** TailwindCSS (reuse existing classes from React implementation)
- **Optional:** React micro-widget (Vite-built) only if complex interactions needed

## Migration Steps

1. **Create Jinja2 Template**
   - Create template file: `templates/{'admin' if is_admin else 'customer'}/{screen_data['name'].lower().replace(' ', '_')}.html`
   - Base on existing React component structure
   - Reuse TailwindCSS classes from React implementation
   - Extract reusable components to Jinja2 macros/partials

2. **Create FastAPI Route**
   - Add route in appropriate router (`server/routers/admin.py` or customer router)
   - Connect to existing API endpoints
   - Return Jinja2 template response with data

3. **Add Interactivity**
   - Use Alpine.js for client-side state management
   - Use HTMX for server-side interactions (forms, pagination, inline edits)
   - Keep React widget only if truly complex visualization needed

4. **Test**
   - Verify all functionality from React version works
   - Test with real API data
   - Ensure visual parity (same TailwindCSS classes)
   - Test accessibility (ARIA labels, keyboard navigation)

5. **Archive React Implementation**
   - Move React file to `/legacy/apps/` directory
   - Update documentation
   - Remove from active codebase when migration verified

## Acceptance Criteria

- [ ] Jinja2 template created and functional
- [ ] FastAPI route serves template correctly
- [ ] All functionality from React version works
- [ ] Visual parity maintained (same TailwindCSS classes)
- [ ] Interactivity works (Alpine.js/HTMX)
- [ ] API integration verified (real data, not mocks)
- [ ] React file archived to `/legacy/apps/`
- [ ] Documentation updated

## References

- Architecture Decision: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
- Admin UI: `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
- Customer UI: `specs/146-customer-ui-fastapi-templates/README.md`
- {spec_ref}: `specs/{screen_data['spec']}-{'admin-dashboard' if is_admin else 'customer-ui-fastapi-templates'}/{'spec.md' if is_admin else 'README.md'}`

## Estimated Effort

{screen_data['effort']}

## Priority

{screen_data['priority']}

## Notes

- Reuse existing TailwindCSS classes from React implementation
- Reference React component for UI structure and styling
- Test thoroughly before archiving React version
"""

    tags = [f"spec-{screen_data['spec']}", "migration", "react-to-jinja2", "fastapi", "jinja2", "templates"]

    if is_admin:
        tags.append("admin")
    else:
        tags.append("customer")

    if dry_run:
        print(f"  [DRY RUN] Would create: {subject}")
        print(f"  Spec: {spec_ref}")
        print(f"  Tags: {', '.join(tags)}")
        print(f"  Priority: {screen_data['priority']}")
        print(f"  Effort: {screen_data['effort']}")
        return None

    # Get status IDs
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
            story = create_migration_story(importer, project, screen, dry_run=args.dry_run)
            if story:
                all_stories.append(story)

    # Customer screens
    if not args.admin_only:
        print("\n\n📋 Customer Screens (SPEC-146):")
        print("-" * 100)
        for screen in CUSTOMER_SCREENS:
            print(f'\n{screen["name"]}:')
            story = create_migration_story(importer, project, screen, dry_run=args.dry_run)
            if story:
                all_stories.append(story)

    print("\n" + "=" * 100)
    print(f"📊 Summary:")
    print(f"   Stories created: {len(all_stories)}")
    print(f"   Admin screens: {len(ADMIN_SCREENS) if not args.customer_only else 0}")
    print(f"   Customer screens: {len(CUSTOMER_SCREENS) if not args.admin_only else 0}")
    print(f"   Total screens: {len(ADMIN_SCREENS) + len(CUSTOMER_SCREENS)}")
    print("=" * 100)

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no stories were created")
        print("   Run without --dry-run to create stories")
    elif all_stories:
        print(f"\n✅ Created {len(all_stories)} migration stories")
        print('   Stories are in "New" status and ready for assignment')
        print(f"\n📋 Next Steps:")
        print("   1. Review stories in Taiga")
        print("   2. Assign to developers")
        print("   3. Prioritize P0 stories first")
        print("   4. Start migration work")


if __name__ == "__main__":
    main()
