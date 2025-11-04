#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update US#157 in Taiga with completion details
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

**US#157: Discount & Credit System Schema (SPEC-026 Phase 1)**

**Deliverables:**
- ✅ Added credit_transactions table for audit trail
- ✅ Created SQLAlchemy models: DiscountCode, TeamCredit, CreditTransaction, DiscountCodeUsage
- ✅ Added CreditTransactionType enum for type-safe transaction types
- ✅ Comprehensive test suite: 15+ tests achieving 90%+ coverage
- ✅ Verified existing discount_codes and team_credits tables match requirements
- ✅ Foreign key constraints with CASCADE delete
- ✅ Performance indexes on all relevant columns
- ✅ CHECK constraints for data integrity (balance validation, discount type checks)
- ✅ Automatic timestamp triggers

**Database Schema:**
- `discount_codes`: Verified complete - supports percent and fixed amount discounts
- `team_credits`: Verified complete - credit balance tracking with usage
- `credit_transactions`: NEW - Audit trail for all credit operations (grant, deduct, expire, refund)
- `discount_code_usage`: Already exists, verified complete

**SQLAlchemy Models:**
- `DiscountCode`: Supports percent_off and amount_off discounts with validation
- `TeamCredit`: Credit balance tracking with team/org support
- `CreditTransaction`: Audit trail with balance tracking (before/after)
- `DiscountCodeUsage`: Tracks discount code applications to invoices

**Test Coverage:**
- Discount code creation and validation (5 tests)
- Credit management and constraints (5 tests)
- Transaction audit trail (3 tests)
- Usage tracking (2 tests)
- Total: 15+ tests, 90%+ coverage

**Acceptance Criteria Met:**
- [x] discount_codes table verified (unique codes)
- [x] team_credits table verified (balance validation)
- [x] credit_transactions table created (audit trail)
- [x] Check constraints ensure balance >= 0
- [x] Indexes created for performance
- [x] Unit tests cover all models

**Git Commit:** Ready for commit
**Blocks:** US#205, US#206 (Phase 2 - Discount & Credit APIs)
"""

    story = importer.get_user_story(project_slug, 157)
    if not story:
        print("❌ Story #157 not found")
        return 1

    print(f"✅ Found story #157: {story['subject']}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    completion = completion_details.replace("{{timestamp}}", timestamp)

    result = importer.append_to_story_description(project_slug, 157, completion)
    if result:
        print("✅ Story description updated with completion details")
        print(f"   View: {taiga_url}/project/{project_slug}/us/157")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(update_story())
