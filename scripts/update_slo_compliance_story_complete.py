#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Taiga Story US#141 with completion details

SLO Monitoring & Compliance Tracking
"""

import os
import sys
from datetime import datetime

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

COMPLETION_DETAILS = """
---

## ✅ **COMPLETE** - {timestamp}

**Developer**: Developer G
**Status**: ✅ COMPLETE

### Implementation Summary

Successfully implemented `/health/slo-compliance` endpoint for SLO monitoring and compliance tracking.

### Deliverables Completed

1. ✅ **SLO Compliance Endpoint** (`GET /health/slo-compliance`)
   - Availability SLO (99.9% uptime, 30-day window)
   - Response time SLO (P95 < 200ms, 24-hour window)
   - Error rate SLO (< 0.1%, 24-hour window)
   - Supports time windows: 1h, 24h, 7d (configured via query parameter)
   - Returns comprehensive compliance status

2. ✅ **Comprehensive Test Suite** (`tests/observability/test_slo_compliance_endpoint.py`)
   - 9 tests covering all scenarios
   - All tests passing in conda env nina ✅

### Key Features

**Endpoint:**
- `GET /health/slo-compliance?window={1h|24h|7d}`
- Returns SLO targets, current metrics, compliance status
- Validates window parameter
- Handles errors gracefully

**SLO Targets:**
- Availability: 99.9% (0.999) uptime
- Response Time P95: < 200ms (0.2 seconds)
- Error Rate: < 0.1% (0.001)

**Integration:**
- Uses existing `lib.observability.slo_monitoring.get_slo_status()`
- Leverages existing `SLOTracker` class
- Prometheus metrics integration
- Works with existing health endpoint infrastructure

### Acceptance Criteria Met

- ✅ `/health/slo-compliance` endpoint created
- ✅ Availability SLO tracking (99.9% uptime, 30-day window)
- ✅ Response time SLO tracking (P95 < 200ms, 24-hour window)
- ✅ Error rate SLO tracking (< 0.1%, 24-hour window)
- ✅ Time window support (1h, 24h, 7d)
- ✅ Prometheus histogram metrics (P50, P95, P99) - via existing infrastructure
- ✅ Redis-backed rolling windows - via existing SLOTracker
- ✅ Comprehensive test coverage (9 tests)
- ✅ All tests passing ✅

### Test Results

**Test Suite**: `test_slo_compliance_endpoint.py`
- ✅ 9/9 tests passing in conda env nina
- Tests cover: endpoint existence, window support, healthy/degraded status, partial violations, error handling, default window, response structure

### Files Created/Modified

**Modified:**
- `services/core-api/routers/health.py` - Added `/health/slo-compliance` endpoint and `SLOComplianceResponse` model

**Created:**
- `services/core-api/tests/observability/test_slo_compliance_endpoint.py` - Comprehensive test suite (9 tests)

### Usage Example

```bash
# Get SLO compliance status
curl http://localhost:8000/health/slo-compliance?window=24h
```

---

**Documentation**: See `services/core-api/SLO_COMPLIANCE_ENDPOINT_COMPLETE.md` for full details.

**Status**: ✅ **COMPLETE** - All tests passing, ready for production use
"""


def authenticate():
    """Authenticate with Taiga."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    url = f"{API_ENDPOINT}/userstories/by_ref"
    params = {"project": project_id, "ref": story_ref}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    return None


def get_statuses(auth_token, project_id):
    """Get all statuses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                name = status.get("name", "").lower()
                statuses[name] = status.get("id")
            return statuses
        return {}
    except Exception:
        return {}


def update_story(auth_token, story_id, story_version, description, status_id=None):
    """Update story description and optionally status."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    data = {
        "version": story_version,
        "description": description,
    }

    if status_id:
        data["status"] = status_id

    try:
        response = requests.patch(url, headers=headers, json=data)
        return response.status_code in [200, 204], response.text
    except Exception as e:
        return False, str(e)


def main():
    """Update US#141 with completion details."""
    print("=" * 80)
    print("UPDATING SLO COMPLIANCE STORY (US#141)")
    print("=" * 80)
    print()

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated with Taiga")
    print()

    # Get project ID
    headers = {"Authorization": f"Bearer {auth_token}"}
    project_url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    project_response = requests.get(project_url, headers=headers)

    if project_response.status_code != 200:
        print("❌ Failed to get project")
        return 1

    project_id = project_response.json().get("id")
    print(f"✅ Found project: {PROJECT_SLUG} (ID: {project_id})")
    print()

    # Get statuses
    statuses = get_statuses(auth_token, project_id)
    done_status_id = statuses.get("done") or statuses.get("completed") or statuses.get("complete")

    if done_status_id:
        print(f"✅ Found 'Done' status (ID: {done_status_id})")
    else:
        print("⚠️  'Done' status not found, will update description only")
    print()

    # Story to update
    story_ref = 141
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completion_text = COMPLETION_DETAILS.format(timestamp=timestamp)

    print(f"📝 Processing US#{story_ref}...")

    # Find story
    story = find_story_by_ref(auth_token, project_id, story_ref)
    if not story:
        print(f"  ❌ Story US#{story_ref} not found")
        return 1

    story_id = story.get("id")
    story_version = story.get("version", 1)
    current_description = story.get("description", "")
    subject = story.get("subject", "")

    print(f"  ✅ Found: {subject}")
    print(f"     Story ID: {story_id}, Version: {story_version}")

    # Append completion details
    new_description = current_description
    if current_description and not current_description.endswith("\n"):
        new_description += "\n"
    new_description += completion_text

    # Update story
    success, response_text = update_story(
        auth_token, story_id, story_version, new_description, status_id=done_status_id if done_status_id else None
    )

    if success:
        print(f"  ✅ Updated description")
        if done_status_id:
            print(f"  ✅ Status set to 'Done'")
    else:
        print(f"  ❌ Failed to update: {response_text[:200]}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Story updated: US#{story_ref}")
    print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_ref}")
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
