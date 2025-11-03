# Developer A - Quick Reference Card

**Your Services:** Memory Service (Rust) + Graph Service (Rust)

---

## 🎯 Your Assignments

| Service | Port | Container Name |
|---------|------|----------------|
| Memory Service | **13393** | ninaivalaigal-dev-memory-service |
| Graph Service | **13394** | ninaivalaigal-dev-graph-service |

---

## 🚀 Quick Start Commands

### Start Your Service
```bash
cd rust-services/memory-service
./nv-memory-service-start.sh
```

### Check Status
```bash
curl http://localhost:13393/health
container list | grep memory
```

### View Logs
```bash
container logs -n 50 ninaivalaigal-dev-memory-service
```

### Stop Service
```bash
container stop ninaivalaigal-dev-memory-service
```

---

## 📋 Naming Rules

**Container:** `ninaivalaigal-dev-{service}`
**Database:** `ninaivalaigal_dev` (shared, don't create new!)
**Port:** Internal `8000` → External `13393` or `13394`
**Scripts:** `nv-{service}-start.sh`, `nv-{service}-stop.sh`

---

## 🔄 Build Workflow

```bash
# 1. Build with Docker
docker build --no-cache -t nina-memory-service:arm64 .

# 2. Save as tar
docker save -o /tmp/memory.tar nina-memory-service:arm64

# 3. Load into Apple Container
container image load -i /tmp/memory.tar

# 4. Run
container run -d --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 nina-memory-service:arm64
```

---

## 🗄️ Database Connection

```bash
# Get PgBouncer IP (dynamic!)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Connect via PgBouncer
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

**Remember:** Port **6432** (PgBouncer), not 5432!

---

## 🔐 JWT Integration

```bash
# Get token from Core API
TOKEN=$(curl -s -X POST http://localhost:13390/auth/signup \
  -d '{"email":"test@rust.com","password":"test123","name":"Test"}' \
  | jq -r '.jwt_token')

# Use token with your service
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:13393/memory/remember
```

**JWT Secret:** From `.env.dev`: `NINAIVALAIGAL_JWT_SECRET`

---

## ❌ Don't Do

```bash
# Wrong: Create separate database
docker exec memory-postgres psql -U postgres -c "CREATE DATABASE ninaivalaigal_dev;"

# Wrong: Container names
docker run --name memory-postgres ...
docker run --name my-service ...

# Wrong: Ports
-p 5433:5432
-p 8080:8000

# Wrong: Commands
docker run ...  # Use: container run
docker ps       # Use: container list
```

## ✅ Do

```bash
# Correct: Use existing database
DATABASE_URL="postgresql://nina:password@host:6432/ninaivalaigal_dev"

# Correct: Container names
container run --name ninaivalaigal-dev-memory-service ...

# Correct: Ports
-p 13393:8000  # Memory
-p 13394:8000  # Graph

# Correct: Commands
container run
container list
```

---

## 📚 Full Guide

See: `services/DEVELOPER_A_CONVENTIONS_GUIDE.md` (1000+ lines)

---

**Port Matrix:** `config/ports.nv.yaml`
**Example Scripts:** `services/core-api/nv-core-api-start.sh`
**Credentials:** `.env.dev`
