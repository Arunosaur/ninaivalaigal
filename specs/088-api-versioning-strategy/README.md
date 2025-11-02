---
id: SPEC-088
owner: developer-b
phase: Infrastructure
sidebar_position: 88
start_date: 2025-10-08
status: Planned
tags:
- API
- Versioning
- Documentation
title: API Versioning Strategy
updated: 2025-11-02
---

# SPEC-088: API Versioning Strategy

**Status**: 📋 Planned (In Progress - Documentation Phase)
**Owner**: Developer B
**Taiga Story**: US#568
**Last Updated**: November 2, 2025

---

## Overview and Rationale

### **Purpose**

This specification defines the API versioning strategy for the Ninaivalaigal platform, ensuring:
- **Backward compatibility** for existing clients
- **Smooth migration paths** when breaking changes are necessary
- **Clear communication** of deprecation timelines
- **Predictable version lifecycle** management

### **Why API Versioning?**

As the platform evolves, we need to make breaking changes to improve the API:
- Rename fields for clarity
- Remove deprecated endpoints
- Change authentication mechanisms
- Restructure response formats
- Optimize performance

**Without versioning**: Breaking changes would break all existing clients immediately.
**With versioning**: Old and new versions coexist, giving clients time to migrate.

### **Goals**

1. ✅ **Stability**: Existing integrations continue working
2. ✅ **Flexibility**: Enable breaking changes when needed
3. ✅ **Clarity**: Clear version numbers and deprecation timelines
4. ✅ **Simplicity**: Easy for clients to understand and adopt

---

## Versioning Approach Decision (URL vs. Header)

### **Decision**: URL-Based Versioning (Path-Based)

We use **path-based major versioning** in the URL:

```
/api/v1/users
/api/v2/users
/api/v3/users
```

### **Why URL-Based?**

| Criterion | URL-Based | Header-Based | Winner |
|-----------|-----------|--------------|--------|
| **Simplicity** | ✅ Visible in URL | ❌ Hidden in headers | URL |
| **Cacheability** | ✅ Easy to cache | ❌ Complex cache keys | URL |
| **Debugging** | ✅ Clear in logs | ❌ Need to check headers | URL |
| **Browser Testing** | ✅ Works in browser | ❌ Need tools | URL |
| **Documentation** | ✅ Self-documenting | ❌ Requires explanation | URL |

### **Alternatives Considered**

#### **1. Header-Based Versioning** ❌ Not Used
```http
GET /api/users
Accept: application/vnd.ninaivalaigal.v2+json
```

**Pros**: URL stays clean
**Cons**: Hidden, harder to debug, complex caching

#### **2. Query Parameter Versioning** ❌ Not Used
```http
GET /api/users?version=2
```

**Pros**: Flexible
**Cons**: Easy to forget, inconsistent usage

#### **3. Subdomain Versioning** ❌ Not Used
```http
GET https://v2.api.ninaivalaigal.com/users
```

**Pros**: Complete separation
**Cons**: Complex infrastructure, SSL certificates

### **Our Choice**: URL-Based (Path) ✅

**Simple, visible, and works everywhere.**

---

## Version Numbering Scheme

### **Major Versions Only**

We use **major versions only** (v1, v2, v3), **not minor versions** (v1.1, v1.2).

**Format**: `/api/v{N}/`

**Examples**:
- `/api/v1/users` - Version 1
- `/api/v2/users` - Version 2
- `/api/v3/users` - Version 3

### **When to Increment Major Version**

**Increment when making breaking changes**:
- ❌ Renamed fields (e.g., `user_name` → `username`)
- ❌ Removed endpoints
- ❌ Changed authentication mechanism
- ❌ Modified response structure
- ❌ Changed required parameters

**Examples**:
- v1 → v2: Renamed `user_name` to `username`
- v2 → v3: Removed `/api/v2/legacy-endpoint`
- v3 → v4: Changed from JWT to OAuth2

### **Version Increment Rules**

1. **Never skip versions**: v1 → v2 → v3 (not v1 → v3)
2. **Start at v1**: First version is always v1
3. **No v0**: No beta versions in production URLs
4. **Sequential**: Always increment by 1

---

## Version Lifecycle (alpha, beta, stable, deprecated)

### **Lifecycle Stages**

Each API version goes through these stages:

```
Development → Beta (Optional) → Release → Deprecation → Sunset
```

### **1. Development Stage**

**Purpose**: Build and test new version internally

**Activities**:
- Create new version directory (`lib/api/v2/`)
- Implement breaking changes
- Write comprehensive tests
- Update OpenAPI schema
- Internal code review

**Duration**: Variable (weeks to months)

**Status**: Not publicly available

### **2. Beta Stage** (Optional)

**Purpose**: Early testing with select partners

**Activities**:
- Deploy to staging environment
- Internal team testing
- Early adopter feedback
- Performance validation
- Bug fixes

**Duration**: 2-4 weeks

**Status**: Available to beta testers only

**URL Format**: `/api/v2-beta/` (optional)

### **3. Release Stage (Active)**

**Purpose**: General availability for all clients

**Activities**:
- Deploy to production
- Both old and new versions available
- Announce to all stakeholders
- Publish migration guide
- Monitor adoption metrics

**Duration**: Indefinite (until next version)

**Status**: ✅ **Active** - Fully supported

**Support**: Full support, bug fixes, security patches

### **4. Deprecation Stage**

**Purpose**: Transition period for clients to migrate

**Activities**:
- Mark old version as deprecated
- Add deprecation warnings to responses
- Monitor usage metrics
- Provide migration support
- Send reminder notifications

**Duration**: 30-90 days (see [Deprecation Timeline](#deprecation-timeline))

**Status**: ⚠️ **Deprecated** - Still works but discouraged

**Support**: Security patches only, no new features

**Warnings**:
```http
HTTP/1.1 200 OK
X-API-Deprecated: true
X-API-Sunset-Date: 2025-12-22
X-API-Replacement: /api/v2/users
```

### **5. Sunset Stage**

**Purpose**: Remove old version from production

**Activities**:
- Remove old version endpoints
- Return 410 Gone for old endpoints
- Archive documentation
- Update all internal links
- Monitor for stragglers

**Duration**: Permanent

**Status**: ❌ **Removed** - No longer available

**Response**:
```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": "API_VERSION_REMOVED",
  "message": "API v1 was removed on 2025-12-22. Please use v2.",
  "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2"
}
```

---

## Multiple Version Support Policy

### **Support Matrix**

| Version | Status | Support Duration | Bug Fixes | New Features | Security Patches |
|---------|--------|------------------|-----------|--------------|------------------|
| **Current (vN)** | Active | Indefinite | ✅ Yes | ✅ Yes | ✅ Yes |
| **Current-1 (vN-1)** | Deprecated | 30-90 days | ❌ No | ❌ No | ✅ Yes |
| **Current-2 (vN-2)** | Removed | N/A | ❌ No | ❌ No | ❌ No |

### **Example Timeline**

**Scenario**: v3 is released

| Version | Status | Support |
|---------|--------|---------|
| v3 | ✅ Active | Full support |
| v2 | ⚠️ Deprecated | Security patches only (60 days) |
| v1 | ❌ Removed | No support |

**Scenario**: v2 is released

| Version | Status | Support |
|---------|--------|---------|
| v2 | ✅ Active | Full support |
| v1 | ⚠️ Deprecated | Security patches only (60 days) |

### **Maximum Concurrent Versions**

**Rule**: Support maximum of **2 versions** simultaneously (current + deprecated)

**Rationale**:
- Reduces maintenance burden
- Encourages timely migration
- Simplifies testing and deployment

---

## Breaking vs. Non-Breaking Changes

See [SPEC-089: Breaking Change Management](../089-breaking-change-management/README.md) for the complete breaking change management process, detection tools, and approval workflow.

**Summary:** Breaking changes require a new API version (v1 → v2). Non-breaking changes can be added to existing versions. For detailed examples and process, see [SPEC-089](../089-breaking-change-management/README.md).

**Related:** [breaking-changes.md](./breaking-changes.md) - Summary within versioning context

## Deprecation Timeline

### **Standard Timeline: 60 Days**

```
Day 0:  v2 released, v1 active
Day 30: v1 deprecated warning added
Day 60: v1 removed from production
Day 90: v1 archived
```

**Activities by Phase**:

| Day | Activity | Status | Communication |
|-----|----------|--------|---------------|
| 0 | New version released | v2 Active, v1 Active | Release announcement |
| 30 | Add deprecation warnings | v2 Active, v1 Deprecated | Deprecation notice |
| 45 | Send migration reminders | v2 Active, v1 Deprecated | Email to active users |
| 60 | Remove old version | v2 Active, v1 Removed | Sunset announcement |
| 90 | Archive documentation | v2 Active | Archive complete |

### **Extended Timeline: 90 Days**

**When to use**: Major versions with many active users

**Example**: v1 has 1000+ active integrations

**Timeline**:
```
Day 0:  v2 released
Day 30: v1 deprecation warning
Day 60: Migration reminder
Day 90: v1 removed
```

### **Accelerated Timeline: 30 Days**

**When to use**: Security-critical breaking changes

**Example**: Critical security vulnerability requires immediate API change

**Timeline**:
```
Day 0:  v2 released with security fix
Day 15: v1 deprecation warning
Day 30: v1 removed
```

**Requirements**:
- Security team approval
- Emergency communication plan
- 24/7 migration support

### **Deprecation Warning Implementation**

**HTTP Headers**:
```http
HTTP/1.1 200 OK
X-API-Deprecated: true
X-API-Sunset-Date: 2025-12-22
X-API-Replacement: /api/v2/users
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
```

**Response Body**:
```json
{
  "data": [...],
  "warnings": [
    {
      "code": "DEPRECATED_API_VERSION",
      "message": "API v1 is deprecated and will be removed on Dec 22, 2025.",
      "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2",
      "replacement": "/api/v2/users",
      "sunset_date": "2025-12-22"
    }
  ]
}
```

For complete deprecation policy, see [deprecation-policy.md](./deprecation-policy.md).

---

## Migration Path for Clients

### **Migration Guide Requirements**

Every version migration must include a comprehensive migration guide:

**Required Sections**:
1. **Overview** - What changed and why
2. **Breaking Changes** - Complete list with examples
3. **Migration Steps** - Step-by-step instructions
4. **Code Examples** - Before/after comparisons
5. **Timeline** - Deprecation and sunset dates
6. **Support** - How to get help

### **Example Migration Guide Structure**

```markdown
# Migration Guide: v1 → v2

## Overview
API v2 introduces improved field naming and response structure.

## Breaking Changes
1. Field renamed: `user_name` → `username`
2. Field renamed: `created_date` → `created_at`
3. Endpoint removed: `/api/v1/legacy-endpoint`

## Migration Steps
1. Update field names in your code
2. Test with v2 endpoints
3. Deploy to production
4. Monitor for errors

## Code Examples

### Before (v1)
```python
response = requests.get("/api/v1/users/123")
user_name = response.json()["user_name"]
```

### After (v2)
```python
response = requests.get("/api/v2/users/123")
username = response.json()["username"]
```

## Timeline
- Dec 1: v2 released
- Dec 31: v1 deprecated
- Jan 30: v1 removed

## Support
- Email: api-support@ninaivalaigal.com
- Slack: #api-migration
```

### **Client Migration Checklist**

**For API Consumers**:
- [ ] Read migration guide
- [ ] Identify affected endpoints
- [ ] Update code to use new version
- [ ] Test in staging environment
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Remove old version references

**For API Providers**:
- [ ] Write migration guide
- [ ] Add deprecation warnings
- [ ] Monitor usage metrics
- [ ] Provide migration support
- [ ] Send reminder emails
- [ ] Remove old version on sunset date

---

## Current Version Status

**As of November 2025**:

| Service | v1 Status | v2 Status | v3 Status |
|---------|-----------|-----------|-----------|
| **auth** | ✅ Active | - | - |
| **memory** | ✅ Active | - | - |
| **graph** | ✅ Active | - | - |
| **business** | ✅ Active | - | - |
| **admin** | ✅ Active | - | - |

**Note**: All services currently on v1. No versions deprecated or removed yet.

---

## Implementation Guidelines

### **For Developers**

**When creating a new version**:
1. Create version directory: `lib/api/v2/`
2. Copy relevant files from v1
3. Implement breaking changes
4. Update tests
5. Update OpenAPI schema
6. Write migration guide

**File Organization**:
```
lib/api/
├── v1/
│   ├── __init__.py
│   ├── auth.py
│   ├── memory.py
│   └── ...
├── v2/
│   ├── __init__.py
│   ├── auth.py
│   ├── memory.py
│   └── ...
└── versioning.py
```

**Router Setup**:
```python
from fastapi import APIRouter

# Version 1
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v1_router.include_router(auth_v1.router)
v1_router.include_router(memory_v1.router)

# Version 2
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
v2_router.include_router(auth_v2.router)
v2_router.include_router(memory_v2.router)

# Add to main app
app.include_router(v1_router)
app.include_router(v2_router)
```

---

## Related Documentation

- **[format.md](./format.md)** - API version format specifications and examples
- **[breaking-changes.md](./breaking-changes.md)** - Breaking change definitions and examples
- **[deprecation-policy.md](./deprecation-policy.md)** - Complete deprecation policy
- **[migration-guide.md](./migration-guide.md)** - Migration guide template
- **[compatibility-matrix.md](./compatibility-matrix.md)** - Version compatibility tracking
- **[SPEC-089](../089-breaking-change-management/README.md)** - Breaking change management process
- **[SPEC-087](../087-api-surface-contracts/README.md)** - API contract definitions

---

## References

- **Semantic Versioning**: https://semver.org/
- **API Versioning Best Practices**: https://restfulapi.net/versioning/
- **Stripe API Versioning**: https://stripe.com/docs/api/versioning
- **GitHub API Versioning**: https://docs.github.com/en/rest/overview/api-versions

---

**Last Updated**: November 2, 2025
**Status**: 📋 Planned (Documentation Phase)
**Next Steps**: Complete supporting documentation files
