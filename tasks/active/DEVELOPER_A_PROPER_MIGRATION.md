# Developer A: Proper Alembic Migration Approach

**Date:** October 21, 2025, 4:56 PM
**Status:** CORRECTED - Use Alembic, not raw SQL

---

## 🎯 **THE RIGHT WAY**

You're absolutely correct to question the raw SQL approach. Even for experimental/benchmark work, we should use proper migrations for:

- ✅ Migration tracking
- ✅ Rollback capability
- ✅ Version control
- ✅ Team coordination
- ✅ Repeatable deployments

---

## ✅ **PROPER ALEMBIC MIGRATION CREATED**

### **Connection Details:**
```
Host:     localhost
Port:     5433          (separate from main DB on 5432)
Database: ninaivalaigal-graph-db
User:     nina          ← Consistent with rest of platform
Password: dev_password_change_in_production
```

### **Connection String:**
```
postgresql://nina:dev_password_change_in_production@localhost:5433/ninaivalaigal-graph-db  # pragma: allowlist secret
```
   - Can override with `DATABASE_URL` env var

### **Files Created:**

1. **`rust-services/graphops/alembic.ini`**
   - Alembic configuration

2. **`rust-services/graphops/migrations/env.py`**
   - Alembic environment configuration
   - Handles online/offline migrations

3. **`rust-services/graphops/migrations/script.py.mako`**
   - Template for new migrations

4. **`rust-services/graphops/migrations/versions/20251021_001_initial_graphops_schema.py`**
   - Baseline migration (tracks existing AGE schema)
   - Does not create schema (already exists from init scripts)
   - Establishes version control baseline

5. **`rust-services/graphops/migrations/versions/20251021_002_create_age_indexes.py`**
   - Creates the 7 performance indexes
   - Includes proper upgrade/downgrade
   - Documented with US #86 context

---

## 🚀 **CORRECT USAGE (If Not Already Applied)**

### **Step 1: Stop if you already ran raw SQL**

If you already created indexes with raw SQL:

```bash
# Check if indexes exist
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db -c "\di ninaivalaigal_graph.*"

# If indexes exist, stamp Alembic to current version
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops
alembic stamp 002_age_indexes
```

This tells Alembic "these migrations are already applied" without re-running them.

---

### **Step 2: If you haven't applied anything yet (CLEAN SLATE)**

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# Install alembic if needed
pip3 install alembic

# Initialize migration tracking (baseline)
alembic stamp 001_initial_schema

# Apply index migration
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
✅ Verified Apache AGE schema baseline
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_age_indexes
✅ Created 7 AGE indexes for query performance optimization
```

---

### **Step 3: Verify indexes created**

```bash
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db -c "
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'ninaivalaigal_graph'
ORDER BY tablename, indexname;
"
```

**Expected:** Should see 7 indexes

---

### **Step 4: Rerun benchmark**

```bash
conda run -n nina python3 scripts/mcp_mix_run.py \
  --config benchmarks/graphops/config/realistic_mix.json \
  --target localhost:13398 \
  --target-rps 100 \
  --parallel 5 \
  --output-dir benchmarks/results
```

---

## 🔄 **ROLLBACK CAPABILITY**

If indexes cause issues, you can rollback:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# Rollback to before indexes
alembic downgrade 001_initial_schema

# Re-apply if needed
alembic upgrade head
```

---

## 📋 **MIGRATION HISTORY**

```bash
# Check current version
alembic current

# Show migration history
alembic history --verbose

# Show pending migrations
alembic show head
```

---

## 🎯 **FUTURE MIGRATIONS**

When you need new indexes or schema changes:

```bash
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops

# Create new migration
alembic revision -m "add similarity score indexes"

# Edit the generated file in migrations/versions/
# Add your upgrade() and downgrade() logic

# Apply it
alembic upgrade head
```

---

## ⚠️ **IF YOU ALREADY RAN RAW SQL**

**Option A: Stamp and continue (RECOMMENDED)**

```bash
# Tell Alembic the migrations are already applied
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops
alembic stamp 002_age_indexes

# Verify
alembic current
# Should show: 002_age_indexes (head)
```

**Option B: Rollback and redo properly**

```bash
# Drop indexes manually
psql -h localhost -p 5433 -U nina -d ninaivalaigal-graph-db << 'EOF'
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_memory_user_id;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_memory_created_at;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_memory_context_id;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_context_user_id;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_team_id;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_tagged_with_topic;
DROP INDEX IF EXISTS ninaivalaigal_graph.idx_accessed_timestamp;
EOF

# Then use Alembic properly
cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/graphops
alembic stamp 001_initial_schema
alembic upgrade head
```

---

## 📝 **WHY THIS MATTERS**

### **With Alembic:**
- ✅ Team knows what schema version is deployed
- ✅ Can rollback if indexes cause issues
- ✅ Migrations tracked in version control
- ✅ Repeatable across environments (dev/staging/prod)
- ✅ Clear history of schema changes
- ✅ Safe to apply in CI/CD pipelines

### **With Raw SQL:**
- ❌ No tracking of what's applied
- ❌ No easy rollback
- ❌ Team coordination difficult
- ❌ Not repeatable
- ❌ Can't tell what version is deployed
- ❌ Creates technical debt

---

## 🎓 **LESSON LEARNED**

**Even for "experimental" or "quick fix" database changes:**
1. Always use migrations (Alembic/SQLAlchemy)
2. Never use raw SQL scripts (except for debugging)
3. Think "how will this be deployed to production?"
4. Think "how will another developer replicate this?"

**Urgency is not an excuse to skip proper patterns.**

---

## 🚀 **YOUR NEXT STEPS**

### **Choose based on your current state:**

**If you haven't run anything yet:**
```bash
cd rust-services/graphops
alembic stamp 001_initial_schema
alembic upgrade head
# Rerun benchmark
```

**If you already ran raw SQL:**
```bash
cd rust-services/graphops
alembic stamp 002_age_indexes
# Verify indexes exist
psql -h localhost -p 5433 -U postgres -d ninaivalaigal-graph-db -c "\di ninaivalaigal_graph.*"
# Rerun benchmark
```

**Then report back:**
```
Migration approach used: [alembic stamp / alembic upgrade]
Indexes verified: [YES/NO]
New P95 latency: [X] ms
Ready for next phase: [YES/NO]
```

---

## ✅ **THANK YOU FOR CATCHING THIS**

This is exactly the kind of discipline that prevents technical debt. Even under pressure to "just fix it fast," we should maintain proper patterns.

**Updated guidance reflects the correct Alembic approach!**

---

**Files ready in:**
- `rust-services/graphops/alembic.ini`
- `rust-services/graphops/migrations/env.py`
- `rust-services/graphops/migrations/versions/20251021_001_initial_graphops_schema.py`
- `rust-services/graphops/migrations/versions/20251021_002_create_age_indexes.py`
