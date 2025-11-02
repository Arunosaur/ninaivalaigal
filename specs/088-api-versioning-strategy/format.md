# API Versioning Format

**Last Updated**: November 2, 2025
**Related**: [SPEC-088: API Versioning Strategy](./README.md)

---

## Overview

This document defines the technical format for API versioning in the Ninaivalaigal platform. We use **URL-based versioning** as our primary approach.

**Key Decision**: `/api/v{N}/` format (e.g., `/api/v1/users`, `/api/v2/users`)

---

## URL Versioning (Primary Approach) ✅

### **Format**

```
/api/v{N}/{resource}
```

**Examples**:
```
GET /api/v1/users
GET /api/v1/memories
GET /api/v2/users
GET /api/v2/memories
```

### **Advantages**

| Benefit | Description |
|---------|-------------|
| **Visibility** | Version is immediately visible in URL |
| **Simplicity** | Easy to understand and use |
| **Cacheability** | Simple cache key structure |
| **Debugging** | Clear in logs and error messages |
| **Browser-friendly** | Works directly in browser address bar |
| **Documentation** | Self-documenting URLs |

### **Implementation**

**FastAPI Router Setup**:
```python
from fastapi import APIRouter

# Version 1
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

@v1_router.get("/users")
async def list_users_v1():
    return {"users": [...]}

# Version 2
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

@v2_router.get("/users")
async def list_users_v2():
    return {"users": [...]}

# Add to main app
app.include_router(v1_router)
app.include_router(v2_router)
```

### **URL Structure Rules**

1. **Version comes after `/api/`**: `/api/v1/`, not `/v1/api/`
2. **Lowercase `v`**: Use `v1`, not `V1` or `version1`
3. **No dots**: Use `v1`, not `v1.0`
4. **No leading zeros**: Use `v1`, not `v01`
5. **Sequential**: v1, v2, v3 (never skip)

---

## Header Versioning (Not Used) ❌

### **Format**

```http
Accept: application/vnd.ninaivalaigal.v{N}+json
```

**Example**:
```http
GET /api/users
Accept: application/vnd.ninaivalaigal.v2+json
```

### **Why We Don't Use This**

| Issue | Impact |
|-------|--------|
| **Hidden** | Version not visible in URL |
| **Complex caching** | Cache keys must include headers |
| **Harder debugging** | Must check headers in logs |
| **Browser unfriendly** | Can't test easily in browser |
| **Documentation complexity** | Requires explanation |

### **When Header Versioning Makes Sense**

- RESTful purists who want clean URLs
- APIs with many versions (10+)
- Content negotiation is already heavily used
- Advanced API consumers only

**Our Decision**: Simplicity and visibility outweigh REST purity.

---

## Hybrid Approach (Not Used) ❌

### **Format**

Support both URL and header versioning:
```http
# URL-based
GET /api/v2/users

# Header-based
GET /api/users
Accept: application/vnd.ninaivalaigal.v2+json
```

### **Why We Don't Use This**

- **Complexity**: Two ways to do the same thing
- **Confusion**: Which takes precedence?
- **Maintenance**: Must support both methods
- **Testing**: Double the test cases

**Our Decision**: Pick one approach and stick with it (URL-based).

---

## Recommendation

### **Our Choice: URL-Based Versioning** ✅

**Format**: `/api/v{N}/{resource}`

**Rationale**:
1. ✅ **Simple** - Easy for all developers to understand
2. ✅ **Visible** - Version is obvious in URL
3. ✅ **Debuggable** - Clear in logs and errors
4. ✅ **Browser-friendly** - Works without tools
5. ✅ **Industry standard** - Used by Stripe, GitHub, Twitter

**Examples from Industry**:
- **Stripe**: `https://api.stripe.com/v1/charges`
- **GitHub**: `https://api.github.com/v3/users`
- **Twitter**: `https://api.twitter.com/2/tweets`

---

## Version Header Examples

### Request Examples

**Requesting v1:**
```http
GET /api/memories
Accept: application/vnd.ninaivalaigal.v1+json
```

**Requesting v2:**
```http
GET /api/memories
Accept: application/vnd.ninaivalaigal.v2+json
```

### Response Format Differences

**v1 Response:**
```json
{
  "data": [
    {
      "id": "123",
      "text": "This is a memory."
    }
  ]
}
```

**v2 Response (with new `metadata` field):**
```json
{
  "data": [
    {
      "id": "123",
      "text": "This is a memory.",
      "metadata": {
        "source": "API"
      }
    }
  ]
}
```

### Content Negotiation

**Version Not Found**:
```http
GET /api/v99/users
HTTP/1.1 404 Not Found

{
  "error": {
    "code": "VERSION_NOT_FOUND",
    "message": "API version v99 does not exist",
    "available_versions": ["v1", "v2"],
    "latest_version": "v2"
  }
}
```

**No Version Specified** (Future Enhancement):
```http
GET /api/users
HTTP/1.1 308 Permanent Redirect
Location: /api/v2/users

{
  "message": "Please specify API version. Redirecting to latest version (v2)."
}
```

---

## Complete Request/Response Examples

### **Example 1: List Users**

**v1 Request**:
```http
GET /api/v1/users HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
Accept: application/json
```

**v1 Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: v1

{
  "data": [
    {
      "id": "123",
      "user_name": "john_doe",
      "created_date": "2025-11-02"
    }
  ]
}
```

**v2 Request**:
```http
GET /api/v2/users HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
Accept: application/json
```

**v2 Response** (Breaking changes: field names changed):
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: v2

{
  "data": [
    {
      "id": "123",
      "username": "john_doe",
      "created_at": "2025-11-02T08:00:00Z"
    }
  ]
}
```

### **Example 2: Create Memory**

**v1 Request**:
```http
POST /api/v1/memories HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "text": "This is a memory",
  "tags": ["important"]
}
```

**v1 Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json
X-API-Version: v1
Location: /api/v1/memories/456

{
  "id": "456",
  "text": "This is a memory",
  "tags": ["important"],
  "created_date": "2025-11-02"
}
```

**v2 Request** (Breaking change: `metadata` field added):
```http
POST /api/v2/memories HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "text": "This is a memory",
  "tags": ["important"],
  "metadata": {
    "source": "API",
    "importance": "high"
  }
}
```

**v2 Response**:
```http
HTTP/1.1 201 Created
Content-Type: application/json
X-API-Version: v2
Location: /api/v2/memories/456

{
  "id": "456",
  "text": "This is a memory",
  "tags": ["important"],
  "metadata": {
    "source": "API",
    "importance": "high"
  },
  "created_at": "2025-11-02T08:00:00Z"
}
```

### **Example 3: Deprecated Version**

**v1 Request** (after deprecation):
```http
GET /api/v1/users HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
```

**v1 Response** (with deprecation warnings):
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: v1
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30
X-API-Replacement: /api/v2/users
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2

{
  "data": [...],
  "warnings": [
    {
      "code": "DEPRECATED_API_VERSION",
      "message": "API v1 is deprecated and will be removed on Jan 30, 2026.",
      "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2",
      "sunset_date": "2026-01-30",
      "days_remaining": 45
    }
  ]
}
```

### **Example 4: Removed Version**

**v1 Request** (after sunset):
```http
GET /api/v1/users HTTP/1.1
Host: api.ninaivalaigal.com
Authorization: Bearer eyJhbGc...
```

**v1 Response** (410 Gone):
```http
HTTP/1.1 410 Gone
Content-Type: application/json
X-API-Version: removed

{
  "error": {
    "code": "API_VERSION_REMOVED",
    "message": "API v1 was removed on Jan 30, 2026. Please use v2.",
    "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2",
    "replacement": "/api/v2/users",
    "sunset_date": "2026-01-30"
  }
}
```

---

## Version Headers

### **Response Headers**

All API responses should include version information:

**Standard Headers**:
```http
X-API-Version: v2
```

**Deprecated Version Headers**:
```http
X-API-Version: v1
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30
X-API-Replacement: /api/v2/users
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
```

**Removed Version Headers**:
```http
X-API-Version: removed
X-API-Sunset-Date: 2026-01-30
```

### **Request Headers** (Optional)

Clients can optionally send version preference:
```http
X-API-Version-Preference: v2
```

**Note**: URL version takes precedence over header preference.

---

## Error Responses

### **Version Not Found (404)**

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "VERSION_NOT_FOUND",
    "message": "API version v99 does not exist",
    "available_versions": ["v1", "v2"],
    "latest_version": "v2",
    "documentation": "https://docs.ninaivalaigal.com/api/versions"
  }
}
```

### **Version Removed (410)**

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "API_VERSION_REMOVED",
    "message": "API v1 was removed on Jan 30, 2026",
    "sunset_date": "2026-01-30",
    "replacement": "/api/v2/users",
    "migration_guide": "https://docs.ninaivalaigal.com/api/v1-to-v2"
  }
}
```

### **Invalid Version Format (400)**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "INVALID_VERSION_FORMAT",
    "message": "Invalid version format: 'v1.5'. Use format: v1, v2, v3",
    "valid_format": "v{N} where N is a positive integer",
    "examples": ["v1", "v2", "v3"]
  }
}
```

---

## OpenAPI/Swagger Documentation

### **Separate Schemas Per Version**

Each version should have its own OpenAPI schema:

**v1 OpenAPI**:
```
GET /api/v1/openapi.json
```

**v2 OpenAPI**:
```
GET /api/v2/openapi.json
```

### **Version-Specific Documentation**

**v1 Docs**:
```
GET /api/v1/docs
```

**v2 Docs**:
```
GET /api/v2/docs
```

---

## Implementation Checklist

**For Each New Version**:
- [ ] Create version directory (`lib/api/v2/`)
- [ ] Implement version router with prefix (`/api/v2`)
- [ ] Add version tag to all endpoints
- [ ] Generate version-specific OpenAPI schema
- [ ] Add version headers to responses
- [ ] Update documentation
- [ ] Add version to monitoring/logging

**For Deprecated Versions**:
- [ ] Add deprecation headers
- [ ] Add warning to response body
- [ ] Update documentation with warnings
- [ ] Monitor usage metrics
- [ ] Send deprecation notices

**For Removed Versions**:
- [ ] Return 410 Gone
- [ ] Remove endpoints
- [ ] Archive documentation
- [ ] Update all references

---

## References

- **[SPEC-088: API Versioning Strategy](./README.md)** - Overall versioning approach
- **[breaking-changes.md](./breaking-changes.md)** - Breaking change examples
- **[deprecation-policy.md](./deprecation-policy.md)** - Deprecation policy
- **FastAPI Versioning**: https://fastapi.tiangolo.com/advanced/sub-applications/
- **REST API Versioning**: https://restfulapi.net/versioning/

---

**Last Updated**: November 2, 2025
**Status**: 📋 Planned (Documentation Phase)
**Implementation**: Phase 2 (Infrastructure)
