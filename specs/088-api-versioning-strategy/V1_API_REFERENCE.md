# V1 API Reference

**Version**: 1.0.0
**Base URL**: `/api/v1`
**Status**: Active
**Related**: SPEC-088 API Versioning Strategy

---

## Overview

The V1 API is the first versioned release of the Ninaivalaigal API. It provides a stable, well-documented interface for authentication, user management, memory operations, team collaboration, and organization management.

**Key Features**:
- RESTful design
- JWT authentication
- RBAC authorization
- Tenant isolation
- Comprehensive error handling

---

## Authentication

All endpoints (except signup/login) require authentication via JWT token.

### Headers

```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

### Response Headers

All V1 responses include:
```http
X-API-Version: v1
```

Deprecated endpoints also include:
```http
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30T00:00:00Z
X-API-Replacement: v2
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "details": {...}
}
```

### Pagination

V1 uses simple skip/limit pagination:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 100
  }
}
```

---

## Endpoints

### Authentication (`/api/v1/auth`)

#### POST `/api/v1/auth/signup/individual`

Create an individual user account.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",  // pragma: allowlist secret
  "name": "John Doe"
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Individual user account created successfully",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "account_type": "individual",
    "role": "user"
  },
  "verification_required": true,
  "next_steps": ["verify_email", "create_first_context", "install_tools"]
}
```

---

#### POST `/api/v1/auth/signup/organization`

Create an organization account.

**Request**:
```json
{
  "email": "admin@company.com",
  "password": "SecurePass123!",  // pragma: allowlist secret
  "organization_name": "Acme Corp",
  "industry": "Technology",
  "size": "51-200"
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Organization account created successfully",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@company.com",
    "account_type": "organization",
    "role": "owner"
  },
  "organization": {
    "organization_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Corp",
    "industry": "Technology",
    "size": "51-200"
  },
  "verification_required": true
}
```

---

#### POST `/api/v1/auth/login`

Authenticate and receive JWT token.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"  // pragma: allowlist secret
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Login successful",
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "account_type": "individual",
  "role": "user",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

---

#### GET `/api/v1/auth/me`

Get current authenticated user.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "account_type": "individual",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-11-02T08:00:00Z"
  }
}
```

---

#### POST `/api/v1/auth/refresh`

Refresh JWT token.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

---

### Users (`/api/v1/users`)

#### GET `/api/v1/users/me`

Get my profile.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "email": "user@example.com",
    "name": "John Doe",
    "account_type": "individual",
    "subscription_tier": "free",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-11-02T08:00:00Z"
  }
}
```

---

#### PUT `/api/v1/users/me`

Update my profile.

**Headers**: `Authorization: Bearer TOKEN`

**Request**:
```json
{
  "name": "John Smith",
  "username": "johnsmith"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johnsmith",
    "email": "user@example.com",
    "name": "John Smith"
  }
}
```

---

### Memory (`/api/v1/memory`)

#### POST `/api/v1/memory`

Store a memory.

**Headers**: `Authorization: Bearer TOKEN`

**Request**:
```json
{
  "content": "Important meeting notes from project kickoff",
  "source": "manual",
  "data": {
    "context": "work",
    "tags": ["meeting", "project"]
  }
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Memory stored successfully",
  "memory_id": "770e8400-e29b-41d4-a716-446655440002",
  "context": "work"
}
```

---

#### GET `/api/v1/memory`

Get memories with pagination.

**Headers**: `Authorization: Bearer TOKEN`

**Query Parameters**:
- `context` (optional): Filter by context
- `source` (optional): Filter by source
- `limit` (optional, default: 10, max: 100): Number of results
- `skip` (optional, default: 0): Number to skip

**Example**: `GET /api/v1/memory?context=work&limit=20&skip=0`

**Response** (200):
```json
{
  "success": true,
  "memories": [
    {
      "memory_id": "770e8400-e29b-41d4-a716-446655440002",
      "content": "Important meeting notes",
      "context": "work",
      "source": "manual",
      "created_at": "2025-11-02T08:00:00Z",
      "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 1
  }
}
```

---

#### GET `/api/v1/memory/{memory_id}`

Get a specific memory.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "memory": {
    "memory_id": "770e8400-e29b-41d4-a716-446655440002",
    "content": "Important meeting notes",
    "context": "work",
    "source": "manual",
    "created_at": "2025-11-02T08:00:00Z",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": {
      "tags": ["meeting", "project"]
    }
  }
}
```

---

#### DELETE `/api/v1/memory/{memory_id}`

Delete a memory.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "message": "Memory deleted successfully",
  "memory_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

---

#### POST `/api/v1/memory/search`

Search memories.

**Headers**: `Authorization: Bearer TOKEN`

**Query Parameters**:
- `query` (required): Search query
- `context` (optional): Filter by context
- `limit` (optional, default: 10, max: 100): Number of results

**Example**: `POST /api/v1/memory/search?query=meeting&context=work&limit=10`

**Response** (200):
```json
{
  "success": true,
  "query": "meeting",
  "results": [
    {
      "memory_id": "770e8400-e29b-41d4-a716-446655440002",
      "content": "Important meeting notes",
      "context": "work",
      "source": "manual",
      "relevance_score": 0.95
    }
  ],
  "count": 1
}
```

---

### Teams (`/api/v1/teams`)

#### POST `/api/v1/teams`

Create a team.

**Headers**: `Authorization: Bearer TOKEN`

**Request**:
```json
{
  "name": "Engineering Team",
  "organization_id": "660e8400-e29b-41d4-a716-446655440001",
  "description": "Core engineering team",
  "governance_type": "internal"
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Team created successfully",
  "team": {
    "team_id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "Engineering Team",
    "organization_id": "660e8400-e29b-41d4-a716-446655440001",
    "description": "Core engineering team",
    "governance_type": "internal",
    "status": "active",
    "created_at": "2025-11-02T08:00:00Z"
  }
}
```

---

#### GET `/api/v1/teams`

List my teams.

**Headers**: `Authorization: Bearer TOKEN`

**Query Parameters**:
- `skip` (optional, default: 0)
- `limit` (optional, default: 10, max: 100)

**Response** (200):
```json
{
  "success": true,
  "teams": [
    {
      "team_id": "880e8400-e29b-41d4-a716-446655440003",
      "name": "Engineering Team",
      "description": "Core engineering team",
      "governance_type": "internal",
      "status": "active"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 1
  }
}
```

---

#### GET `/api/v1/teams/{team_id}/members`

List team members.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "members": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "name": "John Doe",
      "role": "owner",
      "joined_at": "2025-11-02T08:00:00Z"
    }
  ],
  "count": 1
}
```

---

### Organizations (`/api/v1/organizations`)

#### POST `/api/v1/organizations`

Create an organization.

**Headers**: `Authorization: Bearer TOKEN`

**Request**:
```json
{
  "name": "Acme Corp",
  "industry": "Technology",
  "size": "51-200",
  "description": "Leading tech company"
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Organization created successfully",
  "organization": {
    "organization_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Corp",
    "industry": "Technology",
    "size": "51-200",
    "description": "Leading tech company",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-02T08:00:00Z"
  }
}
```

---

#### GET `/api/v1/organizations`

List my organizations.

**Headers**: `Authorization: Bearer TOKEN`

**Response** (200):
```json
{
  "success": true,
  "organizations": [
    {
      "organization_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Acme Corp",
      "industry": "Technology",
      "size": "51-200",
      "description": "Leading tech company"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total": 1
  }
}
```

---

## Error Codes

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `410 Gone`: Version removed
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### V1 Error Codes

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...}
  }
}
```

**Common Error Codes**:
- `VERSION_NOT_FOUND`: API version not supported
- `VERSION_REMOVED`: API version has been removed
- `INVALID_TOKEN`: JWT token invalid or expired
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Request validation failed

---

## Rate Limiting

V1 API implements rate limiting:

**Limits**:
- Authenticated: 1000 requests/hour
- Unauthenticated: 100 requests/hour

**Headers**:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699000000
```

---

## Deprecation

When V1 endpoints are deprecated, responses include:

```http
X-API-Deprecated: true
X-API-Sunset-Date: 2026-01-30T00:00:00Z
X-API-Replacement: v2
X-API-Migration-Guide: https://docs.ninaivalaigal.com/api/v1-to-v2
Deprecation: 2026-01-30T00:00:00Z
Sunset: 2026-01-30T00:00:00Z
```

---

## V2 Migration

V1 will be supported until **January 30, 2026** (90-day deprecation period).

**Key V2 Changes**:
- Field names: snake_case → camelCase
- Pagination: skip/limit → cursor-based
- UUIDs: strings → UUID objects
- Timestamps: ISO strings → datetime objects
- Delete operations: hard delete → soft delete with grace period

**Migration Guide**: [V1 to V2 Migration Guide](./migration-guide.md)

---

## Support

- **Documentation**: https://docs.ninaivalaigal.com/api/v1
- **Email**: api-support@ninaivalaigal.com
- **Emergency**: api-emergency@ninaivalaigal.com

---

**Last Updated**: November 2, 2025
**Version**: 1.0.0
**Status**: Active ✅
