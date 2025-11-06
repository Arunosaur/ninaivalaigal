# Rust Memory Provider Runbook

Operational checklist for enabling, validating, and rolling back the Rust Memory Service provider inside the ninaivalaigal platform.

---

## 1. Environment Configuration

Export these variables before starting the service or running pytest suites:

| Variable | Purpose | Recommended Value |
|----------|---------|-------------------|
| `MEMORY_PROVIDER` | Forces provider selection. Leave unset to allow flag auto-detection. | `rust` (staging/prod rollout) or `postgres` (fallback) |
| `USE_RUST_MEMORY` | Feature flag read by Python factories and pytest gate. | `1` to enable, `0` to disable |
| `MEMORY_SERVICE_URL` | Base URL for Rust service when proxying through FastAPI. | `http://localhost:13393` (dev) |
| `PYTEST_RUN_RUST_INTEGRATION` | Opts into the Rust pytest suite when CI flag is off. | `1` for targeted validation |

> Tip: persist the flag set using `.env.dev` or `direnv` so the Python factories and pytest gate stay in sync.

## 2. Deployment Steps (Dev/Staging)

1. **Build image**
   ```bash
docker build -t ninaivalaigal/memory-service:dev rust-services/memory-service
   ```
2. **Run via Compose**
   ```bash
docker compose up -d rust_memory
   ```
   or use the Apple Container CLI flow documented in `DEVELOPER_A_CONTAINER_DEPLOYMENT.md`.
3. **Verify container**
   ```bash
docker ps --filter name=memory-service
   ```
4. **Configure API gateway** – ensure `MEMORY_PROVIDER=rust` (or `USE_RUST_MEMORY=1`) on FastAPI deployments so requests proxy to the Rust service.

## 3. Health & Connectivity Checks

Run after deployment and again post-flag flip:

| Command | Expected |
|---------|----------|
| `curl http://localhost:13393/health` | `ok` JSON payload |
| `curl -H "Authorization: Bearer <jwt>" \
    -X POST http://localhost:13393/memory/remember \
    -d '{"content":"probe","metadata":{}}'` | `200 OK` with normalized memory payload |
| `curl http://localhost:13393/metrics` | Prometheus plaintext |

If any fail, capture logs with `RUST_LOG=debug` and attach to incident notes before rolling back.

## 4. Test Strategy

1. **Unit safety net** (always on):
   ```bash
pytest -m unit tests --maxfail=1
   ```
2. **Rust integration verification** (requires service & env flag):
   ```bash
pytest -m rust_integration --run-rust-integration
   ```
3. **CI toggle** – the default pipeline skips `rust_integration` unless `USE_RUST_MEMORY=1` or `PYTEST_RUN_RUST_INTEGRATION=1` is set.

## 5. Observability Hooks

- **Prometheus**: scrape target `http://memory-service:13393/metrics`; ensure alerts on latency spikes and non-200 response ratios.
- **Grafana**: dashboard panel under “Memory Provider” should plot Rust query latencies vs. Postgres fallback.
- **Logs**: forward structured JSON logs via existing Loki pipeline (`RUST_LOG=json`).

## 6. Rollback Plan

1. Set `USE_RUST_MEMORY=0` (or `MEMORY_PROVIDER=postgres`) on API deployments.
2. Restart the FastAPI processes (`nv-core-api-start.sh` or systemd unit) to pick up the flag.
3. Run smoke tests to confirm Postgres provider resumes handling requests:
   ```bash
pytest -m "unit and not rust_integration" tests/server/memory
   ```
4. Stop the Rust container to avoid straggling writes: `docker stop rust_memory`.
5. Create a Taiga comment on US#635 documenting the reason and scope of the rollback.

## 7. Ownership & Escalation

| Role | Contact |
|------|---------|
| Platform Architect | platform-architects@ninaivalaigal.local |
| Rust Lead | rust-leads@ninaivalaigal.local |
| DevOps On-Call | devops-oncall@ninaivalaigal.local |

Escalate immediately if memory write/read error rates exceed baseline by >5% for more than 5 minutes.

---

**Last Updated:** 2025-11-04

Use this runbook when requesting Platform/Rust/DevOps sign-off for SPEC-139 gating readiness.
