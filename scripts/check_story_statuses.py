#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Check status of updated stories and whether Done stories should be re-opened"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))
import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def get_all_updated_stories(importer, project_id):
    """Get all stories that were updated (have architecture notes or deprecation notices)."""
    headers = {"Authorization": f"Bearer {importer._auth_token}"}
    url = f"{taiga_url}/api/v1/userstories"

    all_stories = []
    page = 1
    page_size = 100

    while True:
        params = {"project": project_id, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            break

        stories = response.json()
        if not stories:
            break

        all_stories.extend(stories)

        if len(stories) < page_size:
            break

        page += 1

    # Filter to updated stories
    updated_stories = []
    for story in all_stories:
        description = story.get("description", "")
        if "ARCHITECTURE UPDATE (2025-11-02)" in description or "SPEC DEPRECATED (2025-11-02)" in description:
            updated_stories.append(story)

    return updated_stories


def analyze_story_for_reopening(story):
    """Analyze if a Done story should be reopened based on content."""
    status = story.get("status_extra_info", {}).get("name", "Unknown")
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()

    # Stories that might need work
    needs_work_keywords = [
        "next.js",
        "nextjs",
        "react",
        "frontend integration",
        "update frontend",
        "frontend auth",
        "frontend migration",
        "nextauth",
        "vercel",
        "customer app",
        "admin app",
    ]

    # Check if story mentions Next.js/React and is Done
    if status == "Done":
        has_nextjs_refs = any(kw in subject or kw in description for kw in needs_work_keywords)
        has_deprecation = "SPEC DEPRECATED" in story.get("description", "")
        has_architecture_note = "ARCHITECTURE UPDATE" in story.get("description", "")

        # If it's a deprecated SPEC story, it's informational only
        if has_deprecation:
            return False, "deprecated_spec", "Informational only - SPEC is deprecated"

        # If it has Next.js references and is Done, might need reopening
        if has_nextjs_refs and has_architecture_note:
            return True, "needs_migration", "References Next.js/React - may need FastAPI templating work"

        # If it's an implementation story that might need updates
        if "frontend" in subject or "frontend" in description:
            return True, "needs_review", "Frontend-related - may need architecture alignment review"

    return False, None, None


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print("🔍 Analyzing updated stories for reopening needs...\n")

    updated_stories = get_all_updated_stories(importer, project["id"])
    print(f"📊 Found {len(updated_stories)} stories with architecture updates\n")

    # Group by status
    by_status = {}
    needs_reopening = []

    for story in updated_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(story)

        # Check if needs reopening
        should_reopen, reason, explanation = analyze_story_for_reopening(story)
        if should_reopen:
            needs_reopening.append((story, reason, explanation))

    # Print summary by status
    print("=" * 100)
    print("📊 Stories by Status:")
    print("=" * 100)
    for status in sorted(by_status.keys()):
        stories = by_status[status]
        print(f"\n{status}: {len(stories)} stories")
        print("-" * 100)

        for story in stories[:5]:  # Show first 5
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            print(f"  US#{ref}: {subject[:70]}...")

        if len(stories) > 5:
            print(f"  ... and {len(stories) - 5} more")

    # Print stories that might need reopening
    print("\n" + "=" * 100)
    print("⚠️  Done Stories That May Need Reopening:")
    print("=" * 100)

    if not needs_reopening:
        print("\n✅ No Done stories identified for reopening.")
        print("   All Done stories are either:")
        print("   - Deprecated SPEC stories (informational only)")
        print("   - Already aligned with FastAPI + Jinja2")
        print("   - Backend-only (no frontend changes needed)")
    else:
        print(f"\nFound {len(needs_reopening)} Done stories that may need reopening:\n")

        for story, reason, explanation in needs_reopening:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            status = story.get("status_extra_info", {}).get("name", "Unknown")

            print(f"US#{ref}: {subject}")
            print(f"   Status: {status}")
            print(f"   Reason: {reason}")
            print(f"   Explanation: {explanation}")

            # Check if story has enough info
            description = story.get("description", "")
            has_architecture_note = "ARCHITECTURE UPDATE (2025-11-02)" in description
            has_deprecation = "SPEC DEPRECATED (2025-11-02)" in description
            has_references = (
                "docs/FRONTEND_ARCHITECTURE_DECISION.md" in description
                or "docs/ADMIN_UI_FASTAPI_ANALYSIS.md" in description
            )

            if has_architecture_note or has_deprecation:
                print(f"   ✅ Has architecture note/deprecation notice")
            if has_references:
                print(f"   ✅ Has documentation references")
            if not (has_architecture_note or has_deprecation):
                print(f"   ⚠️  Missing architecture note")

            print()

    # Summary
    print("=" * 100)
    print("📊 Summary:")
    print(f"   Total updated stories: {len(updated_stories)}")
    print(f'   Done stories: {len(by_status.get("Done", []))}')
    print(f"   Stories that may need reopening: {len(needs_reopening)}")
    print("=" * 100)

    # Recommendations
    print("\n💡 Recommendations:")
    if needs_reopening:
        print("\n1. Review Done stories listed above:")
        print("   - Check if they reference Next.js/React implementation")
        print("   - Determine if work is needed to align with FastAPI + Jinja2")
        print('   - If work needed, consider reopening to "New" or "Ready" status')
        print("\n2. For stories with architecture notes:")
        print("   - Developers have enough info to start work")
        print("   - Architecture notes point to correct documentation")
        print("   - No status change needed unless work is actually required")
        print("\n3. For deprecated SPEC stories:")
        print("   - Keep as Done (informational/historical)")
        print("   - No reopening needed")
    else:
        print("\n✅ All Done stories are properly categorized:")
        print("   - Deprecated SPEC stories are informational only")
        print("   - Active stories have architecture notes for future work")
        print("   - No reopening needed at this time")


if __name__ == "__main__":
    main()
