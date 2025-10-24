# Dual PgBouncer Quick Start Guide

**Task #85 - Revised Architecture**
**Date:** October 20, 2025
**Status:** ✅ Ready for Implementation

---

## 🎯 What is Dual PgBouncer?

Two separate PgBouncer instances optimized for different workload types:

| Instance | Mode | Port | For | Performance |
|----------|------|------|-----|-------------|
| **pgbouncer-tx** | transaction | 6432 | Core API, GraphOps, REST | ⚡ Fastest |
| **pgbouncer-sess** | session | 6433 | Memory Service (Rust/SQLx) | 🔧 Prepared Statements |

---

## 📋 Prerequisites

1. **PostgreSQL running:**
   ```bash
   container list | grep db
   # Should show: ninaivalaigal-dev-db
   ```

2. **Environment configured:**
   ```bash
   ls -la .env.dev
   # Should exist with DB credentials
   ```

3. **PgBouncer image built:**
   ```bash
   cd containers/pgbouncer
   docker build --platform linux/arm64 -t nina-pgbouncer:latest .
   docker save nina-pgbouncer:latest -o /tmp/pgbouncer.tar
   container image load -i /tmp/pgbouncer.tar
   ```

---

## 🚀 Starting Dual PgBouncer

### **Step 1: Start Transaction Mode (for Core API, GraphOps)**

```bash
./scripts/nv-pgbouncer-tx-start.sh
```

**Expected output:**
```
🚀 Starting PgBouncer - TRANSACTION Mode
========================================
Purpose: High-throughput stateless services
Port: 6432
...
✅ PgBouncer-TX Started Successfully
```

**Verify:**
```bash
container list | grep pgbouncer-tx
# Should show: ninaivalaigal-dev-pgbouncer-tx running on 192.168.x.x
```

### **Step 2: Start Session Mode (for Memory Service)**

```bash
./scripts/nv-pgbouncer-sess-start.sh
```

**Expected output:**
```
🚀 Starting PgBouncer - SESSION Mode
====================================
Purpose: Prepared statements (Rust/SQLx)
Port: 6433
...
✅ PgBouncer-SESS Started Successfully
```

**Verify:**
```bash
container list | grep pgbouncer-sess
# Should show: ninaivalaigal-dev-pgbouncer-sess running on 192.168.x.x
```

---

## ✅ Verification Tests

### **Test Transaction Mode (Port 6432)**

```bash
# Test connection
psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# Check pool stats
psql -h localhost -p 6432 -U nina -d pgbouncer -c "SHOW POOLS;"

# Expected: pool_mode = transaction
```

### **Test Session Mode (Port 6433)**

```bash
# Test connection
psql -h localhost -p 6433 -U nina -d ninaivalaigal_dev -c "SELECT 1;"

# Check pool stats
psql -h localhost -p 6433 -U nina -d pgbouncer -c "SHOW POOLS;"

# Expected: pool_mode = session
```

### **Test Prepared Statements (Session Mode Only)**

```bash
# This should ONLY work on port 6433 (session mode)
psql -h localhost -p 6433 -U nina -d ninaivalaigal_dev << 'EOF'
PREPARE test_stmt AS SELECT $1::integer AS value;
EXECUTE test_stmt(42);
DEALLOCATE test_stmt;
EOF

# Expected: Returns value = 42

# This should FAIL on port 6432 (transaction mode)
psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev << 'EOF'
PREPARE test_stmt AS SELECT $1::integer AS value;
EXECUTE test_stmt(42);
EOF
# Expected: ERROR: prepared statements not supported in transaction mode
```

---

## 🔧 Service Connection Routing

### **Core API (Future - Python FastAPI)**

**Use Transaction Mode (port 6432):**
```bash
DATABASE_URL=postgresql://nina:$PASS@localhost:6432/ninaivalaigal_dev
```

**Why:** Stateless REST endpoints, no prepared statements needed, fastest performance

---

### **Memory Service (Rust/SQLx)**

**Use Session Mode (port 6433):**
```bash
DATABASE_URL=postgresql://nina:$PASS@localhost:6433/ninaivalaigal_dev
```

**Why:** SQLx requires prepared statements, needs session state

**Start script updated:**
```bash
./rust-services/memory-service/nv-memory-service-start.sh
# Automatically connects to pgbouncer-sess (port 6433)
```

---

### **GraphOps (Cypher Queries)**

**Use Transaction Mode (port 6432):**
```bash
DATABASE_URL=postgresql://nina:$PASS@localhost:6432/ninaivalaigal_dev
```

**Why:** Stateless graph queries, optimal for transaction mode

---

## 📊 Monitoring Both Pools

### **Monitor Transaction Pool:**
```bash
# Stats
psql -h localhost -p 6432 -U nina -d pgbouncer -c "SHOW POOLS;"
psql -h localhost -p 6432 -U nina -d pgbouncer -c "SHOW STATS;"

# Logs
container logs -f ninaivalaigal-dev-pgbouncer-tx
```

### **Monitor Session Pool:**
```bash
# Stats
psql -h localhost -p 6433 -U nina -d pgbouncer -c "SHOW POOLS;"
psql -h localhost -p 6433 -U nina -d pgbouncer -c "SHOW STATS;"

# Logs
container logs -f ninaivalaigal-dev-pgbouncer-sess
```

---

## 🛑 Stopping Both Instances

### **Stop Transaction Mode:**
```bash
container stop ninaivalaigal-dev-pgbouncer-tx
container rm ninaivalaigal-dev-pgbouncer-tx
```

### **Stop Session Mode:**
```bash
container stop ninaivalaigal-dev-pgbouncer-sess
container rm ninaivalaigal-dev-pgbouncer-sess
```

### **Stop Both (Quick):**
```bash
container stop ninaivalaigal-dev-pgbouncer-tx ninaivalaigal-dev-pgbouncer-sess
container rm ninaivalaigal-dev-pgbouncer-tx ninaivalaigal-dev-pgbouncer-sess
```

---

## 🐛 Troubleshooting

### **Problem: Container won't start**

**Check database is running:**
```bash
container list | grep db
```

**Check logs:**
```bash
container logs ninaivalaigal-dev-pgbouncer-tx
container logs ninaivalaigal-dev-pgbouncer-sess
```

**Common issues:**
- Database container not found → Start database first
- Port already in use → Stop existing PgBouncer
- Invalid credentials → Check .env.dev

---

### **Problem: Can't connect to PgBouncer**

**Test connectivity:**
```bash
# Test TX mode
nc -zv localhost 6432

# Test SESS mode
nc -zv localhost 6433
```

**Check container IP:**
```bash
container inspect ninaivalaigal-dev-pgbouncer-tx | jq -r '.[0].networks[0].address'
container inspect ninaivalaigal-dev-pgbouncer-sess | jq -r '.[0].networks[0].address'
```

---

### **Problem: Wrong pool mode being used**

**Verify pool mode:**
```bash
# Check TX mode (should be transaction)
psql -h localhost -p 6432 -U nina -d pgbouncer -c "SHOW CONFIG;" | grep pool_mode

# Check SESS mode (should be session)
psql -h localhost -p 6433 -U nina -d pgbouncer -c "SHOW CONFIG;" | grep pool_mode
```

**Fix:** Rebuild PgBouncer image and restart containers

---

## 📈 Performance Expectations

### **Transaction Mode (Port 6432):**
- **Latency:** ~2ms overhead
- **Throughput:** 10,000+ req/sec
- **Memory:** Low (minimal state)
- **Use case:** REST APIs, GraphQL, stateless queries

### **Session Mode (Port 6433):**
- **Latency:** ~5ms overhead
- **Throughput:** 5,000+ req/sec
- **Memory:** Higher (maintains session state)
- **Use case:** Rust/SQLx, prepared statements, ORMs

### **Combined System:**
- **30%+ throughput improvement** vs single session mode
- **Clean separation** between workload types
- **Optimal performance** for each service

---

## ✅ Success Criteria

- [ ] Both PgBouncer containers running
- [ ] Transaction mode verified on port 6432
- [ ] Session mode verified on port 6433
- [ ] Memory Service connects to port 6433
- [ ] Prepared statements work on port 6433
- [ ] Prepared statements fail on port 6432 (expected)
- [ ] Connection pool stats visible for both
- [ ] Services route to correct pool

---

## 📚 Additional Resources

- **Task #85 Implementation:** `docs/TASK_85_IMPLEMENTATION_PLAN.md`
- **Revised Architecture:** `docs/TASK_85_REVISED_DUAL_PGBOUNCER.md`
- **PgBouncer Dockerfile:** `containers/pgbouncer/Dockerfile`
- **Environment Config:** `.env.dev`

---

**Questions?** Check logs or ask Developer X/Developer A.

**Status:** ✅ Ready for testing (rebuild image first)
