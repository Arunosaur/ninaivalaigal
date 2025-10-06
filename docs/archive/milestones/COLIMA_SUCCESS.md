# ✅ Colima Development Environment - WORKING

**Date:** 2025-10-05
**Status:** ✅ Fully Operational
**Runtime:** Colima (lightweight Docker alternative)

---

## 🎯 What We Achieved

### **1. Fixed Docker Corruption**
- **Problem:** Docker Desktop had persistent internal corruption (`rw layer snapshot not found`)
- **Solution:** Switched to Colima with fresh VM
- **Commands:**
  ```bash
  colima stop
  colima delete --force
  colima start --cpu 4 --memory 8 --disk 60 --arch aarch64 --vm-type vz --mount-type virtiofs
  ```

### **2. Correct Port Configuration**
Following the **Runtime × Environment Full Port Matrix**:

| Service | Port |
|---------|------|
| PostgreSQL | 5442 |
| PgBouncer | 6442 |
| Redis | 6389 |
| API | 13380 |
| Customer App | 8091 |
| Admin Console | 8191 |

### **3. Working Services**
```bash
docker ps
```
Output:
- ✅ `ninaivalaigal-dev-db` - PostgreSQL 15.14 on `0.0.0.0:5442`
- ✅ `ninaivalaigal-dev-redis` - Redis 7 on `0.0.0.0:6389`

### **4. Database Connection**
```bash
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 5442 -U nina -d ninaivalaigal_dev
```
**Status:** ✅ Connected successfully

---

## 📁 File Structure

### **Configuration Files**
1. **`.env.colima.dev`** - Colima-specific environment variables with correct ports
2. **`compose.colima.yml`** - Colima Docker Compose configuration
3. **`scripts/colima-dev-up.sh`** - Smart startup script (Apple Container CLI pattern)
4. **`scripts/colima-dev-down.sh`** - Clean shutdown script

### **Data Storage**
- **Type:** Docker named volumes (no bind mounts to avoid corruption)
- **PostgreSQL:** `ninaivalaigal_dev_postgres_data_colima`
- **Redis:** `ninaivalaigal_dev_redis_data_colima`

---

## 🚀 Usage

### **Start Stack**
```bash
make colima-dev-up
```
or
```bash
docker compose -f compose.colima.yml --env-file .env.colima.dev up -d
```

### **Stop Stack**
```bash
make colima-dev-down
```
or
```bash
docker compose -f compose.colima.yml --env-file .env.colima.dev down
```

### **View Logs**
```bash
docker compose -f compose.colima.yml logs -f postgres redis
```

### **Check Status**
```bash
docker ps --filter "name=ninaivalaigal-dev"
```

---

## 📊 Database Connection Strings

### **Direct PostgreSQL**
```
postgresql://nina:dev_password_change_in_production@localhost:5442/ninaivalaigal_dev
```

### **Redis**
```
redis://:dev_redis_password@localhost:6389/0
```

---

## ✅ Next Steps

### **1. Run Migrations**
```bash
cd server
alembic upgrade head
```

### **2. Seed Admin User**
```bash
python -m scripts.seed_admin
```

### **3. Add PgBouncer**
- Port: 6442
- Update `compose.colima.yml` with PgBouncer service
- Configure connection pooling

### **4. Start API Server**
- Port: 13380
- Update environment to use PgBouncer
- Test `/health` and `/docs` endpoints

### **5. Test UI Applications**
- Customer App: http://localhost:8091
- Admin Console: http://localhost:8191

---

## 🔧 Configuration Details

### **Colima VM Settings**
- **CPUs:** 4
- **Memory:** 8 GB
- **Disk:** 60 GB
- **Architecture:** aarch64 (ARM64)
- **VM Type:** vz (Apple Virtualization Framework)
- **Mount Type:** virtiofs (faster file sharing)

### **Image Configuration**
```yaml
postgres:
  image: ghcr.io/arunosaur/ninaivalaigal-db:latest
  build:
    context: ./containers/consolidated-db
  platform: linux/arm64
```

---

## 🐛 Troubleshooting

### **If Containers Won't Start**
```bash
# Reset Colima completely
colima stop
colima delete --force
colima start --cpu 4 --memory 8 --disk 60 --arch aarch64 --vm-type vz

# Remove all volumes
docker volume prune -f

# Restart stack
make colima-dev-up
```

### **If Ports Are Wrong**
```bash
# Verify env file
cat .env.colima.dev | grep PORT

# Verify compose config
docker compose -f compose.colima.yml --env-file .env.colima.dev config | grep published

# Should show:
# published: "5442" (PostgreSQL)
# published: "6389" (Redis)
```

### **If Database Connection Fails**
```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check logs
docker logs ninaivalaigal-dev-db

# Test connection
psql -h localhost -p 5442 -U nina -d ninaivalaigal_dev
```

---

## 📝 Important Notes

1. **Data Persistence:** Data is stored in Docker named volumes, persists across restarts
2. **Fresh Database:** Current database is empty, needs migrations
3. **Cross-Platform:** Configuration supports both ARM64 and x86_64
4. **All Runtimes:** Same approach will work for Docker and Apple Container CLI with port adjustments

---

## 🎓 Lessons Learned

### **What Caused the Issues**
1. Docker Desktop internal corruption from file lock contention
2. GitHub Actions self-hosted runner interfering with local Docker
3. Bind mounts on macOS causing metadata corruption

### **What Fixed It**
1. Complete Docker reset (Colima fresh start)
2. Docker named volumes instead of bind mounts
3. Proper environment variable configuration with `.env.colima.dev`

### **Best Practices**
1. Use Colima for local development (lighter than Docker Desktop)
2. Use named volumes for data (avoid bind mounts for database data)
3. Separate env files per runtime (`.env.colima.dev`, `.env.docker.dev`, etc.)
4. Test with `docker compose config` before `up` to verify port bindings

---

**Status:** Ready for migrations and application development! 🚀
