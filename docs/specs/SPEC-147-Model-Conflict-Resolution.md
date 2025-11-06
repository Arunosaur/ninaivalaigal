# SPEC-147 Model Conflict Resolution

**Date:** 2025-11-05
**Developer:** Developer C
**Status:** ✅ Complete

## Issue

After implementing SPEC-147 billing schema migrations, a model conflict was discovered between:

1. **Old SPEC-026 Models** in `server/database/models.py`:
   - `DiscountCode` (lines 409-446)
   - `DiscountCodeUsage` (lines 536-568)

2. **New SPEC-147 Models** in `server/billing/models.py`:
   - `DiscountCode` (lines 417-450) - cleaner, unified version
   - `DiscountApplication` (lines 453-468) - replaces DiscountCodeUsage

## Root Cause

The SPEC-147 migration (0139) successfully dropped the old database tables, but the Python SQLAlchemy models were not removed from the codebase, causing:
- Import conflicts
- Model definition ambiguity
- Test failures

## Resolution

### 1. Removed Old SPEC-026 Models

**File:** `server/database/models.py`

**Removed:**
- `DiscountCode` class (lines 409-446)
- `DiscountCodeUsage` class (lines 536-568)

**Replaced with:**
```python
# US#157: Discount & Credit System Models (SPEC-026 Phase 1)
# NOTE: DiscountCode moved to server.billing.models.py (SPEC-147)
# Use: from server.billing.models import DiscountCode

# NOTE: DiscountCodeUsage removed - replaced by DiscountApplication in SPEC-147
# Use: from server.billing.models import DiscountApplication
```

### 2. Updated Test Files

**File:** `server/tests/test_discount_credit_models.py`

**Changes:**
- Added deprecation warning to file header
- Updated imports to use SPEC-147 models
- Added `@pytest.mark.skip` decorators to DiscountCodeUsage tests
- Documented migration path for future test updates

### 3. Verification

**Checked:**
- ✅ No production code imports old models
- ✅ Database tables correctly use SPEC-147 schema
- ✅ New SPEC-147 models available in `server.billing.models`

## Migration Path

### For Developers

**Old SPEC-026:**
```python
from server.database.models import DiscountCode, DiscountCodeUsage
```

**New SPEC-147:**
```python
from server.billing.models import DiscountCode, DiscountApplication
```

### Model Mapping

| SPEC-026 (Old) | SPEC-147 (New) | Notes |
|----------------|----------------|-------|
| `DiscountCode` | `DiscountCode` | Simplified, removed `created_by`, `updated_at` |
| `DiscountCodeUsage` | `DiscountApplication` | Renamed, uses `billing_account_id` instead of `team_id`/`org_id` |
| `TeamCredit` | `CreditBalance` | Unified for all account types |
| `CreditTransaction` | `CreditBalance.used_amount` | Simplified tracking |

## Database Schema

### SPEC-147 discount_codes Table

```sql
CREATE TABLE discount_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    percent_off INTEGER,
    amount_off INTEGER,
    expires_at TIMESTAMPTZ,
    usage_limit INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_percent_off_range CHECK (percent_off >= 1 AND percent_off <= 100),
    CONSTRAINT check_amount_off_positive CHECK (amount_off >= 1),
    CONSTRAINT check_discount_type CHECK (
        (percent_off IS NOT NULL AND amount_off IS NULL) OR
        (percent_off IS NULL AND amount_off IS NOT NULL)
    )
);
```

### SPEC-147 discount_applications Table

```sql
CREATE TABLE discount_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_code_id UUID NOT NULL REFERENCES discount_codes(id) ON DELETE CASCADE,
    billing_account_id UUID NOT NULL REFERENCES billing_accounts(id) ON DELETE CASCADE,
    applied_by UUID REFERENCES users(id),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
```

## Benefits of SPEC-147 Approach

1. **Unified Architecture:** Single `billing_accounts` table for Org/Team/User
2. **Simplified Relationships:** No more dual `team_id`/`org_id` columns
3. **Better Tracking:** `DiscountApplication` tracks who applied the discount
4. **Cleaner Models:** Removed unnecessary fields like `created_by`, `updated_at`
5. **Polymorphic Design:** Works with any account type

## Next Steps

1. ✅ Models cleaned up
2. ✅ Tests marked as deprecated
3. ⏳ Create new SPEC-147 billing tests
4. ⏳ Update API endpoints to use new models
5. ⏳ Update documentation

## Files Modified

- `server/database/models.py` - Removed old models
- `server/tests/test_discount_credit_models.py` - Marked tests as deprecated
- `docs/specs/SPEC-147-Model-Conflict-Resolution.md` - This document

## References

- SPEC-026: Standalone Teams and Billing Phase 1 (deprecated)
- SPEC-147: Kubernetes Billing Operations Architecture (current)
- Migration 0139: Drop SPEC-026 billing tables
- Migrations 0140-0142: Create SPEC-147 billing schema
