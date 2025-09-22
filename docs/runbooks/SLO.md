# Service Level Objectives (SLO)

This document defines the Service Level Objectives for the ninaivalaigal platform, establishing performance and reliability targets for monitoring and alerting.

## Overview

Service Level Objectives (SLOs) define the target level of service reliability and performance that users can expect. These metrics are used for:

- **Monitoring**: Continuous tracking of service health
- **Alerting**: Automated notifications when SLOs are at risk
- **Capacity Planning**: Understanding system limits and scaling needs
- **Incident Response**: Prioritizing issues based on SLO impact

## Core SLOs

### 1. API Availability
- **Target**: 99.9% uptime (8.76 hours downtime per year)
- **Measurement**: HTTP 200 responses / total requests
- **Time Window**: 30-day rolling window
- **Alert Threshold**: <99.5% (risk of SLO breach)

### 2. API Response Time
- **Target**: 95th percentile < 250ms
- **Measurement**: End-to-end API response time
- **Time Window**: 5-minute rolling window
- **Alert Threshold**: p95 > 300ms for 5+ minutes

### 3. Health Check Latency
- **Target**: 95th percentile < 100ms
- **Measurement**: `/health/detailed` endpoint response time
- **Time Window**: 1-minute rolling window
- **Alert Threshold**: p95 > 150ms for 2+ minutes

### 4. Database Connection Health
- **Target**: 99.95% successful connections
- **Measurement**: Successful DB queries / total attempts
- **Time Window**: 5-minute rolling window
- **Alert Threshold**: <99.9% success rate

### 5. Memory Provider Availability (HTTP mode)
- **Target**: 99.9% availability when MEMORY_PROVIDER=http
- **Measurement**: Successful mem0 health checks / total attempts
- **Time Window**: 5-minute rolling window
- **Alert Threshold**: <99.5% availability

## Error Budget

### Monthly Error Budget
- **API Availability**: 0.1% (43.2 minutes downtime per month)
- **Response Time**: 5% of requests may exceed 250ms
- **Health Checks**: 0.05% may exceed 100ms

### Error Budget Policies
- **50% consumed**: Increase monitoring frequency
- **75% consumed**: Freeze non-critical deployments
- **90% consumed**: Emergency response, halt all deployments
- **100% consumed**: Post-incident review required

## Monitoring Metrics

### Prometheus Metrics

#### Core Application Metrics
```
# Request metrics
ninaivalaigal_requests_total - Total API requests
ninaivalaigal_request_duration_seconds - Request duration histogram

# Health metrics
ninaivalaigal_health_latency_seconds - Health check response time
ninaivalaigal_database_healthy - Database health status (0/1)

# System metrics
ninaivalaigal_cpu_usage_percent - CPU utilization
ninaivalaigal_memory_usage_percent - Memory utilization
ninaivalaigal_uptime_seconds - Application uptime
```

#### Database Metrics
```
ninaivalaigal_db_connections_active - Active database connections
ninaivalaigal_db_query_duration_seconds - Database query time
ninaivalaigal_db_connection_errors_total - Database connection failures
```

#### Memory Provider Metrics (HTTP mode)
```
ninaivalaigal_memory_provider_healthy - Memory provider health (0/1)
ninaivalaigal_memory_requests_total - Total memory provider requests
ninaivalaigal_memory_request_duration_seconds - Memory request duration
```

### Health Check Endpoints

#### `/health` - Basic Health Check
- **Purpose**: Load balancer health checks
- **Response**: Simple 200 OK or 503 Service Unavailable
- **SLO**: <50ms response time, 99.99% availability

#### `/health/detailed` - Comprehensive Health Check
- **Purpose**: SLO monitoring and diagnostics
- **Response**: Detailed JSON with component health and latencies
- **SLO**: <100ms response time, includes SLO compliance indicator

#### `/metrics` - Prometheus Metrics
- **Purpose**: Metrics collection for monitoring systems
- **Response**: Prometheus format metrics
- **SLO**: <200ms response time, 99.9% availability

## Alerting Rules

### Critical Alerts (PagerDuty)
```yaml
# API Down
- alert: APIDown
  expr: ninaivalaigal_requests_total{status!~"2.."} / ninaivalaigal_requests_total > 0.1
  for: 1m
  severity: critical

# High Latency
- alert: HighLatency
  expr: histogram_quantile(0.95, ninaivalaigal_request_duration_seconds) > 0.25
  for: 5m
  severity: critical

# Database Unhealthy
- alert: DatabaseUnhealthy
  expr: ninaivalaigal_database_healthy == 0
  for: 30s
  severity: critical
```

### Warning Alerts (Slack)
```yaml
# SLO Risk
- alert: SLORisk
  expr: ninaivalaigal_requests_total{status!~"2.."} / ninaivalaigal_requests_total > 0.05
  for: 5m
  severity: warning

# High CPU
- alert: HighCPU
  expr: ninaivalaigal_cpu_usage_percent > 80
  for: 10m
  severity: warning

# High Memory
- alert: HighMemory
  expr: ninaivalaigal_memory_usage_percent > 85
  for: 10m
  severity: warning
```

## SLO Monitoring Dashboard

### Key Metrics Dashboard
- **Availability**: Current uptime percentage and trend
- **Latency**: p50, p95, p99 response times with SLO thresholds
- **Error Rate**: 4xx/5xx error rates with budget consumption
- **Throughput**: Requests per second and capacity utilization

### Component Health Dashboard
- **Database**: Connection pool, query performance, health status
- **Memory Provider**: Availability, response times, error rates
- **System Resources**: CPU, memory, disk utilization
- **Container Health**: Container status, restart counts, resource limits

### SLO Compliance Dashboard
- **Error Budget**: Current consumption and burn rate
- **SLO Trends**: Historical compliance over time
- **Incident Impact**: SLO impact of recent incidents
- **Capacity Planning**: Resource utilization trends

## Implementation

### Metrics Collection
```bash
# Start stack with metrics enabled
make stack-up

# Verify metrics endpoint
curl http://localhost:13370/metrics

# Check detailed health
curl http://localhost:13370/health/detailed
```

### Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ninaivalaigal-api'
    static_configs:
      - targets: ['localhost:13370']
    scrape_interval: 15s
    metrics_path: /metrics
```

### Grafana Dashboard
- Import dashboard from `monitoring/grafana-dashboard.json`
- Configure data source: Prometheus
- Set up alerting channels: PagerDuty, Slack

## Incident Response

### SLO Breach Response
1. **Immediate**: Acknowledge alert, assess impact
2. **Investigation**: Use SLO dashboard to identify root cause
3. **Mitigation**: Apply immediate fixes to restore service
4. **Communication**: Update status page, notify stakeholders
5. **Resolution**: Implement permanent fix
6. **Post-Incident**: Review SLO impact, update procedures

### Error Budget Management
- **Budget Tracking**: Monitor consumption in real-time
- **Release Gating**: Automatic deployment blocks when budget low
- **Capacity Planning**: Scale resources before budget exhaustion
- **Process Improvement**: Adjust SLOs based on user needs

## Review and Updates

### Monthly SLO Review
- Analyze SLO compliance and error budget consumption
- Review alert effectiveness and false positive rates
- Update SLO targets based on user feedback and system capacity
- Plan infrastructure improvements for SLO compliance

### Quarterly Business Review
- Report SLO performance to stakeholders
- Align SLOs with business objectives
- Budget for infrastructure improvements
- Update incident response procedures

This SLO framework ensures reliable, performant service delivery while providing clear metrics for operational excellence and continuous improvement.
