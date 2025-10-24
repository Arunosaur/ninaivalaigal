# Go Services Deployment and Operations Guide

This guide covers the deployment workflow for the three Go deliverables introduced in US #77:

- gRPC Gateway (service port 13395)
- Load Tester tooling (port reservation 13396)
- CLI Tools bundle (port reservation 13397, local execution)

The content is organised as the four phases agreed with the team and includes acceptance criteria, validation steps, and troubleshooting notes.

## Phase 1 – Container Images (Day 1)

### Build arm64 images

Use the new Make targets to produce Apple Container CLI compatible images. Each target outputs an image tarball under `/tmp` with a timestamp suffix.

```bash
# gRPC Gateway
make -C go-services/grpc-gateway docker-package-arm64

# Load Tester
make -C go-services/load-tester docker-package-arm64

# CLI Tools (optional container form)
make -C go-services/cli-tools docker-package-arm64
```

### Local smoke tests

Before exporting, you can validate the services with Docker Desktop:

```bash
make -C go-services/grpc-gateway docker-run
make -C go-services/load-tester docker-run
```

## Phase 2 – Stack Integration (Day 1–2)

### Start script for gRPC Gateway

`scripts/nv-grpc-gateway-start.sh` builds, exports, imports, and launches the gateway inside the Apple container runtime. The script detects the host IP, wires backend service addresses, and sets OTEL environment variables.

```bash
./scripts/nv-grpc-gateway-start.sh

# useful overrides
HOST_SERVICE_IP=192.168.66.92 ./scripts/nv-grpc-gateway-start.sh
SKIP_BUILD=true ./scripts/nv-grpc-gateway-start.sh
```

Environment variables consumed by the Go service:

- `GATEWAY_HOST`, `GATEWAY_PORT` – bind address and port inside the container.
- `GATEWAY_PUBLIC_HOST`, `GATEWAY_PUBLIC_PORT` – advertised URL shown in logs and curl samples.
- `CORE_API_ADDR`, `MEMORY_SERVICE_ADDR`, `GRAPHOPS_SERVICE_ADDR` – upstream targets (host:port).
- `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACING_ENABLED` – tracing configuration.

### Stack orchestration

- Include the gateway invocation in any local stack scripts (e.g., append the call to `nv-stack-start.sh` when that orchestrator is reintroduced).
- Use `container list` to confirm companion services are running: `ninaivalaigal-dev-memory-service`, `ninaivalaigal-dev-graphops`, `ninaivalaigal-dev-grpc-gateway`.

## Phase 3 – Testing and Validation (Day 2)

### Health checks

```bash
curl http://localhost:13395/health | jq
```

### Load testing (port 13396 reservation)

Build the binary and run the predefined scenarios against the gateway.

```bash
make -C go-services/load-tester build
go-services/load-tester/bin/load-tester scenario grpc-gateway --concurrency 50 --duration 60s
```

### CLI integration

The CLI exposes the health command that surfaces the gateway status.

```bash
make -C go-services/cli-tools build
go-services/cli-tools/nina health check --json
```

### Optional container loading

If the load tester or CLI tools are required as containers, load the tarballs produced in Phase 1:

```bash
container image load -i /tmp/load-tester-*.tar
container image load -i /tmp/cli-tools-*.tar
```

## Phase 4 – Documentation (Day 3)

- Update `docs/DEPLOYMENT.md` with a short summary pointing to this guide.
- Capture operational runbooks in `docs/GO_SERVICES_OPERATIONS.md` (this file).
- Ensure the new Make targets are referenced in the developer onboarding material where appropriate.

## Acceptance Criteria Checklist

- gRPC Gateway container running on port 13395 (health check responds with `status: healthy`).
- Load tester executable available (`go-services/load-tester/bin/load-tester`).
- CLI tools deployed (`go-services/cli-tools/nina` or tarball artefacts under `dist/`).
- Health checks passing (`curl` plus CLI validation).
- Stack integration complete (gateway wired to core API, memory service, GraphOps).
- Documentation updated (this guide and the deployment landing page).

## Troubleshooting Quick Reference

| Symptom | Probable Cause | Resolution |
| ------- | -------------- | ---------- |
| `curl` to `/health` returns HTTP 500 | Backend service unreachable | Confirm `CORE_API_ADDR`, `MEMORY_SERVICE_ADDR`, and `GRAPHOPS_SERVICE_ADDR`. Override via environment variables and re-run the start script. |
| Container fails to start with `address already in use` | Port 13395 bound by previous run | `container stop ninaivalaigal-dev-grpc-gateway` followed by the start script. |
| Load tester binary missing | Build directory cleaned | `make -C go-services/load-tester build` rebuilds the binary. |
| CLI health command shows GraphOps `EOF` | Expected (GraphOps is gRPC only) | Use `grpcurl -plaintext localhost:13398 list` to confirm GraphOps availability. |

## Contacts

- Primary owner: Developer A
- Escalation path: Infrastructure team via `#nina-stack-ops`
