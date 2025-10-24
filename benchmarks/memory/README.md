# Memory Service Recall/Write Benchmark (US-86)

**Objective:** Exercise realistic Memory Service workloads (remember + recall) at Week 3 target rates to validate latency and throughput improvements.

## Prerequisites
- Memory Service running locally (`ninaivalaigal-dev-memory-service`).
- Redis + Postgres containers warmed (avoid cold-start penalties unless intentionally testing cold cache).
- Load tester binary built at `go-services/load-tester/bin/load-tester`.
- Python available for JWT generation.

## Steps

1. **Generate JWT token**
   ```bash
   python scripts/generate_jwt_token.py --interactive
   export NINA_TOKEN="<token output>"
   ```
   - Use an org/user combo aligned with the seeded dataset.

2. **Run recall/write scenario**
   ```bash
   chmod +x benchmarks/memory/run-recall-write.sh
   NINA_TOKEN="$NINA_TOKEN" \
   ./benchmarks/memory/run-recall-write.sh ./go-services/load-tester/bin/load-tester
   ```
   - Defaults: concurrency 60, duration 120s, rate limit 25k RPS.
   - Adjust by editing the script or exporting `PER_QUERY_*` style env vars (see inline comments).

3. **Optional sweeps**
   - Increase rate limit to 32k+ RPS to mirror prior stress tests.
   - Flush Redis (`docker exec ninaivalaigal-dev-redis redis-cli FLUSHALL`) between runs to compare cold vs warm cache.

4. **Capture metrics**
   ```bash
   chmod +x benchmarks/capture_resource_snapshot.sh
   ./benchmarks/capture_resource_snapshot.sh
   ```
   - Store console output / CSV logs under `benchmarks/results/<date>/` for later analysis.

## What to Record
- Request totals, success rate, latency percentiles (P50/P95/P99).
- Error distribution (expect 0 under successful run).
- CPU/RAM usage from docker stats snapshot.
- Observations on cache behavior (warm vs cold).

Use these datapoints to update `docs/DEVELOPER_A_RETEST_RESULTS.md` and the SPEC-099 cost savings template.
