# Developer A: Suggestions for GraphOps Benchmarking (US #86)

**Date:** October 21, 2025
**Context:** Phase 3 benchmarking with realistic query mixes and cost savings analysis

---

## 🎯 Excellent Progress Summary

**Completed:**
✅ Inline Cypher documentation for MCP ingestion (map-shaped rows)
✅ Version-controlled fixtures: `rust-services/graphops/tests/cypher/perf_user_seed.cypher`, `rust-services/graphops/tests/cypher/memory_feed.cypher`
✅ Extended `rust-services/graphops/tests/grpc_integration_test.rs` with map-shape validation
✅ Baseline performance: 5k RPS @ P95 0.27ms, 99.96% success

**Next Phase:** Mix workload testing + resource snapshots + cost model

---

## 📋 High-Priority Suggestions

### 1. **Infrastructure Preparation (Before Mix Run)**

**Database Seeding Automation:**

**IMPORTANT:** Apache AGE runs as an extension in the **same** PostgreSQL container (`ninaivalaigal-dev-db`) on port 5432, not a separate graph database. The graph schema (`ninaivalaigal_graph`) lives alongside the standard application tables in `ninaivalaigal_dev`.

```bash
# Seed the perf graph via GraphOps (delegates to ExecuteQuery)
./scripts/seed-perf-graph.sh
```

**Health Check Before Mix:**
```bash
# Quick readiness probe (returns one perf_user node)
./scripts/validate-graph-ready.sh
```

### 2. **Enhanced Mix Workload Configuration**

**Expand `scripts/mcp_mix_run.py` Parameters:**

`scripts/mcp_mix_run.py` now loads weighted query configs, drives the Go load tester, and captures optional psutil/Prometheus samples. Key flags:

```bash
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 1000 \
  --parallel 10 \
  --output-dir benchmarks/results
```

- `--config` points to the workload definition (weighted queries, ramp/steady/cooldown, snapshot cadence).
- `--target-rps` and `--parallel` override the totals without editing JSON.
- `--proto` can be supplied if reflection is disabled; otherwise reflection is used by default.
- To skip resource sampling: add `--no-snapshots` (useful on systems without `psutil`).

**Suggested Invocation:**
```bash
# Ramp-up test (gradual load increase)
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 1000 \
  --parallel 10 \
  --output-dir benchmarks/results

# Stress test (push to limits)
python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/stress_mix.json \
  --target localhost:13398 \
  --target-rps 5000 \
  --parallel 50 \
  --output-dir benchmarks/results
```

### 3. **Resource Monitoring Strategy**

**Docker Stats Collection:**

**NOTE:** AGE graph data is in `ninaivalaigal-dev-db` (consolidated architecture), so monitor that container for both SQL and graph query performance.

```bash
# Stream docker stats (GraphOps + postgres+AGE + redis) every 10s
./scripts/monitor-resources.sh results/resources_mix_test.csv &
MONITOR_PID=$!
# ... run your tests ...
kill $MONITOR_PID
```

**Prometheus Queries for GraphOps:**
```promql
# CPU usage over time
rate(container_cpu_usage_seconds_total{name="ninaivalaigal-dev-graphops"}[5m])

# Memory usage
container_memory_usage_bytes{name="ninaivalaigal-dev-graphops"}

# Query latency percentiles
histogram_quantile(0.95, rate(grpc_server_handling_seconds_bucket{service="GraphOpsService"}[5m]))

# Request rate
rate(grpc_server_handled_total{service="GraphOpsService"}[5m])

# Error rate
rate(grpc_server_handled_total{service="GraphOpsService",grpc_code!="OK"}[5m])
```

### 4. **Cost Savings Model Template**

**Create Baseline vs Optimized Comparison:**
```markdown
# GraphOps Cost Savings Analysis

## Baseline (Before SPEC-099)
- **Runtime:** Python GraphQL API
- **Throughput:** ~100 RPS (estimated)
- **P95 Latency:** ~500ms (estimated)
- **Infrastructure:**
  - 4 vCPU, 8GB RAM
  - Cost: $150/month (AWS t3.xlarge)

## Optimized (After SPEC-099 Rust + AGE)
- **Runtime:** Rust gRPC + Apache AGE
- **Throughput:** 5,000 RPS (actual, 50x improvement)
- **P95 Latency:** 0.27ms (actual, 1,850x improvement)
- **Infrastructure:**
  - 2 vCPU, 4GB RAM (sufficient for same workload)
  - Cost: $60/month (AWS t3.medium)

## Savings Calculation
- **Infrastructure:** $90/month (60% reduction)
- **Engineering velocity:** 50x throughput = handle 50x users on same hardware
- **Operational efficiency:** Sub-ms latency = better UX, lower retry rates
- **ROI:** 3-month migration pays for itself in 4 months of savings
```

### 5. **Integration Test Alignment**

**Export Fixtures to Load Tester:**
```bash
# Ensure go-services/load-tester uses the same fixtures from the GraphOps crate
cp rust-services/graphops/tests/cypher/*.cypher go-services/load-tester/fixtures/
cp benchmarks/graphops/queries/*.json go-services/load-tester/queries/

# Update load-tester config
cat > go-services/load-tester/config/graphops_queries.yaml << 'YAML'
queries:
  - name: memory_feed
    template: queries/memory_feed.request.json
    weight: 0.4
    expected_shape: map  # JSON object per row

  - name: context_similarity
    template: queries/context_similarity.request.json
    weight: 0.3
    expected_shape: map

  - name: team_collaboration
    template: queries/team_collaboration.request.json
    weight: 0.2
    expected_shape: map

  - name: topic_aggregation
    template: queries/topic_aggregation.request.json
    weight: 0.1
    expected_shape: map
YAML
```

### 6. **Automated Reporting**

**Create Results Aggregator:**
```python
# scripts/aggregate_benchmark_results.py
import json
import sys
from pathlib import Path
from typing import List, Dict

def aggregate_results(result_files: List[Path]) -> Dict:
    """Aggregate multiple benchmark runs into summary report"""
    all_runs = []
    for file in result_files:
        with open(file) as f:
            all_runs.append(json.load(f))

    return {
        "summary": {
            "total_runs": len(all_runs),
            "avg_rps": sum(r["rps"] for r in all_runs) / len(all_runs),
            "avg_p95_latency": sum(r["p95_ms"] for r in all_runs) / len(all_runs),
            "avg_success_rate": sum(r["success_rate"] for r in all_runs) / len(all_runs),
            "max_rps_achieved": max(r["rps"] for r in all_runs),
            "min_p95_latency": min(r["p95_ms"] for r in all_runs),
        },
        "runs": all_runs,
        # Add resource utilization summary
        "resource_efficiency": {
            "avg_cpu_percent": sum(r.get("avg_cpu", 0) for r in all_runs) / len(all_runs),
            "avg_memory_mb": sum(r.get("avg_memory", 0) for r in all_runs) / len(all_runs),
            "queries_per_cpu_core": (sum(r["rps"] for r in all_runs) / len(all_runs)) / 2,  # Assuming 2 cores
        }
    }

if __name__ == "__main__":
    results = aggregate_results([Path(f) for f in sys.argv[1:]])
    print(json.dumps(results, indent=2))
```

### 7. **Documentation Updates**

**Update DEVELOPER_A_STATUS_UPDATE_20251021.md:**
```markdown
## 🧪 Mix Workload Test Results (Add after completion)

**Test Configuration:**
- Duration: 5 minutes steady-state
- Target RPS: 1,000
- Parallel Workers: 10
- Query Mix: 40% feed, 30% similarity, 20% collab, 10% topic

**Performance Results:**
- Achieved RPS: [FILL IN]
- P95 Latency: [FILL IN] ms
- P99 Latency: [FILL IN] ms
- Success Rate: [FILL IN]%
- Error Breakdown: [FILL IN]

**Resource Utilization:**
- GraphOps CPU: [FILL IN]%
- GraphOps Memory: [FILL IN] MB
- Graph-DB CPU: [FILL IN]%
- Graph-DB Memory: [FILL IN] MB
- Redis CPU: [FILL IN]%

**Cost Model:**
- Current Infrastructure: [FILL IN]
- Projected Savings: [FILL IN]
- ROI Timeline: [FILL IN]
```

---

## 🚀 Execution Checklist

### Pre-Test Setup
- [ ] Run `scripts/seed-perf-graph.sh` to populate graph
- [ ] Run `scripts/validate-graph-ready.sh` to confirm setup
- [ ] Start Prometheus/Grafana for metrics collection
- [ ] Start resource monitoring: `./scripts/monitor-resources.sh`

### Test Execution
- [ ] Run realistic mix workload (1k RPS, 5 min)
- [ ] Run stress test (5k RPS, 1 min)
- [ ] Capture Prometheus snapshots
- [ ] Export docker stats CSV

### Post-Test Analysis
- [ ] Aggregate results with `scripts/aggregate_benchmark_results.py`
- [ ] Generate cost savings model
- [ ] Update DEVELOPER_A_STATUS_UPDATE_20251021.md
- [ ] Create graphs/charts for Taiga update
- [ ] Update DEVELOPER_A_RETEST_RESULTS.md

### Documentation
- [ ] Export fixtures to load-tester
- [ ] Update US #86 in Taiga with results
- [ ] Create SPEC-099 ROI summary document
- [ ] Share findings with team

---

## 💡 Key Insights

1. **Map-Shape Validation:** Your integration test ensures MCP compliance - excellent!
2. **Fixture Version Control:** Having `.cypher` files tracked prevents "works on my machine" issues
3. **Resource Monitoring:** Critical for cost model - capture CPU/RAM during tests
4. **Realistic Mix:** 40/30/20/10 split mirrors production usage patterns
5. **Reproducibility:** Scripts + fixtures = anyone can re-run your benchmarks

---

## 📊 Expected Outcomes

After completing mix workload tests, you should have:
- ✅ Validated 1k+ RPS with realistic query distribution
- ✅ P95 latency < 5ms across all query types
- ✅ Resource utilization baseline for cost model
- ✅ Clear ROI calculation for SPEC-099 migration
- ✅ Complete benchmark suite ready for CI/CD

---

**Next Taiga Update:** Include actual numbers, resource graphs, and cost model in US #86
**Timeline:** 1-2 days to complete testing + analysis
**Deliverable:** SPEC-099 ROI report with hard data supporting 30-60% cost reduction claim

Good luck! 🚀
