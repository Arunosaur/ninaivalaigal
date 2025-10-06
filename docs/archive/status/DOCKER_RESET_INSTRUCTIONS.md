# Docker Desktop Factory Reset Required

**Date:** October 5, 2025, 2:35 PM
**Issue:** Docker internal storage corrupted (`rw layer snapshot not found`)

## **Root Cause:**
Docker Desktop's overlay filesystem is corrupted. This causes all containers to enter Created → Dead loop regardless of configuration.

## **Factory Reset Steps:**

### **Option 1: Via Docker Desktop UI (RECOMMENDED)**
1. Open Docker Desktop
2. Click Settings (gear icon)
3. Go to "Troubleshoot"
4. Click "Clean / Purge data"
5. Select "Reset to factory defaults"
6. Click "Reset"
7. Wait for restart (~2 minutes)

### **Option 2: Via Command Line**
```bash
# Stop Docker
osascript -e 'quit app "Docker"'
sleep 5

# Remove Docker data (WARNING: deletes all containers/images/volumes)
rm -rf ~/Library/Containers/com.docker.docker/Data

# Restart Docker
open -a Docker

# Wait for Docker to initialize
sleep 30
docker info
```

## **After Reset:**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Verify Docker is healthy
docker system df
docker ps

# Start stack
docker-compose -f compose.docker.yml --env-file .env.dev up -d postgres redis

# Test
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 5432 -U nina -d ninaivalaigal_dev -c "SELECT 1;"
```

## **Data Impact:**
- ❌ All Docker images will be deleted (will need to rebuild/pull)
- ❌ All Docker volumes will be deleted (**THIS INCLUDES YOUR DATABASE DATA**)
- ❌ All Docker containers will be deleted
- ✅ Your code in `/Users/swami/WorkSpace/ninaivalaigal` is safe
- ✅ Your bind-mounted `./data/postgres_dev/` backup is safe (62MB)

## **Alternative: Use Apple Container CLI**
Your memory shows you have working scripts that avoid Docker Desktop entirely:
```bash
./scripts/nv-db-start.sh
./scripts/nv-pgbouncer-start.sh
./scripts/nv-api-start.sh
```

This would avoid Docker Desktop issues completely.
