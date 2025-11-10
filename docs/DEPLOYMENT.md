# Deployment Overview

This document lists the primary guides covering runtime deployment for Ninaivalaigal services. For detailed runbooks, follow the linked resources.

## 📚 Complete Deployment Guide

**For comprehensive deployment instructions, see:**
- **[Complete Deployment Guide](deployment/DEPLOYMENT_GUIDE_EXPANDED.md)** - Full reference covering Docker, GitHub Actions, CI runners, and Apple Container CLI

## Core References

| Component | Guide |
| --------- | ----- |
| **Complete Deployment Guide** | `docs/deployment/DEPLOYMENT_GUIDE_EXPANDED.md` |
| Docker Deployment | `docs/deployment/DEPLOYMENT_GUIDE_EXPANDED.md#docker-deployment` |
| GitHub Actions CI/CD | `docs/deployment/DEPLOYMENT_GUIDE_EXPANDED.md#github-actions-cicd` |
| CI Runner Configuration | `docs/deployment/DEPLOYMENT_GUIDE_EXPANDED.md#ci-runner-configuration` |
| Apple Container CLI | `docs/deployment/DEPLOYMENT_GUIDE_EXPANDED.md#apple-container-cli-setup` |
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

## Quick Start

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d

# Or build individual services
docker build -t ninaivalaigal/core-api:latest -f services/core-api/Dockerfile .
docker run -d --name nv-api -p 13370:8000 ninaivalaigal/core-api:latest
```

### Apple Container CLI
```bash
# Start complete stack
make stack-up

# Check status
make stack-status
```

### GitHub Actions
- Workflows are automatically triggered on push/PR
- See `.github/workflows/` for all CI/CD pipelines
- Self-hosted runners configured for Mac Studio deployment

For detailed instructions, see [Complete Deployment Guide](deployment/DEPLOYMENT_GUIDE_EXPANDED.md).
