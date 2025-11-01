# US#243: Remove Legacy Code - Execution Plan

**Date**: 2025-01-27
**Story**: US#243 - Remove Legacy Code and Deploy to Production
**Status**: In Progress
**Dependencies**: US#237-242 (✅ Complete)

---

## Current Status

✅ **Completed Work** (US#237-242):
- Shared `InvoicingService` module created (400+ lines)
- Shared `TaxCalculator` module created (200+ lines)
- SPEC-027 refactored to use shared services
- SPEC-028 refactored to use shared services
- Test suite created (90+ tests)
- Feature flag `USE_INVOICING_SERVICE` implemented (default: `false`)

⏳ **Pending Work** (US#243):
- Remove legacy code from SPEC-027
- Remove legacy code from SPEC-028
- Remove feature flag checks (always use shared service)
- Enable feature flag by default

---

## Legacy Code to Remove

### SPEC-027 (`billing_engine_integration_api.py`)

#### Function: `calculate_tax_amount()` (lines 162-188)
- **Status**: DEPRECATED, uses feature flag
- **Legacy Implementation**: Lines 178-188
- **Action**: Remove entire function, update all callers

#### Function: `generate_invoice_pdf()` (lines 191-291)
- **Status**: DEPRECATED, uses feature flag
- **Legacy Implementation**: Lines 224-291 (~67 lines of ReportLab code)
- **Action**: Remove entire function, update all callers

### SPEC-028 (`invoice_management_api.py`)

#### Function: `calculate_tax()` (lines 145-167)
- **Status**: DEPRECATED, uses feature flag
- **Legacy Implementation**: Lines 160-166
- **Action**: Remove entire function, update all callers

#### Function: `create_pdf_invoice()` (lines 176-357)
- **Status**: DEPRECATED, uses feature flag
- **Legacy Implementation**: Lines 222-357 (~135 lines of ReportLab code)
- **Action**: Remove entire function, update all callers

---

## Execution Plan

### Phase 1: Pre-removal Validation ✅

1. **Verify Test Suite**
   ```bash
   pytest server/tests/services/ server/tests/integration/ -v
   ```
   - Expected: All 90+ tests pass

2. **Run PDF Comparison Script**
   ```bash
   python scripts/compare_invoice_pdfs.py --count 100
   ```
   - Expected: SHA256 hashes match (or acceptable differences documented)

3. **Enable Feature Flag in Development**
   ```bash
   export USE_INVOICING_SERVICE=true
   ```
   - Test all invoice generation endpoints
   - Verify no errors in logs

### Phase 2: Remove Legacy Functions

1. **Remove from SPEC-027**:
   - Delete `calculate_tax_amount()` function
   - Delete `generate_invoice_pdf()` function
   - Update all callers to use shared services directly

2. **Remove from SPEC-028**:
   - Delete `calculate_tax()` function
   - Delete `create_pdf_invoice()` function
   - Update all callers to use shared services directly

### Phase 3: Remove Feature Flag Logic

1. **Remove Feature Flag Checks**:
   - Remove `USE_INVOICING_SERVICE` environment variable checks
   - Remove conditional initialization (`if USE_INVOICING_SERVICE else None`)
   - Always initialize shared services

2. **Update Configuration**:
   - Change `USE_INVOICING_SERVICE="false"` to `USE_INVOICING_SERVICE="true"` in `defaults.env`
   - Remove feature flag documentation (no longer needed)

### Phase 4: Cleanup & Documentation

1. **Remove Unused Imports**:
   - Remove ReportLab imports from SPEC-027/028 if no longer needed
   - Clean up unused helper functions

2. **Update Documentation**:
   - Update SPEC-027 and SPEC-028 spec.md files
   - Update API documentation
   - Update CHANGELOG.md

3. **Final Validation**:
   - Run full test suite
   - Verify no linting errors
   - Verify code coverage maintained

---

## Expected Code Reduction

- **SPEC-027**: ~67 lines removed (legacy PDF generation)
- **SPEC-028**: ~135 lines removed (legacy PDF generation)
- **Tax Calculation**: ~10 lines per file (~20 lines total)
- **Feature Flag Logic**: ~15 lines per file (~30 lines total)

**Total Reduction**: ~252 lines of duplicate/legacy code

---

## Risk Mitigation

1. **Backward Compatibility**:
   - ✅ Shared services handle all use cases
   - ✅ Test suite validates compatibility

2. **Rollback Plan**:
   - Keep this branch until production validation complete
   - Feature flag could be re-added if needed (unlikely)

3. **Production Deployment**:
   - Deploy to staging first
   - Monitor for 24 hours
   - Gradual rollout (10% → 50% → 100%)

---

## Acceptance Criteria

- ✅ Legacy functions removed
- ✅ All callers updated to use shared services
- ✅ Feature flag removed (always use shared service)
- ✅ Test suite passes (90+ tests)
- ✅ No linting errors
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

---

## Next Steps

1. Review and approve this plan
2. Execute Phase 1 (Validation)
3. Execute Phase 2 (Remove Legacy Functions)
4. Execute Phase 3 (Remove Feature Flag)
5. Execute Phase 4 (Cleanup)
6. Deploy to staging
7. Monitor and validate
8. Deploy to production
