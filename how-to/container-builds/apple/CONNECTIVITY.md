# Apple Container CLI - Container Connectivity
**How containers communicate with each other**

---

## Network Architecture

### Overview
```
┌─────────────────────────────────────────────────────────┐
│ Host (Mac)                                              │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │ Apple Container CLI Network                     │   │
│  │                                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐   │   │
│  │  │ Database │  │  Redis   │  │ PgBouncer  │   │   │
│  │  │192.168.x │  │192.168.x │  │192.168.x   │   │   │
│  │  └─────┬────┘  └─────┬────┘  └──────┬─────┘   │   │
│  │        │             │               │         │   │
│  │        └─────────────┴───────────────┘         │   │
│  │                      │                         │   │
│  │                ┌─────┴─────┐                   │   │
│  │                │    API    │                   │   │
│  │                │192.168.x  │                   │   │
│  │                └─────┬─────┘                   │   │
│  └──────────────────────┼─────────────────────────┘   │
│                         │                             │
│            ┌────────────┴────────────┐                │
│            │   Port Mappings         │                │
│            │   5452 → DB:5432        │                │
│            │   6389 → Redis:6379     │                │
│            │   6452 → PgB:6432       │                │
│            │   13390 → API:8000      │                │
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
```bash
# Standard command (use this)
container inspect {name} | jq -r '.[0].networks[0].address' | cut -d'/' -f1

# Examples
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
```

### Typical IP Range
```
192.168.64.x where x is dynamically assigned
192.168.65.x (alternative range)
```

### IP Persistence
- **Not guaranteed**: IPs may change on container restart
- **Always query**: Don't hardcode IPs
- **Get fresh**: Query IP before each connection

---

## Container-to-Container Communication

### Critical Rule
❌ **NEVER use hostnames**
✅ **ALWAYS use IP addresses**

```bash
# ❌ Wrong - Will fail
DATABASE_URL="postgresql://nina:password@ninaivalaigal-dev-db:5432/nina"  # pragma: allowlist secret
REDIS_URL="redis://ninaivalaigal-dev-redis:6379/0"

# ✅ Correct - Will work
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret

REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_URL="redis://:password@${REDIS_IP}:6379/0"
```

### Why Hostnames Don't Work
- Apple Container CLI doesn't provide built-in DNS resolution
- Container names are not automatically added to /etc/hosts
- No service discovery like Docker Compose

---

## Connection Patterns

### API → Database (via PgBouncer)

**Pattern**: API → PgBouncer → Database

```bash
# 1. Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# 2. Configure API
container run -d --name ninaivalaigal-dev-api \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  nina-api:arm64
```

**Connection String Format**:
```
postgresql://{user}:{password}@{pgbouncer_ip}:{pgbouncer_port}/{database}  # pragma: allowlist secret
```

### API → Redis

**Pattern**: API → Redis (direct)

```bash
# 1. Get Redis IP
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# 2. Configure API
container run -d --name ninaivalaigal-dev-api \
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  nina-api:arm64
```

**Connection String Format**:
```
redis://:{password}@{redis_ip}:6379/{db_number}
```

**Note**: The `:` before password is intentional (no username)

### PgBouncer → Database

**Pattern**: PgBouncer → Database (connection pool)

```bash
# 1. Get Database IP
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# 2. Create PgBouncer config
cat > /tmp/pgbouncer.ini <<EOF
[databases]
nina = host=${DB_IP} port=5432 dbname=nina

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
EOF

# 3. Start PgBouncer
container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -v /tmp/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini \
  nina-pgbouncer:arm64
```

### Workers → Database/Redis

**Pattern**: Same as API

```bash
# Get IPs
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start workers
container run -d --name ninaivalaigal-dev-workers \
  -e DATABASE_URL="postgresql://nina:password@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:password@${REDIS_IP}:6379/0" \
  nina-workers:arm64
```

---

## Port Mappings

### Development Ports (Host → Container)

```bash
# Database
container run -p 5452:5432 ninaivalaigal-dev-db
# Access from host: localhost:5452
# Access from containers: ${DB_IP}:5432

# Redis
container run -p 6389:6379 ninaivalaigal-dev-redis
# Access from host: localhost:6389
# Access from containers: ${REDIS_IP}:6379

# PgBouncer
container run -p 6452:6432 ninaivalaigal-dev-pgbouncer
# Access from host: localhost:6452
# Access from containers: ${PGB_IP}:6432

# API
container run -p 13390:8000 ninaivalaigal-dev-api
# Access from host: localhost:13390
# API uses container IPs to reach DB/Redis
```

### Why Different Ports?
- **Host ports (+20 offset)**: Avoid conflicts with production/other instances
- **Container ports (standard)**: Keep consistent for application code
- **Containers communicate via container ports**, not host ports

---

## Connection Verification

### Test Database Connection
```bash
# From host
psql "postgresql://nina:change_me_securely@localhost:5452/nina" -c "SELECT 1;"  # pragma: allowlist secret

# From PgBouncer
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
container run --rm pgvector/pgvector:pg15 \
  psql "postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" -c "SELECT 1;"  # pragma: allowlist secret

# From API container
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
container exec ninaivalaigal-dev-api \
  python -c "import psycopg2; conn = psycopg2.connect('postgresql://nina:password@${DB_IP}:5432/nina'); print('OK')"  # pragma: allowlist secret
```

### Test Redis Connection
```bash
# From host
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ping

# From container
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
container run --rm redis:7-alpine redis-cli -h ${REDIS_IP} -a nina_redis_dev_password ping
```

### Test API Connectivity
```bash
# Health check
curl http://localhost:13390/health

# Database through API
curl http://localhost:13390/api/health/database

# Redis through API
curl http://localhost:13390/api/health/redis
```

---

## Environment Variable Patterns

### Database Connection
```bash
# Direct to database
DATABASE_URL="postgresql://nina:password@${DB_IP}:5432/nina"  # pragma: allowlist secret

# Through PgBouncer (recommended)
DATABASE_URL="postgresql://nina:password@${PGB_IP}:6432/nina"  # pragma: allowlist secret

# Both (for flexibility)
NINAIVALAIGAL_DATABASE_URL="postgresql://nina:password@${PGB_IP}:6432/nina"  # pragma: allowlist secret
```

### Redis Connection
```bash
# With password
REDIS_URL="redis://:password@${REDIS_IP}:6379/0"

# Or separate variables
REDIS_HOST="${REDIS_IP}"
REDIS_PORT="6379"
REDIS_PASSWORD="password"  # pragma: allowlist secret
REDIS_DB="0"
```

### Full API Configuration
```bash
# Get all IPs
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start API
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
  -e ENVIRONMENT="dev" \
  -e LOG_LEVEL="debug" \
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64
```

---

## Startup Script Template

### Complete Stack Startup
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting Nina Intelligence Stack ==="

# 1. Database
echo "Starting database..."
container run -d --name ninaivalaigal-dev-db \
  -p 5452:5432 \
  -e POSTGRES_DB=nina \
  -e POSTGRES_USER=nina \
  -e POSTGRES_PASSWORD=change_me_securely \  # pragma: allowlist secret
  nina-intelligence-db:arm64

sleep 15
echo "Database ready"

# 2. Redis
echo "Starting Redis..."
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server \
  --requirepass nina_redis_dev_password \  # pragma: allowlist secret
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru

sleep 3
echo "Redis ready"

# 3. Get IPs
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "Database IP: $DB_IP"
echo "Redis IP: $REDIS_IP"

# 4. PgBouncer
echo "Starting PgBouncer..."
# Get SCRAM password from database
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')

# Create userlist
echo "\"nina\" \"${SCRAM_PASSWORD}\"" > /tmp/userlist.txt

# Create config
cat > /tmp/pgbouncer.ini <<EOF
[databases]
nina = host=${DB_IP} port=5432 dbname=nina

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
EOF

container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -v /tmp/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini \
  -v /tmp/userlist.txt:/etc/pgbouncer/userlist.txt \
  nina-pgbouncer:arm64

sleep 5
echo "PgBouncer ready"

# 5. Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "PgBouncer IP: $PGB_IP"

# 6. API
echo "Starting API..."
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \  # pragma: allowlist secret
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \  # pragma: allowlist secret
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64

sleep 10
echo "API ready"

# 7. Verification
echo ""
echo "=== Verification ==="
curl -f http://localhost:13390/health && echo "✅ API healthy"
echo ""
echo "Stack ready!"
```

---

## Troubleshooting

### Connection Refused
```bash
# Check if container is running
container list | grep {name}

# Check if port is listening
container exec {name} netstat -tuln | grep {port}

# Check firewall (unlikely on Mac)
sudo pfctl -s all
```

### Wrong IP Address
```bash
# Container IP changed after restart
# Always query fresh
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Don't cache IPs in environment files
```

### Authentication Failures
```bash
# Verify password
container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -c "SELECT 1;"

# Verify SCRAM hash
container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';"
```

### Network Isolation
```bash
# Verify containers can see each other
container exec ninaivalaigal-dev-api ping -c 3 ${DB_IP}
container exec ninaivalaigal-dev-api ping -c 3 ${REDIS_IP}
```

---

## Best Practices

1. **Always query IPs fresh** - Don't hardcode or cache
2. **Use environment variables** - Pass IPs as env vars to containers
3. **Test connections** before starting dependent services
4. **Document connection strings** in this file
5. **Use consistent patterns** across all services
6. **Verify after changes** - Test all connections after container restarts

---

## Quick Reference

```bash
# Get container IP
container inspect {name} | jq -r '.[0].networks[0].address' | cut -d'/' -f1

# PostgreSQL connection string
postgresql://{user}:{password}@{ip}:{port}/{database}  # pragma: allowlist secret

# Redis connection string
redis://:{password}@{ip}:6379/{db}

# Test database
psql "postgresql://nina:password@${DB_IP}:5432/nina" -c "SELECT 1;"  # pragma: allowlist secret

# Test Redis
redis-cli -h ${REDIS_IP} -a password ping

# Test API
curl http://localhost:13390/health
```
