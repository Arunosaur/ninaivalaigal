#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Rate Limiting Story in Taiga with completion details and mark as Done
"""

import os
import sys
from datetime import datetime

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update rate limiting story in Taiga"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)

    # Find rate limiting story (try multiple search terms)
    story = None
    story_refs = ["Rate Limiting", "Rate Limit", "313"]  # US#313 or similar

    project = importer.get_project("ninaivalaigal")
    if not project:
        print("❌ Project 'ninaivalaigal' not found")
        return 1

    # Search for story
    url = f"{importer.base_url}/userstories"
    params = {"project": project["id"]}
    headers = importer._get_headers()

    response = importer._session.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to get stories: {response.status_code}")
        return 1

    stories = response.json()
    for s in stories:
        subject_lower = s.get("subject", "").lower()
        if any(term.lower() in subject_lower for term in ["rate limit", "rate limiting", "p0 security"]):
            story = s
            break

    if not story:
        print("⚠️  Rate limiting story not found. Summary:")
        summary = """
✅ **Rate Limiting Implementation Completed**

**Status**: Fully integrated and active

**Key Features**:
- RBAC-aware rate limiting with role-based limits
- Endpoint-specific rate limits (auth, memory, contexts, etc.)
- Sliding window counter algorithm
- Token bucket algorithm with burst allowance
- Concurrent request tracking
- Automatic counter cleanup
- Standard rate limit headers (X-RateLimit-*)

**Files Modified**:
- `server/security_integration.py` - Enhanced rate limiting integration
- `server/tests/security/test_rate_limiting.py` - Comprehensive test suite (30+ tests)

**Integration**:
- Rate limiting is active through `SecurityManager.configure_app_security()`
- Graceful fallback to Redis rate limiter if enhanced limiter unavailable
- Integrated with FastAPI middleware stack

**Report**: `governance/reports/RATE_LIMITING_COMPLETION.md`
        """
        print(summary)
        return 0

    story_id = story["id"]
    story_ref = story.get("ref", "N/A")
    print(f"✅ Found story #{story_ref}: {story['subject']}")

    # Get current description
    original_description = story.get("description") or ""

    # Completion summary
    summary = """✅ **Rate Limiting Implementation Completed**

**Status**: Fully integrated and active

**Key Features**:
- RBAC-aware rate limiting with role-based limits
- Endpoint-specific rate limits (auth, memory, contexts, etc.)
- Sliding window counter algorithm
- Token bucket algorithm with burst allowance
- Concurrent request tracking
- Automatic counter cleanup
- Standard rate limit headers (X-RateLimit-*)

**Files Modified**:
- `server/security_integration.py` - Enhanced rate limiting integration
- `server/tests/security/test_rate_limiting.py` - Comprehensive test suite (30+ tests)

**Integration**:
- Rate limiting is active through `SecurityManager.configure_app_security()`
- Graceful fallback to Redis rate limiter if enhanced limiter unavailable
- Integrated with FastAPI middleware stack

**Test Coverage**: 30+ comprehensive tests covering all functionality.

**Report**: `governance/reports/RATE_LIMITING_COMPLETION.md`"""

    # Append completion details
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n---\n**Completion Update {stamp}**\n{summary}\n"

    if summary.strip() in original_description:
        print("✅ Update already present in description")
    else:
        new_desc = original_description + entry
        result = importer.update_user_story(story_id, story["version"], {"description": new_desc})

        if result:
            print(f"✅ Description updated for story #{story_ref}")

            # Try to get "Done" status
            status_url = f"{importer.base_url}/userstory-statuses?project={project['id']}"
            status_response = importer._session.get(status_url, headers=headers)
            if status_response.status_code == 200:
                statuses = status_response.json()
                done_status = None
                for status in statuses:
                    name_lower = status.get("name", "").lower()
                    if "done" in name_lower or "complete" in name_lower or "closed" in name_lower:
                        done_status = status["id"]
                        break

                if done_status:
                    # Update status to Done
                    result = importer.update_story_status(story_id, done_status, result["version"])
                    if result:
                        print(f"✅ Story #{story_ref} marked as Done")
                    else:
                        print(f"⚠️  Failed to update status (description updated)")
                else:
                    print(f"⚠️  'Done' status not found (description updated)")
        else:
            print(f"⚠️  Failed to update description")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
