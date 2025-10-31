---
{}
---


|---------|
| `vendor/dashboard.html` | Global stats and system health |
| `vendor/orgs.html` | List/search orgs → drill-down into teams/users |
| `vendor/usage.html` | Memory usage graphs per org/team/user |
| `vendor/rate-limits.html` | Configure and enforce quota settings |
| `vendor/tokens.html` | JWT/token dashboard |
| `vendor/logs.html` | Error log viewer |
| `vendor/settings.html` | System settings, global overrides |

### API Endpoints

```http
# Tenant Management
GET /vendor/tenants
POST /vendor/tenants/{id}/suspend
PUT /vendor/tenants/{id}/quotas

# Usage Analytics
GET /vendor/usage/stats
GET /vendor/usage/by-org/{org_id}
GET /vendor/usage/by-user/{user_id}

# Rate Limiting
GET /vendor/rate-limits
PUT /vendor/rate-limits/{tenant_id}
GET /vendor/rate-limits/violations

# System Health
GET /vendor/health/system
GET /vendor/health/services
GET /vendor/health/database

# Token Management
GET /vendor/tokens/active
POST /vendor/tokens/{token_id}/invalidate
PUT /vendor/tokens/{user_id}/scope-override

# Audit Logs
GET /vendor/audit/logs
GET /vendor/audit/export
POST /vendor/audit/search
```

### Database Schema Extensions

```sql
-- Usage statistics tracking
CREATE TABLE usage_stats (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    tenant_type VARCHAR(20), -- 'user', 'team', 'organization'
    metric_name VARCHAR(50),
    metric_value INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Rate limiting configuration
CREATE TABLE rate_limits (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    tenant_type VARCHAR(20),
    limit_type VARCHAR(50), -- 'requests_per_hour', 'memory_per_month'
    limit_value INTEGER,
    current_usage INTEGER DEFAULT 0,
    reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit logging (if not exists)
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vendor admin roles
ALTER TABLE users ADD COLUMN vendor_role VARCHAR(20);
-- Values: NULL, 'vendor_admin', 'vendor_support'
```

## Access Control

- Only users with `role: "vendor_admin"` may access this UI
- Requires separate login or SSO (TBD)
- All actions logged in `audit_log` table
- Multi-factor authentication required for destructive operations

## Security Requirements

### Authentication & Authorization
- Separate vendor admin authentication flow
- Role-based access control with `vendor_admin` role
- Session management with secure tokens
- IP whitelisting for vendor admin access

### Audit & Compliance
- Complete audit trail for all vendor actions
- Immutable audit logs with cryptographic integrity
- Compliance reporting capabilities
- Data retention policies for audit logs

## Success Criteria

- [ ] Vendor admin console accessible with proper authentication
- [ ] All tenant management operations working
- [ ] Real-time usage statistics and monitoring
- [ ] Rate limiting enforcement functional
- [ ] Complete audit logging implemented
- [ ] System health monitoring operational
- [ ] Token management capabilities working
- [ ] Export/reporting features functional

## Business Impact

### Medhasys-as-a-Service Enablement
- **Multi-tenant SaaS platform** with vendor control
- **Subscription management** foundation
- **Usage-based billing** preparation
- **Enterprise compliance** capabilities

### Operational Benefits
- **Proactive monitoring** of platform health
- **Automated quota enforcement**
- **Rapid issue resolution** with comprehensive logs
- **Scalable tenant management**

## Implementation Priority

**Priority**: Medium-High (enables SaaS business model)

### Dependencies
- JWT token model must support `role: vendor_admin`
- FastAPI must expose `/vendor/...` endpoints with scoped access
- Database schema extensions required
- Separate vendor authentication system

### Estimated Effort
- **Backend API**: 2-3 weeks
- **Frontend Console**: 2-3 weeks
- **Database Schema**: 1 week
- **Testing & Security**: 1-2 weeks
- **Total**: 6-9 weeks

## Status
📋 Planned - Ready for implementation

---

## Related Documentation

### Components
- **Backend API:** `/vendor/*` endpoints in admin-vendor-service
- **Frontend Console:** Vendor admin dashboard (to be built)
- **Database:** usage_stats, rate_limits, audit_log tables

### Related SPECs
- **SPEC-009:** RBAC Policy Enforcement (vendor_admin role)
- **SPEC-018:** API Health Monitoring (system health integration)
- **SPEC-101:** Unified Observability (usage metrics)
- **SPEC-026-030:** Billing & Analytics (future integration)

### Taiga Tracking
- **US#155:** SPEC-025 Vendor Admin Console Implementation

---

## Implementation Status

📋 **PLANNED** - Not yet implemented

**Business Priority:** Medium-High (enables SaaS business model)

**Key Benefits:**
- Transforms ninaivalaigal into enterprise SaaS platform
- Enables multi-tenant subscription management
- Foundation for usage-based billing
- Enterprise compliance capabilities

**Estimated Effort:** 6-9 weeks

---

**Last Updated:** October 30, 2025 (Taiga tracking added)
**Status:** Tracked in Taiga US#155

## Notes

- This SPEC enables **Medhasys-as-a-Service**
- Paves the way for multi-tenant subscription management
- Essential for future billing/reporting (e.g., per-org pricing)
- Transforms ninaivalaigal from tool to enterprise SaaS platform
