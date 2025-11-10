# Router Tagging Guide

**SPEC-087: API Surface Contracts**

This guide explains how to properly tag FastAPI routers to control API surface exposure and documentation visibility.

## Overview

Router tags control which endpoints appear in OpenAPI documentation for different user roles. This is a critical security feature that prevents accidental exposure of internal/admin endpoints to public documentation.

## Tag Categories

### Public Tags (Safe for External Users)

These tags are visible to unauthenticated and external users:

- **`auth`** - Authentication endpoints (signup, login, password reset)
- **`health`** - Health check and status endpoints

**Usage:**
```python
router = APIRouter(prefix="/auth", tags=["auth"])
```

### External Tags (Authenticated External Users)

Visible to authenticated users with VIEWER role:

- **`memory-public`** - Public memory operations (tokenize, recall)

**Usage:**
```python
router = APIRouter(prefix="/memory/public", tags=["memory-public"])
```

### Member Tags (Team Members)

Visible to MEMBER and MAINTAINER roles:

- **`memory`** - Full memory CRUD operations
- **`context`** - Context management
- **`teams`** - Team operations

**Usage:**
```python
router = APIRouter(prefix="/memory", tags=["memory"])
router = APIRouter(prefix="/contexts", tags=["context"])
router = APIRouter(prefix="/teams", tags=["teams"])
```

### Admin Tags (Administrators)

Visible to ADMIN role:

- **`organizations`** - Organization management
- **`users`** - User management
- **`admin`** - Admin-specific operations
- **`analytics`** - Usage analytics

**Usage:**
```python
router = APIRouter(prefix="/admin", tags=["admin"])
router = APIRouter(prefix="/organizations", tags=["organizations"])
router = APIRouter(prefix="/users", tags=["users"])
```

### Staff Tags (Internal/System)

Visible to OWNER and SYSTEM roles only:

- **`metrics`** - System metrics
- **`ops`** - Operational endpoints
- **`billing`** - Billing and subscriptions
- **`audit`** - Audit logs
- **`queue`** - Queue management
- **`preload`** - Memory preloading
- **`session`** - Session management

**Usage:**
```python
router = APIRouter(prefix="/ops", tags=["ops"])
router = APIRouter(prefix="/billing", tags=["billing"])
```

### Specialized Tags

- **`gdpr-compliance`** - GDPR compliance endpoints
- **`hipaa-compliance`** - HIPAA compliance endpoints
- **`admin-dashboard`** - Admin dashboard endpoints
- **`memory-substrate`** - Memory substrate operations
- **`polyglot-extensions`** - Polyglot extension endpoints
- **`ai-intelligence`** - AI-powered features

**Usage:**
```python
router = APIRouter(prefix="/compliance", tags=["gdpr-compliance"])
router = APIRouter(prefix="/admin", tags=["admin-dashboard"])
```

## Role Hierarchy

The role hierarchy determines which tags are visible:

```
public (unauthenticated) < external (VIEWER) < member (MEMBER/MAINTAINER) < admin (ADMIN) < staff (OWNER/SYSTEM)
```

Each role sees all tags from lower roles plus their own role-specific tags.

## Tag Allowlist Configuration

Tag allowlists are defined in `server/api_exposure.py`:

```python
DOCS_TAG_ALLOWLIST: dict[str, set[str]] = {
    "public": set(),  # No Swagger access without auth
    "external": {"auth", "health", "memory-public"},
    "member": {"auth", "health", "memory-public", "memory", "context", "teams"},
    "admin": {..., "admin", "analytics"},
    "staff": {..., "metrics", "ops", "billing", "audit"},
}
```

## Best Practices

### 1. Always Tag Your Routers

**❌ Bad:**
```python
router = APIRouter(prefix="/admin")  # No tag!
```

**✅ Good:**
```python
router = APIRouter(prefix="/admin", tags=["admin"])
```

### 2. Use Appropriate Tags

- Use `auth` for authentication endpoints
- Use `admin` for admin-only endpoints
- Use `staff` for internal/system endpoints
- Use `memory-public` for public memory operations
- Use `memory` for full memory CRUD

### 3. Never Use Public Tags for Internal Endpoints

**❌ Bad:**
```python
router = APIRouter(prefix="/admin/users", tags=["auth"])  # Wrong tag!
```

**✅ Good:**
```python
router = APIRouter(prefix="/admin/users", tags=["admin"])
```

### 4. Use Specific Tags for Compliance

**✅ Good:**
```python
router = APIRouter(prefix="/compliance/gdpr", tags=["gdpr-compliance"])
router = APIRouter(prefix="/compliance/hipaa", tags=["hipaa-compliance"])
```

### 5. Document Tag Purpose

Add comments explaining why a tag is used:

```python
# Admin-only endpoints - requires ADMIN role
router = APIRouter(prefix="/admin", tags=["admin"])
```

## Verification

### Run Policy Tests

```bash
pytest tests/test_public_api_surface.py -v
```

### Check OpenAPI Schema

```bash
# Get public schema (should be minimal)
curl http://localhost:8000/openapi.json

# Get admin schema (should include admin endpoints)
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/openapi.json
```

### CI Validation

The GitHub Actions workflow `.github/workflows/api-surface-policy.yml` automatically validates:
- No internal endpoints in public schema
- All routes have explicit tags
- Role hierarchy is enforced
- Sensitive paths are protected

## Common Mistakes

### 1. Missing Tags

**Problem:** Router without tags defaults to empty tag list, may not appear in documentation correctly.

**Solution:** Always specify explicit tags.

### 2. Wrong Tag Category

**Problem:** Using `auth` tag for admin endpoints exposes them in public docs.

**Solution:** Use appropriate tag category (`admin`, `staff`, etc.).

### 3. Inconsistent Tagging

**Problem:** Similar endpoints use different tags.

**Solution:** Follow tag categories consistently across all routers.

## Adding New Tags

If you need a new tag category:

1. **Define the tag** in your router:
   ```python
   router = APIRouter(prefix="/new-feature", tags=["new-feature"])
   ```

2. **Add to allowlist** in `server/api_exposure.py`:
   ```python
   DOCS_TAG_ALLOWLIST = {
       "member": {..., "new-feature"},  # Add to appropriate role level
   }
   ```

3. **Update this guide** with the new tag category.

4. **Run tests** to verify:
   ```bash
   pytest tests/test_public_api_surface.py -v
   ```

## Related Files

- `server/api_exposure.py` - Tag allowlist configuration
- `server/openapi_filter.py` - OpenAPI schema filtering
- `tests/test_public_api_surface.py` - Policy validation tests
- `.github/workflows/api-surface-policy.yml` - CI validation

## Questions?

If you're unsure which tag to use:
1. Check existing routers for similar endpoints
2. Review `server/api_exposure.py` for tag categories
3. Ask the team in #api-security channel

---

**Last Updated:** 2025-11-07
**Maintained By:** Developer D
**Related SPEC:** SPEC-087
