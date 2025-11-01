# SPEC-028: Invoice Management System

**Status**: 🔄 **PARTIAL IMPLEMENTATION** (65% Complete)  
**Priority**: High (Customer Experience)  
**Created**: 2024-09-20  
**Updated**: 2025-10-31  
**Authors**: Arun Rajagopalan  
**Implementation**: Partial (743 lines, needs refactoring)  
**Testing**: Minimal (shared with SPEC-027)

---

## Title

Professional Invoice Management with Customer Portal and Accounting Integration

---

## Objective

Provide a comprehensive, customer-facing invoice management system with self-service portal, professional PDF generation, invoice corrections, multi-currency support, and accounting system integration.

This SPEC focuses on the **invoice lifecycle and customer experience** while SPEC-027 handles the underlying payment processing engine.

---

## Motivation

### Business Need

Professional invoice management is critical for customer satisfaction and operational efficiency:
- **Customer Self-Service**: Reduce support tickets by 30-40%
- **Brand Credibility**: Professional, branded invoices
- **Dispute Resolution**: Efficient correction and credit memo workflows
- **International Support**: Multi-currency invoice display
- **Finance Efficiency**: Automated accounting system exports save 10+ hours/month

### Technical Challenge

Invoice management requires:
- Professional PDF generation with custom branding
- Customer portal with secure access tokens
- Invoice correction workflows (adjustments, credits, voids)
- Multi-currency display and conversion
- Accounting system integration (QuickBooks, Xero, CSV)
- Audit trail for compliance
- Tax configuration flexibility

### Solution

Complete invoice management system with:
- Customer invoice portal for self-service access
- Professional PDF invoices with custom branding
- Invoice correction and credit memo workflows
- Multi-currency support with real-time conversion
- Accounting system export (CSV/Excel/API)
- Advanced tax configuration UI
- Complete audit trail and compliance tracking

---

## Scope

### Inclusions

**Invoice Display & Access:**
- ✅ Invoice viewing and search
- ✅ PDF generation with ReportLab
- 🟡 Customer self-service portal (partial)
- ⏳ Invoice filtering and sorting
- ⏳ Invoice status tracking dashboard

**Invoice Corrections:**
- ⏳ Adjustment workflows (quantity/price changes)
- ⏳ Credit memo generation
- ⏳ Invoice voiding with reason tracking
- ⏳ Dispute management system

**Tax & Compliance:**
- ✅ Tax-inclusive/exclusive models
- ✅ Per-team tax configuration
- ⏳ Multi-jurisdiction tax handling
- ⏳ Tax reporting and compliance
- ⏳ Record retention policies

**Accounting Integration:**
- ⏳ CSV/Excel export
- ⏳ QuickBooks Online integration
- ⏳ Xero integration
- ⏳ Real-time sync webhooks

**Customization:**
- ⏳ Custom invoice branding (logo, colors)
- ⏳ Invoice footer customization
- ⏳ Payment terms templates
- ⏳ Custom fields and metadata

### Exclusions

- ❌ Payment processing (owned by SPEC-027)
- ❌ Stripe integration (owned by SPEC-027)
- ❌ Subscription management (owned by SPEC-027)
- ❌ Usage tracking (owned by SPEC-027)
- ❌ Dunning campaigns (owned by SPEC-027)
- ❌ Revenue analytics (owned by SPEC-027)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ninaivalaigal Platform                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │  SPEC-026    │      │  SPEC-028    │      │  Customer │ │
│  │  Team Billing│─────>│  Invoice     │<─────│   Portal  │ │
│  │     UI       │      │ Management   │      │           │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │      │
│         │                      │                     │      │
│         v                      v                     v      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastAPI Core (main.py)                     │  │
│  │    /invoicing/* endpoints                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │              │
│         v                 v                 v              │
│  ┌───────────┐     ┌───────────┐     ┌──────────┐         │
│  │PostgreSQL │     │ ReportLab │     │Accounting│         │
│  │ (Invoice  │     │   (PDF)   │     │ Systems  │         │
│  │   Data)   │     │           │     │(CSV/API) │         │
│  └───────────┘     └───────────┘     └──────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Integration with SPEC-027:
┌───────────────────────┐
│   SPEC-027            │
│   Billing Engine      │
│  - Payment Processing │ ──> Creates Invoices
│  - Stripe Webhooks    │ ──> Updates Status
│  - Automated Billing  │ ──> Triggers Generation
└───────────────────────┘
```

### Separation of Concerns: SPEC-027 vs SPEC-028

| Responsibility | SPEC-027 | SPEC-028 |
|----------------|----------|----------|
| **Payment Processing** | ✅ Owns | ❌ References |
| **Stripe Integration** | ✅ Owns | ❌ None |
| **Invoice Generation** | ✅ Creates | ✅ Displays |
| **PDF Creation** | 🔄 Shared | ✅ Owns |
| **Tax Calculation** | 🔄 Shared | ✅ Owns UI |
| **Customer Portal** | ❌ None | ✅ Owns |
| **Invoice Corrections** | ❌ None | ✅ Owns |
| **Accounting Export** | ❌ None | ✅ Owns |
| **Dunning Campaigns** | ✅ Owns | ❌ None |
| **Revenue Analytics** | ✅ Owns | ❌ None |

### Components

#### 1. Invoice Display API

**Current Endpoints**:
- `GET /invoicing/team/{team_id}` - List team invoices
- `GET /invoicing/{invoice_id}` - Get specific invoice
- `GET /invoicing/{invoice_id}/pdf` - Download PDF

**Missing Endpoints**:
- `GET /invoicing/search` - Advanced invoice search
- `GET /invoicing/dashboard/{team_id}` - Invoice dashboard metrics
- `GET /invoicing/export/{team_id}` - Export to CSV/Excel

#### 2. Customer Invoice Portal

**Status**: ⏳ **NEEDS IMPLEMENTATION**

**Features**:
```
Customer Portal Features:
1. Secure Access
   - Time-limited access tokens
   - Email-based authentication
   - No password required
   
2. Invoice Viewing
   - List all invoices for team
   - Filter by status/date/amount
   - Search functionality
   
3. Actions
   - Download PDF
   - View payment history
   - Request corrections
   - Update billing email
   
4. Notifications
   - New invoice alerts
   - Payment confirmations
   - Overdue reminders
```

**Proposed Endpoints**:
```python
POST /invoicing/portal/request-access
    # Request portal access token via email
    
GET /invoicing/portal/invoices?token={token}
    # List invoices with valid token
    
GET /invoicing/portal/invoice/{id}?token={token}
    # View specific invoice
    
POST /invoicing/portal/request-correction
    # Request invoice correction
```

#### 3. Invoice Correction Workflows

**Status**: ⏳ **NEEDS IMPLEMENTATION**

**Correction Types**:

1. **Adjustment**: Modify existing invoice
   - Change line item quantities
   - Update unit prices
   - Add/remove line items
   - Reason required

2. **Credit Memo**: Partial refund
   - Specify credit amount
   - Link to original invoice
   - Apply to future invoices or refund

3. **Void**: Cancel entire invoice
   - Mark as void (not deleted)
   - Reason required
   - Audit trail preserved

**Workflow**:
```
1. Customer/Admin initiates correction
2. Reason documented
3. Original invoice preserved (audit trail)
4. New invoice/credit memo generated
5. Notifications sent
6. Accounting system updated
```

**Proposed Endpoints**:
```python
POST /invoicing/{invoice_id}/adjust
    # Create adjustment
    
POST /invoicing/{invoice_id}/credit
    # Generate credit memo
    
POST /invoicing/{invoice_id}/void
    # Void invoice
    
GET /invoicing/corrections
    # List all corrections
```

#### 4. PDF Generation

**Current Implementation** (743 lines):
```python
def create_pdf_invoice(invoice, tax_settings):
    # ReportLab-based PDF generation
    # Professional layout
    # Company branding
    # Line items table
    # Tax breakdown
```

**Enhancement Needed**:
- Custom branding (team logos, colors)
- Invoice footer customization
- Multiple language support
- Payment instructions per payment method
- QR code for online payment

**Customization Model**:
```python
class InvoiceBranding(BaseModel):
    team_id: UUID
    company_logo_url: Optional[str]
    primary_color: str = "#2563eb"
    secondary_color: str = "#1f2937"
    invoice_footer: Optional[str]
    payment_instructions: Optional[str]
    show_qr_code: bool = False
```

#### 5. Tax Configuration

**Current Implementation**:
```python
class TaxSettings(BaseModel):
    tax_rate: float  # Percentage
    tax_name: str    # "Sales Tax", "VAT", "GST"
    tax_id: Optional[str]
    tax_address: Optional[Dict]
    is_tax_inclusive: bool = False
```

**Enhancement Needed**:
- Multiple tax rates per team (state/province)
- Tax exemption certificates
- Reverse charge mechanism (B2B in EU)
- Tax holidays and special rates
- Automatic tax rate lookup by address

**Proposed UI**:
- Tax configuration dashboard
- Upload tax exemption certificates
- Configure tax rates by jurisdiction
- Test tax calculation preview

#### 6. Multi-Currency Support

**Current Status**: 🟡 **MODEL EXISTS, NOT FUNCTIONAL**

**Model**:
```python
class Invoice(BaseModel):
    currency: str  # "USD", "EUR", "GBP", etc.
    # But no conversion logic!
```

**Required Implementation**:
- Real-time currency conversion API (e.g., exchangerate-api.io)
- Display amount in team's preferred currency
- Store original amount and converted amount
- Exchange rate at time of invoice creation
- Multi-currency invoice templates

**Conversion Logic**:
```python
class CurrencyConverter:
    def convert(self, amount, from_currency, to_currency, date):
        # Fetch exchange rate for specific date
        rate = get_exchange_rate(from_currency, to_currency, date)
        return amount * rate
    
    def display_invoice(self, invoice, display_currency):
        # Convert all amounts to display currency
        # Show original amount as reference
```

#### 7. Accounting System Integration

**Status**: ⏳ **NOT IMPLEMENTED**

**Required Integrations**:

1. **CSV/Excel Export**
   - All invoices in period
   - Line item details
   - Tax breakdown
   - Payment status
   - Format: Standard accounting format

2. **QuickBooks Online**
   - OAuth 2.0 integration
   - Automatic invoice sync
   - Customer matching
   - Payment reconciliation
   - Real-time updates

3. **Xero**
   - OAuth 2.0 integration
   - Invoice creation in Xero
   - Payment tracking
   - Tax code mapping

**Export Endpoints**:
```python
GET /invoicing/export/csv?start_date=&end_date=
    # CSV export for accounting
    
POST /invoicing/integrations/quickbooks/connect
    # OAuth connection
    
POST /invoicing/integrations/quickbooks/sync
    # Manual sync trigger
    
GET /invoicing/integrations/status
    # Integration health check
```

---

## Database Schema

### Current State: Mock Stores (NEEDS MIGRATION)

```python
# NOT PRODUCTION READY!
invoices_db = {}
billing_cycles_db = {}
payment_failures_db = {}
tax_settings_db = {}
```

### Required Tables

```sql
-- Invoice preferences and branding
CREATE TABLE invoice_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID UNIQUE REFERENCES teams(id),
    company_name VARCHAR(255),
    company_logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    secondary_color VARCHAR(7) DEFAULT '#1f2937',
    invoice_footer TEXT,
    payment_instructions TEXT,
    show_qr_code BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoice corrections and credit memos
CREATE TABLE invoice_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_invoice_id UUID REFERENCES invoices(id),
    correction_type VARCHAR(50) NOT NULL, -- adjustment, credit, void
    new_invoice_id UUID REFERENCES invoices(id),
    reason TEXT NOT NULL,
    amount_difference DECIMAL(10,2),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ
);

CREATE INDEX idx_corrections_original ON invoice_corrections(original_invoice_id);
CREATE INDEX idx_corrections_type ON invoice_corrections(correction_type);

-- Customer portal access tokens
CREATE TABLE invoice_portal_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id),
    customer_email VARCHAR(255) NOT NULL,
    access_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accessed_count INT DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_portal_tokens_team ON invoice_portal_tokens(team_id);
CREATE INDEX idx_portal_tokens_email ON invoice_portal_tokens(customer_email);
CREATE INDEX idx_portal_tokens_token ON invoice_portal_tokens(access_token);

-- Tax configuration per team
CREATE TABLE tax_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id),
    jurisdiction VARCHAR(100), -- "US-CA", "GB", "EU-DE"
    tax_name VARCHAR(100) NOT NULL,
    tax_rate DECIMAL(5,2) NOT NULL,
    tax_id_number VARCHAR(100),
    is_tax_inclusive BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    effective_from DATE,
    effective_to DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tax_config_team ON tax_configurations(team_id);
CREATE INDEX idx_tax_config_jurisdiction ON tax_configurations(jurisdiction);

-- Tax exemption certificates
CREATE TABLE tax_exemptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id),
    exemption_type VARCHAR(50), -- non-profit, government, reseller
    certificate_url TEXT,
    certificate_number VARCHAR(100),
    jurisdiction VARCHAR(100),
    valid_from DATE NOT NULL,
    valid_to DATE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Multi-currency exchange rates (cache)
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(12,6) NOT NULL,
    rate_date DATE NOT NULL,
    source VARCHAR(50), -- "exchangerate-api", "manual"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_currency, to_currency, rate_date)
);

CREATE INDEX idx_exchange_rates_currencies ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_date ON exchange_rates(rate_date);

-- Accounting system integrations
CREATE TABLE accounting_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID UNIQUE REFERENCES teams(id),
    system_type VARCHAR(50) NOT NULL, -- quickbooks, xero, csv
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ,
    sync_status VARCHAR(50), -- active, error, disconnected
    error_message TEXT,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoice audit trail
CREATE TABLE invoice_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id),
    action VARCHAR(50) NOT NULL, -- created, sent, paid, corrected, voided
    actor_id UUID REFERENCES users(id),
    actor_type VARCHAR(50), -- user, system, api
    details JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_invoice ON invoice_audit_log(invoice_id);
CREATE INDEX idx_audit_action ON invoice_audit_log(action);
```

---

## API Specifications

### Current Endpoints (11 total)

| Method | Path | Status | Purpose |
|--------|------|--------|---------|
| POST | `/invoicing/generate` | ✅ | Generate invoice |
| GET | `/invoicing/team/{team_id}` | ✅ | List team invoices |
| GET | `/invoicing/{invoice_id}` | ✅ | Get invoice details |
| GET | `/invoicing/{invoice_id}/pdf` | ✅ | Download PDF |
| POST | `/invoicing/{invoice_id}/send` | 🟡 | Email invoice (mocked) |
| POST | `/invoicing/tax-settings/{team_id}` | ✅ | Update tax settings |
| GET | `/invoicing/tax-settings/{team_id}` | ✅ | Get tax settings |
| POST | `/invoicing/billing-cycle/{team_id}` | ✅ | Setup billing cycle |
| POST | `/invoicing/process-billing-cycles` | ✅ | Process cycles (cron) |
| GET | `/invoicing/payment-failures` | ✅ | Get failures |
| POST | `/invoicing/retry-payment/{failure_id}` | ✅ | Retry payment |

### Required New Endpoints

**Customer Portal** (6 endpoints):
```
POST   /invoicing/portal/request-access
GET    /invoicing/portal/invoices
GET    /invoicing/portal/invoice/{id}
GET    /invoicing/portal/invoice/{id}/pdf
POST   /invoicing/portal/request-correction
PATCH  /invoicing/portal/update-email
```

**Invoice Corrections** (4 endpoints):
```
POST   /invoicing/{id}/adjust
POST   /invoicing/{id}/credit
POST   /invoicing/{id}/void
GET    /invoicing/corrections
```

**Branding & Customization** (3 endpoints):
```
POST   /invoicing/branding/{team_id}
GET    /invoicing/branding/{team_id}
GET    /invoicing/branding/{team_id}/preview
```

**Accounting Integration** (6 endpoints):
```
GET    /invoicing/export/csv
GET    /invoicing/export/excel
POST   /invoicing/integrations/quickbooks/connect
POST   /invoicing/integrations/xero/connect
POST   /invoicing/integrations/{type}/sync
GET    /invoicing/integrations/status
```

**Total New Endpoints**: 19

---

## Dependencies

### Required SPECs

- ✅ **SPEC-027**: Billing Engine Integration (creates invoices)
- ✅ **SPEC-026**: Standalone Teams & Billing (consumes invoices)
- ✅ **PostgreSQL**: Database infrastructure
- ✅ **FastAPI**: Web framework

### External Dependencies

- **ReportLab**: v4.0.7+ (already integrated)
- **Stripe**: For payment status updates (via SPEC-027)
- **Currency API**: exchangerate-api.io or similar
- **Email Service**: SendGrid/AWS SES (shared with SPEC-027)
- **QuickBooks SDK**: intuit-oauth, quickbooks-python
- **Xero SDK**: xero-python

---

## Frontend Implementation

### Existing Files (3 total)

1. `/frontend/invoice-management.html` - Main dashboard
2. `/frontend/customer/invoice-management.html` - Customer portal
3. `/frontend/admin/invoice-management.html` - Admin view

**Status**: Files exist, need review and enhancement

**Required Enhancements**:
- Invoice search and filtering
- Correction workflow UI
- Tax configuration dashboard
- Branding customization UI
- Integration setup wizards
- Multi-currency selector

---

## Testing Strategy

### Current State
- 🟡 Some coverage in `/tests/billing_flow_testing.py`
- Mixed with SPEC-027 tests
- No dedicated SPEC-028 test file

### Required Tests

**Unit Tests** (30-40 tests):
- Invoice lifecycle (draft → paid → overdue)
- PDF generation with various configurations
- Tax calculation (inclusive/exclusive)
- Currency conversion accuracy
- Access token generation and expiration
- Invoice correction logic

**Integration Tests** (15-20 tests):
- Customer portal access flow
- Invoice correction workflows
- Accounting system export
- Multi-currency invoice creation
- Tax configuration management

**E2E Tests** (5-8 scenarios):
- Complete customer portal journey
- Invoice dispute and correction
- QuickBooks/Xero sync
- Multi-currency invoice viewing
- Admin branding customization

---

## Performance Requirements

- **Invoice PDF Generation**: <3 seconds
- **Customer Portal Load**: <1 second
- **Invoice Search**: <500ms for 10,000 invoices
- **CSV Export**: <10 seconds for 1 year of data
- **Accounting Sync**: <30 seconds for 100 invoices
- **Portal Token Generation**: <200ms

---

## Security Considerations

### Implemented ✅

1. **JWT Authentication**: All admin endpoints
2. **Team Ownership Validation**: Can only access own invoices

### Required ⏳

1. **Portal Access Tokens**
   - Time-limited (24-48 hours)
   - Single-use or limited use
   - Email verification required

2. **Audit Logging**
   - All invoice modifications logged
   - User actions tracked
   - IP address recorded

3. **Data Access Control**
   - Customer can only see their own invoices
   - Admin can see all team invoices
   - Portal users can't modify invoices

4. **Sensitive Data**
   - Tax IDs encrypted at rest
   - OAuth tokens encrypted
   - Audit logs tamper-proof

---

## Business Impact

### Customer Experience

- **Self-Service**: 30-40% reduction in support tickets
- **Professional Branding**: Increased brand credibility
- **Fast Dispute Resolution**: 80% faster correction workflows
- **Multi-Currency**: Support for international customers

### Operational Efficiency

- **Accounting Integration**: Save 10+ hours/month for finance team
- **Automated Exports**: Eliminate manual data entry
- **Tax Compliance**: Reduce risk of tax calculation errors
- **Audit Trail**: Simplify compliance and audits

### Revenue Impact

- **Reduced Churn**: Better customer experience
- **International Expansion**: Multi-currency support
- **Faster Collections**: Professional invoices paid faster
- **Lower Costs**: Reduced support and finance overhead

---

## Known Issues & Technical Debt

### Critical Issues ❌

1. **File Header Mislabeled**
   - Current: "SPEC-027: Invoice and Plan Management API"
   - Should be: "SPEC-028: Invoice Management System API"

2. **Overlap with SPEC-027**
   - Invoice generation logic duplicated
   - PDF creation duplicated
   - Tax calculation duplicated
   - Needs refactoring

3. **Mock Data Stores**
   - All data lost on restart
   - Not production-ready

4. **Mocked Email Service**
   - Invoices not actually sent

### Missing Features ⏳

5. **Customer Portal**: Not implemented
6. **Invoice Corrections**: Not implemented
7. **Multi-Currency**: Partial (model only)
8. **Accounting Integration**: Not implemented
9. **Custom Branding**: Not implemented
10. **Advanced Tax Config**: Basic only

---

## Migration Path to Production

### Phase 1: Foundation (Week 1)

- [ ] Fix file header mislabeling
- [ ] Create comprehensive spec.md ✅
- [ ] Create Taiga stories (8 stories)
- [ ] Refactor overlap with SPEC-027

### Phase 2: Database Migration (Week 2)

- [ ] Create 8 database tables
- [ ] Write Alembic migrations
- [ ] Migrate from mock stores to PostgreSQL
- [ ] Update all endpoints to use database

### Phase 3: Customer Portal (Week 3)

- [ ] Implement portal access tokens
- [ ] Create portal API endpoints (6 endpoints)
- [ ] Build portal UI
- [ ] Test end-to-end portal flow

### Phase 4: Invoice Corrections (Week 4)

- [ ] Implement adjustment workflow
- [ ] Implement credit memo generation
- [ ] Implement void workflow
- [ ] Build correction UI

### Phase 5: Multi-Currency (Week 5)

- [ ] Integrate currency conversion API
- [ ] Implement conversion logic
- [ ] Update PDF generation for multi-currency
- [ ] Test with various currencies

### Phase 6: Accounting Integration (Week 6-7)

- [ ] CSV/Excel export
- [ ] QuickBooks OAuth integration
- [ ] Xero OAuth integration
- [ ] Test accounting sync

### Phase 7: Polish & Testing (Week 8)

- [ ] Complete test suite (80% coverage)
- [ ] Custom branding implementation
- [ ] Advanced tax configuration
- [ ] Production readiness checklist

**Total Timeline**: 8 weeks to full completion

---

## Related Documentation

- **SPEC-027**: [Billing Engine Integration](/specs/027-billing-engine-integration/spec.md) (payment processing)
- **SPEC-026**: [Standalone Teams & Billing](/specs/026-standalone-teams-billing/spec.md) (UI consumer)
- **SPEC-029**: [Subscription Management](/specs/029-subscription-management/) (subscription lifecycle)

---

## Contributors

- **Owner**: Arun Rajagopalan
- **Implementation**: Partial (743 lines, needs refactoring)
- **Testing**: Minimal (shared with SPEC-027)
- **Reviewers**: Needed (Platform Team)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-09-20 | 0.1 | Initial partial implementation (743 lines) |
| 2025-10-31 | 1.0 | Comprehensive documentation, gap analysis, refactoring plan |

---

## Approval

- [ ] **Product Owner**: _______________ Date: ___________
- [ ] **Engineering Lead**: _______________ Date: ___________
- [ ] **Finance Team**: _______________ Date: ___________ (accounting integration)
- [ ] **Customer Success**: _______________ Date: ___________ (portal UX)

---

**SPEC Status**: 🔄 **PARTIAL IMPLEMENTATION** (65% Complete)  
**Implementation**: 🟡 Partial (743 lines, overlaps with SPEC-027)  
**Testing**: 🟡 Minimal (shared tests)  
**Production Ready**: ❌ NO (needs portal, corrections, database)  
**Taiga Epic**: TO BE CREATED (8 stories needed)  
**Next Priority**: Refactor overlap, implement customer portal  
**Estimated Timeline**: 8 weeks to full completion
