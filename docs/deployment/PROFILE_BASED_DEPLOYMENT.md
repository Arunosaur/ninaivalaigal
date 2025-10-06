# Profile-Based Deployment - External/Internal Separation

**Status**: Implemented
**Date**: 2025-10-02
**Related**: SPEC-083 (Product Surface Split & Naming)

---

## Overview

Ninaivalaigal uses **Docker Compose profiles** to separate external (customer-facing) and internal (staff-only) services. This enables:

- ✅ **Clean separation** between public and internal apps
- ✅ **Selective deployment** - run only what you need
- ✅ **Production-ready** - same isolation model in dev and prod
- ✅ **Future-proof** - easy to add monitoring, workers, etc.

---

## Architecture

### **Two Profiles**

1. **`external`** - Customer-facing services
   - Customer App (public UI)
   - API (public endpoints)

2. **`internal`** - Staff-only services
   - Admin Console (ops/support UI)
   - API (internal endpoints)
   - Future: Prometheus, Grafana, workers, etc.

### **Shared Infrastructure**

These services run for BOTH profiles:
- PostgreSQL (database)
- Redis (cache)
- API (serves both external and internal)

---

## Usage

### **Quick Start**

```bash
# Customer app only (most common for development)
make docker-dev-up-external

# Admin console only (for ops work)
make docker-dev-up-internal

# Everything (full stack)
make docker-dev-up-all
```

### **All Runtimes**

```bash
# DOCKER
make docker-dev-up-external    # Ports: 8000, 3000, 3001
make docker-dev-up-internal
make docker-dev-up-all

# COLIMA
make colima-dev-up-external    # Ports: 8010, 3010, 3011
make colima-dev-up-internal
make colima-dev-up-all

# APPLE CONTAINER CLI
make apple-dev-up-external     # Ports: 8020, 3020, 3021
make apple-dev-up-internal
make apple-dev-up-all
```

### **Direct Compose Commands**

```bash
# If you prefer not using Make
docker-compose -f compose.docker.yml --profile external up -d
docker-compose -f compose.docker.yml --profile internal up -d
docker-compose -f compose.docker.yml --profile external --profile internal up -d
```

---

## Port Matrix

| Runtime | API | Customer App | Admin Console |
|---------|-----|--------------|---------------|
| **Docker** | 8000 | 3000 | 3001 |
| **Colima** | 8010 | 3010 | 3011 |
| **Apple CLI** | 8020 | 3020 | 3021 |

**Database & Redis** (shared per environment):
- Docker: 5432, 6379
- Colima: 5442, 6389
- Apple: 5452, 6399

---

## Container Names

All containers use the same names across runtimes:
```
ninaivalaigal-dev-db              # Shared database
ninaivalaigal-dev-redis           # Shared cache
ninaivalaigal-dev-api             # API server
ninaivalaigal-dev-customer-app    # Customer app
ninaivalaigal-dev-admin-console   # Admin console
```

**Why?** Port separation allows parallel execution, not container names.

---

## Data Sharing

### **Shared Per Environment**

All runtimes for a given environment share the same data:

```bash
./data/postgres_dev  # Shared by docker/colima/apple
./data/redis_dev     # Shared by docker/colima/apple
```

**Benefit**: Switch runtimes without losing data!

```bash
# Start with Docker
make docker-dev-up-external
# Create some data...

# Switch to Apple CLI (sees same data!)
make docker-dev-down
make apple-dev-up-external
```

---

## Adding Internal Services

Future internal services (monitoring, workers, etc.) go under the `internal` profile:

```yaml
# In compose.docker.yml

  prometheus:
    image: prom/prometheus:latest
    profiles: ["internal"]  # Staff-only
    ports:
      - "9090:9090"
    # ... config ...

  grafana:
    image: grafana/grafana:latest
    profiles: ["internal"]  # Staff-only
    ports:
      - "3002:3000"
    # ... config ...

  worker:
    build: .
    profiles: ["internal"]  # Staff-only
    command: ["celery", "worker"]
    # ... config ...
```

Then they'll automatically be included when running:
```bash
make docker-dev-up-internal  # Includes prometheus, grafana, worker
```

---

## Benefits Over Alternative Approaches

### **❌ Option 1: Separate Compose Files**
- Duplication (maintain 2 files per runtime = 6 files)
- Risk of "hidden coupling" between files
- Harder to onboard colleagues

### **✅ Option 2: Profiles (Current)**
- Single source of truth (1 file per runtime = 3 files)
- Clean separation via profiles
- Production-ready isolation model
- Simple commands: `make docker-dev-up-external`

---

## Production Deployment

In production, you'll likely want:

```bash
# Public-facing servers (exposed via ingress)
docker-compose -f compose.docker.yml --profile external up -d

# Internal servers (Tailnet/VPN only)
docker-compose -f compose.docker.yml --profile internal up -d
```

Or use separate hosts:
- `app.ninaivalaigal.com` → external profile
- `admin.ninaivalaigal.com` → internal profile (Tailnet/SSO)

---

## Troubleshooting

### **Profile Not Starting**

```bash
# Check if profile is specified
docker-compose -f compose.docker.yml config --profiles

# Verify service has correct profile
docker-compose -f compose.docker.yml config | grep -A 5 "customer-app"
```

### **Port Conflicts**

```bash
# Use different runtime
make colima-dev-up-external  # Different ports

# Or check what's using the port
lsof -i :3000
```

### **Data Not Shared**

```bash
# Verify bind mounts
docker volume inspect ninaivalaigal_dev_postgres_data

# Check data directory
ls -la ./data/postgres_dev
```

---

## Files Modified

- `compose.docker.yml` - Docker runtime with profiles
- `compose.colima.yml` - Colima runtime with profiles
- `compose.apple.yml` - Apple CLI runtime with profiles
- `Makefile.compose` - Simple make targets
- `COLLEAGUE_QUICK_START.md` - Updated onboarding

---

## Next Steps

1. ✅ Profile-based separation implemented
2. ⏳ Test one combination end-to-end
3. ⏳ Add Dockerfiles for customer-app and admin-console
4. ⏳ Add monitoring services (Prometheus, Grafana)
5. ⏳ Production deployment guide

---

**Questions?** See `COLLEAGUE_QUICK_START.md` or ask the team!
