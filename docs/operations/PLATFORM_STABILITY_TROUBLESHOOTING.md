# Platform Stability Troubleshooting Guide

**SPEC**: SPEC-051 - Platform Stability & Developer Experience
**Version**: 1.0
**Last Updated**: November 1, 2025

---

## Quick Reference

| Symptom | Likely Cause | Quick Fix | Section |
|---------|--------------|-----------|---------|
| No health data | Monitoring not started | Restart Core API | [No Health Data](#no-health-data) |
| All services unhealthy | Network issue | Check connectivity | [Network Issues](#network-issues) |
| Circuit breaker stuck open | Service intermittent | Manual reset | [Circuit Breaker Issues](#circuit-breaker-issues) |
| High memory usage | Cache not clearing | Restart monitoring | [Performance Issues](#performance-issues) |
| False alerts | Baseline too tight | Adjust thresholds | [Alert Issues](#alert-issues) |
| Slow dashboard | Too much data | Reduce time range | [Dashboard Issues](#dashboard-issues) |

---

## No Health Data

### Symptom
- Dashboard shows "No data"
- API returns empty results
- No metrics in Prometheus

### Diagnosis

**Step 1**: Check if Core API is running
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status": "healthy", "service": "core-api", "version": "1.0.0"}`

**If fails**: Core API is down
- Check Docker: `docker ps | grep core-api`
- Check logs: `docker logs core-api --tail 50`
- Restart: `docker restart core-api`

**Step 2**: Check monitoring initialization
```bash
docker logs core-api | grep "monitoring"
```

**Expected logs**:
```
✅ Circuit breakers initialized
✅ Container health monitoring started
✅ Platform stability alerting started
```

**If missing**: Monitoring failed to start
- Check for initialization errors in logs
- Verify Redis connection (monitoring uses Redis)
- Restart Core API

**Step 3**: Check individual service health
```bash
# Test each service
for port in 8000 13393 8002 8003 8004; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/health || echo "FAILED"
done
```

**If services fail**: Services are down or unreachable
- Start missing services
- Check network connectivity
- Verify port configuration

### Resolution

**Quick Fix**:
```bash
# Restart Core API
docker restart core-api

# Wait 30 seconds for initialization
sleep 30

# Verify monitoring started
curl http://localhost:8000/platform/health/summary
```

**Permanent Fix**:
- Ensure all services start before Core API
- Add health check retries in monitoring code
- Implement graceful degradation

---

## Network Issues

### Symptom
- Multiple services showing as unhealthy
- Timeout errors in logs
- Intermittent connectivity

### Diagnosis

**Step 1**: Check network connectivity
```bash
# Ping services
ping -c 3 localhost

# Check DNS resolution
nslookup localhost

# Check port accessibility
netstat -tuln | grep -E '8000|13393|8002|8003|8004|6379|5432'
```

**Step 2**: Check Docker network
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect bridge

# Check container connectivity
docker exec core-api ping -c 3 memory-service
```

**Step 3**: Check firewall rules
```bash
# Check iptables
sudo iptables -L -n

# Check firewalld
sudo firewall-cmd --list-all
```

### Resolution

**Docker Network Issues**:
```bash
# Recreate Docker network
docker network create platform-network

# Reconnect containers
docker network connect platform-network core-api
docker network connect platform-network memory-service
# etc.
```

**Firewall Issues**:
```bash
# Allow required ports
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --add-port=13393/tcp --permanent
# etc.
sudo firewall-cmd --reload
```

**DNS Issues**:
```bash
# Add to /etc/hosts
echo "127.0.0.1 memory-service" | sudo tee -a /etc/hosts
```

---

## Circuit Breaker Issues

### Symptom
- Circuit breaker stuck in OPEN state
- Service calls being blocked
- "Circuit breaker is OPEN" errors

### Diagnosis

**Step 1**: Check circuit breaker status
```bash
curl http://localhost:8000/platform/health/containers/<service> | jq
```

**Look for**:
- `circuit_breaker_state`: "open"
- `failure_count`: High number
- `last_failure_time`: Recent timestamp

**Step 2**: Check target service health
```bash
# Direct health check
curl http://localhost:<port>/health

# Check service logs
docker logs <service> --tail 100
```

**Step 3**: Review failure pattern
```bash
# Check monitoring logs
docker logs core-api | grep "circuit_breaker"

# Look for:
# - Repeated failures
# - Timeout patterns
# - Connection errors
```

### Resolution

**If Service is Healthy**:
```bash
# Manual circuit breaker reset
python3 << 'EOF'
from lib.observability.circuit_breaker import get_circuit_breaker_registry
registry = get_circuit_breaker_registry()
breaker = registry.get('<service-name>')
breaker.reset()
print(f"Circuit breaker reset for <service-name>")
EOF
```

**If Service is Unhealthy**:
1. Fix the underlying service issue
2. Wait for automatic recovery (60 seconds)
3. Monitor for re-opening

**If Circuit Keeps Opening**:
```python
# Adjust thresholds in circuit_breaker.py
registry.register(
    name="service-name",
    failure_threshold=10,  # Increase from 5
    recovery_timeout=120,  # Increase from 60
    success_threshold=3    # Increase from 2
)
```

**Prevention**:
- Implement proper retry logic in services
- Add exponential backoff
- Improve error handling
- Monitor service dependencies

---

## Performance Issues

### Symptom
- High CPU usage by monitoring
- High memory usage
- Slow health checks
- Dashboard lag

### Diagnosis

**Step 1**: Check resource usage
```bash
# CPU and memory
docker stats core-api

# Process details
ps aux | grep python | grep main.py
```

**Step 2**: Check monitoring overhead
```bash
# Count health checks
docker logs core-api | grep "health_check" | wc -l

# Check cache size
python3 << 'EOF'
from lib.observability.container_health import get_container_health_monitor
monitor = get_container_health_monitor()
print(f"Cached services: {len(monitor.health_cache)}")
EOF
```

**Step 3**: Check alert volume
```bash
# Count alerts
docker logs core-api | grep "alert" | wc -l

# Check alert rate
docker logs core-api | grep "alert" | tail -100
```

### Resolution

**High CPU**:
```python
# Increase check intervals in container_health.py
self.check_interval = 60  # From 30 seconds

# In platform_alerting.py
self.check_interval = 120  # From 60 seconds
```

**High Memory**:
```python
# Implement cache eviction in container_health.py
def _evict_old_cache(self):
    # Remove entries older than 5 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    for service, health in list(self.health_cache.items()):
        if health.last_check < cutoff:
            del self.health_cache[service]
```

**Slow Health Checks**:
```python
# Reduce timeout in container_health.py
self.timeout = 2  # From 5 seconds

# Reduce parallel checks
# Check services in batches instead of all at once
```

**Alert Storm**:
```python
# Increase cooldown in platform_alerting.py
if time_since_alert < 600:  # From 300 (10 minutes)
    return
```

---

## Alert Issues

### Symptom
- Too many alerts
- False positive alerts
- Missing alerts
- Duplicate alerts

### Diagnosis

**Step 1**: Check alert frequency
```bash
# Count alerts by type
docker logs core-api | grep "alert" | \
  awk '{print $NF}' | sort | uniq -c
```

**Step 2**: Check alert accuracy
```bash
# Compare alerts to actual service health
curl http://localhost:8000/platform/health/summary

# Check for discrepancies
```

**Step 3**: Review baseline thresholds
```bash
python3 << 'EOF'
from lib.observability.performance_baselines import get_baseline_manager
manager = get_baseline_manager()
baselines = manager.get_all_baselines()
for service, metrics in baselines.items():
    for metric, baseline in metrics.items():
        print(f"{service}.{metric}: {baseline['baseline_value']} "
              f"(warn: {baseline['threshold_warning']}, "
              f"crit: {baseline['threshold_critical']})")
EOF
```

### Resolution

**Too Many Alerts**:
1. Increase alert cooldown period
2. Adjust baseline thresholds
3. Implement alert aggregation
4. Add alert suppression rules

**False Positives**:
1. Update baselines with real data
2. Increase warning/critical multipliers
3. Add alert confirmation (require N consecutive failures)
4. Implement smart alerting (time-of-day awareness)

**Missing Alerts**:
1. Check alert manager connectivity
2. Verify alert routing rules
3. Check notification channels
4. Review alert conditions

**Duplicate Alerts**:
1. Verify cooldown is working
2. Check alert deduplication logic
3. Review alert key generation
4. Implement alert grouping

**Example: Adjust Baselines**:
```python
from lib.observability.performance_baselines import get_baseline_manager
manager = get_baseline_manager()

# Update baseline with more realistic values
manager.establish_baseline(
    service="core-api",
    metric="response_time_ms",
    baseline_value=75.0,  # Increased from 50
    unit="ms",
    warning_multiplier=2.0,  # Increased from 1.5
    critical_multiplier=3.0,  # Increased from 2.0
    sample_size=10000
)
```

---

## Dashboard Issues

### Symptom
- Dashboard not loading
- No data in panels
- Slow performance
- Missing metrics

### Diagnosis

**Step 1**: Check Grafana status
```bash
# Check if Grafana is running
curl http://localhost:3000/api/health

# Check Grafana logs
docker logs grafana --tail 100
```

**Step 2**: Check Prometheus data source
```bash
# Test Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Check if metrics are being scraped
curl http://localhost:9090/api/v1/targets
```

**Step 3**: Check metric availability
```bash
# Query specific metrics
curl 'http://localhost:9090/api/v1/query?query=container_health_status'
```

### Resolution

**Dashboard Not Loading**:
1. Import dashboard JSON again
2. Check Grafana data source configuration
3. Verify dashboard permissions
4. Clear browser cache

**No Data in Panels**:
1. Verify Prometheus is scraping Core API
2. Check metric names in queries
3. Adjust time range
4. Check data source selection

**Slow Performance**:
1. Reduce time range (use last 1h instead of 24h)
2. Increase refresh interval (use 1m instead of 30s)
3. Reduce number of panels
4. Optimize Prometheus queries

**Missing Metrics**:
1. Verify metrics are being exported
2. Check Prometheus scrape configuration
3. Add missing metrics to exporter
4. Restart Prometheus

**Example: Add Prometheus Scrape Config**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'platform-health'
    scrape_interval: 30s
    static_configs:
      - targets: ['core-api:8000']
    metrics_path: '/metrics'
```

---

## Service-Specific Issues

### Core API Not Responding

**Symptoms**: Health checks timeout, 502/503 errors

**Checks**:
```bash
# Check if running
docker ps | grep core-api

# Check logs
docker logs core-api --tail 100

# Check resource usage
docker stats core-api
```

**Resolution**:
```bash
# Restart
docker restart core-api

# If OOM killed
docker update --memory=1g core-api
docker restart core-api
```

### Memory Service Unhealthy

**Symptoms**: Memory operations fail, circuit breaker opens

**Checks**:
```bash
# Check Rust service
curl http://localhost:13393/health

# Check logs
docker logs memory-service --tail 100

# Check database connection
psql -h localhost -U postgres -d ninaivalaigal -c "SELECT 1"
```

**Resolution**:
```bash
# Restart service
docker restart memory-service

# Check database
# If connection pool exhausted, restart PgBouncer
docker restart pgbouncer
```

### Redis Connection Issues

**Symptoms**: Cache operations fail, degraded performance

**Checks**:
```bash
# Check Redis
redis-cli ping

# Check connections
redis-cli CLIENT LIST | wc -l

# Check memory
redis-cli INFO memory
```

**Resolution**:
```bash
# If too many connections
redis-cli CLIENT KILL TYPE normal

# If memory full
redis-cli FLUSHDB  # Caution: clears cache

# Restart Redis
docker restart redis
```

---

## Debugging Tools

### Enable Debug Logging

```python
# In main.py, add before structlog.configure():
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Health Checks in Real-Time

```bash
# Watch health checks
watch -n 5 'curl -s http://localhost:8000/platform/health/summary | jq'
```

### Trace Circuit Breaker State Changes

```bash
# Monitor circuit breaker logs
docker logs -f core-api | grep "circuit_breaker"
```

### Profile Performance

```python
# Add to container_health.py
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... monitoring code ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Common Error Messages

### "Circuit breaker is OPEN"
**Meaning**: Service has failed threshold times, calls are blocked
**Action**: Check target service health, wait for recovery or manual reset

### "Connection refused"
**Meaning**: Service is not running or not accessible
**Action**: Start service, check network, verify port

### "Timeout"
**Meaning**: Service took too long to respond
**Action**: Check service performance, increase timeout, scale service

### "No baseline established"
**Meaning**: Performance baseline not set for metric
**Action**: Establish baseline or ignore metric

### "Alert cooldown active"
**Meaning**: Alert suppressed due to recent alert
**Action**: Wait for cooldown period or adjust cooldown

---

## Escalation Path

1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Consult operations runbook
3. **Level 3**: Contact platform team in Slack (#platform-alerts)
4. **Level 4**: Page on-call engineer via PagerDuty
5. **Level 5**: Declare incident and escalate to engineering lead

---

## Related Documentation

- [Operations Runbook](./PLATFORM_STABILITY_RUNBOOK.md)
- [SPEC-051: Platform Stability](../specs/051-platform-stability/spec.md)
- [Architecture Documentation](../architecture/PLATFORM_MONITORING.md)

---

**Document Version**: 1.0
**Last Review**: November 1, 2025
**Next Review**: December 1, 2025
