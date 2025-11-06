# Frontend Monitoring Guide

**Version:** 2.0 (FastAPI Templating)
**Last Updated:** January 2025
**Status:** Production
**References:** SPEC-118 (Observability), SPEC-119 (SLO Enforcement)

---

## Overview

This guide covers monitoring for the FastAPI-based frontend (customer and admin UIs). Since the frontend is server-rendered, monitoring focuses on server-side metrics rather than client-side analytics.

---

## Monitoring Architecture

### Metrics Flow

```
┌─────────────────┐
│  FastAPI App    │
│  (Frontend UI)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Prometheus     │────▶│   Grafana    │
│  (Metrics)      │     │ (Dashboards) │
└─────────────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  AlertManager   │
│  (Alerts)       │
└─────────────────┘
```

---

## Grafana Dashboards

### Available Dashboards

See **SPEC-118** for complete dashboard setup. Frontend metrics are included in:

#### 1. API Performance Dashboard

**Location**: `config/grafana/dashboards/api-performance-overview.json`

**Metrics**:
- Requests Per Second (RPS)
- Request Latency (P50, P95, P99)
- Error Rate by Status Code (4xx/5xx)
- Application Errors by Type

**Frontend-Specific Panels**:
- Customer UI page load times
- Admin UI page load times
- Template rendering latency

#### 2. Service Health Dashboard

**Location**: `config/grafana/dashboards/service-health.json`

**Metrics**:
- Service Uptime
- CPU Usage
- Memory Usage
- Active Connections

#### 3. Business Metrics Dashboard

**Location**: `config/grafana/dashboards/business-metrics.json`

**Metrics**:
- Memory Operations (remember/recall)
- User & Team Growth
- Registration Activity

**Frontend-Specific Panels**:
- Customer UI page views
- Admin UI page views
- User session duration

#### 4. SLO Compliance Dashboard

**Location**: `config/grafana/dashboards/slo-compliance.json`

**Metrics**:
- Availability (99.9% target)
- Latency (p95 < 800ms)
- Error Rate (< 1%)

---

## Prometheus Metrics

### Frontend-Specific Metrics

#### Request Metrics

```python
# Prometheus metrics for frontend routes
http_requests_total{
    method="GET",
    route="/customer/dashboard",
    status="200"
}

http_request_duration_seconds{
    route="/customer/dashboard",
    quantile="0.95"
}
```

#### Template Rendering Metrics

```python
# Template rendering time
template_render_duration_seconds{
    template="customer/dashboard.html"
}
```

#### User Session Metrics

```python
# Active user sessions
active_sessions_total{
    role="customer"
}

active_sessions_total{
    role="admin"
}
```

---

## Alert Rules

### Critical Alerts

#### High Error Rate

**Alert**: `HighErrorRate`

**Condition**: Error rate > 1% for 5 minutes

**Impact**: Customer UI or Admin UI experiencing errors

**Action**: Check logs, verify database/Redis connectivity

#### High Latency

**Alert**: `HighLatencyP95`

**Condition**: P95 latency > 800ms for 5 minutes

**Impact**: Slow page loads affecting user experience

**Action**: Check database queries, optimize templates

#### Service Down

**Alert**: `ServiceDown`

**Condition**: Service unavailable for 1 minute

**Impact**: Customer/Admin UI completely down

**Action**: Restart service, check health endpoints

### Warning Alerts

#### Template Rendering Slow

**Alert**: `TemplateRenderSlow`

**Condition**: Template render time > 500ms

**Impact**: Slow page rendering

**Action**: Optimize template queries, check database

---

## Performance Budgets

### Page Load Time Targets

| Page | Target | Warning | Critical |
|------|--------|---------|----------|
| Customer Dashboard | < 500ms | > 800ms | > 1500ms |
| Admin Dashboard | < 500ms | > 800ms | > 1500ms |
| Memory Browser | < 800ms | > 1200ms | > 2000ms |
| Login Page | < 300ms | > 500ms | > 1000ms |

### Error Rate Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Customer UI | < 0.1% | > 0.5% | > 1% |
| Admin UI | < 0.1% | > 0.5% | > 1% |
| API Errors | < 0.1% | > 0.5% | > 1% |

---

## Logging

### Structured Logging

Frontend routes log structured JSON:

```json
{
    "timestamp": "2025-01-15T10:30:00Z",
    "level": "INFO",
    "route": "/customer/dashboard",
    "method": "GET",
    "status": 200,
    "duration_ms": 245,
    "user_id": "user-123",
    "session_id": "session-456"
}
```

### Log Aggregation

**Grafana Loki** (see SPEC-118):
- Aggregates logs from all services
- 30-day retention
- Searchable via Grafana

### Log Levels

- **ERROR**: Errors requiring immediate attention
- **WARN**: Warnings that may indicate issues
- **INFO**: General information (request logs)
- **DEBUG**: Detailed debugging information (development only)

---

## Error Tracking

### Server-Side Errors

**Prometheus Metrics**:
```python
app_errors_total{
    error_type="TemplateNotFound",
    route="/customer/dashboard"
}
```

**Grafana Alerts**:
- Error rate > threshold triggers alert
- AlertManager routes to PagerDuty/Slack

### Client-Side Errors

Since we use server-side rendering, most errors are caught server-side. For any client-side JavaScript errors:

**Option 1: Log to Server**
```javascript
// Alpine.js error handling
window.addEventListener('error', (e) => {
    fetch('/api/errors', {
        method: 'POST',
        body: JSON.stringify({
            message: e.message,
            stack: e.stack,
            url: window.location.href
        })
    });
});
```

**Option 2: External Service (Optional)**
- Sentry (if needed)
- LogRocket (if needed)

---

## Runbooks

### Common Issues

#### 1. High Error Rate

**Symptoms**: Error rate > 1% in Grafana

**Steps**:
1. Check Grafana logs (Loki)
2. Identify error pattern (404, 500, timeout)
3. Check database/Redis connectivity
4. Review recent deployments
5. Rollback if needed

#### 2. Slow Page Loads

**Symptoms**: P95 latency > 800ms

**Steps**:
1. Check database query performance
2. Review template rendering time
3. Check Redis cache hit rate
4. Optimize database queries
5. Add database indexes if needed

#### 3. Template Not Found

**Symptoms**: 404 errors for template routes

**Steps**:
1. Verify template file exists
2. Check template path in router
3. Verify Jinja2Templates directory
4. Restart service if needed

---

## Monitoring Best Practices

### 1. Set Up Alerts Early

- Configure alerts before deployment
- Test alert notifications
- Document alert response procedures

### 2. Regular Dashboard Reviews

- Review dashboards weekly
- Identify trends and patterns
- Optimize based on metrics

### 3. Performance Budgets

- Define performance budgets
- Monitor against budgets
- Enforce budgets in CI/CD (SPEC-118)

### 4. Log Retention

- Keep logs for 30 days (Loki)
- Archive older logs if needed
- Ensure compliance with data retention policies

---

## Integration with SPEC-118

### Metrics Collection

- **Prometheus**: Collects metrics from FastAPI
- **Grafana**: Visualizes metrics in dashboards
- **Loki**: Aggregates logs from all services
- **Tempo**: Distributed tracing (if implemented)

### Alerting

- **AlertManager**: Routes alerts to appropriate channels
- **PagerDuty**: Critical alerts
- **Slack**: Warning alerts
- **GitHub Actions**: Incident creation (SPEC-119)

---

## References

- **SPEC-118**: Observability & Performance Budgets
- **SPEC-119**: Automated SLO Enforcement
- **SPEC-016**: CI/CD Pipeline Architecture
- **Grafana Documentation**: https://grafana.com/docs/

---

**Status**: ✅ **Production-Ready**
**Last Updated**: January 2025
**Next Review**: After monitoring validation
