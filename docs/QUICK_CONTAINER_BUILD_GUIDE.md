# Quick Container Build Guide

**For building individual service containers in the ninaivalaigal project**

---

## 🚀 Quick Start

### Standard Build Command

```bash
./scripts/docker-to-apple-container.sh <service-name> \
    --dockerfile <path-to-dockerfile> \
    --context <build-context>
```

### 💡 Quick Troubleshooting

**Build fails?**
- ✅ Check you're in the project root directory
- ✅ Verify Dockerfile path is correct
- ✅ Verify build context includes all necessary files

**Container won't start?**
- ✅ Check logs: `container logs ninaivalaigal-dev-<service-name>`
- ✅ Verify dependencies (database, redis) are running
- ✅ Verify environment variables are set correctly

**Need more help?** See [Full Troubleshooting](#-troubleshooting) section below.

---

## 📋 Service Configurations

### Python Services (build context: project root `.`)

| Service | Dockerfile | Context | Port |
|---------|------------|---------|------|
| **core-api** | `services/core-api/Dockerfile` | `.` | 13390 |
| **business-service** | `services/business-service/Dockerfile` | `.` | 13391 |
| **admin-vendor-service** | `services/admin-vendor-service/Dockerfile` | `.` | 13392 |
| **graph-service** | `services/graph-service/Dockerfile` | `.` | 13394 |

### Rust Services (build context: service directory)

| Service | Dockerfile | Context | Port |
|---------|------------|---------|------|
| **memory-service** | `rust-services/memory-service/Dockerfile` | `rust-services/memory-service` | 13393 |

### Go Services (build context: service directory)

| Service | Dockerfile | Context | Port |
|---------|------------|---------|------|
| **grpc-gateway** | `go-services/grpc-gateway/Dockerfile` | `go-services/grpc-gateway` | 13395 |

---

## 💡 Service-Specific Examples

### Core API (most common)
```bash
./scripts/docker-to-apple-container.sh core-api \
    --dockerfile services/core-api/Dockerfile \
    --context .
```

### Memory Service (Rust)
```bash
./scripts/docker-to-apple-container.sh memory-service \
    --dockerfile rust-services/memory-service/Dockerfile \
    --context rust-services/memory-service
```

### Business Service
```bash
./scripts/docker-to-apple-container.sh business-service \
    --dockerfile services/business-service/Dockerfile \
    --context .
```

### Admin Vendor Service
```bash
./scripts/docker-to-apple-container.sh admin-vendor-service \
    --dockerfile services/admin-vendor-service/Dockerfile \
    --context .
```

### Graph Service
```bash
./scripts/docker-to-apple-container.sh graph-service \
    --dockerfile services/graph-service/Dockerfile \
    --context .
```

### gRPC Gateway (Go)
```bash
./scripts/docker-to-apple-container.sh grpc-gateway \
    --dockerfile go-services/grpc-gateway/Dockerfile \
    --context go-services/grpc-gateway
```

---

## 🔄 After Building: Restart Container

After building, restart the container to use the new image:

### Core API
```bash
./services/core-api/nv-core-api-start.sh
```

### Memory Service (Rust)
```bash
./rust-services/memory-service/nv-memory-service-start.sh
```

### Business Service
```bash
./services/business-service/nv-business-service-start.sh
```

### Graph Service
```bash
./services/graph-service/nv-graph-service-start.sh
```

### gRPC Gateway
```bash
./scripts/nv-grpc-gateway-start.sh
```

### Other Services
```bash
# Python services (core-api, business-service, graph-service):
./services/<service-name>/nv-<service-name>-start.sh

# Rust services:
./rust-services/<service-name>/nv-<service-name>-start.sh

# Go services:
./scripts/nv-<service-name>-start.sh
```

---

## 🛠️ Advanced Options

### Skip Build (use existing image)
```bash
./scripts/docker-to-apple-container.sh core-api \
    --dockerfile services/core-api/Dockerfile \
    --context . \
    --skip-build
```

### Custom Tag
```bash
./scripts/docker-to-apple-container.sh core-api \
    --dockerfile services/core-api/Dockerfile \
    --context . \
    --tag custom-tag
```

### Verbose Output
```bash
./scripts/docker-to-apple-container.sh core-api \
    --dockerfile services/core-api/Dockerfile \
    --context . \
    --verbose
```

---

## ✅ Verification

### Check if image was built
```bash
container image list | grep nina-<service-name>
```

### Check if container is running
```bash
container list | grep ninaivalaigal-dev-<service-name>
```

### Check container logs
```bash
container logs ninaivalaigal-dev-<service-name>
```

### Test health endpoint
```bash
# Core API (port 13390)
curl http://localhost:13390/health

# Business Service (port 13391)
curl http://localhost:13391/health

# Admin Vendor Service (port 13392)
curl http://localhost:13392/health

# Memory Service (port 13393)
curl http://localhost:13393/health

# Graph Service (port 13394)
curl http://localhost:13394/health

# gRPC Gateway (port 13395)
curl http://localhost:13395/health
```

---

## 🐛 Troubleshooting

### Build fails with "file not found"
- **Check**: Ensure you're in the project root directory
- **Check**: Verify Dockerfile path is correct
- **Check**: Verify build context includes all necessary files

### Container won't start after rebuild
- **Check**: Look at container logs: `container logs ninaivalaigal-dev-<service-name>`
- **Check**: Verify dependencies (database, redis) are running
- **Check**: Verify environment variables are set correctly

### Migration errors
- **Check**: Ensure Alembic migrations are in proper order
- **Check**: Clear Python cache: `find alembic/versions/__pycache__ -name "*.pyc" -delete`
- **Check**: Rebuild container to pick up migration fixes
- **Check**: Verify migration chain: `grep -r "down_revision" alembic/versions/012*.py`

### Service-specific issues

**Core API:**
- Database connection errors: Check PgBouncer is running and DATABASE_URL is correct
- Memory browser API 500: Ensure router is included in `server/main.py`
- JWT errors: Verify `NINAIVALAIGAL_JWT_SECRET` is set

**Memory Service (Rust):**
- Build failures: Ensure Rust toolchain is installed: `rustc --version`
- Port conflicts: Check if port 13393 is available

**gRPC Gateway (Go):**
- Build failures: Ensure Go is installed: `go version`
- gRPC connection errors: Verify memory-service is running first

---

## 📚 Full Documentation

For complete details, see:
- **Service Build Guide**: [docs/SERVICE_CONTAINER_BUILD_DEPLOYMENT.md](SERVICE_CONTAINER_BUILD_DEPLOYMENT.md)
- **Apple Container CLI**: [how-to/container-builds/apple/00-OVERVIEW.md](../how-to/container-builds/apple/00-OVERVIEW.md)
- **Build All Services**: Run `./scripts/build-and-deploy-all-services.sh --help`

---

## 🎯 Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│  Build Core API:                                │
│  ./scripts/docker-to-apple-container.sh core-api │
│    --dockerfile services/core-api/Dockerfile     │
│    --context .                                   │
│                                                  │
│  Restart:                                        │
│  ./services/core-api/nv-core-api-start.sh       │
│                                                  │
│  Verify:                                         │
│  curl http://localhost:13390/health  # Core API  │
│                                                  │
│  Other service ports:                            │
│  - business-service: 13391                       │
│  - admin-vendor-service: 13392                   │
│  - memory-service: 13393                        │
│  - graph-service: 13394                         │
│  - grpc-gateway: 13395                          │
└─────────────────────────────────────────────────┘
```

---

**Last Updated**: November 4, 2025
**Script Location**: `scripts/docker-to-apple-container.sh`
