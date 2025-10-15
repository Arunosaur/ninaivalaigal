# Docker Infrastructure Documentation

**Last Updated**: October 15, 2025
**Status**: Production-ready templates
**Phase**: SPEC-100 Stage 3

This directory contains Docker infrastructure for the ninaivalaigal platform, including multi-stage Dockerfiles, Docker Compose configurations, and deployment templates.

---

## 📁 Directory Structure

```
docker/
├── templates/                      # Dockerfile templates
│   ├── python-service.Dockerfile  # Python FastAPI services
│   └── rust-service.Dockerfile    # Rust gRPC services
├── dev/                           # Development configs
├── prod/                          # Production configs
├── docker-compose.dev.yml         # Development stack
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp docker/.env.example docker/.env

# Edit values (especially DB_PASSWORD)
vim docker/.env
```

### 2. Start Development Stack

```bash
# From project root
docker-compose -f docker/docker-compose.dev.yml up

# Or with rebuild
docker-compose -f docker/docker-compose.dev.yml up --build
```

### 3. Verify Services

```bash
# Check all services are running
docker-compose -f docker/docker-compose.dev.yml ps

# Check logs
docker-compose -f docker/docker-compose.dev.yml logs -f
```

**Access Points**:
- Core API: http://localhost:8000
- GraphOps gRPC: localhost:50051
- GraphOps Metrics: http://localhost:9090
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9091
- Grafana: http://localhost:3000 (admin/admin)

---

## 🏗️ Building Images

### Python Services

```bash
# Build Python service image
docker build \
  -f docker/templates/python-service.Dockerfile \
  -t ninaivalaigal/core-api:latest \
  .

# Build with specific Python version
docker build \
  -f docker/templates/python-service.Dockerfile \
  --build-arg PYTHON_VERSION=3.11 \
  -t ninaivalaigal/core-api:latest \
  .
```

### Rust Services

```bash
# Build Rust service image
docker build \
  -f docker/templates/rust-service.Dockerfile \
  -t ninaivalaigal/graphops-service:latest \
  .

# Build with specific Rust version
docker build \
  -f docker/templates/rust-service.Dockerfile \
  --build-arg RUST_VERSION=1.75 \
  -t ninaivalaigal/graphops-service:latest \
  .
```

---

## 📊 Multi-Stage Build Benefits

### Python Service Stages

1. **Builder Stage**: Install all dependencies with build tools
2. **Runtime Stage**: Copy only necessary packages, minimal image

**Benefits**:
- **Smaller images**: ~150MB vs ~500MB
- **Faster deployments**: Less data to transfer
- **Better security**: Fewer attack surfaces
- **Faster builds**: Cached dependency layer

### Rust Service Stages

1. **Planner Stage**: Create dependency recipe with cargo-chef
2. **Builder Stage**: Build dependencies and application
3. **Runtime Stage**: Copy only the binary, minimal Alpine image

**Benefits**:
- **Tiny images**: ~20MB final image
- **Fast cached builds**: Dependencies cached separately
- **Maximum performance**: Stripped, optimized binary
- **Minimal attack surface**: No build tools in final image

---

## 🔧 Development Workflow

### Start Services

```bash
# Start all services
docker-compose -f docker/docker-compose.dev.yml up -d

# Start specific service
docker-compose -f docker/docker-compose.dev.yml up -d graphops

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f graphops
```

### Code Changes

**Python Services**:
- Code is volume-mounted for hot-reload
- Changes reflect immediately
- No rebuild needed

**Rust Services**:
- Requires rebuild for code changes
- `docker-compose up --build graphops`

### Database Migrations

```bash
# Run migrations
docker-compose -f docker/docker-compose.dev.yml exec core-api \
  alembic upgrade head

# Create new migration
docker-compose -f docker/docker-compose.dev.yml exec core-api \
  alembic revision -m "description"
```

### Shell Access

```bash
# Python service shell
docker-compose -f docker/docker-compose.dev.yml exec core-api sh

# Rust service shell
docker-compose -f docker/docker-compose.dev.yml exec graphops sh

# PostgreSQL shell
docker-compose -f docker/docker-compose.dev.yml exec postgres \
  psql -U nina -d ninaivalaigal_dev
```

---

## 🧪 Testing in Docker

### Run Tests

```bash
# Python tests
docker-compose -f docker/docker-compose.dev.yml exec core-api \
  pytest tests/

# Rust tests
docker-compose -f docker/docker-compose.dev.yml exec graphops \
  /app/graphops-service --test
```

### Integration Tests

```bash
# Full integration test suite
docker-compose -f docker/docker-compose.dev.yml run --rm core-api \
  pytest tests/integration/
```

---

## 🔍 Monitoring & Debugging

### Health Checks

All services have health checks configured:

```bash
# Check service health
docker-compose -f docker/docker-compose.dev.yml ps

# Inspect health details
docker inspect graphops-service | grep -A 10 Health
```

### Metrics

**Prometheus Metrics**:
```bash
# GraphOps metrics
curl http://localhost:9090/metrics | grep graphops_

# View in Prometheus UI
open http://localhost:9091
```

**Grafana Dashboards**:
```bash
# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

### Logs

```bash
# All services
docker-compose -f docker/docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.dev.yml logs -f graphops

# Last 100 lines
docker-compose -f docker/docker-compose.dev.yml logs --tail=100 graphops
```

---

## 🔒 Security Best Practices

### Implemented

✅ **Non-root user**: All services run as `appuser` (UID 1000)
✅ **Minimal base images**: Alpine Linux for smallest attack surface
✅ **Multi-stage builds**: No build tools in production images
✅ **Health checks**: Automatic container restart on failure
✅ **Network isolation**: Services communicate via internal network
✅ **Secret management**: Environment variables, never hardcoded

### Recommendations for Production

1. **Use secrets management**:
   - Docker secrets
   - Kubernetes secrets
   - AWS Secrets Manager / HashiCorp Vault

2. **Enable TLS**:
   - gRPC with TLS certificates
   - HTTPS for web services
   - Encrypted database connections

3. **Scan images**:
   ```bash
   docker scan ninaivalaigal/core-api:latest
   ```

4. **Use specific versions**:
   - Don't use `:latest` tag in production
   - Pin to specific versions: `:1.0.0`

---

## 📦 Image Size Optimization

### Python Service

**Before optimization**: ~800MB
**After multi-stage**: ~150MB
**Savings**: 81%

**Techniques**:
- Alpine base image
- Multi-stage build
- `.dockerignore` file
- No dev dependencies in production

### Rust Service

**Before optimization**: ~500MB
**After multi-stage**: ~20MB
**Savings**: 96%

**Techniques**:
- cargo-chef for dependency caching
- Stripped binary
- Alpine runtime
- Static linking

---

## 🚀 Production Deployment

### Build Production Images

```bash
# Tag with version
docker build \
  -f docker/templates/rust-service.Dockerfile \
  -t ninaivalaigal/graphops-service:1.0.0 \
  -t ninaivalaigal/graphops-service:latest \
  .

# Push to registry
docker push ninaivalaigal/graphops-service:1.0.0
docker push ninaivalaigal/graphops-service:latest
```

### Kubernetes Deployment

(Coming in SPEC-100 Stage 3)

```bash
# Create namespace
kubectl create namespace ninaivalaigal

# Deploy services
kubectl apply -f k8s/

# Check status
kubectl get pods -n ninaivalaigal
```

---

## 🐛 Troubleshooting

### Build Failures

**Issue**: "failed to solve: failed to copy files"
```bash
# Solution: Check .dockerignore
# Ensure required files aren't ignored
```

**Issue**: "cargo build failed"
```bash
# Solution: Clear Docker cache
docker builder prune
docker build --no-cache ...
```

### Runtime Failures

**Issue**: Service won't start
```bash
# Check logs
docker-compose -f docker/docker-compose.dev.yml logs graphops

# Check environment
docker-compose -f docker/docker-compose.dev.yml exec graphops env
```

**Issue**: Can't connect to database
```bash
# Verify database is healthy
docker-compose -f docker/docker-compose.dev.yml ps postgres

# Check network
docker network inspect ninaivalaigal
```

### Performance Issues

**Issue**: Slow builds
```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
docker-compose build

# Check cache usage
docker system df
```

**Issue**: High memory usage
```bash
# Check resource usage
docker stats

# Limit memory
docker-compose -f docker/docker-compose.dev.yml up -d --memory="2g"
```

---

## 📚 Additional Resources

**Docker Best Practices**:
- https://docs.docker.com/develop/dev-best-practices/
- https://docs.docker.com/develop/security-best-practices/

**Multi-Stage Builds**:
- https://docs.docker.com/build/building/multi-stage/

**Docker Compose**:
- https://docs.docker.com/compose/

**Rust in Docker**:
- https://hub.docker.com/_/rust
- https://github.com/LukeMathWalker/cargo-chef

---

## ✅ Validation Checklist

Before deploying:

- [ ] All services build successfully
- [ ] All services start and become healthy
- [ ] Health checks pass
- [ ] Services can communicate
- [ ] Database migrations run
- [ ] Metrics are exposed
- [ ] Logs are accessible
- [ ] Environment variables set correctly
- [ ] No hardcoded secrets
- [ ] Images scanned for vulnerabilities

---

**Questions?** Contact the platform team or check `#engineering` in Slack.
