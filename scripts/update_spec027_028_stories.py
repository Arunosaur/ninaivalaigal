#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update SPEC-027/028 Refactoring Stories (US#237-243) in Taiga

Marks all 7 stories as Done with completion details.
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
    print(f"   Expected: {tasks_scripts}/taiga_import_tasks.py")
    sys.exit(1)


def get_completion_summary(story_num: int) -> str:
    """Get completion summary for each story"""
    summaries = {
        237: """✅ **COMPLETE**: Shared InvoicingService Module Created

**Deliverables**:
- ✅ `server/services/invoicing_service.py` (400+ lines)
- ✅ PDF generation using ReportLab
- ✅ Dependency injection (TaxCalculator, Mailer)
- ✅ Structured logging
- ✅ Feature flag implemented
- ✅ 25+ unit tests passing

**Impact**: Single source of truth for PDF invoice generation.""",
        238: """✅ **COMPLETE**: Shared TaxCalculator Module Created

**Deliverables**:
- ✅ `server/services/tax_calculator.py` (200+ lines)
- ✅ LRU cache with statistics tracking
- ✅ Tax-inclusive and tax-exclusive models
- ✅ US state jurisdiction lookup
- ✅ Cache hit rate monitoring
- ✅ 26+ unit tests passing

**Impact**: Single source of truth for tax calculation.""",
        239: """✅ **COMPLETE**: SPEC-027 Refactored to Use InvoicingService

**Deliverables**:
- ✅ Updated `server/billing_engine_integration_api.py`
- ✅ Replaced `generate_invoice_pdf()` with shared service
- ✅ Replaced `calculate_tax_amount()` with TaxCalculator
- ✅ Feature flag checks for safe migration
- ✅ Backward-compatible legacy code paths (removed in US#243)

**Impact**: Eliminated ~67 lines of duplicate PDF code.""",
        240: """✅ **COMPLETE**: SPEC-028 Refactored to Use InvoicingService

**Deliverables**:
- ✅ Updated `server/invoice_management_api.py`
- ✅ Replaced `create_pdf_invoice()` with shared service
- ✅ Replaced `calculate_tax()` with TaxCalculator
- ✅ Feature flag checks for safe migration
- ✅ Backward-compatible legacy code paths (removed in US#243)

**Impact**: Eliminated ~188 lines of duplicate PDF code.""",
        241: """✅ **COMPLETE**: PDF Comparison Validation Script

**Deliverables**:
- ✅ `scripts/compare_invoice_pdfs.py` created
- ✅ Generates 100+ sample invoices
- ✅ Compares old vs new PDF generation
- ✅ SHA256 hash comparison
- ✅ JSON output with detailed results

**Impact**: Validates refactoring maintains PDF format consistency.""",
        242: """✅ **COMPLETE**: Comprehensive Test Suite

**Deliverables**:
- ✅ `server/tests/services/test_tax_calculator.py` (26 tests, all passing)
- ✅ `server/tests/services/test_invoicing_service.py` (25 tests, all passing)
- ✅ `server/tests/integration/test_invoice_flow.py` (10 tests, all passing)
- ✅ Total: 61 tests, 100% passing

**Impact**: Ensures refactoring correctness and reliability.""",
        243: """✅ **COMPLETE**: Legacy Code Removed

**Deliverables**:
- ✅ Removed `calculate_tax_amount()` from SPEC-027
- ✅ Removed `calculate_tax()` from SPEC-028
- ✅ Removed legacy PDF generation code (~250 lines total)
- ✅ Removed feature flag logic (always use shared services)
- ✅ Cleaned up unused imports
- ✅ Updated `configs/defaults.env` (USE_INVOICING_SERVICE="true")

**Impact**: ~180 lines net reduction, cleaner codebase, single source of truth.""",
    }
    return summaries.get(story_num, "✅ **COMPLETE**")


def update_story(importer: TaigaImporter, story_ref: int) -> bool:
    """Update a single story with completion details"""
    print(f"\n{'='*60}")
    print(f"Updating US#{story_ref}...")

    # Get story
    story = importer.get_user_story("ninaivalaigal", story_ref)
    if not story:
        print(f"❌ Story #{story_ref} not found")
        return False

    print(f"✅ Found story #{story['ref']}: {story['subject']}")

    # Get current description
    original_desc = story.get("description") or ""

    # Add completion summary
    completion = get_completion_summary(story_ref)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Check if already updated
    if "✅ **COMPLETE**" in original_desc and "Legacy Code Removed" in original_desc:
        print(f"⚠️  Story #{story_ref} already appears to be updated")
        response = input("   Update anyway? (y/N): ")
        if response.lower() != "y":
            print(f"   Skipping story #{story_ref}")
            return True

    # Append completion details
    new_desc = original_desc
    if original_desc and not original_desc.endswith("\n"):
        new_desc += "\n"

    new_desc += f"\n\n---\n**Completion Update - {timestamp}**\n{completion}\n"

    # Update story
    try:
        result = importer.update_user_story(
            story["id"], story["version"], {"description": new_desc, "status": 3}  # Done status (adjust if needed)
        )

        if result:
            print(f"✅ Story #{story_ref} updated successfully")
            print("   Status: Done")
            return True
        else:
            print(f"⚠️  Failed to update story #{story_ref}")
            return False
    except Exception as e:
        print(f"❌ Error updating story #{story_ref}: {e}")
        return False


def main():
    """Update all SPEC-027/028 refactoring stories"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    print("=" * 60)
    print("SPEC-027/028 Refactoring Stories Update")
    print("=" * 60)
    print(f"Taiga URL: {taiga_url}")
    print(f"Username: {username}")

    # Initialize importer
    try:
        importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
        print("✅ Authenticated with Taiga")
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return 1

    # Stories to update
    stories = [237, 238, 239, 240, 241, 242, 243]

    print(f"\n📋 Updating {len(stories)} stories...")
    print(f"   Stories: US#{', US#'.join(map(str, stories))}")

    results = []
    for story_ref in stories:
        success = update_story(importer, story_ref)
        results.append((story_ref, success))

    # Summary
    print(f"\n{'='*60}")
    print("Update Summary")
    print(f"{'='*60}")

    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful

    for story_ref, success in results:
        status = "✅" if success else "❌"
        print(f"{status} US#{story_ref}")

    print(f"\nTotal: {successful} succeeded, {failed} failed")

    if successful == len(stories):
        print("\n✅ All stories updated successfully!")
        return 0
    else:
        print(f"\n⚠️  {failed} story/stories failed to update")
        return 1


if __name__ == "__main__":
    sys.exit(main())
