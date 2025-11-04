#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#409 and US#410 in Taiga with completion details
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
    print(f"   Expected location: {os.path.join(tasks_scripts, 'taiga_import_tasks.py')}")
    sys.exit(1)


def update_stories():
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")
    project_slug = "ninaivalaigal"

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    # Get auth token (this authenticates)
    try:
        auth_token = importer._get_auth_token()
        print("✅ Authenticated with Taiga")
    except Exception as e:
        print(f"❌ Failed to authenticate with Taiga: {e}")
        sys.exit(1)

    completion_details = """
✅ **Completion Summary - {{timestamp}}**

**US#409: Performance Benchmarking Enhancement (SPEC-069)**
- ✅ Database schema for benchmark tracking (runs, results, comparisons, trends)
- ✅ Benchmark storage service with regression detection
- ✅ 6 new API endpoints for benchmark management:
  * POST /performance/benchmarks/run - Create benchmark run
  * POST /performance/benchmarks/run/{run_id}/result - Record result
  * POST /performance/benchmarks/run/{run_id}/complete - Complete run
  * GET /performance/benchmarks/history - Historical results
  * GET /performance/benchmarks/compare/{run_id} - Compare with baseline
  * GET /performance/benchmarks/regressions - Get recent regressions
- ✅ Features: historical tracking, automatic regression detection, percentile tracking,
  git commit SHA tracking for CI runs, multi-metric support
- ✅ Test suite for benchmark_storage.py created

**US#410: Test Coverage Standardization (SPEC-052)**
- ✅ Enhanced pytest.ini with comprehensive test discovery and marker configuration
- ✅ Enhanced .coveragerc with detailed exclusion patterns and reporting settings
- ✅ Created centralized threshold constants file (.coverage-thresholds.env)
- ✅ Added comprehensive TEST_COVERAGE_STANDARDS.md documentation
- ✅ Standardized coverage thresholds:
  * Unit: 90%
  * Integration: 80%
  * Functional: 70%
  * Overall: 85%
- ✅ Added 7 standardized test markers: unit, integration, functional, performance, slow, security, chaos

**Code Quality Fixes:**
- ✅ Fixed pre-commit hook: Replaced unsupported 'typescript' type with file pattern
- ✅ Fixed test coverage check: Added support for server/tests/ directory structure
- ✅ Fixed bandit issues: Replaced silent exception handlers with proper logging
- ✅ All pre-commit hooks passing

**Git Commit:** f532e85b
**Status:** Ready for production deployment after staging validation
"""

    stories = {
        409: "US#409: Performance Benchmarking Enhancement (SPEC-069)",
        410: "US#410: Comprehensive Test Coverage Standardization (SPEC-052)",
    }

    print("\n📋 Updating 2 stories...")
    print(f"   Stories: {', '.join([f'US#{s}' for s in stories.keys()])}\n")

    for story_ref, story_title in stories.items():
        print("=" * 60)
        print(f"Updating US#{story_ref}...")
        story = importer.get_user_story(project_slug, story_ref)

        if story:
            original_desc = story.get("description", "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            completion = completion_details.replace("{{timestamp}}", timestamp)

            # Append completion details
            new_desc = original_desc
            if original_desc and not original_desc.endswith("\n"):
                new_desc += "\n"

            final_details = f"\n\n---\n{completion}\n"
            if final_details.strip() not in new_desc.strip():
                new_desc += final_details

            # Update story description
            try:
                result = importer.append_to_story_description(project_slug, story_ref, completion)
                if result:
                    print(f"✅ Story #{story_ref} description updated successfully")

                    # Try to update status to Done if not already
                    if story.get("status_extra_info", {}).get("name", "").lower() != "done":
                        # Get status ID from story's status field (it's already a number)
                        # Or just update description and leave status as-is
                        print("   Note: Status update requires project status lookup")
                else:
                    print(f"⚠️  Failed to update story #{story_ref}")
            except Exception as e:
                print(f"❌ Error updating story #{story_ref}: {e}")
        else:
            print(f"❌ Story #{story_ref} not found")

    print("\n" + "=" * 60)
    print("✅ Story updates complete!")
    print("=" * 60)


if __name__ == "__main__":
    update_stories()
