# API Version Compatibility Matrix

**Last Updated**: November 2, 2025
**Related**: [SPEC-088: API Versioning Strategy](./README.md)

---

## Overview

This document tracks API version compatibility, support status, and deprecation timelines for the Ninaivalaigal platform.

**Purpose**: Provide a single source of truth for API version status and compatibility.

---

## Current API Versions

### **Version Status Summary**

| Version | Status | Released | Deprecated | Sunset | Support Level |
|---------|--------|----------|------------|--------|---------------|
| **v1** | ✅ Active | Nov 1, 2025 | - | - | Full support |
| **v2** | 📋 Planned | TBD | - | - | Not yet released |
| **v3** | 📋 Future | TBD | - | - | Not yet released |

**Legend**:
- ✅ **Active**: Fully supported, recommended for new integrations
- ⚠️ **Deprecated**: Still works but discouraged, security patches only
- ❌ **Removed**: No longer available, returns 410 Gone
- 📋 **Planned**: Not yet released

---

## Service-Specific Version Status

### **Core Services**

| Service | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| **Authentication** | ✅ Active | 📋 Planned | - | JWT-based auth |
| **Users** | ✅ Active | 📋 Planned | - | User management |
| **Memory** | ✅ Active | 📋 Planned | - | Memory CRUD operations |
| **Context** | ✅ Active | 📋 Planned | - | Context management |
| **Graph** | ✅ Active | 📋 Planned | - | Graph operations |
| **Teams** | ✅ Active | 📋 Planned | - | Team collaboration |
| **Organizations** | ✅ Active | 📋 Planned | - | Org management |

### **Business Services**

| Service | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| **Billing** | ✅ Active | 📋 Planned | - | Subscription management |
| **Invoices** | ✅ Active | 📋 Planned | - | Invoice generation |
| **Analytics** | ✅ Active | 📋 Planned | - | Usage analytics |
| **Admin** | ✅ Active | 📋 Planned | - | Admin console |

### **Compliance Services**

| Service | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| **GDPR** | ✅ Active | 📋 Planned | - | GDPR compliance |
| **HIPAA** | ✅ Active | 📋 Planned | - | HIPAA compliance |

---

## Version Support Timeline

### **v1 Timeline**

```
Nov 1, 2025    →    Active (Current)
    |
    └─→ Full support
        - All features supported
        - Bug fixes
        - Security patches
        - New features
```

**Status**: ✅ **Active**
**Released**: November 1, 2025
**Support Level**: Full support
**Recommended**: Yes

### **v2 Timeline** (Planned)

```
TBD           →    TBD           →    TBD
Release          Deprecate v1       Sunset v1
    |                |                 |
    └─→ Active       └─→ Deprecated    └─→ Removed
```

**Status**: 📋 **Planned**
**Estimated Release**: TBD
**Support Level**: Not yet available

---

## Breaking Changes by Version

### **v1 → v2** (Planned)

**Expected Breaking Changes**:
- Field naming convention changes (snake_case → camelCase)
- Timestamp format changes (date → ISO 8601)
- Error response structure changes
- Pagination format changes

**Migration Guide**: [v1-to-v2-migration.md](./migration-guide.md)

### **v2 → v3** (Future)

**Status**: Not yet planned

---

## Client SDK Compatibility

### **Official SDKs**

| SDK | v1 Support | v2 Support | v3 Support | Latest Version |
|-----|------------|------------|------------|----------------|
| **Python** | ✅ Yes | 📋 Planned | - | 1.0.0 |
| **JavaScript** | ✅ Yes | 📋 Planned | - | 1.0.0 |
| **TypeScript** | ✅ Yes | 📋 Planned | - | 1.0.0 |
| **Go** | 📋 Planned | - | - | Not yet released |
| **Ruby** | 📋 Planned | - | - | Not yet released |

### **SDK Version Requirements**

**Python SDK**:
- v1.x.x → API v1
- v2.x.x → API v2 (future)

**JavaScript SDK**:
- v1.x.x → API v1
- v2.x.x → API v2 (future)

---

## Feature Availability Matrix

### **Authentication Features**

| Feature | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| JWT Auth | ✅ | ✅ | - | Standard JWT |
| OAuth2 | ❌ | 📋 | - | Planned for v2 |
| API Keys | ✅ | ✅ | - | Available |
| SSO | ❌ | 📋 | - | Planned for v2 |

### **Memory Features**

| Feature | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| CRUD Operations | ✅ | ✅ | - | Basic operations |
| Vector Search | ✅ | ✅ | - | pgvector-based |
| Relevance Ranking | ✅ | ✅ | - | Redis-backed |
| Batch Operations | ❌ | 📋 | - | Planned for v2 |
| Streaming | ❌ | 📋 | - | Planned for v2 |

### **Graph Features**

| Feature | v1 | v2 | v3 | Notes |
|---------|----|----|-----|-------|
| Node Operations | ✅ | ✅ | - | Apache AGE |
| Relationship Queries | ✅ | ✅ | - | Cypher support |
| Graph Analytics | ❌ | 📋 | - | Planned for v2 |
| Path Finding | ✅ | ✅ | - | Basic paths |

---

## Deprecation Schedule

### **Active Deprecations**

Currently no versions are deprecated.

### **Planned Deprecations**

| Version | Deprecation Date | Sunset Date | Reason |
|---------|------------------|-------------|--------|
| v1 | TBD (when v2 releases) | TBD (60-90 days after) | Breaking changes in v2 |

---

## Migration Paths

### **Recommended Migration Timeline**

```
Current State    →    Transition    →    Target State
     v1          →    v1 + v2       →         v2
                      (60 days)
```

**Steps**:
1. **Day 0**: v2 released, begin testing
2. **Day 1-30**: Test v2 in staging
3. **Day 30-60**: Migrate production to v2
4. **Day 60**: Complete migration, remove v1 references

### **Supported Migration Paths**

| From | To | Supported | Migration Guide |
|------|----|-----------|-----------------|
| v1 | v2 | ✅ Yes | [v1-to-v2](./migration-guide.md) |
| v1 | v3 | ❌ No | Must migrate v1 → v2 → v3 |
| v2 | v3 | 📋 Future | TBD |

**Rule**: Never skip versions. Always migrate sequentially.

---

## Backward Compatibility

### **Within Same Version**

**v1 Compatibility Promise**:
- ✅ Adding optional fields: Safe
- ✅ Adding new endpoints: Safe
- ✅ Adding new enum values: Safe
- ❌ Removing fields: Breaking (requires v2)
- ❌ Renaming fields: Breaking (requires v2)
- ❌ Changing field types: Breaking (requires v2)

### **Across Versions**

**v1 → v2 Compatibility**:
- ❌ No backward compatibility guaranteed
- Breaking changes allowed
- Migration guide provided

---

## API Endpoint Inventory

### **v1 Endpoints**

**Authentication** (`/api/v1/auth/`):
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /refresh` - Token refresh
- `GET /me` - Current user info

**Users** (`/api/v1/users/`):
- `GET /users` - List users
- `GET /users/{id}` - Get user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

**Memory** (`/api/v1/memory/`):
- `GET /memories` - List memories
- `POST /memories` - Create memory
- `GET /memories/{id}` - Get memory
- `PUT /memories/{id}` - Update memory
- `DELETE /memories/{id}` - Delete memory
- `GET /relevant` - Get relevant memories

**Context** (`/api/v1/context/`):
- `GET /contexts` - List contexts
- `POST /contexts` - Create context
- `GET /contexts/{id}` - Get context
- `PUT /contexts/{id}` - Update context
- `DELETE /contexts/{id}` - Delete context

**Graph** (`/api/v1/graph/`):
- `POST /nodes` - Create node
- `POST /relationships` - Create relationship
- `GET /query` - Execute Cypher query

**Teams** (`/api/v1/teams/`):
- `GET /teams` - List teams
- `POST /teams` - Create team
- `GET /teams/{id}` - Get team
- `PUT /teams/{id}` - Update team
- `DELETE /teams/{id}` - Delete team

**Organizations** (`/api/v1/organizations/`):
- `GET /organizations` - List organizations
- `POST /organizations` - Create organization
- `GET /organizations/{id}` - Get organization
- `PUT /organizations/{id}` - Update organization
- `DELETE /organizations/{id}` - Delete organization

### **v2 Endpoints** (Planned)

TBD - Will be documented when v2 is released

---

## Performance Characteristics

### **Response Time SLOs**

| Endpoint Category | v1 P95 | v2 P95 (Target) | Notes |
|-------------------|--------|-----------------|-------|
| **Authentication** | <100ms | <50ms | Optimized in v2 |
| **CRUD Operations** | <200ms | <100ms | Improved queries |
| **Search/Query** | <500ms | <300ms | Better indexing |
| **Batch Operations** | N/A | <1000ms | New in v2 |

### **Rate Limits**

| Version | Authenticated | Unauthenticated | Burst |
|---------|---------------|-----------------|-------|
| **v1** | 1000 req/min | 100 req/min | 2x for 10s |
| **v2** | 1000 req/min | 100 req/min | 2x for 10s |

---

## Security & Compliance

### **Security Features by Version**

| Feature | v1 | v2 | v3 |
|---------|----|----|-----|
| **TLS 1.3** | ✅ | ✅ | - |
| **JWT Auth** | ✅ | ✅ | - |
| **OAuth2** | ❌ | 📋 | - |
| **Rate Limiting** | ✅ | ✅ | - |
| **IP Allowlisting** | ✅ | ✅ | - |
| **Audit Logging** | ✅ | ✅ | - |

### **Compliance Support**

| Compliance | v1 | v2 | v3 |
|------------|----|----|-----|
| **GDPR** | ✅ | ✅ | - |
| **HIPAA** | ✅ | ✅ | - |
| **SOC 2** | 📋 | 📋 | - |
| **ISO 27001** | 📋 | 📋 | - |

---

## Monitoring & Observability

### **Metrics Available**

| Metric | v1 | v2 | v3 |
|--------|----|----|-----|
| **Request Count** | ✅ | ✅ | - |
| **Response Time** | ✅ | ✅ | - |
| **Error Rate** | ✅ | ✅ | - |
| **Version Usage** | ✅ | ✅ | - |
| **Deprecation Warnings** | ✅ | ✅ | - |

### **Health Endpoints**

| Endpoint | v1 | v2 | v3 |
|----------|----|----|-----|
| `/health` | ✅ | ✅ | - |
| `/health/detailed` | ✅ | ✅ | - |
| `/health/live` | ✅ | ✅ | - |
| `/metrics` | ✅ | ✅ | - |

---

## Update History

### **Version History**

| Date | Version | Change | Impact |
|------|---------|--------|--------|
| Nov 1, 2025 | v1.0.0 | Initial release | N/A |

### **Compatibility Matrix Updates**

| Date | Update | Description |
|------|--------|-------------|
| Nov 2, 2025 | Initial | Created compatibility matrix |

---

## References

- **[SPEC-088: API Versioning Strategy](./README.md)** - Overall versioning approach
- **[breaking-changes.md](./breaking-changes.md)** - Breaking change definitions
- **[deprecation-policy.md](./deprecation-policy.md)** - Deprecation policy
- **[migration-guide.md](./migration-guide.md)** - Migration guide template
- **[format.md](./format.md)** - API version format specifications

---

**Last Updated**: November 2, 2025
**Status**: 📋 Planned (Documentation Phase)
**Next Review**: Upon v2 release or quarterly
