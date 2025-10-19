# Developer A – Container Deployment Runbook

**Author:** Python Microservices Team
**Last Updated:** October 19, 2025

---

## 🧭 Overview

Tasks #36 (gRPC Gateway), #37 (Load Tester), and #38 (CLI Tools) are feature-complete. The remaining work for Task #36 is to ship the gRPC gateway alongside the Rust Memory Service into the Apple Container CLI runtime that powers the Ninaivalaigal developer sandbox.

This runbook captures everything you need to:

- Build reproducible, arm64-compatible images.
- Import those images into the Apple Container CLI (ACC) runtime.
- Launch, validate, and operate the new services.
- Troubleshoot common failures and rollback when needed.

---

## ✅ Prerequisites

| Requirement | Command to Verify | Notes |
| --- | --- | --- |
| Apple Container CLI (ACC) | `container version` | Must be logged in to the dev environment host. |
| Docker Engine (arm64 capable) | `docker version --format '{{.Server.Arch}}'` | Should return `aarch64` or `arm64`. |
| Rust toolchain (for local builds) | `rustc --version` | Optional if you rely exclusively on Docker multi-stage build. |
| Go 1.21+ (for local builds) | `go version` | Optional when using Dockerfile build stage. |
| Network access to infra | `ping 192.168.66.5` and `ping 192.168.66.6` | Database/Redis hosts must be reachable. |
| Ports free on host | `lsof -i :13393` and `lsof -i :13395` | Stop conflicting processes before deployment. |

> **Tip:** If the ACC CLI is missing, run `brew install apple/container-cli` on macOS or consult `deploy/ACC_SETUP.md`.

---

## 📦 Build Artifacts

### Option A – Using Makefiles (recommended)

Both services ship with a `Makefile` that encapsulates the correct flags. Execute from the repository root:

```bash
# Build and package the gRPC gateway image as a tarball
make -C go-services/grpc-gateway docker-build-arm64

# Build and package the memory service image as a tarball
make -C rust-services/memory-service docker-build-arm64
```

Each target produces `/tmp/<service>-arm64-<timestamp>.tar`. The Makefile ensures:
- `GOARCH=arm64` or `CARGO_BUILD_TARGET=aarch64-unknown-linux-musl`
- Static binaries (CGO disabled) where applicable
- Stripped binaries to keep images lean

### Option B – Manual Docker commands

If you prefer to run the commands yourself, use the snippets below.

#### gRPC Gateway (Go)

```bash
cd go-services/grpc-gateway

# Build arm64 image
docker build --platform linux/arm64 \
  -t ninaivalaigal-grpc-gateway:arm64 .

# Export the image as tar for ACC
STAMP=$(date +%Y%m%d-%H%M%S)
docker save ninaivalaigal-grpc-gateway:arm64 \
  -o /tmp/grpc-gateway-${STAMP}.tar
```

#### Memory Service (Rust)

```bash
cd rust-services/memory-service

docker build --platform linux/arm64 \
  -t ninaivalaigal-memory-service:arm64 .

STAMP=$(date +%Y%m%d-%H%M%S)
docker save ninaivalaigal-memory-service:arm64 \
  -o /tmp/memory-service-${STAMP}.tar
```

---

## 🚀 Deploy to Apple Container CLI

> **Reminder:** ACC does not talk to the Docker daemon. Every image must be imported via tarball.

### 1. Import Images

```bash
container image load -i /tmp/grpc-gateway-*.tar
container image load -i /tmp/memory-service-*.tar
```

Verify import:

```bash
container image list | grep ninaivalaigal
```

### 2. Provision gRPC Gateway Container

```bash
container run -d \
  --name ninaivalaigal-dev-grpc-gateway \
  -p 13395:8080 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.66.5:6432/ninaivalaigal_dev" \
  -e REDIS_URI="redis://192.168.66.6:6379/0" \
  -e MEMORY_SERVICE_URL="http://192.168.66.4:13393" \
  -e GRAPHOPS_SERVICE_URL="http://192.168.66.4:13394" \
  -e LOG_LEVEL=info \
  --restart always \
  --memory 512m \
  --cpus 2 \
  ninaivalaigal-grpc-gateway:arm64
```

Notes:
- Replace `192.168.66.4` with the host that exposes the sibling services if different.
- `--restart always` keeps the container healthy during host restarts.

### 3. Provision Memory Service Container

```bash
container run -d \
  --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 \
  -e SERVICE_ROLE=memory-service \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.66.5:6432/ninaivalaigal_dev" \
  -e REDIS_URI="redis://192.168.66.6:6379/0" \
  -e LOG_LEVEL=info \
  --restart always \
  --memory 1g \
  --cpus 4 \
  ninaivalaigal-memory-service:arm64
```

---

## 🧪 Post-Deployment Validation

Run these checks from the host after a short warm-up (~5 s).

```bash
# Container state
container list | grep ninaivalaigal

# Service health endpoints
curl -sf http://localhost:13395/health | jq
curl -sf http://localhost:13393/health | jq

# Log tail (spot-check warnings)
container logs --tail 50 ninaivalaigal-dev-grpc-gateway
container logs --tail 50 ninaivalaigal-dev-memory-service
```

Expected JSON response shape:

```json
{
  "status": "healthy",
  "service": "grpc-gateway",   // or memory-service
  "version": "1.0.0"
}
```

### Integration Smoke Tests

1. **Gateway ↔ Memory Service**
   ```bash
   curl -X POST http://localhost:13395/api/memory/entries \
     -H 'Content-Type: application/json' \
     -d '{"key":"deployment-check","value":"ok"}'
   ```
2. **CLI Tools (Task #38) Health Command**
   ```bash
   cd go-services/cli-tools
   ./nina health check --target http://localhost:13395
   ```
3. **Load Tester Sanity Run (Task #37)**
   ```bash
   cd go-services/load-tester
   ./load-tester quick --target http://localhost:13395/health --duration 5s
   ```

---

## 🔁 Rolling Updates & Rollback

### Redeploy Workflow

1. `container stop ninaivalaigal-dev-grpc-gateway`
2. `container delete ninaivalaigal-dev-grpc-gateway`
3. Import new tar and re-run `container run ...`

### Rollback

- Keep the previous tarball (`/tmp/grpc-gateway-<old>.tar`).
- Re-import and redeploy using the same steps.
- Document rollbacks in `deployment/ROLLBACK_LOG.md`.

---

## 🛠 Troubleshooting Cheatsheet

| Symptom | Diagnostic | Resolution |
| --- | --- | --- |
| Container exits immediately | `container logs <name>` | Missing env var, binary crash, port already bound. |
| Health endpoint 500 | `container logs`, check upstream dependencies | Ensure PgBouncer/Redis reachable, verify credentials. |
| Cannot reach DB | `nc -vz 192.168.66.5 6432` | Restart PgBouncer (`container restart ninaivalaigal-dev-pgbouncer`). |
| Port binding failure | `lsof -i :13395` | Stop conflicting service or update port mapping. |
| ACC refuses image | `container image load ...` output | Ensure tar was generated with `--platform linux/arm64` and not compressed. |

---

## 📚 Reference

- `config/ports.nv.yaml` – authoritative port assignments.
- `deploy/ACC_SETUP.md` – provisioning Apple Container CLI.
- `deploy/network-topology.drawio` – service to port mapping visual.
- `docs/runbooks/postgres.md` – PgBouncer maintenance and credentials rotation.
- `docs/runbooks/redis.md` – Redis maintenance windows.

---

## ✅ Completion Checklist

- [ ] gRPC Gateway image built, loaded into ACC, container running.
- [ ] Memory Service image built, loaded into ACC, container running.
- [ ] Health endpoints for both services return `status=healthy`.
- [ ] Integration smoke tests pass (gateway ↔ memory service).
- [ ] Logs show no errors or panics during the first 5 minutes.
- [ ] `TAIGA_UPDATE` chore executed to mark Task #36 containerization complete.
- [ ] Deployment summary added to `deploy/release-notes/2025-10-19.md`.

---

**Next Steps:** Once both containers are live, proceed with system-wide load testing (Task #37) and leverage the CLI tooling to orchestrate validation flows. Capture results in `testing-logs/` and update Taiga with deployment evidence.
