#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Analyze Done stories to see if they need reopening and if they have enough info"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

import requests
from taiga_import_tasks import TaigaImporter

taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
username = os.getenv("TAIGA_USERNAME", "admin")
password = os.getenv("TAIGA_PASSWORD", "admin123")


def get_done_stories_with_ui_refs(importer, project_id):
    """Get Done stories that mention UI technologies."""
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

    # Filter to Done stories with UI references
    done_ui_stories = []
    for story in all_stories:
        status = story.get("status_extra_info", {}).get("name", "Unknown")
        if status != "Done":
            continue

        subject = story.get("subject", "").lower()
        description = story.get("description", "").lower()

        ui_keywords = [
            "next.js",
            "nextjs",
            "react",
            "frontend",
            "spa",
            "vercel",
            "admin ui",
            "admin dashboard",
            "customer ui",
            "customer frontend",
            "frontend-nextjs",
            "frontend-shared",
            "turborepo",
            "jinja2",
            "template",
            "templating",
            "spec-005",
            "spec-102",
            "spec-103",
            "spec-113",
            "spec-114",
            "spec-115",
            "spec-116",
            "spec-121",
            "spec-122",
            "spec-123",
            "spec-124",
            "us-98",
            "us-99",
            "us-100",
            "us-101",
            "us-102",
            "us-89",
            "profile page",
            "settings page",
            "auth integration",
            "realtime",
            "websocket",
            "sse",
            "nextauth",
        ]

        combined = f"{subject} {description}"
        if any(kw in combined for kw in ui_keywords):
            done_ui_stories.append(story)

    return done_ui_stories


def analyze_story_info(story):
    """Analyze if story has enough information for developers."""
    description = story.get("description", "")

    has_architecture_note = "ARCHITECTURE UPDATE (2025-11-02)" in description
    has_deprecation = "SPEC DEPRECATED (2025-11-02)" in description
    has_docs_reference = (
        "docs/FRONTEND_ARCHITECTURE_DECISION.md" in description or "docs/ADMIN_UI_FASTAPI_ANALYSIS.md" in description
    )
    has_uniformity_plan = "docs/SPEC_TAIGA_UNIFORMITY_PLAN.md" in description

    # Check for actionable information
    has_stack_info = "FastAPI + Jinja2" in description
    has_tech_details = any(x in description for x in ["Alpine.js", "HTMX", "TailwindCSS", "Vite-built"])
    has_replacement_spec = "Replacement SPEC" in description or "Replacement SPECs" in description

    info_score = 0
    if has_architecture_note or has_deprecation:
        info_score += 3
    if has_docs_reference:
        info_score += 2
    if has_uniformity_plan:
        info_score += 1
    if has_stack_info:
        info_score += 2
    if has_tech_details:
        info_score += 1
    if has_replacement_spec:
        info_score += 1

    return {
        "has_architecture_note": has_architecture_note,
        "has_deprecation": has_deprecation,
        "has_docs_reference": has_docs_reference,
        "has_uniformity_plan": has_uniformity_plan,
        "has_stack_info": has_stack_info,
        "has_tech_details": has_tech_details,
        "has_replacement_spec": has_replacement_spec,
        "info_score": info_score,
        "sufficient_info": info_score >= 5,
    }


def should_reopen(story, info_analysis):
    """Determine if story should be reopened."""
    subject = story.get("subject", "").lower()
    description = story.get("description", "").lower()

    # Deprecated SPEC stories should stay Done
    if info_analysis["has_deprecation"]:
        return False, "deprecated_spec", "Informational only - SPEC is deprecated"

    # Stories that mention Next.js/React and might need migration work
    nextjs_keywords = ["next.js", "nextjs", "react", "nextauth", "vercel", "turborepo"]
    if any(kw in subject or kw in description for kw in nextjs_keywords):
        # Check if it's a completed implementation that needs migration
        if "implement" in subject or "create" in subject or "build" in subject:
            return True, "needs_migration", "Completed Next.js/React work - may need FastAPI templating migration"

    # Stories that are implementation tasks that might need updates
    if "frontend" in subject or "frontend" in description:
        if "integration" in subject or "auth" in subject or "ui" in subject:
            return True, "needs_review", "Frontend implementation - may need architecture alignment"

    return False, None, None


def main():
    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project not found")
        return

    print("🔍 Analyzing Done stories for reopening needs and information sufficiency...\n")

    done_stories = get_done_stories_with_ui_refs(importer, project["id"])
    print(f"📊 Found {len(done_stories)} Done stories with UI references\n")

    if not done_stories:
        print("✅ No Done stories with UI references found.")
        return

    print("=" * 100)
    print("📋 Analysis Results:")
    print("=" * 100)

    stories_to_reopen = []
    stories_with_sufficient_info = []
    stories_needing_info = []
    deprecated_spec_stories = []

    for story in done_stories:
        ref = story.get("ref")
        subject = story.get("subject", "N/A")

        info_analysis = analyze_story_info(story)
        should_reopen_flag, reason, explanation = should_reopen(story, info_analysis)

        if info_analysis["has_deprecation"]:
            deprecated_spec_stories.append((story, info_analysis))
        elif should_reopen_flag:
            stories_to_reopen.append((story, reason, explanation, info_analysis))
        elif info_analysis["sufficient_info"]:
            stories_with_sufficient_info.append((story, info_analysis))
        else:
            stories_needing_info.append((story, info_analysis))

    # Print deprecated SPEC stories
    print(f"\n🚫 Deprecated SPEC Stories ({len(deprecated_spec_stories)}):")
    print("   These should stay Done - they are informational/historical")
    print("-" * 100)
    for story, info in deprecated_spec_stories[:5]:
        ref = story.get("ref")
        subject = story.get("subject", "N/A")
        print(f"  US#{ref}: {subject[:70]}...")
    if len(deprecated_spec_stories) > 5:
        print(f"  ... and {len(deprecated_spec_stories) - 5} more")

    # Print stories that might need reopening
    print(f"\n⚠️  Stories That May Need Reopening ({len(stories_to_reopen)}):")
    print("-" * 100)
    if stories_to_reopen:
        for story, reason, explanation, info in stories_to_reopen:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            print(f"\nUS#{ref}: {subject}")
            print(f"   Reason: {reason}")
            print(f"   Explanation: {explanation}")
            print(f'   Info Score: {info["info_score"]}/10')
            print(f'   Has Architecture Note: {"✅" if info["has_architecture_note"] else "❌"}')
            print(f'   Has Docs Reference: {"✅" if info["has_docs_reference"] else "❌"}')
            print(f'   Sufficient Info: {"✅ Yes" if info["sufficient_info"] else "⚠️  Partial"}')
    else:
        print("   ✅ None identified")

    # Print stories with sufficient info
    print(f"\n✅ Stories With Sufficient Information ({len(stories_with_sufficient_info)}):")
    print("   These have enough info for developers - no reopening needed unless work is required")
    print("-" * 100)
    for story, info in stories_with_sufficient_info[:5]:
        ref = story.get("ref")
        subject = story.get("subject", "N/A")
        print(f'  US#{ref}: {subject[:70]}... (Score: {info["info_score"]}/10)')
    if len(stories_with_sufficient_info) > 5:
        print(f"  ... and {len(stories_with_sufficient_info) - 5} more")

    # Print stories needing more info
    if stories_needing_info:
        print(f"\n⚠️  Stories Needing More Information ({len(stories_needing_info)}):")
        print("-" * 100)
        for story, info in stories_needing_info[:5]:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            print(f'  US#{ref}: {subject[:70]}... (Score: {info["info_score"]}/10)')
        if len(stories_needing_info) > 5:
            print(f"  ... and {len(stories_needing_info) - 5} more")

    # Summary
    print("\n" + "=" * 100)
    print("📊 Summary:")
    print(f"   Total Done UI stories: {len(done_stories)}")
    print(f"   Deprecated SPEC stories: {len(deprecated_spec_stories)} (stay Done)")
    print(f"   May need reopening: {len(stories_to_reopen)}")
    print(f"   Have sufficient info: {len(stories_with_sufficient_info)}")
    print(f"   Need more info: {len(stories_needing_info)}")
    print("=" * 100)

    # Recommendations
    print("\n💡 Recommendations:")
    print("\n1. Status Changes:")
    if stories_to_reopen:
        print(f'   ⚠️  Consider reopening {len(stories_to_reopen)} Done stories to "New" or "Ready" if:')
        print("      - They reference Next.js/React implementations that need migration")
        print("      - Work is actually needed to align with FastAPI + Jinja2")
        print("      - They are active implementation stories (not historical)")
        print("\n   Stories to review:")
        for story, reason, explanation, info in stories_to_reopen:
            ref = story.get("ref")
            subject = story.get("subject", "N/A")
            print(f"      - US#{ref}: {subject[:60]}...")
    else:
        print("   ✅ No Done stories need reopening at this time")

    print("\n2. Information Sufficiency:")
    if stories_with_sufficient_info:
        print(f"   ✅ {len(stories_with_sufficient_info)} stories have sufficient information")
        print("      - Architecture notes are present")
        print("      - Documentation references are included")
        print("      - Developers can pick up work from these stories")

    if stories_needing_info:
        print(f"   ⚠️  {len(stories_needing_info)} stories may need additional information")
        print("      - Consider adding more detail about FastAPI templating approach")

    print("\n3. Deprecated SPEC Stories:")
    print(f"   ✅ {len(deprecated_spec_stories)} deprecated SPEC stories should stay Done")
    print("      - They are informational/historical references only")
    print("      - No work needed - they document what was deprecated")

    print("\n4. Action Items:")
    if stories_to_reopen:
        print("   - Review each story listed above")
        print("   - Determine if actual work is needed")
        print("   - If work needed, reopen to appropriate status")
        print("   - If no work needed, keep as Done with architecture note")
    else:
        print("   - ✅ No immediate action needed")
        print("   - Stories have sufficient information for future work")
        print("   - Developers can reference architecture notes when needed")


if __name__ == "__main__":
    main()
