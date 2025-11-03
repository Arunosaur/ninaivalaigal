# SPEC-027/028 Refactoring - Implementation Checklist

**Status**: ✅ **APPROVED** - Ready for Implementation
**Date**: October 31, 2025
**Estimated**: 2-3 days
**Developer**: TBD

---

## ✅ Approval Summary

**Verdict**: Plan is **technically sound and operationally feasible**

**Strengths Noted**:
- ✅ Excellent separation of concerns (Billing → creates, InvoiceService → renders, Management → consumes)
- ✅ Feature-flag rollback strategy for revenue-critical path
- ✅ Quantified success metrics (LOC reduction, test coverage, perf budgets)
- ✅ Comprehensive testing matrix (unit + integration + visual + performance)
- ✅ Gradual rollout with PDF diff comparison
- ✅ Business-aligned benefits (compliance, brand consistency, maintainability)

---

## 🌱 Refinements to Incorporate

### 1. Module Naming

**Recommendation**: Use `invoicing_service.py` (noun form) instead of `invoice_service.py`

**Rationale**: Mirrors "billing_engine" naming pattern, keeps future naming consistent

**Action**:
- [ ] Rename to `server/services/invoicing_service.py`
- [ ] Update all imports to use `InvoicingService`

---

### 2. Dependency Injection

**Recommendation**: Let `InvoicingService` accept optional injected `TaxCalculator` and `Mailer`

**Rationale**: Easier unit testing and mocking

**Before**:
```python
class InvoicingService:
    def __init__(self, db: Session):
        self.db = db
        self.tax_calculator = TaxCalculator(db)  # Hard-coded dependency
```

**After**:
```python
class InvoicingService:
    def __init__(
        self,
        db: Session,
        tax_calculator: Optional[TaxCalculator] = None,
        mailer: Optional[Mailer] = None
    ):
        self.db = db
        self.tax_calculator = tax_calculator or TaxCalculator(db)
        self.mailer = mailer or Mailer()
```

**Action**:
- [ ] Add optional dependency injection to `__init__`
- [ ] Update tests to inject mocks

---

### 3. Config & Branding

**Recommendation**: Move `BrandingConfig` to `config/branding.py` or database table

**Rationale**: Allows admin-panel updates without code changes

**Options**:
1. **Config file**: `config/branding.py` or `config/branding.yaml`
2. **Database table**: `branding_settings` (team_id → logo_url, colors, etc.)

**Action**:
- [ ] Create `database/schemas/branding_settings.sql` table
- [ ] Add CRUD endpoints for branding in admin API
- [ ] Load branding from database in `InvoicingService`

---

### 4. PDF Composition

**Recommendation**: Replace low-level ReportLab with Platypus templates or HTML→PDF renderer

**Options**:
1. **Platypus templates** (ReportLab's high-level API)
2. **WeasyPrint** (HTML/CSS → PDF)
3. **xhtml2pdf** (simpler HTML → PDF)

**Rationale**: Easier to style and localize, separates content from presentation

**Phase 1** (Current refactoring):
- [ ] Keep ReportLab (use SPEC-028's implementation)
- [ ] Document as technical debt

**Phase 2** (Future enhancement):
- [ ] Evaluate WeasyPrint for HTML→PDF
- [ ] Create invoice.html Jinja2 template
- [ ] Switch PDF renderer without changing API

---

### 5. Caching Layer

**Recommendation**: Add simple LRU or Redis cache in `TaxCalculator._get_tax_rate()`

**Rationale**: Prevent repetitive lookups for same jurisdiction

**Implementation**:
```python
from functools import lru_cache

class TaxCalculator:
    @lru_cache(maxsize=128)
    def _get_tax_rate(self, jurisdiction: str) -> Decimal:
        """Get tax rate for jurisdiction (cached)"""
        # Cache prevents DB lookup on every invoice
```

**Action**:
- [ ] Add `@lru_cache` decorator to `_get_tax_rate()`
- [ ] Add cache invalidation on tax rate updates
- [ ] Monitor cache hit rate

---

### 6. Observability

**Recommendation**: Add structured logs for `generate_pdf` and `deliver_invoice`

**Implementation**:
```python
import structlog

logger = structlog.get_logger(__name__)

def generate_pdf(self, invoice_id: str, ...) -> bytes:
    logger.info(
        "invoice_pdf_generation_started",
        invoice_id=invoice_id,
        team_id=invoice.team_id
    )

    start_time = time.time()
    try:
        # Generate PDF
        pdf_bytes = ...

        logger.info(
            "invoice_pdf_generation_completed",
            invoice_id=invoice_id,
            duration_ms=int((time.time() - start_time) * 1000),
            pdf_size_bytes=len(pdf_bytes)
        )
        return pdf_bytes
    except Exception as e:
        logger.error(
            "invoice_pdf_generation_failed",
            invoice_id=invoice_id,
            error=str(e)
        )
        raise
```

**Action**:
- [ ] Add structured logging to all public methods
- [ ] Log: invoice_id, team_id, duration_ms, pdf_size_bytes, method (email/portal/download)
- [ ] Tie into SPEC-118 observability layer later

---

### 7. Testing - Snapshot Tests

**Recommendation**: Add snapshot tests for PDF byte equality

**Implementation**:
```python
# tests/services/test_invoicing_service_snapshots.py

def test_invoice_pdf_snapshot(snapshot, sample_invoice):
    """PDF output should match snapshot"""
    service = InvoicingService(db)
    pdf_bytes = service.generate_pdf(sample_invoice.id)

    # Compare with saved snapshot
    snapshot.assert_match(pdf_bytes, "invoice_basic.pdf")
```

**Rationale**: Visual regression automated—any PDF change triggers review

**Action**:
- [ ] Install `pytest-snapshot` or similar
- [ ] Create baseline PDF snapshots
- [ ] Add to CI pipeline (fail on unexpected changes)

---

### 8. Docs Cross-Link

**Recommendation**: Add "Delegates to InvoicingService" note in both SPEC-027 and 028

**Location**:
- `specs/027-billing-engine-integration/spec.md` → Implementation Overview section
- `specs/028-invoice-management-system/spec.md` → Implementation Overview section

**Content**:
```markdown
## Implementation Overview

### Invoice Generation (Delegated)

Invoice PDF generation and delivery is **delegated to the shared InvoicingService**:
- **Module**: `server/services/invoicing_service.py`
- **Refactoring Plan**: `docs/refactoring/SPEC_027_028_REFACTORING_PLAN.md`
- **Rationale**: Single source of truth for invoice rendering eliminates duplication

SPEC-027 (Billing Engine) creates invoice data and triggers PDF generation.
SPEC-028 (Invoice Management) displays invoices and provides customer portal.

Both use the same `InvoicingService` for consistent rendering.
```

**Action**:
- [ ] Update SPEC-027 spec.md with delegation note
- [ ] Update SPEC-028 spec.md with delegation note
- [ ] Link to refactoring plan

---

### 9. Future Extension - Reserved Stubs

**Recommendation**: Reserve stubs for `CreditNote` and `RefundInvoice` flows

**Implementation**:
```python
class InvoicingService:
    # ... existing methods ...

    def generate_credit_note_pdf(self, credit_note_id: str) -> bytes:
        """Generate PDF credit note (future)"""
        raise NotImplementedError("Credit notes coming in Phase 2")

    def generate_refund_invoice_pdf(self, refund_id: str) -> bytes:
        """Generate PDF refund invoice (future)"""
        raise NotImplementedError("Refund invoices coming in Phase 2")
```

**Rationale**: These often reuse PDF logic, having stubs prevents future duplication

**Action**:
- [ ] Add placeholder methods with `NotImplementedError`
- [ ] Document in future enhancements section

---

### 10. CI Enforcement

**Recommendation**: Add pre-commit rule verifying no duplicate `generate_invoice_pdf` functions

**Implementation**:
```yaml
# .pre-commit-config.yaml

- repo: local
  hooks:
    - id: no-duplicate-invoice-pdf
      name: Prevent duplicate invoice PDF generation
      entry: bash -c 'if grep -r "def generate_invoice_pdf" server/ --exclude="invoicing_service.py" | grep -v test; then echo "ERROR: generate_invoice_pdf found outside invoicing_service.py"; exit 1; fi'
      language: system
      pass_filenames: false
```

**Rationale**: Prevents future developers from re-introducing duplication

**Action**:
- [ ] Add pre-commit hook
- [ ] Test hook triggers on duplicate code
- [ ] Document in CONTRIBUTING.md

---

## 📋 Practical Implementation Sequence

### Step 1: Scaffold Service (Day 1 Morning - 2 hours)

**Tasks**:
- [ ] Create `server/services/invoicing_service.py`
- [ ] Copy SPEC-028's `create_pdf_invoice()` as base
- [ ] Rename to `InvoicingService.generate_pdf()`
- [ ] Add dependency injection (__init__ accepts TaxCalculator, Mailer)
- [ ] Add structured logging (invoice_id, team_id, duration_ms)
- [ ] Add docstrings

**Deliverable**: Empty service with PDF generation method

---

### Step 2: Add Feature Flag (Day 1 Morning - 1 hour)

**Tasks**:
- [ ] Add `USE_INVOICING_SERVICE` to `.env.dev`
- [ ] Add config loading in `server/config.py`
- [ ] Document flag in `README.md`

**Code**:
```python
# server/config.py
USE_INVOICING_SERVICE = os.getenv("USE_INVOICING_SERVICE", "false").lower() == "true"
```

**Deliverable**: Feature flag ready for gradual rollout

---

### Step 3: Extract Tax Calculator (Day 1 Afternoon - 3 hours)

**Tasks**:
- [ ] Create `server/services/tax_calculator.py`
- [ ] Consolidate tax logic from both SPECs
- [ ] Add `@lru_cache` to `_get_tax_rate()`
- [ ] Write 30+ unit tests
- [ ] Add structured logging

**Deliverable**: Standalone `TaxCalculator` class with tests

---

### Step 4: Replace in SPEC-027 (Day 2 Morning - 2 hours)

**Tasks**:
- [ ] Update `billing_engine_integration_api.py`
- [ ] Replace `generate_invoice_pdf()` with `InvoicingService.generate_pdf()`
- [ ] Add feature flag check
- [ ] Run billing-side integration tests
- [ ] Verify Stripe webhook flow

**Code**:
```python
# billing_engine_integration_api.py
from services.invoicing_service import InvoicingService
from config import USE_INVOICING_SERVICE

if USE_INVOICING_SERVICE:
    invoicing_service = InvoicingService(db)
    pdf_bytes = invoicing_service.generate_pdf(invoice_id)
else:
    pdf_bytes = generate_invoice_pdf_legacy(invoice_data)  # Keep temporarily
```

**Deliverable**: SPEC-027 using new service (with fallback)

---

### Step 5: Replace in SPEC-028 (Day 2 Afternoon - 2 hours)

**Tasks**:
- [ ] Update `invoice_management_api.py`
- [ ] Replace `create_pdf_invoice()` with `InvoicingService.generate_pdf()`
- [ ] Add feature flag check
- [ ] Run portal & export tests
- [ ] Verify customer portal displays correctly

**Deliverable**: SPEC-028 using new service (with fallback)

---

### Step 6: Parallel Run - PDF Comparison (Day 2 Evening - 1 hour)

**Tasks**:
- [ ] Enable `USE_INVOICING_SERVICE=true` on staging
- [ ] Generate 100 invoices with both old and new service
- [ ] Compare PDF byte hashes (should be identical)
- [ ] Log any differences for investigation

**Script**:
```python
# scripts/compare_invoice_pdfs.py
for invoice_id in sample_invoices:
    pdf_old = generate_invoice_pdf_legacy(invoice_id)
    pdf_new = invoicing_service.generate_pdf(invoice_id)

    if hashlib.sha256(pdf_old).hexdigest() != hashlib.sha256(pdf_new).hexdigest():
        logger.warning(f"PDF mismatch for invoice {invoice_id}")
```

**Deliverable**: Confidence that new service produces identical output

---

### Step 7: Integration Tests (Day 3 Morning - 3 hours)

**Tasks**:
- [ ] Write `test_invoicing_service.py` (50+ unit tests)
- [ ] Write `test_tax_calculator.py` (30+ unit tests)
- [ ] Write `test_invoice_integration.py` (10+ integration tests)
- [ ] Add snapshot tests for PDF byte equality
- [ ] Run full test suite

**Coverage Target**: 80%+ for invoicing_service.py

**Deliverable**: Comprehensive test coverage

---

### Step 8: Remove Legacy Code (Day 3 Afternoon - 2 hours)

**Tasks**:
- [ ] Set `USE_INVOICING_SERVICE=true` in production
- [ ] Monitor for 24 hours (no errors)
- [ ] Remove `generate_invoice_pdf_legacy()` from SPEC-027
- [ ] Remove `create_pdf_invoice()` from SPEC-028
- [ ] Remove feature flag code
- [ ] Push coverage report to dashboard

**Deliverable**: Clean codebase with single source of truth

---

### Step 9: Documentation Updates (Day 3 Afternoon - 1 hour)

**Tasks**:
- [ ] Update SPEC-027 spec.md (add delegation note)
- [ ] Update SPEC-028 spec.md (add delegation note)
- [ ] Create API documentation for InvoicingService
- [ ] Update architecture diagrams
- [ ] Add to CHANGELOG.md

**Deliverable**: Complete documentation

---

## ✅ Success Criteria

### Code Quality Metrics

- [ ] Lines of Code: Reduce by ~250 lines (eliminate duplication)
- [ ] Test Coverage: 80%+ for invoicing_service.py
- [ ] Cyclomatic Complexity: <10 per function
- [ ] Code Duplication: 0% (no duplicate PDF/tax code)

### Functional Metrics

- [ ] PDF Consistency: 100% identical output before/after refactoring
- [ ] Tax Accuracy: 100% match with existing calculations
- [ ] Delivery Success: 99.9% email delivery rate maintained
- [ ] Performance: <500ms PDF generation (p95)

### Observability Metrics

- [ ] Structured logs: All public methods logged
- [ ] Cache hit rate: >80% for tax rate lookups
- [ ] Error tracking: All exceptions logged with context
- [ ] Metrics dashboard: Invoice generation metrics visible

---

## 🎯 Daily Goals

### Day 1: Foundation
- ✅ Scaffold invoicing_service.py
- ✅ Extract tax_calculator.py
- ✅ Add feature flag
- ✅ Write initial tests (30+)

### Day 2: Integration
- ✅ Replace in SPEC-027
- ✅ Replace in SPEC-028
- ✅ Parallel run PDF comparison
- ✅ Verify both SPECs work

### Day 3: Validation & Cleanup
- ✅ Complete test suite (80+)
- ✅ Remove legacy code
- ✅ Update documentation
- ✅ Push to production

---

## 🚀 Deployment Strategy

### Phase 1: Canary (Day 2 Evening)
- Enable `USE_INVOICING_SERVICE=true` on staging
- Test with 10% of invoice traffic
- Monitor for errors (expect: 0)

### Phase 2: Gradual Rollout (Day 3 Morning)
- Increase to 50% of traffic
- Compare old vs new PDF hashes
- Monitor performance metrics

### Phase 3: Full Rollout (Day 3 Afternoon)
- Enable for 100% of traffic
- Monitor for 24 hours
- Remove legacy code if successful

### Phase 4: Cleanup (Day 3 Evening)
- Remove feature flags
- Push coverage report
- Celebrate! 🎉

---

## 📊 Monitoring Checklist

### During Rollout

- [ ] Error rate: <0.1% (should be ~0%)
- [ ] PDF generation time: <500ms (p95)
- [ ] Cache hit rate: >80%
- [ ] Email delivery: >99.9%

### Post-Rollout

- [ ] Test coverage: >80%
- [ ] Code duplication: 0%
- [ ] Documentation: 100% complete
- [ ] Team knowledge transfer: Complete

---

## 🎓 Model Template for Future Extractions

**This refactoring establishes patterns for future shared-service extractions**:

### Pattern: Shared Service Extraction

1. **Identify Duplication**: Find code duplicated across 2+ SPECs
2. **Create Shared Module**: Extract to `server/services/{service_name}.py`
3. **Add Dependency Injection**: Make testing easier
4. **Add Feature Flag**: Enable gradual rollout
5. **Replace Gradually**: One SPEC at a time
6. **Parallel Run**: Compare old vs new output
7. **Remove Legacy**: Clean up after validation

**Examples for Future**:
- `NotificationService` (email/SMS/push notifications)
- `ReceiptService` (payment receipt generation)
- `ReportService` (CSV/Excel export generation)

---

## ✅ Final Checklist

### Before Starting

- [ ] Review full refactoring plan
- [ ] Assign developer
- [ ] Schedule 2-3 day focused block
- [ ] Set up monitoring dashboard

### During Implementation

- [ ] Follow step-by-step sequence
- [ ] Run tests after each change
- [ ] Commit frequently with descriptive messages
- [ ] Document any deviations from plan

### Before Completion

- [ ] All tests passing (80%+ coverage)
- [ ] Documentation updated
- [ ] Code review approved by 2+ developers
- [ ] Monitoring dashboard shows green
- [ ] Legacy code removed

---

**Status**: Ready for implementation! 🚀
**Next**: Assign developer and schedule 2-3 day implementation block
