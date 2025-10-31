---
title: 'SPEC-022: Kubernetes Monitoring with Prometheus + Grafana'
---


# SPEC-022: Kubernetes Monitoring with Prometheus + Grafana

## Title
Cluster Observability with Prometheus & Grafana

## Objective
Provide detailed metrics and visualization for all running workloads.

## Features

- Deploy Prometheus + Grafana via Helm
- Scrape API `/metrics` endpoint
- Dashboards for:
  - Pod CPU / Memory usage
  - API error rates
  - Request latency
  - Container restarts

## Implementation Targets

- Alert rules via Prometheus
- Grafana dashboard provisioning via config maps

## Technical Requirements

### Prometheus Configuration
```yaml
# monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'ninaivalaigal-api'
      static_configs:
      - targets: ['ninaivalaigal-api:8000']
      metrics_path: '/metrics'
```

### Grafana Dashboards
- **API Performance**: Request rate, error rate, duration (RED metrics)
- **Infrastructure**: CPU, memory, disk usage per pod
- **Database**: Connection pool, query performance
- **Memory System**: Memory operations, provider health

### Alert Rules
```yaml
# monitoring/alerts.yaml
groups:
- name: ninaivalaigal
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    annotations:
      summary: "High error rate detected"
```

## Success Criteria
- [ ] Prometheus collecting metrics from all components
- [ ] Grafana dashboards showing real-time data
- [ ] Alerts firing for error conditions
- [ ] Historical data retention (30 days minimum)

## Status
📋 Planned - **See SPEC-101 for comprehensive implementation**

---

## Note: Merged into SPEC-101

**SPEC-022** (Prometheus + Grafana) is a **subset** of **SPEC-101** (Unified Observability).

**SPEC-101 includes:**
- ✅ Prometheus (metrics)
- ✅ Grafana (dashboards)
- ✅ Loki (log aggregation)
- ✅ Promtail (log shipping)
- ✅ Jaeger (distributed tracing - already running)

**Recommendation:** Implement the full observability stack via SPEC-101 rather than deploying Prometheus + Grafana in isolation.

---

## Related Documentation

### Comprehensive SPEC
- **SPEC-101:** Unified Observability and Performance Governance
  - Location: `/specs/101-unified-observability-performance/README.md`
  - Taiga: **US#152**

### Related SPECs
- **SPEC-099:** Rust Migration Strategy (ROI validation via metrics)
- **SPEC-100:** API Container Modularization (service monitoring)
- **SPEC-018:** API Health Monitoring

### Taiga Tracking
- **US#152:** SPEC-101 Unified Observability Stack (includes SPEC-022)

---

**Last Updated:** October 30, 2025
**Status:** Merged into SPEC-101 - Track via US#152
