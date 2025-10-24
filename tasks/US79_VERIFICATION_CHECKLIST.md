# US#79 - Verification Checklist for Architects
## What Needs to Be Verified

**Document Purpose**: Detailed verification steps for architectural review
**Estimated Review Time**: 3-6 hours
**Reviewer Role**: System Architect / Technical Lead

---

## ✅ Section 1: Database Schema Review

### 1.1 Migration Inspection

**Files to Review**:
```
/alembic/versions/0115_user_columns.py
/alembic/versions/0116_teams_org_id.py
/alembic/versions/0117_team_provenance.py
/alembic/versions/0118_team_intelligence.py
/alembic/versions/0119_user_provenance.py
/alembic/versions/0120_org_provenance.py
```

**Verify**:
- [ ] Migration `upgrade()` functions are idempotent
- [ ] Migration `downgrade()` functions correctly reverse changes
- [ ] No data loss in downgrade operations
- [ ] Column defaults are appropriate
- [ ] Nullable columns are correctly marked
- [ ] Foreign key cascades are intentional (`CASCADE` vs `SET NULL`)

**Red Flags**:
- ⚠️ Non-nullable columns without defaults (breaks existing data)
- ⚠️ CASCADE deletes that could orphan data
- ⚠️ Missing indexes on foreign keys
- ⚠️ Downgrade that drops columns without backup

**Tool**:
```bash
# Review migration SQL without executing
cd /Users/swami/WorkSpace/ninaivalaigal
DATABASE_URL="..." alembic upgrade head --sql > migrations.sql
```

---

### 1.2 Trigger Logic Review

**Triggers Created**:
1. `set_acquisition_date()` - Auto-set acquisition_date when acquired_from_organization_id is set
2. `update_team_lineage_path()` - Maintain full_lineage_path array
3. `update_user_reporting_chain()` - Maintain full_reporting_chain array
4. `update_org_corporate_hierarchy()` - Maintain full_corporate_hierarchy array

**Verify Each Trigger**:
- [ ] **Correctness**: Logic handles all edge cases
- [ ] **Performance**: Trigger doesn't cause cascade updates
- [ ] **Safety**: Max depth limit prevents infinite loops
- [ ] **Idempotency**: Re-running trigger produces same result
- [ ] **Error Handling**: Raises warnings on anomalies

**Test Scenarios**:
```sql
-- Test 1: Simple chain (A → B → C)
-- Expected: C.full_reporting_chain = [A, B, C]

-- Test 2: Deep chain (8+ levels)
-- Expected: Handles gracefully, raises warning if > 20 levels

-- Test 3: Circular reference (A → B → A)
-- Expected: Prevented by CHECK constraint or trigger logic

-- Test 4: NULL parent (root entity)
-- Expected: full_*_chain = [self_id]

-- Test 5: Update parent (change B's parent from A to X)
-- Expected: C's chain updates automatically to [X, B, C]
```

**Red Flags**:
- ⚠️ No max depth limit (infinite loop risk)
- ⚠️ Trigger mutates multiple rows (cascade performance issue)
- ⚠️ No error handling for cycles
- ⚠️ Trigger logic not tested with concurrent updates

---

### 1.3 Constraint Validation

**CHECK Constraints Added**: 18 total

**Verify Categories**:

**Category A: Data Integrity**
```sql
-- Examples:
CHECK (manager_id IS NULL OR manager_id != id)
CHECK (parent_team_id IS NULL OR parent_team_id != id)
CHECK (parent_organization_id IS NULL OR parent_organization_id != id)
```
- [ ] Self-reference prevention works
- [ ] Circular reference handled at constraint level

**Category B: Business Rules**
```sql
-- Examples:
CHECK (acquired_from_organization_id IS NULL OR origin = 'acquired')
CHECK (employment_governance != 'contractor' OR vendor_organization_id IS NOT NULL)
```
- [ ] Rules are correct and complete
- [ ] No contradictory constraints
- [ ] Rules match product requirements

**Category C: Enum Validation**
```sql
-- Examples:
CHECK (status IN ('active', 'inactive', 'sunset', 'transitioning'))
CHECK (origin IN ('native', 'acquired', 'contractor', 'partner', 'intern'))
```
- [ ] All valid values are included
- [ ] No typos in enum values
- [ ] Future-proof (easy to add new values)

**Test Each Constraint**:
```sql
-- Should FAIL (constraint violation):
INSERT INTO users (manager_id, id) VALUES (uuid1, uuid1);  -- Self-manager

-- Should SUCCEED:
INSERT INTO users (origin, acquired_from_organization_id)
VALUES ('acquired', valid_org_uuid);

-- Should FAIL:
INSERT INTO users (employment_governance, vendor_organization_id)
VALUES ('contractor', NULL);  -- Missing vendor
```

**Red Flags**:
- ⚠️ Constraint too restrictive (blocks valid use cases)
- ⚠️ Constraint too permissive (allows invalid data)
- ⚠️ No test coverage for constraint violations

---

### 1.4 Index Strategy Review

**Indexes Added**: 30+ (single-column, composite, GIN)

**Verify**:
- [ ] **Coverage**: All foreign keys have indexes
- [ ] **Cardinality**: Indexed columns have high cardinality
- [ ] **Query Patterns**: Indexes match WHERE/JOIN clauses
- [ ] **Composite Order**: Leftmost column is most selective
- [ ] **GIN Appropriateness**: GIN only used for array containment

**Analyze Query Plans**:
```sql
-- Example: Verify index is used
EXPLAIN ANALYZE
SELECT * FROM users
WHERE primary_organization_id = $1
  AND employment_status = 'active';

-- Expected: Index Scan on ix_users_org_status
-- Red Flag: Seq Scan (index not used)
```

**Index Overhead**:
```sql
-- Check total index size
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'ag_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Red Flags**:
- ⚠️ Duplicate indexes (e.g., (col1) and (col1, col2))
- ⚠️ Indexes on low-cardinality columns (e.g., boolean)
- ⚠️ No index on foreign keys
- ⚠️ Total index size > table size (over-indexed)

---

## ✅ Section 2: Data Model Review

### 2.1 Entity Relationship Diagram

**Verify**:
- [ ] **No Circular Dependencies**: A → B → C → A cycles
- [ ] **Cascade Logic**: DELETE cascades are intentional
- [ ] **Nullable Relationships**: Optional FKs are nullable
- [ ] **Orphan Prevention**: Critical entities can't be orphaned

**Key Relationships**:
```
Organization → Teams (1:N)
Organization → Users (1:N via primary_organization_id)
Organization → Organization (1:N via parent_organization_id)
Team → Team (1:N via parent_team_id)
User → User (1:N via manager_id)
Team → Organization (M:N via acquired_from_organization_id)
User → Organization (M:N via acquired_from_organization_id, vendor_organization_id)
```

**Test Scenarios**:
```sql
-- Test 1: Delete organization
-- Expected behavior: What happens to teams? Users?

-- Test 2: Delete team
-- Expected behavior: What happens to team_members?

-- Test 3: Delete user (who is a manager)
-- Expected behavior: What happens to direct reports?
```

**Red Flags**:
- ⚠️ DELETE CASCADE chains (deleting Org deletes all Teams, Users)
- ⚠️ Circular foreign keys (A → B, B → A)
- ⚠️ Orphaned records after cascade delete

---

### 2.2 Normalization Analysis

**Verify**:
- [ ] **3NF Compliance**: No transitive dependencies
- [ ] **Denormalization Justification**: Arrays (full_*_chain) are intentional
- [ ] **Data Duplication**: No redundant storage

**Denormalized Fields** (Requires Justification):
```python
# These are NOT normalized (stored redundantly):
full_reporting_chain: UUID[]  # Computed from manager_id chain
full_corporate_hierarchy: UUID[]  # Computed from parent_organization_id
full_lineage_path: UUID[]  # Computed from parent_team_id

# Justification: Performance optimization for ancestry queries
# Trade-off: Storage space + update complexity vs query speed
```

**Questions**:
- ❓ Is the performance gain worth the complexity?
- ❓ Could we compute on-the-fly with recursive CTEs?
- ❓ Have we measured the actual performance difference?

---

### 2.3 SQLAlchemy Model Review

**Files to Review**:
```
/services/core-api/database/models.py
```

**Verify**:
- [ ] **Relationship Ambiguity**: All `foreign_keys` explicitly defined
- [ ] **Backref Consistency**: `back_populates` matches on both sides
- [ ] **Cascade Rules**: SQLAlchemy cascades match DB constraints
- [ ] **Lazy Loading**: Appropriate loading strategy (lazy, joined, subquery)

**Original Issue** (Should Be Fixed):
```python
# BEFORE (ambiguous):
refresh_tokens = relationship("RefreshToken", back_populates="user")

# AFTER (explicit):
refresh_tokens = relationship(
    "RefreshToken",
    foreign_keys="[RefreshToken.user_id]",
    back_populates="user"
)
```

**Red Flags**:
- ⚠️ Missing `foreign_keys` on ambiguous relationships
- ⚠️ Mismatched `back_populates` names
- ⚠️ SQLAlchemy cascade doesn't match DB cascade
- ⚠️ N+1 query problems from lazy loading

---

## ✅ Section 3: Performance Validation

### 3.1 Trigger Performance Testing

**Test Setup**:
```sql
-- Create test hierarchy (10 levels deep)
INSERT INTO users (id, name, manager_id) VALUES
  (uuid1, 'CEO', NULL),
  (uuid2, 'VP', uuid1),
  (uuid3, 'Director', uuid2),
  ...
  (uuid10, 'IC', uuid9);

-- Measure trigger execution time
\timing on
UPDATE users SET manager_id = uuid_new WHERE id = uuid10;
\timing off
```

**Benchmarks**:
- [ ] Single insert: < 10ms
- [ ] Update with 10-level chain: < 50ms
- [ ] Bulk insert (1000 records): < 5 seconds
- [ ] Concurrent updates (10 connections): No deadlocks

**Load Test**:
```bash
# Simulate 100 concurrent reorganizations
pgbench -c 10 -j 2 -T 60 -f test_trigger_load.sql
```

**Red Flags**:
- ⚠️ Trigger execution > 100ms
- ⚠️ Deadlocks under concurrent updates
- ⚠️ Array size > 1MB (PostgreSQL limit warnings)

---

### 3.2 Query Performance Testing

**Critical Queries**:

**Query 1: Org Chart (Reporting Chain)**
```sql
-- Get all direct reports
EXPLAIN ANALYZE
SELECT * FROM users WHERE manager_id = $1 AND employment_status = 'active';

-- Expected: Index Scan on ix_users_manager_id
-- Benchmark: < 5ms for 1000 employees
```

**Query 2: M&A Employee List**
```sql
-- All acquired employees from specific deal
EXPLAIN ANALYZE
SELECT * FROM users
WHERE acquired_from_organization_id = $1
  AND origin = 'acquired'
  AND employment_status = 'active';

-- Expected: Index Scan on ix_users_acquired_from_org
-- Benchmark: < 10ms for 10,000 employees
```

**Query 3: Array Containment (GIN Index)**
```sql
-- Find all users under a specific VP
EXPLAIN ANALYZE
SELECT * FROM users WHERE $vp_uuid = ANY(full_reporting_chain);

-- Expected: Bitmap Index Scan using ix_users_reporting_chain_gin
-- Benchmark: < 20ms for 10,000 employees
```

**Query 4: Corporate Hierarchy**
```sql
-- All subsidiaries under parent company
EXPLAIN ANALYZE
SELECT * FROM organizations
WHERE parent_organization_id = $1
  AND organization_status = 'active';

-- Expected: Index Scan on ix_organizations_parent_status
-- Benchmark: < 5ms for 500 organizations
```

**Benchmarks**:
- [ ] All queries < 50ms with 10K records
- [ ] All queries < 100ms with 100K records
- [ ] No sequential scans on large tables
- [ ] GIN indexes used for array queries

**Red Flags**:
- ⚠️ Seq Scan on tables > 1000 rows
- ⚠️ Query time > 1 second
- ⚠️ Index not used despite being available

---

### 3.3 Storage Impact Analysis

**Measure**:
```sql
-- Table sizes before migrations
-- (Baseline measurement required)

-- Table sizes after migrations
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'ag_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Verify**:
- [ ] Index size < 2x table size
- [ ] Array fields don't dominate storage
- [ ] JSON fields are appropriately used (not TEXT)

**Projections**:
```
Assumptions:
- 10,000 users
- 500 teams
- 50 organizations
- Average reporting chain depth: 5 levels
- Average corporate hierarchy depth: 3 levels

Storage Estimate:
- Users table: ~5MB (base) + ~2MB (provenance) = 7MB
- Teams table: ~500KB (base) + ~200KB (provenance) = 700KB
- Organizations table: ~100KB (base) + ~50KB (provenance) = 150KB
- Indexes: ~10MB total

Total Impact: ~18MB (acceptable)
```

**Red Flags**:
- ⚠️ Array fields consuming > 50% of storage
- ⚠️ Index size > table size (over-indexed)
- ⚠️ Storage growth trajectory unsustainable

---

## ✅ Section 4: Data Integrity Testing

### 4.1 Circular Reference Prevention

**Test Cases**:
```sql
-- Test 1: Direct self-reference (should fail)
UPDATE users SET manager_id = id WHERE id = $uuid1;
-- Expected: CHECK constraint violation

-- Test 2: Circular reference (A → B → A)
UPDATE users SET manager_id = $uuid_b WHERE id = $uuid_a;
UPDATE users SET manager_id = $uuid_a WHERE id = $uuid_b;
-- Expected: Second UPDATE should fail or infinite loop prevented

-- Test 3: Long cycle (A → B → C → D → A)
-- Expected: Prevented by max depth limit in trigger
```

**Verify**:
- [ ] Self-reference prevented by CHECK constraint
- [ ] Circular references detected
- [ ] Trigger raises warning for deep hierarchies (> 20 levels)
- [ ] No silent data corruption

**Red Flags**:
- ⚠️ Circular reference succeeds
- ⚠️ Trigger enters infinite loop
- ⚠️ Array grows unbounded

---

### 4.2 Constraint Violation Testing

**Test Each Constraint**:
```sql
-- Test: Acquired user without source org
INSERT INTO users (origin, acquired_from_organization_id)
VALUES ('acquired', NULL);
-- Expected: CHECK constraint violation

-- Test: Contractor without vendor
INSERT INTO users (employment_governance, vendor_organization_id)
VALUES ('contractor', NULL);
-- Expected: CHECK constraint violation

-- Test: Invalid enum value
INSERT INTO users (employment_status) VALUES ('invalid_status');
-- Expected: CHECK constraint violation
```

**Verify**:
- [ ] All constraints fire as expected
- [ ] Error messages are clear
- [ ] Constraints cannot be bypassed

---

### 4.3 Trigger Edge Cases

**Test Scenarios**:
```sql
-- Test 1: Update triggers NULL → UUID
UPDATE users SET manager_id = $uuid WHERE manager_id IS NULL;
-- Expected: full_reporting_chain updates from [self] to [manager, self]

-- Test 2: Update triggers UUID → NULL
UPDATE users SET manager_id = NULL WHERE id = $uuid;
-- Expected: full_reporting_chain updates to [self]

-- Test 3: Update triggers UUID → Different UUID
UPDATE users SET manager_id = $uuid_new WHERE manager_id = $uuid_old;
-- Expected: full_reporting_chain recomputes

-- Test 4: Bulk update (1000 rows)
UPDATE users SET manager_id = $new_manager WHERE team_id = $team;
-- Expected: All 1000 reporting chains update correctly
```

**Verify**:
- [ ] Trigger handles NULL → value correctly
- [ ] Trigger handles value → NULL correctly
- [ ] Trigger handles value → different value correctly
- [ ] Bulk updates don't timeout

---

## ✅ Section 5: Migration Safety

### 5.1 Rollback Testing

**Test Procedure**:
```bash
# 1. Apply all migrations
alembic upgrade head

# 2. Rollback one migration
alembic downgrade -1

# 3. Verify database state
# - Tables exist?
# - Data intact?
# - Triggers removed?

# 4. Repeat for all 6 migrations
alembic downgrade -1  # Repeat 5 more times
```

**Verify**:
- [ ] Each downgrade completes without errors
- [ ] No data loss after rollback
- [ ] Triggers cleanly removed
- [ ] Constraints cleanly removed
- [ ] Can re-apply migrations after rollback

**Red Flags**:
- ⚠️ Downgrade fails
- ⚠️ Data loss after rollback
- ⚠️ Orphaned triggers after rollback
- ⚠️ Cannot re-apply after rollback

---

### 5.2 Production Data Compatibility

**Questions**:
- ❓ Do we have existing production data?
- ❓ Will new nullable columns cause issues?
- ❓ Can existing workflows continue without changes?

**Test with Production-Like Data**:
```bash
# 1. Clone production database structure
pg_dump --schema-only production > schema.sql

# 2. Apply migrations to clone
psql cloned_db < schema.sql
alembic upgrade head

# 3. Verify existing functionality
# - Can create users?
# - Can create teams?
# - Can create organizations?
```

**Verify**:
- [ ] Migrations apply cleanly to production schema
- [ ] Existing records remain valid
- [ ] New nullable fields don't break queries
- [ ] Application code works with new schema

---

### 5.3 Backfill Strategy

**Challenge**: Auto-maintained arrays are NULL for existing records

**Options**:

**Option A: Backfill Script**
```python
# Backfill full_reporting_chain for all existing users
def backfill_reporting_chains():
    users = User.query.filter(User.full_reporting_chain == None).all()
    for user in users:
        chain = compute_reporting_chain(user)
        user.full_reporting_chain = chain
    db.session.commit()
```

**Option B: Trigger on Read (Lazy)**
```sql
-- Compute on-the-fly if NULL
SELECT COALESCE(
    full_reporting_chain,
    compute_reporting_chain(id)  -- Fallback function
) AS reporting_chain
FROM users;
```

**Option C: Gradual Backfill**
```python
# Backfill 1000 records per day
celery.schedule(backfill_batch, cron='0 2 * * *')
```

**Architect Decision Required**:
- [ ] Which backfill strategy to use?
- [ ] Timeline for backfill completion?
- [ ] Acceptable data inconsistency period?

---

## ✅ Section 6: Code Quality Review

### 6.1 Documentation

**Verify**:
- [ ] Each migration has descriptive docstring
- [ ] Triggers have inline comments
- [ ] Complex logic is explained
- [ ] Database comments on columns

**Documentation Files**:
```
/services/core-api/ENTERPRISE_INTELLIGENCE_COMPLETE.md  ✅ 300+ lines
/services/core-api/ENTERPRISE_TEAM_MODEL_V1.1.md         ✅ 250+ lines
/tasks/US79_ARCHITECTURAL_REVIEW.md                      ✅ This file
/tasks/US79_VERIFICATION_CHECKLIST.md                    ✅ This file
```

**Red Flags**:
- ⚠️ Undocumented migrations
- ⚠️ No examples of how to use new fields
- ⚠️ No migration between system states

---

### 6.2 Testing Coverage

**Current State**:
- ❌ No unit tests for triggers
- ❌ No integration tests for relationships
- ❌ No load tests for performance
- ❌ No migration tests (up/down)

**Required Tests**:
```python
# Test 1: Trigger correctness
def test_reporting_chain_auto_maintained():
    user_a = User(name="A", manager=None)
    user_b = User(name="B", manager=user_a)
    user_c = User(name="C", manager=user_b)
    assert user_c.full_reporting_chain == [user_a.id, user_b.id, user_c.id]

# Test 2: Circular reference prevention
def test_circular_manager_prevented():
    user_a = User(name="A")
    user_b = User(name="B", manager=user_a)
    with pytest.raises(IntegrityError):
        user_a.manager = user_b  # Should fail

# Test 3: Constraint validation
def test_contractor_requires_vendor():
    with pytest.raises(IntegrityError):
        User(employment_governance='contractor', vendor_organization_id=None)
```

**Architect Decision**:
- [ ] Tests required before approval? YES / NO
- [ ] Minimum coverage threshold? ___%

---

## ✅ Section 7: Operational Readiness

### 7.1 Monitoring & Observability

**Questions**:
- ❓ How do we monitor trigger execution time?
- ❓ How do we detect circular references in production?
- ❓ How do we alert on deep hierarchies?
- ❓ How do we track array growth over time?

**Recommended Metrics**:
```sql
-- Average reporting chain depth
SELECT AVG(array_length(full_reporting_chain, 1)) FROM users;

-- Max hierarchy depth
SELECT MAX(array_length(full_corporate_hierarchy, 1)) FROM organizations;

-- Trigger execution time (requires logging)
SELECT pg_stat_statements WHERE query LIKE '%reporting_chain%';
```

**Red Flags**:
- ⚠️ No monitoring for trigger failures
- ⚠️ No alerting for data anomalies
- ⚠️ No visibility into performance degradation

---

### 7.2 Runbook & Procedures

**Required Documentation**:
- [ ] How to backfill arrays for existing data
- [ ] How to fix circular references if detected
- [ ] How to rollback migrations in production
- [ ] How to rebuild triggers if corrupted
- [ ] How to handle trigger timeouts

**Example Runbook**:
```markdown
## Procedure: Fix Circular Manager Reference

**Symptoms**: User reporting chain appears to loop

**Diagnosis**:
1. Identify affected user: SELECT * FROM users WHERE ...
2. Check manager chain: SELECT full_reporting_chain FROM users WHERE id = $uuid

**Resolution**:
1. Break circular reference: UPDATE users SET manager_id = NULL WHERE id = $uuid
2. Rebuild reporting chains: SELECT update_user_reporting_chain() FROM users
3. Verify: Check full_reporting_chain is correct

**Prevention**: CHECK constraint should prevent this; investigate why it didn't fire
```

---

## Summary: Architect Decision Matrix

**For Each Item, Mark**: ✅ Approve | ⚠️ Concern | ❌ Block

| Category | Item | Decision |
|----------|------|----------|
| **Schema** | Trigger-maintained arrays | ___ |
| **Schema** | CHECK constraints for business rules | ___ |
| **Schema** | 30+ indexes added | ___ |
| **Performance** | Not load tested | ___ |
| **Performance** | Trigger execution time unknown | ___ |
| **Performance** | Concurrent update behavior unknown | ___ |
| **Data Model** | Denormalization justified | ___ |
| **Data Model** | Relationship complexity acceptable | ___ |
| **Testing** | No unit tests for triggers | ___ |
| **Testing** | No integration tests | ___ |
| **Testing** | No migration rollback tests | ___ |
| **Operations** | No backfill strategy defined | ___ |
| **Operations** | No monitoring plan | ___ |
| **Operations** | No runbook procedures | ___ |
| **Product** | No validated customer requirements | ___ |
| **Product** | Built before roadmap confirmation | ___ |

---

## Final Recommendation

**Overall Assessment**:
- [ ] ✅ **APPROVE** - Ready for production
- [ ] ⚠️ **CONDITIONAL** - Approve with modifications
- [ ] 🟠 **REVISE** - Significant changes required
- [ ] ❌ **REJECT** - Rollback and restart

**Required Actions Before Approval**:
1. ___________________________________
2. ___________________________________
3. ___________________________________

**Estimated Effort for Required Actions**: ___ hours/days

**Architect Signature**: ___________________
**Date**: ___________________

---

**Questions? Contact**: [Your contact information]
