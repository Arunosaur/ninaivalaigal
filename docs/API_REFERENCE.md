# ninaivalaigal API Reference

**Version:** 1.0
**Last Updated:** October 12, 2025
**Base URL:** `http://localhost:13390` (development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limits](#rate-limits)
3. [Error Handling](#error-handling)
4. [Authentication Endpoints](#authentication-endpoints)
5. [Memory Endpoints](#memory-endpoints)
6. [Context Endpoints](#context-endpoints)
7. [RBAC Endpoints](#rbac-endpoints)
8. [Webhooks](#webhooks)

---

## Authentication

All endpoints except signup and login require JWT authentication.

**Include in headers:**
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Token expires:** 24 hours
**Refresh token expires:** 30 days
**See:** [Authentication Endpoints](#authentication-endpoints)

---

## Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 100 |
| Team | 600 | 1000 |
| Enterprise | 6000 | 10000 |

**Rate limit headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697123456
```

---

## Error Handling

All errors follow this format:

```json
{
  "success": false,
  "detail": "Error message",
  "error_code": "ERROR_TYPE"
}
```

**Common error codes:**
- `VALIDATION_ERROR` - Invalid input
- `AUTH_ERROR` - Authentication failed
- `PERMISSION_ERROR` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_ERROR` - Too many requests

---

## Authentication Endpoints

### POST /auth/signup/individual

**Description:** Register a new individual user account.

**Authentication:** None

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/signup/individual HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Test User"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | User's password (min 8 characters) |
| name | string | Yes | User's full name |

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-goes-here",
    "email": "user@example.com",
    "name": "Test User",
    "jwt_token": "...",
    "refresh_token": "..."
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid email format or weak password |
| 409 | Conflict | Email address already registered |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'
```

### POST /auth/signup/team

**Description:** Register a new team account.

**Authentication:** None

**Rate Limit:** 5 requests/minute

**Request:**
```http
POST /auth/signup/team HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "email": "admin@team.com",
  "password": "SecurePass123!",
  "name": "Admin User",
  "team_name": "My Awesome Team"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Admin's email address |
| password | string | Yes | Admin's password (min 8 characters) |
| name | string | Yes | Admin's full name |
| team_name | string | Yes | Name of the new team |

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-goes-here",
    "email": "admin@team.com",
    "name": "Admin User",
    "jwt_token": "...",
    "refresh_token": "..."
  },
  "team": {
    "id": "team-uuid-goes-here",
    "name": "My Awesome Team"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid input |
| 409 | Conflict | Team name already taken |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/signup/team \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@team.com",
    "password": "SecurePass123!",
    "name": "Admin User",
    "team_name": "My Awesome Team"
  }'
```

### POST /auth/signup/team

**Description:** Register a new team account.

**Authentication:** None

**Rate Limit:** 5 requests/minute

**Request:**
```http
POST /auth/signup/team HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "email": "admin@team.com",
  "password": "SecurePass123!",
  "name": "Admin User",
  "team_name": "My Awesome Team"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Admin's email address |
| password | string | Yes | Admin's password (min 8 characters) |
| name | string | Yes | Admin's full name |
| team_name | string | Yes | Name of the new team |

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-goes-here",
    "email": "admin@team.com",
    "name": "Admin User",
    "jwt_token": "...",
    "refresh_token": "..."
  },
  "team": {
    "id": "team-uuid-goes-here",
    "name": "My Awesome Team"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid input |
| 409 | Conflict | Team name already taken |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/signup/team \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@team.com",
    "password": "SecurePass123!",
    "name": "Admin User",
    "team_name": "My Awesome Team"
  }'
```

### POST /auth/login

**Description:** Log in an existing user.

**Authentication:** None

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/login HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | User's password |

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-goes-here",
    "email": "user@example.com",
    "name": "Test User",
    "jwt_token": "...",
    "refresh_token": "..."
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Incorrect email or password |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### POST /auth/login

**Description:** Log in an existing user.

**Authentication:** None

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/login HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | User's password |

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid-goes-here",
    "email": "user@example.com",
    "name": "Test User",
    "jwt_token": "...",
    "refresh_token": "..."
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Incorrect email or password |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### POST /auth/logout

**Description:** Log out the current user by revoking the refresh token.

**Authentication:** Required

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/logout HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token to revoke. |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/logout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### POST /auth/token/refresh

**Description:** Obtain a new access token using a refresh token.

**Authentication:** None

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/token/refresh HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token. |

**Response (200 OK):**
```json
{
  "access_token": "new_jwt_token",
  "token_type": "bearer"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid or expired refresh token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### POST /auth/token/revoke

**Description:** Revoke a specific refresh token.

**Authentication:** Required

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/token/revoke HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "refresh_token": "TOKEN_TO_REVOKE"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token to revoke. |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Token revoked"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/revoke \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "TOKEN_TO_REVOKE"
  }'
```

### POST /auth/token/revoke-all

**Description:** Revoke all refresh tokens for the current user (logout from all devices).

**Authentication:** Required

**Rate Limit:** 5 requests/minute

**Request:**
```http
POST /auth/token/revoke-all HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "All tokens revoked"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/revoke-all \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### POST /auth/logout

**Description:** Log out the current user by revoking the refresh token.

**Authentication:** Required

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/logout HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token to revoke. |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/logout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### POST /auth/token/refresh

**Description:** Obtain a new access token using a refresh token.

**Authentication:** None

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/token/refresh HTTP/1.1
Host: localhost:13390
Content-Type: application/json

{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token. |

**Response (200 OK):**
```json
{
  "access_token": "new_jwt_token",
  "token_type": "bearer"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid or expired refresh token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### POST /auth/token/revoke

**Description:** Revoke a specific refresh token.

**Authentication:** Required

**Rate Limit:** 10 requests/minute

**Request:**
```http
POST /auth/token/revoke HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "refresh_token": "TOKEN_TO_REVOKE"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | The refresh token to revoke. |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Token revoked"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/revoke \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "TOKEN_TO_REVOKE"
  }'
```

### POST /auth/token/revoke-all

**Description:** Revoke all refresh tokens for the current user (logout from all devices).

**Authentication:** Required

**Rate Limit:** 5 requests/minute

**Request:**
```http
POST /auth/token/revoke-all HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "All tokens revoked"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 401 | Unauthorized | Invalid token |

**Example:**
```bash
curl -X POST http://localhost:13390/auth/token/revoke-all \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Memory Endpoints

### POST /memory/remember

**Description:** Store a new memory.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
POST /memory/remember HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "text": "This is a test memory",
  "context_id": "my-test-project",
  "meta": {
    "source": "API"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | Yes | The content of the memory. |
| context_id | string | No | The ID of the context to associate the memory with. |
| meta | object | No | A JSON object for storing arbitrary metadata. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is a test memory",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `text` field. |
| 404 | Not Found | `context_id` not found. |

**Example:**
```bash
curl -X POST http://localhost:13390/memory/remember \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test memory",
    "context_id": "my-test-project"
  }'
```

---

## Memory Endpoints

### POST /memory/remember

**Description:** Store a new memory.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
POST /memory/remember HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "text": "This is a test memory",
  "context_id": "my-test-project",
  "meta": {
    "source": "API"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | Yes | The content of the memory. |
| context_id | string | No | The ID of the context to associate the memory with. |
| meta | object | No | A JSON object for storing arbitrary metadata. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is a test memory",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `text` field. |
| 404 | Not Found | `context_id` not found. |

**Example:**
```bash
curl -X POST http://localhost:13390/memory/remember \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test memory",
    "context_id": "my-test-project"
  }'
```

### GET /memory/recall

**Description:** Search for memories using semantic similarity.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /memory/recall?query=user%20preferences&k=5 HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | The search query. |
| k | integer | No | The number of results to return (default: 10). |
| context_id | string | No | The ID of the context to search within. |

**Response (200 OK):**
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory-uuid-goes-here",
      "text": "User prefers dark mode",
      "context_id": "user-preferences",
      "relevance_score": 0.95
    }
  ]
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `query` parameter. |

**Example:**
```bash
curl -X GET "http://localhost:13390/memory/recall?query=user%20preferences&k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /memory/memories

**Description:** Retrieve a list of memories, with optional filters.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /memory/memories?context_id=my-test-project&limit=20 HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| context_id| string | No | Filter memories by a specific context ID. |
| limit | integer| No | Number of memories to return (default: 50). |
| offset | integer| No | Offset for pagination. |

**Response (200 OK):**
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory-uuid-1",
      "text": "This is the first memory.",
      "context_id": "my-test-project"
    },
    {
      "id": "memory-uuid-2",
      "text": "This is the second memory.",
      "context_id": "my-test-project"
    }
  ]
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | `context_id` does not exist. |

**Example:**
```bash
curl -X GET "http://localhost:13390/memory/memories?limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /memory/memories/{id}

**Description:** Retrieve a single memory by its ID.

**Authentication:** Required

**Rate Limit:** 120 requests/minute

**Request:**
```http
GET /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to retrieve. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is the first memory.",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X GET http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### PUT /memory/memories/{id}

**Description:** Update the content of an existing memory.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
PUT /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "text": "This is the updated memory content."
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to update. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | Yes | The new content for the memory. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is the updated memory content.",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `text` field. |
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X PUT http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is the updated memory content."
  }'
```

### DELETE /memory/memories/{id}

**Description:** Delete a memory by its ID.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
DELETE /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to delete. |

**Response (204 No Content):**

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X DELETE http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Context Endpoints

### POST /contexts

**Description:** Create a new context.

**Authentication:** Required

**Rate Limit:** 30 requests/minute

**Request:**
```http
POST /contexts HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "name": "my-new-context",
  "description": "A new context for my project",
  "scope": "personal"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | The name of the context. |
| description| string | No | A description of the context. |
| scope | string | No | The scope of the context (`personal`, `team`, `organization`). Defaults to `personal`. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-new-context",
    "description": "A new context for my project",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `name` field. |
| 409 | Conflict | A context with this name already exists. |

**Example:**
```bash
curl -X POST http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-new-context",
    "description": "A new context for my project"
  }'
```

### GET /contexts

**Description:** Retrieve a list of all contexts accessible to the user.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /contexts HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "contexts": [
    {
      "id": "context-uuid-1",
      "name": "my-new-context",
      "description": "A new context for my project",
      "scope": "personal"
    },
    {
      "id": "context-uuid-2",
      "name": "team-project",
      "description": "A shared project for the team",
      "scope": "team"
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /contexts/{id}

**Description:** Retrieve a single context by its ID.

**Authentication:** Required

**Rate Limit:** 120 requests/minute

**Request:**
```http
GET /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to retrieve. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-new-context",
    "description": "A new context for my project",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X GET http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### PUT /contexts/{id}

**Description:** Update a context's name or description.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
PUT /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "name": "my-updated-context-name",
  "description": "An updated description."
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to update. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | No | The new name for the context. |
| description | string | No | The new description for the context. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-updated-context-name",
    "description": "An updated description.",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | No fields to update provided. |
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X PUT http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-updated-context-name"
  }'
```

### DELETE /contexts/{id}

**Description:** Delete a context by its ID.

**Authentication:** Required

**Rate Limit:** 30 requests/minute

**Request:**
```http
DELETE /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to delete. |

**Response (204 No Content):**

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X DELETE http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### POST /contexts/{id}/share

**Description:** Share a context with a user or team.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
POST /contexts/context-uuid-goes-here/share HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "target_type": "user",
  "target_id": "user-uuid-to-share-with",
  "permission_level": "read"
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to share. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target_type | string | Yes | The type of entity to share with (`user` or `team`). |
| target_id | string | Yes | The UUID of the user or team. |
| permission_level | string | Yes | The permission level (`read`, `write`, `admin`). |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Context shared successfully"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid `target_type` or `permission_level`. |
| 404 | Not Found | Context, user, or team not found. |
| 403 | Forbidden | You do not have permission to share this context. |

**Example:**
```bash
curl -X POST http://localhost:13390/contexts/context-uuid-goes-here/share \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "user",
    "target_id": "user-uuid-to-share-with",
    "permission_level": "read"
  }'
```

### GET /memory/recall

**Description:** Search for memories using semantic similarity.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /memory/recall?query=user%20preferences&k=5 HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | The search query. |
| k | integer | No | The number of results to return (default: 10). |
| context_id | string | No | The ID of the context to search within. |

**Response (200 OK):**
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory-uuid-goes-here",
      "text": "User prefers dark mode",
      "context_id": "user-preferences",
      "relevance_score": 0.95
    }
  ]
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `query` parameter. |

**Example:**
```bash
curl -X GET "http://localhost:13390/memory/recall?query=user%20preferences&k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /memory/memories

**Description:** Retrieve a list of memories, with optional filters.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /memory/memories?context_id=my-test-project&limit=20 HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| context_id| string | No | Filter memories by a specific context ID. |
| limit | integer| No | Number of memories to return (default: 50). |
| offset | integer| No | Offset for pagination. |

**Response (200 OK):**
```json
{
  "success": true,
  "memories": [
    {
      "id": "memory-uuid-1",
      "text": "This is the first memory.",
      "context_id": "my-test-project"
    },
    {
      "id": "memory-uuid-2",
      "text": "This is the second memory.",
      "context_id": "my-test-project"
    }
  ]
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | `context_id` does not exist. |

**Example:**
```bash
curl -X GET "http://localhost:13390/memory/memories?limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /memory/memories/{id}

**Description:** Retrieve a single memory by its ID.

**Authentication:** Required

**Rate Limit:** 120 requests/minute

**Request:**
```http
GET /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to retrieve. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is the first memory.",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X GET http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### PUT /memory/memories/{id}

**Description:** Update the content of an existing memory.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
PUT /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "text": "This is the updated memory content."
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to update. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | Yes | The new content for the memory. |

**Response (200 OK):**
```json
{
  "success": true,
  "memory": {
    "id": "memory-uuid-goes-here",
    "text": "This is the updated memory content.",
    "context_id": "my-test-project"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `text` field. |
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X PUT http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is the updated memory content."
  }'
```

### DELETE /memory/memories/{id}

**Description:** Delete a memory by its ID.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
DELETE /memory/memories/memory-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the memory to delete. |

**Response (204 No Content):**

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No memory found with the specified ID. |

**Example:**
```bash
curl -X DELETE http://localhost:13390/memory/memories/memory-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Context Endpoints

### POST /contexts

**Description:** Create a new context.

**Authentication:** Required

**Rate Limit:** 30 requests/minute

**Request:**
```http
POST /contexts HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "name": "my-new-context",
  "description": "A new context for my project",
  "scope": "personal"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | The name of the context. |
| description| string | No | A description of the context. |
| scope | string | No | The scope of the context (`personal`, `team`, `organization`). Defaults to `personal`. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-new-context",
    "description": "A new context for my project",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Missing `name` field. |
| 409 | Conflict | A context with this name already exists. |

**Example:**
```bash
curl -X POST http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-new-context",
    "description": "A new context for my project"
  }'
```

### GET /contexts

**Description:** Retrieve a list of all contexts accessible to the user.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
GET /contexts HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "contexts": [
    {
      "id": "context-uuid-1",
      "name": "my-new-context",
      "description": "A new context for my project",
      "scope": "personal"
    },
    {
      "id": "context-uuid-2",
      "name": "team-project",
      "description": "A shared project for the team",
      "scope": "team"
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### GET /contexts/{id}

**Description:** Retrieve a single context by its ID.

**Authentication:** Required

**Rate Limit:** 120 requests/minute

**Request:**
```http
GET /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to retrieve. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-new-context",
    "description": "A new context for my project",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X GET http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### PUT /contexts/{id}

**Description:** Update a context's name or description.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
PUT /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "name": "my-updated-context-name",
  "description": "An updated description."
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to update. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | No | The new name for the context. |
| description | string | No | The new description for the context. |

**Response (200 OK):**
```json
{
  "success": true,
  "context": {
    "id": "context-uuid-goes-here",
    "name": "my-updated-context-name",
    "description": "An updated description.",
    "scope": "personal"
  }
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | No fields to update provided. |
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X PUT http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-updated-context-name"
  }'
```

### DELETE /contexts/{id}

**Description:** Delete a context by its ID.

**Authentication:** Required

**Rate Limit:** 30 requests/minute

**Request:**
```http
DELETE /contexts/context-uuid-goes-here HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to delete. |

**Response (204 No Content):**

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 404 | Not Found | No context found with the specified ID. |

**Example:**
```bash
curl -X DELETE http://localhost:13390/contexts/context-uuid-goes-here \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### POST /contexts/{id}/share

**Description:** Share a context with a user or team.

**Authentication:** Required

**Rate Limit:** 60 requests/minute

**Request:**
```http
POST /contexts/context-uuid-goes-here/share HTTP/1.1
Host: localhost:13390
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "target_type": "user",
  "target_id": "user-uuid-to-share-with",
  "permission_level": "read"
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | The UUID of the context to share. |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target_type | string | Yes | The type of entity to share with (`user` or `team`). |
| target_id | string | Yes | The UUID of the user or team. |
| permission_level | string | Yes | The permission level (`read`, `write`, `admin`). |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Context shared successfully"
}
```

**Error Responses:**

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid `target_type` or `permission_level`. |
| 404 | Not Found | Context, user, or team not found. |
| 403 | Forbidden | You do not have permission to share this context. |

**Example:**
```bash
curl -X POST http://localhost:13390/contexts/context-uuid-goes-here/share \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "user",
    "target_id": "user-uuid-to-share-with",
    "permission_level": "read"
  }'
```
