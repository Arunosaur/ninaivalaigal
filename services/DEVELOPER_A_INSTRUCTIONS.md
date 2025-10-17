# Developer A - Instructions Summary

**Date:** Oct 16, 2025  
**Status:** Infrastructure Ready ✅

---

## 🎯 CRITICAL: DO NOT CREATE ANY DATABASES

### What's Already Done For You ✅

```bash
✅ Database Created:      ninaivalaigal_dev
✅ AGE Graph Created:     ninaivalaigal_intelligence_dev
✅ PgBouncer Running:     Connection pooling ready
✅ Redis Running:         Cache ready
✅ Core API Running:      JWT authentication ready (port 13390)
```

### What You Should NOT Do ❌

```bash
❌ DO NOT create database containers
❌ DO NOT create databases
❌ DO NOT create AGE graphs
❌ DO NOT use docker commands (use 'container' instead)
❌ DO NOT use random ports (use 13393, 13394)
```

---

## 📚 Required Documents (Read in This Order)

### 1️⃣ DEVELOPER_A_QUICKSTART.md ⭐ START HERE (15 min)
**Location:** `services/DEVELOPER_A_QUICKSTART.md`

**What it covers:**
- Quick setup guide
- What NOT to do (critical!)
- Testing your setup
- Success criteria

### 2️⃣ DEVELOPER_A_QUICK_REFERENCE.md (5 min)
**Location:** `services/DEVELOPER_A_QUICK_REFERENCE.md`

**What it covers:**
- Port assignments: 13393 (Memory), 13394 (Graph)
- Container names
- Build workflow
- Database connection
- Quick commands

### 3️⃣ DEVELOPER_A_CONVENTIONS_GUIDE.md (20 min)
**Location:** `services/DEVELOPER_A_CONVENTIONS_GUIDE.md`

**What it covers:**
- Detailed naming conventions
- Apple Container CLI usage
- Docker → tar → Container workflow
- Complete working examples
- JWT integration
- Common mistakes (1000+ lines)

### 4️⃣ NAMING_CONVENTIONS.md (10 min)
**Location:** `docs/NAMING_CONVENTIONS.md`

**What it covers:**
- Container: `ninaivalaigal-{env}-{service}`
- Database: `ninaivalaigal_{env}`
- AGE Graph: `ninaivalaigal_intelligence_{env}`
- Complete validation commands

### 5️⃣ OPTION_A_NAMING_SUMMARY.md (5 min)
**Location:** `docs/OPTION_A_NAMING_SUMMARY.md`

**What it covers:**
- Why Option A (Full Suffixes)
- Complete naming matrix
- Migration guide

---

## 🗄️ Database Infrastructure (Ready to Use)

### Connection Information

```bash
# Database (via PgBouncer - REQUIRED!)
DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev

# AGE Graph Name
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev

# JWT Secret (from Core API)
NINAIVALAIGAL_JWT_SECRET=dev_password_change_in_production

# Get PgBouncer IP dynamically (IPs change on container restart!)
PGBOUNCER_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

### What's Available

**PostgreSQL Database:** `ninaivalaigal_dev`
- Schemas: `public`, (you can create: `memory`, `graph`)
- Tables in public: `users`, `teams`, `organizations`
- Extensions: Apache AGE, pgvector

**Apache AGE Graph:** `ninaivalaigal_intelligence_dev`
- Graph namespace: `ninaivalaigal_intelligence_dev`
- Ready for Cypher queries
- Schema: vertex and edge tables auto-created

**Credentials:**
- User: `nina`
- Password: `dev_password_change_in_production`
- Database: `ninaivalaigal_dev`
- PgBouncer Port: `6432` (NOT 5432!)

---

## 🚀 Your Services

### Memory Service (Rust)

**Specifications:**
- Port: **13393** (external) → 8000 (internal)
- Container: `ninaivalaigal-dev-memory-service`
- Purpose: Memory CRUD operations in Rust
- Database: `ninaivalaigal_dev` (shared, via PgBouncer)
- Schema: Create `memory` schema for your tables

**Scripts to Create:**
```bash
rust-services/memory-service/
├── nv-memory-service-start.sh    # Start container
├── nv-memory-service-stop.sh     # Stop container
└── nv-memory-service-status.sh   # Check status
```

**Reference:** Copy from `services/core-api/nv-core-api-start.sh`

---

### Graph Service (Rust)

**Specifications:**
- Port: **13394** (external) → 8000 (internal)
- Container: `ninaivalaigal-dev-graph-service`
- Purpose: Graph intelligence operations in Rust
- Database: `ninaivalaigal_dev` (shared, via PgBouncer)
- AGE Graph: `ninaivalaigal_intelligence_dev` (use existing!)
- Schema: Create `graph` schema for your tables

**Scripts to Create:**
```bash
rust-services/graph-service/
├── nv-graph-service-start.sh     # Start container
├── nv-graph-service-stop.sh      # Stop container
└── nv-graph-service-status.sh    # Check status
```

**Reference:** Copy from `services/core-api/nv-core-api-start.sh`

---

## 🔧 Your Implementation Tasks

### Phase 1: Setup & Connect (Day 1)
1. ✅ Read all 5 required documents
2. ✅ Set up `.env` file with database connection
3. ✅ Test database connectivity via PgBouncer
4. ✅ Verify AGE graph access
5. ✅ Test JWT token from Core API

### Phase 2: Memory Service (Days 2-3)
1. Create Rust service with Axum/Actix-web
2. Connect to `ninaivalaigal_dev` via PgBouncer
3. Create `memory` schema and tables
4. Implement JWT authentication middleware
5. Create CRUD endpoints for memories
6. Create container startup scripts
7. Test with Core API JWT tokens

### Phase 3: Graph Service (Days 4-5)
1. Create Rust service with Axum/Actix-web
2. Connect to `ninaivalaigal_intelligence_dev` graph
3. Create `graph` schema and tables (if needed)
4. Implement Cypher query execution via AGE
5. Implement graph intelligence operations
6. Create container startup scripts
7. Test integration with Memory Service

### Phase 4: Integration Testing (Day 6)
1. Test Memory Service → Graph Service communication
2. Test JWT authentication flow
3. Test cross-service queries
4. Performance testing
5. Documentation

---

## 🧪 Verification Commands

### Check Infrastructure Status
```bash
# List all containers
container list | grep ninaivalaigal

# Should see:
# ninaivalaigal-dev-db
# ninaivalaigal-dev-pgbouncer
# ninaivalaigal-dev-redis
# ninaivalaigal-dev-core-api
```

### Test Database Connection
```bash
# Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Connect to database
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev" -c "SELECT current_database();"

# Expected: ninaivalaigal_dev
```

### Verify AGE Graph
```bash
# Check graph exists
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev \
  -c "SELECT * FROM ag_catalog.ag_graph;"

# Expected output:
# graphid |              name              |           namespace
# --------|--------------------------------|--------------------------------
#   17669 | ninaivalaigal_intelligence_dev | ninaivalaigal_intelligence_dev
```

### Test Core API & JWT
```bash
# Health check
curl http://localhost:13390/health

# Get JWT token
TOKEN=$(curl -s -X POST http://localhost:13390/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"devA@test.com","password":"test123","name":"Developer A"}' \
  | jq -r '.jwt_token')

# Verify token received
echo $TOKEN
```

---

## 📊 Port Allocation Summary

| Service | External Port | Internal Port | Container Name |
|---------|--------------|---------------|----------------|
| PostgreSQL | 5452 | 5432 | ninaivalaigal-dev-db |
| PgBouncer | 6452 | 6432 | ninaivalaigal-dev-pgbouncer |
| Redis | 6399 | 6379 | ninaivalaigal-dev-redis |
| Core API | 13390 | 8000 | ninaivalaigal-dev-core-api |
| **Memory Service** | **13393** | **8000** | **ninaivalaigal-dev-memory-service** |
| **Graph Service** | **13394** | **8000** | **ninaivalaigal-dev-graph-service** |

**Reference:** `config/ports.nv.yaml`

---

## ✅ Success Checklist

Before you start coding, verify:

- [ ] Read all 5 required documents
- [ ] Understand you should NOT create databases
- [ ] Understand you should NOT create AGE graphs
- [ ] Know to use PgBouncer (port 6432), not direct PostgreSQL
- [ ] Know your ports: 13393 (Memory), 13394 (Graph)
- [ ] Know your container names: `ninaivalaigal-dev-{service}`
- [ ] Can connect to database: `ninaivalaigal_dev`
- [ ] Can access AGE graph: `ninaivalaigal_intelligence_dev`
- [ ] Can get JWT from Core API
- [ ] Know to use `container` commands, not `docker`

---

## 🆘 If You Get Stuck

### Common Issues & Solutions

**Issue:** "Can't connect to database"
```bash
# Solution: Use PgBouncer, not direct PostgreSQL
# Wrong: postgresql://nina:password@localhost:5432/ninaivalaigal_dev
# Right: postgresql://nina:password@${PGB_IP}:6432/ninaivalaigal_dev
```

**Issue:** "Graph doesn't exist"
```bash
# Solution: Use correct graph name
# Wrong: ninaivalaigal_intelligence
# Right: ninaivalaigal_intelligence_dev
```

**Issue:** "Container won't start"
```bash
# Solution: Check logs
container logs -n 50 ninaivalaigal-dev-memory-service

# Check if port is in use
lsof -i:13393
```

**Issue:** "Can't build image"
```bash
# Solution: Use Docker → tar → Container workflow
docker build -t nina-memory-service:arm64 .
docker save -o /tmp/memory.tar nina-memory-service:arm64
container image load -i /tmp/memory.tar
```

---

## 📞 Reference Points

**Working Example:** `services/core-api/nv-core-api-start.sh` (153 lines, proven workflow!)

**Port Matrix:** `config/ports.nv.yaml` (canonical source of truth)

**Full Guide:** `services/DEVELOPER_A_CONVENTIONS_GUIDE.md` (1000+ lines)

**Quick Ref:** `services/DEVELOPER_A_QUICK_REFERENCE.md` (one-page cheat sheet)

---

## 🎯 Summary

**Infrastructure Status:** ✅ 100% Ready

**Your Tasks:**
1. Read documentation (60 minutes)
2. Build Rust Memory Service (connects to existing DB)
3. Build Rust Graph Service (connects to existing DB & AGE)
4. Create container startup scripts
5. Integrate with Core API JWT

**What's Ready:**
- ✅ Database: `ninaivalaigal_dev`
- ✅ AGE Graph: `ninaivalaigal_intelligence_dev`
- ✅ PgBouncer: Connection pooling
- ✅ Core API: JWT authentication (port 13390)
- ✅ Ports assigned: 13393, 13394
- ✅ Documentation: Complete

**What You Create:**
- ❌ NO databases
- ❌ NO database containers
- ❌ NO AGE graphs
- ✅ Rust Memory Service (port 13393)
- ✅ Rust Graph Service (port 13394)
- ✅ Container startup scripts
- ✅ Database schemas (memory, graph)

---

**Start here:** Read `services/DEVELOPER_A_QUICKSTART.md` 🚀

Good luck with your Rust services! 🦀
