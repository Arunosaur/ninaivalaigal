# Microservices Port Allocation Plan

**Reference:** `config/ports.nv.yaml` (SPEC-086)
**Environment:** Apple Container - Dev
**Updated:** Oct 16, 2025

---

## Port Formula

```
Final Port = Base Port + Runtime Offset + Environment Offset + Service Offset
```

**Base Values:**
- Base API Port: 13370
- Runtime Offset (Apple): +20
- Environment Offset (dev): +0
- **Base for Apple Dev:** 13390

---

## Microservices Port Allocation (Apple Dev)

| Service | Port | Formula | Purpose |
|---------|------|---------|---------|
| **Core API** | **13390** | 13370+20+0+0 | Auth, Users, Teams, Organizations |
| **Business Logic** | **13391** | 13370+20+0+1 | Business operations, workflows |
| **Admin/Vendor** | **13392** | 13370+20+0+2 | Admin console, vendor management |
| **Memory Service** (Rust) | **13393** | 13370+20+0+3 | Memory CRUD operations |
| **Graph Service** (Rust) | **13394** | 13370+20+0+4 | Graph intelligence operations |
| **Gateway** (Rust gRPC) | **13395** | 13370+20+0+5 | API Gateway / Service mesh |

**Port Range Reserved:** 13390-13399 (10 services max)

---

## Container Names Convention

Following existing pattern from `ports.nv.yaml`:

```bash
ninaivalaigal-{env}-{service}
```

| Service | Container Name |
|---------|----------------|
| Core API | ninaivalaigal-dev-core-api |
| Business Logic | ninaivalaigal-dev-business-logic |
| Admin/Vendor | ninaivalaigal-dev-admin-vendor |
| Memory Service | ninaivalaigal-dev-memory-service |
| Graph Service | ninaivalaigal-dev-graph-service |
| Gateway | ninaivalaigal-dev-gateway |

---

## Internal Container Ports

All services use **port 8000** internally (container port).
External ports are mapped according to the allocation table above.

**Port Mapping Pattern:**
```bash
container run -p {EXTERNAL}:8000 ...
```

Example:
```bash
# Core API
-p 13390:8000

# Business Logic
-p 13391:8000

# Admin/Vendor
-p 13392:8000
```

---

## Health Check URLs

| Service | URL |
|---------|-----|
| Core API | http://localhost:13390/health |
| Business Logic | http://localhost:13391/health |
| Admin/Vendor | http://localhost:13392/health |
| Memory Service | http://localhost:13393/health |
| Graph Service | http://localhost:13394/health |
| Gateway | http://localhost:13395/health |

---

## Service Dependencies Matrix

| Service | Depends On | Ports Used |
|---------|-----------|------------|
| Core API | PgBouncer (6452), Redis (6399) | 13390 |
| Business Logic | Core API (13390), PgBouncer, Redis | 13391 |
| Admin/Vendor | Core API (13390), Business Logic (13391) | 13392 |
| Memory Service | PgBouncer (6452) | 13393 |
| Graph Service | PgBouncer (6452), Memory Service (13393) | 13394 |
| Gateway | All above services | 13395 |

---

## Scripts Naming Convention

Following the pattern established with Core API:

```bash
nv-{service}-start.sh
nv-{service}-stop.sh
nv-{service}-status.sh
```

Examples:
- `nv-business-logic-start.sh`
- `nv-admin-vendor-start.sh`
- `nv-memory-service-start.sh`

---

## Update to ports.nv.yaml (Future)

When ready to formalize, add to `config/ports.nv.yaml`:

```yaml
# Microservices sub-allocation (SPEC-100 Stage 3)
microservices:
  apple:
    dev:
      core_api: 13390      # Auth, Users, Teams, Orgs
      business_logic: 13391  # Business operations
      admin_vendor: 13392    # Admin/vendor management
      memory_service: 13393  # Memory CRUD (Rust)
      graph_service: 13394   # Graph intelligence (Rust)
      gateway: 13395        # API Gateway (Rust gRPC)
```

---

## Port Conflict Prevention

**Before starting a new service:**
```bash
# Check if port is available
lsof -ti:13391

# If occupied, kill the process
kill $(lsof -ti:13391)

# Or check what's running
lsof -i:13391
```

---

## Status: Ready for Implementation ✅

- ✅ Core API: Port 13390 (Running)
- 🚧 Business Logic: Port 13391 (Next)
- 🚧 Admin/Vendor: Port 13392 (Planned)
- 🚧 Memory Service: Port 13393 (Developer A)
- 🚧 Graph Service: Port 13394 (Developer A)
- 🚧 Gateway: Port 13395 (Week 2)
