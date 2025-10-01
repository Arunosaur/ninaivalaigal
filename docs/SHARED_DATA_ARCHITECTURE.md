# Shared Data Architecture - Corrected

**Date**: 2025-09-30
**Requirement**: Data shared across runtimes within same environment

---

## 🎯 **Core Requirement**

**Within each environment, all runtimes share the same data:**

```
Dev Environment:
  docker/dev  ─┐
  colima/dev  ├─→ Same PostgreSQL data volume
  apple/dev   ─┘   Same Redis data volume
                   Same database content

Test Environment:
  docker/test  ─┐
  colima/test  ├─→ Same PostgreSQL data volume
  apple/test   ─┘   Same Redis data volume
                    Same database content

Prod Environment:
  docker/prod  ─┐
  colima/prod  ├─→ Same PostgreSQL data volume
  apple/prod   ─┘   Same Redis data volume
                    Same database content
```

**Why?** A developer can switch between Docker, Colima, or Apple CLI and see the same data!

---

## 📊 **Corrected Port & Volume Matrix**

| # | Environment | Runtime | Postgres | Redis | API   | UI   | DB Name | Shared Volume |
|---|-------------|---------|----------|-------|-------|------|---------|---------------|
| 1 | **dev**     | docker  | 5432     | 6379  | 13370 | 8081 | ninaivalaigal_dev | **postgres_dev_data** |
| 2 | **dev**     | colima  | 5442     | 6389  | 13380 | 8091 | ninaivalaigal_dev | **postgres_dev_data** ← Same! |
| 3 | **dev**     | apple   | 5452     | 6399  | 13390 | 8101 | ninaivalaigal_dev | **postgres_dev_data** ← Same! |
| 4 | **test**    | docker  | 5532     | 6479  | 13470 | 8181 | ninaivalaigal_test | **postgres_test_data** |
| 5 | **test**    | colima  | 5542     | 6489  | 13480 | 8191 | ninaivalaigal_test | **postgres_test_data** ← Same! |
| 6 | **test**    | apple   | 5552     | 6499  | 13490 | 8201 | ninaivalaigal_test | **postgres_test_data** ← Same! |
| 7 | **prod**    | docker  | 5632     | 6579  | 13570 | 8281 | ninaivalaigal_prod | **postgres_prod_data** |
| 8 | **prod**    | colima  | 5642     | 6589  | 13580 | 8291 | ninaivalaigal_prod | **postgres_prod_data** ← Same! |
| 9 | **prod**    | apple   | 5652     | 6599  | 13590 | 8301 | ninaivalaigal_prod | **postgres_prod_data** ← Same! |

---

## 🔑 **Key Architecture Points**

### **Shared Per Environment**
- ✅ **Database name**: `ninaivalaigal_${ENV}` (same within environment)
- ✅ **PostgreSQL volume**: `postgres_${ENV}_data` (shared across runtimes)
- ✅ **Redis volume**: `redis_${ENV}_data` (shared across runtimes)
- ✅ **Data content**: Identical across all runtimes in same environment

### **Unique Per Runtime**
- ✅ **Ports**: Different for each runtime (no conflicts)
- ✅ **Container names**: Different for each runtime
- ✅ **Networks**: Can be shared or separate (doesn't matter)

### **Volume Naming Convention**
```
postgres_${ENV}_data  # Shared by all runtimes in environment
redis_${ENV}_data     # Shared by all runtimes in environment

Examples:
- postgres_dev_data   # Used by docker/dev, colima/dev, apple/dev
- postgres_test_data  # Used by docker/test, colima/test, apple/test
- postgres_prod_data  # Used by docker/prod, colima/prod, apple/prod
```

---

## ⚠️ **Important Constraint**

**Only ONE runtime can run per environment at a time!**

Why? Because they share the same PostgreSQL data volume, and PostgreSQL locks the data directory.

```bash
# This works:
docker-compose -f compose.docker.yml up -d  # dev environment

# This will FAIL (data directory locked):
docker-compose -f compose.colima.dev.yml up -d  # also dev environment

# But this works (different environment):
NINA_ENV=test docker-compose -f compose.docker.yml up -d  # test environment
```

**Solution**: Stop one runtime before starting another in the same environment.

---

## 🚀 **Developer Workflow**

### **Switch from Docker to Apple CLI (same data)**

```bash
# Currently using Docker
docker-compose -f compose.docker.yml down

# Switch to Apple CLI (sees same data!)
docker-compose -f compose.apple.dev.yml up -d

# Database content is identical
# Redis cache is identical
# User can continue where they left off
```

### **Run Multiple Environments Simultaneously**

```bash
# Dev with Docker
docker-compose -f compose.docker.yml up -d

# Test with Colima (different data)
NINA_ENV=test docker-compose -f compose.colima.yml up -d

# Prod with Apple CLI (different data)
NINA_ENV=prod docker-compose -f compose.apple.yml up -d

# All 3 run simultaneously - different environments, different data
```

---

## 📋 **Required Compose File Structure**

### **All compose files must use environment-based volumes:**

```yaml
volumes:
  postgres_data:
    name: postgres_${NINA_ENV:-dev}_data
    driver: local
  redis_data:
    name: redis_${NINA_ENV:-dev}_data
    driver: local
```

### **PostgreSQL service must reference shared volume:**

```yaml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Maps to postgres_${ENV}_data
```

---

## ✅ **What Needs to be Fixed**

### **1. compose.docker.yml**
```yaml
# Current (WRONG):
volumes:
  postgres_data:
    driver: local

# Fixed (CORRECT):
volumes:
  postgres_data:
    name: postgres_${NINA_ENV:-dev}_data
    driver: local
  redis_data:
    name: redis_${NINA_ENV:-dev}_data
    driver: local
```

### **2. compose.colima.yml**
Same fix as docker.yml

### **3. compose.apple.dev.yml**
```yaml
# Current (WRONG):
volumes:
  postgres_apple_dev_data:
    driver: local

# Fixed (CORRECT):
volumes:
  postgres_data:
    name: postgres_dev_data  # Shared with docker/dev and colima/dev
    driver: local
  redis_data:
    name: redis_dev_data
    driver: local
```

---

## 🎯 **Benefits of This Architecture**

### **For Developers**
- ✅ Switch runtimes without losing data
- ✅ Test Docker vs Colima vs Apple CLI with same dataset
- ✅ No data migration needed when switching
- ✅ Consistent development experience

### **For Testing**
- ✅ Test environment isolated from dev
- ✅ Prod environment isolated from test
- ✅ Can run all 3 environments simultaneously
- ✅ Each environment has its own data

### **For Performance**
- ✅ Compare runtime performance with identical data
- ✅ Benchmark Docker vs Colima vs Apple CLI fairly
- ✅ No data differences affecting results

---

## 📊 **Volume Usage Matrix**

| Volume Name | Used By | Purpose |
|-------------|---------|---------|
| `postgres_dev_data` | docker/dev, colima/dev, apple/dev | Shared dev database |
| `redis_dev_data` | docker/dev, colima/dev, apple/dev | Shared dev cache |
| `postgres_test_data` | docker/test, colima/test, apple/test | Shared test database |
| `redis_test_data` | docker/test, colima/test, apple/test | Shared test cache |
| `postgres_prod_data` | docker/prod, colima/prod, apple/prod | Shared prod database |
| `redis_prod_data` | docker/prod, colima/prod, apple/prod | Shared prod cache |

---

## 🔧 **Implementation Steps**

1. ✅ Update all compose files to use named volumes with `${NINA_ENV}`
2. ✅ Ensure volume names follow pattern: `postgres_${ENV}_data`
3. ✅ Test switching between runtimes in same environment
4. ✅ Verify data persists across runtime switches
5. ✅ Document the constraint (only one runtime per environment)

---

## ⚡ **Quick Reference**

### **Shared Within Environment**
- Database name
- PostgreSQL data volume
- Redis data volume
- All data content

### **Unique Per Runtime**
- Ports
- Container names
- Can run different environments simultaneously

### **Constraint**
- Only one runtime per environment at a time
- Must stop docker/dev before starting colima/dev
- Different environments can run simultaneously

---

**Status**: Architecture clarified, ready to implement
**Next Step**: Update compose files to use shared volumes per environment
