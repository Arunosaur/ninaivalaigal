# SPEC-074 Database Migration Created

**Date**: November 2, 2025
**Status**: ✅ **Migration & Models Complete**

---

## 📋 Summary

Alembic migration and SQLAlchemy models have been created for GDPR compliance tables in the `public` schema. The database structure is ready for Phase 1 implementation.

---

## ✅ Files Created

### 1. Alembic Migration ✅

**File**: `alembic/versions/0127_spec074_gdpr_compliance_schema.py`

**Revision**: `0127_spec074_gdpr_compliance_schema`
**Revises**: `0126_spec026_team_billing_schema`
**Schema**: `public` (default)

**Tables Created**:

1. **`public.data_subject_requests`**
   - GDPR data subject requests (DSAR, erasure, portability, etc.)
   - Links to `public.users(id)`
   - Indexes on `user_id`, `status`, `request_type`, `created_at`

2. **`public.data_exports`**
   - Encrypted export tracking
   - Links to `public.users(id)` and `data_subject_requests(id)`
   - Indexes on `user_id`, `request_id`, `status`, `expires_at`

**Features**:
- ✅ UUID primary keys with `gen_random_uuid()`
- ✅ Foreign keys with CASCADE delete
- ✅ CHECK constraints for data integrity
- ✅ Performance indexes on key columns
- ✅ Auto-updating `updated_at` triggers
- ✅ Comprehensive comments documenting GDPR articles

### 2. SQLAlchemy Models ✅

**File**: `server/compliance/models.py`

**Models**:

1. **`DataSubjectRequest`**
   - Maps to `public.data_subject_requests`
   - Relationships: `user`, `exports`
   - Enums: `DataSubjectRequestType`, `RequestStatus`

2. **`DataExport`**
   - Maps to `public.data_exports`
   - Relationships: `user`, `request`
   - Enums: `ExportFormat`, `ExportStatus`

**Enums Exported**:
- `DataSubjectRequestType` - Request types (access, erasure, etc.)
- `RequestStatus` - Request status (pending, completed, etc.)
- `ExportFormat` - Export formats (json, xml, csv)
- `ExportStatus` - Export status (pending, ready, etc.)

### 3. Updated Compliance Modules ✅

**Updated Files**:
- `server/compliance/gdpr.py` - Integrated with SQLAlchemy models
- `server/compliance/export.py` - Integrated with SQLAlchemy models

**Changes**:
- Added `db_session` parameter to managers
- Implemented `get_request_status()` and `list_user_requests()`
- Implemented `get_export()` with database queries
- Removed duplicate enum definitions (now imported from models)

---

## 📊 Database Schema

### Table: `data_subject_requests`

```sql
CREATE TABLE public.data_subject_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    description TEXT,
    response_data JSONB,
    rejection_reason TEXT,
    retained_data_categories JSONB,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CHECK (request_type IN ('access', 'rectification', 'erasure', 'portability', 'restriction', 'objection')),
    CHECK (status IN ('pending', 'in_progress', 'completed', 'partial', 'rejected', 'expired'))
);
```

**Indexes**:
- `idx_data_subject_requests_user_id` - User lookup
- `idx_data_subject_requests_status` - Status filtering
- `idx_data_subject_requests_request_type` - Type filtering
- `idx_data_subject_requests_created_at` - Time-based queries
- `idx_data_subject_requests_user_status` - Composite (user + active status)

### Table: `data_exports`

```sql
CREATE TABLE public.data_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    request_id UUID REFERENCES public.data_subject_requests(id) ON DELETE SET NULL,
    format VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    download_url VARCHAR(500),
    encryption_key_id VARCHAR(255),
    file_size BIGINT,
    expires_at TIMESTAMPTZ,
    downloaded_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CHECK (format IN ('json', 'xml', 'csv')),
    CHECK (status IN ('pending', 'generating', 'ready', 'expired', 'downloaded', 'failed')),
    CHECK (file_size >= 0 OR file_size IS NULL)
);
```

**Indexes**:
- `idx_data_exports_user_id` - User lookup
- `idx_data_exports_request_id` - Link to request
- `idx_data_exports_status` - Status filtering
- `idx_data_exports_expires_at` - Expiry queries
- `idx_data_exports_user_status` - Composite (user + active status)

---

## 🔄 Migration Commands

### Apply Migration

```bash
cd server
alembic upgrade head
```

### Verify Migration

```bash
# Check tables exist
psql -d ninaivalaigal_dev -c "\dt public.data_*"

# Check indexes
psql -d ninaivalaigal_dev -c "\d data_subject_requests"
psql -d ninaivalaigal_dev -c "\d data_exports"

# Check foreign keys
psql -d ninaivalaigal_dev -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
    AND tc.table_name IN ('data_subject_requests', 'data_exports');
"
```

### Rollback Migration (if needed)

```bash
cd server
alembic downgrade -1
```

---

## ✅ Verification Checklist

- [x] Migration file created with proper revision chain
- [x] Tables created in `public` schema
- [x] Foreign keys to `public.users(id)`
- [x] CHECK constraints for data integrity
- [x] Performance indexes on key columns
- [x] Auto-updating `updated_at` triggers
- [x] SQLAlchemy models created
- [x] Enums defined in models
- [x] Relationships configured
- [x] Compliance modules updated to use models
- [x] No linter errors
- [x] Files compile successfully

---

## 🎯 Next Steps

1. **Apply Migration** (Priority 1)
   ```bash
   alembic upgrade head
   ```

2. **Test Database Integration** (Priority 2)
   - Create test requests via GDPR manager
   - Verify data persistence
   - Test relationships

3. **Implement DSAR Handler** (Priority 3)
   - Use `DataSubjectRequest` model
   - Persist requests to database
   - Link to `DataExport` when needed

4. **Implement Export Persistence** (Priority 4)
   - Use `DataExport` model
   - Save export records
   - Track status changes

---

## 📚 References

- `/docs/spec-analysis/SPEC_074_SCHEMA_ANALYSIS.md` - Schema decision
- `alembic/versions/0126_spec026_team_billing_schema.py` - Migration pattern
- `server/database/models.py` - Base model structure
- `specs/011-data-lifecycle-management/spec.md` - Related table definitions

---

**Migration Created**: November 2, 2025
**Status**: ✅ **Ready to Apply**
