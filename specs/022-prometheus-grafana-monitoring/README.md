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
📋 Planned
