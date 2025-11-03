# Ninaivalaigal Containerization Standard

**Version**: 1.0
**Last Updated**: October 31, 2025
**Status**: CANONICAL REFERENCE

This document defines the **complete, authoritative containerization standard** for all Ninaivalaigal services. Follow this standard for all new service deployments.

---

## Table of Contents

1. [Port Standards](#1-port-standards)
2. [Container Naming Standards](#2-container-naming-standards)
3. [Environment Variables & Secrets](#3-environment-variables--secrets)
4. [Dynamic IP Discovery](#4-dynamic-ip-discovery)
5. [Docker Build Process](#5-docker-build-process)
6. [Tar Export for Apple Container CLI](#6-tar-export-for-apple-container-cli)
7. [Apple Container CLI Deployment](#7-apple-container-cli-deployment)
8. [Complete Example: Rust Memory Service](#8-complete-example-rust-memory-service)

---

## 1. Port Standards

**Reference**: `config/ports.nv.yaml` (canonical source)

### Port Allocation Formula

```yaml
final_port = base_port + runtime_offset + environment_offset
```

### Base Ports

| Service | Base Port |
|---------|-----------|
| PostgreSQL | 5432 |
| PgBouncer | 6432 |
| Redis | 6379 |
| Core API | 13370 |
| Memory Service (Rust) | 13393 |
| Graph Service (Rust) | 13394 |
| gRPC Gateway (Go) | 13395 |

### Runtime Offsets

| Runtime | Offset |
|---------|--------|
| Docker | 0 |
| Colima | 10 |
| Apple Container CLI | 20 |

### Environment Offsets

| Environment | Offset |
|-------------|--------|
| dev | 0 |
| test | 100 |
| prod | 200 |

### Examples

**Memory Service ports**:
- Docker dev: `13393` (13393 + 0 + 0)
- Apple Container CLI dev: `13393` (13393 + 0 + 0) ← **Container port, NOT host port**
- Apple Container CLI test: `13493` (13393 + 0 + 100)

**Rule**: Services bind to their **base port inside the container**. Host port mapping is handled by the container runtime.

---

## 2. Container Naming Standards

**Reference**: `config/ports.nv.yaml` lines 135-189

### Pattern

```bash
ninaivalaigal-{env}-{service}
```

### Environment Values

- `dev` - Development
- `test` - Testing
- `prod` - Production

### Service Names

| Service | Container Name |
|---------|----------------|
| PostgreSQL | `ninaivalaigal-{env}-db` |
| PgBouncer | `ninaivalaigal-{env}-pgbouncer` |
| Redis | `ninaivalaigal-{env}-redis` |
| Core API | `ninaivalaigal-{env}-core-api` |
| Memory Service | `ninaivalaigal-{env}-memory-service` |
| Graph Service | `ninaivalaigal-{env}-graph-service` |
| gRPC Gateway | `ninaivalaigal-{env}-grpc-gateway` |
| GraphOps | `ninaivalaigal-{env}-graphops` |

### Examples

```bash
ninaivalaigal-dev-memory-service
ninaivalaigal-test-graph-service
ninaivalaigal-prod-core-api
```

**Critical**: Environment is part of the name, NOT runtime. All runtimes use the same names per environment.

---

## 3. Environment Variables & Secrets

### Required Environment Variables

**Every service MUST accept these**:

```bash
# Environment
NINA_ENV=dev|test|prod

# Database Connection
DATABASE_URL=postgresql://{user}:{password}@{host}:{port}/{database}

# Redis Connection
REDIS_URI=redis://{host}:{port}/{db}

# Service Configuration
SERVICE_NAME={service-name}
SERVICE_ROLE={service-role}
LOG_LEVEL=debug|info|warn|error
```

### Secrets Handling

**Rule**: NEVER hardcode secrets. ALWAYS use environment variables.

**Source Order** (highest priority first):
1. `.env.{environment}` file (e.g., `.env.dev`, `.env.test`, `.env.prod`)
2. System environment variables
3. Container runtime environment (`-e` flags)

**Example `.env.dev`**:

```bash
# .env.dev - Development environment configuration
NINA_ENV=dev
NINA_DB_USER=nina
NINA_DB_PASSWORD=dev_password_change_in_production  # pragma: allowlist secret
NINA_DB_NAME=ninaivalaigal_dev
NINA_DB_HOST=ninaivalaigal-dev-db
NINA_DB_PORT=5432
PGBOUNCER_PORT=6432
REDIS_PORT=6379
```

**Security Requirements**:
1. Add `.env.*` to `.gitignore` ✅ (already done)
2. Use `.env.example` as template
3. Rotate secrets in production
4. Use `# pragma: allowlist secret` for dev passwords in committed code

### Dynamic Secrets (Production)

For production, use:
- **Kubernetes Secrets** - Mounted as volumes or env vars
- **HashiCorp Vault** - Dynamic secret generation
- **AWS Secrets Manager** - Rotated credentials

---

## 4. Dynamic IP Discovery

**Pattern**: Always resolve container IPs dynamically at runtime.

### Standard IP Discovery Function

```bash
# Resolve container IP dynamically
# Args: $1 = container name
resolve_container_ip() {
    local container_name=$1
    local container_ip

    container_ip=$(container inspect "$container_name" 2>/dev/null \
        | jq -r '.[0].networks[0].address' \
        | cut -d'/' -f1)

    if [ -z "$container_ip" ] || [ "$container_ip" = "null" ]; then
        echo "ERROR: Unable to resolve IP for container: $container_name" >&2
        return 1
    fi

    echo "$container_ip"
}
```

### Usage in Startup Scripts

```bash
# Example: Resolve database IP
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db"
DB_IP=$(resolve_container_ip "$DB_CONTAINER")

if [ $? -ne 0 ]; then
    echo "❌ Database container not running"
    echo "   Run: ./scripts/nv-db-start.sh"
    exit 1
fi

echo "✅ Database IP: $DB_IP"
```

### Why Dynamic Discovery?

1. **Container IPs change** on restart
2. **Multi-environment support** (dev, test, prod on same host)
3. **Runtime-agnostic** (works with Docker, Colima, Apple Container CLI)
4. **No hardcoded IPs** in code or configs

### Fallback Strategy

```bash
# Priority order for database connection
1. Environment variable: $NINA_DB_HOST (if set)
2. Dynamic IP discovery: resolve_container_ip
3. Localhost fallback: 127.0.0.1 (development only)
```

---

## 5. Docker Build Process

### Multi-Stage Build Pattern

**Every service Dockerfile MUST use multi-stage builds**:

```dockerfile
# Stage 1: Builder
FROM rust:1.75-alpine AS builder
WORKDIR /build
# ... build process ...

# Stage 2: Runtime (minimal)
FROM alpine:3.18
COPY --from=builder /build/target/release/app /usr/local/bin/
CMD ["/usr/local/bin/app"]
```

### Platform-Specific Builds

**Always specify platform**:

```bash
docker build --platform linux/arm64 -t {image}:{tag} .
docker build --platform linux/amd64 -t {image}:{tag} .
```

### Image Tagging Standard

```bash
{service-name}:arm64
{service-name}:amd64
{service-name}:latest  # Points to arm64 on Apple Silicon
```

### Build Requirements

1. **Static binaries** (no dynamic linking)
2. **Minimal base images** (alpine, distroless, scratch)
3. **Multi-arch support** (arm64 + amd64)
4. **Health check** built into image
5. **Non-root user** for security

### Example: Rust Service Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: Build
FROM rust:1.75-alpine AS builder

# Install build dependencies
RUN apk add --no-cache musl-dev postgresql-dev

WORKDIR /build

# Cache dependencies
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN rm -rf src

# Build actual service
COPY src ./src
RUN touch src/main.rs
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN strip target/x86_64-unknown-linux-musl/release/memory-service

# Stage 2: Runtime
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache ca-certificates libpq

# Create non-root user
RUN addgroup -g 1000 nina && \
    adduser -D -u 1000 -G nina nina

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/target/x86_64-unknown-linux-musl/release/memory-service /usr/local/bin/

# Switch to non-root
USER nina

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/memory-service", "--health-check"]

# Expose service port (internal container port)
EXPOSE 8000

# Run service
CMD ["/usr/local/bin/memory-service"]
```

---

## 6. Tar Export for Apple Container CLI

### Why Tar Export?

Apple Container CLI **does not** connect to Docker registry. Images must be imported via tarball.

### Export Process

```bash
# 1. Build image
docker build --platform linux/arm64 -t {service}:arm64 .

# 2. Export to tar (uncompressed)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker save {service}:arm64 -o /tmp/{service}-${TIMESTAMP}.tar

# 3. Verify tar
ls -lh /tmp/{service}-${TIMESTAMP}.tar
```

### Standard Export Script

```bash
#!/usr/bin/env bash
# export-container.sh - Standard container export

set -euo pipefail

SERVICE_NAME=$1
PLATFORM=${2:-linux/arm64}

echo "Exporting ${SERVICE_NAME} for ${PLATFORM}..."

# Build
docker build --platform "$PLATFORM" -t "${SERVICE_NAME}:arm64" .

# Export
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TARBALL="/tmp/${SERVICE_NAME}-${TIMESTAMP}.tar"

docker save "${SERVICE_NAME}:arm64" -o "$TARBALL"

echo "✅ Exported: $TARBALL"
echo "   Size: $(du -h "$TARBALL" | cut -f1)"
echo ""
echo "Import with:"
echo "   container image load -i $TARBALL"
```

### Tar Requirements

1. **Uncompressed** (no .tar.gz) - Apple Container CLI requires raw tar
2. **Platform-specific** - Must match host architecture
3. **Named with timestamp** - For version tracking
4. **Stored in /tmp** - Temporary location, clean up after import

---

## 7. Apple Container CLI Deployment

### Standard Deployment Process

```bash
# 1. Load image from tar
container image load -i /tmp/{service}-{timestamp}.tar

# 2. Verify image
container image list | grep {service}

# 3. Resolve dependency IPs
DB_IP=$(container inspect ninaivalaigal-${NINA_ENV}-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-${NINA_ENV}-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# 4. Run container
container run -d \
  --name ninaivalaigal-${NINA_ENV}-{service} \
  -p {host_port}:{container_port} \
  -e NINA_ENV=${NINA_ENV} \
  -e DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/${NINA_DB_NAME}" \
  -e REDIS_URI="redis://${REDIS_IP}:6379/0" \
  -e LOG_LEVEL=info \
  --restart always \
  --memory {memory_limit} \
  --cpus {cpu_limit} \
  {service}:arm64

# 5. Verify health
sleep 5
curl -f http://localhost:{host_port}/health
```

### Standard Startup Script Template

```bash
#!/usr/bin/env bash
# nv-{service}-start.sh - Start {Service Name}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting {Service Name}"
echo "========================================"

# Load environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment from .env.dev"
else
    echo "❌ .env.dev not found!"
    exit 1
fi

# Validate required variables
required_vars=(
    "NINA_ENV"
    "NINA_DB_USER"
    "NINA_DB_PASSWORD"
    "NINA_DB_NAME"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "❌ Required environment variable $var not set"
        exit 1
    fi
done

# Set variables
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-{service}"
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db"
REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis"
HOST_PORT={host_port}
CONTAINER_PORT={container_port}

echo ""
echo "Configuration:"
echo "  Environment: $NINA_ENV"
echo "  Container: $CONTAINER_NAME"
echo "  Port: $HOST_PORT -> $CONTAINER_PORT"
echo ""

# Resolve dependency IPs
echo "Resolving dependency endpoints..."
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$DB_IP" ] || [ "$DB_IP" = "null" ]; then
    echo "❌ Database container not found: $DB_CONTAINER"
    exit 1
fi

REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
    echo "❌ Redis container not found: $REDIS_CONTAINER"
    exit 1
fi

echo "  Database IP: $DB_IP"
echo "  Redis IP: $REDIS_IP"
echo ""

# Stop existing container
if container inspect "$CONTAINER_NAME" &>/dev/null; then
    echo "Stopping existing container..."
    container stop "$CONTAINER_NAME" 2>/dev/null || true
    container rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "  ✅ Cleaned up"
fi

# Start container
echo ""
echo "Starting container..."
container run -d \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT:$CONTAINER_PORT" \
  -e NINA_ENV="$NINA_ENV" \
  -e DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/${NINA_DB_NAME}" \
  -e REDIS_URI="redis://${REDIS_IP}:6379/0" \
  -e SERVICE_NAME="{service}" \
  -e LOG_LEVEL="${LOG_LEVEL:-info}" \
  --restart always \
  --memory {memory_limit} \
  --cpus {cpu_limit} \
  {service}:arm64

echo "✅ Container started: $CONTAINER_NAME"
echo ""

# Wait for health
echo "Waiting for service to be healthy..."
sleep 5

if curl -sf "http://localhost:$HOST_PORT/health" > /dev/null; then
    echo "✅ Service is healthy!"
    curl -s "http://localhost:$HOST_PORT/health" | jq .
else
    echo "❌ Health check failed"
    echo "   Check logs: container logs $CONTAINER_NAME"
    exit 1
fi

echo ""
echo "🎉 {Service Name} is running!"
echo "   Health: http://localhost:$HOST_PORT/health"
echo "   Logs: container logs -f $CONTAINER_NAME"
```

---

## 8. Complete Example: Rust Memory Service

### Directory Structure

```
services/memory-service/
├── Cargo.toml
├── Cargo.lock
├── Dockerfile
├── Makefile
├── README.md
└── src/
    ├── main.rs
    ├── handlers/
    ├── models/
    └── config.rs
```

### 1. Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
# Rust Memory Service - Production Dockerfile

FROM rust:1.75-alpine AS builder

RUN apk add --no-cache musl-dev postgresql-dev

WORKDIR /build

# Cache dependencies
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN rm -rf src

# Build service
COPY src ./src
RUN touch src/main.rs
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN strip target/x86_64-unknown-linux-musl/release/memory-service

# Runtime image
FROM alpine:3.18

RUN apk add --no-cache ca-certificates libpq && \
    addgroup -g 1000 nina && \
    adduser -D -u 1000 -G nina nina

WORKDIR /app

COPY --from=builder /build/target/x86_64-unknown-linux-musl/release/memory-service /usr/local/bin/

USER nina

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/memory-service", "--health-check"]

EXPOSE 8000

CMD ["/usr/local/bin/memory-service"]
```

### 2. Makefile

```makefile
.PHONY: build docker-build docker-export deploy clean

# Configuration
SERVICE_NAME := memory-service
IMAGE_NAME := ninaivalaigal-memory-service
PLATFORM := linux/arm64
TIMESTAMP := $(shell date +%Y%m%d-%H%M%S)
TARBALL := /tmp/$(SERVICE_NAME)-$(TIMESTAMP).tar

build:
	cargo build --release --target x86_64-unknown-linux-musl

docker-build:
	docker build --platform $(PLATFORM) -t $(IMAGE_NAME):arm64 .

docker-export: docker-build
	docker save $(IMAGE_NAME):arm64 -o $(TARBALL)
	@echo "✅ Exported: $(TARBALL)"
	@du -h $(TARBALL)

deploy: docker-export
	container image load -i $(TARBALL)
	@echo "✅ Image loaded into Apple Container CLI"
	@echo "Run: ./scripts/nv-memory-service-start.sh"

clean:
	cargo clean
	rm -f /tmp/$(SERVICE_NAME)-*.tar
```

### 3. Startup Script (nv-memory-service-start.sh)

```bash
#!/usr/bin/env bash
# Start Rust Memory Service

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting Rust Memory Service"
echo "======================================"

# Load environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment"
else
    echo "❌ .env.dev not found!"
    exit 1
fi

# Configuration
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db"
REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis"
HOST_PORT=13393
CONTAINER_PORT=8000

echo ""
echo "Configuration:"
echo "  Environment: $NINA_ENV"
echo "  Container: $CONTAINER_NAME"
echo "  Port: $HOST_PORT -> $CONTAINER_PORT"
echo ""

# Resolve dependency IPs
echo "Resolving dependencies..."
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

if [ -z "$DB_IP" ] || [ "$DB_IP" = "null" ]; then
    echo "❌ Database not running: $DB_CONTAINER"
    exit 1
fi

if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
    echo "❌ Redis not running: $REDIS_CONTAINER"
    exit 1
fi

echo "  Database: $DB_IP:5432"
echo "  Redis: $REDIS_IP:6379"
echo ""

# Stop existing
if container inspect "$CONTAINER_NAME" &>/dev/null; then
    echo "Stopping existing container..."
    container stop "$CONTAINER_NAME" 2>/dev/null || true
    container rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Start container
echo "Starting container..."
container run -d \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT:$CONTAINER_PORT" \
  -e NINA_ENV="$NINA_ENV" \
  -e DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/${NINA_DB_NAME}" \
  -e REDIS_URI="redis://${REDIS_IP}:6379/0" \
  -e SERVICE_NAME="memory-service" \
  -e SERVICE_ROLE="memory-crud" \
  -e LOG_LEVEL="${LOG_LEVEL:-info}" \
  --restart always \
  --memory 1g \
  --cpus 4 \
  ninaivalaigal-memory-service:arm64

echo "✅ Container started"
echo ""

# Health check
echo "Waiting for service..."
sleep 5

if curl -sf "http://localhost:$HOST_PORT/health" > /dev/null; then
    echo "✅ Service is healthy!"
    curl -s "http://localhost:$HOST_PORT/health" | jq .
else
    echo "❌ Health check failed"
    echo "   Logs: container logs $CONTAINER_NAME"
    exit 1
fi

echo ""
echo "🎉 Rust Memory Service running!"
echo "   Health: http://localhost:$HOST_PORT/health"
echo "   Docs: http://localhost:$HOST_PORT/docs"
echo "   Logs: container logs -f $CONTAINER_NAME"
```

### 4. Deployment Commands

```bash
# Full deployment workflow
cd services/memory-service

# 1. Build and export
make deploy

# 2. Start service
./scripts/nv-memory-service-start.sh

# 3. Verify
curl http://localhost:13393/health
```

---

## Summary Checklist

When containerizing a new service, ensure:

- [ ] Port assigned in `config/ports.nv.yaml`
- [ ] Container name follows `ninaivalaigal-{env}-{service}` pattern
- [ ] All secrets from environment variables (no hardcoded)
- [ ] Dynamic IP discovery for dependencies
- [ ] Multi-stage Dockerfile with health check
- [ ] Makefile with `docker-export` target
- [ ] Startup script with IP resolution
- [ ] `.env.example` updated with new service variables
- [ ] Health endpoint implemented (`/health`)
- [ ] Documentation updated

---

## References

- **Port Registry**: `config/ports.nv.yaml`
- **Example Scripts**: `scripts/nv-*-start.sh`
- **Environment Template**: `.env.example`
- **Developer Guide**: `docs/guides/DEVELOPER_A_CONTAINER_DEPLOYMENT.md`

---

**This is the canonical containerization standard. All services MUST follow these guidelines.**
