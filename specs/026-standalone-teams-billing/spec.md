# SPEC-026: Standalone Teams and Billing

**Status**: 📋 **PLANNED** - Ready for Implementation
**Priority**: High (Completes SaaS Platform Foundation)
**Created**: 2024-09-23
**Updated**: 2025-10-31
**Authors**: Arun Rajagopalan
**Epic**: SPEC-026 (Taiga)

---

## Title

Standalone Team Accounts with Comprehensive Billing Infrastructure

---

## Objective

Enable creation and management of teams that are not tied to any parent organization, with full billing capabilities including payment processing, discount codes, credit systems, and non-profit support. This completes the SaaS platform foundation by providing a flexible, community-friendly pricing model that supports growth from individual → team → organization.

---

## Motivation

### Market Need

Many use cases require collaborative memory management but don't belong to formal organizations:
- **Small project teams** and working groups
- **Classroom/student collaborations**
- **Informal communities** or non-profits
- **Startups evaluating** the platform pre-onboarding
- **Freelancers and contractors** collaborating on projects

### Business Challenge

Requiring organization setup creates friction and limits adoption. Competitors offering team-first models have lower barriers to entry and higher conversion rates.

### Solution

Provide standalone teams with:
- Flexible billing (free → paid tiers)
- Promotional tools (discounts, credits)
- Social impact support (non-profit pricing)
- Scalable growth path to organizations

---

## Scope

### Inclusions

**Team Management:**
- ✅ Team creation without organization requirement
- ✅ Team-scoped RBAC (admin, contributor, viewer)
- ✅ Team invitation and join flows
- ✅ Upgrade path from standalone team to organization
- ✅ Team-isolated memory and context management

**Billing Infrastructure:**
- ✅ Payment processing via Stripe
- ✅ Multiple subscription tiers (Free, Team, Pro, Enterprise)
- ✅ Usage tracking and quota enforcement
- ✅ Invoice generation and delivery
- ✅ Automated billing cycles and prorations

**Promotional System:**
- ✅ Discount code creation and management
- ✅ Credit system (grant, revoke, auto-deduct)
- ✅ Non-profit application workflow
- ✅ Rate limiting and fraud prevention

**Vendor Admin Tools:**
- ✅ Discount code CRUD operations
- ✅ Credit management dashboard
- ✅ Non-profit application review
- ✅ Billing analytics and reporting

### Exclusions

- ❌ Organization-level features (handled by org upgrade)
- ❌ Cross-team collaboration (handled by SPEC-049/050)
- ❌ Advanced audit logs (organization-only feature)
- ❌ White-label billing (future SPEC)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ninaivalaigal Platform                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Individual User ──> Standalone Team ──> Organization       │
│     (Free)              (Free/Paid)          (Enterprise)   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Frontend (Next.js)  │
│  - Team Dashboard    │
│  - Billing Pages     │
│  - Usage Analytics   │
└──────────┬───────────┘
           │
           │ HTTPS/REST
           │
┌──────────▼────────────┐
│   Core API (Python)   │
│  - Team CRUD          │
│  - Billing APIs       │
│  - Discount/Credit    │
└──────────┬────────────┘
           │
           ├──────────┬───────────┬──────────┐
           │          │           │          │
    ┌──────▼───┐  ┌──▼───────┐ ┌▼──────┐  ┌▼────────┐
    │PostgreSQL│  │  Stripe  │ │ Redis │  │ Vendor  │
    │ (pgvector│  │    API   │ │ Cache │  │  Admin  │
    │  + RBAC) │  │          │ │       │  │ Console │
    └──────────┘  └──────────┘ └───────┘  └─────────┘
```

### Components

#### 1. Database Schema

**New Tables:**
```sql
-- Team billing configuration
CREATE TABLE team_billing (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    stripe_customer_id VARCHAR(255),
    subscription_tier VARCHAR(50), -- 'free', 'team', 'pro', 'enterprise'
    billing_email VARCHAR(255),
    payment_method_type VARCHAR(50),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Team subscriptions
CREATE TABLE team_subscriptions (
    id UUID PRIMARY KEY,
    team_billing_id UUID REFERENCES team_billing(id),
    stripe_subscription_id VARCHAR(255),
    plan_id VARCHAR(100),
    status VARCHAR(50), -- 'active', 'past_due', 'canceled', 'trialing'
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Discount codes
CREATE TABLE discount_codes (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    discount_type VARCHAR(20), -- 'percentage', 'fixed_amount'
    discount_value DECIMAL(10,2),
    max_redemptions INT,
    current_redemptions INT DEFAULT 0,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    applicable_plans TEXT[], -- Array of plan IDs
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Team credits
CREATE TABLE team_credits (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    balance DECIMAL(10,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    updated_at TIMESTAMPTZ
);

-- Credit transactions
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY,
    team_credit_id UUID REFERENCES team_credits(id),
    transaction_type VARCHAR(20), -- 'grant', 'deduct', 'expire'
    amount DECIMAL(10,2),
    reason TEXT,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ
);

-- Non-profit applications
CREATE TABLE nonprofit_applications (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    organization_name VARCHAR(255),
    tax_id VARCHAR(100),
    mission_statement TEXT,
    documentation_url TEXT,
    status VARCHAR(50), -- 'pending', 'approved', 'rejected'
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ
);

-- Team usage metrics
CREATE TABLE team_usage_metrics (
    id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(id),
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    memory_count INT DEFAULT 0,
    api_calls INT DEFAULT 0,
    storage_bytes BIGINT DEFAULT 0,
    recorded_at TIMESTAMPTZ
);
```

#### 2. API Endpoints

**Team Management:**
- `POST /auth/signup/team-create` - Create team during signup
- `POST /auth/signup/team-join` - Join team during signup
- `POST /team/create-standalone` - Create team from dashboard
- `GET /team/my` - Get current user's team info
- `POST /team/invite` - Send team invitations
- `POST /team/{id}/upgrade-to-org` - Upgrade team to organization

**Team Billing:**
- `GET /team/billing` - Get billing info and subscription status
- `POST /team/billing/payment-method` - Add/update payment method
- `GET /team/billing/invoices` - List invoices
- `POST /team/billing/change-plan` - Change subscription tier
- `POST /team/billing/cancel` - Cancel subscription

**Discounts & Credits:**
- `POST /team/billing/apply-discount` - Apply discount code
- `GET /team/billing/credits` - View credit balance and history
- `POST /nonprofit/apply` - Submit non-profit application

**Vendor Admin:**
- `POST /vendor/discounts` - Create discount code
- `GET /vendor/discounts` - List discount codes
- `PUT /vendor/discounts/{id}` - Update discount code
- `DELETE /vendor/discounts/{id}` - Delete/expire discount code
- `POST /vendor/credits/grant` - Grant credits to team
- `POST /vendor/credits/revoke` - Revoke credits from team
- `GET /vendor/nonprofit/applications` - List non-profit applications
- `POST /vendor/nonprofit/{id}/approve` - Approve application
- `POST /vendor/nonprofit/{id}/reject` - Reject application
- `GET /vendor/billing-overview` - Billing analytics dashboard

#### 3. Stripe Integration

**Webhook Events:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `charge.succeeded`
- `charge.failed`

**Integration Points:**
- Stripe Customers API (team billing)
- Stripe Subscriptions API (plan management)
- Stripe Payment Methods API (card storage)
- Stripe Invoices API (invoice generation)
- Stripe Webhook Events (real-time updates)

#### 4. Frontend Pages

**Team Pages:**
- `/team/create` - Standalone team creation
- `/team/dashboard` - Team memory and members overview
- `/team/usage` - Usage graphs (memory, context, API)
- `/team/billing` - Payment info, plan selection, invoices
- `/team/upgrade` - Upgrade guide (team → organization)

**Billing Enhancement Pages:**
- `/team/billing/discount` - Apply promo codes
- `/team/billing/credits` - View credit balance and history
- `/team/nonprofit/apply` - Non-profit application form

**Vendor Admin Console Extensions:**
- `/vendor/discounts` - Manage discount codes
- `/vendor/credits` - Grant or revoke credits
- `/vendor/nonprofit` - Review non-profit applications
- `/vendor/billing-overview` - Usage vs credit breakdown

---

## Dependencies

### Required SPECs (Must be Complete)

- ✅ **SPEC-006**: User Management, Authentication & Signup
- ✅ **SPEC-025**: Vendor Admin Console (admin interface foundation)
- ✅ **SPEC-027**: Billing Engine Integration (Stripe integration)

### Related SPECs (Integration Points)

- 🔄 **SPEC-028**: Invoice Management System (partial - needs enhancement)
- ✅ **SPEC-029**: Subscription Management (billing cycles)
- 📋 **SPEC-049**: Memory Sharing Collaboration (future team features)

---

## User Stories

### Team Lead Perspective

- [ ] As a startup founder, I want to create a team account so my co-founders can collaborate on memories without setting up an organization
- [ ] As a team admin, I want to invite members via email so they can join our shared workspace
- [ ] As a team lead, I want to upgrade to an organization when we're ready for enterprise features and billing

### Team Member Perspective

- [ ] As a student, I want to join a classroom team so I can share study materials with classmates
- [ ] As a freelancer, I want to contribute to a project team so we can collaborate on client work
- [ ] As a team contributor, I want to see team-scoped memories only so I'm not overwhelmed with irrelevant data

### Billing & Finance Perspective

- [ ] As a team admin, I want to add a payment method so we can upgrade to a paid plan
- [ ] As a billing user, I want to apply a discount code so we can reduce our subscription cost
- [ ] As a non-profit lead, I want to apply for special pricing so our limited budget goes further
- [ ] As a team owner, I want to view usage analytics so I can forecast our costs

### Vendor Admin Perspective

- [ ] As a vendor admin, I want to create discount codes so I can run promotional campaigns
- [ ] As a vendor admin, I want to grant credits to teams so I can resolve billing issues or reward loyalty
- [ ] As a vendor admin, I want to review non-profit applications so I can support social impact organizations
- [ ] As a vendor admin, I want to see billing analytics so I can optimize pricing and retention

---

## Acceptance Criteria

### Team Management

- [ ] Users can create standalone teams during signup or from dashboard
- [ ] Team invitations work via email with secure, expiring tokens
- [ ] RBAC is enforced within team boundaries (admin/contributor/viewer)
- [ ] Team members can only access team-scoped memories and contexts
- [ ] Standalone teams can upgrade to organizations seamlessly
- [ ] Team data is isolated at database level (no cross-team leaks)

### Billing Infrastructure

- [ ] Teams can add payment methods via Stripe
- [ ] Subscription tiers are enforced (Free, Team, Pro, Enterprise)
- [ ] Billing cycles are automated with prorations
- [ ] Invoices are generated and emailed automatically
- [ ] Failed payments trigger dunning management (retry logic)
- [ ] Usage is tracked and quota limits are enforced

### Promotional System

- [ ] Discount codes can be applied at checkout
- [ ] Credits automatically deduct from invoices
- [ ] Non-profit applications have approval workflow
- [ ] Discount code redemption limits are enforced
- [ ] Rate limiting prevents discount code abuse

### Security & Compliance

- [ ] PCI compliance through Stripe (no card data storage)
- [ ] Billing data is encrypted at rest
- [ ] Secure token storage for Stripe customer IDs
- [ ] Audit trail for all billing operations
- [ ] RBAC for vendor admin operations

---

## Implementation Phases

### Phase 1: Database & Core Models (Week 1-2)

**Deliverables:**
- Database schema migrations (7 new tables)
- Team billing models in SQLAlchemy
- Discount/credit system models
- Non-profit application models
- Unit tests for models (90%+ coverage)

**Success Criteria:**
- All migrations run successfully
- Foreign key constraints validated
- Indexes created for performance
- No migration rollback errors

### Phase 2: Backend APIs (Week 3-5)

**Deliverables:**
- Team CRUD endpoints (5 endpoints)
- Billing management APIs (5 endpoints)
- Discount/credit APIs (3 endpoints)
- Vendor admin APIs (8 endpoints)
- API documentation (OpenAPI/Swagger)
- Integration tests for all endpoints

**Success Criteria:**
- All API endpoints return correct responses
- Error handling is comprehensive
- Response times <200ms P95
- API tests pass in CI/CD

### Phase 3: Stripe Integration (Week 6-7)

**Deliverables:**
- Stripe customer creation/sync
- Subscription management logic
- Webhook handler for 8 events
- Invoice generation integration
- Payment failure handling (dunning)
- Stripe integration tests

**Success Criteria:**
- Webhooks process events correctly
- Subscriptions sync with Stripe
- Failed payments trigger retries
- Invoices generate successfully

### Phase 4: Frontend UI (Week 8-10)

**Deliverables:**
- Team creation flow pages
- Team dashboard and analytics
- Billing management UI (4 pages)
- Discount/credit UI (2 pages)
- Vendor admin billing UI (4 pages)
- E2E tests for critical flows

**Success Criteria:**
- All pages render correctly
- Forms validate input properly
- Analytics charts display data
- Mobile responsive design
- Accessibility (WCAG 2.1 AA)

### Phase 5: Testing & Security (Week 11-12)

**Deliverables:**
- Security audit report
- PCI compliance verification
- Load testing results
- End-to-end test suite
- Performance benchmarks
- Documentation and runbooks

**Success Criteria:**
- No HIGH/CRITICAL security issues
- PCI compliance confirmed
- Load tests pass (100 concurrent users)
- E2E tests pass in CI/CD
- Performance targets met

---

## Risks and Mitigations

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Stripe API changes break integration | HIGH | LOW | Use versioned API, comprehensive error handling |
| Database schema changes affect existing users | HIGH | MEDIUM | Careful migrations with rollback, extensive testing |
| Webhook event processing fails | MEDIUM | MEDIUM | Idempotent handlers, retry logic, dead letter queue |
| Performance issues with billing queries | MEDIUM | LOW | Database indexes, caching, query optimization |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Free teams create resource drain | MEDIUM | HIGH | Resource limits for free tier, conversion tracking |
| Discount code abuse | MEDIUM | MEDIUM | Rate limiting, redemption caps, fraud detection |
| Low team-to-org conversion rate | HIGH | MEDIUM | A/B test upgrade flows, incentives, analytics |
| PCI compliance failure | CRITICAL | LOW | Use Stripe fully (no card storage), regular audits |

### UX Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Three signup paths create confusion | MEDIUM | HIGH | Clear UI design, guided onboarding, user testing |
| Billing UI too complex | MEDIUM | MEDIUM | Simplify interface, progressive disclosure, help docs |
| Team isolation breaks expectations | LOW | LOW | Clear communication, tooltips, documentation |

---

## Success Metrics

### Adoption Metrics

- [ ] **Standalone team creation rate**: 20% of new signups
- [ ] **Team size distribution**: Average 3-5 members per team
- [ ] **Invitation acceptance rate**: >70% within 7 days

### Conversion Metrics

- [ ] **Free → Paid conversion**: 15% within 3 months
- [ ] **Team → Organization upgrade**: 15% within 6 months
- [ ] **Discount code usage**: 30% of paid teams
- [ ] **Non-profit approval rate**: >50% of valid applications

### Revenue Metrics

- [ ] **Average revenue per team**: $50/month
- [ ] **Lifetime value (LTV)**: >$600 per paid team
- [ ] **Churn rate**: <5% monthly for paid teams

### Engagement Metrics

- [ ] **User retention in teams vs individual**: 2x higher
- [ ] **Active users per team**: >60% monthly
- [ ] **Memory creation rate**: 20% higher in teams

---

## Performance Requirements

- **Team creation**: <500ms response time
- **Billing page load**: <1 second (with caching)
- **Stripe API calls**: <3 seconds timeout
- **Invoice generation**: <5 seconds for PDF
- **Webhook processing**: <2 seconds per event
- **Database queries**: <100ms for team-scoped reads

---

## Security Considerations

### Payment Security

- PCI DSS compliance through Stripe (Level 1 Service Provider)
- No credit card data stored in our database
- Secure token storage for Stripe customer IDs
- Encrypted billing data at rest (AES-256)
- TLS 1.3 for all API communication

### Access Control

- RBAC enforcement for team operations
- Vendor admin role for billing management
- Audit logging for all financial operations
- Rate limiting on discount code applications (10/hour)
- Team data isolation at database level

### Fraud Prevention

- Email verification for team creation
- CAPTCHA on signup forms
- Discount code redemption limits
- Unusual activity monitoring
- Failed payment threshold alerts

---

## Testing Strategy

### Unit Tests

- **Target Coverage**: 90%+ for business logic
- **Focus Areas**: Models, validators, calculations
- **Framework**: pytest with fixtures
- **Mocking**: Stripe API calls mocked

### Integration Tests

- **Target Coverage**: 100% of critical flows
- **Focus Areas**: API endpoints, database operations
- **Framework**: pytest with testcontainers
- **Database**: Isolated test PostgreSQL instance

### End-to-End Tests

- **Target Coverage**: All user flows
- **Focus Areas**: Signup, billing, upgrade paths
- **Framework**: Playwright
- **Environment**: Staging with test Stripe account

### Performance Tests

- **Tool**: Locust
- **Scenarios**: Team creation, billing queries, webhook processing
- **Target**: 100 concurrent users, <2s P95 response time

### Security Tests

- **Tools**: Bandit, OWASP ZAP, npm audit
- **Scenarios**: SQL injection, XSS, CSRF, API abuse
- **Frequency**: Every pull request

---

## Business Impact

### Market Expansion

- **Grassroots collaboration** support (small teams, classrooms)
- **Freelancers and informal collectives** enablement
- **Early-stage adoption** without organizational overhead
- **Community growth** through flexible pricing

### Revenue Optimization

- **Multiple pricing tiers** for different team sizes
- **Promotional capabilities** with discount codes
- **Customer retention** through credit systems
- **Social impact** through non-profit support

### Competitive Advantages

- **Lower entry barrier** than organization-only platforms
- **Flexible billing** accommodating various use cases
- **Community-friendly** pricing and support
- **Scalable growth path** from team to organization

### Strategic Value

- **Complete SaaS platform** with billing infrastructure
- **Monetization pipeline** from free to enterprise
- **Customer data** for pricing optimization
- **Market positioning** as team-first AI memory platform

---

## Related Documentation

- **SPEC-025**: [Vendor Admin Console](/specs/025-vendor-admin-console/)
- **SPEC-027**: [Billing Engine Integration](/specs/027-billing-engine-integration/)
- **SPEC-028**: [Invoice Management System](/specs/028-invoice-management-system/)
- **SPEC-029**: [Subscription Management](/specs/029-subscription-management/)
- **SPEC-066**: [Standalone Team Accounts](/specs/066-standalone-team-accounts/) - **DEPRECATED** (duplicate of this SPEC)

---

## Contributors

- **Owner**: Arun Rajagopalan
- **Reviewers**: Platform Team
- **Stakeholders**: Product, Engineering, Business Development, Finance

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-09-23 | 0.1 | Initial draft (malformed README) |
| 2025-10-31 | 1.0 | Complete rewrite following standard template, comprehensive technical design |

---

## Approval

- [ ] **Product Owner**: _______________ Date: ___________
- [ ] **Engineering Lead**: _______________ Date: ___________
- [ ] **Security Review**: _______________ Date: ___________
- [ ] **Finance/Legal**: _______________ Date: ___________

---

**SPEC Status**: 📋 **PLANNED** (Marked "Complete" in SPEC_INDEX.md erroneously - needs correction)
**Implementation**: NOT STARTED
**Taiga Epic**: TO BE CREATED
**Target Start**: Q1 2026
