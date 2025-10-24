# Developer A: Quick Run - AGE Indexes Fixed

**Status:** ✅ Migration corrected with proper AGE syntax
**Time to Results:** 5-10 minutes

---

## 🚀 **COPY-PASTE THIS**

```bash
# 1. Navigate to graphops
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# 2. Set environment (if needed)
export GRAPHOPS_GRAPH_NAME="ninaivalaigal_graph"

# 3. Run migration
alembic upgrade head

# 4. Verify indexes created
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db \
  -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'ninaivalaigal_graph' ORDER BY tablename;"

# 5. Rerun benchmark
cd /Users/swami/WorkSpace/ninaivalaigal
conda run -n nina python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results

# 6. Check results
cd benchmarks/results/graphops_mix_*
cat mix_summary.json | jq '.queries[] | {query: .query_type, p50: .latency_p50_ms, p95: .latency_p95_ms, p99: .latency_p99_ms}'
```

---

## 📊 **EXPECTED IMPROVEMENT**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **P50** | 17-20ms | **2-3ms** | **6-7x faster** |
| **P95** | 43-47ms | **4-5ms** | **9-10x faster** |
| **P99** | 61-65ms | **8-10ms** | **6-7x faster** |

---

## ✅ **SUCCESS CRITERIA**

- Migration creates 15-19 indexes (depending on tables)
- P95 latency drops below 5ms
- Ready to move to 1000 RPS testing

---

## 📝 **WHAT THE FIX CHANGED**

### **Before (Wrong):**
```sql
(properties->>'user_id')  -- PostgreSQL JSON syntax
```

### **After (Correct):**
```sql
agtype_to_text(properties -> '"id"'::agtype)  -- AGE agtype syntax
```

**19 indexes** covering Memory, User, Context, Team nodes + edge tables.

---

## ⚠️ **IF ANYTHING FAILS**

1. **Check logs:** `container logs ninaivalaigal-dev-graph-db`
2. **Verify connection:** `psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db -c "SELECT 1;"`
3. **See full guide:** `tasks/active/DEVELOPER_A_AGE_INDEX_MIGRATION.md`

---

**Run the commands above and report back with latency results!** 🎯
