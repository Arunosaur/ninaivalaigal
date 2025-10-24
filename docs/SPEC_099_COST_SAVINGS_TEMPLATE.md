# SPEC-099 ROI Cost Savings Summary (Template)

**Story:** US-86 — Performance Benchmarking CI (Week 3 Validation)
**Owner:** Developer A
**Target Savings:** 30–60% infrastructure cost reduction vs SPEC-099 baseline

---

## 1. Executive Snapshot

| Metric | Baseline (US-81) | Current (US-86) | Delta | Notes |
|--------|------------------|-----------------|-------|-------|
| GraphOps Throughput (RPS) | | | | |
| GraphOps P95 (ms) | | | | |
| Memory Service Throughput (RPS) | | | | |
| Memory Service P95 (ms) | | | | |
| Infra Cost (est. $/month) | | | | |

**Headline:** _Summarize % latency reduction, throughput gain, and projected cost savings in one sentence._

---

## 2. Detailed Findings

### 2.1 GraphOps Service
- **Workload:** (e.g., 4-query mix, 2k RPS steady, 3k RPS burst)
- **Latency Percentiles:** P50 | P95 | P99
- **Success Rate:**
- **CPU / Memory Usage:** from `benchmarks/capture_resource_snapshot.sh`
- **Key Observations:**
  -
  -

### 2.2 Memory Service
- **Workload:** (e.g., recall/write mix at 25k RPS)
- **Latency Percentiles:** P50 | P95 | P99 (cache warm vs cold)
- **Error Rate:**
- **CPU / Memory Usage:**
- **Key Observations:**
  -
  -

---

## 3. Cost Projection

| Resource | Baseline Utilization | Current Utilization | Scaling Factor | Monthly Cost Impact |
|----------|----------------------|---------------------|----------------|---------------------|
| GraphOps Nodes | | | | |
| Memory Service Nodes | | | | |
| Redis Tier | | | | |
| Postgres Tier | | | | |

**Narrative:** _Explain assumptions (e.g., node type, hourly rate, utilization thresholds)._ Include any caveats.

---

## 4. Risks & Follow-ups
- **Outstanding Issues:** (e.g., occasional INTERNAL errors under load)
- **Mitigations:** (probe traces, adjust query plans, etc.)
- **Next Actions:**
  1.
  2.

---

## 5. Attachments & References
- `docs/DEVELOPER_A_RETEST_RESULTS.md` (Realistic Query Mix section)
- Load tester CSV output: `benchmarks/results/<date>/`
- Prometheus snapshots
- Taiga US-86 comment (date)

---

_Fill this template before marking US-86 "Ready"; copy summary into Taiga and stakeholder update decks._
