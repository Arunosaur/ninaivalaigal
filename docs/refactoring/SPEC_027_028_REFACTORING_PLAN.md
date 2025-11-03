# SPEC-027/028 Refactoring Plan: Eliminate Overlap

**Date**: October 31, 2025
**Priority**: High (Technical Debt Reduction)
**Estimated Effort**: 2-3 days
**Risk Level**: Medium (affects revenue infrastructure)

---

## Executive Summary

SPEC-027 (Billing Engine) and SPEC-028 (Invoice Management) have **significant functional overlap** that creates:
- Code duplication (PDF generation, tax calculation)
- Maintenance burden (changes must be made in 2 places)
- Testing complexity (same logic tested twice)
- Potential inconsistencies (invoices look different)

**Goal**: Refactor to eliminate duplication while preserving distinct responsibilities.

---

## Current State Analysis

### Implementation Status

| Component | SPEC-027 | SPEC-028 | Overlap |
|-----------|----------|----------|---------|
| **Files** | billing_engine_integration_api.py (768 lines) | invoice_management_api.py (742 lines) | Yes |
| **PDF Generation** | ✅ Has ReportLab implementation | ✅ Has ReportLab implementation | **DUPLICATE** |
| **Tax Calculation** | ✅ Tax rate calculation | ✅ Tax settings & calculation | **DUPLICATE** |
| **Invoice Data** | ✅ Invoice creation | ✅ Invoice viewing/management | **OVERLAP** |
| **Database Schema** | 027_billing_engine_integration.sql | Shares tables with 027 | **SHARED** |
| **Testing** | None ❌ | Minimal ❌ | N/A |

### Code Overlap Details

#### 1. **PDF Invoice Generation** (CRITICAL OVERLAP)

**SPEC-027**: `billing_engine_integration_api.py` line 170-220
```python
def generate_invoice_pdf(invoice_data: Dict[str, Any]) -> bytes:
    """Generate PDF invoice"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    # ~50 lines of ReportLab code
```

**SPEC-028**: `invoice_management_api.py` line 154-350
```python
def create_pdf_invoice(invoice: Invoice, tax_settings: Optional[TaxSettings] = None) -> bytes:
    """Generate PDF invoice using ReportLab"""
    # ~200 lines of ReportLab code (MORE COMPREHENSIVE)
```

**Issue**: Two different PDF generation implementations for the same invoices!

#### 2. **Tax Calculation** (MODERATE OVERLAP)

**SPEC-027**: `billing_engine_integration_api.py` line 151-168
```python
def calculate_tax(amount: Decimal, team_id: str) -> Decimal:
    """Calculate tax based on team location"""
    # Basic state-based tax calculation
```

**SPEC-028**: Has `TaxSettings` model and more advanced tax handling

**Issue**: Inconsistent tax calculation logic across SPECs

#### 3. **Invoice Data Models** (SHARED CONCERN)

Both SPECs work with the same database tables:
- `invoices`
- `invoice_line_items`
- `tax_calculations`
- `invoice_corrections`

**Issue**: No clear ownership of invoice lifecycle

---

## Proposed Architecture

### Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    SPEC-027: Billing Engine                 │
│  Responsibility: Payment Processing & Business Logic        │
├─────────────────────────────────────────────────────────────┤
│  - Stripe integration (customers, subscriptions, payments)  │
│  - Webhook event processing                                 │
│  - Payment retry logic & dunning campaigns                  │
│  - Usage tracking & metered billing                         │
│  - Revenue analytics (MRR, ARR, churn)                      │
│  - CREATES invoices (data only)                             │
│  - CALLS shared invoice service for PDF/delivery            │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              SHARED: Invoice Service Module                 │
│         Responsibility: Invoice Rendering & Delivery        │
├─────────────────────────────────────────────────────────────┤
│  - PDF generation (single implementation)                   │
│  - Tax calculation (single source of truth)                 │
│  - Invoice delivery (email, download, portal)               │
│  - Invoice formatting & branding                            │
│  - Tax compliance (calculations, reporting)                 │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│                 SPEC-028: Invoice Management                │
│   Responsibility: Invoice Lifecycle & Customer Experience   │
├─────────────────────────────────────────────────────────────┤
│  - Customer invoice portal                                  │
│  - Invoice viewing, search, filtering                       │
│  - Invoice corrections (adjustments, credits, voids)        │
│  - Multi-currency display                                   │
│  - Accounting system integration (CSV, QuickBooks, Xero)    │
│  - Invoice customization & branding UI                      │
│  - USES shared invoice service for rendering                │
└─────────────────────────────────────────────────────────────┘
```

### New Module: `invoice_service.py`

**Single Responsibility**: Invoice rendering, delivery, and tax compliance

```python
# server/services/invoice_service.py

class InvoiceService:
    """Centralized invoice rendering and delivery service

    Used by both SPEC-027 (billing engine) and SPEC-028 (invoice management)
    """

    def generate_pdf(self, invoice_id: str) -> bytes:
        """Generate PDF invoice (SINGLE IMPLEMENTATION)"""

    def calculate_tax(self, amount: Decimal, team_id: str) -> TaxCalculation:
        """Calculate tax (SINGLE SOURCE OF TRUTH)"""

    def deliver_invoice(self, invoice_id: str, method: str) -> bool:
        """Deliver invoice via email/download/portal"""

    def apply_branding(self, invoice: Invoice, branding: BrandingConfig) -> Invoice:
        """Apply custom branding to invoice"""
```

---

## Refactoring Steps

### Phase 1: Extract Invoice Service (1 day)

**Goal**: Create shared `invoice_service.py` module

1. **Create Module Structure**
   ```bash
   mkdir -p server/services
   touch server/services/__init__.py
   touch server/services/invoice_service.py
   ```

2. **Extract PDF Generation** (Use SPEC-028's implementation as base - more comprehensive)
   - Move `create_pdf_invoice()` from invoice_management_api.py
   - Add error handling and logging
   - Make branding configurable
   - Add unit tests

3. **Extract Tax Calculation**
   - Consolidate tax logic from both SPECs
   - Create `TaxCalculator` class
   - Support multiple tax models (inclusive/exclusive)
   - Add tax jurisdiction lookup

4. **Extract Invoice Delivery**
   - Email delivery
   - Portal link generation
   - Download endpoint

**Deliverables**:
- `server/services/invoice_service.py` (300-400 lines)
- Unit tests (test_invoice_service.py)
- Documentation

---

### Phase 2: Refactor SPEC-027 (0.5 days)

**Goal**: Update billing engine to use shared service

1. **Remove Duplicate Code**
   ```python
   # BEFORE (billing_engine_integration_api.py)
   def generate_invoice_pdf(invoice_data: Dict[str, Any]) -> bytes:
       # 50 lines of ReportLab code ❌ DELETE

   # AFTER
   from services.invoice_service import InvoiceService

   invoice_service = InvoiceService()
   pdf_bytes = invoice_service.generate_pdf(invoice_id)  ✅
   ```

2. **Update Invoice Creation**
   - Create invoice data in database
   - Call `invoice_service.generate_pdf()`
   - Call `invoice_service.deliver_invoice()`

3. **Update Webhook Handlers**
   - Use shared tax calculation
   - Use shared invoice delivery

**Deliverables**:
- Updated billing_engine_integration_api.py (-100 lines)
- Updated tests
- Verified Stripe webhook flow

---

### Phase 3: Refactor SPEC-028 (0.5 days)

**Goal**: Update invoice management to use shared service

1. **Remove Duplicate Code**
   ```python
   # BEFORE (invoice_management_api.py)
   def create_pdf_invoice(invoice: Invoice, ...) -> bytes:
       # 200 lines of ReportLab code ❌ DELETE

   # AFTER
   from services.invoice_service import InvoiceService

   invoice_service = InvoiceService()
   pdf_bytes = invoice_service.generate_pdf(invoice_id)  ✅
   ```

2. **Update Portal Endpoints**
   - Use shared PDF generation
   - Use shared tax display
   - Add customization parameters

3. **Update Accounting Exports**
   - Use shared tax calculations
   - Ensure consistent invoice data

**Deliverables**:
- Updated invoice_management_api.py (-150 lines)
- Updated customer portal
- Verified accounting exports

---

### Phase 4: Testing & Validation (1 day)

**Goal**: Comprehensive testing of refactored system

1. **Unit Tests**
   - InvoiceService methods (PDF, tax, delivery)
   - Edge cases (missing data, invalid tax rates)
   - Branding variations

2. **Integration Tests**
   - SPEC-027: Create subscription → Generate invoice → Deliver PDF
   - SPEC-028: View invoice → Download PDF → Export to CSV
   - Tax calculations match between SPECs

3. **Visual Validation**
   - PDF output identical before/after refactoring
   - Customer portal displays correctly
   - Email invoices look professional

4. **Performance Testing**
   - PDF generation time (<500ms)
   - Tax calculation performance
   - Concurrent invoice generation

**Deliverables**:
- 50+ unit tests
- 10+ integration tests
- Performance benchmarks
- Visual regression tests

---

## Detailed Implementation Plan

### New File Structure

```
server/
├── services/
│   ├── __init__.py
│   ├── invoice_service.py          # NEW: Shared invoice logic
│   └── tax_calculator.py           # NEW: Tax calculation engine
├── billing_engine_integration_api.py  # REFACTORED: -100 lines
├── invoice_management_api.py          # REFACTORED: -150 lines
└── tests/
    ├── services/
    │   ├── test_invoice_service.py    # NEW: Unit tests
    │   └── test_tax_calculator.py     # NEW: Tax tests
    └── integration/
        └── test_invoice_flow.py       # NEW: End-to-end tests
```

### invoice_service.py Structure

```python
# server/services/invoice_service.py
"""
Centralized Invoice Service

Provides invoice rendering, delivery, and tax compliance for both
SPEC-027 (Billing Engine) and SPEC-028 (Invoice Management).

This eliminates code duplication and ensures consistent invoice
generation across all customer touchpoints.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# ... other imports

class TaxCalculation:
    """Tax calculation result"""
    amount: Decimal
    rate: Decimal
    jurisdiction: str
    tax_inclusive: bool

class BrandingConfig:
    """Invoice branding configuration"""
    logo_url: Optional[str]
    primary_color: str
    company_name: str
    footer_text: str

class InvoiceService:
    """Centralized invoice service"""

    def __init__(self, db: Session):
        self.db = db
        self.tax_calculator = TaxCalculator(db)

    def generate_pdf(
        self,
        invoice_id: str,
        branding: Optional[BrandingConfig] = None
    ) -> bytes:
        """Generate professional PDF invoice

        Args:
            invoice_id: Invoice database ID
            branding: Optional custom branding

        Returns:
            PDF bytes ready for download/email

        Raises:
            InvoiceNotFoundError: Invoice doesn't exist
            PDFGenerationError: PDF creation failed
        """
        invoice = self._get_invoice(invoice_id)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Build PDF content
        elements = []
        elements.extend(self._create_header(invoice, branding))
        elements.extend(self._create_line_items(invoice))
        elements.extend(self._create_totals(invoice))
        elements.extend(self._create_footer(invoice, branding))

        doc.build(elements)
        return buffer.getvalue()

    def calculate_tax(
        self,
        amount: Decimal,
        team_id: str,
        tax_inclusive: bool = False
    ) -> TaxCalculation:
        """Calculate tax for invoice amount

        Single source of truth for tax calculations across all SPECs.
        """
        return self.tax_calculator.calculate(amount, team_id, tax_inclusive)

    def deliver_invoice(
        self,
        invoice_id: str,
        method: str = "email",
        recipient: Optional[str] = None
    ) -> bool:
        """Deliver invoice to customer

        Args:
            invoice_id: Invoice to deliver
            method: email, download, portal
            recipient: Override recipient email

        Returns:
            True if delivered successfully
        """
        if method == "email":
            return self._send_email(invoice_id, recipient)
        elif method == "portal":
            return self._add_to_portal(invoice_id)
        elif method == "download":
            return True  # Direct download, no delivery needed
        else:
            raise ValueError(f"Unknown delivery method: {method}")

    def apply_branding(
        self,
        invoice: Invoice,
        branding: BrandingConfig
    ) -> Invoice:
        """Apply custom branding to invoice"""
        # Update invoice metadata with branding
        pass

    # Private helper methods
    def _get_invoice(self, invoice_id: str) -> Invoice:
        """Fetch invoice from database"""
        pass

    def _create_header(self, invoice: Invoice, branding: Optional[BrandingConfig]):
        """Create PDF header with logo and company info"""
        pass

    def _create_line_items(self, invoice: Invoice):
        """Create line items table"""
        pass

    def _create_totals(self, invoice: Invoice):
        """Create totals section with tax breakdown"""
        pass

    def _create_footer(self, invoice: Invoice, branding: Optional[BrandingConfig]):
        """Create PDF footer with payment terms"""
        pass

    def _send_email(self, invoice_id: str, recipient: Optional[str]) -> bool:
        """Send invoice via email"""
        pass

    def _add_to_portal(self, invoice_id: str) -> bool:
        """Add invoice to customer portal"""
        pass


class TaxCalculator:
    """Tax calculation engine

    Supports:
    - Multiple jurisdictions (US states, countries)
    - Tax-inclusive vs tax-exclusive models
    - Tax exemptions
    - Multi-currency
    """

    def __init__(self, db: Session):
        self.db = db
        self._tax_rate_cache = {}

    def calculate(
        self,
        amount: Decimal,
        team_id: str,
        tax_inclusive: bool = False
    ) -> TaxCalculation:
        """Calculate tax for amount"""
        # Get team's tax settings
        settings = self._get_tax_settings(team_id)

        if settings.tax_exempt:
            return TaxCalculation(
                amount=Decimal("0.00"),
                rate=Decimal("0.00"),
                jurisdiction=settings.jurisdiction,
                tax_inclusive=tax_inclusive
            )

        tax_rate = self._get_tax_rate(settings.jurisdiction)

        if tax_inclusive:
            # Amount already includes tax
            tax_amount = amount - (amount / (1 + tax_rate))
        else:
            # Calculate tax on top of amount
            tax_amount = amount * tax_rate

        return TaxCalculation(
            amount=tax_amount,
            rate=tax_rate,
            jurisdiction=settings.jurisdiction,
            tax_inclusive=tax_inclusive
        )

    def _get_tax_settings(self, team_id: str):
        """Get team's tax configuration"""
        pass

    def _get_tax_rate(self, jurisdiction: str) -> Decimal:
        """Get tax rate for jurisdiction (cached)"""
        pass
```

---

## Migration Strategy

### Backward Compatibility

**Requirement**: Existing invoices must continue to work during migration

1. **Dual Code Path** (during transition)
   ```python
   # Both old and new code paths work during migration
   if feature_flag("use_invoice_service"):
       pdf = invoice_service.generate_pdf(invoice_id)
   else:
       pdf = generate_invoice_pdf_legacy(invoice_data)  # Old code
   ```

2. **Gradual Rollout**
   - Phase 1: Internal testing (1 day)
   - Phase 2: Canary deployment (10% of invoices)
   - Phase 3: Full rollout (100% of invoices)
   - Phase 4: Remove legacy code

3. **Rollback Plan**
   - Feature flag to disable new service
   - Keep legacy code for 2 weeks
   - Automated comparison (new vs old PDF)

---

## Testing Strategy

### Test Scenarios

**Invoice Generation**:
- [ ] Basic invoice with no tax
- [ ] Invoice with tax-exclusive amount
- [ ] Invoice with tax-inclusive amount
- [ ] Invoice with discount applied
- [ ] Invoice with multiple line items
- [ ] Invoice with custom branding
- [ ] Invoice with multi-currency display

**Tax Calculation**:
- [ ] US state tax rates (CA, NY, TX, etc.)
- [ ] Tax-exempt teams
- [ ] Tax-inclusive vs exclusive
- [ ] Edge cases (null jurisdiction, invalid team)

**Integration**:
- [ ] SPEC-027: Stripe webhook → Invoice creation → PDF generation
- [ ] SPEC-028: Customer portal → Invoice download → PDF matches
- [ ] Both SPECs generate identical PDFs for same invoice

**Performance**:
- [ ] PDF generation <500ms (p95)
- [ ] Tax calculation <10ms (p95)
- [ ] Concurrent invoice generation (100 invoices/second)

---

## Success Metrics

### Code Quality

- **Lines of Code**: Reduce by ~200 lines (eliminate duplication)
- **Test Coverage**: Increase from 0% to 80%+ for invoice logic
- **Cyclomatic Complexity**: Reduce from 15+ to <10 per function
- **Code Duplication**: Eliminate 100% of PDF/tax overlap

### Functionality

- **PDF Consistency**: 100% identical output before/after refactoring
- **Tax Accuracy**: 100% match with existing calculations
- **Delivery Success**: 99.9% email delivery rate maintained
- **Performance**: No regression (maintain <500ms PDF generation)

### Maintainability

- **Single Source of Truth**: 1 PDF implementation (was 2)
- **Single Tax Logic**: 1 tax calculator (was 2)
- **Documentation**: 100% of public methods documented
- **Test Coverage**: 80%+ for invoice service

---

## Risk Assessment

### High Risk

1. **Revenue Impact**: Invoice generation is revenue-critical
   - **Mitigation**: Feature flags, gradual rollout, rollback plan

2. **PDF Regression**: Customer-facing invoice appearance
   - **Mitigation**: Visual regression tests, manual QA

### Medium Risk

3. **Tax Calculation Errors**: Could cause compliance issues
   - **Mitigation**: Extensive test coverage, accounting validation

4. **Integration Complexity**: Both SPECs depend on this
   - **Mitigation**: Staged migration, thorough integration tests

### Low Risk

5. **Performance Degradation**: Shared service could be slower
   - **Mitigation**: Performance benchmarks, caching

---

## Timeline

### Week 1: Extraction & Refactoring

**Monday-Tuesday** (1.5 days):
- Create invoice_service.py
- Extract PDF generation (use SPEC-028 as base)
- Extract tax calculation
- Write unit tests (50+ tests)

**Wednesday** (0.5 days):
- Refactor SPEC-027 to use invoice_service
- Update webhook handlers
- Test Stripe integration

**Thursday** (0.5 days):
- Refactor SPEC-028 to use invoice_service
- Update customer portal
- Test accounting exports

**Friday** (0.5 days):
- Integration testing
- Visual regression tests
- Performance benchmarks

### Week 2: Validation & Cleanup (if needed)

**Monday-Tuesday**:
- Fix any issues found in testing
- Documentation updates
- Code review

**Wednesday-Thursday**:
- Gradual rollout (canary)
- Monitor for issues
- Compare old vs new PDFs

**Friday**:
- Full rollout
- Remove feature flags
- Update SPEC documentation

---

## Dependencies

### Required Before Starting

- [ ] Approval from stakeholders
- [ ] Access to test Stripe account
- [ ] Sample invoices for validation
- [ ] Accounting export validation criteria

### Required During Implementation

- [ ] Code review from 2+ developers
- [ ] QA validation of PDF output
- [ ] Accounting team validation
- [ ] Performance benchmarking

---

## Deliverables

### Code

1. **server/services/invoice_service.py** (400 lines)
   - PDF generation
   - Tax calculation
   - Invoice delivery

2. **server/services/tax_calculator.py** (200 lines)
   - Tax rate lookup
   - Tax calculation logic
   - Jurisdiction handling

3. **Updated SPEC-027 API** (-100 lines)
   - Remove duplicate PDF code
   - Use shared invoice service

4. **Updated SPEC-028 API** (-150 lines)
   - Remove duplicate PDF code
   - Use shared invoice service

### Tests

5. **test_invoice_service.py** (50+ tests)
6. **test_tax_calculator.py** (30+ tests)
7. **test_invoice_integration.py** (10+ tests)

### Documentation

8. **SPEC-027 Updates**: Document invoice service usage
9. **SPEC-028 Updates**: Document invoice service usage
10. **API Documentation**: Invoice service public API
11. **Migration Guide**: For other developers

---

## Post-Refactoring Benefits

### Developer Experience

- **Single Place to Update**: Invoice changes only touch one file
- **Easier Testing**: Isolated, testable invoice logic
- **Better Documentation**: Clear service boundaries
- **Faster Onboarding**: New developers understand faster

### Code Quality

- **-250 Lines**: Remove duplicated code
- **+80% Coverage**: Add comprehensive tests
- **Lower Complexity**: Simpler, focused modules
- **Better Separation**: Clear SPEC boundaries

### Business Impact

- **Consistency**: Invoices look identical everywhere
- **Reliability**: Single tested implementation
- **Flexibility**: Easy to add new features (branding, etc.)
- **Compliance**: Single tax calculation = easier audits

---

## Conclusion

This refactoring eliminates critical technical debt in revenue infrastructure while preserving distinct SPEC responsibilities. The investment of 2-3 days will pay dividends in maintainability, reliability, and development speed.

**Recommendation**: Proceed with refactoring as outlined, prioritizing Phase 1 (extraction) to establish shared foundation.

---

## Appendix: API Changes

### SPEC-027: Before vs After

**Before**:
```python
# billing_engine_integration_api.py
@router.post("/invoices/{invoice_id}/generate")
def generate_invoice(invoice_id: str):
    invoice_data = get_invoice_data(invoice_id)
    pdf = generate_invoice_pdf(invoice_data)  # Local function ❌
    return pdf
```

**After**:
```python
# billing_engine_integration_api.py
from services.invoice_service import InvoiceService

@router.post("/invoices/{invoice_id}/generate")
def generate_invoice(invoice_id: str):
    invoice_service = InvoiceService(db)
    pdf = invoice_service.generate_pdf(invoice_id)  # Shared service ✅
    return pdf
```

### SPEC-028: Before vs After

**Before**:
```python
# invoice_management_api.py
@router.get("/invoices/{invoice_id}/download")
def download_invoice(invoice_id: str):
    invoice = get_invoice(invoice_id)
    pdf = create_pdf_invoice(invoice, tax_settings)  # Local function ❌
    return pdf
```

**After**:
```python
# invoice_management_api.py
from services.invoice_service import InvoiceService

@router.get("/invoices/{invoice_id}/download")
def download_invoice(invoice_id: str):
    invoice_service = InvoiceService(db)
    pdf = invoice_service.generate_pdf(invoice_id)  # Same shared service ✅
    return pdf
```

---

**Status**: Ready for approval and implementation
**Next Steps**: Review with team, get approval, begin Phase 1
