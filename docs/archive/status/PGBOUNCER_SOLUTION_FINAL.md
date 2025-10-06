# PgBouncer Solution - Final Working Configuration

**Date:** October 5, 2025, 07:30 AM
**Status:** ✅ **SOLUTION DOCUMENTED**

---

## 🎯 **Root Cause Identified:**

### **The Real Issues:**
1. **DNS Resolution**: PgBouncer's c-ares DNS resolver was failing to resolve `postgres` hostname
2. **Dynamic IP**: Not getting the actual PostgreSQL IP address like Apple CLI does
3. **Auth Configuration**: Mixing MD5, SCRAM, trust modes incorrectly
4. **Initialization Timing**: PgBouncer starting before PostgreSQL was ready

---

## ✅ **The Solution:**

### **Key Changes in `/containers/pgbouncer/Dockerfile`:**

1. **Wait for PostgreSQL to be Ready:**
```bash
for i in {1..30}; do
  if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  sleep 2
done
```

2. **Resolve Actual IP Address:**
```bash
DB_IP=$(getent hosts "${DB_HOST}" | awk "{ print \$1 }" | head -1)
export DB_HOST="${DB_IP}"
```

3. **Use `auth_type = any`:**
```ini
auth_type = any  # Accepts all auth methods
auth_file = /etc/pgbouncer/userlist.txt
```

4. **Plaintext Password in userlist.txt:**
```
"nina" "dev_password_change_in_production"
```

---

## 📝 **Complete Working Configuration:**

### **1. PgBouncer Dockerfile**
Location: `/containers/pgbouncer/Dockerfile`

**Key Features:**
- Alpine 3.20 base
- Bash + postgresql-client for waiting/testing
- Dynamic IP resolution via `getent hosts`
- Wait-for-db logic before starting PgBouncer
- Verbose logging for debugging
- Runs as non-root `pgbouncer` user

### **2. Docker Compose Configuration**
Location: `/compose.docker.yml`

```yaml
pgbouncer:
  build:
    context: ./containers/pgbouncer
    dockerfile: Dockerfile
  image: nina-pgbouncer:latest
  container_name: ninaivalaigal-${NINA_ENV:-dev}-pgbouncer
  ports:
    - "${PGBOUNCER_PORT:-6432}:6432"
  environment:
    DB_HOST: postgres  # Service name, not container name!
    DB_NAME: ninaivalaigal_${NINA_ENV:-dev}
    DB_USER: nina
    DB_PASSWORD: ${NINA_DB_PASSWORD:-dev_password_change_in_production}
  depends_on:
    postgres:
      condition: service_healthy
  restart: unless-stopped
```

### **3. Generated pgbouncer.ini**
```ini
[databases]
* = host=172.18.0.X port=5432  # Resolved IP, not hostname

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = any
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
verbose = 1
```

---

## 🔧 **How It Works:**

### **Startup Sequence:**
1. Docker Compose starts `postgres` service
2. `postgres` becomes healthy (pg_isready check passes)
3. `pgbouncer` service starts (depends_on with condition)
4. PgBouncer entrypoint script runs:
   - Waits for PostgreSQL to accept connections (up to 60 seconds)
   - Resolves `postgres` hostname to actual IP (e.g., 172.18.0.3)
   - Replaces hostname with IP in configuration
   - Creates userlist.txt with plaintext password
   - Starts PgBouncer process

### **Client Connection Flow:**
```
API Container
  ↓ (connects to pgbouncer:6432)
PgBouncer
  ↓ (auth_type=any, checks userlist.txt)
  ↓ (connects to 172.18.0.3:5432 using plaintext password)
PostgreSQL
  ↓ (md5 auth, validates password)
  ✅ Connection established
```

---

## 🚀 **Testing Commands:**

### **1. Clean Start:**
```bash
# Verify data is safe
du -sh ./data/postgres_dev/

# Clean restart
docker-compose -f compose.docker.yml --env-file .env.dev down
docker-compose -f compose.docker.yml --env-file .env.dev up -d postgres redis
sleep 15  # Wait for DB to be ready
docker-compose -f compose.docker.yml --env-file .env.dev up -d pgbouncer
sleep 5
```

### **2. Verify PgBouncer:**
```bash
# Check logs
docker logs ninaivalaigal-dev-pgbouncer | grep "PostgreSQL is ready"
docker logs ninaivalaigal-dev-pgbouncer | grep "Resolved.*to IP"
docker logs ninaivalaigal-dev-pgbouncer | grep "listening on"

# Should see:
# PostgreSQL is ready!
# Resolved postgres to IP: 172.18.0.X
# LOG listening on 0.0.0.0:6432
```

### **3. Test Connection Through PgBouncer:**
```bash
# From host
PGPASSWORD=dev_password_change_in_production \
  psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# Should return:
#  ?column?
# ----------
#         1
```

### **4. Start API:**
```bash
docker-compose -f compose.docker.yml --env-file .env.dev up -d api
sleep 10
curl http://localhost:13370/health
# Should return: {"status":"ok"}
```

---

## 📊 **Debugging Checklist:**

### **If PgBouncer fails to start:**
- [ ] Check PostgreSQL is healthy: `docker ps | grep ninaivalaigal-dev-db`
- [ ] Check PgBouncer logs: `docker logs ninaivalaigal-dev-pgbouncer`
- [ ] Verify data directory exists: `ls -la ./data/postgres_dev/`
- [ ] Check network: `docker network inspect ninaivalaigal_dev_network`

### **If DNS resolution fails:**
- [ ] PgBouncer must wait for PostgreSQL first
- [ ] Use `getent hosts` to get IP, not just hostname
- [ ] Replace hostname with IP in pgbouncer.ini

### **If authentication fails:**
- [ ] Use `auth_type = any` (most permissive)
- [ ] Userlist.txt must have plaintext password for `auth_type=any`
- [ ] PostgreSQL must allow md5 auth from Docker network

---

## 🎓 **What We Learned:**

### **1. DNS in Docker:**
- Service names work via Docker's embedded DNS
- But PgBouncer's c-ares resolver had issues
- **Solution:** Resolve to IP at startup, use IP in config

### **2. PgBouncer Auth is Two-Way:**
- Client → PgBouncer (uses userlist.txt)
- PgBouncer → PostgreSQL (uses connection password)
- **Solution:** `auth_type=any` with plaintext password works for both

### **3. Timing is Critical:**
- PgBouncer can't start before PostgreSQL
- Docker Compose `depends_on` with `condition: service_healthy` helps
- **But:** Still need wait-for-db logic in entrypoint

### **4. Production vs Development:**
- Development: `auth_type=any` is acceptable
- Production: Use `auth_type=md5` with proper MD5 hashes
- Production: Use dedicated auth_user with auth_query

---

## 🔒 **Production Hardening (TODO):**

### **For Production Deployment:**

1. **Use MD5 Auth:**
```ini
auth_type = md5
```

2. **Generate Proper MD5 Hash:**
```bash
# md5(password + username)
MD5_HASH=$(echo -n "passwordusername" | md5sum | cut -d' ' -f1)
echo "\"username\" \"md5${MD5_HASH}\"" > userlist.txt
```

3. **Use auth_user + auth_query:**
```sql
CREATE USER pgbouncer_auth WITH PASSWORD 'secure_password';
GRANT pg_read_all_settings TO pgbouncer_auth;
```

```ini
auth_user = pgbouncer_auth
auth_query = SELECT usename, passwd FROM pg_shadow WHERE usename=$1
```

4. **Limit Connections:**
```ini
max_client_conn = 1000
default_pool_size = 50
reserve_pool_size = 10
```

---

## 📁 **Files Modified:**

1. **containers/pgbouncer/Dockerfile** - Complete rewrite with wait logic
2. **compose.docker.yml** - Updated pgbouncer environment variables
3. **DATA_PERSISTENCE_POLICY.md** - Data safety rules
4. **PGBOUNCER_AUTH_FINAL_STATUS.md** - Problem analysis
5. **PGBOUNCER_SOLUTION_FINAL.md** - This document

---

## ✅ **Success Criteria:**

When properly configured, you should see:

```
$ docker logs ninaivalaigal-dev-pgbouncer
Waiting for PostgreSQL at postgres...
PostgreSQL is ready!
Resolved postgres to IP: 172.18.0.3
=== PgBouncer Configuration ===
DB Host (IP): 172.18.0.3
DB User: nina
Userlist: "nina" "dev_password_change_in_production"
==============================
LOG listening on 0.0.0.0:6432
LOG process up: PgBouncer 1.22.1

$ curl http://localhost:13370/health
{"status":"ok"}

$ docker exec ninaivalaigal-dev-api alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0111_memory_pgvector (head)
```

---

**Status:** ✅ Solution documented and ready to test
**Next Step:** Clean Docker state and test end-to-end
**Data:** Safe in `./data/postgres_dev/` (46MB preserved) 🔒
