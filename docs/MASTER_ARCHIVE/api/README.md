# 🚀 API Documentation

## 🎯 API Overview

ninaivalaigal provides a comprehensive REST API for memory management, user authentication, and AI-powered intelligence features.

## 🔗 Base URLs

- **Development**: `http://localhost:8000`
- **Staging**: `https://staging-api.ninaivalaigal.com`
- **Production**: `https://api.ninaivalaigal.com`

## 🔐 Authentication

### JWT Token Authentication
```bash
# Login to get JWT token
curl -X POST /auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'  # pragma: allowlist secret

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" /api/memories
```

### Session Management
- **Token Expiry**: 1 hour (configurable)
- **Refresh**: Automatic with valid session
- **Logout**: `/auth/logout` endpoint
- **Session Storage**: Redis-backed with TTL

## 📚 Core Endpoints

### 🏥 Health & Status
```bash
# Basic health check
GET /health
# Response: {"status": "healthy", "timestamp": "2024-09-21T16:55:00Z"}

# Detailed diagnostics
GET /health/detailed
# Response: Comprehensive system status

# Prometheus metrics
GET /metrics
# Response: Prometheus-formatted metrics
```

### 👤 Authentication Endpoints
```bash
# User registration
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!"  # pragma: allowlist secret,
  "account_type": "individual"
}

# User login
POST /auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"  # pragma: allowlist secret
}

# Token refresh
POST /auth/refresh
# Requires valid session

# Logout
POST /auth/logout
# Invalidates current session
```

### 🧠 Memory Management
```bash
# Create memory
POST /api/memories
{
  "content": "Important information to remember",
  "context": "project_alpha",
  "tags": ["important", "project"],
  "metadata": {"source": "meeting_notes"}
}

# Get memories
GET /api/memories?context=project_alpha&limit=50

# Get specific memory
GET /api/memories/{memory_id}

# Update memory
PUT /api/memories/{memory_id}
{
  "content": "Updated content",
  "tags": ["updated", "important"]
}

# Delete memory
DELETE /api/memories/{memory_id}
```

### 🔍 Memory Search & Intelligence
```bash
# Search memories with AI ranking
GET /api/memories/search?q=project%20status&context=work

# Get memory relevance scores
GET /api/memories/{memory_id}/relevance

# Get related memories (AI-powered)
GET /api/memories/{memory_id}/related

# Memory health check
GET /api/memories/health
```

### 👥 Team Management
```bash
# Create team
POST /api/teams
{
  "name": "Development Team",
  "description": "Core development team"
}

# Get team members
GET /api/teams/{team_id}/members

# Add team member
POST /api/teams/{team_id}/members
{
  "user_id": "user_123",
  "role": "member"
}

# Team memory context
GET /api/memories?team_id={team_id}
```

### 🏢 Organization Management
```bash
# Create organization
POST /api/organizations
{
  "name": "Acme Corp",
  "domain": "acme.com"
}

# Organization teams
GET /api/organizations/{org_id}/teams

# Organization members
GET /api/organizations/{org_id}/members
```

## ⚡ Performance Features

### Redis-Powered Caching
```bash
# Preload user memories (SPEC-038)
POST /api/memories/preload
# Warms cache with user's most relevant memories

# Cache statistics
GET /api/cache/stats
# Returns cache hit rates and performance metrics
```

### Rate Limiting
- **Default Limit**: 1000 requests/hour per user
- **Burst Limit**: 100 requests/minute
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## 🔒 Security Features

### RBAC Endpoints
```bash
# Check user permissions
GET /api/rbac/permissions?resource=memory&action=read

# User roles
GET /api/users/{user_id}/roles

# Role permissions
GET /api/roles/{role_name}/permissions
```

### Security Headers
- **CORS**: Configurable origins
- **HSTS**: Strict transport security
- **CSP**: Content security policy
- **X-Frame-Options**: Clickjacking protection

## 📊 Response Formats

### Standard Response Structure
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-09-21T16:55:00Z",
  "request_id": "req_123456789"
}
```

### Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-09-21T16:55:00Z",
  "request_id": "req_123456789"
}
```

## 🚨 Error Codes

### HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **429**: Rate Limited
- **500**: Internal Server Error

### Custom Error Codes
- **AUTH_001**: Invalid credentials
- **AUTH_002**: Token expired
- **MEM_001**: Memory not found
- **MEM_002**: Invalid memory format
- **RBAC_001**: Insufficient permissions
- **RATE_001**: Rate limit exceeded

## 🧪 Testing the API

### Using curl
```bash
# Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  | jq -r '.access_token')

# Create memory
curl -X POST http://localhost:8000/api/memories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test memory","context":"test"}'
```

### Using Python
```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', json={
    'email': 'test@example.com',
    'password': 'test123'
})
token = response.json()['access_token']

# Create memory
headers = {'Authorization': f'Bearer {token}'}
memory_data = {
    'content': 'Test memory from Python',
    'context': 'development',
    'tags': ['test', 'python']
}
response = requests.post(
    'http://localhost:8000/api/memories',
    json=memory_data,
    headers=headers
)
```

## 📈 Performance Metrics

### Response Time Targets
- **Authentication**: P95 < 100ms
- **Memory Retrieval**: P95 < 50ms (Redis-cached)
- **Memory Search**: P95 < 200ms
- **Health Checks**: P95 < 10ms

### Throughput Targets
- **Concurrent Users**: 1,000+
- **Requests/Minute**: 10,000+
- **Memory Operations**: 12,000+ ops/second

## 📚 Related Documentation

- [Authentication Guide](../security/authentication.md)
- [RBAC Configuration](../security/rbac.md)
- [Performance Benchmarks](../testing/performance.md)
- [Developer Setup](../development/setup.md)

---

**API Version**: v1.0 | **Status**: Production Ready | **Performance**: Exceptional
