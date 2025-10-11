# Container Builds Documentation
**Purpose**: Comprehensive guide for building and managing ninaivalaigal containers across multiple runtimes and architectures

---

## 📁 Directory Structure

```
how-to/container-builds/
├── README.md                    # This file
├── apple/                       # Apple Container CLI builds
│   ├── 00-OVERVIEW.md
│   ├── 01-database.md
│   ├── 02-redis.md
│   ├── 03-pgbouncer.md
│   ├── 04-api.md
│   ├── 05-em.md
│   ├── 06-workers.md
│   ├── 07-ui-admin.md
│   ├── 08-ui-customer.md
│   ├── CONNECTIVITY.md
│   ├── DO-NOT-DOS.md
│   ├── LESSONS-LEARNED.md
│   └── STANDARDS.md
├── docker/                      # Docker builds
│   ├── 00-OVERVIEW.md
│   ├── 01-database.md
│   ├── ... (same structure as apple/)
│   ├── CONNECTIVITY.md
│   ├── DO-NOT-DOS.md
│   ├── LESSONS-LEARNED.md
│   └── STANDARDS.md
└── colima/                      # Colima builds
    ├── 00-OVERVIEW.md
    ├── 01-database.md
    ├── ... (same structure as apple/)
    ├── CONNECTIVITY.md
    ├── DO-NOT-DOS.md
    ├── LESSONS-LEARNED.md
    └── STANDARDS.md
```

---

## 🎯 Supported Architectures

### ARM64 (Apple Silicon)
- **Primary Development**: Mac Studio, MacBook Pro M-series
- **Production**: AWS Graviton, Oracle Ampere
- **Testing**: GitHub Actions (macos-14, macos-15)

### x86_64 (AMD64)
- **Development**: Intel Macs, Linux workstations
- **Production**: Standard cloud VMs (AWS t3, GCP n2, Azure D-series)
- **Testing**: GitHub Actions (ubuntu-latest)

---

## 🏗️ Container Runtimes

### Apple Container CLI
- **Use Case**: Native Mac Silicon development, optimal performance
- **Pros**: Fast, native ARM64, no VM overhead
- **Cons**: macOS only, some DNS/networking quirks
- **Status**: ✅ Production-ready for dev environment

### Docker Desktop
- **Use Case**: Cross-platform builds, CI/CD
- **Pros**: Mature, well-documented, cross-architecture builds
- **Cons**: License costs, VM overhead on macOS
- **Status**: ✅ Production-ready

### Colima
- **Use Case**: Free Docker-compatible runtime for macOS/Linux
- **Pros**: Open source, Docker CLI compatible
- **Cons**: Less mature, some edge case issues
- **Status**: ⚠️ Experimental

---

## 📦 Container Services

### Core Infrastructure
1. **Database** (`ninaivalaigal-dev-db`)
   - PostgreSQL 15
   - Extensions: Apache AGE, pgvector
   - Port: 5452 (dev), 5432 (prod)

2. **Redis** (`ninaivalaigal-dev-redis`)
   - Redis 7
   - Use: Caching, rate limiting, sessions
   - Port: 6389 (dev), 6379 (prod)

3. **PgBouncer** (`ninaivalaigal-dev-pgbouncer`)
   - Connection pooler
   - Port: 6432

### Application Layer
4. **API** (`ninaivalaigal-dev-api`)
   - FastAPI backend
   - Port: 13390 (dev), 8000 (container)

5. **Enhanced Memory** (`ninaivalaigal-dev-em`)
   - Memory management service
   - Port: TBD

6. **Workers** (`ninaivalaigal-dev-workers`)
   - Background job processing
   - No exposed ports

### Frontend
7. **Admin UI** (`ninaivalaigal-dev-ui-admin`)
   - Admin console
   - Port: TBD

8. **Customer UI** (`ninaivalaigal-dev-ui-customer`)
   - Customer-facing interface
   - Port: TBD

---

## 🔄 Multi-Architecture Strategy

### Build Process
1. **Development**: Build natively for host architecture
2. **CI/CD**: Build both arm64 and x86_64
3. **Registry**: Push multi-arch manifests to GHCR
4. **Deployment**: Pull correct architecture automatically

### Image Naming Convention
```
{registry}/{org}/{service}:{tag}[-{arch}]

Examples:
ghcr.io/arunosaur/ninaivalaigal-db:latest          # Multi-arch manifest
ghcr.io/arunosaur/ninaivalaigal-db:latest-arm64    # ARM64 specific
ghcr.io/arunosaur/ninaivalaigal-db:latest-amd64    # x86_64 specific
nina-intelligence-db:arm64                         # Local development
```

---

## 📚 Documentation Guidelines

Each container document should include:

### Build Instructions
- Dockerfile location
- Build command
- Build time estimate
- Dependencies

### Runtime Configuration
- Required environment variables
- Volume mounts
- Port mappings
- Network requirements

### Verification Steps
- Health check commands
- Expected output
- Common issues

### Troubleshooting
- Common errors
- Solutions
- Debug commands

---

## 🚀 Quick Start

### Apple Container CLI (Mac Silicon)
```bash
cd how-to/container-builds/apple
cat 00-OVERVIEW.md
```

### Docker (Cross-platform)
```bash
cd how-to/container-builds/docker
cat 00-OVERVIEW.md
```

### Colima (macOS/Linux)
```bash
cd how-to/container-builds/colima
cat 00-OVERVIEW.md
```

---

## ⚠️ Critical Standards

### Container Naming
**ALWAYS use**: `ninaivalaigal-{env}-{service}`

**Examples**:
- ✅ `ninaivalaigal-dev-db`
- ✅ `ninaivalaigal-prod-api`
- ❌ `nv-db` (legacy, deprecated)
- ❌ `nina-intelligence-db` (inconsistent)

### Build Commands
**ALWAYS use `--no-cache`** after dependency changes:
```bash
container build --no-cache -t {image}:{tag} .
docker build --no-cache -t {image}:{tag} .
```

### Verification
**ALWAYS verify** after build:
```bash
container run --rm {image}:{tag} {health-check-command}
```

---

## 🔗 Related Documentation

- [Port Compliance](../../PORT_COMPLIANCE_FINAL_STATUS.md)
- [Runtime Configuration](../../RUNTIME_CONFIGURATION.md)
- [Legacy Naming Cleanup](../../LEGACY_NAMING_CLEANUP.md)
- [Working State](../../WORKING_STATE.md)

---

## 📅 Last Updated
October 10, 2025

## 👥 Maintainers
- Primary: @Arunosaur
- Documentation: Keep updated with each container change
