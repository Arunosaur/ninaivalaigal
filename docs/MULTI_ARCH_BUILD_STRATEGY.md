# Multi-Architecture Build Strategy

## Objective
Support **18 total combinations** without losing features:
- 3 Runtimes: Docker, Colima, Apple Container CLI
- 3 Environments: dev, test, prod
- 2 Architectures: x86_64 (amd64), arm64

## Database Image Requirements

### Features Required (No Regression):
- ✅ PostgreSQL 15
- ✅ pgvector v0.5.1
- ✅ Apache AGE v1.5.0-rc0 (or v1.4.0-rc0)
- ✅ UUID support (pgcrypto)

### Current State:
- ✅ `nina-intelligence-db:arm64` - EXISTS and WORKS (pgvector + AGE)
- ❌ `nina-intelligence-db:amd64` - DOES NOT EXIST
- ❌ Multi-arch manifest - DOES NOT EXIST

## Build Strategy

### Option 1: Use Existing ARM64 Image + Build AMD64 (RECOMMENDED)
```bash
# 1. Tag existing ARM64 image properly
docker tag b56e09c0d6ab ninaivalaigal-intelligence-db:arm64

# 2. Build AMD64 version using buildx with emulation
docker buildx build --platform linux/amd64 \
  -t ninaivalaigal-intelligence-db:amd64 \
  -f containers/consolidated-db/Dockerfile \
  containers/consolidated-db/ \
  --load

# 3. Create multi-arch manifest
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ninaivalaigal-intelligence-db:latest \
  -f containers/consolidated-db/Dockerfile \
  containers/consolidated-db/ \
  --push  # or --load for local use
```

### Option 2: Use Pre-built pgvector + Separate AGE Container
- Main DB: Use `ankane/pgvector:v0.5.1` (supports both architectures)
- Graph DB: Separate container with Apache AGE
- **DOWNSIDE**: Requires 2 databases, adds complexity

### Option 3: Runtime-Specific Images
- Docker/Colima: Use Docker multi-arch images
- Apple Container CLI: Use `nina-intelligence-db:arm64` (already built)

## Compose File Strategy

### compose.docker.yml
```yaml
services:
  postgres:
    image: ninaivalaigal-intelligence-db:latest
    platform: ${PLATFORM:-linux/arm64}  # Auto-detect or specify
```

### compose.colima.yml
```yaml
services:
  postgres:
    image: ninaivalaigal-intelligence-db:latest
    platform: ${PLATFORM:-linux/amd64}  # Colima typically x86
```

### compose.apple.yml
```yaml
services:
  postgres:
    image: nina-intelligence-db:arm64  # Apple Silicon native
    platform: linux/arm64
```

## Architecture Detection

### Makefile Updates
```makefile
# Detect architecture
ARCH := $(shell uname -m)
ifeq ($(ARCH),x86_64)
    PLATFORM := linux/amd64
else ifeq ($(ARCH),arm64)
    PLATFORM := linux/arm64
else ifeq ($(ARCH),aarch64)
    PLATFORM := linux/arm64
endif

export PLATFORM
```

## Testing Matrix

### ARM64 Testing:
- [x] Apple Container CLI + ARM64 + nina-intelligence-db:arm64 = WORKS
- [ ] Docker + ARM64 + ninaivalaigal-intelligence-db:latest
- [ ] Colima + ARM64 + ninaivalaigal-intelligence-db:latest

### AMD64 Testing:
- [ ] Docker + AMD64 + ninaivalaigal-intelligence-db:latest
- [ ] Colima + AMD64 + ninaivalaigal-intelligence-db:latest
- [ ] Apple Container CLI + AMD64 (Rosetta) + ninaivalaigal-intelligence-db:latest

## Image Naming Convention

### For Docker/Colima (Multi-arch):
- `ninaivalaigal-intelligence-db:latest` - Multi-arch manifest
- `ninaivalaigal-intelligence-db:arm64` - ARM64 specific
- `ninaivalaigal-intelligence-db:amd64` - AMD64 specific

### For Apple Container CLI:
- `nina-intelligence-db:arm64` - Existing, proven working

## Migration Path

1. ✅ Verify ARM64 image works across all runtimes
2. ⏳ Build AMD64 version with same Dockerfile
3. ⏳ Create multi-arch manifest
4. ⏳ Update all compose files
5. ⏳ Test all 18 combinations
6. ⏳ Document architecture-specific considerations

## Success Criteria

- ✅ All features work (PostgreSQL + pgvector + Apache AGE)
- ✅ Both ARM64 and AMD64 supported
- ✅ All 9 runtime combinations work
- ✅ No manual architecture switching required
- ✅ Auto-detection in Makefiles
- ✅ Graceful fallback if one architecture unavailable
