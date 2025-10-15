# Apache AGE Performance Tuning Runbook

**SPEC-099/100: Database-Side Optimization Guide**
**Purpose**: Reduce AGE query execution time from ~2ms to <0.7ms

## Quick Diagnosis

### Step 1: Measure Server Share

```sql
-- Enable statement logging (bench run only!)
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();

-- Run your benchmarks
-- Check PostgreSQL logs at /var/log/postgresql/postgresql-15-main.log

-- Query statistics
SELECT
    query,
    calls,
    mean_exec_time,
    stddev_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%cypher%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Interpretation**:
- If mean_exec_time ≥1.5ms → AGE is the bottleneck (proceed with tuning)
- If mean_exec_time <0.5ms → Network/client overhead dominates (client optimization)

### Step 2: Capture Query Plans

```sql
-- For simple match
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM cypher('ninaivalaigal_graph', $$
  MATCH (n:User)
  RETURN n
  LIMIT 10
$$) as (n agtype);

-- For graph traversal
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM cypher('ninaivalaigal_graph', $$
  MATCH (u:User)-[:CREATED]->(m:Memory)
  RETURN u.name, count(m) as memory_count
$$) as (name agtype, count agtype);
```

**Look for**:
- Planning Time >0.3ms → needs better statistics
- Execution Time >1ms → needs indexes or better plans
- Seq Scan on large tables → add indexes
- High buffer reads → increase work_mem

## Database Optimizations

### 1. Update Statistics (ALWAYS DO THIS FIRST)

```sql
-- Analyze graph tables
VACUUM (ANALYZE, VERBOSE) ag_catalog.ag_vertex;
VACUUM (ANALYZE, VERBOSE) ag_catalog.ag_edge;
VACUUM (ANALYZE, VERBOSE) ag_catalog.ag_label;

-- Increase statistics target for better plans
ALTER TABLE ag_catalog.ag_vertex
  ALTER COLUMN properties SET STATISTICS 1000;
ALTER TABLE ag_catalog.ag_edge
  ALTER COLUMN properties SET STATISTICS 1000;

-- Re-analyze
ANALYZE ag_catalog.ag_vertex;
ANALYZE ag_catalog.ag_edge;
```

**Expected Gain**: 0.2-0.4ms (better planning)

### 2. Add Critical Indexes

```sql
-- Vertex ID lookup (if not exists)
CREATE INDEX CONCURRENTLY idx_ag_vertex_id
  ON ag_catalog.ag_vertex (id);

CREATE INDEX CONCURRENTLY idx_ag_vertex_label_id
  ON ag_catalog.ag_vertex (label, id);

-- Edge relationship lookup
CREATE INDEX CONCURRENTLY idx_ag_edge_start_end
  ON ag_catalog.ag_edge (start_id, end_id);

CREATE INDEX CONCURRENTLY idx_ag_edge_label_start
  ON ag_catalog.ag_edge (label, start_id);

CREATE INDEX CONCURRENTLY idx_ag_edge_label_end
  ON ag_catalog.ag_edge (label, end_id);

-- JSONB properties (for WHERE clauses)
CREATE INDEX CONCURRENTLY idx_ag_vertex_props_gin
  ON ag_catalog.ag_vertex USING GIN (properties jsonb_path_ops);

CREATE INDEX CONCURRENTLY idx_ag_edge_props_gin
  ON ag_catalog.ag_edge USING GIN (properties jsonb_path_ops);

-- Verify indexes
\d+ ag_catalog.ag_vertex
\d+ ag_catalog.ag_edge
```

**Expected Gain**: 0.3-0.7ms (Index Scan vs Seq Scan)

### 3. Session-Level Tuning

```sql
-- Per-session for graph traversals (add to connection setup)
SET work_mem = '64MB';              -- Higher for complex joins
SET jit = off;                       -- JIT often slower for <10ms queries
SET enable_seqscan = off;           -- Test forcing index usage
SET enable_material = on;            -- Can help with graph recursion
SET from_collapse_limit = 20;        -- More aggressive join collapse
SET join_collapse_limit = 20;

-- For write-heavy workloads
SET synchronous_commit = off;       -- Faster writes (acceptable for non-critical)
```

**Test Impact**:
```bash
# Before
cargo bench --bench graphops_benchmark | grep "time:"

# After setting session params
cargo bench --bench graphops_benchmark | grep "time:"

# Compare difference
```

**Expected Gain**: 0.2-0.5ms depending on query

### 4. PostgreSQL Configuration (postgresql.conf)

```ini
# Memory
shared_buffers = 4GB                 # 25% of system RAM
effective_cache_size = 12GB          # 75% of system RAM
work_mem = 64MB                      # Per-operation (increased from 4MB)

# Query Planning
random_page_cost = 1.1               # SSD tuning (default: 4.0)
effective_io_concurrency = 200       # SSD parallelism
default_statistics_target = 500      # Better estimates

# Parallelism (if ≥4 cores)
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Connections
max_connections = 100                # Match PgBouncer pool size
```

**Apply Changes**:
```bash
sudo systemctl restart postgresql
# or
sudo pg_ctlcluster 15 main restart
```

**Expected Gain**: 0.1-0.3ms (cumulative effect)

### 5. AGE-Specific Settings

```sql
-- Enable parallel query for graph scans
SET max_parallel_workers_per_gather = 4;

-- Adjust AGE label cache (if available in your version)
-- Check AGE documentation for version-specific tunables

-- Disable unnecessary graph features if not used
-- (consult AGE docs for your version)
```

## Validation Checklist

### Before Optimization

```bash
# Capture baseline
cargo bench --bench graphops_benchmark > before.txt

# Extract metrics
grep "cypher_simple_match" before.txt
grep "cypher_graph_traversal" before.txt

# Server time
psql -U nina -d ninaivalaigal_dev -c "
  SELECT query, mean_exec_time
  FROM pg_stat_statements
  WHERE query LIKE '%cypher%';
"
```

### After Each Optimization

```bash
# Re-run benchmarks
cargo bench --bench graphops_benchmark > after.txt

# Compare
diff before.txt after.txt

# Update pg_stat_statements
psql -U nina -d ninaivalaigal_dev -c "SELECT pg_stat_statements_reset();"
cargo bench --bench graphops_benchmark
psql -U nina -d ninaivalaigal_dev -c "
  SELECT query, mean_exec_time
  FROM pg_stat_statements
  WHERE query LIKE '%cypher%';
"
```

### Success Criteria

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Planning Time | >0.5ms | <0.2ms | ⏳ |
| Execution Time | ~1.8ms | <0.7ms | ⏳ |
| Total Latency | ~2.0ms | <1.0ms | ⏳ |
| Index Hit Rate | N/A | >95% | ⏳ |

## Troubleshooting

### Indexes Not Being Used

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'ag_catalog'
ORDER BY idx_scan;

-- If idx_scan = 0, index is not used
-- Force index scan to test
SET enable_seqscan = off;
EXPLAIN (ANALYZE) SELECT * FROM cypher(...);
```

### Query Plans Still Suboptimal

```sql
-- More aggressive statistics
ALTER TABLE ag_catalog.ag_vertex
  ALTER COLUMN properties SET STATISTICS 5000;
ANALYZE ag_catalog.ag_vertex;

-- Check planner cost estimates vs actual
EXPLAIN (ANALYZE, VERBOSE, BUFFERS, COSTS)
SELECT * FROM cypher('ninaivalaigal_graph', $$...$$) as (...);

-- If estimates are way off, consider pg_hint_plan extension
```

### Out of Memory

```sql
-- Reduce work_mem
SET work_mem = '32MB';

-- Enable query result caching
-- (application layer, not PostgreSQL)
```

## Concurrency Testing

After single-query optimization, validate sustained throughput:

```bash
# Install wrk
brew install wrk

# Test sustained load (requires HTTP endpoint)
wrk -t4 -c40 -d30s --latency \
  http://127.0.0.1:8080/graphops/cypher/simple_match

# Expected results:
# - Latency: p50 <2ms, p95 <5ms, p99 <10ms
# - Throughput: >500 req/s sustained
# - Errors: <0.1%

# Monitor during test
watch -n 1 'psql -U nina -d ninaivalaigal_dev -c "
  SELECT count(*) as active_queries
  FROM pg_stat_activity
  WHERE state = '\''active'\'';"
'
```

## Memory Tracking

```bash
# During benchmarks
ps -o pid,comm,rss,vsz | grep graphops

# Or with continuous monitoring
while true; do
  ps -o rss= -p $(pgrep graphops_benchmark) | \
    awk '{print $1/1024 " MB"}'
  sleep 1
done

# Target: RSS <200 MB sustained
```

## Results Documentation

### Template for Commit Messages

```
perf(graphops): <optimization description>

**Before**:
- Simple Match: X.XX ms (median), X.XX ms (P95)
- Graph Traversal: X.XX ms (median), X.XX ms (P95)
- Server Time: X.XX ms (EXPLAIN ANALYZE)

**After**:
- Simple Match: X.XX ms (median), X.XX ms (P95) [XX% improvement]
- Graph Traversal: X.XX ms (median), X.XX ms (P95) [XX% improvement]
- Server Time: X.XX ms (EXPLAIN ANALYZE) [XX% improvement]

**Changes**:
- Added B-tree index on ag_vertex(id)
- Increased work_mem to 64MB
- Updated statistics with ANALYZE

**Validation**: CI benchmarks passing, memory <200MB
```

## Recommended Course

1. ✅ **Start here**: VACUUM ANALYZE + basic indexes (Steps 1-2)
2. ⏳ **Measure**: Capture EXPLAIN ANALYZE before/after
3. ⏳ **Session tuning**: work_mem, jit, enable_seqscan (Step 3)
4. ⏳ **System tuning**: postgresql.conf changes (Step 4) - requires restart
5. ⏳ **Validate**: Run concurrent load test (wrk)
6. ⏳ **Document**: Update performance baselines in README

**Expected Total Gain**: 0.8-1.5ms (bringing 2ms → 0.5-1.2ms)

If you achieve <1ms AGE execution, **then** revisit client optimization (postgres crate, simd-json).

## References

- Apache AGE Docs: https://age.apache.org/age-manual/master/performance/performance.html
- PostgreSQL Tuning: https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server
- pg_stat_statements: https://www.postgresql.org/docs/current/pgstatstatements.html
- Index Advisor: https://github.com/ankane/dexter

---

**Owner**: Developer C (Database Infrastructure)
**Reviewer**: Developer A (Integration Testing)
**Sprint**: SPEC-099 Phase 1 (Database Optimization)
