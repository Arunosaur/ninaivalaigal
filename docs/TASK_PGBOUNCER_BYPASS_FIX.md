# Task: Fix PgBouncer Bypass in Memory Service

**Priority:** HIGH (before production scaling)
**Status:** Pending
**Created:** October 20, 2025
**Related:** rust-services/memory-service/TECH_DEBT.md

---

## 🚨 Problem

The Rust Memory Service currently **bypasses PgBouncer** and connects directly to PostgreSQL. This is a **documented short-term workaround** that will cause connection exhaustion at scale.

### Current Connection Path
```
Memory Service → PostgreSQL:5432  ❌ Direct (bypassing PgBouncer)
```

### Why It's a Problem
```
SQLx (Rust) uses prepared statements by default
PgBouncer (transaction mode) doesn't support prepared statements
Result: Connection directly to PostgreSQL, bypassing connection pooler
```

### Scaling Impact
| Instances | DB Connections | Status |
|-----------|----------------|--------|
| 1-2       | 8-16           | ✅ SAFE (current) |
| 3-5       | 24-40          | ⚠️ MONITOR |
| 10+       | 80+            | ❌ REQUIRES FIX |

PostgreSQL max_connections = 200. With 10 Memory Service instances = 80 connections, leaving only 120 for all other services.

---

## 🎯 Proposed Solution

### Option 1: PgBouncer Session Mode ⭐ RECOMMENDED

**Change PgBouncer from transaction mode to session mode:**

```ini
# pgbouncer.ini
[databases]
ninaivalaigal_dev = host=ninaivalaigal-dev-db port=5432 dbname=ninaivalaigal_dev

[pgbouncer]
pool_mode = session  # Changed from 'transaction' to 'session'
max_client_conn = 1000
default_pool_size = 50
```

**Pros:**
- ✅ Supports prepared statements
- ✅ SQLx works without changes
- ✅ Central connection management
- ✅ Better connection pooling

**Cons:**
- ⚠️ Slightly less efficient than transaction mode
- ⚠️ Connection held for entire session (not just transaction)

### Option 2: Disable Prepared Statements in SQLx

**Configure SQLx to not use prepared statements:**

```rust
// src/storage.rs
let pool = PgPoolOptions::new()
    .max_connections(8)
    .after_connect(|conn, _meta| {
        Box::pin(async move {
            conn.execute("SET statement_timeout = '30s'").await?;
            Ok(())
        })
    })
    .connect_with(
        options.application_name("memory-service")
               .statement_cache_capacity(0)  // Disable prepared statements
    )
    .await?;
```

**Pros:**
- ✅ Works with PgBouncer transaction mode
- ✅ Efficient connection pooling

**Cons:**
- ⚠️ Slightly slower queries (no prepared statement caching)
- ⚠️ Requires code changes

### Option 3: Use Supavisor (Modern Alternative)

**Replace PgBouncer with Supavisor** (supports prepared statements in transaction mode):

```yaml
# docker-compose addition
supavisor:
  image: supabase/supavisor:latest
  ports:
    - "6432:6432"
  environment:
    DATABASE_URL: postgresql://postgres:password@db:5432/postgres  # pragma: allowlist secret
```

**Pros:**
- ✅ Supports prepared statements in transaction mode
- ✅ Modern, actively developed
- ✅ Better observability

**Cons:**
- ⚠️ New dependency to learn/maintain
- ⚠️ Migration effort

---

## 📋 Implementation Plan

### Phase 1: Testing (Week 1)
- [ ] Test Option 1 (PgBouncer session mode) in development
- [ ] Verify Memory Service connects successfully
- [ ] Run benchmark tests to measure performance impact
- [ ] Compare connection usage vs current approach

### Phase 2: Implementation (Week 2)
- [ ] Update PgBouncer configuration
- [ ] Update Memory Service to use PgBouncer
- [ ] Add connection pooling metrics to health endpoint
- [ ] Update documentation

### Phase 3: Validation (Week 3)
- [ ] Load test with 5-10 service instances
- [ ] Verify connection count stays reasonable
- [ ] Monitor for "prepared statement" errors
- [ ] Performance regression testing

### Phase 4: Production (Week 4)
- [ ] Deploy to staging environment
- [ ] Run 48-hour soak test
- [ ] Monitor connection metrics
- [ ] Deploy to production

---

## 🔍 Success Criteria

- ✅ Memory Service connects through PgBouncer (not direct)
- ✅ No "prepared statement already exists" errors
- ✅ 10+ instances use < 100 total DB connections
- ✅ Query performance within 10% of current baseline
- ✅ Connection acquisition < 50ms P99

---

## 📊 Current Status

```json
GET http://localhost:13393/health
{
  "database": {
    "connection_mode": "direct_postgresql",
    "connection_strategy": "short_term_workaround",  ← MUST FIX
    "connections_active": 0,
    "connections_idle": 2,
    "connections_total": 2,
    "connections_max": 8
  }
}
```

**Expected After Fix:**
```json
{
  "database": {
    "connection_mode": "pgbouncer_pooled",
    "connection_strategy": "production_ready",
    "connections_active": 0,
    "connections_idle": 2,
    "connections_total": 2,
    "connections_max": 50
  }
}
```

---

## 🔗 Related Files

- `rust-services/memory-service/TECH_DEBT.md` - Original documentation
- `rust-services/memory-service/src/storage.rs` - Connection code
- `containers/pgbouncer/pgbouncer.ini` - PgBouncer config
- `scripts/nv-pgbouncer-start.sh` - PgBouncer startup script

---

## 📝 Notes

This is **documented technical debt** that is **safe for development** (1-2 instances) but **must be fixed before production scaling** (10+ instances).

The workaround was intentionally implemented to unblock development while we researched the best long-term solution. The recommendation is **Option 1: PgBouncer Session Mode** as it requires minimal code changes and provides the best balance of simplicity and performance.

---

**Recommended Owner:** Rust team member familiar with SQLx and database connection pooling
**Estimated Effort:** 2-3 weeks (including testing and validation)
**Risk Level:** Medium (requires careful testing to avoid production issues)
