# Database Container - Apple Container CLI
**PostgreSQL 15 with Apache AGE + pgvector extensions**

---

## Container Information

- **Name**: `ninaivalaigal-dev-db`
- **Image**: `nina-intelligence-db:arm64`
- **Base**: `postgres:15`
- **Architecture**: ARM64
- **Port Mapping**: `5452:5432` (dev)
- **Extensions**: Apache AGE 1.5.0, pgvector 0.8.1

---

## Prerequisites

### Files Required
```bash
/Users/swami/WorkSpace/ninaivalaigal/scripts/consolidation/
├── Dockerfile.nv-db-age       # Build definition
├── init-age.sql               # AGE initialization
└── restore-data.sql           # Data restoration (if any)
```

### Tools Required
```bash
# Docker (for building if Apple Container CLI has DNS issues)
docker --version

# jq (for JSON parsing)
brew install jq

# PostgreSQL client (for testing)
brew install postgresql@15
```

---

## Build Process

### Method 1: Apple Container CLI (Preferred)

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/scripts/consolidation

# Build (2-3 minutes)
container build --no-cache -t nina-intelligence-db:arm64 -f Dockerfile.nv-db-age .

# Verify image
container image list | grep nina-intelligence-db
```

### Method 2: Docker Build + Transfer (Fallback)

**Use when**: Apple Container CLI has DNS resolution issues

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/scripts/consolidation

# Build with Docker (2-3 minutes)
docker build --no-cache -t nina-intelligence-db:arm64 -f Dockerfile.nv-db-age .

# Verify build
docker run --rm nina-intelligence-db:arm64 psql --version
docker run --rm nina-intelligence-db:arm64 ls /usr/lib/postgresql/15/lib/ | grep -E 'age|vector'

# Transfer to Apple Container CLI
docker save nina-intelligence-db:arm64 -o /tmp/nina-db-$(date +%Y%m%d-%H%M%S).tar
container image load --input /tmp/nina-db-*.tar

# Verify in Apple Container CLI
container image list | grep nina-intelligence-db
```

---

## Dockerfile

**Location**: `/Users/swami/WorkSpace/ninaivalaigal/scripts/consolidation/Dockerfile.nv-db-age`

```dockerfile
# PostgreSQL 15 with Apache AGE extension
FROM postgres:15

# Install dependencies for Apache AGE
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-server-dev-15 \
    git \
    flex \
    bison \
    && rm -rf /var/lib/apt/lists/*

# Clone and build Apache AGE
RUN git clone https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && git checkout PG15 \
    && make install \
    && rm -rf /tmp/age

# Install pgvector extension
RUN apt-get update && apt-get install -y postgresql-15-pgvector && rm -rf /var/lib/apt/lists/*

# Copy initialization scripts
COPY init-age.sql /docker-entrypoint-initdb.d/01-init-age.sql
COPY restore-data.sql /docker-entrypoint-initdb.d/02-restore-data.sql

# Set environment variables
ENV POSTGRES_DB=nina
ENV POSTGRES_USER=nina
ENV POSTGRES_PASSWORD=change_me_securely
```

**Key Points**:
- ✅ Branch is `PG15` (not `PG15/stable`)
- ✅ Both AGE and pgvector installed
- ✅ Init scripts run automatically on first startup

---

## Runtime Configuration

### Start Container

```bash
container run -d --name ninaivalaigal-dev-db \
  -p 5452:5432 \
  -e POSTGRES_DB=nina \
  -e POSTGRES_USER=nina \
  -e POSTGRES_PASSWORD=change_me_securely \  # pragma: allowlist secret
  nina-intelligence-db:arm64

# Wait for initialization (15-20 seconds)
sleep 15
```

### With Volume (Recommended for Data Persistence)

```bash
container run -d --name ninaivalaigal-dev-db \
  -p 5452:5432 \
  -e POSTGRES_DB=nina \
  -e POSTGRES_USER=nina \
  -e POSTGRES_PASSWORD=change_me_securely \  # pragma: allowlist secret
  -v ninaivalaigal_dev_db_data:/var/lib/postgresql/data \
  nina-intelligence-db:arm64
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | Yes | `nina` | Database name |
| `POSTGRES_USER` | Yes | `nina` | Database user |
| `POSTGRES_PASSWORD` | Yes | - | Database password (CHANGE IN PROD) |
| `POSTGRES_INITDB_ARGS` | No | - | Additional initdb arguments |

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-db
```

### Check Logs
```bash
# View all logs
container logs ninaivalaigal-dev-db

# Check for initialization completion
container logs ninaivalaigal-dev-db | grep "database system is ready to accept connections"

# Check for extension installation
container logs ninaivalaigal-dev-db | grep -E "age|vector"
```

### Test Database Connection
```bash
# From host
psql "postgresql://nina:change_me_securely@localhost:5452/nina" -c "SELECT version();"  # pragma: allowlist secret

# From container
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "SELECT version();"
```

### Verify Extensions
```bash
# Check installed extensions
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "\dx"

# Expected output:
#   Name   | Version |   Schema   |         Description
# ---------+---------+------------+------------------------------
#  age     | 1.5.0   | ag_catalog | AGE database extension
#  plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
#  vector  | 0.8.1   | public     | vector data type...
```

### Test AGE Graph Operations
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina <<EOF
LOAD 'age';
SET search_path = ag_catalog, "\$user", public;
SELECT * FROM ag_graph WHERE name = 'ninaivalaigal_intelligence';
EOF
```

### Test pgvector Operations
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  CREATE TABLE IF NOT EXISTS test_vectors (
    id serial PRIMARY KEY,
    embedding vector(3)
  );
  INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]');
  SELECT * FROM test_vectors;
  DROP TABLE test_vectors;
"
```

---

## Get Container IP

```bash
# Get IP for PgBouncer/API configuration
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Database IP: $DB_IP"

# Test connectivity from another container
container run --rm pgvector/pgvector:pg15 \
  psql "postgresql://nina:change_me_securely@${DB_IP}:5432/nina" -c "SELECT 1;"  # pragma: allowlist secret
```

---

## Data Management

### Backup Database
```bash
# SQL dump
container exec ninaivalaigal-dev-db \
  pg_dump -U nina -d nina > backup-$(date +%Y%m%d-%H%M%S).sql

# With compression
container exec ninaivalaigal-dev-db \
  pg_dump -U nina -d nina | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz
```

### Restore Database
```bash
# From SQL file
container exec -i ninaivalaigal-dev-db \
  psql -U nina -d nina < backup.sql

# From compressed file
gunzip -c backup.sql.gz | container exec -i ninaivalaigal-dev-db \
  psql -U nina -d nina
```

### Export Container
```bash
# Export entire container filesystem
container export ninaivalaigal-dev-db > db-container-$(date +%Y%m%d-%H%M%S).tar
```

---

## Maintenance

### View Active Connections
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  SELECT pid, usename, application_name, client_addr, state
  FROM pg_stat_activity
  WHERE datname = 'nina';
"
```

### Database Size
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  SELECT pg_size_pretty(pg_database_size('nina'));
"
```

### Table Sizes
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  SELECT schemaname, tablename,
         pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  LIMIT 10;
"
```

### Vacuum and Analyze
```bash
# Vacuum
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "VACUUM VERBOSE;"

# Analyze
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "ANALYZE VERBOSE;"

# Full vacuum (requires exclusive lock)
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "VACUUM FULL VERBOSE;"
```

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
container logs ninaivalaigal-dev-db
```

**Common issues**:
1. **Port conflict**: Another service using 5452
   ```bash
   lsof -i :5452
   # Kill conflicting process or use different port
   ```

2. **Volume permission issues**:
   ```bash
   container delete ninaivalaigal-dev-db
   # Remove volume and start fresh
   container run -d --name ninaivalaigal-dev-db ... # without -v
   ```

3. **Initialization script failures**:
   ```bash
   container logs ninaivalaigal-dev-db | grep ERROR
   # Fix init-age.sql or restore-data.sql
   ```

### Extensions Not Installed

**Check logs for errors**:
```bash
container logs ninaivalaigal-dev-db | grep -E "age|vector|ERROR"
```

**Manually install extensions**:
```bash
# AGE
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "CREATE EXTENSION IF NOT EXISTS age;"

# pgvector
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Connection Refused

**Check if running**:
```bash
container list | grep ninaivalaigal-dev-db
```

**Check if port is listening**:
```bash
container exec ninaivalaigal-dev-db netstat -tuln | grep 5432
```

**Test from host**:
```bash
psql "postgresql://nina:change_me_securely@localhost:5452/nina" -c "SELECT 1;"  # pragma: allowlist secret
```

### Slow Queries

**Enable query logging**:
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
  SELECT pg_reload_conf();
"
```

**View slow queries**:
```bash
container logs ninaivalaigal-dev-db | grep "duration:"
```

---

## Performance Tuning

### Recommended Settings (Development)

```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina <<EOF
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET max_connections = 100;
SELECT pg_reload_conf();
EOF
```

### For Production
```bash
# Adjust based on available RAM
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET max_connections = 200;
```

---

## Security

### Change Password
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "
  ALTER USER nina WITH PASSWORD 'new_secure_password';  -- pragma: allowlist secret
"

# Update PgBouncer userlist with new SCRAM hash
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')
echo "\"nina\" \"${SCRAM_PASSWORD}\"" > /tmp/userlist.txt
```

### Create Read-Only User
```bash
container exec ninaivalaigal-dev-db psql -U nina -d nina <<EOF
CREATE USER readonly WITH PASSWORD 'readonly_password';  -- pragma: allowlist secret
GRANT CONNECT ON DATABASE nina TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
EOF
```

---

## Clean Up

### Stop and Remove Container
```bash
container stop ninaivalaigal-dev-db
container delete ninaivalaigal-dev-db
```

### Remove Image
```bash
container image rm nina-intelligence-db:arm64
```

### Remove Volume
```bash
# List volumes
container volume list

# Remove specific volume
container volume rm ninaivalaigal_dev_db_data
```

---

## Build Time Breakdown

1. **Base image pull**: 30 seconds (cached after first time)
2. **Install build dependencies**: 30-45 seconds
3. **Clone and build Apache AGE**: 60-90 seconds
4. **Install pgvector**: 15-20 seconds
5. **Copy init scripts**: <1 second

**Total**: 2-3 minutes for fresh build

---

## Common Errors and Solutions

### Error: DNS resolution failure during build
```
Error: Temporary failure resolving 'apt.postgresql.org'
```
**Solution**: Use Docker build + transfer method (Method 2 above)

### Error: AGE branch not found
```
error: pathspec 'PG15/stable' did not match any file(s)
```
**Solution**: Already fixed in Dockerfile - uses `PG15` branch

### Error: Container exits immediately
```
container list --all | grep ninaivalaigal-dev-db
# Shows "Exited"
```
**Solution**: Check logs for initialization errors
```bash
container logs ninaivalaigal-dev-db
```

### Error: Extension not available
```
ERROR: could not open extension control file
```
**Solution**: Rebuild image with --no-cache

---

## Next Steps

1. ✅ Database built and running
2. → Verify extensions installed
3. → Configure PgBouncer (see [03-pgbouncer.md](./03-pgbouncer.md))
4. → Connect API to database (see [04-api.md](./04-api.md))

---

## Quick Reference

```bash
# Build
container build --no-cache -t nina-intelligence-db:arm64 -f scripts/consolidation/Dockerfile.nv-db-age scripts/consolidation/

# Run
container run -d --name ninaivalaigal-dev-db -p 5452:5432 \
  -e POSTGRES_DB=nina -e POSTGRES_USER=nina -e POSTGRES_PASSWORD=change_me_securely \  # pragma: allowlist secret
  nina-intelligence-db:arm64

# Verify
container exec ninaivalaigal-dev-db psql -U nina -d nina -c "\dx"

# Get IP
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Backup
container exec ninaivalaigal-dev-db pg_dump -U nina -d nina > backup.sql
```
