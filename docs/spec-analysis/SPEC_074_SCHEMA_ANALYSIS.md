# SPEC-074 Schema Analysis: GDPR Compliance Tables

**Date**: November 2, 2025
**Status**: ✅ **Analysis Complete**

---

## 📋 Summary

After analyzing all existing schemas and migration patterns, **GDPR compliance tables should be created in the `public` schema**. This follows the established pattern for cross-domain infrastructure tables.

---

## 🏗️ Current Schema Architecture

Based on `/docs/DATABASE_SCHEMA_REFERENCE.md` and migration `0124_memory_schema`:

```
ninaivalaigal_dev (database)
├── public schema      → Core identity & cross-domain entities
│   ├── users          → User accounts (core identity)
│   ├── teams          → Team entities
│   ├── organizations  → Organization entities
│   ├── contexts       → Memory contexts
│   └── [billing tables] → SPEC-026 billing (migration 0126)
│
├── memory schema      → Memory persistence (owned by Memory Service)
│   ├── memory_records → Canonical memory storage
│   └── memory_tags    → Memory tagging
│
├── graph schema       → Graph intelligence (future)
├── billing schema     → Financial records (future - not yet created)
└── admin schema       → System monitoring (future)
```

---

## 🔍 Analysis Results

### 1. SPEC-011 Tables Pattern

**Location**: SPEC-011 spec defines these tables:
- `data_lifecycle_audits`
- `data_export_requests`
- `data_subject_requests` (for GDPR)

**Schema**: ❌ **No schema specified in CREATE TABLE statements**
- Defaults to `public` schema
- References `users(id)` which is in `public.users`
- Cross-domain infrastructure (not domain-specific)

**Evidence**:
```sql
-- From specs/011-data-lifecycle-management/spec.md
CREATE TABLE data_subject_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),  -- References public.users
    ...
);
-- No schema prefix = defaults to public
```

### 2. SPEC-026 Billing Tables Pattern

**Location**: Migration `0126_spec026_team_billing_schema.py`

**Schema**: `public` schema (no explicit schema specified)
- Uses `op.create_table()` without schema parameter
- Tables: `team_billing`, `team_subscriptions`, `discount_codes`, etc.
- Also references `public.teams(id)`

### 3. Schema Ownership Principles

From migration `0124_memory_schema`:
- **`public` schema**: Core identity & cross-domain entities
- **`memory` schema**: Domain-specific (Memory Service owned)
- **Cross-domain**: Goes in `public`
- **Domain-specific**: Gets own schema

---

## ✅ Decision: `public` Schema

### Why `public` Schema?

1. **Cross-Domain Requirement** ✅
   - GDPR affects users, memories, billing, contexts
   - Not owned by a single domain service
   - Core infrastructure similar to users/teams

2. **References Core Identity** ✅
   - Tables reference `public.users(id)`
   - Foreign keys to `public` schema entities
   - Logical grouping with other user-related tables

3. **Follows Existing Pattern** ✅
   - SPEC-011 tables (`data_subject_requests`) use `public`
   - SPEC-026 billing tables use `public` (for now)
   - Audit/security tables typically in `public`

4. **No Domain Ownership** ✅
   - Not owned by Memory Service (Rust)
   - Not owned by Graph Service
   - Not owned by Business Service
   - **Core API (Python) owns GDPR compliance** → `public` schema

---

## 📊 Tables to Create in `public` Schema

### Required Tables

1. **`public.data_subject_requests`**
   ```sql
   CREATE TABLE public.data_subject_requests (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
       request_type VARCHAR(50) NOT NULL,
       status VARCHAR(50) DEFAULT 'pending',
       description TEXT,
       response_data JSONB,
       completed_at TIMESTAMPTZ,
       created_at TIMESTAMPTZ DEFAULT NOW(),
       ...
   );
   ```

2. **`public.data_exports`**
   ```sql
   CREATE TABLE public.data_exports (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
       format VARCHAR(50) NOT NULL,
       status VARCHAR(50) DEFAULT 'pending',
       download_url VARCHAR(500),
       encryption_key_id VARCHAR(255),
       expires_at TIMESTAMPTZ,
       file_size BIGINT,
       created_at TIMESTAMPTZ DEFAULT NOW(),
       ...
   );
   ```

### Optional (Future)

3. **`public.data_processing_records`** (Article 30)
4. **`public.consent_history`** (GDPR-compliant)
5. **`public.data_breach_notifications`** (Article 33/34)

---

## 🔗 Cross-Schema Foreign Keys

Following migration `0124` pattern, **all cross-schema FKs must be fully qualified**:

```sql
-- ✅ CORRECT
user_id UUID REFERENCES public.users(id) ON DELETE CASCADE

-- ❌ WRONG
user_id UUID REFERENCES users(id)
```

**For GDPR compliance:**
- All tables in `public` schema
- FKs to `public.users(id)` → use `public.users`
- FKs to `public.teams(id)` → use `public.teams` (if needed)
- **No cross-schema FKs needed** (all in `public`)

---

## 📝 Migration Structure

### Alembic Migration File

**File**: `alembic/versions/0127_spec074_gdpr_compliance_schema.py`

**Revision**: `0127_spec074_gdpr_compliance_schema`
**Revises**: `0126_spec026_team_billing_schema`

**Schema**: `public` (default, no schema parameter needed)

```python
def upgrade():
    """Create GDPR compliance tables in public schema."""

    # Table 1: Data Subject Requests
    op.create_table(
        "data_subject_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, ...),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ...), ...),
        ...
    )

    # Table 2: Data Exports
    op.create_table(
        "data_exports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, ...),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ...), ...),
        ...
    )

    # Indexes
    op.create_index("idx_data_subject_requests_user_id", "data_subject_requests", ["user_id"])
    op.create_index("idx_data_exports_user_id", "data_exports", ["user_id"])
    ...
```

---

## ✅ Verification Checklist

- [x] Analyzed all existing schemas (`public`, `memory`)
- [x] Reviewed SPEC-011 table patterns
- [x] Reviewed SPEC-026 billing migration pattern
- [x] Confirmed schema ownership principles
- [x] Verified FK reference patterns
- [x] Determined appropriate schema: **`public`**

---

## 🎯 Next Steps

1. **Create Alembic Migration** (Priority 1)
   - File: `alembic/versions/0127_spec074_gdpr_compliance_schema.py`
   - Tables: `data_subject_requests`, `data_exports`
   - Indexes: User ID, status, created_at
   - Schema: `public` (default)

2. **Create SQLAlchemy Models** (Priority 2)
   - File: `server/compliance/models.py`
   - Models: `DataSubjectRequest`, `DataExport`
   - Use `public` schema (default)

3. **Update GDPR Manager** (Priority 3)
   - Integrate with database models
   - Use fully-qualified table names if needed

---

## 📚 References

- `/docs/DATABASE_SCHEMA_REFERENCE.md` - Schema architecture
- `alembic/versions/0124_memory_schema.py` - Schema separation pattern
- `alembic/versions/0126_spec026_team_billing_schema.py` - Billing tables pattern
- `specs/011-data-lifecycle-management/spec.md` - SPEC-011 table definitions
- `specs/019-database-management-migration/spec.md` - Database architecture principles

---

**Analysis Completed**: November 2, 2025
**Decision**: ✅ **Use `public` schema for all GDPR compliance tables**
