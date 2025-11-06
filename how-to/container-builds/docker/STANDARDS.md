# Docker - Standards
**Mandatory naming and configuration standards for Docker builds**

---

## Container Naming Convention

### Pattern
```
ninaivalaigal-{environment}-{service}
```

### Environments
- `dev` - Development (local)
- `test` - Testing/CI
- `prod` - Production

### Services
- `db` - PostgreSQL database
- `redis` - Redis cache
- `pgbouncer` - PgBouncer connection pooler
- `core-api` - FastAPI backend
- `business-service` - Business logic service
- `admin-vendor-service` - Admin vendor service
- `memory-service` - Memory service (Rust)
- `graph-service` - Graph service
- `grpc-gateway` - gRPC gateway (Go)

### Examples
```bash
✅ ninaivalaigal-dev-db
✅ ninaivalaigal-dev-core-api
✅ ninaivalaigal-prod-memory-service
✅ ninaivalaigal-test-graph-service

❌ nv-db                    # Legacy naming
❌ nina-intelligence-db     # Inconsistent
❌ db                       # Too generic
❌ ninaivalaigal_dev_db     # Wrong separator
```

---

## Image Naming Convention

### Development Images
```
nina-{service}:arm64
nina-{service}:amd64
nina-{service}:latest
```

### Production Images (Registry)
```
ghcr.io/arunosaur/ninaivalaigal-{service}:latest
ghcr.io/arunosaur/ninaivalaigal-{service}:{version}
ghcr.io/arunosaur/ninaivalaigal-{service}:latest-arm64
ghcr.io/arunosaur/ninaivalaigal-{service}:latest-amd64
```

### Multi-Architecture Manifests
```
nina-{service}:latest  # Multi-arch manifest (points to both arm64 and amd64)
ghcr.io/arunosaur/ninaivalaigal-{service}:latest  # Multi-arch in registry
```

### Examples
```bash
# Local development (single arch)
docker images | grep nina-core-api
# nina-core-api    arm64    abc123    1 hour ago    1.2GB
# nina-core-api    amd64    def456    1 hour ago    1.1GB

# Multi-arch manifest
docker manifest inspect nina-core-api:latest
# Shows both linux/arm64 and linux/amd64

# Registry (multi-arch)
ghcr.io/arunosaur/ninaivalaigal-core-api:latest
```

---

## Port Allocation

All ports follow `config/ports.nv.yaml`:

### Docker Dev Environment
- **core-api**: 13370
- **business-service**: 13371
- **admin-vendor-service**: 13372
- **memory-service**: 13373
- **graph-service**: 13374
- **grpc-gateway**: 13375

### Docker Test Environment
- **core-api**: 13470 (+100 offset)
- **business-service**: 13471
- **admin-vendor-service**: 13472
- **memory-service**: 13473
- **graph-service**: 13474
- **grpc-gateway**: 13475

### Docker Prod Environment
- **core-api**: 13570 (+200 offset)
- **business-service**: 13571
- **admin-vendor-service**: 13572
- **memory-service**: 13573
- **graph-service**: 13574
- **grpc-gateway**: 13575

See `config/ports.nv.yaml` for complete port matrix.

---

## Multi-Architecture Build Standards

### Build Method
**ALWAYS use Docker buildx** for multi-architecture builds:

```bash
# Build both architectures separately (recommended for local)
./scripts/build-docker-service.sh {service} \
  --dockerfile {path} \
  --context {context} \
  --arch arm64,amd64

# Build multi-arch manifest (for registry)
./scripts/build-docker-service.sh {service} \
  --dockerfile {path} \
  --context {context} \
  --multi-arch
```

### Platform Specification
**ALWAYS specify platform** explicitly:

```bash
# ✅ Correct
docker build --platform linux/arm64 ...
docker build --platform linux/amd64 ...
docker buildx build --platform linux/arm64,linux/amd64 ...

# ❌ Wrong (may default to wrong platform)
docker build ...
```

### Architecture Tagging
**Tag images with architecture** for clarity:

```bash
# Single architecture
docker build --platform linux/arm64 -t nina-core-api:arm64 ...
docker build --platform linux/amd64 -t nina-core-api:amd64 ...

# Multi-arch manifest (points to both)
docker buildx build --platform linux/arm64,linux/amd64 \
  -t nina-core-api:latest \
  --push
```

---

## Environment Variables

### Standard Variables
**ALL containers MUST support**:
```bash
NINA_ENV=dev|test|prod
LOG_LEVEL=debug|info|warning|error
```

### Database Containers
```bash
POSTGRES_DB=nina
POSTGRES_USER=nina
POSTGRES_PASSWORD={secure_password}
```

### Service Containers
```bash
DATABASE_URL=postgresql://{user}:{pass}@{host}:{port}/{db}  # pragma: allowlist secret
REDIS_URL=redis://:{password}@{host}:{port}/0
NINAIVALAIGAL_JWT_SECRET={secure_secret}
```

### Load from Environment Files
```bash
# Load from configs/env-{env}.env
source configs/env-dev.env
docker run -d --name ninaivalaigal-dev-{service} \
  --env-file configs/env-dev.env \
  nina-{service}:{arch}
```

---

## Build Standards

### Always Use --no-cache After:
- Dockerfile changes
- Dependency updates (requirements.txt, package.json, Cargo.toml)
- Base image updates
- COPY/ADD instruction changes

```bash
# ✅ Correct
docker build --platform linux/arm64 --no-cache -t nina-core-api:arm64 .

# ❌ Wrong (after changes)
docker build --platform linux/arm64 -t nina-core-api:arm64 .
```

### Build Context
**Python services** (core-api, business-service, etc.):
```bash
# Context: project root (.)
docker build --platform linux/arm64 \
  -t nina-core-api:arm64 \
  -f services/core-api/Dockerfile .
```

**Rust services** (memory-service):
```bash
# Context: service directory
docker build --platform linux/arm64 \
  -t nina-memory-service:arm64 \
  -f rust-services/memory-service/Dockerfile \
  rust-services/memory-service
```

**Go services** (grpc-gateway):
```bash
# Context: service directory
docker build --platform linux/arm64 \
  -t nina-grpc-gateway:arm64 \
  -f go-services/grpc-gateway/Dockerfile \
  go-services/grpc-gateway
```

### Verification After Build
```bash
# 1. Verify image exists and architecture
docker images | grep nina-{service}
docker inspect nina-{service}:arm64 | jq -r '.[0].Architecture'
# Should output: arm64

# 2. Test image runs
docker run --rm nina-{service}:arm64 {health_check_command}

# 3. Verify dependencies
docker run --rm nina-core-api:arm64 pip list | grep fastapi
docker run --rm nina-memory-service:arm64 /usr/local/bin/memory-service --version
```

---

## Container Lifecycle

### Startup Order
**MUST start in this order**:
1. Database (`ninaivalaigal-dev-db`)
2. Redis (`ninaivalaigal-dev-redis`)
3. PgBouncer (`ninaivalaigal-dev-pgbouncer`)
4. Core API (`ninaivalaigal-dev-core-api`)
5. Business Service (`ninaivalaigal-dev-business-service`)
6. Memory Service (`ninaivalaigal-dev-memory-service`)
7. Graph Service (`ninaivalaigal-dev-graph-service`)
8. gRPC Gateway (`ninaivalaigal-dev-grpc-gateway`)

### Shutdown Order
**MUST stop in reverse order**

### Wait Times
```bash
# After starting database
sleep 15  # Wait for init scripts

# After starting Redis
sleep 3

# After starting PgBouncer
sleep 5

# After starting services
sleep 10
```

---

## Networking

### Container-to-Container Communication
**Use container names** (Docker supports DNS):

```bash
# Docker supports hostname resolution
DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina"  # pragma: allowlist secret

# Or use IP (more explicit)
DB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-db)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret
```

### Network Inspection
```bash
# Get container IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {name}

# List networks
docker network ls

# Inspect network
docker network inspect bridge
```

---

## Health Checks

### Core API
```bash
curl http://localhost:13370/health
curl http://localhost:13370/docs
```

### Memory Service
```bash
curl http://localhost:13373/health
```

### Graph Service
```bash
curl http://localhost:13374/health
```

### Database
```bash
docker exec ninaivalaigal-dev-db pg_isready -U nina
docker exec ninaivalaigal-dev-db psql -U nina -d nina -c "SELECT 1;"
```

### Redis
```bash
docker exec ninaivalaigal-dev-redis redis-cli ping
```

---

## Multi-Architecture Testing

### Test Both Architectures
```bash
# Test ARM64
docker run --rm --platform linux/arm64 nina-core-api:arm64 python --version

# Test x86-64
docker run --rm --platform linux/amd64 nina-core-api:amd64 python --version

# Verify correct architecture
docker inspect nina-core-api:arm64 | jq -r '.[0].Architecture'
docker inspect nina-core-api:amd64 | jq -r '.[0].Architecture'
```

### Cross-Platform Verification
```bash
# Check multi-arch manifest
docker manifest inspect nina-core-api:latest

# Should show:
# - linux/arm64
# - linux/amd64
```

---

## Security

### Passwords
**NEVER hardcode in**:
- Dockerfiles
- Source code
- Git repositories

**ALWAYS use**:
- Environment variables
- Secrets management
- `.env` files (git-ignored)

### User Permissions
```dockerfile
# Run as non-root when possible
RUN useradd -m -u 1000 appuser
USER appuser
```

### Image Scanning
```bash
# Scan for vulnerabilities
docker scan nina-core-api:arm64
docker scan nina-core-api:amd64
```

---

## Compliance

### Must Follow
- ✅ Use standard naming convention
- ✅ Use standard ports from `config/ports.nv.yaml`
- ✅ Build both ARM64 and x86-64
- ✅ Document all changes
- ✅ Use `--no-cache` after changes
- ✅ Verify after build
- ✅ Test health checks
- ✅ Load environment from `configs/env-{env}.env`

### Must Not Do
- ❌ Use legacy `nv-*` naming
- ❌ Hardcode secrets
- ❌ Skip documentation
- ❌ Skip verification
- ❌ Build only one architecture
- ❌ Use cached builds after changes
- ❌ Skip multi-arch testing

---

**Last Updated**: 2025-01-31
**Part of**: SPEC-145 Multi-Runtime Multi-Architecture Builds
