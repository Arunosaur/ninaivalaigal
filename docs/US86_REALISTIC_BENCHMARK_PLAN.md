# US-86 Realistic Benchmark Execution Plan (Week 3)

**Owner:** Developer A
**Status:** In Progress
**Last Updated:** October 21, 2025

This playbook captures the remaining steps to close US-86 by exercising realistic workloads, collecting performance telemetry, and translating gains into ROI. Use it alongside `docs/DEVELOPER_A_STATUS_UPDATE_20251021.md`.

---

## 1. GraphOps Query Mix (gRPC)

| Step | Action | Command / Reference | Notes |
|------|--------|----------------------|-------|
| 1 | Verify reflection + seeded data | `grpcurl -plaintext localhost:13398 list` | Ensure `perf_user` artifacts respond to smoke tests. |
| 2 | Run query mix (steady-state) | `chmod +x benchmarks/graphops/run-query-mix.sh` then `./benchmarks/graphops/run-query-mix.sh ./go-services/load-tester/bin/load-tester` | Default env values yield 4×500 RPS (≈2k total). Adjust `PER_QUERY_*` for sweeps. |
| 3 | Capture metrics | - Load tester output per stream<br>- Prometheus scrape `graphops_request_duration_seconds_*`<br>- `chmod +x benchmarks/capture_resource_snapshot.sh` then run script | Save artifacts under `benchmarks/results/`. |
| 4 | Repeat for burst profile | Set `PER_QUERY_RPS=750`, `DURATION=60s` | Target: validate 3k RPS mix sustained under <1 ms P95. |
| 5 | Document results | `docs/DEVELOPER_A_RETEST_RESULTS.md` → add "Realistic Query Mix" subsection | Include success/error counts, latency percentiles, CPU/RAM. |

**Observation targets:**
- Success rate ≥99.9% (investigate INTERNAL failures per query).
- P95 per scenario ≤ 1 ms (steady) / ≤ 2 ms (burst).
- Docker stats snapshot for cost modelling.

---

## 2. Memory Service Recall/Write Mix (HTTP)

| Step | Action | Command / Reference | Notes |
|------|--------|----------------------|-------|
| 1 | Generate JWT token | `python scripts/generate_jwt_token.py --interactive` | Export `NINA_TOKEN` env variable post generation. |
| 2 | Run scenario | `chmod +x benchmarks/memory/run-recall-write.sh` then `NINA_TOKEN=... ./benchmarks/memory/run-recall-write.sh ./go-services/load-tester/bin/load-tester` | Scenario concurrently exercises remember + recall endpoints. |
| 3 | Parameter sweeps | Adjust `--concurrency`, `--rate-limit`, `--duration` in script as needed (edit file or use env overrides). | Baseline: concurrency 60, rate 25k RPS, duration 120s. |
| 4 | Metrics capture | Collect load tester CSV/console + `benchmarks/capture_resource_snapshot.sh`. | Compare cache-hit vs cold-run latencies by flushing Redis if needed. |
| 5 | Document results | Update retest doc with P50/P95/P99, error rates, and heatmap of recall vs write latency. | Tie back to sub‑ms objective. |

**Optional drills:**
- Warm vs cold cache comparison (restart Redis between runs).
- Larger payloads to simulate long-form memories.

---

## 3. Cost Savings & ROI Summary

| Step | Action | Artifact |
|------|--------|----------|
| 1 | Aggregate metrics | Build table: service, RPS, P95, CPU%, Memory MB (baseline vs new). |
| 2 | Convert to infra savings | Estimate node count reduction using CPU headroom + throughput gains. |
| 3 | Draft summary | `docs/SPEC_099_COST_SAVINGS_TEMPLATE.md` (new) — populate sections for latency gains, throughput gains, cost delta (30–60% target). |
| 4 | Feed into executive report | Update SPEC-099 ROI slide deck / final report reference. |

**Inputs required:** Docker stats snapshots, load tester results, baseline numbers from US‑81.

---

## 4. Taiga Documentation & Hand-off

1. Post benchmark findings to Taiga US‑86 comment thread.
2. Flip status to **Ready for Review** only after:
   - GraphOps & Memory mixes documented with metrics + cost model draft.
   - ROI summary attached / linked in docs.
3. Reference this playbook and status update doc for reviewers.

---

## Appendix: Useful Paths

- GraphOps payloads: `benchmarks/graphops/queries/`
- GraphOps mix script: `benchmarks/graphops/run-query-mix.sh`
- Memory scenario: `benchmarks/memory/recall_write.json`
- Memory mix script: `benchmarks/memory/run-recall-write.sh`
- Resource snapshot: `benchmarks/capture_resource_snapshot.sh`
- Status summary: `docs/DEVELOPER_A_STATUS_UPDATE_20251021.md`
- Retest results log: `docs/DEVELOPER_A_RETEST_RESULTS.md`

---

**Next Checkpoint:** Capture first run artifacts (steady-state GraphOps mix + memory recall/write) and update retest doc before proceeding to cost modelling.
