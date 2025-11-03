# Rust Memory Service - Deployment Guide

**Service**: Memory CRUD Operations
**Language**: Rust
**Port**: 13393 (dev), 13493 (test), 13593 (prod)
**Standard**: Follows `docs/standards/CONTAINERIZATION_STANDARD.md`

---

## Quick Start

### 1. Build and Deploy

```bash
# From rust-services/memory-service directory
make deploy
```

This will:
1. Build Docker image for ARM64
2. Export to tar
3. Load into Apple Container CLI

### 2. Start Service

```bash
# From project root
./scripts/nv-memory-service-start.sh
```

### 3. Verify Health

```bash
curl http://localhost:13393/health
```

---

## Development Workflow

### Local Development

```bash
# Build Rust binary locally
make build

# Run tests
make test

# Build Docker image
make docker-build
```

### Deployment Workflow

```bash
# Full deployment (build + export + load)
make deploy

# Quick iteration (rebuild without timestamp)
make quick-deploy

# Start service
cd ../../scripts
./nv-memory-service-start.sh

# Check logs
container logs -f ninaivalaigal-dev-memory-service

# Stop service
./nv-memory-service-stop.sh
```

---

## Configuration

### Environment Variables

Required (from `.env.dev`):
- `NINA_ENV` - Environment (dev/test/prod)
- `NINA_DB_USER` - Database user
- `NINA_DB_PASSWORD` - Database password
- `NINA_DB_NAME` - Database name

Optional:
- `MEMORY_CACHE_TTL_SECONDS` - Cache TTL (default: 3600)
- `LOG_LEVEL` - Log level (default: info)
- `NINA_JWT_SECRET` - JWT secret for authentication

### Port Allocation

From `config/ports.nv.yaml`:
- **Dev**: 13393
- **Test**: 13493
- **Prod**: 13593

---

## Architecture

### Container Layers

**Builder Stage**:
- Base: `rust:1.75-alpine`
- Dependencies: musl-dev, postgresql-dev, openssl
- Optimization: Dependency caching with dummy main.rs
- Output: Stripped static binary

**Runtime Stage**:
- Base: `alpine:3.18` (minimal)
- Runtime deps: ca-certificates, libpq, libgcc
- Security: Non-root user (nina:nina, UID 1000)
- Health: `/health` endpoint check every 30s

### Dependencies

**Database**:
- Connects to PostgreSQL via PgBouncer (session mode)
- Dynamic IP discovery at startup
- Connection pooling via sqlx

**Redis**:
- Cache layer for memory operations
- TTL-based expiration
- Dynamic IP discovery

**Authentication**:
- JWT-based authentication
- Bearer token in Authorization header
- User context propagation

---

## API Endpoints

### Health

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "memory-service",
  "language": "rust",
  "database": {
    "connected": true,
    "pool_size": 10
  },
  "cache": {
    "connected": true,
    "ttl_seconds": 3600
  }
}
```

### Memory Operations

All require `Authorization: Bearer <token>` header.

**Create Memory**:
```bash
POST /memory/remember
Content-Type: application/json
Authorization: Bearer <token>

{
  "content": "Memory content",
  "metadata": {}
}
```

**Recall Memories**:
```bash
POST /memory/recall
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "search query",
  "limit": 10
}
```

**List Memories**:
```bash
GET /memory/memories
Authorization: Bearer <token>
```

**Delete Memory**:
```bash
DELETE /memory/memories/:id
Authorization: Bearer <token>
```

### Documentation

- **Swagger UI**: http://localhost:13393/docs
- **OpenAPI JSON**: http://localhost:13393/api-docs/openapi.json

---

## Troubleshooting

### Build Failures

**Issue**: Dependency compilation errors
```bash
# Clean and rebuild
make clean
make build
```

**Issue**: OpenSSL linking errors
```bash
# Ensure openssl-dev installed in Dockerfile
# Already included in current Dockerfile
```

### Runtime Issues

**Issue**: Container exits immediately
```bash
# Check logs
container logs ninaivalaigal-dev-memory-service

# Common causes:
# - Missing DATABASE_URL
# - Database not reachable
# - Redis not reachable
```

**Issue**: Health check failing
```bash
# Verify dependencies
./scripts/nv-db-start.sh
./scripts/nv-redis-start.sh

# Check container IP resolution
container inspect ninaivalaigal-dev-memory-service
```

**Issue**: Cannot connect to database
```bash
# Verify PgBouncer is running
container list | grep pgbouncer

# Test database connectivity
psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev
```

### Network Issues

**Issue**: Container can't reach database/redis
```bash
# Verify dynamic IP discovery
container inspect ninaivalaigal-dev-db | jq '.[0].networks[0].address'
container inspect ninaivalaigal-dev-redis | jq '.[0].networks[0].address'

# Restart dependencies
./scripts/nv-db-start.sh
./scripts/nv-redis-start.sh
```

---

## Performance

### Build Times

- **First build**: 5-10 minutes (dependency compilation)
- **Incremental build**: 1-2 minutes (cached dependencies)
- **Image size**: ~50MB (Alpine-based)

### Runtime Performance

- **Cold start**: <2 seconds
- **Health check**: <10ms
- **Memory operations**: <50ms (cached), <200ms (uncached)

### Resource Limits

- **Memory**: 1GB (configured in startup script)
- **CPU**: 4 cores (configured in startup script)

---

## Files Overview

```
rust-services/memory-service/
├── Dockerfile              # Production-ready multi-stage build
├── Makefile               # Build, export, deploy targets
├── Cargo.toml             # Rust dependencies
├── DEPLOYMENT.md          # This file
├── src/
│   ├── main.rs           # Service entry point
│   ├── auth.rs           # JWT authentication
│   ├── cache.rs          # Redis caching layer
│   ├── storage.rs        # PostgreSQL storage
│   ├── models.rs         # Data models
│   └── telemetry.rs      # OpenTelemetry tracing
└── benchmarks/           # Performance benchmarks

scripts/
├── nv-memory-service-start.sh   # Start service (Apple Container CLI)
└── nv-memory-service-stop.sh    # Stop service
```

---

## Next Steps

1. **Integration Testing**: Test with core-api proxy layer
2. **Load Testing**: Use Developer A's load tester
3. **Monitoring**: Add Prometheus metrics export
4. **Scaling**: Configure horizontal pod autoscaling in K8s

---

## Related Documentation

- **Containerization Standard**: `docs/standards/CONTAINERIZATION_STANDARD.md`
- **Port Registry**: `config/ports.nv.yaml`
- **Developer A Guide**: `docs/guides/DEVELOPER_A_CONTAINER_DEPLOYMENT.md`
- **SPEC-099**: Rust Migration Strategy

---

**Status**: ✅ Production-ready following containerization standard
**Last Updated**: October 31, 2025
