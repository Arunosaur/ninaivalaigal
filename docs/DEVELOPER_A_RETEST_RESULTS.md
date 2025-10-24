# Developer A Retest Results (PgBouncer Dual Mode)

**Date:** October 20, 2025  \
**Story:** US-81 — Verify performance after dual PgBouncer rebuild  \
**Tester:** Developer A (via load-tester + grpcurl harness)

## Test Environment
- Local macOS dev stack with docker/colima containers running refreshed PgBouncer images (tx + sess)
- Services under test: Memory Service (`http://localhost:13393`), Core API (`http://localhost:13390`), GraphOps gRPC (`localhost:13398`)
- Tools:
  - `go-services/load-tester/bin/load-tester` (Task #37 HTTP harness)
  - `scripts/load-test-with-cache.sh` (grpcurl fan-out harness)
  - Prometheus metrics exposed by GraphOps at `http://localhost:9090/metrics`

> ℹ️ All tests performed after confirming GraphOps reflection availability: `grpcurl -plaintext localhost:13398 list` → service + reflection enumerated.

## Summary Table

| Service | Prior RPS | Prior P95 (ms) | New Test Settings | New RPS | New P95 (ms) | Delta & Notes |
|---------|-----------|----------------|-------------------|---------|--------------|----------------|
| Memory Service | 31.2k | ≈1.00 | `load-tester http … --concurrency 50 --requests 0 --duration 30s --rate-limit 25000` | **25.4k** | 0.97 | ✅ Sub-ms P95 restored while sustaining 25k RPS. Separate stress sweeps at 32k RPS (concurrency 60–100) held zero errors with P95 1.5–2.2 ms, confirming extra headroom when we accept slightly higher latency. |
| Core API | 3.07k | ≈0.69 | `load-tester http … --concurrency 30 --duration 30s --rate-limit 5000` | **5.1k** | 0.74 | ✅ Throughput +66% with comparable latency (P95 +0.05 ms). No errors over 204k requests. |
| GraphOps gRPC | Broken (timeouts / 501) | — | `load-tester grpc … --concurrency 80 --requests 5000 --rps 5000` | **5.0k** | 0.27† | ✅ Reflection-enabled GraphOps now sustains ~5k RPS with the native gRPC harness. 4,998 / 5,000 requests succeeded (0.04% `INTERNAL` errors) while staying under the 5k RPS target. |

† Prometheus histogram snapshot: `graphops_request_duration_seconds_bucket{le="0.001"} 6528 / 6530 total`, `p95 < 1 ms`, `avg ≈ 0.011 ms`.

## Detailed Observations

### Memory Service (PgBouncer-Session)
- Re-test at `--concurrency 50 --rate-limit 25000` delivered **25.4k RPS** with **P95 0.97 ms** (P99 1.73 ms), restoring the <1 ms latency target while maintaining high throughput.
- Higher-rate sweeps (`concurrency 60–100`, `rate-limit 32000`) posted **32k RPS** with P95 in the 1.5–2.2 ms range and zero errors, so the service has headroom if we tolerate slightly higher latency.
- Prior burst run (`--rate-limit 60000`) still reaches **47.7k RPS** (P95 ≈3.3 ms); keeping the data point for capacity planning.

### Core API (PgBouncer-Transaction)
- At a moderate 5k RPS target the service delivered **5,107 RPS** with **P95 0.74 ms**, **P99 1.09 ms**, matching the expected 5–15% gain (actually +66%).
- No 4xx/5xx responses over ~200k requests, confirming SCRAM authentication + new connection path working under load.

### GraphOps (PgBouncer-Transaction, gRPC)
- Reflection still verified — `grpc.reflection.v1alpha.ServerReflection` and `ninaivalaigal.graphops.v1.GraphOpsService` enumerate correctly.
- New native gRPC load tester (Task #37 enhancement) delivered **~5,000 RPS** with `--concurrency 80 --rps 5000`; success rate **99.96%** with two `INTERNAL` responses logged by GraphOps.
- Prometheus metrics after the run:
  - `graphops_request_duration_seconds_count 6530`
  - `graphops_request_duration_seconds_sum 0.0751` (avg ≈ 11 µs)
  - Buckets show **99.97% ≤ 1 ms**, all ≤ 50 ms.
- `grpcurl` fan-out scripts remain helpful for smoke tests, but throughput benchmarking now uses the gRPC-aware load tester.

## Issues & Follow-ups
- **GraphOps rare INTERNAL errors**: Investigate the two `INTERNAL` responses observed at 5k RPS (likely query/data related); repeats still hold success rate >99.9%.
- **Memory Service high-load profile**: Optional follow-up to exercise mixed read/write workloads at >30k RPS to verify latency behavior beyond the health endpoint.

## Next Actions
1. Monitor GraphOps under varied query mix to confirm the `INTERNAL` errors remain rare and gather failure details.
2. Optional: Run mixed Memory Service workloads (recall/write) to see if sub-ms latency holds beyond `/health`.
3. Update SPEC-099/US-81 acceptance notes with native gRPC load tester output now that Memory Service latency is back under 1 ms.

---

## Realistic Query Mix (US-86 Week 3) — Placeholder
- **Status:** Pending execution. Use `benchmarks/graphops/run-query-mix.sh` for GraphOps and `benchmarks/memory/run-recall-write.sh` for Memory Service.
- **Artifacts to collect:**
  - Load tester console/CSV per stream
  - Prometheus scrape (`graphops_request_duration_seconds_*`, `http_request_duration_seconds_bucket`)
  - `benchmarks/capture_resource_snapshot.sh` output for CPU/RAM snapshots
- **To document:**
  - Per-query success/error counts and latency percentiles (P50/P95/P99)
  - Memory Service recall vs write latency (warm/cold cache)
  - Resource utilization deltas feeding into `docs/SPEC_099_COST_SAVINGS_TEMPLATE.md`

_Update this section once the realistic workloads are executed to replace the placeholder bullets with measured data._
