# Apple Container CLI Strategy for SPEC-100

**Date**: October 15, 2025
**Context**: SPEC-100 Stage 3 - Container Splitting
**Primary Runtime**: Apple Container CLI
**Build Workaround**: Docker (for DNS issues)

---

## 🎯 Strategy Overview

**Goal**: Use Apple Container CLI as the primary container runtime for all ninaivalaigal services while maintaining Docker as a build workaround when DNS issues arise.

**Why Apple Container CLI**:
- Native ARM64 performance on Mac Studio (3-5x faster than emulated Docker)
- Lower resource overhead
- Better integration with macOS
- Proven reliability with existing stack

**Why Keep Docker for Building**:
- DNS resolution issues in Apple Container CLI during builds
- Package repository connectivity problems
- Industry-standard Dockerfiles work without modification

---

## 📋 Dual-Build Strategy

### Method 1: Direct Apple Container CLI (Preferred)

Use when DNS/connectivity works:

```bash
# Build directly with Apple Container CLI
container build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .

# Verify
container image list | grep nina-[service]

# Run
container run -d --name ninaivalaigal-dev-[service] \
  -p [PORT]:[PORT] \
  [ENV_VARS] \
  nina-[service]:arm64
```

**Pros**:
- Single-step process
- Faster builds
- Native Apple CLI experience

**Cons**:
- May fail with DNS/connectivity issues
- Less reliable for package downloads

---

### Method 2: Docker Build + Transfer (DNS Workaround)

Use when Method 1 fails due to DNS issues:

```bash
# Step 1: Build with Docker (reliable DNS)
docker build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .

# Step 2: Export to tarball
docker save nina-[service]:arm64 -o /tmp/nina-[service].tar

# Step 3: Import to Apple Container CLI
container image load --input /tmp/nina-[service].tar

# Step 4: Cleanup
rm /tmp/nina-[service].tar

# Step 5: Verify
container image list | grep nina-[service]

# Step 6: Run with Apple Container CLI
container run -d --name ninaivalaigal-dev-[service] \
  -p [PORT]:[PORT] \
  [ENV_VARS] \
  nina-[service]:arm64
```

**Pros**:
- Reliable builds (Docker handles DNS well)
- Standard Dockerfiles work unchanged
- Final runtime still uses Apple CLI

**Cons**:
- Two-step process
- Requires both runtimes installed
- Temporary disk space for tarball

---

## 🏗️ SPEC-100 Stage 3 Application

### Services to Containerize

1. **Core API Service** (port 8000)
2. **Memory Service** (port 8001)
3. **Graph/AI Service** (port 8002)
4. **Business Service** (port 8003)
5. **Admin/Vendor Service** (port 8004)

### Build & Deploy Process

For each service:

```bash
# Try Method 1 first
container build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .

# If Method 1 fails, use Method 2
docker build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .
docker save nina-[service]:arm64 -o /tmp/nina-[service].tar
container image load --input /tmp/nina-[service].tar
rm /tmp/nina-[service].tar

# Always run with Apple Container CLI
container run -d --name ninaivalaigal-dev-[service] \
  -p [PORT]:[PORT] \
  -e DATABASE_URL="..." \
  -e REDIS_URL="..." \
  nina-[service]:arm64
```

---

## 📚 How-To Guide Structure

For each service, create: `how-to/container-builds/apple/[NN]-[service-name].md`

### Standard Sections (Following Existing Pattern)

1. **Container Information**
   - Name, image, base, architecture, ports

2. **What's Inside**
   - Application details, key files

3. **Prerequisites**
   - Dependencies, tools required

4. **Build Process**
   - Method 1: Apple Container CLI (with example)
   - Method 2: Docker build + transfer (with example)

5. **Runtime Configuration**
   - Start container with Apple CLI
   - Environment variables
   - Volume mounts

6. **Verification**
   - Health checks, logs, API tests

7. **Get Container IP** (Apple CLI specific)
   ```bash
   SERVICE_IP=$(container inspect ninaivalaigal-dev-[service] | \
     jq -r '.[0].networks[0].address' | cut -d'/' -f1)
   ```

8. **Troubleshooting**
   - Common issues and solutions

9. **Clean Up**
   - Stop, delete, remove image

10. **Quick Reference**
    - One-command examples

### Example Service Guides

- `08-core-api.md` - Core API Service
- `09-memory-service.md` - Memory Service
- `10-graph-ai-service.md` - Graph/AI Service
- `11-business-service.md` - Business Service
- `12-admin-vendor-service.md` - Admin/Vendor Service

---

## 🔗 Integration with Existing Stack

### Current Stack (Already Using Apple CLI)

- `ninaivalaigal-dev-db` - PostgreSQL + pgvector
- `ninaivalaigal-dev-redis` - Redis cache
- `ninaivalaigal-dev-pgbouncer` - Connection pooler
- `ninaivalaigal-dev-em` - Enhanced Memory sidecar

### New Services (Stage 3)

All use same Apple CLI runtime:
- `ninaivalaigal-dev-core-api`
- `ninaivalaigal-dev-memory`
- `ninaivalaigal-dev-graph-ai`
- `ninaivalaigal-dev-business`
- `ninaivalaigal-dev-admin`

### Networking

All containers share same network:
```bash
# Services can discover each other by container name or IP
DB_IP=$(container inspect ninaivalaigal-dev-db | ...)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | ...)
```

---

## ✅ Best Practices

### 1. Always Use `--no-cache` After Dependency Changes
```bash
# Force rebuild to pick up new dependencies
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
```

**Why**: Container layer caching can keep old dependency layers

### 2. Verify Dependencies in Built Image
```bash
container run --rm nina-api:arm64 pip list | grep [dependency]
```

### 3. Test Before Deploying
```bash
container run --rm nina-api:arm64 python -c "import [module]; print('✅ works')"
```

### 4. Document Build Method Used
In how-to guides, always show both methods and note which is preferred.

### 5. Keep How-To Guides Updated
When building or modifying containers, immediately update the corresponding how-to guide.

---

## 📊 Performance Comparison

| Metric | Docker (x86 emulation) | Apple Container CLI (native ARM64) |
|--------|------------------------|-------------------------------------|
| Build Time | 2-5 minutes | 1-2 minutes |
| Startup Time | 10-20 seconds | 3-5 seconds |
| Runtime Performance | 100% (baseline) | 300-500% (3-5x faster) |
| Memory Overhead | Higher (emulation) | Lower (native) |

---

## 🚧 Known Issues & Workarounds

### Issue 1: DNS Resolution During Build
**Symptom**: `apt-get update` fails, pip package downloads fail
**Solution**: Use Docker build + transfer method

### Issue 2: Container Networking
**Symptom**: Services can't reach each other
**Solution**: Use container IP discovery with `container inspect`

### Issue 3: Health Check Failures
**Symptom**: Container starts but health check fails
**Solution**: Ensure `curl` is installed in Dockerfile

---

## 📋 Stage 3 Checklist

### Week 1
- [ ] Create Dockerfile for each service
- [ ] Test both build methods for each service
- [ ] Create how-to guide for each service
- [ ] Document any DNS workarounds used

### Week 2
- [ ] Create docker-compose configurations (reference only)
- [ ] Update Makefile with Apple CLI commands
- [ ] Test service-to-service communication
- [ ] Validate health checks

### Week 3
- [ ] Migrate code to service directories
- [ ] Test independent service deployment
- [ ] Update all documentation
- [ ] Complete Stage 3 report

---

## 📚 Related Documentation

- **Existing How-To Guides**: `how-to/container-builds/apple/`
- **Standards**: `how-to/container-builds/apple/STANDARDS.md`
- **Lessons Learned**: `how-to/container-builds/apple/LESSONS-LEARNED.md`
- **Stage 3 Plan**: `docs/architecture/spec-100-stage3-plan.md`

---

## 🎯 Success Criteria

✅ All 5 services build successfully (either method)
✅ All 5 services run with Apple Container CLI
✅ Service-to-service communication working
✅ How-to guides complete for all services
✅ No Docker containers running (only Apple CLI)
✅ Performance meets expectations (native ARM64)

---

**Primary Runtime**: Apple Container CLI
**Build Strategy**: Try direct build first, fall back to Docker if needed
**Documentation**: Keep how-to guides current
**Goal**: Native ARM64 performance for all services

**Last Updated**: 2025-10-15
**Status**: Active Strategy for Stage 3
