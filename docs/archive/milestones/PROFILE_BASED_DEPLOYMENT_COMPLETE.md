# ✅ Profile-Based External/Internal Separation - COMPLETE & TESTED

**Date**: 2025-10-03
**Status**: ✅ Fully Functional
**Related**: SPEC-083 (Product Surface Split & Naming)

---

## 🎉 What We Accomplished

### 1. **True Single Source of Truth**
- ✅ One `.env.dev` file for ALL runtimes (Docker, Colima, Apple)
- ✅ Passwords and secrets defined once
- ✅ Ports set by Makefile based on your port matrix
- ✅ No duplicate configuration files

### 2. **Profile-Based Architecture**
- ✅ `external` profile: Customer app (public-facing)
- ✅ `internal` profile: Admin console + monitoring (staff-only)
- ✅ Clean separation per SPEC-083
- ✅ API serves both profiles

### 3. **Correct Port Matrix (with PgBouncer!)**
```
Docker Dev:   5432, 6432, 6379, 13370, 8081, 8181
Colima Dev:   5442, 6442, 6389, 13380, 8091, 8191
Apple Dev:    5452, 6452, 6399, 13390, 8101, 8201
```

### 4. **All Services Running & Healthy**
- ✅ Postgres: healthy (port 5432)
- ✅ PgBouncer: running (port 6432)
- ✅ Redis: healthy (port 6379)
- ✅ API: healthy (port 13370)
- ✅ Customer App: running (port 8081)

### 5. **Code Fixes Applied**
- ✅ Redis rate limiter middleware now uses `REDIS_PASSWORD`
- ✅ Proper password authentication for all services
- ✅ Environment variables correctly passed through

---

## 🚀 Usage

### Quick Start Commands

```bash
# Customer app only (most common for development)
make docker-dev-up-external

# Admin console only (for ops work)
make docker-dev-up-internal

# Everything (full stack)
make docker-dev-up
```

### All Available Commands

```bash
# DOCKER
make docker-dev-up              # Both apps
make docker-dev-up-external     # Customer app only
make docker-dev-up-internal     # Admin console only
make docker-dev-down            # Stop all

# COLIMA (different ports to avoid conflicts)
make colima-dev-up
make colima-dev-up-external
make colima-dev-up-internal
make colima-dev-down

# APPLE CONTAINER CLI (different ports)
make apple-dev-up
make apple-dev-up-external
make apple-dev-up-internal
make apple-dev-down
```

---

## 🔍 Verification

### Test the Stack

```bash
# 1. API Health
curl http://localhost:13370/health
# Expected: {"status":"ok"}

# 2. Database
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT 1;"
# Expected: 1 row returned

# 3. Redis
docker exec ninaivalaigal-dev-redis redis-cli -a dev_redis_password ping
# Expected: PONG

# 4. Customer App
curl http://localhost:8081
# Expected: Vite dev server response

# 5. Check all containers
docker ps --filter "name=ninaivalaigal"
```

---

## 📁 File Structure

### Environment Files (Single Source of Truth)
```
.env.dev   ← Development (all runtimes)
.env.test  ← Testing (all runtimes)
.env.prod  ← Production (all runtimes)
```

### Compose Files (Profile-Based)
```
compose.docker.yml  ← Docker runtime
compose.colima.yml  ← Colima runtime
compose.apple.yml   ← Apple Container CLI runtime
```

### Key Files Modified
- `server/security/middleware/redis_rate_limiter.py` - Fixed Redis password auth
- `compose.docker.yml` - Added profiles, PgBouncer, correct ports
- `compose.colima.yml` - Added profiles, correct ports
- `compose.apple.yml` - Added profiles, correct ports, uses `container compose`
- `Makefile` - Updated with profile commands
- `apps/customer/Dockerfile` - Created
- `apps/admin-console/Dockerfile` - Created

### Files Cleaned Up
- ❌ `.env.docker.dev` (removed - was duplicate)
- ❌ `.env.colima.dev` (removed - was duplicate)
- ❌ `.env.apple.dev` (removed - was duplicate)
- ❌ `compose.template.yml` (removed - not needed)
- ❌ `Makefile.compose` (removed - integrated into main Makefile)

---

## 🎯 Architecture Benefits

### 1. **Clean Separation**
- Customer-facing services isolated from internal tools
- Production-ready security model
- Easy to add monitoring, workers, etc. to internal profile

### 2. **Single Source of Truth**
- Change password once in `.env.dev`
- All runtimes use the same credentials
- No configuration drift

### 3. **Port Isolation**
- Run Docker, Colima, and Apple simultaneously
- No port conflicts
- Easy to switch between runtimes

### 4. **Developer Friendly**
```bash
# Simple commands your colleague can use
make docker-dev-up-external    # Just works!
```

---

## 🔧 Technical Details

### Password Management
All passwords are defined in `.env.dev`:
```bash
NINA_DB_PASSWORD=dev_password_change_in_production
NINA_REDIS_PASSWORD=dev_redis_password
NINA_JWT_SECRET=dev_jwt_secret_change_in_production
```

Compose files have safe defaults that match `.env.dev`:
```yaml
POSTGRES_PASSWORD: ${NINA_DB_PASSWORD:-dev_password_change_in_production}
```

### Redis Connection
The rate limiter middleware constructs the Redis URL from environment variables:
```python
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", "6379")
redis_password = os.getenv("REDIS_PASSWORD", "")
redis_db = os.getenv("REDIS_DB", "0")

if redis_password:
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
```

### Profile System
Services are tagged with profiles:
```yaml
api:
  profiles: ["external", "internal"]  # Serves both

customer-app:
  profiles: ["external"]  # Public only

admin-console:
  profiles: ["internal"]  # Staff only
```

---

## 📊 Port Matrix Reference

| Runtime    | Postgres | PgBouncer | Redis | API   | Customer | Admin |
|------------|----------|-----------|-------|-------|----------|-------|
| **Docker** | 5432     | 6432      | 6379  | 13370 | 8081     | 8181  |
| **Colima** | 5442     | 6442      | 6389  | 13380 | 8091     | 8191  |
| **Apple**  | 5452     | 6452      | 6399  | 13390 | 8101     | 8201  |

---

## 🚨 Troubleshooting

### Issue: Password authentication failed
**Solution**: The database was created with an old password. Reset it:
```bash
docker exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev \
  -c "ALTER USER nina WITH PASSWORD 'dev_password_change_in_production';"
docker restart ninaivalaigal-dev-api
```

### Issue: Redis authentication required
**Solution**: Fixed in `redis_rate_limiter.py` - middleware now uses `REDIS_PASSWORD` env var.

### Issue: Port already in use
**Solution**: Use a different runtime (Colima or Apple) or stop the conflicting service.

### Issue: Containers not starting
**Solution**: Clean up and restart:
```bash
docker-compose -f compose.docker.yml down -v
docker volume prune -f
make docker-dev-up-external
```

---

## ✅ Verification Checklist

- [x] All containers running
- [x] API responds to /health
- [x] Database accepts connections
- [x] Redis accepts authenticated connections
- [x] PgBouncer running
- [x] Customer app serves content
- [x] Single .env.dev file used
- [x] Passwords match across all services
- [x] Profile-based separation working
- [x] Port matrix correct

---

## 🎓 For Your Colleague

When your colleague clones the repo, they can start in **3 commands**:

```bash
git clone https://github.com/Arunosaur/ninaivalaigal.git
cd ninaivalaigal
make docker-dev-up-external
```

That's it! They'll have:
- ✅ Customer app on http://localhost:8081
- ✅ API on http://localhost:13370
- ✅ Full database and Redis
- ✅ All configured with single source of truth

---

## 📝 Next Steps

1. ✅ Profile-based separation - COMPLETE
2. ✅ Single source of truth - COMPLETE
3. ✅ All services running - COMPLETE
4. ⏳ Add monitoring services to internal profile (Prometheus, Grafana)
5. ⏳ Production deployment guide
6. ⏳ CI/CD pipeline updates

---

**Questions?** Everything is documented and working. Your colleague can start immediately with `make docker-dev-up-external`!
