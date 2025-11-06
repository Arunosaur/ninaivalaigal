# SPEC-145: Multi-Runtime Multi-Architecture Container Builds

**Status**: Draft
**Date**: 2025-01-31
**Priority**: High
**Assigned To**: Developer D

---

## Overview

This specification defines the comprehensive container build strategy for ninaivalaigal across **3 runtimes** (Docker, Colima, Apple Container CLI) and **2 architectures** (ARM64, x86-64), enabling universal deployment and development flexibility.

## Motivation

- **Universal Compatibility**: Support development and deployment across Docker, Colima, and Apple Container CLI
- **Architecture Flexibility**: Native ARM64 and x86-64 builds for optimal performance
- **Developer Experience**: Consistent build process across all runtimes
- **Production Ready**: Support cloud deployments (AWS Graviton ARM64, standard x86-64 VMs)

## Goals

1. **Build containers for all 3 runtimes** (Docker, Colima, Apple Container CLI)
2. **Support both architectures** (ARM64, x86-64) for Docker and Colima
3. **Standardize port allocation** across all runtime/architecture combinations
4. **Automate builds** with comprehensive scripts and documentation
5. **Maintain consistency** with existing CONTAINERIZATION_STANDARD.md

## Scope

### Runtimes Covered
- ✅ **Docker**: Standard Docker Desktop/Engine (already in use)
- ✅ **Colima**: Docker-compatible runtime for macOS/Linux
- ✅ **Apple Container CLI**: Native macOS Sequoia+ runtime (already implemented)

### Architectures Covered
- ✅ **ARM64**: Apple Silicon, AWS Graviton, Oracle Ampere
- ✅ **x86-64 (AMD64)**: Intel/AMD processors, standard cloud VMs

### Services Covered
All 6 microservices from SPEC-100 Stage 3:
1. core-api (Python)
2. business-service (Python)
3. admin-vendor-service (Python)
4. memory-service (Rust)
5. graph-service (Python)
6. grpc-gateway (Go)

## Port Allocation Strategy

### Current Status
- ✅ Apple Container CLI dev: All microservice ports defined
- ❌ Docker dev/test/prod: Missing microservice ports
- ❌ Colima dev/test/prod: Missing microservice ports
- ❌ Apple test/prod: Missing microservice ports

### Port Formula
Following SPEC-086 formula:
```
port = base_port + runtime_offset + environment_offset
```

**Base Ports** (microservices):
- core_api: 13370
- business_logic: 13371
- admin_vendor: 13372
- memory_service: 13373
- graph_service: 13374
- grpc_gateway: 13375

**Runtime Offsets**:
- docker: 0
- colima: 10
- apple: 20

**Environment Offsets**:
- dev: 0
- test: 100
- prod: 200

## Build Strategy

### Architecture Support Matrix

| Runtime | ARM64 | x86-64 | Notes |
|---------|-------|--------|-------|
| Docker | ✅ | ✅ | Docker buildx for multi-arch |
| Colima | ✅ | ✅ | Docker-compatible, supports both |
| Apple Container CLI | ✅ | ❌ | macOS only, ARM64 native |

### Build Methods

#### 1. Docker (ARM64 + x86-64)
```bash
# Single architecture
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker build --platform linux/amd64 -t nina-core-api:amd64 .

# Multi-architecture (buildx)
docker buildx build --platform linux/arm64,linux/amd64 -t nina-core-api:latest .
```

#### 2. Colima (ARM64 + x86-64)
```bash
# Colima uses Docker CLI, same commands as Docker
colima start --arch arm64  # or x86-64
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker build --platform linux/amd64 -t nina-core-api:amd64 .
```

#### 3. Apple Container CLI (ARM64 only)
```bash
# Direct build (when DNS works)
container build --platform linux/arm64 -t nina-core-api:arm64 -f Dockerfile .

# Docker → tar → Apple Container (DNS workaround)
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker save nina-core-api:arm64 -o /tmp/core-api.tar
container image load --input /tmp/core-api.tar
```

## Implementation Tasks

### Phase 1: Port Matrix Update
- [ ] Update `config/ports.nv.yaml` with all microservice ports
- [ ] Add Docker dev/test/prod microservice ports
- [ ] Add Colima dev/test/prod microservice ports
- [ ] Add Apple test/prod microservice ports
- [ ] Validate no port collisions

### Phase 2: Build Scripts
- [ ] Create `scripts/build-docker-all.sh` (ARM64 + x86-64)
- [ ] Create `scripts/build-colima-all.sh` (ARM64 + x86-64)
- [ ] Update `scripts/docker-to-apple-container.sh` (already done)
- [ ] Create unified build script for all combinations

### Phase 3: Service-Specific Builds
For each of 6 services:
- [ ] Docker ARM64 build script
- [ ] Docker x86-64 build script
- [ ] Docker multi-arch build script
- [ ] Colima ARM64 build script
- [ ] Colima x86-64 build script
- [ ] Apple Container CLI build script (ARM64)

### Phase 4: Documentation
- [ ] Update `how-to/container-builds/docker/` guides
- [ ] Update `how-to/container-builds/colima/` guides
- [ ] Document architecture-specific considerations
- [ ] Create build workflow diagrams

### Phase 5: Testing & Validation
- [ ] Test Docker ARM64 builds
- [ ] Test Docker x86-64 builds
- [ ] Test Colima ARM64 builds
- [ ] Test Colima x86-64 builds
- [ ] Validate port assignments
- [ ] Test cross-runtime compatibility

## Success Criteria

1. ✅ All 6 services build for Docker (ARM64 + x86-64)
2. ✅ All 6 services build for Colima (ARM64 + x86-64)
3. ✅ All 6 services build for Apple Container CLI (ARM64)
4. ✅ Port matrix covers all 18 combinations (3 runtimes × 3 envs × 2 archs)
5. ✅ Build scripts are automated and documented
6. ✅ All services can run simultaneously without port conflicts

## Dependencies

- SPEC-086: Multi-Runtime Port Allocation (port formula)
- SPEC-100: API Container Modularization (service definitions)
- SPEC-013: Multi-Architecture Container Strategy (buildx reference)
- CONTAINERIZATION_STANDARD.md (standards compliance)

## Related Documentation

- `config/ports.nv.yaml` - Port allocation matrix
- `docs/standards/CONTAINERIZATION_STANDARD.md` - Build standards
- `how-to/container-builds/MULTI-ARCH-REQUIREMENTS.md` - Multi-arch guide
- `scripts/docker-to-apple-container.sh` - Apple Container CLI migration

---

**Next Steps**: Create Taiga stories and start implementation.
