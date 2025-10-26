# Alembic Migration Updates for SPEC-009 User Stories

**Date:** October 26, 2025
**Updated Stories:** US-115, US-117

---

## 🎯 Why This Update Was Needed

### Issue
The initial SPEC-009 user stories showed **raw SQL DDL** examples for database schema changes, but the ninaivalaigal project uses **Alembic migrations** for all schema changes per SPEC-019 standards.

### Examples of Raw SQL (Incorrect)
```sql
-- ❌ DO NOT USE - Raw SQL DDL
CREATE TABLE policy_audits (...);
CREATE INDEX idx_policy_audits_user_id ON policy_audits(user_id);
```

### Correct Approach (Alembic)
```python
# ✅ CORRECT - Alembic migration
def upgrade():
    op.create_table('policy_audits', ...)
    op.create_index('idx_policy_audits_user_id', 'policy_audits', ['user_id'])
```

---

## ✅ Stories Updated

### Story #115: Context Sensitivity + RBAC Integration

**What Was Added:**
- Complete Alembic migration code for `policy_audits` table
- Migration commands (create, apply, verify, test)
- 5 new acceptance criteria (AC11-AC15) for migration testing
- Testing checklist for upgrade/downgrade validation

**New Section:**
```
## 🗄️ Database Migration (ALEMBIC REQUIRED)
```

**Key Requirements:**
1. Create migration: `alembic revision -m "Add policy_audits table"`
2. Table includes: user_id, resource, action, sensitivity_tier, decision, etc.
3. 4 performance indexes: user_id, timestamp, decision, (resource, action)
4. Test upgrade → verify → downgrade → upgrade cycle
5. Application code logs to new table

**Taiga Link:** http://localhost:9000/project/ninaivalaigal/us/115

---

### Story #117: ORM Guardrails & Multi-Tenant Isolation

**What Was Added:**
- Schema verification commands for `organization_id` columns
- Index verification queries for existing indexes
- Alembic migration template (if indexes missing)
- Performance verification with EXPLAIN ANALYZE
- 4 new acceptance criteria (AC11-AC14) for schema verification

**New Section:**
```
## 🗄️ Database Migration (ALEMBIC VERIFICATION)
```

**Key Requirements:**
1. Verify all multi-tenant tables have `organization_id` column
2. Verify all have index on `organization_id`
3. Create Alembic migration if indexes missing
4. Verify ORM filters use indexed columns (performance check)

**Performance Check:**
```sql
EXPLAIN ANALYZE SELECT * FROM memories WHERE organization_id = 1;
-- Should use "Index Scan using idx_memories_organization_id"
```

**Taiga Link:** http://localhost:9000/project/ninaivalaigal/us/117

---

## 📊 Summary of Changes

| Story | Original | After Update | Impact |
|-------|----------|--------------|--------|
| **US-115** | Raw SQL examples | Alembic migration code | +5 ACs, complete migration guide |
| **US-117** | ORM-only focus | Schema verification + Alembic | +4 ACs, performance validation |

---

## 🔧 Migration Standards (SPEC-019)

### Project Standard
All database schema changes in ninaivalaigal **MUST** use Alembic migrations.

### Why Alembic?
1. **Version Control**: Migrations tracked in Git
2. **Rollback**: Can downgrade if issues occur
3. **Reproducibility**: Same schema across dev/staging/prod
4. **Testing**: Can test upgrade/downgrade cycles
5. **Collaboration**: Team knows what changed and when

### Alembic Workflow
```bash
# 1. Create migration
cd server
alembic revision -m "Description of change"

# 2. Edit generated file in alembic/versions/
# Add upgrade() and downgrade() logic

# 3. Apply migration
alembic upgrade head

# 4. Verify
alembic current
psql -d ninaivalaigal -c "\\dt table_name"

# 5. Test downgrade (optional)
alembic downgrade -1
alembic upgrade head
```

---

## ✅ What Developers Should Do

### For US-115 Implementation
1. **Create** migration file using template provided
2. **Test** migration: upgrade → verify → downgrade → upgrade
3. **Verify** all indexes created
4. **Update** application code to log to `policy_audits`
5. **Document** migration in PR description

### For US-117 Implementation
1. **Run** verification queries to check current schema
2. **Create** migration only if indexes missing
3. **Test** ORM filters use indexes (EXPLAIN ANALYZE)
4. **Verify** performance after migration
5. **Document** findings in PR

---

## 🚨 Critical Reminders

### ❌ DO NOT
- Use raw SQL `CREATE TABLE` or `ALTER TABLE`
- Manually run DDL in psql
- Skip migration testing
- Commit without testing downgrade

### ✅ DO
- Always use Alembic migrations
- Test upgrade/downgrade before PR
- Verify indexes with EXPLAIN ANALYZE
- Document schema changes in PR
- Follow SPEC-019 standards

---

## 📋 Acceptance Criteria Added

### US-115 New ACs
- **AC11**: Alembic migration created for `policy_audits` table
- **AC12**: Migration includes 4 performance indexes
- **AC13**: Migration tested: upgrade → verify → downgrade → upgrade
- **AC14**: `policy_audits` table visible in database after migration
- **AC15**: Policy audit logging uses new table (no raw SQL inserts)

### US-117 New ACs
- **AC11**: All multi-tenant tables have `organization_id` column (verified)
- **AC12**: All multi-tenant tables have index on `organization_id` (verified or added)
- **AC13**: ORM filters use indexed `organization_id` column
- **AC14**: Performance: Organization filter queries use index (EXPLAIN verified)

---

## 🔗 Related Documentation

- **SPEC-019**: Database Management & Migration
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Migrations**: https://docs.sqlalchemy.org/en/14/core/schema.html

---

## ✅ Verification

After implementing these stories, verify:

```bash
# Check migration history
alembic history

# Current version
alembic current

# Show pending migrations
alembic show <revision>

# Verify tables exist
psql -d ninaivalaigal -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('policy_audits');
"

# Verify indexes
psql -d ninaivalaigal -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('policy_audits', 'memories', 'contexts')
  AND (indexname LIKE '%organization_id%' OR indexname LIKE '%policy%')
ORDER BY tablename, indexname;
"
```

---

**Update Complete:** October 26, 2025, 2:05 AM
**Stories Updated:** 2 (US-115, US-117)
**Standard Applied:** SPEC-019 (Alembic Migrations)
**Status:** ✅ Ready for Implementation
