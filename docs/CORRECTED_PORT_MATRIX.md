# Corrected Port & Isolation Matrix

**Date**: 2025-09-30
**Purpose**: Define the complete 9-combination matrix with proper isolation

---

## 🎯 Key Principle: Complete Isolation

Each of the 9 combinations is **completely isolated**:
- ✅ Separate PostgreSQL **container**
- ✅ Separate PostgreSQL **data volume**
- ✅ Separate Redis **container**
- ✅ Separate Redis **data volume**
- ✅ Unique **ports** (no conflicts)
- ✅ Unique **container names**

**Database names can be the same** (e.g., `ninaivalaigal_dev`) because each runtime has its own isolated PostgreSQL container.

---

## 📊 **Corrected Port Assignment Matrix**

| # | Environment | Runtime | Postgres | Redis | API   | UI   | Container Prefix | DB Name | Volume Prefix |
|---|-------------|---------|----------|-------|-------|------|------------------|---------|---------------|
| 1 | **dev**     | docker  | 5432     | 6379  | 13370 | 8081 | ninaivalaigal-dev | ninaivalaigal_dev | postgres_dev |
| 2 | **dev**     | colima  | 5442     | 6389  | 13380 | 8091 | ninaivalaigal-colima-dev | ninaivalaigal_dev | postgres_colima_dev |
| 3 | **dev**     | apple   | 5452     | 6399  | 13390 | 8101 | ninaivalaigal-apple-dev | ninaivalaigal_dev | postgres_apple_dev |
| 4 | **test**    | docker  | 5532     | 6479  | 13470 | 8181 | ninaivalaigal-test | ninaivalaigal_test | postgres_test |
| 5 | **test**    | colima  | 5542     | 6489  | 13480 | 8191 | ninaivalaigal-colima-test | ninaivalaigal_test | postgres_colima_test |
| 6 | **test**    | apple   | 5552     | 6499  | 13490 | 8201 | ninaivalaigal-apple-test | ninaivalaigal_test | postgres_apple_test |
| 7 | **prod**    | docker  | 5632     | 6579  | 13570 | 8281 | ninaivalaigal-prod | ninaivalaigal_prod | postgres_prod |
| 8 | **prod**    | colima  | 5642     | 6589  | 13580 | 8291 | ninaivalaigal-colima-prod | ninaivalaigal_prod | postgres_colima_prod |
| 9 | **prod**    | apple   | 5652     | 6599  | 13590 | 8301 | ninaivalaigal-apple-prod | ninaivalaigal_prod | postgres_apple_prod |

---

## 🔑 **Key Points**

### **Database Names**
- All use `ninaivalaigal_${ENV}` format
- Same name within environment is OK because containers are isolated
- Example: docker/dev, colima/dev, apple/dev all use `ninaivalaigal_dev`
- But each has its own PostgreSQL container with separate data

### **Container Names**
- Format: `ninaivalaigal-[runtime-]${ENV}-service`
- Docker: `ninaivalaigal-dev-db` (no runtime prefix for default)
- Colima: `ninaivalaigal-colima-dev-db`
- Apple: `ninaivalaigal-apple-dev-db`

### **Volume Names**
- Format: `postgres_[runtime_]${ENV}_data`
- Docker: `postgres_dev_data`
- Colima: `postgres_colima_dev_data`
- Apple: `postgres_apple_dev_data`

### **Data Isolation**
Each runtime/environment combination has:
```
docker/dev:
  - Container: ninaivalaigal-dev-db
  - Volume: postgres_dev_data
  - Database: ninaivalaigal_dev
  - Port: 5432

colima/dev:
  - Container: ninaivalaigal-colima-dev-db
  - Volume: postgres_colima_dev_data
  - Database: ninaivalaigal_dev (same name, different container!)
  - Port: 5442

apple/dev:
  - Container: ninaivalaigal-apple-dev-db
  - Volume: postgres_apple_dev_data
  - Database: ninaivalaigal_dev (same name, different container!)
  - Port: 5452
```

**Result**: All 3 can run simultaneously with no conflicts!

---

## 🎯 **Port Calculation Formula**

```
Final Port = Base Port + Environment Offset + Runtime Offset

Base Ports:
- Postgres: 5432
- Redis: 6379
- API: 13370
- UI: 8081

Environment Offsets:
- dev: +0
- test: +100
- prod: +200

Runtime Offsets:
- docker: +0
- colima: +10
- apple: +20

Example (Apple/Test/Postgres):
5432 + 100 (test) + 20 (apple) = 5552
```

---

## 🚀 **Usage Examples**

### **Start Docker Dev**
```bash
docker-compose -f compose.docker.yml up -d
# Postgres: 5432, Redis: 6379, API: 13370, UI: 8081
```

### **Start Colima Dev (simultaneously)**
```bash
docker-compose -f compose.colima.dev.yml up -d
# Postgres: 5442, Redis: 6389, API: 13380, UI: 8091
```

### **Start Apple Dev (simultaneously)**
```bash
docker-compose -f compose.apple.dev.yml up -d
# Postgres: 5452, Redis: 6399, API: 13390, UI: 8101
```

**All 3 run at the same time with no conflicts!**

---

## 📋 **Validation Checklist**

For each compose file, verify:
- ✅ Correct ports from matrix
- ✅ Unique container names
- ✅ Unique volume names
- ✅ Correct database name (`ninaivalaigal_${ENV}`)
- ✅ Environment variables properly set

---

## 🔧 **What Needs to be Fixed**

### **1. compose.apple.yml**
- ❌ Uses `nina_${ENV}` instead of `ninaivalaigal_${ENV}`
- ❌ Uses custom images that don't exist
- ✅ **Fix**: Update to use standard images and correct DB names

### **2. compose.docker.yml**
- ✅ Correct database name: `ninaivalaigal_${NINA_ENV:-dev}`
- ✅ Uses environment variables for ports
- ⚠️ **Needs**: Explicit volume names for clarity

### **3. compose.colima.yml**
- ✅ Correct database name: `ninaivalaigal_${NINA_ENV:-dev}`
- ✅ Uses environment variables for ports
- ⚠️ **Needs**: Explicit volume names for clarity

---

## ✅ **Corrected Understanding**

**Q: Can two containers point to the same database?**
**A**: No, but they don't! Each runtime has its own PostgreSQL container.

**Q: Why do they have the same database name?**
**A**: The database name (`ninaivalaigal_dev`) is just a logical name inside each container. Each container has its own isolated copy.

**Q: How is data isolated?**
**A**: Through separate Docker volumes:
- docker/dev → `postgres_dev_data` volume
- colima/dev → `postgres_colima_dev_data` volume
- apple/dev → `postgres_apple_dev_data` volume

**Q: Can they run simultaneously?**
**A**: Yes! Different ports + different containers + different volumes = complete isolation.

---

**Status**: Matrix corrected, isolation clarified
**Next Step**: Update compose files to match corrected matrix
