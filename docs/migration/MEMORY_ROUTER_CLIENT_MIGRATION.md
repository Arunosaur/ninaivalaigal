# Memory Router Client Migration Guide

**US#93/US#95**: Memory Router Rationalization - SPEC-131
**Date**: 2025-01-31
**Status**: Migration in Progress

---

## 🎯 Overview

The Memory Injection API and Queue API have been migrated from Python Core API to Rust Memory Service. This guide helps clients migrate from Python endpoints to Rust endpoints.

---

## 📊 Migration Summary

| API | Python Endpoint | Rust Endpoint | Status |
|-----|----------------|---------------|--------|
| **Injection API** | `http://localhost:13390/memory/injection/*` | `http://localhost:13393/memory/injection/*` | ✅ Available |
| **Queue API** | `http://localhost:13390/queue/*` | `http://localhost:13393/queue/*` | ✅ Available |
| **Health API** | `http://localhost:13390/health` | `http://localhost:13393/health` | ✅ Available |

**Key Change**: Port change from `13390` (Core API) to `13393` (Memory Service)

---

## 🔄 Endpoint Mapping

### Memory Injection API

All endpoints use the same path structure, only the base URL changes:

| Endpoint | Python | Rust |
|----------|--------|------|
| Analyze Opportunities | `POST /memory/injection/analyze` | `POST /memory/injection/analyze` |
| Execute Injection | `POST /memory/injection/execute` | `POST /memory/injection/execute` |
| Bulk Injection | `POST /memory/injection/bulk` | `POST /memory/injection/bulk` |

### Queue API

All endpoints use the same path structure:

| Endpoint | Python | Rust |
|----------|--------|------|
| Enqueue Task | `POST /queue/tasks` | `POST /queue/tasks` |
| Get Job Status | `GET /queue/jobs/:job_id` | `GET /queue/jobs/:job_id` |
| Queue Stats | `GET /queue/stats` | `GET /queue/stats` |
| Process Memory | `POST /queue/memory/:memory_id/process` | `POST /queue/memory/:memory_id/process` |
| Queue Health | `GET /queue/health` | `GET /queue/health` |

### Health API

| Endpoint | Python | Rust |
|----------|--------|------|
| Health Check | `GET /health` | `GET /health` |

---

## 💻 Code Examples

### Python Client

#### Before (Python Core API)
```python
import requests

BASE_URL = "http://localhost:13390"
headers = {"Authorization": f"Bearer {token}"}

# Injection API - Analyze
response = requests.post(
    f"{BASE_URL}/memory/injection/analyze",
    json={
        "current_activity": "coding",
        "semantic_context": {"language": "rust"},
        "max_candidates": 10
    },
    headers=headers
)

# Queue API - Enqueue Task
response = requests.post(
    f"{BASE_URL}/queue/tasks",
    json={
        "task_type": "memory_processing",
        "parameters": {"memory_id": "123"}
    },
    headers=headers
)
```

#### After (Rust Memory Service)
```python
import requests

# Memory Service base URL
MEMORY_SERVICE_URL = "http://localhost:13393"
headers = {"Authorization": f"Bearer {token}"}

# Injection API - Analyze (same endpoint, different base URL)
response = requests.post(
    f"{MEMORY_SERVICE_URL}/memory/injection/analyze",
    json={
        "current_activity": "coding",
        "semantic_context": {"language": "rust"},
        "max_candidates": 10
    },
    headers=headers
)

# Queue API - Enqueue Task (same endpoint, different base URL)
response = requests.post(
    f"{MEMORY_SERVICE_URL}/queue/tasks",
    json={
        "task_type": "memory_processing",
        "parameters": {"memory_id": "123"}
    },
    headers=headers
)
```

### JavaScript/TypeScript Client

#### Before
```typescript
const BASE_URL = "http://localhost:13390";

async function analyzeInjection(token: string, context: any) {
  const response = await fetch(`${BASE_URL}/memory/injection/analyze`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(context)
  });
  return response.json();
}
```

#### After
```typescript
const MEMORY_SERVICE_URL = "http://localhost:13393";

async function analyzeInjection(token: string, context: any) {
  const response = await fetch(`${MEMORY_SERVICE_URL}/memory/injection/analyze`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(context)
  });
  return response.json();
}
```

### cURL Examples

#### Before
```bash
# Injection API
curl -X POST http://localhost:13390/memory/injection/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_activity": "coding",
    "semantic_context": {"language": "rust"},
    "max_candidates": 10
  }'

# Queue API
curl -X POST http://localhost:13390/queue/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "memory_processing",
    "parameters": {"memory_id": "123"}
  }'
```

#### After
```bash
# Injection API (port 13393)
curl -X POST http://localhost:13393/memory/injection/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_activity": "coding",
    "semantic_context": {"language": "rust"},
    "max_candidates": 10
  }'

# Queue API (port 13393)
curl -X POST http://localhost:13393/queue/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "memory_processing",
    "parameters": {"memory_id": "123"}
  }'
```

---

## 🔑 Key Changes

### 1. Base URL Change
- **Old**: `http://localhost:13390` (Core API)
- **New**: `http://localhost:13393` (Memory Service)

### 2. Service Architecture
- **Old**: Requests go through Core API (Python)
- **New**: Requests go directly to Memory Service (Rust)

### 3. What Stays the Same
- ✅ Same endpoint paths
- ✅ Same request/response formats
- ✅ Same authentication (JWT Bearer tokens)
- ✅ Same error codes
- ✅ Same HTTP methods

---

## ⚠️ Breaking Changes

### None Expected
- ✅ Request/response formats are identical
- ✅ Authentication method unchanged
- ✅ Error handling unchanged
- ✅ Only change is base URL

### Port Configuration
Make sure your environment variables and configuration point to the correct port:

```bash
# Old configuration
MEMORY_API_URL=http://localhost:13390

# New configuration
MEMORY_SERVICE_URL=http://localhost:13393
```

---

## 📋 Migration Checklist

- [ ] Update base URL from port `13390` to `13393`
- [ ] Update environment variables
- [ ] Update configuration files
- [ ] Test all endpoints
- [ ] Verify authentication works
- [ ] Check error handling
- [ ] Update documentation
- [ ] Update monitoring/alerting
- [ ] Update API client libraries

---

## 🧪 Testing

### Verify Migration
```bash
# Test health endpoint
curl http://localhost:13393/health

# Test injection API (requires auth token)
curl -X POST http://localhost:13393/memory/injection/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_activity": "test", "max_candidates": 5}'

# Test queue API (requires auth token)
curl -X POST http://localhost:13393/queue/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "test", "parameters": {}}'
```

---

## 📈 Performance Benefits

After migration, you should see:
- ✅ **Faster response times** (Rust performance)
- ✅ **Higher throughput** (>1000 memories/sec for bulk operations)
- ✅ **Lower latency** (P99 < 10ms for queue operations)
- ✅ **Better resource efficiency** (30% reduction)

---

## 🆘 Troubleshooting

### Connection Errors
- **Issue**: Cannot connect to `localhost:13393`
- **Solution**: Ensure Memory Service is running
  ```bash
  # Check service status
  curl http://localhost:13393/health
  ```

### Authentication Errors
- **Issue**: 401 Unauthorized
- **Solution**: Verify JWT token is valid and properly formatted
  ```bash
  # Token should be in format: Bearer <token>
  Authorization: Bearer <your-jwt-token>
  ```

### CORS Issues
- **Issue**: CORS errors in browser
- **Solution**: Memory Service should have CORS configured, verify with service team

---

## 📚 Additional Resources

- **Deprecation Plan**: `tasks/active/US_93_95_PYTHON_DEPRECATION_PLAN.md`
- **Production Readiness**: `tasks/active/US_93_95_PRODUCTION_READY.md`
- **SPEC-131**: `specs/131-memory-router-rationalization/SPEC-131-memory-router-rationalization.md`
- **API Reference**: `rust-services/memory-service/API_REFERENCE.md`

---

## 🗓️ Timeline

- **Migration Start**: 2025-01-31
- **Deprecation Date**: 2025-01-31
- **Removal Date**: 2025-04-30 (3 months grace period)

**Action Required**: Migrate before April 30, 2025

---

## 📞 Support

For questions or issues during migration:
1. Check this migration guide
2. Review API documentation
3. Contact the development team
4. Open an issue in the project repository

---

**Status**: Migration in progress - Python endpoints deprecated, Rust endpoints available
