# Docker - Do Not Dos
**Critical mistakes to avoid - Learn from pain**

---

## 🚫 NEVER Build Only One Architecture Without Testing the Other

### What NOT to do
```bash
# DON'T build only ARM64 and assume it works everywhere
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker push ghcr.io/arunosaur/ninaivalaigal-core-api:arm64

# Then deploy to x86-64 cloud instance
# ❌ Fails: "exec format error" or "Illegal instruction"
```

### Why
- ARM64 images won't run on x86-64 systems
- x86-64 images won't run optimally on ARM64
- Production may need different architectures
- **This caused deployment failures in production**

### What TO do instead
```bash
# Build BOTH architectures
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context . \
  --arch arm64,amd64

# Test both locally
docker run --rm --platform linux/arm64 nina-core-api:arm64 python --version
docker run --rm --platform linux/amd64 nina-core-api:amd64 python --version

# Build multi-arch manifest for registry
./scripts/build-docker-service.sh core-api \
  --dockerfile services/core-api/Dockerfile \
  --context . \
  --multi-arch \
  --push
```

---

## 🚫 NEVER Use Cached Builds After Dependency Changes

### What NOT to do
```bash
# You updated requirements.txt
# DON'T do this:
docker build --platform linux/arm64 -t nina-core-api:arm64 .
```

### Why
- Docker layer caching keeps old dependency layers
- New dependencies won't be installed
- Container will crash at runtime with "ModuleNotFoundError"
- **We wasted hours debugging this on multiple occasions**

### What TO do instead
```bash
# ALWAYS use --no-cache after:
# - requirements.txt changes
# - package.json changes
# - Cargo.toml changes
# - Dockerfile changes
# - Base image updates

docker build --platform linux/arm64 --no-cache -t nina-core-api:arm64 .

# Then verify
docker run --rm nina-core-api:arm64 pip list | grep {new_dependency}
```

---

## 🚫 NEVER Skip Platform Specification in Build Commands

### What NOT to do
```bash
# DON'T build without --platform
docker build -t nina-core-api:latest .
```

### Why
- May default to wrong architecture
- Can't control which platform builds
- Multi-arch builds require explicit platforms
- **Builds may fail on wrong architecture**

### What TO do instead
```bash
# ALWAYS specify platform explicitly
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker build --platform linux/amd64 -t nina-core-api:amd64 .

# For multi-arch
docker buildx build --platform linux/arm64,linux/amd64 \
  -t nina-core-api:latest .
```

---

## 🚫 NEVER Assume Multi-Arch Manifests Work Without Verification

### What NOT to do
```bash
# Build multi-arch manifest
docker buildx build --platform linux/arm64,linux/amd64 \
  -t nina-core-api:latest \
  --push

# Assume it works without checking
```

### Why
- Manifest may not include both architectures
- Registry may have issues
- One architecture might have failed silently
- **Production deployments failed because only one arch was available**

### What TO do instead
```bash
# Build multi-arch
docker buildx build --platform linux/arm64,linux/amd64 \
  -t nina-core-api:latest \
  --push

# Verify manifest
docker manifest inspect nina-core-api:latest

# Should show:
# - linux/arm64
# - linux/amd64

# Test both architectures
docker pull --platform linux/arm64 nina-core-api:latest
docker pull --platform linux/amd64 nina-core-api:latest
```

---

## 🚫 NEVER Use Legacy `nv-*` Naming

### What NOT to do
```bash
# DON'T use old naming
docker run -d --name nv-db ...
docker run -d --name nv-api ...
```

### Why
- Violates naming standards
- Conflicts with new naming
- Hard to distinguish from new containers
- **We archived 31 scripts using this naming**

### What TO do instead
```bash
# ALWAYS use standard naming
docker run -d --name ninaivalaigal-dev-db ...
docker run -d --name ninaivalaigal-dev-core-api ...
```

---

## 🚫 NEVER Skip Build Verification

### What NOT to do
```bash
# Build and immediately deploy without testing
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker run -d --name ninaivalaigal-dev-core-api nina-core-api:arm64

# Then discover it crashes
```

### Why
- Runtime failures are harder to debug
- Wastes time restarting/rebuilding
- May affect other services
- **API crashed multiple times due to missing dependencies**

### What TO do instead
```bash
# Build
docker build --platform linux/arm64 --no-cache -t nina-core-api:arm64 .

# Verify dependencies
docker run --rm nina-core-api:arm64 pip list | grep fastapi
docker run --rm nina-core-api:arm64 python -c "import fastapi; print('OK')"

# Test startup
docker run --rm nina-core-api:arm64 python -c "from server.main import app; print('OK')"

# THEN deploy
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  nina-core-api:arm64

# Verify health
sleep 10
curl http://localhost:13370/health
```

---

## 🚫 NEVER Hardcode Secrets in Dockerfiles

### What NOT to do
```dockerfile
# DON'T put secrets in Dockerfile
ENV POSTGRES_PASSWORD=change_me_securely
ENV REDIS_PASSWORD=nina_redis_dev_password
ENV JWT_SECRET=test-jwt-secret-for-ci
```

### Why
- Security risk
- Gets committed to git
- Hard to change per environment
- **Found 7 secret patterns across 47 files**

### What TO do instead
```dockerfile
# Use ARG with no default for build-time secrets (if needed)
ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Better: Use runtime environment variables
# Don't set secrets in Dockerfile at all
```

```bash
# Pass at runtime
docker run -d \
  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \  # pragma: allowlist secret
  -e REDIS_PASSWORD="${REDIS_PASSWORD}" \  # pragma: allowlist secret
  --env-file configs/env-dev.env \
  ninaivalaigal-dev-db
```

---

## 🚫 NEVER Skip Multi-Architecture Testing

### What NOT to do
```bash
# Build both architectures
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker build --platform linux/amd64 -t nina-core-api:amd64 .

# Deploy without testing both
docker run -d --name ninaivalaigal-dev-core-api nina-core-api:arm64
# Never test amd64 version
```

### Why
- x86-64 version may have different issues
- Some dependencies are architecture-specific
- Production may need different architecture
- **We discovered Rust memory-service issues on x86-64 only**

### What TO do instead
```bash
# Build both
docker build --platform linux/arm64 -t nina-core-api:arm64 .
docker build --platform linux/amd64 -t nina-core-api:amd64 .

# Test both
docker run --rm --platform linux/arm64 nina-core-api:arm64 python --version
docker run --rm --platform linux/amd64 nina-core-api:amd64 python --version

# Test health checks
docker run --rm --platform linux/arm64 -p 13370:8000 nina-core-api:arm64 &
sleep 5
curl http://localhost:13370/health
docker stop $(docker ps -q --filter ancestor=nina-core-api:arm64)

docker run --rm --platform linux/amd64 -p 13370:8000 nina-core-api:amd64 &
sleep 5
curl http://localhost:13370/health
docker stop $(docker ps -q --filter ancestor=nina-core-api:amd64)
```

---

## 🚫 NEVER Use Wrong Build Context

### What NOT to do
```bash
# DON'T use wrong context
cd services/core-api
docker build --platform linux/arm64 -t nina-core-api:arm64 .
# ❌ Fails: Can't find shared/contracts, alembic, etc.
```

### Why
- Python services need project root as context
- Rust/Go services need service directory
- Missing files cause build failures
- **Builds failed with "file not found" errors**

### What TO do instead
```bash
# Python services: Use project root (.)
cd /Users/swami/WorkSpace/ninaivalaigal
docker build --platform linux/arm64 \
  -t nina-core-api:arm64 \
  -f services/core-api/Dockerfile .

# Rust services: Use service directory
docker build --platform linux/arm64 \
  -t nina-memory-service:arm64 \
  -f rust-services/memory-service/Dockerfile \
  rust-services/memory-service

# Go services: Use service directory
docker build --platform linux/arm64 \
  -t nina-grpc-gateway:arm64 \
  -f go-services/grpc-gateway/Dockerfile \
  go-services/grpc-gateway
```

---

## 🚫 NEVER Ignore Buildx Errors

### What NOT to do
```bash
# Buildx fails with platform error
docker buildx build --platform linux/arm64,linux/amd64 ...

# Error: "failed to solve: failed to load cache key"
# Ignore and try again
docker buildx build --platform linux/arm64,linux/amd64 ...
# Still fails
```

### Why
- Buildx requires proper setup
- Builder instance may not be initialized
- May need to create builder instance
- **Multi-arch builds failed until buildx was properly configured**

### What TO do instead
```bash
# 1. Check buildx status
docker buildx ls

# 2. Create builder if needed
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# 3. Verify builder supports platforms
docker buildx inspect | grep -A 5 "Platforms"

# 4. Then build
docker buildx build --platform linux/arm64,linux/amd64 ...
```

---

## 🚫 NEVER Start Containers Out of Order

### What NOT to do
```bash
# DON'T start API before database
docker run -d --name ninaivalaigal-dev-core-api ...
docker run -d --name ninaivalaigal-dev-db ...

# DON'T start PgBouncer before database
docker run -d --name ninaivalaigal-dev-pgbouncer ...
```

### Why
- Services can't connect
- Will fail health checks
- May crash immediately
- **API failed because Redis wasn't ready**

### What TO do instead
```bash
# ALWAYS start in correct order with wait times

# 1. Database
docker run -d --name ninaivalaigal-dev-db ...
sleep 15  # Wait for init

# 2. Redis
docker run -d --name ninaivalaigal-dev-redis ...
sleep 3

# 3. PgBouncer
docker run -d --name ninaivalaigal-dev-pgbouncer ...
sleep 5

# 4. Services
docker run -d --name ninaivalaigal-dev-core-api ...
sleep 10

# 5. Verify each service
curl http://localhost:13370/health
```

---

## 🚫 NEVER Skip Documentation Updates

### What NOT to do
```bash
# Make changes
docker build --platform linux/arm64 --no-cache -t nina-core-api:arm64 .

# Deploy
docker run -d --name ninaivalaigal-dev-core-api nina-core-api:arm64

# Done! (No documentation)
```

### Why
- Future you forgets what you did
- Others can't understand changes
- Can't debug issues later
- **We repeated same mistakes because documentation was missing**

### What TO do instead
```bash
# After ANY container change:

# 1. Update the container's build document
vim how-to/container-builds/docker/04-core-api.md

# 2. Document what changed and why
git commit -m "build(core-api): add structlog dependency for logging

- Added structlog==23.2.0 to requirements.txt
- Rebuilt with --no-cache for both ARM64 and x86-64
- Verified import works on both architectures
- Fixes logging issues in production"

# 3. Update LESSONS-LEARNED if you learned something
```

---

## Summary: Critical Don'ts

1. ❌ **NEVER build only one architecture**
2. ❌ **NEVER skip `--no-cache` after changes**
3. ❌ **NEVER skip platform specification**
4. ❌ **NEVER assume multi-arch manifests work**
5. ❌ **NEVER use legacy `nv-*` naming**
6. ❌ **NEVER skip build verification**
7. ❌ **NEVER hardcode secrets**
8. ❌ **NEVER skip multi-arch testing**
9. ❌ **NEVER use wrong build context**
10. ❌ **NEVER ignore buildx errors**
11. ❌ **NEVER start containers out of order**
12. ❌ **NEVER skip documentation**

**When in doubt, refer to this document. These are lessons learned the hard way.**

---

**Last Updated**: 2025-01-31
**Part of**: SPEC-145 Multi-Runtime Multi-Architecture Builds
