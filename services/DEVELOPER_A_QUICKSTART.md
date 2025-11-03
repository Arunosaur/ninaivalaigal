# Developer A - Quick Start Guide

**Your Role:** Rust Memory Service & Graph Service Development
**Updated:** Oct 16, 2025
**Status:** Ready to Start

---

## 🎯 What You Need to Do

### **DO NOT CREATE ANY DATABASES!** ❌

The database infrastructure is **already set up** and **ready to use**:

✅ **Database:** `ninaivalaigal_dev` (running in `ninaivalaigal-dev-db`)
✅ **AGE Graph:** `ninaivalaigal_intelligence_dev` (created and ready)
✅ **PgBouncer:** Connection pooling ready
✅ **Redis:** Cache ready

**Your job:** Connect your Rust services to the **existing** infrastructure.

---

## 📚 Required Reading (In Order)

### 1. **DEVELOPER_A_QUICK_REFERENCE.md** (5 min) ⭐ START HERE
**Location:** `services/DEVELOPER_A_QUICK_REFERENCE.md`

Quick one-page reference with:
- Your port assignments (13393, 13394)
- Container names
- Database connection
- Build workflow
- Do's and Don'ts

### 2. **DEVELOPER_A_CONVENTIONS_GUIDE.md** (15 min) ⭐ COMPREHENSIVE
**Location:** `services/DEVELOPER_A_CONVENTIONS_GUIDE.md`

Complete guide covering:
- Container naming: `ninaivalaigal-dev-memory-service`
- Database naming: `ninaivalaigal_dev` (shared, don't create!)
- Apple Container CLI usage
- Docker → tar → Container workflow
- Database connection via PgBouncer
- JWT integration with Core API
- Complete working examples
- Common mistakes to avoid

### 3. **NAMING_CONVENTIONS.md** (10 min)
**Location:** `docs/NAMING_CONVENTIONS.md`

Naming conventions for:
- Containers: `ninaivalaigal-{env}-{service}`
- Databases: `ninaivalaigal_{env}`
- AGE Graphs: `ninaivalaigal_intelligence_{env}`
- Scripts: `nv-{service}-{action}.sh`
- Complete validation commands

### 4. **OPTION_A_NAMING_SUMMARY.md** (5 min)
**Location:** `docs/OPTION_A_NAMING_SUMMARY.md`

Why we use Option A (Full Suffixes):
- Multi-environment support
- Complete naming matrix
- Environment configurations

### 5. **ports.nv.yaml** (Reference)
**Location:** `config/ports.nv.yaml`

Canonical port assignments and naming patterns

---

## 🚀 Your Services

### Memory Service (Rust)

**Port:** 13393
**Container:** `ninaivalaigal-dev-memory-service`
**Purpose:** Memory CRUD operations in Rust

**Database Connection:**
```bash
# Use existing database (don't create!)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

**AGE Graph:**
```bash
# Use existing graph (already created!)
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev
```

---

### Graph Service (Rust)

**Port:** 13394
**Container:** `ninaivalaigal-dev-graph-service`
**Purpose:** Graph intelligence operations in Rust

**Same database and graph as Memory Service!**

---

## 🗄️ Database Infrastructure (Already Set Up)

### What's Already Running

```bash
# Check status
container list | grep ninaivalaigal

# You should see:
ninaivalaigal-dev-db         # PostgreSQL 15 + AGE
ninaivalaigal-dev-pgbouncer  # Connection pooling
ninaivalaigal-dev-redis      # Cache
ninaivalaigal-dev-core-api   # Python Core API (port 13390)
```

### Database Details

**Database:** `ninaivalaigal_dev`
```sql
-- Already exists, DON'T CREATE!
-- Connect: postgresql://nina:password@pgbouncer:6432/ninaivalaigal_dev
```

**AGE Graph:** `ninaivalaigal_intelligence_dev`
```sql
-- Already created, READY TO USE!
-- Graph schema: ninaivalaigal_intelligence_dev
```

**Tables/Schemas Available:**
```
public schema:
  - users (from Core API)
  - teams (from Core API)
  - organizations (from Core API)

Your schemas (create as needed):
  - memory schema (for Memory Service tables)
  - graph schema (for Graph Service tables)
```

---

## 🔧 What You Actually Need to Do

### Step 1: Read the Documentation (30 min)
✅ Read the 5 documents listed above in order

### Step 2: Set Up Your Environment (5 min)

```bash
cd rust-services/memory-service

# Copy environment template
cp .env.example .env

# Verify configuration
cat .env
# Should show:
# DATABASE_URL=postgresql://nina:dev_password_change_in_production@192.168.64.137:6432/ninaivalaigal_dev
# (IP will be dynamic)
```

### Step 3: Create Your Service Scripts (30 min)

Following the Core API example, create:

```bash
# Memory Service
nv-memory-service-start.sh   # Build and start container
nv-memory-service-stop.sh    # Stop container
nv-memory-service-status.sh  # Check status

# Graph Service
nv-graph-service-start.sh    # Build and start container
nv-graph-service-stop.sh     # Stop container
nv-graph-service-status.sh   # Check status
```

**Template:** Copy from `services/core-api/nv-core-api-start.sh` (153 lines, proven to work!)

### Step 4: Build Your Rust Service (Your Code)

```rust
// src/main.rs
use sqlx::PgPool;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Get DATABASE_URL from environment
    let database_url = std::env::var("DATABASE_URL")?;

    // Connect to existing database
    let pool = PgPool::connect(&database_url).await?;

    // Your service code here
    // ...

    Ok(())
}
```

### Step 5: Connect to AGE Graph (If Needed)

```rust
// For AGE graph queries
let graph_name = std::env::var("GRAPHOPS_GRAPH")
    .unwrap_or_else(|_| "ninaivalaigal_intelligence_dev".to_string());

// Execute Cypher query via AGE
let query = format!(
    "SELECT * FROM cypher('{}', $$ MATCH (n) RETURN n $$) as (result agtype);",
    graph_name
);

let result = sqlx::query(&query)
    .fetch_all(&pool)
    .await?;
```

### Step 6: Implement JWT Authentication

Get JWT tokens from Core API and validate them:

```rust
use jsonwebtoken::{decode, DecodingKey, Validation};

#[derive(Debug, serde::Deserialize)]
struct Claims {
    user_id: String,
    email: String,
    exp: usize,
}

fn validate_token(token: &str) -> Result<String, Error> {
    let jwt_secret = std::env::var("NINAIVALAIGAL_JWT_SECRET")?;

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(jwt_secret.as_bytes()),
        &Validation::default(),
    )?;

    Ok(token_data.claims.user_id)
}
```

### Step 7: Test Integration

```bash
# 1. Get JWT from Core API
TOKEN=$(curl -s -X POST http://localhost:13390/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"rust@test.com","password":"test123","name":"Rust User"}' \
  | jq -r '.jwt_token')

# 2. Call your Memory Service with JWT
curl -X POST http://localhost:13393/memory/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test from Rust"}'
```

---

## ❌ DO NOT DO

### 1. **Don't Create Databases**
```bash
# ❌ WRONG - Don't do this!
docker exec memory-postgres psql -c "CREATE DATABASE ninaivalaigal_dev;"
docker exec graph-postgres psql -c "CREATE DATABASE memory_db;"

# ✅ RIGHT - Use existing database
DATABASE_URL="postgresql://nina:password@pgbouncer:6432/ninaivalaigal_dev"
```

### 2. **Don't Create Database Containers**
```bash
# ❌ WRONG - Don't do this!
docker run --name memory-postgres -p 5433:5432 postgres:15
docker run --name graph-postgres -p 5434:5432 postgres:15

# ✅ RIGHT - Connect to existing container
container inspect ninaivalaigal-dev-db
```

### 3. **Don't Use Docker Commands**
```bash
# ❌ WRONG
docker run ...
docker ps
docker build ...

# ✅ RIGHT
container run ...
container list
# Build with docker, then: docker save → container image load
```

### 4. **Don't Use Wrong Ports**
```bash
# ❌ WRONG
-p 5433:5432  # Random port
-p 8080:8000  # Not canonical

# ✅ RIGHT
-p 13393:8000  # Memory Service (from ports.nv.yaml)
-p 13394:8000  # Graph Service (from ports.nv.yaml)
```

### 5. **Don't Create AGE Graphs**
```bash
# ❌ WRONG - Graph already created!
SELECT create_graph('ninaivalaigal_intelligence_dev');

# ✅ RIGHT - Use existing graph
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev
```

---

## ✅ DO THIS

### 1. **Connect to Existing Database**
```bash
# Dynamic PgBouncer IP discovery
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

### 2. **Use Correct Container Names**
```bash
container run -d \
  --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 \
  nina-memory-service:arm64
```

### 3. **Use Canonical Ports**
```bash
# Memory Service
-p 13393:8000

# Graph Service
-p 13394:8000
```

### 4. **Use Apple Container CLI**
```bash
container run ...
container list
container logs -n 50 ninaivalaigal-dev-memory-service
```

### 5. **Create Schemas (Not Databases)**
```sql
-- Inside ninaivalaigal_dev database
CREATE SCHEMA IF NOT EXISTS memory;
CREATE TABLE memory.memories (...);

CREATE SCHEMA IF NOT EXISTS graph;
CREATE TABLE graph.nodes (...);
```

---

## 🧪 Testing Your Setup

### Verify Database Access
```bash
# Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Test connection
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev" -c "SELECT current_database();"

# Expected output: ninaivalaigal_dev
```

### Verify AGE Graph
```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT * FROM ag_catalog.ag_graph;"

# Expected output:
# ninaivalaigal_intelligence_dev
```

### Test Core API Integration
```bash
# Health check
curl http://localhost:13390/health

# Get JWT token
curl -X POST http://localhost:13390/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@rust.com","password":"test123","name":"Test User"}'
```

---

## 📊 Your Environment Setup

```bash
# In rust-services/memory-service/.env
DATABASE_URL=postgresql://nina:dev_password_change_in_production@192.168.64.137:6432/ninaivalaigal_dev
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev
NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production
RUST_LOG=info
```

---

## 🎯 Success Criteria

You're set up correctly when:

- ✅ Can connect to `ninaivalaigal_dev` database via PgBouncer
- ✅ Can query `ninaivalaigal_intelligence_dev` graph
- ✅ Container named `ninaivalaigal-dev-memory-service`
- ✅ Service running on port `13393`
- ✅ Can validate JWT tokens from Core API
- ✅ Health endpoint responds: `http://localhost:13393/health`
- ✅ No separate database containers created

---

## 🆘 Getting Help

**If stuck, check:**

1. **Core API scripts:** `services/core-api/nv-core-api-start.sh` (working example!)
2. **Port matrix:** `config/ports.nv.yaml` (canonical ports)
3. **Conventions:** `services/DEVELOPER_A_CONVENTIONS_GUIDE.md` (1000+ lines of examples)
4. **Naming:** `docs/NAMING_CONVENTIONS.md` (complete patterns)

**Common issues:**

- Wrong database name → Should be `ninaivalaigal_dev` (with `_dev`!)
- Wrong graph name → Should be `ninaivalaigal_intelligence_dev` (with `_dev`!)
- Hardcoded IP → Use dynamic discovery: `container inspect ninaivalaigal-dev-pgbouncer`
- Wrong port → Use `6432` (PgBouncer), not `5432` (direct PostgreSQL)

---

## 🚀 Ready to Start!

**Infrastructure:** ✅ Ready
**Database:** ✅ Created
**AGE Graph:** ✅ Created
**Documentation:** ✅ Complete
**Examples:** ✅ Available (Core API)

**Your next step:** Read the 5 documents, then start coding your Rust services!

Good luck! 🦀
