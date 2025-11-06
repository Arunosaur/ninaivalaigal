# Service Container Build & Deployment Guide

**Date**: 2025-01-31
**Status**: Ready for Testing
**Compliance**: ✅ CONTAINERIZATION_STANDARD.md, ports.nv.yaml, env files

---

## Overview

Complete automation for building and deploying all 6 microservices using the Docker → tar → Apple Container CLI workflow.

---

## Scripts Created

### 1. `scripts/docker-to-apple-container.sh`
**Purpose**: Build and migrate individual service images

**Features**:
- ✅ Docker build with `--no-cache` and `--platform linux/arm64`
- ✅ Automatic tarball export
- ✅ Apple Container CLI image loading
- ✅ Image verification
- ✅ Cleanup of temporary files
- ✅ Comprehensive error handling

**Usage**:
```bash
# Build core-api
./scripts/docker-to-apple-container.sh core-api \
    --dockerfile services/core-api/Dockerfile \
    --context services/core-api

# Build memory-service (Rust)
./scripts/docker-to-apple-container.sh memory-service \
    --dockerfile rust-services/memory-service/Dockerfile \
    --context rust-services/memory-service
```

---

### 2. `scripts/test-build-all-services.sh`
**Purpose**: Test build script for all services

**Features**:
- Tests all 6 services sequentially
- Validates Dockerfiles and contexts exist
- Provides detailed logs for each service
- Summary report of passed/failed/skipped

**Usage**:
```bash
./scripts/test-build-all-services.sh
```

**Output**:
- Logs: `/tmp/build-test-{service}.log`
- Summary: Passed/Failed/Skipped counts

---

### 3. `scripts/build-and-deploy-all-services.sh`
**Purpose**: Comprehensive build and deploy automation

**Features**:
- Builds all 6 services using standardized workflow
- Optionally deploys services after building
- Validates start scripts exist
- Health checks after deployment
- Comprehensive reporting

**Usage**:
```bash
# Build only (no deployment)
./scripts/build-and-deploy-all-services.sh

# Build and deploy all services
./scripts/build-and-deploy-all-services.sh --deploy

# Skip tests
./scripts/build-and-deploy-all-services.sh --skip-tests

# Verbose output
./scripts/build-and-deploy-all-services.sh --verbose
```

---

## Services Configured

All services follow `config/ports.nv.yaml` for Apple Container CLI dev environment:

| Service | Port | Type | Dockerfile | Context |
|---------|------|------|------------|---------|
| core-api | 13390 | Python | `services/core-api/Dockerfile` | `services/core-api` |
| business-service | 13391 | Python | `services/business-service/Dockerfile` | `services/business-service` |
| admin-vendor-service | 13392 | Python | `services/admin-vendor-service/Dockerfile` | `services/admin-vendor-service` |
| memory-service | 13393 | Rust | `rust-services/memory-service/Dockerfile` | `rust-services/memory-service` |
| graph-service | 13394 | Python | `services/graph-service/Dockerfile` | `services/graph-service` |
| grpc-gateway | 13395 | Go | `go-services/grpc-gateway/Dockerfile` | `go-services/grpc-gateway` |

---

## Standards Compliance

### ✅ Container Naming
- Pattern: `ninaivalaigal-{env}-{service}`
- Example: `ninaivalaigal-dev-core-api`

### ✅ Port Allocation
- All ports from `config/ports.nv.yaml`
- Apple Container CLI dev environment
- Container ports: 8000 (Python/Rust), 13395 (gRPC Gateway)

### ✅ Environment Variables
- Reads from `configs/env-{env}.env`
- Falls back to defaults if file missing
- Supports dev/test/prod environments

### ✅ Image Naming
- Pattern: `nina-{service}:arm64`
- Example: `nina-core-api:arm64`

### ✅ Build Process
- Platform: `linux/arm64`
- Build flag: `--no-cache`
- Export: Uncompressed tar
- Load: Apple Container CLI

### ✅ Dynamic IP Discovery
- Uses `container inspect` for dependency IPs
- No hardcoded IPs
- Works with all runtimes

---

## Start Scripts Status

All services have start scripts that follow standards:

| Service | Start Script | Status |
|---------|--------------|--------|
| core-api | `services/core-api/nv-core-api-start.sh` | ✅ Updated (uses configs/env-*.env) |
| business-service | `scripts/nv-business-service-start.sh` | ✅ Exists |
| admin-vendor-service | Needs creation | ⚠️ TODO |
| memory-service | `scripts/nv-memory-service-start.sh` | ✅ Exists |
| graph-service | `services/graph-service/nv-graph-service-start.sh` | ✅ Exists |
| grpc-gateway | `scripts/nv-grpc-gateway-start.sh` | ✅ Exists |

**Note**: admin-vendor-service start script needs to be created following the same pattern as other services.

---

## Testing Workflow

### 1. Test Build Script
```bash
# Test all service builds
./scripts/test-build-all-services.sh
```

### 2. Build All Services
```bash
# Build only (no deployment)
./scripts/build-and-deploy-all-services.sh
```

### 3. Build and Deploy
```bash
# Build and deploy all services
./scripts/build-and-deploy-all-services.sh --deploy
```

### 4. Verify Services
```bash
# Check all services are running
container list | grep ninaivalaigal-dev

# Health checks
curl http://localhost:13390/health  # core-api
curl http://localhost:13391/health  # business-service
curl http://localhost:13392/health  # admin-vendor-service
curl http://localhost:13393/health  # memory-service
curl http://localhost:13394/health  # graph-service
curl http://localhost:13395/health  # grpc-gateway
```

---

## Troubleshooting

### Build Failures
- Check Dockerfile exists and is valid
- Verify build context directory exists
- Review logs: `/tmp/build-{service}.log`

### Deployment Failures
- Verify dependencies are running (db, redis, pgbouncer)
- Check start script exists and is executable
- Review logs: `/tmp/deploy-{service}.log`

### Health Check Failures
- Verify service is running: `container list | grep {service}`
- Check logs: `container logs {container-name}`
- Verify port is correct from `ports.nv.yaml`

---

## Next Steps

1. ✅ Build script created and compliant
2. ✅ Test script created
3. ✅ Build-and-deploy script created
4. ⏳ **Test build script for all services** (run `./scripts/test-build-all-services.sh`)
5. ⏳ Create admin-vendor-service start script
6. ⏳ Update all start scripts to use `configs/env-*.env` consistently

---

## Related Documentation

- `docs/standards/CONTAINERIZATION_STANDARD.md` - Full standards reference
- `config/ports.nv.yaml` - Port allocation matrix
- `docs/US22_APPLE_CONTAINER_MIGRATION_PROGRESS.md` - Migration progress
- `how-to/container-builds/apple/00-OVERVIEW.md` - Apple Container CLI guide

---

**Status**: Ready for testing. Run `./scripts/test-build-all-services.sh` to validate all builds.
