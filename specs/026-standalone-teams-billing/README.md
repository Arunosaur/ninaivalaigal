# SPEC-026: Standalone Teams & Flexible Billing System

## Title
Standalone Team Management with Comprehensive Billing Infrastructure

## Objective
Enable flexible team collaboration without organizational overhead while providing comprehensive billing infrastructure including team-level quotas, discount codes, credits, and non-profit support.

## Overview

This SPEC defines how Ninaivalaigal supports **teams that are not part of any formal organization**, enabling flexible collaboration among individuals. It also introduces **team-level usage tracking, quotas, and billing** with comprehensive flexibility features for discounts, credits, and non-profit pricing models.

## Purpose

To allow groups of individuals to:

- Form a team without requiring an organization
- Record and share scoped memory
- View usage statistics and quotas
- Opt into paid plans for higher limits
- Convert to full organizations later
- Access flexible billing options including discounts and credits

## Core Features

### ✅ Standalone Team Creation

- Users may create a team without linking to an org
- Team structure:
  - `team_id`
  - `team_name`
  - `org_id` = `null`
- Users can belong to multiple standalone teams
- Teams can later be upgraded to full orgs

### ✅ Memory Scoping

- Memory entries can be associated to:
  - `user_id`
  - `team_id`
  - No `org_id` required
- Token context should reflect: `"team-only"`

### ✅ Team-Level Roles

- Team Lead
- Member
- Viewer (optional read-only role)
- Team Lead can invite/remove members

## Billing & Quotas

### Free Tier (Default)

- Up to 10 contexts
- 1,000 memories/month
- 1 GB memory size
- Up to 5 members

### Paid Tier (Starter)

- $10/month/team (configurable)
- Up to 50 contexts
- 25,000 memories/month
- 10 GB memory size
- Up to 25 members

### Non-Profit Plan

- Special pricing tier for verified non-profits
- Manual application with document upload (e.g., IRS 501(c)(3))
- Admin approval flow
- Non-profit plan benefits:
  - $5/month (or free)
  - 50 contexts
  - 100,000 memories/month
  - 20 GB storage

### Billing System

- Integration with Stripe or other billing provider
- Team-level customer ID
- UI for team payment portal
- View invoices and billing history
- Email receipts to team lead

## Billing Flexibility Features

### 🎫 Discount Codes

- Admin-generated discount codes
- Fixed (`$5 off`) or percentage-based (`25% off`)
- Expiry date and usage limits
- Applied during plan upgrade or billing cycle

### 💳 Free Credits

- Teams or orgs can be granted credits (e.g., $50 credit)
- Automatically deducted from future invoices
- Stackable with discounts
- Expires after specified period

### 🏛️ Non-Profit Support

- Verified non-profit organizations receive special pricing
- Document verification process
- Admin approval workflow
- Reduced rates or free access

## Technical Requirements

### Database Schema Extensions

```sql
-- Enhanced teams table for standalone teams
ALTER TABLE teams ADD COLUMN org_id INTEGER NULL;
ALTER TABLE teams ADD COLUMN billing_plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE teams ADD COLUMN billing_customer_id VARCHAR(255);

-- Discount codes system
CREATE TABLE discount_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    percent_off INTEGER,
    amount_off INTEGER, -- in cents
    expires_at TIMESTAMP,
    usage_limit INTEGER,
    used_count INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Credits system
CREATE TABLE team_credits (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    org_id INTEGER REFERENCES organizations(id),
    amount NUMERIC(10,2) NOT NULL, -- in dollars
    granted_by INTEGER REFERENCES users(id),
    expires_at TIMESTAMP,
    used_amount NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Non-profit applications
CREATE TABLE nonprofit_applications (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    org_id INTEGER REFERENCES organizations(id),
    organization_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    documentation_url TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage tracking for teams
CREATE TABLE team_usage_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    metric_name VARCHAR(50) NOT NULL, -- 'memories', 'contexts', 'api_calls'
    metric_value INTEGER NOT NULL,
    recorded_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

```http
# Standalone Team Management
POST /teams/create-standalone
GET /teams/{team_id}/members
POST /teams/{team_id}/invite
DELETE /teams/{team_id}/members/{user_id}

# Team Billing
GET /teams/{team_id}/billing
POST /teams/{team_id}/billing/upgrade
POST /teams/{team_id}/billing/apply-discount
GET /teams/{team_id}/usage

# Organization Conversion
POST /teams/{team_id}/convert-to-org

# Non-profit Applications
POST /teams/{team_id}/apply-nonprofit
GET /vendor/nonprofit-applications
PUT /vendor/nonprofit-applications/{id}/approve

# Credits & Discounts (Vendor Admin)
POST /vendor/discount-codes
POST /vendor/credits/grant
GET /vendor/billing/overview
```

## Usage Metrics

Tracked per team:

- Active members
- Total memories stored
- Tokenized size
- Monthly API calls
- Context count

Displayed in `team/settings/usage` dashboard.

## Team to Organization Upgrade

Allow teams to convert to organizations:

- Team Lead becomes Org Admin
- Existing members become org users
- Memory and context remain intact
- New `org_id` is issued
- Optional: Domain verification

## UI Features

### Team Management Pages

| Page | Description |
|------|-------------|
| `team/create.html` | Standalone team creation (no org required) |
| `team/dashboard.html` | Team memory and members overview |
| `team/usage.html` | Graphs for memory, context, and API usage |
| `team/billing.html` | Payment info, plan selection, invoices |
| `team/upgrade.html` | Guide to convert team into an org |

### Billing Enhancement Pages

| Page | Description |
|------|-------------|
| `team/billing/discount.html` | Apply promo codes |
| `team/billing/credits.html` | View credit balance and history |
| `team/nonprofit/apply.html` | Non-profit application form |

### Vendor Admin Console Extensions

| Page | Description |
|------|-------------|
| `vendor/discounts.html` | Manage discount codes |
| `vendor/credits.html` | Grant or revoke credits |
| `vendor/nonprofit.html` | Review non-profit applications |
| `vendor/billing-overview.html` | Usage vs. credit breakdown |

## Access Control

### Team Level
- Only team lead can:
  - Change plan
  - View billing info
  - Upgrade to organization
  - Apply discount codes
  - Submit non-profit applications

### Vendor Admin Level
- Only vendor_admin can:
  - Create/expire discount codes
  - Grant or revoke credits
  - Approve/reject non-profit applications
  - View comprehensive billing analytics

## Security Requirements

### Payment Security
- PCI compliance for payment processing
- Secure token storage for billing customer IDs
- Encrypted storage of sensitive billing data

### Access Control
- RBAC enforcement for all scoped actions
- Audit logging for all billing operations
- Rate limiting on discount code applications

## Success Criteria

- [ ] Standalone teams can be created without organizations
- [ ] Team-level billing and quota enforcement working
- [ ] Discount code system functional
- [ ] Credit system operational with automatic deduction
- [ ] Non-profit application and approval process working
- [ ] Team to organization conversion functional
- [ ] Usage analytics and reporting operational
- [ ] Stripe integration complete and tested

## Business Impact

### Market Expansion
- **Grassroots collaboration** support
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

## Implementation Priority

**Priority**: High (completes SaaS platform foundation)

### Dependencies
- SPEC-025 (Vendor Admin Console) for admin features
- Stripe or equivalent billing provider integration
- Database schema extensions
- Enhanced UI components

### Estimated Effort
- **Backend API**: 3-4 weeks
- **Billing Integration**: 2-3 weeks
- **Frontend UI**: 3-4 weeks
- **Admin Console**: 1-2 weeks
- **Testing & Security**: 2-3 weeks
- **Total**: 11-16 weeks

## Status
📋 Planned - Ready for implementation

## Notes

This SPEC allows Ninaivalaigal to support:

- **Flexible collaboration models** from individual to enterprise
- **Comprehensive billing infrastructure** with promotional capabilities
- **Inclusive pricing** supporting non-profits and community initiatives
- **Scalable growth path** from standalone teams to full organizations

It significantly expands usability, lowers entry barriers, and provides complete SaaS platform billing capabilities.
