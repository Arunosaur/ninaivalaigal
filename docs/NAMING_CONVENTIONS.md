# Ninaivalaigal Naming Conventions

**Version:** 1.0  
**Updated:** Oct 16, 2025  
**Reference:** SPEC-086, ports.nv.yaml v2.1

---

## 🎯 Overview

All ninaivalaigal services, databases, and containers follow consistent naming patterns for:
- Easy identification
- Environment separation (dev/test/prod)
- Automated tooling compatibility
- Team coordination

---

## 📋 Naming Patterns

### 1. Container Names

**Pattern:** `ninaivalaigal-{env}-{service}`

**Components:**
- `ninaivalaigal` - Project name (always, never abbreviated)
- `{env}` - Environment: `dev`, `test`, or `prod`
- `{service}` - Service name (kebab-case)

**Examples:**
```
ninaivalaigal-dev-db                    # PostgreSQL (development)
ninaivalaigal-dev-pgbouncer             # PgBouncer (development)
ninaivalaigal-dev-redis                 # Redis (development)
ninaivalaigal-dev-core-api              # Core API service
ninaivalaigal-dev-business-logic        # Business Logic service
ninaivalaigal-dev-memory-service        # Rust Memory Service
ninaivalaigal-dev-graph-service         # Rust Graph Service
ninaivalaigal-test-core-api             # Core API (test)
ninaivalaigal-prod-gateway              # Gateway (production)
```

**Why Hyphen (-):** Apple Container CLI and Docker standard

---

### 2. Database Names

**Pattern:** `ninaivalaigal_{env}`

**Components:**
- `ninaivalaigal` - Project name (always)
- `{env}` - Environment: `dev`, `test`, or `prod`

**Examples:**
```sql
ninaivalaigal_dev      -- Development database
ninaivalaigal_test     -- Test database
ninaivalaigal_prod     -- Production database
```

**Why Underscore (_):** PostgreSQL convention for database names

**IMPORTANT:** All services in the same environment share the same database!

**Architecture Choice:** **Option A - Full Suffixes**
- Enables running multiple environments on same host
- Self-documenting database dumps (filename includes environment)
- Clear separation for dev, test, prod on shared infrastructure

---

### 2b. Apache AGE Graph Names

**Pattern:** `ninaivalaigal_intelligence_{env}`

**Components:**
- `ninaivalaigal_intelligence` - Graph purpose identifier
- `{env}` - Environment: `dev`, `test`, or `prod`

**Examples:**
```sql
-- Inside ninaivalaigal_dev database
ninaivalaigal_intelligence_dev

-- Inside ninaivalaigal_test database  
ninaivalaigal_intelligence_test

-- Inside ninaivalaigal_prod database
ninaivalaigal_intelligence_prod
```

**Why Suffix:** Consistent with database naming (Option A), enables multi-environment testing

**Configuration:**
```bash
# Development
DATABASE_URL=postgresql://nina:password@host:6432/ninaivalaigal_dev
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_dev

# Test
DATABASE_URL=postgresql://nina:password@host:6432/ninaivalaigal_test
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_test

# Production
DATABASE_URL=postgresql://nina:password@host:6432/ninaivalaigal_prod
GRAPHOPS_GRAPH=ninaivalaigal_intelligence_prod
```

---

### 3. Script Names

**Pattern:** `nv-{service}-{action}.sh`

**Components:**
- `nv` - Ninaivalaigal prefix (abbreviated for brevity)
- `{service}` - Service name (kebab-case)
- `{action}` - Action: `start`, `stop`, `status`, `rebuild`, etc.

**Examples:**
```bash
nv-db-start.sh
nv-db-stop.sh
nv-pgbouncer-start.sh
nv-core-api-start.sh
nv-core-api-stop.sh
nv-core-api-status.sh
nv-memory-service-start.sh
nv-graph-service-rebuild.sh
```

**Location:** Place scripts in the service directory or `scripts/` directory

---

### 4. Schema Names (PostgreSQL)

**Pattern:** `{service}` or default `public`

**Examples:**
```sql
public              -- Shared tables (users, teams, orgs)
memory              -- Memory service tables
graph               -- Graph service tables
business_logic      -- Business logic service tables
```

**Note:** Use schemas to organize tables by service while sharing a database

---

### 5. Table Names

**Pattern:** `{entity}` or `{service}_{entity}`

**Format:** Lowercase with underscores (snake_case)

**Examples:**
```sql
-- Shared in public schema
users
teams
organizations
team_members

-- Service-specific (if using service schemas)
memory.memories
memory.memory_tags
graph.nodes
graph.edges

-- Service-specific (if using table prefixes)
memory_memories
memory_tags
graph_nodes
graph_edges
```

---

### 6. Image Names

**Pattern:** `nina-{service}:{tag}`

**Components:**
- `nina` - Short project prefix
- `{service}` - Service name (kebab-case)
- `{tag}` - Version tag: `arm64`, `v1.0`, `latest`, etc.

**Examples:**
```
nina-core-api:arm64
nina-business-logic:v1.0
nina-memory-service:arm64
nina-graph-service:latest
nina-gateway:v2.0
```

---

## 🚫 Anti-Patterns (Don't Do This!)

### ❌ Wrong Container Names
```bash
memory-postgres          # Missing project name and environment
my-service              # Not descriptive, no environment
test-container          # Generic, no project name
core_api                # Wrong separator (underscore)
ninaivalaigal_dev_api   # Wrong separator (should be hyphen)
nv-dev-api              # Project name abbreviated
```

### ❌ Wrong Database Names
```bash
postgres                # Generic, no project context
memory_db               # Service-specific (should be shared)
ninaivalaigal-dev       # Wrong separator (hyphen instead of underscore)
ninaivalaigal           # Missing environment
nina_dev                # Project name abbreviated
```

### ❌ Wrong Script Names
```bash
start-memory.sh         # Missing project prefix
memory_start.sh         # Wrong separator
start-nv-memory.sh      # Prefix at wrong end
memory-service-start.sh # Missing nv prefix
```

### ❌ Wrong Commands
```bash
# Don't create separate databases per service!
docker exec memory-postgres psql -U postgres -c "CREATE DATABASE memory_db;"
docker exec graph-postgres psql -U postgres -c "CREATE DATABASE graph_db;"

# Don't use service-specific database containers!
docker run --name memory-postgres ...
docker run --name graph-postgres ...
```

---

## ✅ Correct Examples

### Container Creation
```bash
# Memory Service
container run -d \
  --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 \
  -e DATABASE_URL="postgresql://nina:password@host:6432/ninaivalaigal_dev" \
  nina-memory-service:arm64

# Graph Service
container run -d \
  --name ninaivalaigal-dev-graph-service \
  -p 13394:8000 \
  -e DATABASE_URL="postgresql://nina:password@host:6432/ninaivalaigal_dev" \
  nina-graph-service:arm64
```

### Database Connection (All Services)
```bash
# All services connect to the SAME database
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

### Script Creation
```bash
# Create start script
cat > nv-memory-service-start.sh << 'EOF'
#!/usr/bin/env bash
# Start Memory Service
CONTAINER_NAME="ninaivalaigal-dev-memory-service"
IMAGE_NAME="nina-memory-service:arm64"
# ... rest of script
EOF

chmod +x nv-memory-service-start.sh
```

---

## 📊 Complete Example: Memory Service

### All Components Named Correctly

```bash
# 1. Build image
docker build -t nina-memory-service:arm64 .

# 2. Save and load (Docker → Container CLI)
docker save -o /tmp/memory.tar nina-memory-service:arm64
container image load -i /tmp/memory.tar

# 3. Get database connection
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"

# 4. Run container
container run -d \
  --name ninaivalaigal-dev-memory-service \
  -p 13393:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  nina-memory-service:arm64

# 5. Check status
container list | grep ninaivalaigal-dev-memory-service
curl http://localhost:13393/health

# 6. View logs
container logs -n 50 ninaivalaigal-dev-memory-service
```

### Database Schema (Inside PostgreSQL)

```sql
-- Connect to shared database
\c ninaivalaigal_dev

-- Create schema for memory service
CREATE SCHEMA IF NOT EXISTS memory;

-- Create tables in service schema
CREATE TABLE memory.memories (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES public.users(id),
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memory.memory_tags (
  id UUID PRIMARY KEY,
  memory_id UUID REFERENCES memory.memories(id),
  tag VARCHAR(255)
);
```

---

## 🌍 Environment-Specific Examples

### Development Environment
```
Container:  ninaivalaigal-dev-memory-service
Database:   ninaivalaigal_dev
Port:       13393 (from ports.nv.yaml: apple.dev.memory_service)
Script:     nv-memory-service-start.sh
```

### Test Environment
```
Container:  ninaivalaigal-test-memory-service
Database:   ninaivalaigal_test
Port:       13493 (from ports.nv.yaml: apple.test.memory_service)
Script:     nv-memory-service-start.sh (same, uses NINA_ENV=test)
```

### Production Environment
```
Container:  ninaivalaigal-prod-memory-service
Database:   ninaivalaigal_prod
Port:       13593 (from ports.nv.yaml: apple.prod.memory_service)
Script:     nv-memory-service-start.sh (same, uses NINA_ENV=prod)
```

---

## 🔍 Validation Commands

### Check Container Names
```bash
# Should all start with "ninaivalaigal-{env}-"
container list | grep ninaivalaigal

# Expected output:
# ninaivalaigal-dev-db
# ninaivalaigal-dev-pgbouncer
# ninaivalaigal-dev-redis
# ninaivalaigal-dev-core-api
# ninaivalaigal-dev-memory-service
# ninaivalaigal-dev-graph-service
```

### Check Database Names
```bash
# Should be: ninaivalaigal_dev, ninaivalaigal_test, ninaivalaigal_prod
container exec ninaivalaigal-dev-db psql -U nina -l | grep ninaivalaigal

# Expected output:
# ninaivalaigal_dev     | nina | UTF8
```

### Check Scripts
```bash
# Should all start with "nv-"
ls -la scripts/*.sh | grep nv-

# Expected output:
# nv-db-start.sh
# nv-pgbouncer-start.sh
# nv-core-api-start.sh
# nv-memory-service-start.sh
```

---

## 📚 References

1. **Port Matrix:** `config/ports.nv.yaml` - Canonical ports and container names
2. **Developer A Guide:** `services/DEVELOPER_A_CONVENTIONS_GUIDE.md` - Detailed examples
3. **Port Allocation:** `services/MICROSERVICES_PORT_ALLOCATION.md` - Port planning
4. **SPEC-086:** Multi-Runtime Port Allocation specification

---

## ✅ Quick Checklist

When creating a new service, verify:

- [ ] Container name: `ninaivalaigal-{env}-{service}`
- [ ] Database: Uses existing `ninaivalaigal_{env}` (don't create new!)
- [ ] Image name: `nina-{service}:{tag}`
- [ ] Scripts: `nv-{service}-{action}.sh`
- [ ] Port: From `ports.nv.yaml`
- [ ] Schema (optional): `{service}` schema inside shared database
- [ ] Tables: Lowercase snake_case in service schema

---

**Key Principle:** 
> All services in the same environment share ONE database (`ninaivalaigal_{env}`).  
> Use schemas or table prefixes to separate service data within the shared database.

**Why?**
- Simpler infrastructure (one DB per environment)
- Easier cross-service queries and transactions
- Reduced operational complexity
- Consistent with existing ninaivalaigal architecture

---

**Last Updated:** Oct 16, 2025  
**Maintained By:** Developer C (Python Services) + Developer A (Rust Services)
