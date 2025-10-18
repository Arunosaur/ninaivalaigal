# Memory Service - Technical Debt

**Last Updated**: October 17, 2025
**Priority**: HIGH
**Status**: REQUIRES ACTION BEFORE SCALING

---

## 🚨 SHORT-TERM WORKAROUND: Direct PostgreSQL Connection

### Current Implementation

```rust
// src/storage.rs
let pool = PgPoolOptions::new()
    .max_connections(8)
    .connect_with(options)  // Direct to PostgreSQL
    .await?;
```

**Connection Path**: Memory Service → PostgreSQL (port 5432)
**Status**: ⚠️ **SHORT-TERM WORKAROUND**
**Bypasses**: PgBouncer connection pooler

---

## 📋 Why This Is SHORT-TERM

### Root Cause
SQLx (Rust database library) uses **prepared statements** by default for performance. PgBouncer in **transaction mode** does NOT support prepared statements because they are tied to individual connections, not transactions.

### Error Without Workaround
```
Database(PgDatabaseError {
    code: "42P05",
    message: "prepared statement \"sqlx_s_1\" already exists"
})
```

### Current Solution
Connect directly to PostgreSQL, bypassing PgBouncer entirely.

---

## ⚠️ Scaling Limitations

### Safe Operating Range
| Instances | DB Connections | Status |
|-----------|----------------|--------|
| 1-2 | 8-16 | ✅ SAFE |
| 3-5 | 24-40 | ⚠️ MONITOR |
| 6-10 | 48-80 | ⚠️ APPROACHING LIMIT |
| 10+ | 80+ | ❌ REQUIRES FIX |

### Problems at Scale

1. **Connection Exhaustion**
   - PostgreSQL default max_connections: 200
   - 10 service instances = 80 connections just for memory service
   - Leaves only 120 for API, admin tools, backups

2. **No Central Management**
   - Each service instance manages its own connections
   - No visibility into total connection usage
   - Harder to debug connection leaks

3. **No Failover**
   - Each service connects independently
   - Manual intervention required for database failover
   - No automatic retry/circuit breaker

---

## 🎯 LONG-TERM SOLUTIONS (Pick One)

### Option 1: PgBouncer Session Mode ⭐ RECOMMENDED

**Implementation:**
```ini
# pgbouncer.ini
[pgbouncer]
pool_mode = session  # Instead of transaction
max_client_conn = 200
default_pool_size = 50
```

**Trade-offs:**
- ✅ Supports prepared statements
- ✅ Central connection management
- ⚠️ Less efficient pooling (connections held for entire session)
- ⚠️ Requires PgBouncer reconfiguration

**Effort**: Medium (2-4 hours)
**Risk**: Low
**Timeline**: Before scaling to 5+ instances

---

### Option 2: Read Replicas 🚀 BEST FOR HIGH SCALE

**Architecture:**
```
Memory Service
├─ Writes → PgBouncer (transaction mode) → Primary DB
└─ Reads → Direct Connection → Read Replica
```

**Implementation:**
```rust
pub struct MemoryStorage {
    write_pool: PgPool,  // Through PgBouncer (2 connections)
    read_pool: PgPool,   // Direct to replica (8 connections)
}
```

**Benefits:**
- ✅ Best of both worlds
- ✅ Scales horizontally
- ✅ Offloads read traffic from primary
- ✅ Memory service is read-heavy (90% reads)

**Effort**: High (1-2 days)
**Risk**: Medium
**Timeline**: Before scaling to 10+ instances

---

### Option 3: Disable Prepared Statements ❌ NOT RECOMMENDED

**Implementation:**
```rust
let options = PgConnectOptions::from_str(database_url)?
    .statement_cache_capacity(0);  // Disable prepared statements
```

**Trade-offs:**
- ✅ Works with PgBouncer transaction mode
- ❌ Performance loss (5-10% slower queries)
- ❌ Still direct connection issues
- ❌ Doesn't solve scaling problems

**Effort**: Low (30 minutes)
**Risk**: Low
**Timeline**: NOT RECOMMENDED - use Option 1 or 2 instead

---

## 📊 Monitoring Requirements

### Added in Current Release ✅

**Health Endpoint Enhanced:**
```json
GET /health
{
  "database": {
    "connections_active": 2,
    "connections_idle": 6,
    "connections_total": 8,
    "connections_max": 8,
    "connection_mode": "direct_postgresql",
    "connection_strategy": "short_term_workaround"
  }
}
```

### Required Before Scaling ⏳

1. **Prometheus Metrics**
   ```rust
   db_pool_connections_active.set(stats.active);
   db_pool_connections_idle.set(stats.idle);
   db_pool_connections_max.set(stats.max_connections);
   ```

2. **Alerting Thresholds**
   - Alert if active connections > 6 (75% capacity)
   - Alert if total instances × 8 > 50% of PostgreSQL max_connections
   - Alert on connection acquisition timeouts

3. **Grafana Dashboard**
   - Connection pool usage over time
   - Connection acquisition latency
   - Failed connection attempts

---

## 🗓️ Migration Timeline

### Phase 1: Monitoring (DONE ✅)
- [x] Add connection stats to health endpoint
- [x] Document as short-term workaround
- [x] Add monitoring recommendations

### Phase 2: Prepare for Scale (NEXT SPRINT)
- [ ] Implement Prometheus metrics
- [ ] Set up alerting thresholds
- [ ] Create Grafana dashboard
- [ ] Load test with 5 instances

### Phase 3: Long-Term Solution (BEFORE 10 INSTANCES)
- [ ] Decision: Option 1 (PgBouncer session) vs Option 2 (Read replicas)
- [ ] Implementation based on traffic patterns
- [ ] Performance testing
- [ ] Gradual rollout with monitoring

---

## 📝 Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2025-10-17 | Direct PostgreSQL connection | SQLx prepared statement incompatibility | ⚠️ SHORT-TERM |
| 2025-10-17 | Add connection monitoring | Track usage before scaling | ✅ DONE |
| TBD | Pick Option 1 or 2 | Based on traffic analysis | ⏳ PENDING |

---

## 🚦 Action Required Before Scaling

### Before 5 Instances
- [ ] Implement Prometheus metrics
- [ ] Set up connection pool monitoring
- [ ] Decide on long-term solution (Option 1 or 2)

### Before 10 Instances
- [ ] **MUST implement long-term solution**
- [ ] Load testing with target scale
- [ ] Failover testing
- [ ] Update runbooks

### Before Production
- [ ] Circuit breaker pattern for database connections
- [ ] Connection timeout handling
- [ ] Database failover automation
- [ ] Comprehensive monitoring dashboard

---

## 📚 References

- SQLx Prepared Statement Docs: https://docs.rs/sqlx/latest/sqlx/
- PgBouncer Transaction vs Session Mode: https://www.pgbouncer.org/usage.html
- PostgreSQL Connection Limits: https://www.postgresql.org/docs/current/runtime-config-connection.html

---

**Owner**: Developer A
**Reviewers**: Developer C, Tech Lead
**Next Review**: When planning to scale to 5+ instances
**Escalation**: If connection exhaustion occurs (> 80% capacity)
