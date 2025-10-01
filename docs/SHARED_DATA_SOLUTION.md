# Shared Data Solution - Bind Mounts

**Date**: 2025-09-30
**Solution**: Use bind mounts to share data across ALL runtimes

---

## 🎯 **The Solution: Bind Mounts**

Instead of named volumes, use **bind mounts** to a shared host directory!

### **How It Works**

```yaml
# All runtimes point to the same host directory
services:
  postgres:
    volumes:
      - ./data/postgres_dev:/var/lib/postgresql/data  # Host directory!
```

**Result**: Docker, Colima, AND Apple Container CLI all read/write the **same files** on the host!

---

## 📊 **Architecture**

### **Shared Host Directories**

```
/Users/swami/WorkSpace/ninaivalaigal/
├── data/
│   ├── postgres_dev/      ← All dev runtimes use this
│   ├── postgres_test/     ← All test runtimes use this
│   ├── postgres_prod/     ← All prod runtimes use this
│   ├── redis_dev/         ← All dev runtimes use this
│   ├── redis_test/        ← All test runtimes use this
│   └── redis_prod/        ← All prod runtimes use this
```

### **All Runtimes Point to Same Directories**

```yaml
# Docker
volumes:
  - ./data/postgres_dev:/var/lib/postgresql/data

# Colima
volumes:
  - ./data/postgres_dev:/var/lib/postgresql/data

# Apple Container CLI
volumes:
  - ./data/postgres_dev:/var/lib/postgresql/data
```

**Same directory = Same data!** ✅

---

## 🔑 **Benefits**

### **1. True Data Sharing**
- ✅ Docker sees the data
- ✅ Colima sees the data
- ✅ Apple Container CLI sees the data
- ✅ Switch between ANY runtime = same data!

### **2. Easy Backup**
```bash
# Backup is just copying a directory
tar -czf backup.tar.gz data/
```

### **3. Easy Inspection**
```bash
# You can see the data directly on your Mac
ls -la data/postgres_dev/
```

### **4. No Volume Management**
- No `docker volume create`
- No `docker volume rm`
- Just regular directories

---

## 📋 **Implementation**

### **Step 1: Create Data Directories**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Create data directories
mkdir -p data/postgres_dev
mkdir -p data/postgres_test
mkdir -p data/postgres_prod
mkdir -p data/redis_dev
mkdir -p data/redis_test
mkdir -p data/redis_prod

# Set permissions
chmod 700 data/postgres_*
chmod 700 data/redis_*
```

### **Step 2: Update Compose Files**

```yaml
# compose.docker.yml
services:
  postgres:
    volumes:
      - ./data/postgres_${NINA_ENV:-dev}:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    volumes:
      - ./data/redis_${NINA_ENV:-dev}:/data

# No volumes section needed!
```

### **Step 3: Update .gitignore**

```bash
# Add to .gitignore
data/postgres_*/
data/redis_*/
```

---

## ✅ **Updated Compose Files**

### **compose.docker.yml**
```yaml
services:
  postgres:
    image: postgres:15
    container_name: ninaivalaigal-${NINA_ENV:-dev}-db
    environment:
      POSTGRES_DB: ninaivalaigal_${NINA_ENV:-dev}
      POSTGRES_USER: nina
      POSTGRES_PASSWORD: ${NINA_DB_PASSWORD:-secure_nina_password}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - ./data/postgres_${NINA_ENV:-dev}:/var/lib/postgresql/data  # Bind mount!
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ninaivalaigal-${NINA_ENV:-dev}-redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    command: redis-server --requirepass ${NINA_REDIS_PASSWORD:-secure_nina_password}
    volumes:
      - ./data/redis_${NINA_ENV:-dev}:/data  # Bind mount!
    restart: unless-stopped

# No volumes section needed!
```

### **compose.colima.yml**
Same as docker.yml - uses same bind mounts!

### **compose.apple.dev.yml**
Same as docker.yml - uses same bind mounts!

---

## 🎯 **How It Works**

### **Scenario: Switch from Docker to Apple CLI**

```bash
# 1. Using Docker
docker-compose -f compose.docker.yml up -d
# Data written to: ./data/postgres_dev/

# 2. Stop Docker
docker-compose -f compose.docker.yml down

# 3. Switch to Apple CLI
docker-compose -f compose.apple.dev.yml up -d
# Reads from: ./data/postgres_dev/ (same directory!)

# Result: Apple CLI sees all Docker's data! ✅
```

---

## 📊 **Complete Matrix with Bind Mounts**

| # | Runtime | Environment | Host Directory | Shared? |
|---|---------|-------------|----------------|---------|
| 1 | Docker | dev | `./data/postgres_dev` | ✅ All dev |
| 2 | Colima | dev | `./data/postgres_dev` | ✅ All dev |
| 3 | Apple CLI | dev | `./data/postgres_dev` | ✅ All dev |
| 4 | Docker | test | `./data/postgres_test` | ✅ All test |
| 5 | Colima | test | `./data/postgres_test` | ✅ All test |
| 6 | Apple CLI | test | `./data/postgres_test` | ✅ All test |
| 7 | Docker | prod | `./data/postgres_prod` | ✅ All prod |
| 8 | Colima | prod | `./data/postgres_prod` | ✅ All prod |
| 9 | Apple CLI | prod | `./data/postgres_prod` | ✅ All prod |

**ALL 9 combinations share data within their environment!** ✅

---

## ⚠️ **Important Notes**

### **1. Only One Runtime at a Time**
PostgreSQL locks the data directory, so only one container can access it:
```bash
# This works:
docker-compose -f compose.docker.yml up -d

# This will fail (data directory locked):
docker-compose -f compose.colima.yml up -d  # Same environment!
```

### **2. Permissions**
PostgreSQL requires specific permissions:
```bash
# PostgreSQL user (UID 999) needs ownership
sudo chown -R 999:999 data/postgres_dev/
```

### **3. Backup Strategy**
```bash
# Simple backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf backup-20250930.tar.gz
```

---

## 🚀 **Migration Steps**

### **From Named Volumes to Bind Mounts**

```bash
# 1. Stop all containers
docker-compose -f compose.docker.yml down

# 2. Create data directories
mkdir -p data/postgres_dev data/redis_dev

# 3. Copy existing data (if any)
docker run --rm -v ninaivalaigal_postgres_dev_data:/from -v $(pwd)/data/postgres_dev:/to alpine sh -c "cp -av /from/. /to/"

# 4. Update compose files (use bind mounts)

# 5. Start with bind mounts
docker-compose -f compose.docker.yml up -d

# 6. Verify data is there
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# 7. Remove old volumes (optional)
docker volume rm ninaivalaigal_postgres_dev_data
```

---

## ✅ **Advantages of Bind Mounts**

| Feature | Named Volumes | Bind Mounts |
|---------|---------------|-------------|
| **Cross-runtime sharing** | ❌ No | ✅ Yes |
| **Easy backup** | ❌ Complex | ✅ Simple |
| **Direct access** | ❌ No | ✅ Yes |
| **Git-friendly** | ❌ No | ✅ Yes (.gitignore) |
| **Performance** | ✅ Good | ✅ Good |
| **Portability** | ✅ Good | ✅ Good |

---

## 🎯 **Final Architecture**

```
Your Mac Filesystem
├── ninaivalaigal/
│   ├── data/                    ← Shared by ALL runtimes
│   │   ├── postgres_dev/        ← Docker, Colima, Apple CLI
│   │   ├── postgres_test/       ← Docker, Colima, Apple CLI
│   │   ├── postgres_prod/       ← Docker, Colima, Apple CLI
│   │   ├── redis_dev/           ← Docker, Colima, Apple CLI
│   │   ├── redis_test/          ← Docker, Colima, Apple CLI
│   │   └── redis_prod/          ← Docker, Colima, Apple CLI
│   ├── compose.docker.yml       ← Points to ./data/
│   ├── compose.colima.yml       ← Points to ./data/
│   └── compose.apple.dev.yml    ← Points to ./data/
```

**Result**: True data sharing across ALL runtimes! ✅

---

**Status**: Solution identified - bind mounts
**Next Step**: Implement bind mounts in all compose files
