# PgBouncer Container - Apple Container CLI
**Connection pooler for PostgreSQL with SCRAM-SHA-256 authentication**

---

## Container Information

- **Name**: `ninaivalaigal-dev-pgbouncer`
- **Image**: `nina-pgbouncer:arm64`
- **Base**: `alpine:3.20` (recommended) or `debian:12-slim`
- **Architecture**: ARM64
- **Port Mapping**: `6452:6432` (dev)
- **Purpose**: Connection pooling, authentication, load balancing

---

## Prerequisites

### Files Required
```bash
# Alpine version (recommended)
/Users/swami/WorkSpace/ninaivalaigal/containers/pgbouncer/Dockerfile

# OR Debian version
/Users/swami/WorkSpace/ninaivalaigal/Dockerfile.pgbouncer
```

### Tools Required
```bash
# PostgreSQL client (for testing)
brew install postgresql@15

# jq (for JSON parsing)
brew install jq
```

### Dependencies
- **Database container** must be running first
- Need SCRAM password from PostgreSQL

---

## Build Process

### Method 1: Alpine (Recommended)

**Smaller image (~20MB), faster startup**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build (30-60 seconds)
container build --no-cache -t nina-pgbouncer:arm64 -f containers/pgbouncer/Dockerfile containers/pgbouncer/

# Verify
container image list | grep nina-pgbouncer
```

### Method 2: Debian

**Better compatibility if Alpine has issues**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

# Build (1-2 minutes)
container build --no-cache -t nina-pgbouncer:arm64 -f Dockerfile.pgbouncer .

# Verify
container image list | grep nina-pgbouncer
```

### Build via Docker + Transfer

```bash
# Build with Docker
docker build --no-cache -t nina-pgbouncer:arm64 -f containers/pgbouncer/Dockerfile containers/pgbouncer/

# Transfer
docker save nina-pgbouncer:arm64 -o /tmp/pgbouncer.tar
container image load --input /tmp/pgbouncer.tar
```

---

## Dockerfile (Alpine)

**Location**: `/Users/swami/WorkSpace/ninaivalaigal/containers/pgbouncer/Dockerfile`

```dockerfile
FROM alpine:3.20

# Packages: pgbouncer + certs
RUN apk add --no-cache pgbouncer ca-certificates gettext \
&& addgroup -S pgbouncer \
&& adduser -S -G pgbouncer -H -D -s /sbin/nologin pgbouncer \
&& mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer /var/lib/pgbouncer \
&& chown -R pgbouncer:pgbouncer /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer /var/lib/pgbouncer

# Create configuration templates
RUN echo '[databases]' > /etc/pgbouncer/pgbouncer.ini.template \
&& echo '* = host=${DB_HOST} port=5432 pool_mode=transaction' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo '[pgbouncer]' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'listen_addr = 0.0.0.0' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'listen_port = 6432' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'auth_type = scram-sha-256' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'auth_file = /etc/pgbouncer/userlist.txt' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'pool_mode = transaction' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'max_client_conn = 100' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'default_pool_size = 20' >> /etc/pgbouncer/pgbouncer.ini.template

# Create userlist template
RUN echo '"nina" "${SCRAM_PASSWORD}"' > /etc/pgbouncer/userlist.txt.template

USER pgbouncer
EXPOSE 6432
ENTRYPOINT ["/bin/sh","-c","envsubst < /etc/pgbouncer/pgbouncer.ini.template > /etc/pgbouncer/pgbouncer.ini && envsubst < /etc/pgbouncer/userlist.txt.template > /etc/pgbouncer/userlist.txt && exec pgbouncer /etc/pgbouncer/pgbouncer.ini"]
```

**Key Points**:
- Uses `envsubst` to template DB_HOST and SCRAM_PASSWORD
- Non-root user for security
- Transaction pool mode (recommended for most apps)

---

## Runtime Configuration

### Step 1: Get Database IP and SCRAM Password

```bash
# Get database IP
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Database IP: $DB_IP"

# Get SCRAM password from PostgreSQL
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | \
  tr -d ' ')

# Verify it's a SCRAM hash
echo "$SCRAM_PASSWORD" | grep "SCRAM-SHA-256"
# Should output the SCRAM hash
```

### Step 2: Start PgBouncer

```bash
container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -e DB_HOST="${DB_IP}" \
  -e SCRAM_PASSWORD="${SCRAM_PASSWORD}" \
  nina-pgbouncer:arm64

# Wait for startup
sleep 5
```

### Step 3: Verify Connection

```bash
# Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Test connection through PgBouncer
psql "postgresql://nina:change_me_securely@localhost:6452/nina" -c "SELECT 1;"  # pragma: allowlist secret

# Test from another container
container run --rm pgvector/pgvector:pg15 \
  psql "postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" -c "SELECT 1;"  # pragma: allowlist secret
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_HOST` | Yes | Database container IP address |
| `SCRAM_PASSWORD` | Yes | SCRAM-SHA-256 hash from PostgreSQL |

**Critical**: Must use actual SCRAM hash from PostgreSQL, cannot generate externally.

---

## Configuration

### Pool Modes

**Transaction** (Default - Recommended):
- Connection returned to pool after transaction
- Best for most web applications
- Allows session-level features

**Session**:
- Connection held for entire client session
- Required for prepared statements
- Higher connection usage

**Statement**:
- Connection returned after each statement
- Most aggressive pooling
- Breaks multi-statement transactions

### Connection Limits

**Development**:
```
max_client_conn = 100
default_pool_size = 20
```

**Production**:
```
max_client_conn = 1000
default_pool_size = 50
reserve_pool_size = 10
```

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-pgbouncer
```

### Check Logs
```bash
# View logs
container logs ninaivalaigal-dev-pgbouncer

# Should see:
# process up: PgBouncer 1.x.x
# listening on 0.0.0.0:6432
```

### Test Connection
```bash
# Direct connection (bypassing PgBouncer)
psql "postgresql://nina:change_me_securely@localhost:5452/nina" -c "SELECT 'Direct';"  # pragma: allowlist secret

# Through PgBouncer
psql "postgresql://nina:change_me_securely@localhost:6452/nina" -c "SELECT 'Via PgBouncer';"
```

### Admin Console
```bash
# Connect to admin console
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW POOLS;"

# Show active connections
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW CLIENTS;"

# Show server connections
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW SERVERS;"

# Show statistics
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW STATS;"
```

---

## Get Container IP

```bash
# For API configuration
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "PgBouncer IP: $PGB_IP"

# Connection string for API
DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina"
```

---

## Monitoring

### Connection Pool Status
```bash
container exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U postgres pgbouncer -c "SHOW POOLS;"

# Output shows:
# database | user | cl_active | cl_waiting | sv_active | sv_idle | sv_used
```

### Active Clients
```bash
container exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U postgres pgbouncer -c "SHOW CLIENTS;"
```

### Server Connections
```bash
container exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U postgres pgbouncer -c "SHOW SERVERS;"
```

### Statistics
```bash
container exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U postgres pgbouncer -c "SHOW STATS;"
```

### Configuration
```bash
container exec ninaivalaigal-dev-pgbouncer \
  psql -h localhost -p 6432 -U postgres pgbouncer -c "SHOW CONFIG;"
```

---

## Maintenance

### Reload Configuration
```bash
# If you update environment variables
container restart ninaivalaigal-dev-pgbouncer

# OR send SIGHUP
container exec ninaivalaigal-dev-pgbouncer killall -HUP pgbouncer
```

### Pause/Resume
```bash
# Pause (finish current queries, don't accept new)
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "PAUSE;"

# Resume
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "RESUME;"
```

### Kill Connections
```bash
# Kill all client connections
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "KILL nina;"

# Reconnect servers
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "RECONNECT;"
```

---

## Troubleshooting

### Authentication Failures

**Error**: `no such user`
```bash
# Check userlist.txt was created correctly
container exec ninaivalaigal-dev-pgbouncer cat /etc/pgbouncer/userlist.txt

# Should show:
# "nina" "SCRAM-SHA-256$..."
```

**Error**: `AUTH failed`
```bash
# SCRAM password is wrong or not set
# Re-extract from database
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')

# Verify it's a SCRAM hash
echo "$SCRAM_PASSWORD" | head -c 50

# Restart PgBouncer with correct password
container stop ninaivalaigal-dev-pgbouncer
container delete ninaivalaigal-dev-pgbouncer

container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -e DB_HOST="${DB_IP}" \
  -e SCRAM_PASSWORD="${SCRAM_PASSWORD}" \
  nina-pgbouncer:arm64
```

### Connection Refused

**Database not reachable**:
```bash
# Check database IP is correct
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Database IP: $DB_IP"

# Test direct connection
container exec ninaivalaigal-dev-pgbouncer ping -c 3 ${DB_IP}

# Check pgbouncer.ini
container exec ninaivalaigal-dev-pgbouncer cat /etc/pgbouncer/pgbouncer.ini | grep host
```

**Port not listening**:
```bash
# Check if PgBouncer is running
container logs ninaivalaigal-dev-pgbouncer

# Check port
container exec ninaivalaigal-dev-pgbouncer netstat -tuln | grep 6432
```

### Pool Exhaustion

**Error**: `no more connections allowed`
```bash
# Check pool status
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW POOLS;"

# Increase limits (rebuild with new config)
# max_client_conn = 200
# default_pool_size = 40
```

**Stale connections**:
```bash
# Kill and reconnect
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "KILL nina;"
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "RECONNECT;"
```

### Wrong Pool Mode

**Error**: `prepared statement "..." does not exist`
```bash
# Using transaction mode but app needs session mode
# Rebuild with pool_mode = session in Dockerfile
# Or use direct DB connection for prepared statements
```

---

## Complete Startup Script

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting PgBouncer ==="

# 1. Ensure database is running
if ! container list | grep -q ninaivalaigal-dev-db; then
  echo "Error: Database not running"
  exit 1
fi

# 2. Get database IP
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Database IP: $DB_IP"

# 3. Get SCRAM password
echo "Extracting SCRAM password from database..."
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db \
  psql -U nina -d nina -tAc \
  "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | \
  tr -d ' ')

if [ -z "$SCRAM_PASSWORD" ]; then
  echo "Error: Could not get SCRAM password"
  exit 1
fi

echo "SCRAM password obtained: ${SCRAM_PASSWORD:0:20}..."

# 4. Start PgBouncer
echo "Starting PgBouncer container..."
container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -e DB_HOST="${DB_IP}" \
  -e SCRAM_PASSWORD="${SCRAM_PASSWORD}" \
  nina-pgbouncer:arm64

# 5. Wait for startup
echo "Waiting for PgBouncer to start..."
sleep 5

# 6. Verify
echo "Testing connection..."
if psql "postgresql://nina:change_me_securely@localhost:6452/nina" -c "SELECT 1;" > /dev/null 2>&1; then
  echo "✅ PgBouncer ready"

  # Get IP for API
  PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
  echo "PgBouncer IP: $PGB_IP"
  echo "Connection string: postgresql://nina:PASSWORD@${PGB_IP}:6432/nina"  # pragma: allowlist secret
else
  echo "❌ Connection test failed"
  echo "Checking logs:"
  container logs ninaivalaigal-dev-pgbouncer
  exit 1
fi
```

---

## Integration with API

### Start API with PgBouncer

```bash
# Get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Start API
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \
  nina-api:arm64
```

### Verify API Database Connection
```bash
# Check API logs
container logs ninaivalaigal-dev-api | grep -i database

# Test API endpoint
curl http://localhost:13390/health

# Check PgBouncer stats for API connections
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW CLIENTS;" | grep nina
```

---

## Performance Tuning

### Development
```
max_client_conn = 100
default_pool_size = 20
reserve_pool_size = 5
pool_mode = transaction
```

### Production
```
max_client_conn = 1000
default_pool_size = 50
reserve_pool_size = 10
pool_mode = transaction
server_lifetime = 3600
server_idle_timeout = 600
```

---

## Security

### Non-Root User
- ✅ Runs as `pgbouncer` user
- ✅ No shell access
- ✅ Minimal permissions

### Password Security
- ✅ SCRAM-SHA-256 authentication
- ✅ Password passed as environment variable
- ✅ Not stored in image or logs

### Network Security
```bash
# Only expose to necessary containers
# Don't publish port in production if not needed externally
container run -d --name ninaivalaigal-prod-pgbouncer \
  -e DB_HOST="${DB_IP}" \
  -e SCRAM_PASSWORD="${SCRAM_PASSWORD}" \
  nina-pgbouncer:arm64
# Note: No -p flag, only accessible from other containers
```

---

## Clean Up

### Stop and Remove
```bash
container stop ninaivalaigal-dev-pgbouncer
container delete ninaivalaigal-dev-pgbouncer
```

### Remove Image
```bash
container image rm nina-pgbouncer:arm64
```

---

## Quick Reference

```bash
# Build (Alpine)
container build --no-cache -t nina-pgbouncer:arm64 -f containers/pgbouncer/Dockerfile containers/pgbouncer/

# Get prerequisites
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
SCRAM_PASSWORD=$(container exec ninaivalaigal-dev-db psql -U nina -d nina -tAc "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')

# Start
container run -d --name ninaivalaigal-dev-pgbouncer \
  -p 6452:6432 \
  -e DB_HOST="${DB_IP}" \
  -e SCRAM_PASSWORD="${SCRAM_PASSWORD}" \
  nina-pgbouncer:arm64

# Verify
psql "postgresql://nina:change_me_securely@localhost:6452/nina" -c "SELECT 1;"

# Get IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Monitor
psql "postgresql://postgres@localhost:6452/pgbouncer" -c "SHOW POOLS;"
```
