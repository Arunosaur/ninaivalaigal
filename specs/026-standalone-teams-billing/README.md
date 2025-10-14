---
{}
---


|-------------|
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
