#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update Taiga story US#644 (SPEC-094) with comprehensive SPEC details"""

import os
import sys

# Add tasks/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tasks", "scripts"))

from taiga_import_tasks import TaigaImporter


def main():
    """Update US#644 story with SPEC details"""
    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(f"{taiga_url}/api/v1", username=username, password=password)
    importer._get_auth_token()

    story_ref = 644
    story = importer.get_user_story("ninaivalaigal", story_ref)

    if not story:
        print(f"❌ Story US#{story_ref} not found in Taiga")
        return

    print(f"✅ Found story: SPEC-094: API Health Regression Tracking")
    print(f"   Current version: {story.get('version')}")

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

## 🗄️ Database Schema Decision

**Schema:** **`public` schema**

**Justification:**
1. **Consistency:** Performance benchmarks (SPEC-069) use `public` schema
2. **Monitoring Pattern:** Existing monitoring tables (`system_health_metrics`, `api_performance_logs`) are in `public`
3. **Ownership:** Health regression tracking is infrastructure/monitoring, owned by Core API (manages `public` schema)
4. **Future-proofing:** While an `admin` schema is mentioned for future system monitoring, it's not yet implemented. Migrations can be done later if needed.

**Migration File:** `alembic/versions/0131_spec094_health_regression_tracking.py`
**Down Revision:** `0130_admin_activity_logs`

---

## 📊 Proposed Database Tables

### `public.health_check_results` (Time-Series Storage)

Stores individual health check results with timestamps for historical analysis.

**Key Columns:**
- `check_timestamp` - When the health check was performed
- `endpoint` - Health endpoint (`/health`, `/health/ready`, `/health/detailed`)
- `overall_status` - Overall health status (`healthy`, `degraded`, `unhealthy`)
- `response_time_ms` - Response time for health check
- `database_status`, `redis_status`, `pgbouncer_status` - Component statuses
- `error_rate` - Error rate percentage
- `environment` - Environment (`production`, `staging`, `development`)
- `service_version` - Application version

### `public.health_regressions` (Regression Tracking)

Tracks detected health regressions with severity classification.

**Key Columns:**
- `metric_name` - Metric name (`availability`, `response_time`, `error_rate`)
- `baseline_value`, `current_value` - Values for comparison
- `change_percent` - Percentage change (negative = regression)
- `is_regression` - Whether a regression was detected
- `regression_severity` - Severity (`none`, `minor`, `major`, `critical`)
- `endpoint` - Health endpoint affected
- `environment` - Environment
- `resolved` - Whether regression has been resolved

### `public.health_baselines` (Baseline Definitions)

Defines health metric baselines for regression comparison.

**Key Columns:**
- `baseline_name` - Name of baseline (e.g., `production_stable`, `v1.0_baseline`)
- `metric_name` - Metric name
- `endpoint` - Health endpoint
- `environment` - Environment
- `baseline_value` - Baseline value
- `period_start`, `period_end` - Baseline period
- `is_active` - Whether baseline is currently active

**For full schema details:** See `specs/094-api-health-regression-tracking/README.md`

---

## ⚙️ Implementation Components

### 1. Historical Health Storage Service
**File:** `server/health/health_storage.py`
- Store health check results
- Retrieve historical health data with filtering
- Aggregate health metrics by time period

### 2. Health Regression Detection Algorithm
**File:** `server/health/regression_detector.py`
- Detect health regressions by comparing to baselines
- Classify regression severity
- Compare metrics across time periods

### 3. API Endpoints
**File:** `services/core-api/routers/health_regression.py`
- `GET /health/regressions` - Get detected health regressions
- `GET /health/history` - Get historical health trends
- `GET /health/compare/{time_period}` - Compare health across time periods
- `POST /health/baseline` - Set or update health baseline
- `GET /health/baselines` - List active baselines

### 4. Alerting Integration
**File:** `server/health/health_alerting.py`
- Alert on detected regressions
- Alert on health degradation trends
- Integration with existing alerting system

---

## 🧪 Acceptance Criteria

### Database Schema
- [ ] Alembic migration `0131_spec094_health_regression_tracking.py` created
- [ ] Tables created in `public` schema
- [ ] All indexes created and validated
- [ ] Migration can be upgraded and downgraded successfully

### Historical Storage
- [ ] Health check results stored automatically
- [ ] Historical data retrievable with filtering
- [ ] Data retention policy configurable

### Regression Detection
- [ ] Algorithm detects significant health degradations
- [ ] Regression severity classified correctly
- [ ] Baselines can be set and updated
- [ ] Comparison with baselines works correctly

### API Endpoints
- [ ] All endpoints return correct data
- [ ] Endpoints handle errors gracefully
- [ ] API responses follow OpenAPI schema

### Alerting
- [ ] Alerts generated on detected regressions
- [ ] Alert deduplication works correctly
- [ ] Integration with existing alerting system validated

---

## 📚 Implementation Roadmap

### Phase 1: Database Schema (Foundation) 🔨
1. Create Alembic migration
2. Create tables: `health_check_results`, `health_regressions`, `health_baselines`
3. Add indexes for efficient querying
4. Test migration upgrade/downgrade

### Phase 2: Historical Storage Service 🔨
1. Implement `health_storage.py` service
2. Integrate with existing health endpoints to store results
3. Implement retrieval methods with filtering
4. Add data retention/cleanup logic

### Phase 3: Regression Detection 🔨
1. Implement `regression_detector.py` algorithm
2. Implement baseline management
3. Add severity classification logic
4. Test regression detection with sample data

### Phase 4: API Endpoints 🔨
1. Create `health_regression.py` router
2. Implement all endpoints
3. Add OpenAPI documentation
4. Add request/response validation

### Phase 5: Alerting Integration 🔨
1. Implement `health_alerting.py`
2. Integrate with existing alerting system
3. Add alert deduplication
4. Test alert generation

---

## 🔗 Dependencies

### Required
- **SPEC-018:** API Health & Monitoring (85% complete)
  - Provides health endpoints needed to collect data

### Complementary
- **SPEC-069:** Performance Optimization Suite (Complete)
  - Can reference regression detection patterns

---

## 📊 Related Documentation

- **SPEC README:** `specs/094-api-health-regression-tracking/README.md`
- **Analysis Document:** `docs/spec-analysis/SPEC_094_COMPREHENSIVE_ANALYSIS.md`
- **SPEC-018:** `specs/018-api-health-monitoring/spec.md`
- **SPEC-069:** `specs/069-performance-optimization-suite/README.md`
- **Database Schema Reference:** `docs/DATABASE_SCHEMA_REFERENCE.md`

---

**Ready for Implementation:** Schema decisions documented, implementation roadmap defined.

**Last Updated:** January 2025"""

    import requests

    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000")
    api_endpoint = f"{taiga_url}/api/v1"

    headers = {"Authorization": f"Bearer {importer._auth_token}", "Content-Type": "application/json"}
    update_payload = {"description": description, "version": story.get("version", 1)}

    response = requests.patch(f"{api_endpoint}/userstories/{story['id']}", headers=headers, json=update_payload)

    if response.status_code == 200:
        print("✅ Story description updated with comprehensive SPEC details")
    else:
        print(f"❌ Failed to update story: {response.status_code}")
        print(f"   Response: {response.text[:200]}")


if __name__ == "__main__":
    main()
