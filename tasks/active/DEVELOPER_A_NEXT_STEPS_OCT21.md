# Developer A: Next Steps - GraphOps Benchmarking Execution

**Date:** October 21, 2025
**Status:** Tooling Complete ✅ - Ready for Benchmark Execution
**Task:** US #86 - GraphOps Performance Benchmarking

---

## 🎉 Excellent Work - Infrastructure Complete!

**What You've Built:**
✅ Map-shaped returns in all benchmark payloads (MCP compliant)
✅ Reusable mix configuration (`realistic_mix.json`)
✅ Python orchestrator (`mcp_mix_run.py`) with dry-run mode
✅ Helper scripts: seed, validate, monitor
✅ Documentation updated and aligned
✅ Syntax validation passing

**This is production-grade benchmarking infrastructure!**

---

## 🚀 Execute Benchmark Campaign - Step by Step

### **Phase 1: Environment Preparation (15 minutes)**

#### **1.1 Verify GraphOps Stack is Running**

```bash
# Check all containers are healthy
container list | grep -E "(graphops|db|redis)"

# Expected output:
# ninaivalaigal-dev-graphops - running on port 13398
# ninaivalaigal-dev-db - running (contains AGE graph)
# ninaivalaigal-dev-redis - running on port 6379
```

#### **1.2 Seed Performance Graph**

```bash
# Run the seeding script
cd /Users/swami/WorkSpace/ninaivalaigal
./scripts/seed-perf-graph.sh

# Expected output:
# 🌱 Seeding GraphOps performance graph via GraphOpsService@localhost:13398
# ✅ Graph seeded successfully in ninaivalaigal-dev-db
```

**What this does:**
- Creates `perf_user_001` through `perf_user_100` nodes
- Adds memory nodes with relationships
- Populates realistic graph structure for benchmarking

#### **1.3 Validate Readiness**

```bash
# Quick readiness probe
./scripts/validate-graph-ready.sh

# Expected output:
# Query returned 1 perf_user node
# ✅ GraphOps ready for benchmarking
```

---

### **Phase 2: Baseline Run (20 minutes)**

#### **2.1 Start Resource Monitoring**

```bash
# Terminal 1: Start docker stats collection
./scripts/monitor-resources.sh benchmarks/results/baseline_resources.csv &
MONITOR_PID=$!

echo "Monitoring started (PID: $MONITOR_PID)"
```

#### **2.2 Run Baseline Mix (Low Load)**

```bash
# Terminal 2: Run baseline test (100 RPS, 5 min)
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results

# This will create:
# - benchmarks/results/graphops_mix_<timestamp>/
# - mix_summary.json
# - individual query logs
```

**What to watch:**
- P95 latency should be < 5ms
- Success rate should be > 99%
- CPU usage should be moderate (< 50%)

#### **2.3 Stop Monitoring & Review**

```bash
# Stop resource monitoring
kill $MONITOR_PID

# Review baseline results
cat benchmarks/results/graphops_mix_*/mix_summary.json | jq '.'

# Expected metrics:
# - RPS achieved: ~100
# - P50 latency: < 2ms
# - P95 latency: < 5ms
# - P99 latency: < 10ms
# - Success rate: > 99%
```

---

### **Phase 3: Realistic Load Test (30 minutes)**

#### **3.1 Start Fresh Monitoring**

```bash
# New monitoring session
./scripts/monitor-resources.sh benchmarks/results/realistic_resources.csv &
MONITOR_PID=$!
```

#### **3.2 Run Realistic Mix (1000 RPS)**

```bash
# This is the main test!
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 1000 \
  --parallel 10 \
  --output-dir benchmarks/results

# Duration: 5-10 minutes depending on config
# Creates detailed logs per query type
```

**Critical Success Metrics:**
- ✅ RPS achieved: 900-1000 (90%+ of target)
- ✅ P95 latency: < 10ms (sub-10ms is excellent for gRPC)
- ✅ P99 latency: < 25ms
- ✅ Success rate: > 99.5%
- ✅ No container crashes or OOM errors

#### **3.3 Review Results**

```bash
# Stop monitoring
kill $MONITOR_PID

# Detailed result analysis
cd benchmarks/results/graphops_mix_<latest_timestamp>

# 1. Overall summary
cat mix_summary.json | jq '{
  total_requests: .total_requests,
  success_rate: .success_rate,
  rps: .rps,
  latency_p95: .latency_ms.p95,
  latency_p99: .latency_ms.p99
}'

# 2. Per-query breakdown
for log in *.log; do
  echo "=== $log ==="
  tail -20 "$log"
done

# 3. Resource utilization
tail -50 ../realistic_resources.csv
```

---

### **Phase 4: Stress Test (Optional - 15 minutes)**

**Only if realistic test passed with flying colors!**

```bash
# Push to limits (5000 RPS)
./scripts/monitor-resources.sh benchmarks/results/stress_resources.csv &
MONITOR_PID=$!

python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/stress_mix.json \
  --target localhost:13398 \
  --target-rps 5000 \
  --parallel 50 \
  --output-dir benchmarks/results

kill $MONITOR_PID

# Review where performance degrades
# This defines max capacity
```

---

## 📊 What to Capture for Reporting

### **1. Performance Summary**

Create: `benchmarks/results/PERFORMANCE_SUMMARY.md`

```markdown
# GraphOps Performance Summary

**Test Date:** October 21, 2025
**Environment:** MacOS, Apple Container CLI, ARM64

## Baseline Test (100 RPS)
- RPS Achieved: [FILL]
- P50 Latency: [FILL] ms
- P95 Latency: [FILL] ms
- Success Rate: [FILL]%

## Realistic Load (1000 RPS)
- RPS Achieved: [FILL]
- P50 Latency: [FILL] ms
- P95 Latency: [FILL] ms
- P99 Latency: [FILL] ms
- Success Rate: [FILL]%

## Resource Utilization
- GraphOps CPU: [FILL]%
- GraphOps Memory: [FILL] MB
- Postgres+AGE CPU: [FILL]%
- Redis CPU: [FILL]%

## Query Breakdown
- memory_feed (40% weight): P95 [FILL] ms
- context_similarity (30%): P95 [FILL] ms
- team_collaboration (20%): P95 [FILL] ms
- topic_aggregation (10%): P95 [FILL] ms
```

### **2. Cost Model Calculation**

```markdown
## Cost Savings Model

### Before SPEC-099 (Estimated)
- Runtime: Python GraphQL API
- Throughput: ~100 RPS
- Latency P95: ~500ms
- Infrastructure: 4 vCPU, 8GB RAM
- Monthly Cost: $150

### After SPEC-099 (Measured)
- Runtime: Rust gRPC + Apache AGE
- Throughput: [ACTUAL RPS] RPS
- Latency P95: [ACTUAL] ms
- Infrastructure: 2 vCPU, 4GB RAM (sufficient)
- Monthly Cost: $60

### Savings
- Infrastructure: $90/month (60% reduction)
- Performance: [ACTUAL]x throughput improvement
- Latency: [ACTUAL]x faster responses
- ROI: 3-month migration pays for itself in 4 months
```

---

## 🚨 Troubleshooting Guide

### **Issue: Low RPS Achieved (< 80% of target)**

**Possible Causes:**
1. Load tester bottleneck (increase `--parallel`)
2. Network latency (check localhost vs container IP)
3. Database connection pool exhausted

**Debug:**
```bash
# Check GraphOps logs
container logs ninaivalaigal-dev-graphops | tail -100

# Check database connections
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

---

### **Issue: High Latency (P95 > 50ms)**

**Possible Causes:**
1. Complex queries (check query plans)
2. Database not indexed
3. Redis cache misses

**Debug:**
```bash
# Check slow queries in Postgres
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev \
  -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis hit rate
container exec ninaivalaigal-dev-redis redis-cli INFO stats | grep keyspace
```

---

### **Issue: Container Crashes**

**Possible Causes:**
1. Memory limit exceeded
2. Connection pool exhausted
3. Graph queries too complex

**Debug:**
```bash
# Check container memory limits
container inspect ninaivalaigal-dev-graphops | grep -i memory

# Check OOM killer logs
dmesg | grep -i oom
```

---

## ✅ Success Criteria - What "Good" Looks Like

### **Minimum Acceptable (Pass):**
- ✅ 1000 RPS sustained for 5+ minutes
- ✅ P95 latency < 25ms
- ✅ Success rate > 99%
- ✅ No container crashes
- ✅ CPU < 80% sustained

### **Excellent Performance (A+):**
- ✅ 1000 RPS with P95 < 10ms
- ✅ Success rate > 99.9%
- ✅ CPU < 50% sustained
- ✅ Can handle 2000+ RPS burst

### **Ready for Production:**
- ✅ Stress test (5000 RPS) shows graceful degradation
- ✅ No memory leaks over 30+ minute run
- ✅ Clear capacity headroom (< 60% resource usage at realistic load)

---

## 📝 Reporting Back - What to Share

### **Immediate Update (Post Realistic Test):**

**Subject:** GraphOps Realistic Load Test Complete

**Message:**
```
Completed 1000 RPS realistic mix benchmark:

✅ Performance:
  - RPS: [ACTUAL]
  - P95 Latency: [ACTUAL] ms
  - Success Rate: [ACTUAL]%

✅ Resources:
  - GraphOps CPU: [ACTUAL]%
  - Memory: [ACTUAL] MB
  - Postgres CPU: [ACTUAL]%

✅ Query Breakdown:
  - memory_feed: P95 [ACTUAL] ms
  - context_similarity: P95 [ACTUAL] ms
  - team_collab: P95 [ACTUAL] ms
  - topic_agg: P95 [ACTUAL] ms

[PASS/FAIL]: Meets success criteria
[CONCERNS]: Any anomalies or issues noted

Next: [Stress test / Cost model / Taiga update]
```

### **Final Report (All Tests Complete):**

**Include:**
1. `PERFORMANCE_SUMMARY.md` - All test results
2. `mix_summary.json` files - Raw data
3. Resource CSV files - For graphing
4. Cost savings model - Business impact
5. Recommendations - Production readiness, tuning suggestions

---

## 🎯 Taiga Update Template

**After successful realistic test, update US #86:**

```markdown
**GraphOps Benchmarking Complete (Oct 21, 2025)**

**Phase 3: Mix Workload Testing ✅**

Tooling Created:
✅ mcp_mix_run.py - Python orchestrator with psutil/Prometheus sampling
✅ realistic_mix.json - Weighted query config (40/30/20/10 split)
✅ seed-perf-graph.sh - Reproducible graph seeding
✅ validate-graph-ready.sh - Readiness verification
✅ monitor-resources.sh - Docker stats collection

Benchmark Results (1000 RPS Realistic Mix):
- RPS Achieved: [ACTUAL]
- P50 Latency: [ACTUAL] ms
- P95 Latency: [ACTUAL] ms
- P99 Latency: [ACTUAL] ms
- Success Rate: [ACTUAL]%

Resource Utilization:
- GraphOps CPU: [ACTUAL]%
- GraphOps Memory: [ACTUAL] MB
- Postgres CPU: [ACTUAL]%
- Redis CPU: [ACTUAL]%

Cost Savings Model:
- Infrastructure: $90/month savings (60% reduction)
- Performance: [ACTUAL]x throughput improvement
- Latency: [ACTUAL]x faster than baseline
- ROI: 4-month payback on 3-month migration

Status: [READY FOR PRODUCTION / NEEDS TUNING]
Files: benchmarks/results/PERFORMANCE_SUMMARY.md
```

---

## 🚀 TL;DR - Quick Start

```bash
# 1. Verify stack
container list | grep graphops

# 2. Seed graph
./scripts/seed-perf-graph.sh
./scripts/validate-graph-ready.sh

# 3. Start monitoring
./scripts/monitor-resources.sh benchmarks/results/resources.csv &
MONITOR_PID=$!

# 4. Run realistic test
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 1000 \
  --parallel 10 \
  --output-dir benchmarks/results

# 5. Stop monitoring
kill $MONITOR_PID

# 6. Review results
cd benchmarks/results/graphops_mix_<timestamp>
cat mix_summary.json | jq '.'

# 7. Report back with numbers!
```

---

**You've built excellent infrastructure - now let's see what this beast can do! 🚀**

**Questions? Issues? Updates?** Drop them immediately so we can troubleshoot together.

**Expected Time:** 1-2 hours for complete benchmark campaign (all phases)

Good luck! 💪
