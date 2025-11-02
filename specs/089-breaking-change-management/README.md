---
id: SPEC-089
owner: developer-b
phase: Infrastructure
sidebar_position: 89
start_date: 2025-01-27
status: Planned
tags:
- API
- Breaking Changes
- Change Management
- Documentation
title: Breaking Change Management
updated: 2025-01-27
---

# SPEC-089: Breaking Change Management

**Status:** 📋 **PLANNED** (Implementation: ~70% complete)
**Phase:** Phase 3
**Related SPECs:** [SPEC-088: API Versioning Strategy](../088-api-versioning-strategy/README.md)

---

## Overview and Rationale

SPEC-089 defines the **process and tools for managing breaking changes** in the API and contract system. While [SPEC-088](../088-api-versioning-strategy/README.md) defines the **versioning scheme** (how to version APIs), SPEC-089 defines **when breaking changes are allowed** and **how to detect, approve, and communicate them**.

### Purpose

Establish a comprehensive breaking change management system that:
- Detects breaking changes automatically in CI/CD
- Provides clear policy on when breaking changes are allowed
- Defines a rigorous 8-step process for introducing breaking changes
- Ensures proper communication and migration support
- Maintains API stability and backward compatibility

### Scope

**In Scope:**
- Breaking change detection (automated)
- Breaking change policy and approval process
- Migration guide requirements
- Deprecation workflow coordination
- Communication requirements

**Out of Scope:**
- API versioning scheme (covered by [SPEC-088](../088-api-versioning-strategy/README.md))
- Version routing infrastructure (covered by [SPEC-088](../088-api-versioning-strategy/README.md))
- Contract schema definition (covered by SPEC-100)

---

## Definition of Breaking Change

A **breaking change** is any modification that:
- Causes existing client code to fail
- Changes expected behavior
- Removes functionality
- Makes previously valid data invalid

### Examples of Breaking Changes ❌

**Endpoint Changes:**
- Removing an endpoint: `DELETE /api/v1/users/{id}`
- Removing an HTTP method: Removing `PATCH` from `/api/v1/users/{id}`
- Changing endpoint path: `/api/v1/users` → `/api/v1/people`

**Parameter Changes:**
- Adding a new required parameter
- Removing a required parameter
- Changing parameter type: `string` → `integer`

**Response Changes:**
- Removing a field from response schema
- Renaming a field: `user_name` → `full_name`
- Changing field type: `optional` → `required`
- Changing response status codes

**Schema Changes:**
- Removing a schema definition
- Making a field required that was optional
- Changing enum values

### Examples of Non-Breaking Changes ✅

**Safe Additions:**
- Adding a new optional field
- Adding a new optional parameter
- Adding a new endpoint
- Adding new enum values (without removing old ones)
- Adding new response fields (optional)

**Safe Modifications:**
- Adding documentation
- Improving error messages (without changing codes)
- Performance optimizations (behavior unchanged)
- Adding optional query parameters

---

## When Breaking Changes Are Allowed

### ✅ Allowed (with new version)

Breaking changes are allowed when:
- Major functionality changes are required
- Architectural improvements necessitate API changes
- Security fixes require incompatible changes
- Performance optimizations require API changes
- Business requirements demand breaking changes

**Requirement:** Breaking changes **MUST** create a new API version (see [SPEC-088: API Versioning Strategy](../088-api-versioning-strategy/README.md)).

### ❌ Never Allowed (in same version)

Breaking changes are **NEVER** allowed within the same version:
- Removing fields from v1 ❌
- Renaming fields in v1 ❌
- Changing types in v1 ❌
- Making fields more restrictive in v1 ❌

**All breaking changes require version increment:** v1 → v2, v2 → v3, etc.

---

## Process for Breaking Changes

### Step 1: Justify

Document why breaking change is necessary:
- Security vulnerability?
- Performance bottleneck?
- Design flaw?
- Business requirement?

**Deliverable:** Justification document with impact analysis.

### Step 2: Create New Version

Following [SPEC-088](../088-api-versioning-strategy/README.md) versioning scheme:

```bash
mkdir shared/contracts/my-service/v2
cp -r shared/contracts/my-service/v1/* shared/contracts/my-service/v2/
# Make breaking changes in v2 only
```

**Requirement:** Both versions must coexist during migration period.

### Step 3: Write Migration Guide

Create comprehensive migration guide:
- List all breaking changes
- Provide step-by-step migration instructions
- Include code examples (before/after)
- Document timeline and support

**Template:** See `migration-guide-template.md`

### Step 4: Get Approval

Required approvals:
- Architecture review
- Tech lead sign-off
- Product team notification
- Security team review (if applicable)

**Checklist:** See Review Checklist section.

### Step 5: Deploy Both Versions

Deploy both versions simultaneously:
```python
# FastAPI example
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")
```

**Requirement:** Both versions must be available during migration period.

### Step 6: Communicate

Communication channels:
- Slack announcement (#announcements)
- Email to stakeholders
- Documentation updates
- Deprecation warnings in API responses
- Changelog entries

**Timeline:** Communication should start 30-90 days before old version removal.

### Step 7: Monitor Migration

Track usage:
- Monitor v1 vs v2 usage metrics
- Contact teams still on v1
- Provide migration support
- Track migration progress

**Tools:** API analytics, usage metrics, client surveys.

### Step 8: Remove Old Version

Sunset process:
- Only after migration period (30-90 days)
- Only when v1 usage is zero or minimal
- Keep archived for reference
- Update documentation and links

**Timeline:** Standard is 60 days, extended to 90 days for major versions.

---

## Breaking Change Detection

### Automated Detection

**Implementation:** `ci/check-breaking-changes.py`

The breaking change detector automatically identifies:
- Removed endpoints
- Removed HTTP methods
- New required parameters (breaking)
- Removed schemas/components
- Contract file removal

**CI Integration:** Runs automatically on PR/push in `.github/workflows/contract-validation.yml`

**Usage:**
```bash
python ci/check-breaking-changes.py --base origin/main --head HEAD
```

### Detection Rules

The detector checks for:
1. **Removed Paths:** Any endpoint path that exists in base but not in head
2. **Removed Methods:** HTTP methods removed from existing paths
3. **New Required Parameters:** Parameters marked required in head but not in base
4. **Removed Schemas:** Schema definitions removed from components

### CI Enforcement

**Policy:** Breaking changes without version increment **fail the build**.

**Exceptions:** Breaking changes are allowed if:
- New version created (v2, v3, etc.)
- Migration guide provided
- Approval obtained
- Both versions deployed

---

## Review Checklist

Before approving a breaking change PR:

- [ ] New version created (v2, v3, etc.)
- [ ] Migration guide written and reviewed
- [ ] Timeline defined (minimum 30 days, standard 60 days)
- [ ] All stakeholders notified
- [ ] Both versions deployed
- [ ] Tests cover both versions
- [ ] Documentation updated
- [ ] Architecture review approved
- [ ] Security review completed (if applicable)
- [ ] Deprecation warnings added to old version

---

## Examples

### ✅ Good Breaking Change

**Scenario:** Security vulnerability in authentication flow

```
Problem: Security vulnerability in v1 auth flow
Solution: Create v2 with secure authentication
Timeline: 90 days migration period
Impact: All clients must upgrade
Justification: Security critical - outweighs migration cost
```

**Result:** ✅ **APPROVED** - Security justification sufficient

### ❌ Bad Breaking Change

**Scenario:** Developer preference for field name

```
Problem: Developer wants "name" → "full_name"
Solution: Rename field in v1
Impact: All clients break immediately
Justification: Cosmetic change - personal preference
```

**Result:** ❌ **REJECTED** - No justification, use v2 or keep v1 unchanged

---

## Deprecation Notice Requirements

When deprecating a version, include:

### HTTP Headers

```python
from fastapi import Response

@app.get("/api/v1/users", deprecated=True)
async def list_users_v1():
    return Response(
        headers={
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2025-12-22",
            "X-API-Replacement": "/api/v2/users",
            "Deprecation": "true",
            "Sunset": "Sun, 22 Dec 2025 00:00:00 GMT",
            "Link": "<https://docs.ninaivalaigal.io/migration/v1-to-v2>; rel=\"deprecation\""
        }
    )
```

### Response Body Warnings

```json
{
  "data": [...],
  "warnings": [
    {
      "code": "DEPRECATED_API_VERSION",
      "message": "API v1 is deprecated. Migrate to v2 by Dec 22, 2025.",
      "migration_guide": "https://docs.ninaivalaigal.io/migration/v1-to-v2"
    }
  ]
}
```

---

## Migration Guide Requirements

Each breaking change **must** include a migration guide with:

1. **Breaking Changes List**
   - All changed endpoints
   - All changed fields
   - All removed functionality

2. **Migration Steps**
   - Step-by-step instructions
   - Code examples (before/after)
   - Common pitfalls

3. **Timeline**
   - Version release date
   - Deprecation date
   - Sunset date

4. **Support**
   - Contact information
   - FAQ
   - Migration assistance

**Template:** See `migration-guide-template.md`

---

## Coordination with SPEC-088

SPEC-089 works with [SPEC-088: API Versioning Strategy](../088-api-versioning-strategy/README.md):

| Aspect | SPEC-088 | SPEC-089 |
|--------|----------|----------|
| **Focus** | Versioning scheme and infrastructure | Breaking change detection and process |
| **Scope** | HOW to version (v1, v2, etc.) | WHEN to version and HOW to manage changes |
| **Infrastructure** | Version routing, middleware | Detection scripts, CI enforcement |
| **Policy** | Version lifecycle, deprecation timelines | Breaking change approval, communication |

**Relationship:**
- SPEC-088 defines the **versioning infrastructure**
- SPEC-089 defines the **process for using it** when breaking changes occur

**Cross-Reference:** See [SPEC-088](../088-api-versioning-strategy/README.md) for versioning scheme details.

---

## Implementation Status

### ✅ Completed

1. **Breaking Change Detection Script**
   - File: `ci/check-breaking-changes.py` (175 lines)
   - Status: ✅ Complete and functional
   - Integration: CI/CD pipeline

2. **Breaking Change Policy Documentation**
   - File: `shared/contracts/docs/BREAKING_CHANGES.md` (98 lines)
   - Status: ✅ Complete
   - Content: Comprehensive 8-step process, examples, checklist

3. **CI Integration**
   - Workflow: `.github/workflows/contract-validation.yml`
   - Status: ✅ Integrated
   - Enforcement: Fails build on breaking changes without version bump

### 🔄 In Progress

1. **SPEC Directory Structure**
   - Status: 🔄 Being created
   - Next: Move documentation to SPEC structure

2. **Cross-References**
   - Status: 🔄 Being established
   - Next: Update SPEC-088 to reference SPEC-089

### ❌ Pending

1. **Enhanced Detection**
   - Database schema breaking changes
   - Protocol Buffer breaking changes
   - Additional breaking change patterns

2. **Migration Tools**
   - Automated migration script generation
   - Client SDK migration helpers

---

## Success Criteria

SPEC-089 will be considered **COMPLETE** when:

- [x] Breaking change detection script implemented
- [x] Breaking change policy documented
- [x] CI integration complete
- [ ] SPEC directory structure created
- [ ] Cross-references with SPEC-088 established
- [ ] Migration guide templates available
- [ ] All stakeholders aware of process

---

## References

- **[SPEC-088: API Versioning Strategy](../088-api-versioning-strategy/README.md)** - Versioning scheme and infrastructure
- **[SPEC-087: API Surface Contracts](../087-api-surface-contracts/README.md)** - API visibility and contracts
- **[SPEC-003: Core API Architecture](../003-core-api-architecture/README.md)** - Core API foundation
- **[SPEC-100: API Container Modularization](../100-api-container-modularization/README.md)** - Microservice contracts

**External Documentation:**
- `shared/contracts/docs/BREAKING_CHANGES.md` - Detailed policy (to be consolidated)
- `shared/contracts/docs/DEPRECATION.md` - Deprecation workflow
- `shared/contracts/docs/VERSIONING.md` - Version workflow
- `shared/contracts/docs/COMPATIBILITY.md` - Compatibility guidelines

---

**Status:** 📋 Planned - Implementation ~70% complete
**Next Steps:** Complete SPEC structure, enhance detection capabilities, coordinate with SPEC-088
