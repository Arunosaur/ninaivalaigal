# Ninaivalaigal API Documentation

## 🎯 Overview

The Ninaivalaigal API is a comprehensive AI-powered memory management and context-aware API that enables intelligent storage, retrieval, and organization of memories with advanced search capabilities.

## 📚 Documentation Files

- **[openapi.yaml](./openapi.yaml)** - Complete OpenAPI 3.0 specification
- **[swagger-ui.html](./swagger-ui.html)** - Interactive Swagger UI documentation
- **[README.md](./README.md)** - This documentation overview

## 🚀 Quick Start

### 1. Access the API Documentation

**Interactive Documentation:**
- Open [swagger-ui.html](./swagger-ui.html) in your browser for interactive API exploration
- Base URL: `http://localhost:13370` (Development)

**OpenAPI Specification:**
- Use [openapi.yaml](./openapi.yaml) with any OpenAPI-compatible tool
- Import into Postman, Insomnia, or other API clients

### 2. Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:13370/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"  # pragma: allowlist secret
  }'

# 2. Login to get JWT token
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"  # pragma: allowlist secret
  }'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Basic Memory Operations

```bash
# Set your JWT token
TOKEN="your_jwt_token_here"

# Create a context
curl -X POST http://localhost:13370/contexts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "work-project",
    "description": "Work-related memories"
  }'

# Add a memory
curl -X POST http://localhost:13370/memory \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Meeting notes: Discussed API documentation improvements",
    "context": "work-project",
    "memory_type": "note"
  }'

# Search memories
curl -X POST http://localhost:13370/memory/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API documentation",
    "limit": 10
  }'
```

## 📋 API Endpoints Overview

### 🏥 Health & Observability
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with SLO monitoring
- `GET /metrics` - Prometheus metrics

### 🔐 Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `POST /auth/token/refresh` - Refresh JWT token

### 🧠 Memory Management
- `GET /memory` - List memories with filtering
- `POST /memory` - Create new memory
- `GET /memory/{id}` - Get specific memory
- `PUT /memory/{id}` - Update memory
- `DELETE /memory/{id}` - Delete memory
- `POST /memory/search` - Advanced memory search
- `GET /memory/health` - Memory system health

### 📝 Context Management
- `GET /contexts` - List user contexts
- `POST /contexts` - Create new context
- `GET /contexts/{id}` - Get context details
- `PUT /contexts/{id}` - Update context
- `DELETE /contexts/{id}` - Delete context

## 🔑 Authentication

The API uses **JWT Bearer tokens** for authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Management
- **Login**: Get initial token via `/auth/login`
- **Refresh**: Extend token lifetime via `/auth/token/refresh`
- **Expiry**: Tokens expire after 1 hour (3600 seconds)

## 📊 Data Models

### Memory Object
```json
{
  "id": 123,
  "content": "Memory content text",
  "memory_type": "note",
  "context": "work-project",
  "metadata": {
    "tags": ["important", "meeting"],
    "priority": "high"
  },
  "created_at": "2024-09-22T15:30:00Z",
  "user_id": 456,
  "relevance_score": 0.95
}
```

### Context Object
```json
{
  "id": 789,
  "name": "work-project",
  "description": "Work-related memories",
  "scope": "personal",
  "is_active": true,
  "owner_id": 456,
  "created_at": "2024-09-22T15:00:00Z",
  "memory_count": 42
}
```

### User Object
```json
{
  "id": 456,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-09-22T14:00:00Z",
  "last_login": "2024-09-22T15:30:00Z"
}
```

## 🔍 Search Capabilities

The memory search endpoint supports advanced filtering:

```json
{
  "query": "meeting notes",
  "context": "work-project",
  "memory_type": "note",
  "limit": 50
}
```

**Search Features:**
- **Full-text search** in memory content
- **Context filtering** by specific contexts
- **Type filtering** by memory type
- **Relevance scoring** with AI-powered ranking
- **Pagination** with configurable limits

## 📈 Monitoring & Observability

### Health Checks
- **Basic**: `/health` - Simple status check
- **Detailed**: `/health/detailed` - Comprehensive health with database status, uptime, and SLO metrics

### Metrics
- **Prometheus**: `/metrics` - Standard Prometheus metrics including:
  - HTTP request rates and latencies
  - Database connection pool status
  - Memory system performance
  - Authentication success/failure rates

## 🛡️ Security

### Authentication Security
- **JWT tokens** with configurable expiration
- **Password hashing** with bcrypt
- **Rate limiting** on authentication endpoints

### Data Security
- **User isolation** - Users can only access their own data
- **Context-based access control** - Memories are scoped to contexts
- **Input validation** on all endpoints
- **SQL injection protection** via SQLAlchemy ORM

## 🚨 Error Handling

Standard HTTP status codes with detailed error responses:

```json
{
  "detail": "Memory not found",
  "error_code": "MEMORY_NOT_FOUND",
  "timestamp": "2024-09-22T15:30:00Z"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation errors)
- `500` - Internal Server Error

## 🔧 Development

### Local Development
```bash
# Start the API server
make stack-up

# Check API health
curl http://localhost:13370/health

# View API documentation
open api/docs/swagger-ui.html
```

### Testing
```bash
# Run API tests
make test-api

# Test specific endpoints
curl -X GET http://localhost:13370/health
```

## 📝 Contributing

When adding new endpoints:

1. **Update OpenAPI spec** in `openapi.yaml`
2. **Add endpoint documentation** with examples
3. **Include request/response schemas**
4. **Add authentication requirements**
5. **Update this README** with new endpoint info

## 🔗 Related Documentation

- [Main Project README](../../README.md)
- [Development Setup](../../docs/development/setup.md)
- [Deployment Guide](../../docs/deployment/README.md)
- [Architecture Overview](../../docs/architecture/README.md)

---

**Last Updated:** September 22, 2024
**API Version:** 1.0.0
**OpenAPI Version:** 3.0.0
