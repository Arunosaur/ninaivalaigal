# Deployment Overview

This document lists the primary guides covering runtime deployment for Ninaivalaigal services. For detailed runbooks, follow the linked resources.

## Core References

| Component | Guide |
| --------- | ----- |
| Go services (gRPC gateway, load tester, CLI tools) | `docs/GO_SERVICES_OPERATIONS.md` |
| Memory service (Rust) | `rust-services/memory-service/README.md` and `nv-memory-service-start.sh` |
| GraphOps (Rust gRPC) | `docs/TASK_49_GRAPHOPS_CONTAINERIZATION.md` |
| Apple Container CLI workflow | `docs/guides/DEVELOPER_A_CONTAINER_DEPLOYMENT.md` |

## Quick Checklist

1. Build arm64 images for services that will run inside the Apple container runtime.
2. Load the images using `container image load` and start each service via its `nv-*` helper script.
3. Run health checks (`curl`, CLI `nina health check`, or service-specific binaries).
4. Execute the load tester scenarios to confirm performance baselines.
5. Capture evidence in the relevant Taiga stories before marking them complete.

For gRPC gateway specific steps, consult `docs/GO_SERVICES_OPERATIONS.md`.
