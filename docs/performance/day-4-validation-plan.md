# Day 4 Validation Session Plan

**SPEC-099 Phase 1: Full Stack Validation**
**Participants**: Developer A + Developer C
**Duration**: 2-3 hours
**Goal**: Validate complete performance stack and publish results

## Pre-Session Checklist

### Developer A
- [ ] gRPC service with all 4 RPCs implemented
- [ ] Prometheus metrics integrated (`/metrics` endpoint)
- [ ] EXPLAIN ANALYZE profiling mode working
- [ ] RSS memory tracking in benchmarks
- [ ] Integration tests passing

### Developer C
- [ ] Database optimizations applied (indexes, VACUUM)
- [ ] Monitoring scripts tested
- [ ] Grafana dashboard ready
- [ ] CI scripts validated locally
- [ ] wrk load test script ready

## Session Agenda

### Part 1: Benchmark Validation (45 min)

#### 1.1 Reset and Baseline (10 min)
```bash
# Reset database statistics
./scripts/monitor-query-performance.sh --reset

# Run monitoring in background
watch -n 2 './scripts/monitor-query-performance.sh' &
MONITOR_PID=$!

# Save baseline
cd rust-services/graphops
cargo bench --bench graphops_benchmark -- --save-baseline main
```

#### 1.2 Capture EXPLAIN ANALYZE (15 min)
```bash
# Enable profiling mode
export GRAPHOPS_EXPLAIN=1

# Run benchmarks with profiling
cargo bench --bench graphops_benchmark 2>&1 | tee bench-with-explain.log

# Parse server-side timings
grep "Planning Time\|Execution Time" bench-with-explain.log
```

**Expected Results**:
- Planning Time: <0.2ms
- Execution Time: <0.8ms (with database optimizations)
- Total Latency: <1.5ms

#### 1.3 Memory Profiling (10 min)
```bash
# Run memory benchmarks
cargo bench --bench memory_benchmark

# Check RSS during execution
ps -o pid,comm,rss | grep graphops
```

**Expected Results**:
- RSS: <200MB sustained
- No memory leaks over 1000 iterations

#### 1.4 Compare with Python Baseline (10 min)
```bash
# Run Python baseline
conda activate nina
python benchmarks/python_graphops_baseline.py > python-baseline.txt

# Compare
./scripts/compare_performance.sh
```

**Success Criteria**:
- With database optimization: Rust should be ≤1.5ms (vs Python ~1.2ms)
- Validate database tuning reduced ~0.5-1.0ms from original 2ms

### Part 2: Throughput Testing (30 min)

#### 2.1 Start gRPC Service (5 min)
```bash
# Terminal 1: Start service with HTTP bridge
cd rust-services/graphops
cargo run --release --bin graphops-service
```

#### 2.2 Health Check (5 min)
```bash
# Terminal 2: Verify service is up
curl http://localhost:8080/health
curl http://localhost:9090/metrics | grep graphops_

# Test gRPC
grpcurl -plaintext localhost:50051 \
  ninaivalaigal.graphops.v1.GraphOpsService/HealthCheck
```

#### 2.3 wrk Load Test (15 min)
```bash
# Run sustained load test
wrk -t4 -c40 -d30s --latency \
  --script benchmarks/wrk_graphops.lua \
  http://localhost:8080 | tee wrk-results.txt

# Parse results
python ci/parse-wrk-results.py wrk-results.txt \
  --validate \
  --output wrk-metrics.json
```

**Success Criteria**:
- Throughput: >500 req/s sustained (target: >1000 req/s with optimized DB)
- P95 Latency: <10ms
- Error Rate: <0.1%

#### 2.4 Monitor During Load (5 min)
```bash
# In another terminal
./scripts/monitor-query-performance.sh

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

### Part 3: Grafana Dashboard Validation (30 min)

#### 3.1 Start Prometheus + Grafana (10 min)
```bash
# Start Prometheus (scrape metrics from service)
docker run -d -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Start Grafana
docker run -d -p 3000:3000 grafana/grafana

# Add Prometheus data source (Grafana UI)
# URL: http://host.docker.internal:9090
```

#### 3.2 Import Dashboard (5 min)
```bash
# In Grafana UI:
# 1. Go to Dashboards → Import
# 2. Upload: monitoring/grafana-dashboards/graphops-performance.json
# 3. Select Prometheus data source
```

#### 3.3 Validate Metrics (15 min)

**Check Each Panel**:
- [ ] Request Latency (P50/P95/P99) - Shows data
- [ ] Throughput (Requests/sec) - Updates in real-time
- [ ] Cache Hit Rate - Displays percentage
- [ ] Database Connections - Shows active count
- [ ] Error Rate - Near zero
- [ ] Performance Comparison (Rust vs Python) - Table populated

**Run Load While Monitoring**:
```bash
# Generate traffic
while true; do
  curl -X POST http://localhost:8080/graphops/execute \
    -H "Content-Type: application/json" \
    -d '{"query": "MATCH (n:User) RETURN n LIMIT 10"}' \
    > /dev/null 2>&1
  sleep 0.1
done
```

Watch dashboard update in real-time.

### Part 4: CI Integration Validation (30 min)

#### 4.1 Test Regression Checker (10 min)
```bash
# Save current as baseline
cp rust-services/graphops/target/criterion/main/estimates.json baseline.json

# Simulate regression (edit benchmark to be slower)
# Then run again
cargo bench

# Check for regression
python ci/check-performance-regression.py \
  --current rust-services/graphops/target/criterion/main/estimates.json \
  --baseline baseline.json \
  --threshold 10
```

**Expected**: Should detect and report regression

#### 4.2 Test wrk Parser (5 min)
```bash
# Parse previous wrk results
python ci/parse-wrk-results.py wrk-results.txt \
  --validate \
  --sla-min-throughput 500 \
  --sla-max-p95-latency 10
```

**Expected**: Should validate and exit cleanly

#### 4.3 Dry-Run GitHub Workflow (15 min)
```bash
# Install act (GitHub Actions local runner)
# brew install act

# Test workflow locally (if possible)
act -j benchmark
```

**Fallback**: Manual review of workflow YAML for correctness

### Part 5: Documentation & Publishing (15 min)

#### 5.1 Generate Performance Report
```bash
# Collect all metrics
cat << EOF > docs/performance/phase-1-results.md
# SPEC-099 Phase 1 Performance Results

**Date**: $(date +%Y-%m-%d)

## Benchmark Results

### Single Request Latency
- Median: X.XX ms
- P95: X.XX ms
- P99: X.XX ms

### Server-Side Breakdown (EXPLAIN ANALYZE)
- Planning Time: X.XX ms
- Execution Time: X.XX ms
- Total: X.XX ms

### Throughput (wrk Load Test)
- Sustained RPS: XXX req/s
- Concurrent Clients: 40
- Duration: 30s
- Error Rate: X.XX%

### Memory Footprint
- RSS: XXX MB
- Heap: XXX MB

## Database Optimization Impact
- Before: ~2.0ms total latency
- After: ~X.Xms total latency
- Improvement: XX% faster

## Validation Status
- [x] SLA Met (<25ms P95)
- [x] Throughput Target (>500 req/s)
- [x] Memory Target (<200MB)
- [x] Grafana Dashboard Working
- [x] CI Pipeline Validated

EOF
```

#### 5.2 Update Progress Tracking
```bash
# Update task completion
# Mark all Phase 1 items as complete in task files
```

#### 5.3 Commit and Push
```bash
git add docs/performance/ benchmarks/ ci/
git commit -m "feat(graphops): SPEC-099 Phase 1 complete - performance validated

- gRPC service with Prometheus metrics
- Database optimization: 0.5-1.0ms improvement
- Throughput: XXX req/s sustained
- Memory: XXX MB RSS
- CI regression checks integrated"

git push origin main
```

## Success Criteria Summary

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| Median Latency | <10ms | ___ ms | ☐ |
| P95 Latency | <25ms | ___ ms | ☐ |
| P99 Latency | <50ms | ___ ms | ☐ |
| Throughput | >500 req/s | ___ req/s | ☐ |
| Memory (RSS) | <200MB | ___ MB | ☐ |
| Error Rate | <0.1% | ___% | ☐ |
| DB Optimization | 0.5-1.0ms gain | ___ ms | ☐ |
| Grafana Dashboard | All panels working | ___ | ☐ |
| CI Integration | Tests passing | ___ | ☐ |

## Troubleshooting

### Metrics Not Showing in Grafana
```bash
# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://localhost:9090/metrics | grep graphops_

# Check Prometheus query
# In Prometheus UI: graphops_request_duration_seconds_bucket
```

### wrk Load Test Failing
```bash
# Check service is running
curl http://localhost:8080/health

# Test single request
curl -X POST http://localhost:8080/graphops/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n:User) RETURN n LIMIT 10"}'

# Check wrk Lua script syntax
lua -l benchmarks/wrk_graphops.lua
```

### Database Performance Not Improved
```bash
# Verify indexes exist
psql $DATABASE_URL -c "\d+ ninaivalaigal_intelligence._ag_label_edge"

# Check index usage
./scripts/monitor-query-performance.sh

# Re-run VACUUM ANALYZE
./scripts/optimize-age-performance.sh
```

## Post-Session Actions

### Immediate
- [ ] Publish performance report to docs/
- [ ] Update SPEC-099 status to "Phase 1 Complete"
- [ ] Tag release: `git tag v0.1.0-phase1`
- [ ] Notify team of results

### Follow-Up (Next Sprint)
- [ ] Enable pg_stat_statements (requires DB restart)
- [ ] Add Prometheus alerting rules
- [ ] Create load test automation (daily runs)
- [ ] Document production deployment procedure

## Meeting Notes Template

**Date**: ___
**Attendees**: Developer A, Developer C

**Results**:
- Latency: ___ ms (P95)
- Throughput: ___ req/s
- Memory: ___ MB RSS
- Database improvement: ___ ms

**Blockers**:
- [ ] None / List blockers

**Decisions**:
- ___

**Action Items**:
- [ ] Developer A: ___
- [ ] Developer C: ___

**Next Steps**:
- ___

---

**Prepared By**: Developer C
**Status**: Ready for Day 4 Validation
