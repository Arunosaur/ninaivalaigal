#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create or update Taiga story for SPEC-094: API Health Regression Tracking"""

import json
import os
import sys

import requests

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"


def get_status_id(auth_token: str, project_id: int, status_name: str) -> int:
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstory-statuses?project={project_id}", headers=headers)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name", "").lower() == status_name.lower():
                return status["id"]
    return None


def main():
    """Create or update SPEC-094 story"""
    print("=" * 80)
    print("SPEC-094: API Health Regression Tracking - Taiga Story")
    print("=" * 80)
    print()

    importer = TaigaImporter(
        f"{API_ENDPOINT}", os.getenv("TAIGA_USERNAME", "admin"), os.getenv("TAIGA_PASSWORD", "admin123")
    )
    importer._get_auth_token()
    auth_token = importer._auth_token

    # Get project
    project_info = requests.get(
        f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers={"Authorization": f"Bearer {auth_token}"}
    ).json()
    if not project_info:
        print("❌ Project not found")
        return
    project_id = project_info["id"]

    # Search for existing story
    stories = requests.get(
        f"{API_ENDPOINT}/userstories?project={project_id}", headers={"Authorization": f"Bearer {auth_token}"}
    ).json()

    spec094_story = None
    for story in stories:
        tags = story.get("tags", [])
        tag_names = [t.get("name", t) if isinstance(t, dict) else str(t) for t in tags]
        if "spec-094" in [str(t).lower() for t in tag_names]:
            spec094_story = story
            break

    description = """**SPEC-094: API Health Regression Tracking**

**Status:** 🔄 NEW (Implementation: 0% complete)
**Phase:** Phase 3
**Priority:** Medium
**Dependencies:** SPEC-018 (API Health Monitoring) should be complete first

---

## 📋 Objective

Implement **historical health trend tracking** and **regression detection** for API health metrics (availability, health check response times, error rates from health checks).

**Distinction from Related SPECs:**
- **SPEC-018:** Real-time health status (current health)
- **SPEC-069:** Performance benchmark regression tracking (latency, throughput from load tests)
- **SPEC-094:** Health endpoint regression tracking (historical trends in health checks)

---

## ✅ What Exists (In Related SPECs)

### SPEC-018: API Health Monitoring (85% Complete)
- ✅ Real-time health endpoints (`/health`, `/health/ready`)
- ✅ Component health checks (Database, Redis, PgBouncer)
- ✅ Prometheus metrics
- ❌ **Missing:** Historical health trend tracking
- ❌ **Missing:** Health regression detection

### SPEC-069: Performance Benchmark Regression Tracking (Complete)
- ✅ Performance benchmark regression detection
- ✅ Historical benchmark tracking
- ✅ Regression severity classification
- ✅ `GET /performance/benchmarks/regressions` endpoint
- ❌ **Different Scope:** Performance benchmarks, not health checks

---

## ❌ What's Missing (SPEC-094)

### 1. Database Schema ❌
- Health check results storage (time-series)
- Health regression tracking table
- Health baseline definitions

### 2. Health Regression Detection ❌
- Algorithm to compare current health metrics to baselines
- Regression severity classification (critical, major, minor)
- Trend analysis for health metrics

### 3. Historical Health Storage ❌
- Store health check results over time
- Aggregate health metrics by time period
- Track correlation with deployments/changes

### 4. API Endpoints ❌
- `GET /health/regressions` - Get health regressions
- `GET /health/history` - Get historical health trends
- `GET /health/compare/{time_period}` - Compare health across time periods
- `POST /health/baseline` - Set health baseline

### 5. Alerting Integration ❌
- Alert on health regressions
- Alert on health degradation trends
- Integration with existing alerting systems

---

## 🎯 Proposed Implementation

### Phase 1: Database Schema
1. Create `health_check_results` table (time-series storage)
2. Create `health_regressions` table (regression tracking)
3. Create `health_baselines` table (baseline definitions)

### Phase 2: Historical Storage
1. Store health check results with timestamps
2. Aggregate health metrics by time period
3. Track correlation with deployments/changes

### Phase 3: Regression Detection
1. Compare current health metrics to baselines
2. Detect gradual degradation (e.g., health check latency increasing)
3. Detect sudden health regressions (e.g., availability drop after deployment)
4. Classify regression severity

### Phase 4: API Endpoints
1. `GET /health/regressions` - Get health regressions
2. `GET /health/history` - Get historical health trends
3. `GET /health/compare/{time_period}` - Compare health across time periods
4. `POST /health/baseline` - Set health baseline

### Phase 5: Alerting
1. Alert on health regressions
2. Alert on health degradation trends
3. Integration with existing alerting systems

---

## 📚 Related Documentation

- **Analysis Document:** `docs/spec-analysis/SPEC_094_COMPREHENSIVE_ANALYSIS.md`
- **SPEC-018:** `specs/018-api-health-monitoring/spec.md` - API Health & Monitoring
- **SPEC-069:** `specs/069-performance-optimization-suite/README.md` - Performance Optimization Suite
- **SPEC_INDEX.md:** Line 162 - SPEC-094 entry

---

## 🔗 Dependencies

- **SPEC-018:** Should be complete (currently 85% complete)
- **SPEC-069:** Can reference regression detection patterns

---

**Analysis Complete:** January 2025
**Status:** Placeholder → Ready for Implementation"""

    subject = "SPEC-094: API Health Regression Tracking"
    tags = ["spec-094", "health", "regression", "monitoring", "phase-3"]

    if spec094_story:
        print(f"✅ Found existing story: US#{spec094_story.get('ref')}: {spec094_story.get('subject')}")
        print(f"   Current status: {spec094_story.get('status_extra_info', {}).get('name', 'Unknown')}")

        # Update description
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        update_payload = {"description": description, "version": spec094_story.get("version", 1)}
        response = requests.patch(
            f"{API_ENDPOINT}/userstories/{spec094_story['id']}", headers=headers, json=update_payload
        )
        if response.status_code == 200:
            print("✅ Story description updated")

            # Set status to "New" if not already
            status_name = spec094_story.get("status_extra_info", {}).get("name", "")
            if status_name.lower() not in ["new", "ready", "in progress"]:
                status_id = get_status_id(auth_token, project_id, "New")
                if status_id:
                    update_payload = {"status": status_id, "version": response.json().get("version", 1)}
                    response = requests.patch(
                        f"{API_ENDPOINT}/userstories/{spec094_story['id']}", headers=headers, json=update_payload
                    )
                    if response.status_code == 200:
                        print("✅ Story status set to 'New'")
        else:
            print(f"❌ Failed to update story: {response.status_code}")
    else:
        print("❌ No existing story found. Creating new story...")

        # Get status ID for "New"
        status_id = get_status_id(auth_token, project_id, "New")
        if not status_id:
            print("❌ Could not find 'New' status")
            return

        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        payload = {
            "project": project_id,
            "subject": subject,
            "description": description,
            "tags": tags,
            "status": status_id,
        }

        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)
        if response.status_code == 201:
            story = response.json()
            print(f"✅ Created story: US#{story.get('ref')}: {story.get('subject')}")
        else:
            print(f"❌ Failed to create story: {response.status_code}")
            print(f"   Response: {response.text[:200]}")


if __name__ == "__main__":
    main()
