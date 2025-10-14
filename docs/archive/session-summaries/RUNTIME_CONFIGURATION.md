# Runtime & Architecture Configuration Guide

**Last Updated:** 2024-10-06
**Current Status:** Apple Container CLI + ARM64 (Mac Silicon)

---

## 🎯 Current Container Status

### Running Containers (as of 2024-10-06 18:20 UTC)

```
NAME                     IMAGE                           ARCH   STATUS
ninaivalaigal-dev-db     nina-intelligence-db:arm64     arm64  RUNNING ✅
ninaivalaigal-dev-redis  redis:7-alpine                 arm64  RUNNING ✅
```

**Container Names Pattern:**
```
ninaivalaigal-{environment}-{component}

Examples:
- ninaivalaigal-dev-db
- ninaivalaigal-dev-pgbouncer
- ninaivalaigal-dev-redis
- ninaivalaigal-dev-api
- ninaivalaigal-dev-customer-app
- ninaivalaigal-dev-admin-console
```

---

## 🔧 How Runtime/Architecture is Determined

### **Runtime Detection (Apple vs Docker vs Colima)**

The scripts use **Apple Container CLI by default** because:

1. **Command Used:** `container` (Apple CLI) not `docker`
2. **Port Offset:** Uses SPEC-086 Apple ports (+20 offset)
3. **No Runtime Flag:** Currently hardcoded to Apple CLI

**SPEC-086 Port Matrix:**
```
Runtime    Offset    DB Port    PgBouncer    Redis    API
Docker     +0        5432       6432         6379     13370
Colima     +10       5442       6442         6389     13380
Apple      +20       5452       6452         6399     13390
```

### **Architecture Detection (ARM64 vs x86_64)**

**Current Setup:** ARM64 (Mac Silicon)

Architecture is specified in:
1. **Image tags:** `nina-intelligence-db:arm64`, `nina-api:arm64`
2. **Dockerfiles:** `FROM --platform=linux/arm64 ...`
3. **Container CLI:** Auto-detects Mac Silicon = ARM64

---

## 📝 Current Configuration

### Environment Variables

```bash
# Check current settings
echo $NINA_ENV           # Should be: dev
echo $NINA_RUNTIME       # Currently NOT SET (defaults to Apple CLI)
echo $NINA_DB_PASSWORD   # Currently NOT SET (using default)
echo $NINA_REDIS_PASSWORD # Currently NOT SET (using default)
```

### Default Values (scripts/stack-start-complete.sh)

```bash
readonly ENV="${NINA_ENV:-dev}"                    # Defaults to 'dev'
readonly DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
readonly REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"
readonly JWT_SECRET="${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}"
```

---

## ⚙️ How to Specify Runtime & Architecture

### Option 1: Environment Variables (Current Method)

```bash
# Set environment
export NINA_ENV=dev          # dev, test, or prod

# Set passwords (RECOMMENDED)
export NINA_DB_PASSWORD=your_secure_password
export NINA_REDIS_PASSWORD=your_redis_password
export NINA_JWT_SECRET=your_jwt_secret

# Start stack
make stack-start
```

### Option 2: Inline Variables

```bash
NINA_ENV=dev NINA_DB_PASSWORD=mypass make stack-start
```

### Option 3: Create .env File

```bash
# Create .env.apple.dev
cat > .env.apple.dev <<EOF
NINA_ENV=dev
NINA_RUNTIME=apple
NINA_DB_PASSWORD=dev_password_change_in_production
NINA_REDIS_PASSWORD=dev_redis_password
NINA_JWT_SECRET=dev_jwt_secret_change_in_production
EOF

# Load and run
source .env.apple.dev
make stack-start
```

---

## 🏗️ Multi-Runtime Architecture (SPEC-086)

### To Run ALL Three Runtimes Simultaneously

**Why?** Parallel development without port conflicts

```bash
# Terminal 1: Docker Runtime
NINA_ENV=dev NINA_RUNTIME=docker docker-compose -f compose.docker.yml up

# Terminal 2: Colima Runtime
NINA_ENV=dev NINA_RUNTIME=colima docker-compose -f compose.colima.yml up

# Terminal 3: Apple CLI Runtime
NINA_ENV=dev make stack-start
```

**Result:** All 3 stacks running on different ports!

| Runtime | DB   | PgBouncer | Redis | API   |
|---------|------|-----------|-------|-------|
| Docker  | 5432 | 6432      | 6379  | 13370 |
| Colima  | 5442 | 6442      | 6389  | 13380 |
| Apple   | 5452 | 6452      | 6399  | 13390 |

---

## 🚨 Current Issues & Status

### ✅ What's Working

1. **Container Names:** Proper SPEC-086 naming
2. **DB + Redis:** Running and stable
3. **ARM64 Images:** Built and operational
4. **Port Allocation:** Apple CLI ports (5452, 6399)

### ⚠️ What's NOT Bulletproof Yet

1. **Password Mismatch:** DB has SCRAM password but scripts use plain password
   - **Evidence:** `FATAL: password authentication failed for user "nina"`
   - **Impact:** Cannot connect to DB from scripts
   - **TODO Day 4:** Consolidate passwords

2. **PgBouncer Not Running:** Should be between API and DB
   - **Status:** Container not started
   - **TODO:** Build/start PgBouncer container

3. **API Not Running:** Depends on PgBouncer
   - **Status:** Image exists but container not started
   - **TODO:** Test API startup

4. **UIs Not Running:** Optional components
   - **Status:** Images may not exist
   - **TODO:** Build if needed

### 🔧 To Fix Password Issue

**Option A: Match Script Password to DB**
```bash
# Find DB password in volume
container exec ninaivalaigal-dev-db \
  psql -U nina -d ninaivalaigal_dev -c \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';"

# Update environment
export NINA_DB_PASSWORD=<actual_password>
```

**Option B: Rebuild DB with Known Password (RECOMMENDED)**
```bash
# Stop and remove
make stack-stop
container delete ninaivalaigal-dev-db

# Set password BEFORE starting
export NINA_DB_PASSWORD=my_known_password

# Start fresh
make stack-start
```

---

## 🎯 Complete Example: Fresh Start

```bash
# 1. Clean slate
make stack-stop
container list --all | grep ninaivalaigal | awk '{print $1}' | xargs -I {} container delete {}

# 2. Set environment
export NINA_ENV=dev
export NINA_RUNTIME=apple
export NINA_DB_PASSWORD=secure_password_123
export NINA_REDIS_PASSWORD=redis_password_456
export NINA_JWT_SECRET=jwt_secret_789

# 3. Build images (if needed)
cd containers/consolidated-db
container build --no-cache -t nina-intelligence-db:arm64 .
cd ../..

container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# 4. Start stack
make stack-start

# 5. Check status
make stack-check
```

---

## 📊 Architecture Specification

### For Docker Runtime (x86_64 or ARM64)

```yaml
# compose.docker.yml
services:
  postgres:
    platform: linux/arm64  # or linux/amd64
    image: postgres:15
    ports:
      - "5432:5432"  # Docker base ports
```

### For Apple Container CLI (ARM64 only)

```bash
# scripts/stack-start-complete.sh
container run -d --name ninaivalaigal-dev-db \
  -p 5452:5432 \  # Apple ports (+20)
  nina-intelligence-db:arm64  # ARM64 image
```

### For Colima Runtime (x86_64 or ARM64)

```yaml
# compose.colima.yml
services:
  postgres:
    platform: linux/arm64  # Mac Silicon
    image: postgres:15
    ports:
      - "5442:5432"  # Colima ports (+10)
```

---

## 🔍 How to Verify Current Setup

```bash
# Check command being used
which container          # Should be: /opt/homebrew/bin/container

# Check architecture
uname -m                 # Should be: arm64

# Check running containers
container list

# Check images
container image list | grep nina

# Check environment
env | grep NINA

# Check ports in use
lsof -i :5452            # Apple DB
lsof -i :6452            # Apple PgBouncer
lsof -i :6399            # Apple Redis
```

---

## 💡 Key Insights

### **Runtime Selection is Manual**

The scripts **DO NOT** auto-detect runtime. They use:
- **Apple Container CLI** (hardcoded `container` command)
- **SPEC-086 Apple ports** (hardcoded 5452, 6452, 6399, etc.)

### **To Switch Runtimes:**

**Option A: Use Different Scripts**
```bash
# Apple CLI
make stack-start

# Docker
docker-compose -f compose.docker.yml up

# Colima
docker-compose -f compose.colima.yml up
```

**Option B: Modify Scripts (Future Enhancement)**
```bash
# TODO: Add runtime detection
if [ "$NINA_RUNTIME" = "docker" ]; then
  DB_PORT=5432
elif [ "$NINA_RUNTIME" = "colima" ]; then
  DB_PORT=5442
else
  DB_PORT=5452  # apple
fi
```

---

## 📋 Summary

### **Current State:**
- ✅ Runtime: **Apple Container CLI** (hardcoded)
- ✅ Architecture: **ARM64** (auto-detected on Mac Silicon)
- ✅ Environment: **dev** (default)
- ✅ Containers: DB + Redis running
- ⚠️ Password: Mismatch causing connection failures
- ❌ PgBouncer: Not running yet
- ❌ API: Not running yet

### **To Specify Runtime/Arch:**
1. **Runtime:** Currently hardcoded to Apple CLI (use different compose files for Docker/Colima)
2. **Architecture:** Specified in image tags (`:arm64` vs `:amd64`)
3. **Environment:** Set `NINA_ENV=dev|test|prod`
4. **Passwords:** Set `NINA_DB_PASSWORD`, `NINA_REDIS_PASSWORD`, `NINA_JWT_SECRET`

### **Is it Bulletproof?**
- **80% there:** Infrastructure and orchestration solid
- **20% remaining:** Password consolidation (Day 4 task)
- **Path forward:** Clear and documented

---

**Next Steps:**
1. Fix password mismatch
2. Start PgBouncer
3. Test API connection through PgBouncer
4. Build/start UIs if needed
5. Full end-to-end validation
