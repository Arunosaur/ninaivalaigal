# SPEC-118 Implementation Tasks

**Date:** January 2025
**Status:** ⚠️ **In Progress** (60% Complete)
**Priority:** HIGH
**Category:** Operational Intelligence & Observability

---

## 📊 Current Status

**SPEC-118** is **60% complete**. Core metrics, dashboards, and alerts are working (via US#102), but the full observability stack needs to be completed.

### ✅ Completed (60%)
- Prometheus Metrics (working)
- Grafana Dashboards (4 dashboards via US#102)
- Prometheus & Grafana Infrastructure (deployed)
- Alert Rules (7 rules loaded)

### ❌ Missing (40%)
- Grafana Loki + Promtail
- Grafana Tempo
- Performance Budget CI Enforcement
- PagerDuty/Opsgenie Integration
- Database & Redis Exporters

---

## 🎯 Implementation Tasks

### Priority 1: Complete Three Pillars (High Priority)

#### Task 1: Deploy Grafana Loki + Promtail

**Goal**: Implement structured log aggregation with 30-day retention

**Tasks**:
- [ ] Add Loki service to `docker-compose.dev.yml`
  ```yaml
  loki:
    image: grafana/loki:2.9.3
    ports: ["3100:3100"]
    volumes:
      - loki_data:/loki
  ```
- [ ] Add Promtail service to `docker-compose.dev.yml`
  ```yaml
  promtail:
    image: grafana/promtail:2.9.3
    volumes:
      - /var/log:/var/log:ro
      - ./monitoring/promtail.yml:/etc/promtail/config.yml
    depends_on:
      - loki
  ```
- [ ] Create `monitoring/promtail.yml` configuration
  - Configure log collection from containers
  - Set up labels for service identification
  - Configure Loki push endpoint
- [ ] Create `monitoring/loki.yml` configuration
  - Set retention period: 30 days
  - Configure storage
  - Set up compression
- [ ] Configure Grafana Loki datasource
  - Add Loki datasource to Grafana
  - Test log querying
- [ ] Implement JSON logging in FastAPI
  - Update logging configuration for structured JSON
  - Add request ID propagation to logs
  - Test log aggregation
- [ ] Create log aggregation dashboard in Grafana
  - Log volume by service
  - Error log filtering
  - Request trace correlation

**Acceptance Criteria**:
- ✅ Loki deployed and accessible (port 3100)
- ✅ Promtail collecting logs from containers
- ✅ Logs visible in Grafana
- ✅ 30-day retention configured
- ✅ JSON structured logs working
- ✅ Request ID propagation working

**Estimated Time**: 4-6 hours

**Dependencies**: None

---

#### Task 2: Deploy Grafana Tempo

**Goal**: Implement distributed tracing with end-to-end request tracing

**Tasks**:
- [ ] Add Tempo service to `docker-compose.dev.yml`
  ```yaml
  tempo:
    image: grafana/tempo:2.3.1
    ports: ["3200:3200", "4317:4317"]
    volumes:
      - tempo_data:/tmp/tempo
  ```
- [ ] Create `monitoring/tempo.yml` configuration
  - Configure trace storage
  - Set up retention (7 days per SPEC)
- [ ] Configure Grafana Tempo datasource
  - Add Tempo datasource to Grafana
  - Test trace querying
- [ ] Update OpenTelemetry configuration (SPEC-010)
  - Configure OTLP exporter to send to Tempo
  - Update trace endpoint: `http://tempo:4317`
  - Test trace collection
- [ ] Add frontend tracing (if applicable)
  - Instrument fetch requests with trace context
  - Propagate trace IDs from backend
- [ ] Create trace visualization dashboard in Grafana
  - Service map visualization
  - Trace duration by service
  - Error trace filtering
- [ ] Test end-to-end tracing
  - Frontend → API → DB → Redis
  - Verify trace correlation
  - Verify request ID propagation

**Acceptance Criteria**:
- ✅ Tempo deployed and accessible (ports 3200, 4317)
- ✅ Traces visible in Grafana
- ✅ End-to-end tracing working (frontend → API → DB → Redis)
- ✅ Trace visualization dashboard created
- ✅ 7-day retention configured
- ✅ OpenTelemetry integration working (SPEC-010)

**Estimated Time**: 4-6 hours

**Dependencies**: SPEC-010 (OpenTelemetry - Complete)

---

### Priority 2: CI/CD Integration (Medium Priority)

#### Task 3: Implement Performance Budget CI Enforcement

**Goal**: Automate performance budget enforcement in CI/CD

**Tasks**:
- [ ] Define performance budgets YAML
  - Create `performance-budgets.yml`
  - Define targets:
    - API P95: < 200ms
    - API P99: < 500ms
    - Frontend LCP: < 2.5s
    - Frontend FID: < 100ms
    - Frontend CLS: < 0.1
    - Frontend TTFB: < 800ms
- [ ] Integrate Lighthouse CI for frontend
  - Add `.github/workflows/lighthouse-ci.yml`
  - Configure Lighthouse CI
  - Set performance thresholds
  - Fail CI on budget violations
- [ ] Add backend load testing (Locust)
  - Create `tests/load/locustfile.py`
  - Define load test scenarios
  - Set performance thresholds
  - Add to CI workflow
- [ ] Create performance budget tracking dashboard
  - Add panel to Grafana dashboard
  - Track budget compliance over time
  - Alert on budget violations
- [ ] Configure CI to enforce budgets
  - Update `.github/workflows/ci.yml`
  - Add performance budget checks
  - Fail PRs on budget violations
- [ ] Document performance budget process
  - Add to README
  - Document how to update budgets
  - Document how to handle violations

**Acceptance Criteria**:
- ✅ Lighthouse CI integrated
- ✅ Backend load testing in CI
- ✅ CI fails on budget violations
- ✅ Performance budget dashboard created
- ✅ Documentation complete

**Estimated Time**: 6-8 hours

**Dependencies**: None

---

### Priority 3: Alert Integration (Medium Priority)

#### Task 4: Configure PagerDuty/Opsgenie Integration

**Goal**: Enable < 5min notification for critical issues

**Tasks**:
- [ ] Deploy Alertmanager (if not already deployed)
  - Add Alertmanager service to `docker-compose.dev.yml`
  - Configure Alertmanager
- [ ] Create `monitoring/alertmanager.yml` configuration
  - Configure PagerDuty/Opsgenie receiver
  - Set up routing rules
  - Configure grouping and inhibition
- [ ] Set up PagerDuty/Opsgenie integration
  - Create PagerDuty/Opsgenie service
  - Get integration key
  - Configure webhook
- [ ] Test alert routing
  - Trigger test alert
  - Verify notification received
  - Verify response time < 5min
- [ ] Create runbooks for common alerts
  - HighErrorRate runbook
  - HighLatencyP95 runbook
  - ServiceDown runbook
  - Link runbooks to alerts
- [ ] Document on-call procedures
  - Add to runbooks
  - Document escalation process
  - Document incident response

**Acceptance Criteria**:
- ✅ Alertmanager deployed
- ✅ PagerDuty/Opsgenie integration configured
- ✅ Alerts route to PagerDuty/Opsgenie
- ✅ Response time < 5min verified
- ✅ Runbooks created
- ✅ Documentation complete

**Estimated Time**: 4-6 hours

**Dependencies**: Alert rules (US#102 - Complete)

---

### Priority 4: Enhancements (Lower Priority)

#### Task 5: Deploy Database & Redis Exporters

**Goal**: Add dedicated metrics for database and Redis

**Tasks**:
- [ ] Deploy PostgreSQL exporter
  - Add to `docker-compose.dev.yml`
  - Configure connection to PostgreSQL
  - Set up scrape configuration
- [ ] Deploy Redis exporter
  - Add to `docker-compose.dev.yml`
  - Configure connection to Redis
  - Set up scrape configuration
- [ ] Update Prometheus scrape config
  - Add PostgreSQL exporter job
  - Add Redis exporter job
- [ ] Create database metrics dashboard
  - Query time (P95, P99)
  - Connection pool utilization
  - Active connections
- [ ] Create Redis metrics dashboard
  - Operation time (P95, P99)
  - Memory usage
  - Cache hit rate

**Acceptance Criteria**:
- ✅ PostgreSQL exporter deployed
- ✅ Redis exporter deployed
- ✅ Metrics collected
- ✅ Dashboards created

**Estimated Time**: 3-4 hours

**Dependencies**: None

---

#### Task 6: Verify Request ID Propagation

**Goal**: Ensure request ID propagation works end-to-end

**Tasks**:
- [ ] Verify request ID in FastAPI
  - Check request ID middleware
  - Verify ID generation
  - Test ID propagation
- [ ] Verify request ID in logs
  - Check log format
  - Verify ID in log entries
  - Test log correlation
- [ ] Verify request ID in traces
  - Check trace context
  - Verify ID in traces
  - Test trace correlation
- [ ] Test end-to-end correlation
  - Frontend request → API → DB → Redis
  - Verify same request ID across all services
  - Test log/trace correlation
- [ ] Document request ID propagation
  - Add to README
  - Document correlation process

**Acceptance Criteria**:
- ✅ Request ID generated in FastAPI
- ✅ Request ID in logs
- ✅ Request ID in traces
- ✅ End-to-end correlation working
- ✅ Documentation complete

**Estimated Time**: 2-3 hours

**Dependencies**: Task 1 (Loki), Task 2 (Tempo)

---

## 📋 Implementation Plan

### Week 1: Complete Three Pillars
- **Day 1-2**: Deploy Loki + Promtail (Task 1)
- **Day 3-4**: Deploy Tempo (Task 2)
- **Day 5**: Verify Request ID Propagation (Task 6)

### Week 2: CI/CD Integration
- **Day 1-3**: Implement Performance Budget CI Enforcement (Task 3)
- **Day 4-5**: Test and document

### Week 3: Alert Integration
- **Day 1-2**: Configure PagerDuty/Opsgenie (Task 4)
- **Day 3-4**: Create runbooks
- **Day 5**: Test and document

### Week 4: Enhancements
- **Day 1-2**: Deploy Database & Redis Exporters (Task 5)
- **Day 3-4**: Create dashboards
- **Day 5**: Final testing and documentation

---

## ✅ Success Criteria

**SPEC-118 will be 100% complete when:**

1. ✅ **Three Pillars**: Logs (Loki), Metrics (Prometheus), Traces (Tempo) all deployed
2. ✅ **CI Enforcement**: Performance budgets enforced in CI/CD
3. ✅ **Alert Integration**: PagerDuty/Opsgenie integration working
4. ✅ **Enhancements**: Database & Redis exporters deployed
5. ✅ **Documentation**: All processes documented

**Target Completion**: 4 weeks

---

## 📝 Notes

- **US#102**: Already completed core dashboards and alerts (60% of SPEC-118)
- **SPEC-010**: OpenTelemetry foundation exists, Tempo will extend it
- **Dependencies**: All tasks can be done in parallel except Task 6 (depends on Tasks 1 & 2)

---

**Status**: ⚠️ **In Progress** (60% Complete)
**Next Steps**: Start with Task 1 (Loki + Promtail) to complete the three pillars of observability
