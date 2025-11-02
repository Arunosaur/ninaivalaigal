---
{}
---

# SPEC-094: API Health Regression Tracking

**Status:** Planned (Phase 3)
**Priority:** Medium
**Owner:** Core API (Python)
**Dependencies:** SPEC-018 (API Health Monitoring), SPEC-069 (Performance Optimization Suite)

---

## 🎯 Objective

Implement **historical health trend tracking** and **regression detection** for API health metrics (availability, health check response times, error rates from health checks).

This SPEC provides the capability to:
- Store historical health check results over time
- Detect significant deviations or regressions in API health metrics
- Provide endpoints for querying historical health data and identified regressions
- Integrate with alerting systems for proactive notification of health regressions

---

## 🧩 Context & Distinctions

### How SPEC-094 Differs from Related SPECs

| SPEC | Focus | Status | Relationship |
|------|-------|--------|--------------|
| **SPEC-018** | Real-time API health monitoring & diagnostics | 85% Complete | **Foundation** - SPEC-094 builds on SPEC-018's health endpoints to add historical tracking |
| **SPEC-069** | Performance benchmark regression tracking | Complete | **Complementary** - Different metrics (performance benchmarks vs health checks) |
| **SPEC-094** | Health endpoint regression tracking (historical trends) | Planned | **This SPEC** - Focuses on health check metrics over time |

**Key Distinction:**
- **SPEC-018:** Provides **current/real-time** health status
- **SPEC-069:** Tracks **performance benchmark** regressions (latency, throughput from load tests)
- **SPEC-094:** Tracks **health endpoint** regressions (availability, health check response times, error rates from health checks)

---

## 🏗️ Architecture Overview

### Database Schema

**Schema Decision:** All tables will be created in the **`public` schema**.

**Justification:**
1. **Consistency:** Performance benchmarks (SPEC-069) use `public` schema (`performance_benchmark_runs`, `performance_benchmark_results`)
2. **Monitoring Pattern:** Existing monitoring tables (`system_health_metrics`, `api_performance_logs`) are in `public`
3. **Ownership:** Health regression tracking is infrastructure/monitoring, owned by Core API (which manages `public` schema)
4. **Future-proofing:** While an `admin` schema is mentioned in docs for future system monitoring, it's not yet implemented. Migrations can be done later if needed.

**Migration File:** `alembic/versions/0131_spec094_health_regression_tracking.py`
**Down Revision:** `0130_admin_activity_logs`

### Proposed Database Tables

#### `public.health_check_results` (Time-Series Storage)

Stores individual health check results with timestamps for historical analysis.

```python
op.create_table(
    "health_check_results",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("check_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("endpoint", sa.String(100), nullable=False),  # '/health', '/health/ready', '/health/detailed'
    sa.Column("overall_status", sa.String(20), nullable=False),  # 'healthy', 'degraded', 'unhealthy'
    sa.Column("response_time_ms", sa.Numeric(10, 2)),  # Response time for health check
    sa.Column("database_status", sa.String(20)),  # 'healthy', 'unhealthy', 'unknown'
    sa.Column("database_response_time_ms", sa.Numeric(10, 2)),
    sa.Column("redis_status", sa.String(20)),
    sa.Column("redis_response_time_ms", sa.Numeric(10, 2)),
    sa.Column("pgbouncer_status", sa.String(20)),
    sa.Column("memory_provider_status", sa.String(20)),
    sa.Column("error_rate", sa.Numeric(5, 4)),  # Error rate percentage
    sa.Column("environment", sa.String(50), nullable=False),  # 'production', 'staging', 'development'
    sa.Column("service_version", sa.String(50)),  # Application version
    sa.Column("metadata", postgresql.JSONB, server_default="{}"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    schema="public",
)
```

**Indexes:**
- `idx_health_check_results_timestamp` on `check_timestamp DESC`
- `idx_health_check_results_endpoint` on `endpoint`
- `idx_health_check_results_status` on `overall_status`
- `idx_health_check_results_env_timestamp` on `(environment, check_timestamp DESC)`

#### `public.health_regressions` (Regression Tracking)

Tracks detected health regressions with severity classification.

```python
op.create_table(
    "health_regressions",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("regression_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("metric_name", sa.String(100), nullable=False),  # 'availability', 'response_time', 'error_rate'
    sa.Column("baseline_period_start", sa.DateTime(timezone=True), nullable=False),
    sa.Column("baseline_period_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
    sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("baseline_value", sa.Numeric(15, 4), nullable=False),
    sa.Column("current_value", sa.Numeric(15, 4), nullable=False),
    sa.Column("change_percent", sa.Numeric(8, 2), nullable=False),  # Negative = regression
    sa.Column("change_absolute", sa.Numeric(15, 4), nullable=False),
    sa.Column("regression_threshold", sa.Numeric(8, 2), default=-5.0),  # % change threshold
    sa.Column("is_regression", sa.Boolean(), nullable=False, server_default="false"),
    sa.Column("regression_severity", sa.String(20), default="none"),  # 'none', 'minor', 'major', 'critical'
    sa.Column("endpoint", sa.String(100)),  # Health endpoint affected
    sa.Column("environment", sa.String(50), nullable=False),
    sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
    sa.Column("resolved_at", sa.DateTime(timezone=True)),
    sa.Column("notes", sa.Text()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    schema="public",
)
```

**Indexes:**
- `idx_health_regressions_timestamp` on `regression_timestamp DESC`
- `idx_health_regressions_metric` on `metric_name`
- `idx_health_regressions_unresolved` on `(is_regression, resolved)` WHERE `is_regression = TRUE`
- `idx_health_regressions_severity` on `regression_severity` WHERE `is_regression = TRUE`

#### `public.health_baselines` (Baseline Definitions)

Defines health metric baselines for regression comparison.

```python
op.create_table(
    "health_baselines",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("baseline_name", sa.String(100), nullable=False),  # e.g., 'production_stable', 'v1.0_baseline'
    sa.Column("metric_name", sa.String(100), nullable=False),
    sa.Column("endpoint", sa.String(100)),
    sa.Column("environment", sa.String(50), nullable=False),
    sa.Column("baseline_value", sa.Numeric(15, 4), nullable=False),
    sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
    sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("sample_count", sa.Integer(), nullable=False),
    sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    schema="public",
)
```

**Indexes:**
- `idx_health_baselines_active` on `(metric_name, environment, is_active)` WHERE `is_active = TRUE`

---

## ⚙️ Key Components

### 1. Historical Health Storage Service

**File:** `server/health/health_storage.py`

Service to store and retrieve health check results:
- `store_health_check_result()` - Store individual health check
- `get_health_history()` - Retrieve historical health data with filtering
- `get_health_trends()` - Aggregate health metrics by time period

### 2. Health Regression Detection Algorithm

**File:** `server/health/regression_detector.py`

Algorithm to detect health regressions:
- `detect_regressions()` - Compare current health metrics to baselines
- `classify_severity()` - Classify regression severity (minor, major, critical)
- `compare_to_baseline()` - Compare specific metric across time periods

### 3. API Endpoints

**File:** `services/core-api/routers/health_regression.py`

New endpoints for health regression tracking:
- `GET /health/regressions` - Get detected health regressions
- `GET /health/history` - Get historical health trends
- `GET /health/compare/{time_period}` - Compare health across time periods
- `POST /health/baseline` - Set or update health baseline
- `GET /health/baselines` - List active baselines

### 4. Alerting Integration

**File:** `server/health/health_alerting.py`

Integration with existing alerting systems:
- Alert on detected regressions
- Alert on health degradation trends
- Integration with `lib/observability/platform_alerting.py`

---

## 🔗 Dependencies

### Required (Must be Complete)

- **SPEC-018:** API Health & Monitoring (85% complete)
  - Provides health endpoints (`/health`, `/health/ready`, `/health/detailed`)
  - Needed to collect health check data

### Complementary (Can Reference)

- **SPEC-069:** Performance Optimization Suite (Complete)
  - Regression detection patterns and algorithms
  - Baseline comparison methodology

---

## 🧪 Acceptance Criteria

### Database Schema
- [ ] Alembic migration `0131_spec094_health_regression_tracking.py` created
- [ ] Tables created in `public` schema: `health_check_results`, `health_regressions`, `health_baselines`
- [ ] All indexes created and validated
- [ ] Migration can be upgraded and downgraded successfully

### Historical Storage
- [ ] Health check results stored automatically from health endpoints
- [ ] Historical data retrievable with filtering (time range, endpoint, environment)
- [ ] Data retention policy configurable

### Regression Detection
- [ ] Algorithm detects significant health degradations
- [ ] Regression severity classified correctly (minor, major, critical)
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

### Phase 1: Database Schema (Foundation)
1. Create Alembic migration `0131_spec094_health_regression_tracking.py`
2. Create tables: `health_check_results`, `health_regressions`, `health_baselines`
3. Add indexes for efficient querying
4. Test migration upgrade/downgrade

### Phase 2: Historical Storage Service
1. Implement `health_storage.py` service
2. Integrate with existing health endpoints to store results
3. Implement retrieval methods with filtering
4. Add data retention/cleanup logic

### Phase 3: Regression Detection
1. Implement `regression_detector.py` algorithm
2. Implement baseline management
3. Add severity classification logic
4. Test regression detection with sample data

### Phase 4: API Endpoints
1. Create `health_regression.py` router
2. Implement all endpoints
3. Add OpenAPI documentation
4. Add request/response validation

### Phase 5: Alerting Integration
1. Implement `health_alerting.py`
2. Integrate with existing alerting system
3. Add alert deduplication
4. Test alert generation

---

## 🔒 Security & Compliance

- Health check results may contain system information (not user data)
- Ensure proper access control on health regression endpoints
- Consider data retention policies for compliance

---

## 📊 Related Documentation

- **Analysis Document:** `docs/spec-analysis/SPEC_094_COMPREHENSIVE_ANALYSIS.md`
- **Taiga Story:** US#644: SPEC-094: API Health Regression Tracking
- **SPEC-018:** `specs/018-api-health-monitoring/spec.md` - API Health & Monitoring
- **SPEC-069:** `specs/069-performance-optimization-suite/README.md` - Performance Optimization Suite
- **Database Schema Reference:** `docs/DATABASE_SCHEMA_REFERENCE.md`

---

## 🏁 Status

**Current:** Planned - Ready for implementation
**Next Step:** Create Alembic migration and begin Phase 1 implementation

**Last Updated:** January 2025
