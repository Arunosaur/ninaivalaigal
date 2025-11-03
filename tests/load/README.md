# Load Testing for Platform Stability Monitoring

This directory contains load testing scripts and utilities for validating the platform stability monitoring system (US#407).

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r tests/load/requirements.txt

# Install system dependencies (macOS)
brew install jq

# Or on Linux
sudo apt-get install jq
```

### 2. Start the Platform

```bash
# Ensure all services are running
make stack-up

# Verify services are healthy
make health-check
```

### 3. Run Load Tests

```bash
# Normal load test (100 users, 30 minutes)
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 30m \
  --host http://localhost:8000 \
  --html reports/load_test_normal.html

# Peak load test (500 users, 15 minutes)
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 500 \
  --spawn-rate 100 \
  --run-time 15m \
  --host http://localhost:8000 \
  --user-classes BurstTrafficUser \
  --html reports/load_test_peak.html

# Circuit breaker validation
./tests/load/circuit_breaker_test.sh redis
```

## Test Scenarios

### 1. Normal Load Test
**File**: `test_platform_monitoring_load.py` (PlatformMonitoringUser)

Simulates realistic production traffic with weighted task distribution:
- 10x: Platform health summary checks
- 5x: All containers health checks
- 4x: Service dependency checks
- 3x: Specific service health checks
- 2x: Performance metrics checks
- 2x: Service uptime checks
- 1x: Manual health check triggers

**Usage**:
```bash
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 30m \
  --host http://localhost:8000
```

**Expected Results**:
- CPU overhead: <5%
- Memory usage: <100MB
- Response time p95: <100ms
- No false positive alerts

### 2. Peak Load Test
**File**: `test_platform_monitoring_load.py` (BurstTrafficUser)

Simulates burst traffic patterns with minimal wait times:
- Rapid-fire health checks
- Short wait times (0.1-0.5s)
- High request rate

**Usage**:
```bash
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 500 \
  --spawn-rate 100 \
  --run-time 15m \
  --host http://localhost:8000 \
  --user-classes BurstTrafficUser
```

**Expected Results**:
- CPU overhead: <10%
- Memory usage: <150MB
- Response time p95: <200ms
- System remains stable

### 3. Stress Test
**File**: `test_platform_monitoring_load.py` (StressTestUser)

Finds breaking points with aggressive request patterns:
- Minimal wait times (0.05-0.2s)
- Very high request rate
- Sustained load

**Usage**:
```bash
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 1000 \
  --spawn-rate 200 \
  --run-time 10m \
  --host http://localhost:8000 \
  --user-classes StressTestUser
```

**Expected Results**:
- Identify maximum capacity
- Graceful degradation
- No crashes or data loss

### 4. Realistic Traffic Pattern
**File**: `test_platform_monitoring_load.py` (RealisticTrafficUser)

Production-like traffic distribution:
- 40%: Health summary checks
- 20%: Container health checks
- 15%: Dependency checks
- 10%: Performance metrics
- 10%: Specific service checks
- 5%: Other operations

**Usage**:
```bash
locust -f tests/load/test_platform_monitoring_load.py \
  --headless \
  --users 200 \
  --spawn-rate 20 \
  --run-time 1h \
  --host http://localhost:8000 \
  --user-classes RealisticTrafficUser
```

**Expected Results**:
- Realistic baseline metrics
- Accurate performance data
- Production-ready validation

### 5. Circuit Breaker Test
**File**: `circuit_breaker_test.sh`

Validates circuit breaker behavior:
- Opens after 5 failures
- Enters half-open after 60s
- Closes after 2 successes
- Blocks requests when open

**Usage**:
```bash
# Test specific service
./tests/load/circuit_breaker_test.sh redis

# Test with custom API URL
API_URL=http://localhost:8000 ./tests/load/circuit_breaker_test.sh core-api
```

**Expected Results**:
- All 4 tests pass
- State transitions correct
- Request blocking works
- Recovery automatic

## Interactive Testing

For interactive load testing with web UI:

```bash
# Start Locust web interface
locust -f tests/load/test_platform_monitoring_load.py \
  --host http://localhost:8000

# Open browser to http://localhost:8089
# Configure users and spawn rate in UI
# Monitor real-time metrics and charts
```

## Monitoring During Tests

### 1. System Resources

```bash
# Monitor CPU and memory
watch -n 1 'docker stats --no-stream'

# Monitor specific container
docker stats core-api --no-stream

# System-wide monitoring
htop
```

### 2. Application Metrics

```bash
# Health summary
watch -n 5 'curl -s http://localhost:8000/platform/health/summary | jq'

# Performance metrics
watch -n 5 'curl -s http://localhost:8000/platform/health/performance | jq'

# Active alerts
watch -n 10 'curl -s http://localhost:8000/alerts/active | jq'
```

### 3. Prometheus Metrics

```bash
# Scrape metrics
curl http://localhost:8000/metrics

# Query specific metrics
curl 'http://localhost:9090/api/v1/query?query=platform_health_check_duration_seconds'
```

### 4. Grafana Dashboard

```bash
# Open Grafana
open http://localhost:3000

# Import dashboard
# Upload: grafana/dashboards/platform_stability.json
```

## Results Analysis

### 1. Locust Reports

After each test, Locust generates an HTML report with:
- Request statistics (count, failures, response times)
- Response time distribution charts
- Requests per second over time
- Failure rate over time

**Location**: `reports/load_test_*.html`

### 2. Custom Metrics

Extract custom metrics from test output:

```bash
# Parse Locust output
grep "Total requests" locust.log
grep "Average response time" locust.log
grep "Requests per second" locust.log

# Analyze slow requests
grep "Slow request" locust.log | wc -l

# Count failures
grep "Request failed" locust.log | wc -l
```

### 3. Performance Baselines

Compare results against baselines:

```bash
# Get current baselines
curl http://localhost:8000/platform/health/performance | jq '.baselines'

# Compare with test results
# Update baselines if needed
```

## Success Criteria

### Performance
- ✅ Monitoring overhead <5% CPU (normal load)
- ✅ Monitoring overhead <10% CPU (peak load)
- ✅ Memory usage <100MB (normal), <150MB (peak)
- ✅ Health check p95 <100ms (normal), <200ms (peak)
- ✅ Alert generation <500ms

### Reliability
- ✅ Failure detection <30 seconds
- ✅ Recovery detection <60 seconds
- ✅ Circuit breaker opens after 5 failures
- ✅ Circuit breaker closes after 2 successes
- ✅ No false positives under normal load

### Accuracy
- ✅ False positive rate <1%
- ✅ True positive rate >99%
- ✅ Alert deduplication working (5-minute cooldown)
- ✅ Performance baselines accurate

## Troubleshooting

### High CPU Usage

```bash
# Check monitoring overhead
docker stats core-api

# Reduce monitoring frequency if needed
# Edit: lib/observability/container_health_monitor.py
# Increase check_interval from 30 to 60 seconds
```

### High Memory Usage

```bash
# Check for memory leaks
ps aux | grep python | grep main.py

# Monitor memory over time
watch -n 30 'ps aux | grep python | grep main.py'

# Check health cache size
curl http://localhost:8000/platform/health/summary | jq '.cache_size'
```

### Slow Response Times

```bash
# Check database connections
curl http://localhost:8000/health/detailed | jq '.database'

# Check Redis connections
curl http://localhost:8000/health/detailed | jq '.redis'

# Monitor query performance
# Check PostgreSQL logs
docker logs nv-db | grep "duration:"
```

### False Positive Alerts

```bash
# Check alert history
curl http://localhost:8000/alerts/history | jq

# Tune alert thresholds
# Edit: lib/observability/performance_baselines.py
# Adjust warning_threshold and critical_threshold

# Update baselines with real data
# Use collected metrics from load tests
```

## Best Practices

1. **Start Small**: Begin with low user counts and gradually increase
2. **Monitor Continuously**: Watch system resources during tests
3. **Collect Baselines**: Use realistic traffic to establish baselines
4. **Test Failures**: Simulate failures to validate detection
5. **Document Results**: Save reports and metrics for comparison
6. **Iterate**: Tune thresholds based on test results
7. **Automate**: Integrate load tests into CI/CD pipeline

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r tests/load/requirements.txt

      - name: Start services
        run: |
          make stack-up
          sleep 30

      - name: Run load test
        run: |
          locust -f tests/load/test_platform_monitoring_load.py \
            --headless \
            --users 100 \
            --spawn-rate 10 \
            --run-time 10m \
            --host http://localhost:8000 \
            --html load_test_report.html

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load_test_report.html
```

## Related Documentation

- [US#407 Load Testing Plan](../../docs/operations/US407_LOAD_TESTING_PLAN.md)
- [Operations Runbook](../../docs/operations/PLATFORM_STABILITY_RUNBOOK.md)
- [Troubleshooting Guide](../../docs/operations/PLATFORM_STABILITY_TROUBLESHOOTING.md)
- [Final Completion Summary](../../docs/implementation/US407_FINAL_COMPLETION.md)

## Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the operations runbook
3. Contact Developer C (US#407 owner)
4. Open an issue in the project repository
