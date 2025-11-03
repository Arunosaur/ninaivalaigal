# Platform Stability Operations Runbook

**SPEC**: SPEC-051 - Platform Stability & Developer Experience
**Version**: 1.0
**Last Updated**: November 1, 2025
**Owner**: Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Monitoring & Alerting](#monitoring--alerting)
4. [Common Operations](#common-operations)
5. [Incident Response](#incident-response)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Overview

### Purpose
This runbook provides operational procedures for the platform stability monitoring system, including container health monitoring, circuit breakers, performance baselines, and alerting.

### System Components
- **Container Health Monitor**: Monitors 8 platform services every 30 seconds
- **Circuit Breakers**: Prevents cascading failures across services
- **Performance Baselines**: Tracks metrics against established baselines
- **Platform Alerting**: Generates alerts for unhealthy conditions
- **Grafana Dashboard**: Visualizes platform health and metrics

### Monitored Services
1. Core API (port 8000)
2. Memory Service (port 13393)
3. Graph Service (port 8002)
4. Business Service (port 8003)
5. Upload API (port 8004)
6. Redis (port 6379)
7. PostgreSQL (port 5432)
8. PgBouncer (port 6432)

---

## Architecture

### Monitoring Flow
```
Container Health Monitor (30s interval)
    ↓
Health Checks (parallel, async)
    ↓
Health Status Cache
    ↓
Platform Alerter (60s interval)
    ↓
Alert Manager → Notifications
```

### Data Flow
```
Service → Health Endpoint → Monitor → Cache → API → Dashboard
                                    ↓
                              Alert Manager → PagerDuty/Slack
```

---

## Monitoring & Alerting

### Health Check Endpoints

#### Platform Health API
```bash
# Get all containers health
curl http://localhost:8000/platform/health/containers

# Get specific service
curl http://localhost:8000/platform/health/containers/core-api

# Get health summary
curl http://localhost:8000/platform/health/summary

# Get dependencies
curl http://localhost:8000/platform/health/dependencies

# Trigger manual check
curl -X POST http://localhost:8000/platform/health/check
```

### Alert Types

#### 1. Service Unhealthy (CRITICAL)
**Trigger**: Service health check fails
**Response Time**: Immediate
**Action**: See [Service Down](#service-down)

#### 2. Service Degraded (WARNING)
**Trigger**: Service responds with errors
**Response Time**: 15 minutes
**Action**: See [Service Degraded](#service-degraded)

#### 3. Circuit Breaker Open (CRITICAL)
**Trigger**: Circuit breaker opens after failures
**Response Time**: Immediate
**Action**: See [Circuit Breaker Tripped](#circuit-breaker-tripped)

#### 4. Performance Critical (CRITICAL)
**Trigger**: Metric exceeds 2x baseline
**Response Time**: 15 minutes
**Action**: See [Performance Degradation](#performance-degradation)

#### 5. Performance Warning (WARNING)
**Trigger**: Metric exceeds 1.5x baseline
**Response Time**: 1 hour
**Action**: Monitor and investigate

### Grafana Dashboard

**URL**: `http://localhost:3000/d/platform-stability`

**Panels**:
- Platform Health Overview
- Service Health Status
- Circuit Breaker States
- Service Response Times
- Memory Usage
- Service Uptime
- Dependency Health Matrix
- Active Alerts
- Performance Baseline Deviations

---

## Common Operations

### Check Platform Health

```bash
# Quick health check
curl http://localhost:8000/platform/health/summary | jq

# Expected output:
{
  "overall_status": "healthy",
  "timestamp": "2025-11-01T20:00:00Z",
  "summary": {
    "total_services": 8,
    "status_counts": {
      "healthy": 8,
      "degraded": 0,
      "unhealthy": 0,
      "unknown": 0
    }
  },
  "unhealthy_services": []
}
```

### Check Specific Service

```bash
# Check Core API
curl http://localhost:8000/platform/health/containers/core-api | jq

# Expected output:
{
  "service": "core-api",
  "status": "healthy",
  "response_time_ms": 45.2,
  "cpu_percent": 28.5,
  "memory_mb": 245.8,
  "uptime_seconds": 86400,
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "pgbouncer": "healthy"
  },
  "last_check": "2025-11-01T20:00:00Z"
}
```

### Check Circuit Breakers

```bash
# Get circuit breaker status (via Python)
python3 << 'EOF'
from lib.observability.circuit_breaker import get_circuit_breaker_registry
registry = get_circuit_breaker_registry()
status = registry.get_all_status()
for service, breaker_status in status.items():
    print(f"{service}: {breaker_status['state']} (failures: {breaker_status['failure_count']})")
EOF
```

### Reset Circuit Breaker

```bash
# Reset specific circuit breaker (via Python)
python3 << 'EOF'
from lib.observability.circuit_breaker import get_circuit_breaker_registry
registry = get_circuit_breaker_registry()
breaker = registry.get('redis')
if breaker:
    breaker.reset()
    print(f"Circuit breaker for redis reset")
EOF
```

### Check Performance Baselines

```bash
# Get all baselines (via Python)
python3 << 'EOF'
from lib.observability.performance_baselines import get_baseline_manager
manager = get_baseline_manager()
baselines = manager.get_all_baselines()
import json
print(json.dumps(baselines, indent=2))
EOF
```

---

## Incident Response

### Service Down

**Symptoms**:
- Service health check fails
- Circuit breaker opens
- CRITICAL alert generated

**Immediate Actions**:
1. Check service logs
   ```bash
   # For Docker containers
   docker logs <container_name> --tail 100

   # For systemd services
   journalctl -u <service_name> -n 100
   ```

2. Check service status
   ```bash
   # Docker
   docker ps -a | grep <service_name>

   # Systemd
   systemctl status <service_name>
   ```

3. Attempt restart
   ```bash
   # Docker
   docker restart <container_name>

   # Systemd
   systemctl restart <service_name>
   ```

4. Verify health after restart
   ```bash
   curl http://localhost:8000/platform/health/containers/<service>
   ```

**Escalation**:
- If restart fails: Page on-call engineer
- If multiple services down: Declare incident

### Service Degraded

**Symptoms**:
- Service responds but with errors
- Increased response times
- WARNING alert generated

**Investigation Steps**:
1. Check error rates in logs
2. Check resource utilization (CPU, memory, disk)
3. Check database connection pool
4. Check Redis connection
5. Review recent deployments

**Actions**:
1. If resource constrained: Scale up
2. If database issues: Check connection pool, slow queries
3. If Redis issues: Check memory usage, eviction policy
4. If recent deployment: Consider rollback

### Circuit Breaker Tripped

**Symptoms**:
- Circuit breaker state is OPEN
- Service calls being blocked
- CRITICAL alert generated

**Investigation Steps**:
1. Check why circuit opened
   ```bash
   # Get circuit breaker status
   curl http://localhost:8000/platform/health/containers/<service>
   ```

2. Check target service health
3. Review failure logs

**Actions**:
1. Fix underlying service issue
2. Wait for automatic recovery (60 seconds)
3. Or manually reset circuit breaker (see above)
4. Monitor for re-opening

### Performance Degradation

**Symptoms**:
- Response times exceed baseline
- Memory usage high
- CRITICAL or WARNING alert

**Investigation Steps**:
1. Check current metrics vs baseline
   ```bash
   curl http://localhost:8000/platform/health/performance | jq
   ```

2. Check for:
   - Increased traffic
   - Slow database queries
   - Memory leaks
   - CPU bottlenecks

**Actions**:
1. If traffic spike: Scale horizontally
2. If slow queries: Optimize or add indexes
3. If memory leak: Restart service, investigate code
4. If CPU bound: Scale vertically or optimize code

---

## Troubleshooting

### No Health Data Available

**Symptoms**: Dashboard shows no data or "No data"

**Checks**:
1. Verify Core API is running
   ```bash
   curl http://localhost:8000/health
   ```

2. Check monitoring initialization
   ```bash
   # Check Core API logs for:
   # "✅ Container health monitoring started"
   # "✅ Platform stability alerting started"
   ```

3. Verify services are accessible
   ```bash
   # Test each service endpoint
   curl http://localhost:8000/health
   curl http://localhost:13393/health
   # etc.
   ```

**Resolution**:
- Restart Core API if monitoring not initialized
- Check network connectivity to services
- Verify service ports are correct

### False Positive Alerts

**Symptoms**: Alerts for healthy services

**Checks**:
1. Verify service is actually healthy
2. Check alert cooldown period (5 minutes)
3. Review baseline thresholds

**Resolution**:
1. Adjust baseline thresholds if too sensitive
2. Increase alert cooldown if needed
3. Update performance baselines based on real data

### Circuit Breaker Stuck Open

**Symptoms**: Circuit breaker won't close despite healthy service

**Checks**:
1. Verify service is truly healthy
2. Check success threshold (default: 2 successes)
3. Review recovery timeout (default: 60 seconds)

**Resolution**:
1. Manually reset circuit breaker
2. Adjust success threshold if too high
3. Check for intermittent failures

### High Memory Usage

**Symptoms**: Monitoring system using excessive memory

**Checks**:
1. Check health cache size
2. Check number of monitored services
3. Review alert history retention

**Resolution**:
1. Clear health cache if needed
2. Reduce monitoring frequency if appropriate
3. Implement cache eviction policy

---

## Maintenance

### Update Performance Baselines

```bash
# Establish new baseline (via Python)
python3 << 'EOF'
from lib.observability.performance_baselines import get_baseline_manager
manager = get_baseline_manager()

# Update baseline for a service
manager.establish_baseline(
    service="core-api",
    metric="response_time_ms",
    baseline_value=55.0,  # New baseline
    unit="ms",
    sample_size=1000
)
print("Baseline updated")
EOF
```

### Adjust Alert Thresholds

Edit `lib/observability/platform_alerting.py`:
```python
# Change check interval
self.check_interval = 120  # Check every 2 minutes instead of 1

# Change alert cooldown
if time_since_alert < 600:  # 10 minutes instead of 5
    return
```

### Add New Service to Monitoring

1. Add service endpoint to `container_health.py`:
   ```python
   self.service_endpoints = {
       # ... existing services ...
       ServiceType.NEW_SERVICE: "http://localhost:PORT/health"
   }
   ```

2. Add service dependencies:
   ```python
   self.service_dependencies = {
       # ... existing dependencies ...
       ServiceType.NEW_SERVICE: [ServiceType.POSTGRES, ServiceType.REDIS]
   }
   ```

3. Register circuit breaker in `circuit_breaker.py`:
   ```python
   services = [
       # ... existing services ...
       "new-service"
   ]
   ```

4. Establish performance baseline:
   ```python
   DEFAULT_BASELINES = {
       # ... existing baselines ...
       "new-service": {
           "response_time_ms": {"value": 50, "unit": "ms"},
           "cpu_percent": {"value": 30, "unit": "%"},
           "memory_mb": {"value": 256, "unit": "MB"}
       }
   }
   ```

5. Restart Core API

### Backup and Restore

#### Backup Performance Baselines
```bash
cp performance_baselines.json performance_baselines.backup.json
```

#### Restore Performance Baselines
```bash
cp performance_baselines.backup.json performance_baselines.json
# Restart Core API
```

### Monitoring System Health

Monitor the monitoring system itself:
```bash
# Check monitoring overhead
ps aux | grep python | grep main.py

# Check memory usage
docker stats core-api

# Check log volume
du -sh /var/log/core-api/
```

---

## Emergency Contacts

- **Platform Team Lead**: platform-lead@company.com
- **On-Call Engineer**: PagerDuty rotation
- **Slack Channel**: #platform-alerts
- **Incident Management**: incidents@company.com

---

## Related Documentation

- [SPEC-051: Platform Stability & Developer Experience](/specs/051-platform-stability/spec.md)
- [Troubleshooting Guide](./PLATFORM_STABILITY_TROUBLESHOOTING.md)
- [Architecture Documentation](../architecture/PLATFORM_MONITORING.md)
- [API Documentation](../api/CONTAINER_HEALTH_API.md)

---

**Document Version**: 1.0
**Last Review**: November 1, 2025
**Next Review**: December 1, 2025
