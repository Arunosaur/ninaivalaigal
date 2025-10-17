# Developer A - Naming Conventions & Apple Container CLI Guide

**For:** Rust Memory Service & Graph Service Development  
**Updated:** Oct 16, 2025  
**Reference:** SPEC-086, ports.nv.yaml v2.1

---

## 🎯 Quick Reference

Your services and their canonical settings:

| Service | Port | Container Name | Script Prefix |
|---------|------|----------------|---------------|
| Memory Service | 13393 | ninaivalaigal-dev-memory-service | nv-memory-service-* |
| Graph Service | 13394 | ninaivalaigal-dev-graph-service | nv-graph-service-* |

---

## 📋 Naming Conventions

### Container Names

**Format:** `ninaivalaigal-{env}-{service}`
- `ninaivalaigal` - Project name (always)
- `{env}` - Environment: `dev`, `test`, `prod`
- `{service}` - Service name: `memory-service`, `graph-service`, etc.

### ❌ Don't Do This (Old Way)
```bash
docker run --name memory-postgres ...
docker run --name my-service ...
docker run --name test-container ...
```

### ✅ Do This (Ninaivalaigal Convention)
```bash
# Pattern: ninaivalaigal-{env}-{service}
container run --name ninaivalaigal-dev-memory-service ...
container run --name ninaivalaigal-dev-graph-service ...
```

### Database Names

**Format:** `ninaivalaigal_{env}`
- `ninaivalaigal_dev` - Development database
- `ninaivalaigal_test` - Test database
- `ninaivalaigal_prod` - Production database

### ❌ Don't Do This
```bash
# Wrong: Creating your own database
docker exec memory-postgres psql -U postgres -c "CREATE DATABASE ninaivalaigal_dev;"

# Wrong: Using default database names
CREATE DATABASE postgres;
CREATE DATABASE memory_db;
CREATE DATABASE my_database;
```

### ✅ Do This
```bash
# Correct: Use existing shared database
# Database already exists: ninaivalaigal_dev

# Connect to it via PgBouncer
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

**IMPORTANT:** Don't create a separate database! Use the existing `ninaivalaigal_dev` database shared by all services.

**Examples:**
```bash
ninaivalaigal-dev-memory-service      # Your Rust memory service (dev)
ninaivalaigal-dev-graph-service       # Your Rust graph service (dev)
ninaivalaigal-dev-db                  # Existing PostgreSQL
ninaivalaigal-dev-pgbouncer           # Existing PgBouncer
ninaivalaigal-dev-redis               # Existing Redis
ninaivalaigal-dev-core-api            # Python Core API (Developer C)
```

---

## 🔌 Port Allocation (SPEC-086)

### Your Assigned Ports (Apple Container - Dev)

**Reference:** `config/ports.nv.yaml`

| Service | External Port | Internal Port | Formula |
|---------|--------------|---------------|---------|
| Memory Service | **13393** | 8000 | 13370 + 20 + 0 + 3 |
| Graph Service | **13394** | 8000 | 13370 + 20 + 0 + 4 |

**Port Formula:**
```
Final Port = Base (13370) + Runtime (Apple: 20) + Environment (dev: 0) + Service Offset
```

### ❌ Don't Do This
```bash
# Wrong: Using arbitrary ports
docker run -p 5433:5432 ...    # Port collision risk!
docker run -p 8080:8000 ...    # Not canonical
docker run -p 3000:3000 ...    # Conflicts with UI
```

### ✅ Do This
```bash
# Memory Service: External 13393 → Internal 8000
container run -p 13393:8000 --name ninaivalaigal-dev-memory-service ...

# Graph Service: External 13394 → Internal 8000
container run -p 13394:8000 --name ninaivalaigal-dev-graph-service ...
```

**Internal Port:** Always use **8000** inside your container  
**External Port:** Use assigned canonical port (13393 or 13394)

---

## 🍎 Apple Container CLI (Not Docker!)

### Why Apple Container CLI?

We use **Apple Container CLI** (`container` command), not Docker:
- Native ARM64 support for Apple Silicon
- Better performance on macOS
- Consistent with existing ninaivalaigal infrastructure

### Command Translation Table

| Docker Command | Apple Container CLI | Notes |
|----------------|---------------------|-------|
| `docker run` | `container run` | Same arguments |
| `docker build` | Build with Docker, then convert | See workflow below |
| `docker ps` | `container list` | |
| `docker stop` | `container stop` | |
| `docker rm` | `container rm` | |
| `docker logs` | `container logs` | Use `-n N` not `--tail` |
| `docker inspect` | `container inspect` | |
| `docker exec` | `container exec` | |

---

## 🔄 Proven Workflow: Docker → tar → Apple Container

### The Problem
`container build` hangs with no output (known issue)

### The Solution
Build with Docker, save as tar, load into Apple Container:

```bash
#!/usr/bin/env bash
# Step 1: Build with Docker (reliable)
docker build --no-cache -t nina-memory-service:arm64 -f Dockerfile .

# Step 2: Save as tar
docker save -o /tmp/memory-service.tar nina-memory-service:arm64

# Step 3: Load into Apple Container CLI
container image load -i /tmp/memory-service.tar

# Step 4: Cleanup
rm /tmp/memory-service.tar

# Step 5: Run with Apple Container CLI
container run -d \
    --name ninaivalaigal-dev-memory-service \
    -p 13393:8000 \
    -e DATABASE_URL="postgresql://..." \
    nina-memory-service:arm64
```

**This workflow is proven to work!** (Used by Core API)

---

## 📝 Script Naming Convention

### Pattern: `nv-{service}-{action}.sh`

**Your Scripts Should Be:**
```bash
nv-memory-service-start.sh       # Start Memory Service
nv-memory-service-stop.sh        # Stop Memory Service
nv-memory-service-status.sh      # Check status
nv-memory-service-rebuild.sh     # Rebuild image

nv-graph-service-start.sh        # Start Graph Service
nv-graph-service-stop.sh         # Stop Graph Service
nv-graph-service-status.sh       # Check status
nv-graph-service-rebuild.sh      # Rebuild image
```

**Location:** Place in `rust-services/memory-service/` or `rust-services/graph-service/`

**Reference Example:** See `services/core-api/nv-core-api-start.sh` (153 lines, fully working)

---

## 🔧 Complete Example: Memory Service

### Example Dockerfile
```dockerfile
FROM rust:1.75-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Build dependencies (cache layer)
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY src ./src

# Build application
RUN cargo build --release

# Expose internal port
EXPOSE 8000

# Run
CMD ["./target/release/memory-service"]
```

### Example Start Script (nv-memory-service-start.sh)

```bash
#!/usr/bin/env bash
# Start Memory Service with Apple Container CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Starting ninaivalaigal Memory Service (Rust)"
echo "================================================"

# Load environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    source "$PROJECT_ROOT/.env.dev"
fi

# Configuration
NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"
IMAGE_NAME="nina-memory-service:arm64"
PORT_EXTERNAL=13393  # From ports.nv.yaml
PORT_INTERNAL=8000

echo ""
echo "📊 Configuration:"
echo "   Environment: $NINA_ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Port: $PORT_EXTERNAL → $PORT_INTERNAL"

# Discover PgBouncer IP dynamically
PGB_IP=$(container inspect ninaivalaigal-${NINA_ENV}-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$PGB_IP" ] || [ "$PGB_IP" = "null" ]; then
    echo "❌ PgBouncer not found!"
    exit 1
fi
echo "   PgBouncer: $PGB_IP:6432"

DATABASE_URL="postgresql://nina:${NINA_DB_PASSWORD}@${PGB_IP}:6432/ninaivalaigal_${NINA_ENV}"

echo ""
echo "📦 Building image..."
cd "$SCRIPT_DIR"

# Build with Docker
docker build --no-cache -t "$IMAGE_NAME" . > /tmp/memory-build.log 2>&1
echo "   ✅ Docker build complete"

# Save as tar
docker save -o /tmp/memory-service.tar "$IMAGE_NAME"
echo "   ✅ Saved to tar"

# Load into Apple Container
container image load -i /tmp/memory-service.tar > /dev/null 2>&1
echo "   ✅ Loaded into Apple Container"

# Cleanup
rm -f /tmp/memory-service.tar /tmp/memory-build.log

echo ""
echo "🛑 Stopping existing container..."
container stop "$CONTAINER_NAME" 2>/dev/null || true
container rm "$CONTAINER_NAME" 2>/dev/null || true

echo ""
echo "🚀 Starting container..."
container run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT_EXTERNAL}:${PORT_INTERNAL}" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e RUST_LOG=info \
    "$IMAGE_NAME"

echo ""
echo "⏳ Waiting for health check..."
sleep 3

for i in {1..10}; do
    if curl -s "http://localhost:${PORT_EXTERNAL}/health" > /dev/null 2>&1; then
        echo "✅ Memory Service is healthy!"
        break
    fi
    echo "   Waiting... ($i/10)"
    sleep 2
done

echo ""
echo "================================================"
echo "✅ Memory Service Started Successfully!"
echo "================================================"
echo ""
echo "📍 Access:"
echo "   Health:  http://localhost:${PORT_EXTERNAL}/health"
echo "   API:     http://localhost:${PORT_EXTERNAL}/memory/*"
echo ""
echo "🔍 Commands:"
echo "   Status:  container list | grep memory"
echo "   Logs:    container logs -f $CONTAINER_NAME"
echo "   Stop:    container stop $CONTAINER_NAME"
echo ""
```

**Make it executable:**
```bash
chmod +x nv-memory-service-start.sh
```

---

## 🌐 Database Connection

### Get PgBouncer IP Dynamically

```bash
# Always discover IP dynamically (don't hardcode!)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Construct DATABASE_URL
DATABASE_URL="postgresql://nina:${NINA_DB_PASSWORD}@${PGB_IP}:6432/ninaivalaigal_dev"
```

### ❌ Don't Do This
```bash
# Wrong: Hardcoded IP (changes on restart!)
DATABASE_URL="postgresql://user:pass@192.168.64.137:6432/db"

# Wrong: Using localhost (doesn't work in container)
DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# Wrong: Different port (not PgBouncer!)
DATABASE_URL="postgresql://user:pass@host:5432/db"
```

### ✅ Do This
```bash
# Correct: Dynamic IP discovery + PgBouncer port 6432
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

**Credentials from `.env.dev`:**
- User: `nina`
- Password: `dev_password_change_in_production`
- Database: `ninaivalaigal_dev`
- Port: **6432** (PgBouncer, not 5432!)

---

## 🔐 JWT Integration with Core API

Your Rust services need to accept JWT tokens from Core API.

### Get JWT Secret

From `.env.dev`:
```bash
NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production
```

### Test Flow

```bash
# 1. Get JWT from Core API (Developer C)
TOKEN=$(curl -s -X POST http://localhost:13390/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"rust@test.com","password":"test123","name":"Rust User"}' \
  | jq -r '.jwt_token')

# 2. Use JWT with your Memory Service
curl -X POST http://localhost:13393/memory/remember \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory from Rust"}'
```

### Rust JWT Validation Example

```rust
use jsonwebtoken::{decode, DecodingKey, Validation};

#[derive(Debug, serde::Deserialize)]
struct Claims {
    user_id: String,
    email: String,
    exp: usize,
}

fn extract_user_id(token: &str) -> Result<String, Error> {
    let jwt_secret = std::env::var("NINAIVALAIGAL_JWT_SECRET")?;
    
    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(jwt_secret.as_bytes()),
        &Validation::default(),
    )?;
    
    Ok(token_data.claims.user_id)
}
```

---

## 📚 References

### Key Files to Reference
1. **Port Matrix:** `config/ports.nv.yaml` - Canonical port allocations
2. **Environment:** `.env.dev` - Database credentials, JWT secret
3. **Core API Scripts:** `services/core-api/nv-core-api-start.sh` - Working example (153 lines)
4. **Port Plan:** `services/MICROSERVICES_PORT_ALLOCATION.md` - Your port assignments

### Existing Infrastructure (Already Running)

| Service | Container Name | Port | IP (Dynamic) |
|---------|----------------|------|--------------|
| PostgreSQL | ninaivalaigal-dev-db | 5452 | 192.168.64.x |
| PgBouncer | ninaivalaigal-dev-pgbouncer | 6452 | 192.168.64.137 |
| Redis | ninaivalaigal-dev-redis | 6399 | 192.168.64.105 |
| Core API | ninaivalaigal-dev-core-api | 13390 | Running ✅ |

**Your Services:**
| Service | Container Name | Port | Status |
|---------|----------------|------|--------|
| Memory Service | ninaivalaigal-dev-memory-service | 13393 | 🚧 Your task |
| Graph Service | ninaivalaigal-dev-graph-service | 13394 | 🚧 Your task |

---

## ✅ Checklist for Your Services

### Memory Service Setup
- [ ] Container name: `ninaivalaigal-dev-memory-service`
- [ ] External port: `13393`
- [ ] Internal port: `8000`
- [ ] Scripts: `nv-memory-service-start.sh`, `nv-memory-service-stop.sh`, `nv-memory-service-status.sh`
- [ ] Dockerfile with Rust build
- [ ] Dynamic PgBouncer IP discovery
- [ ] JWT authentication from Core API
- [ ] Health check endpoint: `/health`

### Graph Service Setup
- [ ] Container name: `ninaivalaigal-dev-graph-service`
- [ ] External port: `13394`
- [ ] Internal port: `8000`
- [ ] Scripts: `nv-graph-service-start.sh`, `nv-graph-service-stop.sh`, `nv-graph-service-status.sh`
- [ ] Dockerfile with Rust build
- [ ] Dynamic PgBouncer IP discovery
- [ ] JWT authentication from Core API
- [ ] Health check endpoint: `/health`

---

## 🚨 Common Mistakes to Avoid

### ❌ Port Mistakes
```bash
# Wrong: Random ports
-p 5433:5432
-p 8080:8000
-p 3000:3000

# Correct: Canonical ports
-p 13393:8000  # Memory Service
-p 13394:8000  # Graph Service
```

### ❌ Naming Mistakes
```bash
# Wrong: Inconsistent names
--name memory-postgres
--name my-rust-service
--name test-container

# Correct: Follow convention
--name ninaivalaigal-dev-memory-service
--name ninaivalaigal-dev-graph-service
```

### ❌ Database Mistakes
```bash
# Wrong: Hardcoded IP
DATABASE_URL="postgresql://...@192.168.64.137:..."

# Wrong: Direct PostgreSQL (port 5432)
DATABASE_URL="postgresql://...@host:5432/..."

# Correct: Dynamic IP + PgBouncer (port 6432)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"
```

### ❌ Tool Mistakes
```bash
# Wrong: Using docker commands
docker run ...
docker ps
docker build ...

# Correct: Using container commands
container run ...
container list
# Build with docker, then: docker save → container image load
```

---

## 🤝 Coordination with Developer C

### Shared Resources
- **Database:** Same `ninaivalaigal_dev` via PgBouncer
- **JWT Secret:** Same `NINAIVALAIGAL_JWT_SECRET` from `.env.dev`
- **Port Range:** 13390-13395 (yours: 13393-13394)

### Integration Testing
```bash
# 1. Developer C's Core API (port 13390)
curl http://localhost:13390/health

# 2. Your Memory Service (port 13393)
curl http://localhost:13393/health

# 3. Your Graph Service (port 13394)
curl http://localhost:13394/health

# 4. Cross-service auth test
TOKEN=$(curl -s http://localhost:13390/auth/signup ... | jq -r '.jwt_token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:13393/memory/...
```

---

## 📖 Quick Commands Reference

```bash
# Check what's running
container list | grep ninaivalaigal

# Get PgBouncer IP
container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1

# Check logs
container logs -n 50 ninaivalaigal-dev-memory-service

# Stop service
container stop ninaivalaigal-dev-memory-service

# Remove container
container rm ninaivalaigal-dev-memory-service

# Test health
curl http://localhost:13393/health

# Check port usage
lsof -i:13393
```

---

## 🎯 Success Criteria

Your services are correctly set up when:
- ✅ Container names follow `ninaivalaigal-dev-{service}` pattern
- ✅ Ports are 13393 (memory) and 13394 (graph)
- ✅ Scripts follow `nv-{service}-{action}.sh` pattern
- ✅ Database connects via PgBouncer (dynamic IP, port 6432)
- ✅ JWT authentication works with Core API tokens
- ✅ Health checks respond on `/health`
- ✅ Services can be started with `./nv-{service}-start.sh`

---

**Questions?** Check with Developer C or refer to:
- `services/core-api/nv-core-api-start.sh` (working example)
- `config/ports.nv.yaml` (canonical port matrix)
- `services/MICROSERVICES_PORT_ALLOCATION.md` (port plan)

Good luck with the Rust services! 🦀🚀
