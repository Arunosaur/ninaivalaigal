# Ninaivalaigal API Documentation

**Version**: 2.0
**Base URL**: `http://localhost:13370` (development) | `https://api.ninaivalaigal.com` (production)
**Last Updated**: September 27, 2024

## 🚀 **API Overview**

Ninaivalaigal provides a comprehensive REST API for AI memory management with enterprise-grade features including memory providers, sharing collaboration, and comprehensive security.

### **API Design Principles**
- **RESTful Architecture**: Standard HTTP methods with predictable resource URLs
- **JSON-First**: All requests and responses use JSON format
- **Authentication Required**: JWT tokens or API keys for all endpoints
- **Comprehensive Error Handling**: Detailed error responses with actionable messages
- **Rate Limiting**: Configurable rate limits with proper HTTP status codes

## 🔐 **Authentication**

### **JWT Token Authentication**
```http
Authorization: Bearer <jwt_token>
```

### **API Key Authentication**
```http
X-API-Key: <api_key>
```

### **Authentication Endpoints**

#### **POST /auth/signup**
Create a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",  // pragma: allowlist secret
  "account_type": "individual|organization"
}
```

**Response (201):**
```json
{
  "user_id": "integer",
  "username": "string",
  "email": "string",
  "jwt_token": "string",
  "expires_at": "2024-09-27T12:00:00Z"
}
```

#### **POST /auth/login**
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"  // pragma: allowlist secret
}
```

**Response (200):**
```json
{
  "user_id": "integer",
  "username": "string",
  "jwt_token": "string",
  "expires_at": "2024-09-27T12:00:00Z"
}
```

#### **POST /auth/refresh**
Refresh JWT token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "jwt_token": "string",
  "expires_at": "2024-09-27T12:00:00Z"
}
```

## 💾 **Memory Management API**

### **Core Memory Operations**

#### **POST /memory/remember**
Store a new memory.

**Request Body:**
```json
{
  "content": "string",
  "context": "string",
  "metadata": {
    "tags": ["string"],
    "importance": "high|medium|low",
    "category": "string"
  }
}
```

**Response (201):**
```json
{
  "memory_id": "uuid",
  "content": "string",
  "context": "string",
  "created_at": "2024-09-27T12:00:00Z",
  "metadata": {}
}
```

#### **POST /memory/recall**
Retrieve memories based on query.

**Request Body:**
```json
{
  "query": "string",
  "context": "string",
  "limit": 10,
  "filters": {
    "tags": ["string"],
    "importance": "high|medium|low",
    "date_range": {
      "start": "2024-09-01T00:00:00Z",
      "end": "2024-09-27T23:59:59Z"
    }
  }
}
```

**Response (200):**
```json
{
  "memories": [
    {
      "memory_id": "uuid",
      "content": "string",
      "context": "string",
      "relevance_score": 0.95,
      "created_at": "2024-09-27T12:00:00Z",
      "metadata": {}
    }
  ],
  "total_count": 42,
  "query_time_ms": 15
}
```

#### **GET /memory/memories/{memory_id}**
Retrieve a specific memory by ID.

**Response (200):**
```json
{
  "memory_id": "uuid",
  "content": "string",
  "context": "string",
  "owner_id": "integer",
  "created_at": "2024-09-27T12:00:00Z",
  "updated_at": "2024-09-27T12:00:00Z",
  "metadata": {},
  "sharing_info": {
    "is_shared": true,
    "shared_with": ["scope_info"],
    "permissions": ["view", "comment"]
  }
}
```

#### **PUT /memory/memories/{memory_id}**
Update an existing memory.

**Request Body:**
```json
{
  "content": "string",
  "context": "string",
  "metadata": {}
}
```

**Response (200):**
```json
{
  "memory_id": "uuid",
  "content": "string",
  "context": "string",
  "updated_at": "2024-09-27T12:00:00Z",
  "metadata": {}
}
```

#### **DELETE /memory/memories/{memory_id}**
Delete a memory.

**Response (204):** No content

### **Memory Search & Discovery**

#### **GET /memory/search**
Advanced memory search with filters.

**Query Parameters:**
- `q` (string): Search query
- `context` (string): Context filter
- `tags` (array): Tag filters
- `importance` (string): Importance filter
- `limit` (integer): Result limit (default: 20, max: 100)
- `offset` (integer): Pagination offset

**Response (200):**
```json
{
  "memories": [],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  },
  "facets": {
    "tags": {"work": 45, "personal": 30},
    "importance": {"high": 25, "medium": 50, "low": 75}
  }
}
```

#### **GET /memory/relevant**
Get relevant memories based on current context.

**Query Parameters:**
- `context` (string): Current context
- `limit` (integer): Number of memories to return

**Response (200):**
```json
{
  "relevant_memories": [
    {
      "memory_id": "uuid",
      "content": "string",
      "relevance_score": 0.92,
      "relevance_reason": "Context match + recent access"
    }
  ],
  "context_analysis": {
    "detected_topics": ["AI", "memory management"],
    "confidence": 0.87
  }
}
```

## 🏗️ **Memory Provider API**

### **Provider Management**

#### **GET /providers/**
List all registered memory providers.

**Response (200):**
```json
{
  "providers": [
    {
      "name": "postgres_primary",
      "type": "postgres",
      "status": "healthy",
      "priority": 10,
      "health_status": "healthy",
      "uptime_percentage": 99.9,
      "avg_response_time_ms": 45,
      "last_health_check": "2024-09-27T12:00:00Z"
    }
  ]
}
```

#### **POST /providers/register**
Register a new memory provider.

**Request Body:**
```json
{
  "name": "string",
  "provider_type": "postgres|mem0_http|redis",
  "connection_string": "string",
  "priority": 100,
  "security_level": "public|api_key|rbac|hybrid"
}
```

**Response (201):**
```json
{
  "provider_name": "string",
  "security_level": "rbac",
  "registration_successful": true,
  "created_at": "2024-09-27T12:00:00Z",
  "api_key": {
    "key_id": "string",
    "api_key": "string",
    "permissions": ["provider:configure"],
    "expires_at": "2025-09-27T12:00:00Z"
  }
}
```

#### **GET /providers/{provider_name}/health**
Get detailed health information for a provider.

**Response (200):**
```json
{
  "provider_name": "string",
  "status": "healthy|degraded|unhealthy",
  "uptime_percentage": 99.5,
  "avg_response_time_ms": 42,
  "error_rate": 0.1,
  "last_check": "2024-09-27T12:00:00Z",
  "consecutive_failures": 0,
  "health_history": [
    {
      "timestamp": "2024-09-27T11:00:00Z",
      "status": "healthy",
      "response_time_ms": 38
    }
  ]
}
```

#### **GET /providers/failover/statistics**
Get failover and routing statistics.

**Response (200):**
```json
{
  "total_operations": 10000,
  "successful_operations": 9950,
  "failed_operations": 50,
  "failover_events": 5,
  "provider_usage": {
    "postgres_primary": 8500,
    "postgres_backup": 1500
  },
  "average_response_time_ms": 45,
  "uptime_percentage": 99.5
}
```

#### **POST /providers/{provider_name}/failover**
Manually trigger failover from a provider.

**Response (200):**
```json
{
  "message": "Failover successful",
  "failed_provider": "postgres_primary",
  "backup_provider": "postgres_backup",
  "failover_time_ms": 150
}
```

### **Provider Security**

#### **POST /providers/{provider_name}/api-keys**
Generate API key for provider access.

**Request Body:**
```json
{
  "permissions": ["provider:configure", "provider:view_metrics"],
  "expires_days": 365,
  "description": "string"
}
```

**Response (201):**
```json
{
  "key_id": "string",
  "api_key": "string",
  "permissions": ["provider:configure"],
  "created_at": "2024-09-27T12:00:00Z",
  "expires_at": "2025-09-27T12:00:00Z"
}
```

#### **GET /providers/{provider_name}/api-keys**
List API keys for a provider.

**Response (200):**
```json
{
  "api_keys": [
    {
      "key_id": "string",
      "permissions": ["provider:configure"],
      "created_at": "2024-09-27T12:00:00Z",
      "expires_at": "2025-09-27T12:00:00Z",
      "last_used": "2024-09-27T11:30:00Z",
      "usage_count": 150,
      "is_active": true
    }
  ]
}
```

#### **DELETE /providers/api-keys/{key_id}**
Revoke an API key.

**Response (204):** No content

## 🤝 **Memory Sharing API**

### **Sharing Contracts**

#### **POST /sharing/contracts**
Create a memory sharing contract.

**Request Body:**
```json
{
  "memory_id": "uuid",
  "target_scope": {
    "scope_type": "user|team|organization|agent",
    "scope_id": "string",
    "display_name": "string"
  },
  "permissions": ["view", "comment", "edit"],
  "visibility_level": "private|shared|team|org|public",
  "expires_at": "2024-12-31T23:59:59Z",
  "require_consent": true,
  "title": "string",
  "description": "string"
}
```

**Response (201):**
```json
{
  "contract_id": "string",
  "status": "pending|active",
  "created_at": "2024-09-27T12:00:00Z",
  "consent_required": true,
  "permissions": ["view", "comment"],
  "visibility_level": "shared"
}
```

#### **GET /sharing/contracts/{contract_id}**
Get sharing contract details.

**Response (200):**
```json
{
  "contract_id": "string",
  "memory_id": "uuid",
  "owner_scope": {},
  "target_scope": {},
  "permissions": ["view", "comment"],
  "status": "active",
  "created_at": "2024-09-27T12:00:00Z",
  "expires_at": "2024-12-31T23:59:59Z",
  "usage_count": 25,
  "last_accessed_at": "2024-09-27T11:30:00Z"
}
```

#### **POST /sharing/contracts/{contract_id}/consent**
Grant or deny consent for a sharing contract.

**Request Body:**
```json
{
  "consent_granted": true,
  "reason": "string"
}
```

**Response (200):**
```json
{
  "contract_id": "string",
  "consent_granted": true,
  "consent_timestamp": "2024-09-27T12:00:00Z",
  "contract_status": "active"
}
```

#### **DELETE /sharing/contracts/{contract_id}**
Revoke a sharing contract.

**Request Body:**
```json
{
  "reason": "string"
}
```

**Response (204):** No content

### **Temporal Access**

#### **POST /sharing/temporal-access**
Create time-limited access to memory.

**Request Body:**
```json
{
  "memory_id": "uuid",
  "contract_id": "string",
  "grantee_scope": {},
  "access_type": "time_limited|session_based|usage_limited",
  "duration_minutes": 60,
  "usage_limit": 10,
  "conditions": {}
}
```

**Response (201):**
```json
{
  "grant_id": "string",
  "access_type": "time_limited",
  "status": "active",
  "expires_at": "2024-09-27T13:00:00Z",
  "usage_count": 0,
  "usage_limit": 10
}
```

#### **GET /sharing/temporal-access/{grant_id}**
Get temporal access details.

**Response (200):**
```json
{
  "grant_id": "string",
  "memory_id": "uuid",
  "access_type": "time_limited",
  "status": "active|expired|revoked",
  "created_at": "2024-09-27T12:00:00Z",
  "expires_at": "2024-09-27T13:00:00Z",
  "usage_count": 5,
  "usage_limit": 10,
  "last_accessed_at": "2024-09-27T12:30:00Z"
}
```

#### **POST /sharing/temporal-access/{grant_id}/extend**
Extend temporal access duration.

**Request Body:**
```json
{
  "additional_minutes": 30,
  "additional_usage": 5
}
```

**Response (200):**
```json
{
  "grant_id": "string",
  "extended": true,
  "new_expires_at": "2024-09-27T13:30:00Z",
  "new_usage_limit": 15
}
```

### **Consent Management**

#### **GET /sharing/consent/requests**
Get pending consent requests for user/scope.

**Response (200):**
```json
{
  "pending_requests": [
    {
      "request_id": "string",
      "memory_id": "uuid",
      "requesting_scope": {},
      "requested_permissions": ["view", "comment"],
      "justification": "string",
      "urgency_level": "normal",
      "created_at": "2024-09-27T12:00:00Z",
      "expires_at": "2024-10-04T12:00:00Z"
    }
  ]
}
```

#### **POST /sharing/consent/preferences**
Set consent preferences for a scope.

**Request Body:**
```json
{
  "scope": {},
  "consent_scope": "memory_specific|category_wide|scope_wide",
  "consent_type": "explicit|implicit|automatic",
  "auto_grant": false,
  "conditions": {}
}
```

**Response (201):**
```json
{
  "preference_id": "string",
  "scope": {},
  "consent_type": "explicit",
  "auto_grant": false,
  "created_at": "2024-09-27T12:00:00Z"
}
```

## 📊 **Analytics & Audit API**

### **Audit Logs**

#### **GET /audit/logs**
Get audit logs with filtering.

**Query Parameters:**
- `event_types` (array): Filter by event types
- `memory_ids` (array): Filter by memory IDs
- `user_ids` (array): Filter by user IDs
- `start_time` (string): Start time filter
- `end_time` (string): End time filter
- `limit` (integer): Result limit

**Response (200):**
```json
{
  "audit_logs": [
    {
      "event_id": "string",
      "event_type": "memory_accessed",
      "timestamp": "2024-09-27T12:00:00Z",
      "user_id": 123,
      "memory_id": "uuid",
      "description": "Memory accessed via sharing contract",
      "ip_address": "192.168.1.100",
      "success": true
    }
  ],
  "pagination": {
    "total": 500,
    "limit": 50,
    "offset": 0
  }
}
```

#### **GET /audit/compliance-report**
Generate compliance report for a scope.

**Query Parameters:**
- `scope_type` (string): Scope type
- `scope_id` (string): Scope ID
- `start_date` (string): Report start date
- `end_date` (string): Report end date

**Response (200):**
```json
{
  "report_id": "string",
  "scope": {},
  "period": {
    "start": "2024-09-01T00:00:00Z",
    "end": "2024-09-27T23:59:59Z"
  },
  "summary": {
    "total_events": 1500,
    "unique_memories": 150,
    "unique_users": 25
  },
  "compliance_status": "compliant",
  "security_events": [],
  "transfer_events": []
}
```

### **Usage Analytics**

#### **GET /analytics/usage**
Get usage analytics for user/scope.

**Query Parameters:**
- `scope_type` (string): Scope type
- `scope_id` (string): Scope ID
- `period` (string): Time period (day|week|month)

**Response (200):**
```json
{
  "usage_stats": {
    "memories_created": 50,
    "memories_accessed": 200,
    "searches_performed": 75,
    "sharing_contracts_created": 10,
    "api_calls": 1000
  },
  "trends": {
    "memory_creation_trend": "+15%",
    "access_pattern": "increasing",
    "peak_usage_hours": [9, 14, 16]
  }
}
```

## 🏥 **Health & Monitoring API**

### **System Health**

#### **GET /health**
Basic health check.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-09-27T12:00:00Z",
  "version": "2.0.0"
}
```

#### **GET /health/detailed**
Detailed health information.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-09-27T12:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "connection_pool": "8/20 connections"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2,
      "memory_usage": "45MB"
    },
    "providers": {
      "postgres_primary": "healthy",
      "postgres_backup": "healthy"
    }
  },
  "metrics": {
    "uptime_seconds": 86400,
    "requests_per_minute": 150,
    "error_rate": 0.1
  }
}
```

#### **GET /memory/health**
Memory system health check.

**Response (200):**
```json
{
  "status": "healthy",
  "memory_operations": {
    "total_memories": 10000,
    "avg_response_time_ms": 45,
    "cache_hit_rate": 85.5
  },
  "provider_health": {
    "total_providers": 2,
    "healthy_providers": 2,
    "degraded_providers": 0
  }
}
```

## ❌ **Error Handling**

### **Standard Error Response**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2024-09-27T12:00:00Z",
    "request_id": "req_123456789"
  }
}
```

### **Common Error Codes**
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource not found)
- `409` - Conflict (resource already exists)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (server error)
- `503` - Service Unavailable (maintenance mode)

## 📝 **Rate Limiting**

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### **Default Limits**
- **Authentication**: 10 requests/minute
- **Memory Operations**: 100 requests/minute
- **Provider Management**: 50 requests/minute
- **Sharing Operations**: 200 requests/minute
- **Analytics**: 20 requests/minute

## 🔧 **SDK & Integration**

### **Python SDK Example**
```python
from ninaivalaigal import NinaivalaigalClient

client = NinaivalaigalClient(
    base_url="https://api.ninaivalaigal.com",
    api_key="your_api_key"  # pragma: allowlist secret
)

# Store a memory
memory = client.remember(
    content="Important meeting notes",
    context="work/meetings",
    metadata={"importance": "high"}
)

# Recall memories
memories = client.recall(
    query="meeting notes",
    limit=10
)

# Share memory
contract = client.share_memory(
    memory_id=memory.id,
    target_scope={"scope_type": "team", "scope_id": "team_123"},
    permissions=["view", "comment"]
)
```

### **JavaScript SDK Example**
```javascript
import { NinaivalaigalClient } from '@ninaivalaigal/sdk';

const client = new NinaivalaigalClient({
  baseUrl: 'https://api.ninaivalaigal.com',
  apiKey: 'your_api_key'
});

// Store a memory
const memory = await client.remember({
  content: 'Important meeting notes',
  context: 'work/meetings',
  metadata: { importance: 'high' }
});

// Recall memories
const memories = await client.recall({
  query: 'meeting notes',
  limit: 10
});
```

---

**For interactive API exploration, visit our Swagger UI at `/docs` when running the development server.**
