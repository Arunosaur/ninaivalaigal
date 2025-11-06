# Docker - Container Connectivity
**How containers communicate with each other in Docker**

---

## Network Architecture

### Overview
```
┌─────────────────────────────────────────────────────────┐
│ Host (macOS/Linux)                                      │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │ Docker Network (default: bridge)                │   │
│  │                                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐   │   │
│  │  │ Database │  │  Redis   │  │ PgBouncer  │   │   │
│  │  │172.17.x  │  │172.17.x  │  │172.17.x    │   │   │
│  │  └─────┬────┘  └─────┬────┘  └──────┬─────┘   │   │
│  │        │             │               │         │   │
│  │        └─────────────┴───────────────┘         │   │
│  │                      │                         │   │
│  │                ┌─────┴─────┐                   │   │
│  │                │    API    │                   │   │
│  │                │172.17.x   │                   │   │
│  │                └─────┬─────┘                   │   │
│  └──────────────────────┼─────────────────────────┘   │
│                         │                             │
│            ┌────────────┴────────────┐                │
│            │   Port Mappings         │                │
│            │   5432 → DB:5432        │                │
│            │   6379 → Redis:6379     │                │
│            │   6432 → PgB:6432       │                │
│            │   13370 → API:8000      │                │
│            └─────────────────────────┘                │
│                         │                             │
│                    localhost                          │
│                         │                             │
└─────────────────────────┼─────────────────────────────┘
                          │
                     Applications
```

---

## IP Address Management

### Getting Container IP

**Method 1: Using Docker inspect (Recommended)**
```bash
# Get container IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {name}

# Examples
DB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-db)
REDIS_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-redis)
PGB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-pgbouncer)
```

**Method 2: Using jq**
```bash
docker inspect {name} | jq -r '.[0].NetworkSettings.Networks.bridge.IPAddress'

# Examples
DB_IP=$(docker inspect ninaivalaigal-dev-db | jq -r '.[0].NetworkSettings.Networks.bridge.IPAddress')
```

### Typical IP Range
```
172.17.0.x (default bridge network)
172.18.0.x (custom networks)
```

### IP Persistence
- **Docker supports hostname resolution**: Container names work as hostnames
- **IPs may change**: On container restart, IPs may change
- **Best practice**: Use container names (Docker provides DNS)

---

## Container-to-Container Communication

### Docker DNS Resolution

**✅ Docker supports hostname resolution** (unlike Apple Container CLI)

```bash
# ✅ Correct - Use container names
DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina"  # pragma: allowlist secret
REDIS_URL="redis://:password@ninaivalaigal-dev-redis:6379/0"

# ✅ Also correct - Use IP addresses
DB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-db)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret
```

### Why Hostnames Work in Docker
- Docker provides built-in DNS resolution
- Container names are automatically added to DNS
- Works across all containers on same network
- Default bridge network supports this

---

## Connection Patterns

### API → Database (via PgBouncer)

**Pattern**: API → PgBouncer → Database

```bash
# Method 1: Using container names (recommended)
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  -e DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-pgbouncer:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-pgbouncer:6432/nina" \  # pragma: allowlist secret
  nina-core-api:arm64

# Method 2: Using IP addresses
PGB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-pgbouncer)
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  -e DATABASE_URL="postgresql://nina:password@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  nina-core-api:arm64
```

**Connection String Format**:
```
postgresql://{user}:{password}@{host}:{port}/{database}  # pragma: allowlist secret
```

### API → Redis

**Pattern**: API → Redis (direct)

```bash
# Method 1: Using container names (recommended)
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  -e REDIS_URL="redis://:password@ninaivalaigal-dev-redis:6379/0" \
  nina-core-api:arm64

# Method 2: Using IP addresses
REDIS_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-redis)
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  -e REDIS_URL="redis://:password@${REDIS_IP}:6379/0" \
  nina-core-api:arm64
```

**Connection String Format**:
```
redis://:{password}@{host}:6379/{db_number}
```

### PgBouncer → Database

**Pattern**: PgBouncer → Database (connection pool)

```bash
# Get Database IP
DB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-db)

# Configure PgBouncer
docker run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6432:6432 \
  -e DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina" \  # pragma: allowlist secret
  nina-pgbouncer:arm64
```

---

## Custom Networks

### Creating Custom Network
```bash
# Create custom network
docker network create ninaivalaigal-dev

# Run containers on custom network
docker run -d --name ninaivalaigal-dev-db \
  --network ninaivalaigal-dev \
  nina-db:arm64

docker run -d --name ninaivalaigal-dev-core-api \
  --network ninaivalaigal-dev \
  -e DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina" \  # pragma: allowlist secret
  nina-core-api:arm64
```

### Benefits of Custom Networks
- Isolated from other containers
- Better organization
- Can use network aliases
- More control over IP ranges

---

## Network Inspection

### Check Container Network
```bash
# Inspect container network settings
docker inspect ninaivalaigal-dev-db | jq '.NetworkSettings'

# List all networks
docker network ls

# Inspect specific network
docker network inspect bridge
docker network inspect ninaivalaigal-dev
```

### Check Connectivity
```bash
# Test connectivity between containers
docker exec ninaivalaigal-dev-core-api ping ninaivalaigal-dev-db
docker exec ninaivalaigal-dev-core-api curl http://ninaivalaigal-dev-db:5432

# Test from host
docker exec ninaivalaigal-dev-db pg_isready -U nina
```

---

## Port Mapping

### Host Port → Container Port
```bash
# Map host port 13370 to container port 8000
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  nina-core-api:arm64

# Access from host
curl http://localhost:13370/health

# Multiple ports
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13370:8000 \
  -p 13371:8001 \
  nina-core-api:arm64
```

### Port Allocation
**Follow `config/ports.nv.yaml`**:
- Docker dev: 13370-13375
- Docker test: 13470-13475
- Docker prod: 13570-13575

---

## Troubleshooting

### Container Can't Reach Another Container

**Check 1: Are they on same network?**
```bash
docker inspect ninaivalaigal-dev-core-api | jq '.NetworkSettings.Networks'
docker inspect ninaivalaigal-dev-db | jq '.NetworkSettings.Networks'
# Should show same network
```

**Check 2: Can resolve hostname?**
```bash
docker exec ninaivalaigal-dev-core-api ping ninaivalaigal-dev-db
# Should resolve
```

**Check 3: Is target container running?**
```bash
docker ps | grep ninaivalaigal-dev-db
```

**Check 4: Check firewall/security groups**
```bash
# Check if ports are accessible
docker exec ninaivalaigal-dev-core-api nc -zv ninaivalaigal-dev-db 5432
```

### Port Already in Use

**Error**: `bind: address already in use`

**Solution**:
```bash
# Find what's using the port
lsof -i :13370
# or
docker ps | grep 13370

# Stop the conflicting container
docker stop {container-name}

# Or use different port
docker run -d --name ninaivalaigal-dev-core-api \
  -p 13380:8000 \
  nina-core-api:arm64
```

---

## Best Practices

### Use Container Names (Recommended)
```bash
# ✅ Preferred - Docker provides DNS
DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina"  # pragma: allowlist secret
```

### Use IP Addresses (Alternative)
```bash
# ✅ Also works - More explicit
DB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ninaivalaigal-dev-db)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret
```

### Use Custom Networks for Production
```bash
# Create isolated network
docker network create ninaivalaigal-prod

# Run all containers on same network
docker run -d --network ninaivalaigal-prod ...
```

### Dynamic IP Discovery Script
```bash
#!/bin/bash
# Get container IPs dynamically
get_container_ip() {
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$1"
}

DB_IP=$(get_container_ip ninaivalaigal-dev-db)
REDIS_IP=$(get_container_ip ninaivalaigal-dev-redis)
PGB_IP=$(get_container_ip ninaivalaigal-dev-pgbouncer)

echo "DB IP: $DB_IP"
echo "Redis IP: $REDIS_IP"
echo "PgBouncer IP: $PGB_IP"
```

---

**Last Updated**: 2025-01-31
**Part of**: SPEC-145 Multi-Runtime Multi-Architecture Builds
