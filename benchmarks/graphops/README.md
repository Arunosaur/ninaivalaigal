# GraphOps Benchmark Query Mix (Week 3 Validation)

**Context:** Week 3 SPEC-099 validation requires realistic GraphOps workloads that mirror production usage. This folder holds the curated payloads and steps for the native gRPC load tester to replay those scenarios.

## 📂 Layout

- `queries/`
  - `memory_feed.request.json` – user feed traversal (memories authored by `perf_user_001`).
  - `memory_feed.topics.json` – topical aggregation for dashboard cards.
  - `context_similarity.request.json` – similarity fan-out from anchor memory `perf_mem_001` via `SIMILAR_TO`.
  - `team_collaboration.request.json` – cross-team collaboration map for the benchmark persona.

Each file contains the `CypherRequest` payload consumed by the gRPC load harness (`--data-file`).

## ✅ One-Time Verification

1. Ensure GraphOps reflection is online (already validated earlier):
   ```bash
   grpcurl -plaintext localhost:13398 list ninaivalaigal.graphops.v1.GraphOpsService
   ```
2. Smoke-test each query before automated load:
   ```bash
   grpcurl -plaintext -d @ localhost:13398 ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery < benchmarks/graphops/queries/context_similarity.request.json
   ```
   Repeat for the other three payloads; confirm non-empty responses.

## 🚀 Running the Query Mix (native Go harness)

### Option A: Python orchestrator (weighted mix + resource sampling)

Spin up the mix with the higher-level helper that reads `config/*.json`, launches the Go load tester, and (optionally) captures psutil / Prometheus samples:

```bash
python3 scripts/mcp_mix_run.py \
   --config benchmarks/graphops/config/realistic_mix.json \
   --target-rps 1000 \
   --parallel 10 \
   --output-dir benchmarks/results
```

Add `--no-snapshots` to skip psutil sampling or `--proto shared/contracts/graphops/v1/graphops.proto` if reflection is disabled. Results (logs + JSON summary) land in `benchmarks/results/graphops_mix_<timestamp>/`.

### Option B: Raw shell wrapper (one process per payload)

Example steady-state run at ~2k RPS (4× 500 RPS streams) using the original helper script:

```bash
chmod +x benchmarks/graphops/run-query-mix.sh
TARGET=localhost:13398 \
PER_QUERY_CONCURRENCY=20 \
PER_QUERY_RPS=500 \
./benchmarks/graphops/run-query-mix.sh ./go-services/load-tester/bin/load-tester
```

Adjust `PER_QUERY_CONCURRENCY`, `PER_QUERY_RPS`, `TARGET`, or `DURATION` (env var) to explore other load shapes. The script spawns one load-tester process per payload so the mix runs concurrently.

**Notes:**
- Provide auth metadata via `GRPC_HEADERS="authorization: Bearer <token>" ./benchmarks/graphops/run-query-mix.sh …` if required.
- Start Prometheus scrape at `http://localhost:9090/metrics` and capture `graphops_request_duration_seconds_*` and `graphops_requests_total` deltas for the run.
- Record `success vs error` counts from each load-tester report to track residual `INTERNAL` responses.
- Run `./benchmarks/capture_resource_snapshot.sh` right after each load to snapshot CPU/RAM for the cost model.

## 📊 Metrics to Capture

- P50/P95/P99 latency per query (load tester output + Prometheus histogram).
- Success/error ratio for each CypherRequest in the mix.
- Throughput sustained across the duration (target: ≥1k RPS per scenario, stretch 2k).
- CPU/RAM sample from `docker stats ninaivalaigal-dev-graph-service` or host metrics for cost modeling.

## 🧭 Next Steps

1. Collect the raw metrics tables (load tester CSV + Prometheus snapshots).
2. Document findings in `docs/DEVELOPER_A_RETEST_RESULTS.md` under a new "Realistic Query Mix" section.
3. Feed the results into the SPEC-099 ROI cost model (once CPU/RAM data captured).

Prepared: October 21, 2025
