# Breaking Changes

**Related:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md) for the complete breaking change management process.

## Overview

This document provides a **summary** of breaking change considerations within the context of API versioning. For the **full breaking change management process**, detection tools, and approval workflow, see [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md).

---

## Definition of a Breaking Change

A **breaking change** is any modification that:
- Causes existing client code to fail
- Changes expected behavior
- Removes functionality
- Makes previously valid data invalid

**For full definition and examples:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#definition-of-breaking-change)

---

## Breaking Changes Require New Version

**Key Principle:** Breaking changes **MUST** trigger a new API version increment.

- Breaking change in v1 → Create v2
- Breaking change in v2 → Create v3
- Never make breaking changes within the same version

**For versioning scheme:** See [SPEC-088: API Versioning Strategy README](./README.md)

**For breaking change process:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#process-for-breaking-changes)

---

## Examples of Breaking Changes

### 1. Endpoint Changes ❌

#### Removing an Endpoint
```python
# v1 - Has endpoint
GET /api/v1/legacy-users

# v2 - Endpoint removed (BREAKING)
# 404 Not Found
```

#### Removing an HTTP Method
```python
# v1 - Supports DELETE
DELETE /api/v1/users/123

# v2 - DELETE removed (BREAKING)
# 405 Method Not Allowed
```

#### Changing Endpoint Path
```python
# v1
GET /api/v1/user-profiles

# v2 - Path changed (BREAKING)
GET /api/v2/profiles
```

### 2. Parameter Changes ❌

#### Adding Required Parameter
```python
# v1 - email optional
POST /api/v1/users
{"name": "John"}

# v2 - email required (BREAKING)
POST /api/v2/users
{"name": "John", "email": "john@example.com"}  # email now required
```

#### Removing Parameter
```python
# v1 - Accepts legacy_id
POST /api/v1/users
{"name": "John", "legacy_id": "123"}

# v2 - legacy_id removed (BREAKING)
POST /api/v2/users
{"name": "John"}  # legacy_id no longer accepted
```

#### Changing Parameter Type
```python
# v1 - user_id is string
GET /api/v1/users?user_id="abc123"

# v2 - user_id is integer (BREAKING)
GET /api/v2/users?user_id=123
```

### 3. Response Changes ❌

#### Removing Field
```json
// v1 - Has legacy_name field
{
  "id": 123,
  "name": "John",
  "legacy_name": "john_doe"
}

// v2 - legacy_name removed (BREAKING)
{
  "id": 123,
  "name": "John"
}
```

#### Renaming Field
```json
// v1
{
  "user_name": "john_doe"
}

// v2 - Field renamed (BREAKING)
{
  "username": "john_doe"
}
```

#### Changing Field Type
```json
// v1 - created_at is string
{
  "created_at": "2025-11-02"
}

// v2 - created_at is ISO timestamp (BREAKING)
{
  "created_at": "2025-11-02T08:00:00Z"
}
```

### 4. Authentication Changes ❌

```python
# v1 - JWT token
Authorization: Bearer eyJhbGc...

# v2 - OAuth2 required (BREAKING)
Authorization: OAuth oauth_token="abc123"
```

### 5. Error Response Changes ❌

```json
// v1 - Simple error format
{
  "error": "User not found"
}

// v2 - Structured error format (BREAKING)
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": {}
  }
}
```

**For comprehensive examples:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#examples-of-breaking-changes)

---

## Examples of Non-Breaking Changes

### 1. Safe Additions ✅

#### Adding Optional Fields
```json
// v1
{
  "id": 123,
  "name": "John"
}

// v1 (later) - Added optional field (NON-BREAKING)
{
  "id": 123,
  "name": "John",
  "email": "john@example.com"  // New optional field
}
```

#### Adding Optional Parameters
```python
# v1
POST /api/v1/users
{"name": "John"}

# v1 (later) - Added optional parameter (NON-BREAKING)
POST /api/v1/users
{"name": "John", "email": "john@example.com"}  # email is optional
```

#### Adding New Endpoints
```python
# v1 - Original endpoints
GET /api/v1/users
POST /api/v1/users

# v1 (later) - Added new endpoint (NON-BREAKING)
GET /api/v1/users/search  # New endpoint
```

#### Adding Enum Values
```python
# v1 - Status enum
status: "active" | "inactive"

# v1 (later) - Added new value (NON-BREAKING)
status: "active" | "inactive" | "pending"  # New value added
```

### 2. Safe Modifications ✅

#### Improving Error Messages
```json
// v1 - Basic error
{
  "error": "Invalid input"
}

// v1 (later) - More detailed error (NON-BREAKING)
{
  "error": "Invalid input: email format is incorrect"
}
```

#### Adding Documentation
```python
# v1 - No description
GET /api/v1/users

# v1 (later) - Added description (NON-BREAKING)
GET /api/v1/users  # Returns list of all users
```

#### Performance Optimizations
```python
# v1 - Slower query
SELECT * FROM users

# v1 (later) - Optimized query (NON-BREAKING)
SELECT id, name, email FROM users WHERE active = true
# Same response format, just faster
```

### 3. Backward-Compatible Changes ✅

#### Making Required Field Optional
```python
# v1 - email required
POST /api/v1/users
{"name": "John", "email": "john@example.com"}

# v1 (later) - email now optional (NON-BREAKING)
POST /api/v1/users
{"name": "John"}  # email no longer required
```

#### Relaxing Validation
```python
# v1 - Strict validation (min 8 chars)
password: min_length=8

# v1 (later) - Relaxed validation (min 6 chars) (NON-BREAKING)
password: min_length=6
```

**For detailed list:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#examples-of-non-breaking-changes)

---

## Deprecation Notice Requirements

When deprecating a version due to breaking changes:

1. **Add deprecation headers** to API responses
2. **Provide migration timeline** (30-90 days standard)
3. **Link to migration guide**

**For deprecation workflow:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#deprecation-notice-requirements)

**For deprecation policy:** See [SPEC-088: Deprecation Policy](./deprecation-policy.md)

---

## Migration Guide Requirements

When introducing breaking changes:

1. **Document all breaking changes**
2. **Provide step-by-step migration instructions**
3. **Include code examples** (before/after)
4. **Define timeline** (release → deprecation → sunset)

**For migration guide template:** See [SPEC-089: Migration Guide Template](../../089-breaking-change-management/migration-guide-template.md)

**For full migration requirements:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#migration-guide-requirements)

---

## Detection and Enforcement

### Automated Detection

Breaking changes are automatically detected in CI/CD:
- **Script:** `ci/check-breaking-changes.py`
- **Workflow:** `.github/workflows/contract-validation.yml`
- **Policy:** Fails build on breaking changes without version increment

**For detection details:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md#breaking-change-detection)

---

## Coordination with SPEC-089

| Responsibility | SPEC-088 (This SPEC) | SPEC-089 |
|----------------|---------------------|----------|
| **Versioning Scheme** | ✅ Defines v1, v2, v3 scheme | References |
| **Version Infrastructure** | ✅ Routing, middleware | Uses |
| **Breaking Change Detection** | References | ✅ Implements |
| **Breaking Change Process** | References | ✅ Defines 8-step process |
| **Approval Workflow** | References | ✅ Defines |

**Relationship:**
- SPEC-088 focuses on **versioning infrastructure** (HOW to version)
- SPEC-089 focuses on **breaking change management** (WHEN and HOW to manage changes)

**For complete breaking change management:** See [SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md)

---

## References

- **[SPEC-089: Breaking Change Management](../../089-breaking-change-management/README.md)** - Complete breaking change management process
- **[SPEC-088: API Versioning Strategy](./README.md)** - Versioning scheme and infrastructure
- `shared/contracts/docs/BREAKING_CHANGES.md` - Detailed breaking change policy
