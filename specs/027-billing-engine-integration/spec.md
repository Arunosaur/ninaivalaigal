# SPEC-027: Billing Engine Integration

**Status**: ⚠️ **IMPLEMENTED BUT UNTESTED** (50% Complete)  
**Priority**: Critical (Revenue Infrastructure)  
**Created**: 2024-09-20  
**Updated**: 2025-10-31  
**Authors**: Arun Rajagopalan  
**Implementation**: Complete (769 lines)  
**Testing**: None (CRITICAL GAP)

---

## Title

Advanced Payment Processing Engine with Stripe Integration

---

## Objective

Provide a complete, production-ready billing infrastructure for ninaivalaigal platform with Stripe integration, automated webhook processing, invoice generation, payment retry logic, dunning management, and comprehensive billing analytics.

This SPEC serves as the **payment processing foundation** for SPEC-026 (Standalone Teams & Billing) and all revenue-generating features.

---

## Motivation

### Business Need

A SaaS platform requires robust, reliable payment processing:
- **Revenue Collection**: Automated subscription billing
- **Payment Failures**: Intelligent retry and dunning
- **Compliance**: PCI DSS via Stripe
- **Customer Experience**: Professional invoices and notifications
- **Business Intelligence**: Revenue analytics and churn prediction

### Technical Challenge

Payment processing is **revenue-critical infrastructure**:
- Single point of failure for revenue collection
- Requires 99.99% uptime
- Must handle webhook race conditions
- Needs comprehensive error handling
- Regulatory compliance requirements (PCI DSS)

### Solution

Complete billing engine with:
- Stripe API integration for payment processing
- Webhook event handling for real-time updates
- PDF invoice generation with tax calculations
- Automated payment retry with exponential backoff
- Dunning campaigns for failed payments
- Usage tracking for metered billing
- Billing analytics with churn risk scoring

---

## Scope

### Inclusions

**Payment Infrastructure:**
- ✅ Stripe customer creation and management
- ✅ Subscription lifecycle management
- ✅ Payment method handling
- ✅ Webhook event processing (3 critical events)
- ✅ Signature verification for security

**Billing Operations:**
- ✅ Invoice generation with PDF creation
- ✅ Tax calculation by jurisdiction (US states)
- ✅ Discount code application
- ✅ Credit/debit management
- ✅ Invoice delivery via email

**Failure Management:**
- ✅ Payment retry logic (3 strategies)
- ✅ Dunning campaigns (3 types)
- ✅ Customer notifications
- ✅ Escalation workflows

**Analytics & Tracking:**
- ✅ Usage tracking for metered billing
- ✅ Revenue metrics and KPIs
- ✅ Payment success/failure analytics
- ✅ Churn risk scoring

### Exclusions

- ❌ Multi-currency support (USD only for MVP)
- ❌ Alternative payment gateways (Stripe only)
- ❌ Cryptocurrency payments
- ❌ White-label billing
- ❌ Custom billing cycles (monthly only for MVP)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ninaivalaigal Platform                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │  SPEC-026    │─────>│  SPEC-027    │<─────│  Stripe   │ │
│  │  Team Billing│      │  Billing     │      │    API    │ │
│  │     UI       │      │   Engine     │      │           │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │      │
│         │                      │                     │      │
│         v                      v                     v      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastAPI Core (main.py)                     │  │
│  │    /billing-engine/* endpoints                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │              │
│         v                 v                 v              │
│  ┌───────────┐     ┌───────────┐     ┌──────────┐         │
│  │PostgreSQL │     │   Redis   │     │ ReportLab│         │
│  │ (Billing  │     │  (Cache)  │     │   (PDF)  │         │
│  │   Data)   │     │           │     │          │         │
│  └───────────┘     └───────────┘     └──────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

External Integration:
┌───────────────────┐
│   Stripe Cloud    │
│  - Customers API  │
│  - Subscriptions  │
│  - Webhooks       │
│  - Invoices       │
└───────────────────┘
```

### Components

#### 1. Stripe Customer Management

**File**: `server/billing_engine_integration_api.py` (lines 347-394)

**Endpoint**: `POST /billing-engine/customers/create`

**Functionality**:
- Creates Stripe customer with metadata
- Links customer to team in database
- Handles billing address and tax ID
- Stores customer data (currently in-memory, needs database migration)

**Request**:
```json
{
  "team_id": "uuid",
  "email": "team@example.com",
  "name": "Acme Team",
  "billing_address": {
    "line1": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US"
  },
  "tax_id": "12-3456789"
}
```

**Response**:
```json
{
  "message": "Stripe customer created successfully",
  "customer_id": "cus_xxx",
  "team_id": "uuid"
}
```

#### 2. Subscription Management

**Endpoint**: `POST /billing-engine/subscriptions/create`

**Functionality**:
- Creates Stripe subscription for customer
- Applies discount codes if provided
- Supports trial periods
- Handles prorations automatically
- Stores subscription data

**Request**:
```json
{
  "customer_id": "cus_xxx",
  "price_id": "price_team_monthly",
  "team_id": "uuid",
  "discount_code": "LAUNCH2026",
  "trial_days": 14
}
```

#### 3. Webhook Processing

**Endpoint**: `POST /billing-engine/webhooks/stripe`

**Security**: Webhook signature verification with `STRIPE_WEBHOOK_SECRET`

**Events Handled**:

1. **`invoice.payment_succeeded`**
   - Updates invoice status to "paid"
   - Records payment timestamp
   - Updates amount_paid
   - Actions: `["updated_invoice_status", "recorded_payment"]`

2. **`invoice.payment_failed`**
   - Records payment failure
   - Stores failure reason
   - Initiates retry sequence
   - Actions: `["recorded_payment_failure", "initiated_retry_sequence"]`

3. **`customer.subscription.updated`**
   - Updates subscription status
   - Updates billing period dates
   - Syncs subscription metadata
   - Actions: `["updated_subscription_status"]`

**Webhook Flow**:
```python
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    # 1. Verify signature
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
    
    # 2. Process event asynchronously
    background_tasks.add_task(process_payment_webhook, event)
    
    # 3. Return 200 immediately (Stripe requirement)
    return {"received": True}
```

#### 4. Invoice Generation

**Endpoint**: `POST /billing-engine/invoices/generate`

**Functionality**:
- Generates PDF invoices with ReportLab
- Calculates taxes by jurisdiction
- Applies discounts and credits
- Creates line items with descriptions
- Sends invoice via email (currently mocked)

**PDF Generation**:
```python
def generate_invoice_pdf(invoice_data):
    # Header: Company name and logo
    # Invoice details: Number, date, due date
    # Customer info: Team name, billing email
    # Line items table: Description, quantity, rate, amount
    # Subtotal, tax, total
    # Footer: Thank you message, support contact
    return pdf_bytes
```

**Tax Calculation** (US only for MVP):
```python
state_tax_rates = {
    "CA": 0.0875,  # California
    "NY": 0.08,    # New York
    "TX": 0.0625,  # Texas
    "FL": 0.06,    # Florida
}
```

#### 5. Payment Retry Logic

**Endpoint**: `POST /billing-engine/payments/retry`

**Retry Strategies**:

1. **Immediate**: Retry right away (manual trigger)
2. **Exponential Backoff**: 1h, 4h, 16h, 64h (automatic)
3. **Scheduled**: Custom schedule (e.g., end of month)

**Parameters**:
```json
{
  "invoice_id": "inv_xxx",
  "retry_strategy": "exponential",
  "max_retries": 3,
  "notify_customer": true
}
```

**Exponential Backoff Formula**:
```python
retry_delay = base_delay * (backoff_factor ** retry_count)
# Example: 3600s * (4 ** 0) = 1 hour
#          3600s * (4 ** 1) = 4 hours
#          3600s * (4 ** 2) = 16 hours
```

#### 6. Dunning Management

**Endpoint**: `POST /billing-engine/dunning/create` (implied in code)

**Campaign Types**:

1. **Standard**: Balanced approach (default)
   - Day 1: Friendly reminder
   - Day 3: Payment required notice
   - Day 7: Service suspension warning
   - Day 14: Account suspension

2. **Aggressive**: Fast escalation
   - Day 1: Immediate action required
   - Day 2: Service suspension warning
   - Day 3: Account suspension

3. **Gentle**: Lenient approach
   - Day 3: Polite reminder
   - Day 7: Payment request
   - Day 14: Gentle escalation
   - Day 30: Final notice

**Escalation Schedule**:
```json
{
  "team_id": "uuid",
  "invoice_id": "inv_xxx",
  "campaign_type": "standard",
  "escalation_days": [1, 3, 7, 14]
}
```

#### 7. Usage Tracking

**Endpoint**: `POST /billing-engine/usage/track`

**Metrics Tracked**:
- API calls (per endpoint)
- Memory operations (create, retrieve, update)
- Storage usage (bytes)
- Context operations
- Custom metrics

**Request**:
```json
{
  "team_id": "uuid",
  "metric_name": "api_calls",
  "metric_value": 1250,
  "timestamp": "2025-10-31T12:00:00Z",
  "metadata": {
    "endpoint": "/memory/create",
    "response_time_ms": 45
  }
}
```

#### 8. Billing Analytics

**Endpoint**: `GET /billing-engine/analytics/{team_id}?days=30`

**Analytics Provided**:

```json
{
  "team_id": "uuid",
  "current_period": {
    "start": "2025-10-01",
    "end": "2025-10-31",
    "days_remaining": 5,
    "billing_date": "2025-11-01"
  },
  "revenue_metrics": {
    "mrr": 500.00,
    "arr": 6000.00,
    "lifetime_value": 1500.00
  },
  "payment_metrics": {
    "success_rate": 0.98,
    "failed_count": 2,
    "retry_success_rate": 0.75,
    "average_payment_time_hours": 2.5
  },
  "usage_trends": [
    {
      "date": "2025-10-30",
      "api_calls": 1250,
      "memory_operations": 340,
      "storage_gb": 2.5
    }
  ],
  "churn_risk_score": 0.12
}
```

**Churn Risk Factors**:
- Payment failure frequency
- Support ticket volume
- Usage decline
- Subscription downgrades
- Engagement metrics

---

## Database Schema (NEEDS MIGRATION)

### Current State: In-Memory Dictionaries ⚠️

**Problem**: Data lost on restart, not production-ready

```python
# Current implementation (NOT PERSISTENT)
stripe_customers_store: dict = {}
stripe_subscriptions_store: dict = {}
billing_invoices_store: dict = {}
payment_attempts_store: dict = {}
dunning_campaigns_store: dict = {}
```

### Required Tables (Aligns with SPEC-026 US-200-202)

```sql
-- Stripe customer mapping
CREATE TABLE stripe_customers (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    billing_address JSONB,
    tax_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscription management
CREATE TABLE stripe_subscriptions (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) REFERENCES stripe_customers(stripe_customer_id),
    price_id VARCHAR(100),
    status VARCHAR(50), -- active, past_due, canceled, trialing
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoice tracking
CREATE TABLE billing_invoices (
    id UUID PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    team_id UUID REFERENCES teams(id),
    stripe_invoice_id VARCHAR(255),
    amount_due DECIMAL(10,2),
    amount_paid DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2),
    status VARCHAR(50), -- draft, open, paid, void, uncollectible
    due_date TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    pdf_url TEXT,
    line_items JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_team ON billing_invoices(team_id);
CREATE INDEX idx_invoices_status ON billing_invoices(status);

-- Payment retry tracking
CREATE TABLE payment_attempts (
    id UUID PRIMARY KEY,
    invoice_id UUID REFERENCES billing_invoices(id),
    team_id UUID REFERENCES teams(id),
    attempt_number INT,
    failure_reason TEXT,
    retry_strategy VARCHAR(50),
    next_retry_at TIMESTAMPTZ,
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dunning campaigns
CREATE TABLE dunning_campaigns (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    invoice_id UUID REFERENCES billing_invoices(id),
    campaign_type VARCHAR(50),
    current_step INT DEFAULT 0,
    escalation_days INT[],
    status VARCHAR(50), -- active, completed, canceled
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Usage metrics
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    metric_name VARCHAR(100),
    metric_value BIGINT,
    metadata JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_team_metric ON usage_metrics(team_id, metric_name);
CREATE INDEX idx_usage_recorded ON usage_metrics(recorded_at);
```

---

## Dependencies

### Required SPECs (Must Be Complete)

- ✅ **SPEC-006**: User Management & Authentication (JWT, teams)
- ✅ **PostgreSQL**: Database infrastructure
- ✅ **FastAPI**: Web framework

### Related SPECs (Integration Points)

- ⏳ **SPEC-026**: Standalone Teams & Billing (depends on this SPEC)
- ✅ **SPEC-028**: Invoice Management System (complementary)
- ✅ **SPEC-029**: Subscription Management (complementary)

### External Dependencies

- **Stripe API**: v2023-10-16 or later
- **stripe-python**: v7.8.0+ (already in requirements.txt)
- **reportlab**: v4.0.7+ (already in requirements.txt)
- **Email Service**: SendGrid or AWS SES (NOT YET INTEGRATED)

---

## API Specifications

### Authentication

All endpoints require JWT authentication:
```python
current_user: User = Depends(get_current_user)
```

### Base Path

```
/billing-engine/*
```

### Endpoints Summary

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/customers/create` | Required | Create Stripe customer |
| POST | `/subscriptions/create` | Required | Create subscription |
| POST | `/webhooks/stripe` | Webhook Sig | Process Stripe events |
| POST | `/invoices/generate` | Required | Generate invoice |
| POST | `/payments/retry` | Required | Retry failed payment |
| POST | `/usage/track` | Required | Track usage metrics |
| GET | `/analytics/{team_id}` | Required | Get billing analytics |
| POST | `/dunning/create` | Required | Create dunning campaign |

---

## Security Considerations

### Implemented ✅

1. **Webhook Signature Verification**
   ```python
   event = stripe.Webhook.construct_event(
       payload, sig_header, STRIPE_WEBHOOK_SECRET
   )
   ```

2. **Environment Variables for Secrets**
   ```python
   stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
   STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
   ```

3. **JWT Authentication**
   - All endpoints require authentication
   - Team ownership validation

4. **PCI Compliance**
   - No credit card data stored locally
   - All payment data handled by Stripe

### Missing ⚠️

1. **Rate Limiting**
   - Webhook endpoint needs rate limiting
   - API endpoints need throttling

2. **Audit Logging**
   - All billing operations should be logged
   - Admin actions need audit trail

3. **RBAC for Analytics**
   - Billing analytics should require team_admin role
   - Sensitive data needs role-based access

4. **Encryption at Rest**
   - Billing data should be encrypted in database
   - Invoice PDFs should be encrypted in storage

---

## Testing Strategy (CRITICAL GAP - NOT IMPLEMENTED)

### Unit Tests (0% Coverage - NEEDS IMPLEMENTATION)

**Priority Tests**:
1. Invoice PDF generation
2. Tax calculation accuracy (all US states)
3. Discount code validation
4. Credit/debit calculations
5. Webhook signature verification
6. Retry logic (exponential backoff)
7. Churn risk scoring algorithm

**Estimated**: 40-50 unit tests

### Integration Tests (NOT IMPLEMENTED)

**Priority Tests**:
1. Stripe customer creation (mocked)
2. Subscription lifecycle (create, update, cancel)
3. Webhook event processing (all 3 events)
4. Invoice generation end-to-end
5. Payment retry workflow
6. Dunning campaign execution

**Estimated**: 15-20 integration tests

### E2E Tests (NOT IMPLEMENTED)

**Priority Scenarios**:
1. Complete billing flow (customer → subscription → invoice → payment)
2. Payment failure → retry → success
3. Payment failure → dunning → cancellation
4. Webhook race conditions
5. Concurrent payment processing

**Estimated**: 5-8 E2E tests

---

## Performance Requirements

- **API Response Time**: <200ms P95
- **Webhook Processing**: <2 seconds
- **Invoice PDF Generation**: <5 seconds
- **Concurrent Webhooks**: Handle 100 simultaneous events
- **Database Queries**: <100ms for analytics
- **Stripe API Calls**: <3 seconds timeout

---

## Monitoring & Alerting (NOT IMPLEMENTED)

### Required Metrics

- Stripe API success/failure rate
- Webhook processing time
- Payment success rate
- Invoice generation rate
- Dunning campaign effectiveness
- Churn risk distribution

### Required Alerts

- Payment processing failures (>1% failure rate)
- Webhook processing delays (>5 seconds)
- Stripe API errors (>5 in 5 minutes)
- Invoice generation failures
- Subscription cancellations (spike detection)

---

## Business Impact

### Revenue Infrastructure

SPEC-027 is the **payment processing engine** for all revenue:
- Processes 100% of subscriptions
- Handles 100% of payment events
- Generates 100% of invoices
- Manages 100% of payment failures

**Criticality**: VERY HIGH - Single point of failure for revenue

### Success Metrics

- **Payment Success Rate**: >98%
- **Webhook Processing**: 100% of events handled
- **Invoice Delivery**: 100% sent within 1 hour
- **Retry Success**: >75% of failed payments recovered
- **Dunning Effectiveness**: >50% of past_due accounts recovered

---

## Known Issues & Technical Debt

### Critical Issues ❌

1. **Zero Test Coverage**
   - No validation of revenue-critical code
   - High risk for production bugs

2. **In-Memory Data Stores**
   - Data lost on restart
   - Not production-ready
   - Needs database migration

3. **Mocked Email Service**
   - Invoices not actually sent
   - Needs SendGrid/SES integration

### Medium Priority 🟡

4. **No Rate Limiting**
   - Webhook endpoint vulnerable to abuse
   - API endpoints need throttling

5. **No Audit Logging**
   - Billing operations not tracked
   - Compliance risk

6. **Limited Tax Support**
   - US states only
   - Needs international tax handling

7. **No Multi-Currency**
   - USD only
   - Limits international customers

---

## Migration Path to Production

### Phase 1: Database Migration (Week 1)

- [ ] Create 6 database tables
- [ ] Write Alembic migrations
- [ ] Migrate from in-memory to PostgreSQL
- [ ] Update all endpoints to use database

### Phase 2: Email Integration (Week 1-2)

- [ ] Choose email service (SendGrid vs AWS SES)
- [ ] Create invoice email templates
- [ ] Implement email sending
- [ ] Test delivery and formatting

### Phase 3: Testing (Week 2-3)

- [ ] Unit tests (40-50 tests, 80% coverage)
- [ ] Integration tests (15-20 tests)
- [ ] E2E tests (5-8 scenarios)
- [ ] Stripe webhook simulation

### Phase 4: Security & Compliance (Week 4)

- [ ] Implement rate limiting
- [ ] Add audit logging
- [ ] Security audit
- [ ] PCI compliance verification

### Phase 5: Production Readiness (Week 5)

- [ ] Load testing (100 concurrent webhooks)
- [ ] Monitoring and alerting setup
- [ ] Incident response runbook
- [ ] Production Stripe account configuration

**Total Timeline**: 5 weeks to production-ready

---

## Related Documentation

- **SPEC-026**: [Standalone Teams & Billing](/specs/026-standalone-teams-billing/spec.md)
- **SPEC-028**: [Invoice Management System](/specs/028-invoice-management-system/)
- **SPEC-029**: [Subscription Management](/specs/029-subscription-management/)
- **Stripe Documentation**: https://stripe.com/docs/api

---

## Contributors

- **Owner**: Arun Rajagopalan
- **Implementation**: Complete (769 lines)
- **Testing**: NOT STARTED (CRITICAL)
- **Reviewers**: Needed (Platform Team)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-09-20 | 0.1 | Initial implementation (769 lines) |
| 2025-10-31 | 1.0 | Comprehensive documentation created, critical gaps identified |

---

## Approval

- [ ] **Product Owner**: _______________ Date: ___________
- [ ] **Engineering Lead**: _______________ Date: ___________
- [ ] **Security Review**: _______________ Date: ___________ (CRITICAL)
- [ ] **Finance/Legal**: _______________ Date: ___________

---

**SPEC Status**: ⚠️ **IMPLEMENTED BUT UNTESTED** (50% Complete)  
**Implementation**: ✅ Complete (769 lines, 8 endpoints)  
**Testing**: ❌ None (CRITICAL GAP)  
**Production Ready**: ❌ NO (needs database, email, tests)  
**Taiga Epic**: TO BE CREATED (8 testing stories)  
**Next Priority**: Testing & validation (3-4 weeks)
