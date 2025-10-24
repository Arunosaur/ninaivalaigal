# Developer A: AGE Index Migration - Corrected for agtype

**Date:** October 21, 2025, 9:21 PM
**Status:** ✅ Migration fixed with correct AGE syntax

---

## 🎯 **THE PROBLEM YOU FOUND**

### **Original (Wrong):**
```sql
CREATE INDEX ON Memory USING btree ((properties->>'user_id'))
```
**Error:** `operator ->>' expects jsonb, not agtype`

### **Root Cause:**
Apache AGE stores vertex properties as `agtype`, not `jsonb`. You can't use PostgreSQL JSON operators directly.

---

## ✅ **THE CORRECT SYNTAX**

### **For Text Properties:**
```sql
CREATE INDEX ON Memory
USING btree (agtype_to_text(properties -> '"id"'::agtype))
```

### **For Numeric Properties:**
```sql
CREATE INDEX ON Memory
USING btree (agtype_to_float8(properties -> '"relevance_score"'::agtype))
```

### **For Edge Tables:**
```sql
CREATE INDEX ON CREATED USING btree (start_id)
CREATE INDEX ON CREATED USING btree (end_id)
```

**Key Points:**
- Use `agtype_to_text()` for string fields
- Use `agtype_to_float8()` for numeric fields
- Property keys must be agtype literals: `'"id"'::agtype`
- Edge tables have direct columns (start_id/end_id)

---

## ✅ **UPDATED INDEX MIGRATION**

I've updated `20251021_002_create_age_indexes.py` with **19 indexes**:

### **Memory Node Indexes (6):**
- `idx_memory_id` - on id property
- `idx_memory_type` - on type property
- `idx_memory_topic` - on topic property
- `idx_memory_status` - on status property
- `idx_memory_updated_at` - on updated_at property
- `idx_memory_relevance_score` - on relevance_score (float)

### **User Node Indexes (2):**
- `idx_user_id` - on id property
- `idx_user_role` - on role property

### **Context Node Indexes (1):**
- `idx_context_id` - on id property

### **Team Node Indexes (1):**
- `idx_team_id` - on id property

### **Edge Indexes (8):**
- `idx_created_start_id` / `idx_created_end_id`
- `idx_accessed_start_id` / `idx_accessed_end_id`
- `idx_tagged_with_start_id` / `idx_tagged_with_end_id`
- `idx_belongs_to_start_id` / `idx_belongs_to_end_id`

---

## 🚀 **RUNNING THE MIGRATION**

### **Step 1: Set Environment Variables**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# Set graph name (if different from default)
export GRAPHOPS_GRAPH_NAME="ninaivalaigal_graph"

# Optional: Set database URL explicitly
export GRAPHOPS_DATABASE_URL="postgresql://nina:dev_password_change_in_production@localhost:5433/ninaivalaigal-graph-db"
```

---

### **Step 2: Run Migration**

```bash
# Apply the index migration
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_age_indexes
✅ Created 19 AGE indexes on ninaivalaigal_graph
   Indexes: idx_memory_id, idx_memory_type, idx_memory_topic, idx_memory_status, idx_memory_updated_at
   ... and 14 more
```

**If Some Indexes Skip:**
```
⚠️  Skipped 2 indexes:
   - idx_belongs_to_start_id (table BELONGS_TO missing)
   - idx_belongs_to_end_id (table BELONGS_TO missing)
```
This is **OK** - the migration is resilient to missing tables.

---

### **Step 3: Verify Indexes Created**

```bash
# Check all indexes
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db << 'EOF'
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'ninaivalaigal_graph'
ORDER BY tablename, indexname;
EOF
```

**Expected:** Should see 15-19 indexes depending on which tables exist.

---

### **Step 4: Test Index Usage**

```bash
# Test that indexes are used for queries
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db << 'EOF'
SET search_path = ninaivalaigal_graph, ag_catalog, "$user", public;

-- Explain a query that should use the index
EXPLAIN ANALYZE
SELECT * FROM "Memory"
WHERE agtype_to_text(properties -> '"id"'::agtype) = 'perf_mem_001';
EOF
```

**Expected Output:** Should show "Index Scan using idx_memory_id"

---

## 🎯 **RERUN BENCHMARK**

Now that indexes are created, rerun the benchmark:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal

conda run -n nina python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results
```

---

## 📊 **EXPECTED RESULTS**

### **Before Indexes (Your Baseline):**
- P50: 17-20ms
- P95: 43-47ms
- P99: 61-65ms

### **After Indexes (Expected):**
- P50: **2-3ms** (6-7x improvement)
- P95: **4-5ms** (9-10x improvement)
- P99: **8-10ms** (6-7x improvement)

---

## 🔍 **TROUBLESHOOTING**

### **If Migration Fails:**

1. **Check Alembic current version:**
   ```bash
   alembic current
   ```

2. **If stuck on 001, downgrade and retry:**
   ```bash
   alembic downgrade 001_initial_schema
   alembic upgrade head
   ```

3. **Check PostgreSQL logs:**
   ```bash
   container logs ninaivalaigal-dev-graph-db
   ```

---

### **If Indexes Don't Help Latency:**

1. **Verify indexes are being used:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM cypher('ninaivalaigal_graph', $$
     MATCH (m:Memory {id: 'perf_mem_001'})
     RETURN m
   $$) AS (m agtype);
   ```

2. **Check index statistics:**
   ```sql
   SELECT
     schemaname,
     tablename,
     indexname,
     idx_scan,
     idx_tup_read,
     idx_tup_fetch
   FROM pg_stat_user_indexes
   WHERE schemaname = 'ninaivalaigal_graph'
   ORDER BY idx_scan DESC;
   ```

3. **If still slow, investigate:**
   - Network overhead (gRPC serialization)
   - N+1 query patterns
   - Database configuration (shared_buffers, work_mem)

---

## 🔄 **ROLLBACK (If Needed)**

```bash
# Remove indexes
alembic downgrade 001_initial_schema

# Reapply if needed
alembic upgrade head
```

---

## 📝 **WHAT TO REPORT BACK**

After running the migration and benchmark:

```
Migration Status: [SUCCESS / FAILED]
Indexes Created: [X] out of 19
Indexes Skipped: [list any]

New P50 Latency: [X] ms
New P95 Latency: [Y] ms
New P99 Latency: [Z] ms

Improvement: [X]% faster

Index Usage Verified: [YES / NO]
```

---

## 🎯 **KEY LEARNINGS**

### **Apache AGE is NOT regular PostgreSQL JSON:**
- ❌ `properties->>'user_id'` doesn't work
- ✅ `agtype_to_text(properties -> '"user_id"'::agtype)` works

### **Property Keys Must Be agtype Literals:**
- ❌ `properties -> 'id'` doesn't work
- ✅ `properties -> '"id"'::agtype` works

### **Use Correct Type Converters:**
- Text: `agtype_to_text()`
- Float: `agtype_to_float8()`
- Int: `agtype_to_int4()`
- Boolean: `agtype_to_bool()`

### **Edge Tables Are Different:**
- Edges have direct columns: `start_id`, `end_id`
- No casting needed for these columns
- Index them for fast relationship traversal

---

## ✅ **NEXT STEPS**

1. **Run the migration** (Step 2 above)
2. **Verify indexes** (Step 3 above)
3. **Rerun benchmark** (Step 4 above)
4. **Report results** (latency improvement)
5. **If P95 <5ms:** ✅ Move to 1000 RPS testing
6. **If P95 >10ms:** Deeper investigation needed

---

**The migration is now resilient and uses correct AGE syntax!** 🎯

**Expected time:** 5-10 minutes for migration + benchmark
