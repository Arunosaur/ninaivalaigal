# US#79 - Technical Decision Records
## Enterprise Intelligence System Implementation

**Format**: Lightweight Architecture Decision Records (ADRs)
**Date**: October 23, 2025
**Status**: 🟡 PENDING ARCHITECT REVIEW

---

## ADR-001: Trigger-Maintained Hierarchy Arrays

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

We need to efficiently query organizational hierarchies:
- User reporting chains (manager → manager → CEO)
- Corporate structures (subsidiary → parent → root company)
- Team lineages (sub-team → parent team → root team)

Traditional approaches:
1. **Recursive CTEs**: Compute on-the-fly for every query
2. **Application Logic**: Maintain arrays in code
3. **Database Triggers**: Auto-maintain arrays in database

### Decision

**Chosen**: Database triggers to auto-maintain UUID arrays

**Implementation**:
```sql
-- Example: users.full_reporting_chain
CREATE TRIGGER trg_update_user_reporting_chain
BEFORE INSERT OR UPDATE OF manager_id ON users
FOR EACH ROW
EXECUTE FUNCTION update_user_reporting_chain();
```

**Reasoning**:
- ✅ O(1) lookups for ancestry queries
- ✅ Cannot be forgotten (always consistent)
- ✅ No application code changes needed
- ✅ GIN indexes enable fast array containment queries

**Trade-offs Accepted**:
- ⚠️ Increased complexity (triggers harder to debug)
- ⚠️ Update overhead (trigger fires on every parent change)
- ⚠️ Backfill challenge (existing data is NULL)
- ⚠️ Max depth limit needed (20 levels hardcoded)

### Alternatives Considered

**Alternative 1: Recursive CTEs**
```sql
WITH RECURSIVE reporting_chain AS (
    SELECT id, manager_id, ARRAY[id] AS chain
    FROM users WHERE id = $user_id
    UNION ALL
    SELECT u.id, u.manager_id, rc.chain || u.id
    FROM users u
    JOIN reporting_chain rc ON rc.manager_id = u.id
)
SELECT chain FROM reporting_chain WHERE manager_id IS NULL;
```
- ❌ Slower for frequent queries
- ✅ No storage overhead
- ✅ Always correct (no sync issues)

**Alternative 2: Application-Maintained**
```python
def update_user_manager(user, new_manager):
    user.manager = new_manager
    user.full_reporting_chain = compute_chain(user)
    db.session.commit()
```
- ❌ Easy to forget
- ❌ Can become inconsistent
- ✅ Easier to debug

**Alternative 3: Materialized View**
```sql
CREATE MATERIALIZED VIEW user_reporting_chains AS
WITH RECURSIVE ... ;
REFRESH MATERIALIZED VIEW user_reporting_chains;
```
- ❌ Requires periodic refresh
- ❌ Data may be stale
- ✅ Simple logic

### Consequences

**Positive**:
- Fast org chart queries
- Guaranteed consistency
- Enables new query patterns (e.g., "all users under VP X")

**Negative**:
- Debugging complexity
- Backfill requirement for existing data
- Performance risk for deep hierarchies

**Risks**:
- Circular references could cause infinite loops (mitigated by max depth + CHECK constraints)
- Concurrent updates could cause deadlocks (needs testing)
- Array size could exceed PostgreSQL limits (1GB per field)

### Validation Criteria

- [ ] Trigger execution < 100ms for typical hierarchy (5 levels)
- [ ] No deadlocks under concurrent updates
- [ ] Max depth limit prevents infinite loops
- [ ] Backfill strategy for existing data

### Architect Review Questions

1. Is trigger complexity acceptable given performance benefits?
2. Should we implement alternative 1 (recursive CTEs) instead?
3. Is there a hybrid approach (triggers for common case, CTEs for edge cases)?

---

## ADR-002: CHECK Constraints for Business Rules

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

Business rules need to be enforced:
- "Contractors must have a vendor organization"
- "Acquired entities must have source organization"
- "Users cannot manage themselves"
- "Status values must be from allowed enum"

Where to enforce:
1. **Application Layer**: Validate in Python/API code
2. **Database Layer**: CHECK constraints
3. **Both Layers**: Defense in depth

### Decision

**Chosen**: Database CHECK constraints + application validation

**Implementation**:
```sql
-- Example: Contractor validation
ALTER TABLE users ADD CONSTRAINT chk_users_contractor_vendor
CHECK (employment_governance != 'contractor' OR vendor_organization_id IS NOT NULL);

-- Example: Enum validation
ALTER TABLE users ADD CONSTRAINT chk_users_valid_employment_status
CHECK (employment_status IN ('active', 'on_leave', 'offboarded', 'alumni', 'contractor_expired'));
```

**Reasoning**:
- ✅ Cannot be bypassed (even via raw SQL)
- ✅ Guarantees data integrity at source
- ✅ Self-documenting (constraints show rules)
- ✅ Works across all applications

**Trade-offs Accepted**:
- ⚠️ Business logic split between database and application
- ⚠️ Harder to change rules (requires migration)
- ⚠️ Less flexible error messaging

### Alternatives Considered

**Alternative 1: Application-Only Validation**
```python
def create_user(data):
    if data['employment_governance'] == 'contractor':
        if not data.get('vendor_organization_id'):
            raise ValueError("Contractors require vendor")
```
- ❌ Can be bypassed (direct SQL, admin tools)
- ✅ Easier to change
- ✅ Better error messages

**Alternative 2: Database-Only (No Application Validation)**
```python
# Just let database reject invalid data
try:
    user.save()
except IntegrityError as e:
    # Parse database error message
    raise ValidationError(str(e))
```
- ✅ Single source of truth
- ❌ Poor user experience (cryptic errors)
- ❌ No pre-validation

### Consequences

**Positive**:
- Bulletproof data integrity
- Self-documenting constraints
- Cross-application enforcement

**Negative**:
- Requires migration to change rules
- Less friendly error messages
- Business logic in two places

**Risks**:
- Over-constrained (blocks valid use cases we didn't anticipate)
- Under-constrained (missing edge cases)

### Validation Criteria

- [ ] All constraints have corresponding application validation
- [ ] Error messages are user-friendly
- [ ] Constraints don't block legitimate workflows
- [ ] Edge cases are tested

### Architect Review Questions

1. Is database + application validation acceptable duplication?
2. Should some rules be application-only for flexibility?
3. How do we handle rule changes in production?

---

## ADR-003: Comprehensive Provenance Tracking

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

Organizations evolve through:
- M&A (acquiring companies, being acquired)
- Restructuring (team mergers, splits)
- Employment changes (contractor → FTE, acquisitions)

Traditional approach:
- Simple `is_active` boolean
- Maybe `created_at` / `deleted_at` timestamps

Enterprise approach:
- Full provenance tracking
- Lifecycle management
- Historical audit trail

### Decision

**Chosen**: Comprehensive multi-dimensional provenance

**Scope**:
- **Organizations**: 6 dimensions (origin, status, lineage, metadata, type, structure)
- **Teams**: 6 dimensions (affiliation, origin, lineage, status, governance, hierarchy)
- **Users**: 4 dimensions + hierarchy (origin, status, type, governance, reporting chain)

**Reasoning**:
- ✅ Enables M&A integration tracking
- ✅ Supports contractor management
- ✅ Provides audit trail for compliance
- ✅ Enables org chart generation
- ✅ Alumni/rehire pool management

**Trade-offs Accepted**:
- ⚠️ High complexity (50+ columns added)
- ⚠️ Uncertain product-market fit
- ⚠️ Built before customer validation
- ⚠️ May be premature optimization

### Alternatives Considered

**Alternative 1: Minimal Approach**
```python
# Just add status field
status: Enum['active', 'inactive', 'deleted']
```
- ✅ Simple
- ✅ Fast to implement
- ❌ Doesn't support M&A tracking
- ❌ Doesn't support contractor expiration

**Alternative 2: External System Integration**
```python
# Integrate with existing HR system (Workday, BambooHR)
class User:
    hr_system_id: str  # Reference external system
```
- ✅ Don't rebuild what exists
- ✅ Single source of truth
- ❌ Tight coupling to external system
- ❌ No control over data model

**Alternative 3: Event Sourcing**
```python
# Store events, compute state
UserHired(user_id, date)
UserAcquired(user_id, from_org, date)
UserPromoted(user_id, new_role, date)
UserTerminated(user_id, date)
```
- ✅ Complete audit trail
- ✅ Time-travel queries
- ❌ High complexity
- ❌ Query performance challenges

**Alternative 4: Phased Rollout**
```python
# Phase 1: Basic status (now)
# Phase 2: M&A tracking (when needed)
# Phase 3: Full provenance (enterprise customers)
```
- ✅ Incremental complexity
- ✅ Validated with users
- ❌ Harder to backfill later
- ❌ Migration complexity

### Consequences

**Positive**:
- Ready for enterprise customers
- Complete organizational intelligence
- Competitive differentiator
- Compliance-ready

**Negative**:
- High upfront investment
- Uncertain ROI
- Increased maintenance burden
- Not validated with users

**Risks**:
- Built features nobody needs
- Complexity slows down future development
- Performance issues at scale

### Validation Criteria

- [ ] At least one customer requires M&A tracking
- [ ] Product roadmap includes org chart features
- [ ] Performance tested with 10K+ records
- [ ] Documented use cases for all dimensions

### Architect Review Questions

1. **Scope**: Should we have started minimal and iterated?
2. **Product**: Do we have validated customer needs for this?
3. **Alternatives**: Should we integrate with external HR systems instead?
4. **Phasing**: Can we hide complexity behind feature flags initially?

---

## ADR-004: GIN Indexes for Array Queries

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

With trigger-maintained hierarchy arrays, we need efficient queries:
```sql
-- Find all users under a specific VP
SELECT * FROM users WHERE $vp_uuid = ANY(full_reporting_chain);

-- Find all organizations in corporate group
SELECT * FROM organizations WHERE $root_uuid = ANY(full_corporate_hierarchy);
```

Standard B-tree indexes don't optimize array containment queries.

### Decision

**Chosen**: GIN (Generalized Inverted Index) for hierarchy arrays

**Implementation**:
```sql
CREATE INDEX ix_users_reporting_chain_gin
ON users USING GIN(full_reporting_chain);

CREATE INDEX ix_organizations_hierarchy_gin
ON organizations USING GIN(full_corporate_hierarchy);

CREATE INDEX ix_teams_lineage_path_gin
ON teams USING GIN(full_lineage_path);
```

**Reasoning**:
- ✅ Optimizes `ANY` / `@>` / `<@` array operators
- ✅ Fast containment checks (O(log n))
- ✅ PostgreSQL-native solution

**Trade-offs Accepted**:
- ⚠️ GIN indexes are larger than B-tree
- ⚠️ GIN updates are slower (INSERT/UPDATE overhead)
- ⚠️ PostgreSQL-specific (not portable)

### Alternatives Considered

**Alternative 1: No Special Index (B-tree Only)**
```sql
-- Query would require sequential scan
SELECT * FROM users WHERE $uuid = ANY(full_reporting_chain);
```
- ❌ Poor performance (seq scan)
- ✅ No additional storage overhead

**Alternative 2: Separate Lookup Table**
```sql
CREATE TABLE user_reporting_chain_lookup (
    user_id UUID,
    ancestor_id UUID,
    depth INT
);
CREATE INDEX ON user_reporting_chain_lookup(ancestor_id);
```
- ✅ Standard B-tree index
- ✅ Database-agnostic
- ❌ Requires maintaining separate table
- ❌ More complex trigger logic

**Alternative 3: Recursive CTE (No Stored Data)**
```sql
-- Compute on-the-fly, no index needed
WITH RECURSIVE chain AS (...)
SELECT * FROM chain WHERE ...;
```
- ✅ No storage overhead
- ❌ Slower query performance

### Consequences

**Positive**:
- Fast array containment queries
- PostgreSQL-optimized solution
- Simple query syntax

**Negative**:
- Increased storage (GIN indexes are larger)
- Slower writes (GIN index updates)
- PostgreSQL lock-in

**Risks**:
- GIN index size exceeds table size
- Write performance degradation
- Not portable to other databases

### Validation Criteria

- [ ] Array queries use GIN index (verify with EXPLAIN)
- [ ] Query performance < 50ms for 10K records
- [ ] GIN index size < 2x array column size
- [ ] Write performance acceptable (< 20% degradation)

### Architect Review Questions

1. Is PostgreSQL lock-in acceptable?
2. Should we use alternative 2 (lookup table) for portability?
3. What's the storage overhead budget?

---

## ADR-005: Six Database Migrations Instead of One

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

Original task was to fix one SQLAlchemy relationship. Implementation resulted in 6 migrations over the course of development:

1. `0115_user_columns` - Missing User fields
2. `0116_teams_org_id` - Team organizational affiliation
3. `0117_team_provenance` - Team M&A tracking
4. `0118_team_intelligence` - Team status/governance + triggers
5. `0119_user_provenance` - User employment intelligence + triggers
6. `0120_org_provenance` - Organization corporate structure + triggers

### Decision

**Chosen**: Keep as 6 separate migrations

**Reasoning**:
- ✅ Logical grouping by entity
- ✅ Easier to rollback incrementally
- ✅ Clear progression of features
- ✅ Each migration is self-contained

**Trade-offs Accepted**:
- ⚠️ Migration sprawl (many files)
- ⚠️ Longer migration history
- ⚠️ More complex rollback testing

### Alternatives Considered

**Alternative 1: Consolidate into 1 Migration**
```python
# One big migration with all changes
def upgrade():
    # Add User columns
    # Add Team columns
    # Add Organization columns
    # Add all triggers
    # Add all constraints
```
- ✅ Simpler migration history
- ✅ Atomic deployment
- ❌ Harder to rollback partially
- ❌ Harder to review

**Alternative 2: Consolidate by Layer (3 Migrations)**
```python
# Migration 1: Schema changes only
# Migration 2: Triggers only
# Migration 3: Constraints only
```
- ✅ Logical separation by type
- ⚠️ Still fewer than 6
- ❌ Mixed entity changes

### Consequences

**Positive**:
- Clear audit trail of what was added when
- Can rollback team changes without affecting users
- Easier code review (smaller diffs)

**Negative**:
- Migration sprawl
- Rollback requires 6 steps
- Testing burden (6 up/down cycles)

**Risks**:
- Missed dependencies between migrations
- Incomplete rollback (only rolling back some migrations)

### Validation Criteria

- [ ] Each migration can be rolled back independently
- [ ] Migrations tested in sequence (1 → 6)
- [ ] Migrations tested in reverse (6 → 1)
- [ ] No orphaned triggers after partial rollback

### Architect Review Questions

1. Should we consolidate migrations before merging?
2. Is 6 migrations acceptable for this change?
3. What's the migration file limit per PR?

---

## ADR-006: JSON vs. Separate Tables for Metadata

**Status**: Proposed
**Deciders**: Development Team
**Date**: 2025-10-23

### Context

Need to store flexible metadata:
```python
# Employment metadata
{
    "original_company": "TechCorp Inc.",
    "retention_bonus": True,
    "visa_status": "H1B",
    "cost_center": "ENG-001"
}

# Corporate metadata
{
    "stock_ticker": "MEGA",
    "board_size": 9,
    "funding_rounds": [...]
}
```

Options:
1. **JSON column**: Flexible, schemaless
2. **Separate tables**: Normalized, queryable
3. **EAV pattern**: Entity-Attribute-Value tables

### Decision

**Chosen**: JSON columns for metadata

**Fields**:
- `users.employment_metadata: JSON`
- `teams.provenance_metadata: JSON`
- `organizations.corporate_metadata: JSON`

**Reasoning**:
- ✅ Flexible schema (add fields without migration)
- ✅ Simpler queries (one table)
- ✅ PostgreSQL has good JSON support (JSONB, GIN indexes)
- ✅ Appropriate for rarely-queried data

**Trade-offs Accepted**:
- ⚠️ Not strongly typed
- ⚠️ Harder to query specific fields
- ⚠️ No referential integrity on JSON values

### Alternatives Considered

**Alternative 1: Separate Tables**
```sql
CREATE TABLE user_employment_metadata (
    user_id UUID,
    key VARCHAR,
    value VARCHAR
);
```
- ✅ Strongly typed
- ✅ Queryable
- ❌ Requires migration for new fields
- ❌ Complex joins

**Alternative 2: Dedicated Columns**
```sql
ALTER TABLE users ADD COLUMN retention_bonus BOOLEAN;
ALTER TABLE users ADD COLUMN visa_status VARCHAR(50);
...
```
- ✅ Strongly typed
- ✅ Indexed
- ❌ Schema bloat
- ❌ Migration for every new field

### Consequences

**Positive**:
- Can add metadata without migrations
- Keeps core schema clean
- Future-proof

**Negative**:
- Less type safety
- Harder to query specific metadata fields
- JSON validation at application layer only

### Validation Criteria

- [ ] JSON validation in application code
- [ ] JSON schema defined somewhere
- [ ] Examples of common metadata patterns
- [ ] Size limits on JSON fields (prevent abuse)

### Architect Review Questions

1. Is JSON acceptable for this use case?
2. Should we define JSON schemas for validation?
3. What's the size limit for JSON fields?

---

## Summary: Decisions Requiring Architect Review

| ADR | Decision | Risk Level | Block/Concern |
|-----|----------|------------|---------------|
| ADR-001 | Trigger-maintained arrays | 🔴 HIGH | _______ |
| ADR-002 | CHECK constraints | 🟡 MEDIUM | _______ |
| ADR-003 | Comprehensive provenance | 🔴 HIGH | _______ |
| ADR-004 | GIN indexes | 🟢 LOW | _______ |
| ADR-005 | Six migrations | 🟡 MEDIUM | _______ |
| ADR-006 | JSON metadata | 🟢 LOW | _______ |

**Legend**:
- ✅ Approve
- ⚠️ Approve with modifications
- ❌ Reject / Needs alternative

---

## Architect Sign-Off

**Overall Decision**:
- [ ] ✅ Approve all decisions
- [ ] ⚠️ Approve with modifications (list below)
- [ ] ❌ Reject - alternative approach required

**Modifications Required**:
1. ___________________________________
2. ___________________________________
3. ___________________________________

**Signature**: ___________________
**Date**: ___________________
