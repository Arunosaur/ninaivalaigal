#!/usr/bin/env python3
"""
Create Taiga user stories for multi-language test coverage improvements.

Usage:
    python3 scripts/create_multilang_test_coverage_stories.py

This script creates Taiga user stories based on test coverage analysis
for Python, TypeScript, Rust, Go, and Java codebases.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from taiga_api import create_user_story, get_or_create_epic
except ImportError:
    print("⚠️  Taiga API module not found. Creating stories JSON only.")
    print("   To create stories in Taiga, ensure taiga_api.py exists.")
    create_user_story = None
    get_or_create_epic = None


def load_stories():
    """Load stories from JSON file."""
    stories_file = project_root / "scripts" / "multilang_test_coverage_stories.json"

    if not stories_file.exists():
        print(f"❌ Stories file not found: {stories_file}")
        sys.exit(1)

    with open(stories_file, "r") as f:
        data = json.load(f)

    return data.get("stories", []), data.get("epic", {})


def create_stories_in_taiga(stories, epic_info):
    """Create stories in Taiga project."""
    if not create_user_story or not get_or_create_epic:
        print("⚠️  Taiga API not available. Skipping Taiga creation.")
        return

    # Get or create Epic
    epic_name = epic_info.get("name", "EPIC#028: Multi-Language Test Coverage Improvement")
    epic_description = epic_info.get("description", "")
    epic_tags = epic_info.get("tags", [])

    print(f"\n📋 Creating Epic: {epic_name}")
    try:
        epic = get_or_create_epic(name=epic_name, description=epic_description, tags=epic_tags)
        epic_id = epic.get("id") if isinstance(epic, dict) else epic
        print(f"✅ Epic created/found: ID {epic_id}\n")
    except Exception as e:
        print(f"⚠️  Failed to create epic: {e}")
        epic_id = None

    # Create user stories
    created_stories = []
    failed_stories = []

    print(f"📝 Creating {len(stories)} user stories...\n")

    for idx, story in enumerate(stories, 1):
        subject = story.get("subject", "")
        description = story.get("description", "")
        tags = story.get("tags", [])
        priority = story.get("priority", "Normal")
        effort = story.get("effort", 0)

        # Convert effort to story points (assuming 1 day = 2 points)
        story_points = max(1, effort // 2) if effort > 0 else 1

        print(f"[{idx}/{len(stories)}] Creating: {subject[:60]}...")

        try:
            result = create_user_story(
                subject=subject,
                description=description,
                tags=tags,
                epic_id=epic_id,
                priority=priority,
                story_points=story_points,
            )

            if result:
                story_id = result.get("id") if isinstance(result, dict) else result
                created_stories.append({"id": story_id, "subject": subject, "priority": priority})
                print(f"    ✅ Created: Story #{story_id}")
            else:
                failed_stories.append({"subject": subject, "error": "No ID returned"})
                print(f"    ⚠️  Created but no ID returned")

        except Exception as e:
            failed_stories.append({"subject": subject, "error": str(e)})
            print(f"    ❌ Failed: {e}")

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Created: {len(created_stories)} stories")
    print(f"❌ Failed: {len(failed_stories)} stories")

    if created_stories:
        print(f"\n✅ Successfully Created Stories:")
        for story in created_stories:
            print(f"   - #{story['id']}: {story['subject'][:60]}... [{story['priority']}]")

    if failed_stories:
        print(f"\n❌ Failed Stories:")
        for story in failed_stories:
            print(f"   - {story['subject'][:60]}...")
            print(f"     Error: {story['error']}")

    return created_stories, failed_stories


def main():
    """Main execution function."""
    print("🚀 Multi-Language Test Coverage Stories Creator")
    print("=" * 80)

    # Load stories
    stories, epic_info = load_stories()

    print(f"\n📋 Loaded {len(stories)} stories from JSON")
    print(f"📋 Epic: {epic_info.get('name', 'N/A')}")

    # Show stories by priority
    p0_stories = [s for s in stories if "p0-critical" in s.get("tags", [])]
    p1_stories = [s for s in stories if "p1-important" in s.get("tags", [])]
    p2_stories = [s for s in stories if "p2-medium" in s.get("tags", [])]

    print(f"\n📊 Stories by Priority:")
    print(f"   P0 (Critical): {len(p0_stories)}")
    print(f"   P1 (Important): {len(p1_stories)}")
    print(f"   P2 (Medium-term): {len(p2_stories)}")

    # Show stories by language
    languages = {}
    for story in stories:
        for tag in story.get("tags", []):
            if tag in ["python", "typescript", "rust", "go", "java"]:
                if tag not in languages:
                    languages[tag] = []
                languages[tag].append(story.get("subject", ""))

    print(f"\n🌐 Stories by Language:")
    for lang, story_list in sorted(languages.items()):
        print(f"   {lang.capitalize()}: {len(story_list)}")

    # Ask for confirmation
    print(f"\n{'='*80}")
    response = input("Create stories in Taiga? (yes/no): ").strip().lower()

    if response not in ["yes", "y"]:
        print("⏭️  Skipping Taiga creation. Stories JSON file ready for manual import.")
        print(f"   File: scripts/multilang_test_coverage_stories.json")
        return

    # Create stories
    created, failed = create_stories_in_taiga(stories, epic_info)

    # Save results
    results_file = project_root / "docs" / "spec-analysis" / "MULTILANG_TEST_COVERAGE_STORIES_CREATED.md"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        f.write("# Multi-Language Test Coverage Stories - Creation Results\n\n")
        f.write(f"**Date**: {Path(__file__).stat().st_mtime}\n\n")
        f.write(f"**Total Stories**: {len(stories)}\n")
        f.write(f"**Created**: {len(created)}\n")
        f.write(f"**Failed**: {len(failed)}\n\n")

        if created:
            f.write("## ✅ Successfully Created Stories\n\n")
            for story in created:
                f.write(f"- **#{story['id']}**: {story['subject']} [{story['priority']}]\n")

        if failed:
            f.write("\n## ❌ Failed Stories\n\n")
            for story in failed:
                f.write(f"- **{story['subject']}**: {story['error']}\n")

    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
