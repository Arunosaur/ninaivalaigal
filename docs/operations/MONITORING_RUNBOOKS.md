# Monitoring & Alerting Operations Runbooks

This document provides comprehensive runbooks for operating the ninaivalaigal monitoring and alerting infrastructure.

## Table of Contents

1. [System Overview](#system-overview)
2. [Alert Response Procedures](#alert-response-procedures)
3. [Health Check Troubleshooting](#health-check-troubleshooting)
4. [SLO Incident Management](#slo-incident-management)
5. [Monitoring System Maintenance](#monitoring-system-maintenance)
6. [Grafana Dashboard Operations](#grafana-dashboard-operations)
7. [Emergency Procedures](#emergency-procedures)

---

## System Overview

### Components

- **SLO Monitoring**: Real-time Service Level Objective tracking
- **Alert Manager**: PagerDuty, Slack, and webhook integrations
- **Health Checks**: Database, Redis, and application health monitoring
- **Monitoring Automation**: Self-healing and recovery procedures
- **Grafana Dashboards**: Visualization and business intelligence

### SLO Targets

| Metric | Target | Critical Threshold | High Threshold |
|--------|--------|-------------------|----------------|
| Availability | 99.9% | <99.5% | <99.8% |
| Response Time P95 | <200ms | >1000ms | >500ms |
| Error Rate | <0.1% | >1% | >0.5% |

### Alert Severity Levels

- **CRITICAL**: Service down, major SLO violations
- **HIGH**: Performance degradation, health issues
- **MEDIUM**: Warning thresholds exceeded
- **LOW**: Informational alerts

---

## Alert Response Procedures

### CRITICAL Alerts

**Response Time**: Within 5 minutes
**Escalation**: Immediate PagerDuty escalation

#### Service Down Alert

1. **Immediate Actions (0-5 minutes)**
   ```bash
   # Check service status
   make health-check

   # Check container status
   container ps | grep nina

   # Check recent logs
   container logs nina-api --tail=100
   ```

2. **Diagnostic Steps (5-15 minutes)**
   ```bash
   # Check resource utilization
   container stats nina-api

   # Check database connectivity
   make check-db-health

   # Check Redis connectivity
   make check-redis-health
   ```

3. **Recovery Actions**
   ```bash
   # Restart service if needed
   container restart nina-api

   # Scale resources if needed
   # (Kubernetes: kubectl scale deployment nina-api --replicas=2)
   ```

4. **Verification**
   ```bash
   # Verify service recovery
   curl -f http://localhost:13370/health

   # Check SLO status
   curl http://localhost:13370/monitoring/slo
   ```

#### SLO Critical Violation

1. **Assess Impact**
   ```bash
   # Get current SLO status
   curl "http://localhost:13370/monitoring/slo?window=1h"

   # Check active alerts
   curl http://localhost:13370/monitoring/alerts
   ```

2. **Identify Root Cause**
   - Check response times: Look for slow endpoints
   - Check error rates: Look for failing components
   - Check availability: Look for service downtime

3. **Implement Fixes**
   - Scale horizontally if load-related
   - Optimize slow queries if database-related
   - Fix application bugs if error-related

### HIGH Alerts

**Response Time**: Within 15 minutes
**Escalation**: Team lead notification after 30 minutes

#### Performance Degradation

1. **Performance Analysis**
   ```bash
   # Check response times
   curl http://localhost:13370/metrics | grep http_request_duration

   # Check database performance
   make check-db-health

   # Check Redis performance
   make check-redis-health
   ```

2. **Common Causes and Solutions**
   - **High Memory Usage**: Restart service, check for memory leaks
   - **Database Slow Queries**: Check `pg_stat_statements`, optimize queries
   - **Redis High Latency**: Check memory usage, consider scaling

#### Health Check Failures

1. **Component Health Diagnosis**
   ```bash
   # Database health
   curl http://localhost:13370/health/detailed | jq '.db'

   # Redis health
   curl http://localhost:13370/memory/health | jq '.redis'

   # Memory service health
   curl http://localhost:13370/memory/health | jq '.memory_service'
   ```

2. **Recovery Procedures**
   - **Database Issues**: Check connection pool, restart PgBouncer
   - **Redis Issues**: Clear cache, restart Redis service
   - **Memory Service**: Check dependencies, restart service

### MEDIUM Alerts

**Response Time**: Within 1 hour
**Escalation**: Team notification

#### Warning Thresholds

1. **Monitor Trend**
   ```bash
   # Check metrics trends
   curl http://localhost:13370/metrics | grep -E "(error_rate|response_time)"

   # Check system resources
   container stats --no-stream
   ```

2. **Preventive Actions**
   - Scale resources before hitting critical thresholds
   - Optimize queries showing degradation
   - Clear caches if memory pressure increases

---

## Health Check Troubleshooting

### Database Health Issues

#### Symptoms
- Connection timeouts
- High connection pool usage
- Slow query responses

#### Diagnosis
```bash
# Check database connectivity
curl http://localhost:13370/health/detailed | jq '.db'

# Check connection pool status
curl http://localhost:13370/metrics | grep pg_stat_database

# Check slow queries
docker exec -it nina-db psql -U postgres -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

#### Solutions
```bash
# Restart PgBouncer
container restart nina-pgbouncer

# Check database connections
docker exec -it nina-db psql -U postgres -c "
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;"

# Kill long-running queries if needed
docker exec -it nina-db psql -U postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
```

### Redis Health Issues

#### Symptoms
- High latency
- Connection failures
- Low cache hit rates

#### Diagnosis
```bash
# Check Redis health
curl http://localhost:13370/memory/health | jq '.redis'

# Check Redis info
docker exec -it nina-redis redis-cli INFO memory

# Check slow operations
docker exec -it nina-redis redis-cli SLOWLOG GET 10
```

#### Solutions
```bash
# Clear Redis cache (if needed)
docker exec -it nina-redis redis-cli FLUSHDB

# Restart Redis
container restart nina-redis

# Check memory usage
docker exec -it nina-redis redis-cli INFO memory | grep used_memory_human
```

### Application Health Issues

#### Symptoms
- HTTP 5xx errors
- High response times
- Memory leaks

#### Diagnosis
```bash
# Check application logs
container logs nina-api --tail=200 | grep ERROR

# Check memory usage
container stats nina-api --no-stream

# Check HTTP metrics
curl http://localhost:13370/metrics | grep http_requests_total
```

#### Solutions
```bash
# Restart application
container restart nina-api

# Scale resources (if using Kubernetes)
kubectl scale deployment nina-api --replicas=3

# Check for memory leaks
curl http://localhost:13370/metrics | grep process_resident_memory_bytes
```

---

## SLO Incident Management

### Incident Classification

#### Severity 1 (Critical)
- Multiple SLOs violated
- Service unavailable
- Revenue impact

#### Severity 2 (High)
- Single SLO violated
- Performance degradation
- User experience impacted

#### Severity 3 (Medium)
- Warning thresholds exceeded
- Risk of SLO violation
- Proactive intervention needed

### Incident Response Playbook

#### 1. Detection (0-5 minutes)
```bash
# Check SLO dashboard
curl http://localhost:13370/monitoring/slo

# Check active alerts
curl http://localhost:13370/monitoring/alerts?severity=critical

# Get monitoring status
curl http://localhost:13370/monitoring/status
```

#### 2. Assessment (5-15 minutes)
- Identify affected SLOs
- Determine user impact
- Estimate time to resolution

#### 3. Containment (15-30 minutes)
- Implement quick fixes
- Scale resources if needed
- Communicate with stakeholders

#### 4. Resolution (30 minutes - 2 hours)
- Fix root cause
- Verify SLO recovery
- Update monitoring if needed

#### 5. Post-Incident (2-24 hours)
- Document root cause
- Update runbooks
- Implement preventive measures

### SLO Recovery Procedures

#### Availability Recovery
```bash
# Check service uptime
curl -f http://localhost:13370/health

# Restart failed services
for service in nina-api nina-pgbouncer; do
    if ! container ps | grep -q $service; then
        container start $service
    fi
done

# Verify recovery
curl http://localhost:13370/monitoring/slo | jq '.current.availability'
```

#### Response Time Recovery
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:13370/health

# Scale application
container run -d --name nina-api-2 -p 13371:13370 nina-api:arm64

# Load balance (nginx/haproxy configuration needed)
```

#### Error Rate Recovery
```bash
# Check error patterns
container logs nina-api --tail=100 | grep ERROR

# Restart application
container restart nina-api

# Clear problematic caches
curl -X POST http://localhost:13370/monitoring/clear-cache
```

---

## Monitoring System Maintenance

### Daily Checks

#### Morning Health Check
```bash
# System health
make health-check

# SLO status
curl http://localhost:13370/monitoring/slo

# Active alerts
curl http://localhost:13370/monitoring/alerts

# Monitoring system status
curl http://localhost:13370/monitoring/status
```

#### Metrics Verification
```bash
# Check Prometheus metrics
curl http://localhost:13370/metrics | head -20

# Verify metric collection
curl http://localhost:13370/metrics | grep slo_

# Check alert rule evaluation
curl http://localhost:13370/monitoring/alerts/stats
```

### Weekly Maintenance

#### Performance Review
```bash
# Export weekly metrics
curl "http://localhost:13370/monitoring/slo/summary" > weekly-slo-report.json

# Review dashboard performance
curl http://localhost:13370/monitoring/dashboards | jq '.[] | {name, panel_count}'

# Check alert patterns
curl http://localhost:13370/monitoring/alerts/stats | jq '.last_24h'
```

#### System Updates
```bash
# Update dashboard configurations
curl -X POST http://localhost:13370/monitoring/dashboards/reload

# Clear old monitoring data
curl -X POST http://localhost:13370/monitoring/cleanup?days=7

# Restart monitoring services
curl -X POST http://localhost:13370/monitoring/restart
```

### Monthly Maintenance

#### Capacity Planning
```bash
# Export monthly metrics
curl "http://localhost:13370/monitoring/slo?window=7d" > monthly-slo-report.json

# Review resource utilization
container stats --no-stream | grep nina

# Plan capacity upgrades based on trends
```

#### System Health Audit
```bash
# Comprehensive health check
make comprehensive-health-check

# Review all configurations
curl http://localhost:13370/monitoring/config

# Update documentation
curl http://localhost:13370/monitoring/docs > current-docs.md
```

---

## Grafana Dashboard Operations

### Dashboard Management

#### Import Dashboards
```bash
# Export dashboard JSON
curl http://localhost:13370/monitoring/dashboards/slo-compliance > slo-dashboard.json

# Import to Grafana (via API or UI)
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @slo-dashboard.json \
  http://grafana.local/api/dashboards/db
```

#### Update Dashboards
```bash
# Get current dashboard list
curl http://localhost:13370/monitoring/dashboards

# Update specific dashboard
curl -X PUT \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @updated-dashboard.json \
  http://grafana.local/api/dashboards/db/uid
```

### Data Source Configuration

#### Prometheus Data Source
```json
{
  "name": "Ninaivalaigal-Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true
}
```

#### Alert Data Source
```json
{
  "name": "Ninaivalaigal-Alerts",
  "type": "alertmanager",
  "url": "http://alertmanager:9093",
  "access": "proxy"
}
```

---

## Emergency Procedures

### Complete Service Outage

#### Immediate Response
```bash
# Check all containers
container ps -a | grep nina

# Start critical services
container start nina-db nina-redis nina-pgbouncer nina-api

# Verify basic connectivity
curl -f http://localhost:13370/health

# Check data integrity
docker exec -it nina-db pg_isready -U postgres
```

#### Data Recovery
```bash
# Check database backups
ls -la /backups/postgres/

# Restore latest backup if needed
docker exec -it nina-db pg_restore -U postgres -d ninaivalaigal /backups/latest.dump

# Verify data consistency
docker exec -it nina-db psql -U postgres -c "SELECT count(*) FROM users;"
```

### Security Incident

#### Immediate Actions
```bash
# Isolate affected systems
container stop nina-api

# Preserve evidence
container logs nina-api > incident-logs-$(date +%Y%m%d).log

# Check for unauthorized access
docker exec -it nina-db psql -U postgres -c "
SELECT * FROM audit_log
WHERE created_at > now() - interval '1 hour';"
```

#### Recovery
```bash
# Rotate secrets
make secrets-rotate

# Update authentication
curl -X POST http://localhost:13370/auth/rotate-keys

# Restore service with hardening
container start nina-api
```

### Data Corruption

#### Detection
```bash
# Check database integrity
docker exec -it nina-db pg_dump -U postgres ninaivalaigal | head -20

# Verify Redis data
docker exec -it nina-redis redis-cli DBSIZE

# Check application errors
container logs nina-api --tail=100 | grep -i corruption
```

#### Recovery
```bash
# Stop all services
container stop nina-api nina-pgbouncer

# Restore from known good backup
docker exec -it nina-db pg_restore -U postgres -d ninaivalaigal /backups/good-backup.dump

# Clear corrupted cache
docker exec -it nina-redis redis-cli FLUSHALL

# Restart services
container start nina-pgbouncer nina-api
```

---

## Contact Information

### Primary Contacts
- **On-call Engineer**: [Phone/Slack]
- **Engineering Lead**: [Email/Slack]
- **DevOps Team**: [Email/Slack]

### Escalation Contacts
- **CTO**: [Email/Phone]
- **VP Engineering**: [Email/Phone]

### External Services
- **PagerDuty**: https://ninaivalaigal.pagerduty.com
- **Grafana**: https://grafana.ninaivalaigal.com
- **Prometheus**: https://prometheus.ninaivalaigal.com

---

## Appendices

### Useful Commands

#### Quick Health Check
```bash
make health-check && curl http://localhost:13370/monitoring/status
```

#### Alert Management
```bash
# List active alerts
curl http://localhost:13370/monitoring/alerts

# Resolve alert
curl -X POST http://localhost:13370/monitoring/alerts/{id}/resolve

# Trigger test alert
curl -X POST "http://localhost:13370/monitoring/slo/alert/trigger?metric_name=availability&current_value=0.99"
```

#### System Restart
```bash
# Graceful restart
make stack-restart

# Force restart
container stop $(container ps -q -f name=nina) && \
container start $(container ps -a -q -f name=nina)
```

### Environment Variables

#### Alerting Configuration
```bash
export PAGERDUTY_INTEGRATION_KEY="your-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/your-webhook"
export EMAIL_SMTP_HOST="smtp.company.com"
export ALERT_WEBHOOK_URL="https://your-webhook-endpoint.com"
```

#### Monitoring Configuration
```bash
export SLO_CHECK_INTERVAL_SECONDS=60
export ALERT_COOLDOWN_MINUTES=15
export HEALTH_CHECK_TIMEOUT_SECONDS=30
```

### Monitoring Scripts

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh

echo "=== System Health Check ==="
make health-check

echo -e "\n=== SLO Status ==="
curl -s http://localhost:13370/monitoring/slo | jq '.overall_status'

echo -e "\n=== Active Alerts ==="
curl -s http://localhost:13370/monitoring/alerts | jq '. | length'

echo -e "\n=== Monitoring Status ==="
curl -s http://localhost:13370/monitoring/status | jq '.monitoring_active'
```

#### Alert Resolution Script
```bash
#!/bin/bash
# resolve-alert.sh

ALERT_ID=$1
if [ -z "$ALERT_ID" ]; then
    echo "Usage: $0 <alert-id>"
    exit 1
fi

echo "Resolving alert: $ALERT_ID"
curl -X POST "http://localhost:13370/monitoring/alerts/$ALERT_ID/resolve"
echo "Alert resolution initiated"
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-01
**Next Review**: 2025-12-01
**Approved by**: DevOps Team Lead
