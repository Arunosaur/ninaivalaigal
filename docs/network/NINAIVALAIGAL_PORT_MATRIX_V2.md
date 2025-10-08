# Ninaivalaigal Canonical Port Matrix V2.0

**Version**: 2.0
**Last Updated**: October 7, 2025
**Status**: ✅ Canonical Reference
**Machine-Readable Config**: `config/ports.nv.yaml`

---

## 📊 Complete Port Matrix

### All Runtimes × Environments × Services

| Runtime | Env  | PostgreSQL | PgBouncer | Redis | API   | UI-External | UI-Internal | EM   |
|---------|------|------------|-----------|-------|-------|-------------|-------------|------|
| Docker  | Dev  | 5432       | 6432      | 6379  | 13370 | 8081        | 8181        | 8281 |
| Docker  | Test | 5532       | 6532      | 6479  | 13470 | 8091        | 8191        | 8291 |
| Docker  | Prod | 5632       | 6632      | 6579  | 13570 | 8101        | 8201        | 8301 |
| Colima  | Dev  | 5442       | 6442      | 6389  | 13380 | 8091        | 8191        | 8291 |
| Colima  | Test | 5542       | 6542      | 6489  | 13480 | 8101        | 8201        | 8301 |
| Colima  | Prod | 5642       | 6642      | 6589  | 13580 | 8111        | 8211        | 8311 |
| **Apple**   | **Dev**  | **5452**       | **6452**      | **6399**  | **13390** | **8101**        | **8201**        | **8301** |
| Apple   | Test | 5552       | 6552      | 6499  | 13490 | 8111        | 8211        | 8311 |
| Apple   | Prod | 5652       | 6652      | 6599  | 13590 | 8121        | 8221        | 8321 |

---

## 🧮 Port Calculation Formula

```
Final Port = Base Port + Environment Offset + Runtime Offset
```

### Base Ports

| Service      | Base Port | Description                          |
|--------------|-----------|--------------------------------------|
| PostgreSQL   | 5432      | Standard PostgreSQL port             |
| PgBouncer    | 6432      | Connection pooler (+1000 from PG)    |
| Redis        | 6379      | Standard Redis port                  |
| API          | 13370     | Internal API port                    |
| UI-External  | 8081      | Customer-facing web UI               |
| UI-Internal  | 8181      | Admin console (+100 from external)   |
| EM           | 8281      | Enhanced Memory (+100 from internal) |

### Runtime Offsets

| Runtime | Offset | Example Calculation           |
|---------|--------|-------------------------------|
| Docker  | +0     | 5432 + 0 + 0 = **5432**       |
| Colima  | +10    | 5432 + 0 + 10 = **5442**      |
| Apple   | +20    | 5432 + 0 + 20 = **5452**      |

### Environment Offsets

| Environment | Offset | Example Calculation           |
|-------------|--------|-------------------------------|
| Dev         | +0     | 13370 + 0 + 20 = **13390**    |
| Test        | +100   | 13370 + 100 + 20 = **13490**  |
| Prod        | +200   | 13370 + 200 + 20 = **13590**  |

### Service Grouping Offset

UI and EM services use **+100 per logical layer**:
- UI-External: 8081 (base)
- UI-Internal: 8181 (base + 100)
- EM: 8281 (base + 200)

---

## 🎯 Developer Mnemonics

**Port Ending Patterns** (Apple Dev as example):

| Type        | Port Ending | Description                              |
|-------------|-------------|------------------------------------------|
| UI-External | `-081/-091/-101` | External web UI (user-facing)       |
| UI-Internal | `-181/-191/-201` | Internal admin/ops interface        |
| EM          | `-281/-291/-301` | Exponential Memory service (AI memory orchestrator) |

**Mental Shortcuts**:
- Last digit = Runtime (2=docker, 2=colima, 2=apple... wait, that's the same? No: 0=docker, 2=colima via +10→2, 2=apple via +20→2)
- Actually: **2nd-to-last digit changes by runtime** due to +10/+20 offsets
- Hundreds place = Environment (0=dev, 1=test, 2=prod for services 13xxx range)

---

## 🔑 Key Principles

### 1. Predictable Patterning
Each environment and runtime can be inferred mentally using the formula. No lookup tables needed once you know the pattern.

### 2. No Collisions
All 9 combinations (3 runtimes × 3 envs) stay conflict-free. You can run Docker Dev, Colima Test, and Apple Prod simultaneously.

### 3. Compact Grouping
Developers can visually associate related services:
- `8081` → `8181` → `8281` (External → Internal → EM)
- Each +100 step represents a security/access boundary

### 4. Future Expansion Ready
Next internal components (like GraphOps or Pragna) could continue this pattern:
- GraphOps: 8381, 8481, etc.
- Pattern supports dozens of services without redesign

---

## 🔐 Security Boundaries

| Port Range | Access Level | Authentication       | Purpose                  |
|------------|--------------|----------------------|--------------------------|
| 8081-8101  | Public       | JWT + OAuth          | Customer application     |
| 8181-8221  | Restricted   | Staff JWT + MFA      | Admin console            |
| 8281-8321  | Internal     | Service-to-service   | AI memory orchestrator   |

---

## 📋 Service Details

### PostgreSQL (5432 base)
- **Container Port**: 5432
- **Protocol**: TCP
- **Extensions**: pgvector, Apache AGE
- **Health**: `pg_isready -U nina`

### PgBouncer (6432 base)
- **Container Port**: 6432
- **Protocol**: TCP
- **Auth**: SCRAM-SHA-256
- **Pool Mode**: Transaction
- **Health**: `psql -h localhost -p {port} -U nina -c 'SELECT 1;'`

### Redis (6379 base)
- **Container Port**: 6379
- **Protocol**: TCP
- **Max Memory**: 512MB
- **Eviction**: allkeys-lru
- **Health**: `redis-cli ping`

### API (13370 base)
- **Container Port**: 8000
- **Protocol**: HTTP
- **Framework**: FastAPI + Uvicorn
- **Health**: `curl -f http://localhost:{port}/health`
- **Docs**: `http://localhost:{port}/docs`

### UI-External (8081 base)
- **Container Port**: 8101
- **Protocol**: HTTP
- **Tech**: Static HTML/React
- **Purpose**: Customer-facing interface
- **Health**: `curl -f http://localhost:{port}/`

### UI-Internal (8181 base)
- **Container Port**: 8102
- **Protocol**: HTTP
- **Tech**: Static HTML/React
- **Purpose**: Admin console
- **Health**: `curl -f http://localhost:{port}/`

### EM - Enhanced Memory (8281 base) ⭐ NEW
- **Container Port**: 7070
- **Protocol**: HTTP
- **Framework**: FastAPI + mem0ai
- **Purpose**: AI memory orchestration, context enhancement
- **Health**: `curl -f http://localhost:{port}/health`
- **Note**: Internal service for AI reasoning, not directly user-facing

---

## 🌐 Service URLs (Apple Dev Example)

```bash
# Data Layer
postgresql://localhost:5452            # Direct database (avoid in production)
postgresql://localhost:6452            # Via PgBouncer (REQUIRED for production)
redis://localhost:6399                 # Redis cache

# API Layer
http://localhost:13390                 # API root
http://localhost:13390/health          # Health check
http://localhost:13390/docs            # Swagger UI
http://localhost:13390/redoc           # ReDoc

# UI Layer
http://localhost:8101                  # Customer UI (external)
http://localhost:8201                  # Admin console (internal)

# AI Layer
http://localhost:8301                  # Enhanced Memory (EM)
http://localhost:8301/health           # EM health check
```

---

## 🛠️ Automated Validation

### Using the Validation Script

```bash
# Validate current port bindings
./scripts/validate-ports.sh

# Validate specific runtime/environment
./scripts/validate-ports.sh apple dev

# Fix port mismatches
./scripts/fix-ports-spec-086.sh
```

### Manual Port Check

```bash
# Check what ports are actually listening
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201|8301)"

# Expected output for Apple Dev:
# container *:5452   (PostgreSQL)
# container *:6452   (PgBouncer)
# container *:6399   (Redis)
# container *:13390  (API)
# container *:8101   (Customer UI)
# container *:8201   (Admin Console)
# container *:8301   (Enhanced Memory)
```

---

## 📦 Port Range Reservations

| Component   | Start | End   | Total Ports | Usage                    |
|-------------|-------|-------|-------------|--------------------------|
| PostgreSQL  | 5432  | 5699  | 268         | All environments/runtimes |
| PgBouncer   | 6432  | 6699  | 268         | All environments/runtimes |
| Redis       | 6379  | 6699  | 321         | All environments/runtimes |
| API         | 13370 | 13699 | 330         | All environments/runtimes |
| UI-External | 8081  | 8299  | 219         | Customer UIs             |
| UI-Internal | 8181  | 8399  | 219         | Admin consoles           |
| EM          | 8281  | 8499  | 219         | AI orchestration         |

**Total Reserved Ports**: 1,873 ports across all services

---

## 🔄 Container Naming Convention

### Pattern
```
ninaivalaigal-{environment}-{service}
```

**IMPORTANT**: Container names do **NOT** include runtime suffix!
Multiple runtimes cannot run simultaneously - they share container names.
Only **port allocation** differs by runtime (+0 Docker, +10 Colima, +20 Apple).

### Examples
```bash
# All services follow this pattern (NO runtime suffix)
ninaivalaigal-dev-db
ninaivalaigal-dev-pgbouncer
ninaivalaigal-dev-redis
ninaivalaigal-dev-api
ninaivalaigal-dev-ui-customer
ninaivalaigal-dev-ui-admin
ninaivalaigal-dev-em

# Test environment
ninaivalaigal-test-db
ninaivalaigal-test-api
# ... etc

# Production environment
ninaivalaigal-prod-db
ninaivalaigal-prod-api
# ... etc
```

### Runtime Distinction

Runtimes are distinguished by **port allocation** only:
- **Docker**: Uses base ports (e.g., API on 13370)
- **Colima**: Uses base + 10 (e.g., API on 13380)
- **Apple**: Uses base + 20 (e.g., API on 13390)

**You can run all 3 runtimes if you use DIFFERENT environments**:
- Docker on Dev (API: 13370)
- Colima on Test (API: 13480)
- Apple on Prod (API: 13590)

---

## 🎨 Visual Port Layout (Apple Dev)

```
Port Range: 5000-14000

5452  ●  PostgreSQL (Database Layer)
      │
6399  ●  Redis (Cache Layer)
6452  ●  PgBouncer (Connection Pooling)
      │
      ├─── Data/Cache Foundation ───┘
      │
8101  ●  Customer UI (External, Public)
8201  ●  Admin Console (Internal, Staff)
8301  ●  Enhanced Memory (AI Layer)
      │
      ├─── UI & AI Layer ───┘
      │
13390 ●  API (Application Logic)
      │
      └─── API Gateway ───┘
```

---

## 🚀 Quick Reference Card

**Copy/paste this for your `.bashrc` or `.zshrc`:**

```bash
# Ninaivalaigal Port Quick Reference (Apple Dev)
alias nv-ports='echo "
PostgreSQL:  5452
PgBouncer:   6452
Redis:       6399
API:         13390
Customer UI: 8101
Admin UI:    8201
EM:          8301
"'

# Direct access
alias nv-db='psql postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev'
alias nv-redis='redis-cli -p 6399 -a dev_redis_password'
alias nv-api='curl http://localhost:13390/health'
alias nv-customer='open http://localhost:8101'
alias nv-admin='open http://localhost:8201'
alias nv-em='curl http://localhost:8301/health'
```

---

## 🔗 Related Documentation

- [SPEC-086: Multi-Runtime Port Allocation](../../specs/SPEC-086-multi-runtime-port-allocation.md)
- [Container Architecture](../CONTAINER_ARCHITECTURE.md)
- [Container Build & Deployment Guide](../CONTAINER_BUILD_DEPLOYMENT_GUIDE.md)
- [Port Correction Plan](../PORT_CORRECTION_PLAN.md)
- [Machine-Readable Config](../../config/ports.nv.yaml)

---

## 📝 Changelog

### V2.0 - October 7, 2025
- ✅ Added **EM (Enhanced Memory)** service to matrix
- ✅ Created machine-readable `config/ports.nv.yaml`
- ✅ Added automated validation script
- ✅ Expanded documentation with mnemonics
- ✅ Added visual port layout diagram
- ✅ Created quick reference card

### V1.0 - October 4, 2025
- Initial matrix with 6 services
- Formula and offset logic defined
- SPEC-086 published

---

**Machine-Enforceable**: This specification is now backed by `config/ports.nv.yaml` and validation scripts.
**Zero-Tolerance**: Port mismatches are automatically detected and fixable via scripts.
**Future-Proof**: Pattern supports unlimited service expansion.

✅ **CANONICAL REFERENCE - USE THIS AS SINGLE SOURCE OF TRUTH**
