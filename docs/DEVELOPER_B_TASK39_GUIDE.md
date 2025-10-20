# Developer B - Task #39: Core API Endpoint Testing Guide

**Task:** Core API - Test New Endpoints
**Issue:** Getting 404/405 errors
**Root Cause:** Testing with wrong URL paths
**Date:** October 20, 2025

---

## 🚨 The Problem

You're getting 404/405 errors because the **Core API does NOT use `/api/` prefix**.

### ❌ Wrong (Returns 404):
```bash
curl http://localhost:13390/api/health
curl http://localhost:13390/api/auth/login
curl http://localhost:13390/api/memory/create
```

### ✅ Correct (Works):
```bash
curl http://localhost:13390/health
curl http://localhost:13390/auth/login
curl http://localhost:13390/memory/create
```

---

## 📋 Core API Endpoints

### Health & Status
```bash
# Basic health check
curl http://localhost:13390/health

# OpenAPI documentation
curl http://localhost:13390/openapi.json

# Interactive API docs
open http://localhost:13390/docs
```

### Authentication Endpoints
```bash
# Login
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'  # pragma: allowlist secret

# Get current user
curl http://localhost:13390/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Logout
curl -X POST http://localhost:13390/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Memory Endpoints
```bash
# Create memory
curl -X POST http://localhost:13390/memory/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "Test memory",
    "metadata": {"key": "value"}
  }'

# Get memory
curl http://localhost:13390/memory/{memory_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# List memories
curl http://localhost:13390/memory/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Access Control (ACL) Endpoints
```bash
# Check ACL status
curl http://localhost:13390/acl/ping \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get accessible memories
curl http://localhost:13390/acl/accessible-memories \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Complete Test Suite

### Test Script
```bash
#!/bin/bash
# save as: test-core-api.sh

API_BASE="http://localhost:13390"

echo "🧪 Testing Core API Endpoints..."
echo ""

# Test 1: Health Check
echo "1. Health Check"
curl -s "$API_BASE/health" | jq '.'
echo ""

# Test 2: OpenAPI Schema
echo "2. OpenAPI Endpoints Available"
curl -s "$API_BASE/openapi.json" | jq '.paths | keys | length'
echo " endpoints found"
echo ""

# Test 3: Login (replace with actual credentials)
echo "3. Login Test"
TOKEN=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}' \  # pragma: allowlist secret
  | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✅ Login successful"

  # Test 4: Get current user
  echo "4. Get Current User"
  curl -s "$API_BASE/auth/me" \
    -H "Authorization: Bearer $TOKEN" | jq '.'
  echo ""

  # Test 5: Memory operations
  echo "5. Memory Operations"
  MEMORY_ID=$(curl -s -X POST "$API_BASE/memory/create" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"content": "Test from Developer B", "metadata": {}}' \
    | jq -r '.id')

  echo "Created memory: $MEMORY_ID"
  echo ""

  # Test 6: ACL check
  echo "6. ACL Accessible Memories"
  curl -s "$API_BASE/acl/accessible-memories" \
    -H "Authorization: Bearer $TOKEN" | jq '. | length'
  echo " memories accessible"

else
  echo "❌ Login failed - check credentials"
fi

echo ""
echo "✅ Test suite complete"
```

Make executable and run:
```bash
chmod +x test-core-api.sh
./test-core-api.sh
```

---

## 🔍 Finding All Available Endpoints

### List All Endpoints Programmatically
```bash
curl -s http://localhost:13390/openapi.json | \
  jq -r '.paths | keys[]' | \
  sort
```

### Group by Category
```bash
# Auth endpoints
curl -s http://localhost:13390/openapi.json | \
  jq -r '.paths | keys[] | select(startswith("/auth"))'

# Memory endpoints
curl -s http://localhost:13390/openapi.json | \
  jq -r '.paths | keys[] | select(startswith("/memory"))'

# ACL endpoints
curl -s http://localhost:13390/openapi.json | \
  jq -r '.paths | keys[] | select(startswith("/acl"))'
```

---

## ⚠️ Common Mistakes

### Mistake 1: Using `/api/` prefix
```bash
❌ http://localhost:13390/api/health  # 404 Not Found
✅ http://localhost:13390/health       # Works
```

### Mistake 2: Wrong port
```bash
❌ http://localhost:8080/health   # That's the gRPC Gateway
❌ http://localhost:13393/health  # That's the Memory Service
✅ http://localhost:13390/health  # Core API
```

### Mistake 3: Missing authentication
```bash
❌ curl http://localhost:13390/memory/list
   # Returns 401 Unauthorized

✅ curl http://localhost:13390/memory/list \
   -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🌐 Service Ports Reference

| Service | Port | Health Endpoint |
|---------|------|----------------|
| Core API | 13390 | `/health` |
| Memory Service (Rust) | 13393 | `/health` |
| GraphOps (Rust) | 50051 | gRPC (no HTTP) |
| gRPC Gateway (Go) | 8080 | `/health` |
| Load Tester (Go) | 13396 | N/A |

---

## 📝 Task #39 Checklist

### Authentication Tests
- [ ] POST `/auth/login` - Test valid login
- [ ] POST `/auth/login` - Test invalid credentials
- [ ] GET `/auth/me` - Test authenticated user info
- [ ] POST `/auth/logout` - Test logout
- [ ] POST `/auth/regenerate-token` - Test token regeneration

### Memory Tests
- [ ] POST `/memory/create` - Create new memory
- [ ] GET `/memory/{id}` - Retrieve memory by ID
- [ ] GET `/memory/list` - List all memories
- [ ] PUT `/memory/{id}` - Update memory
- [ ] DELETE `/memory/{id}` - Delete memory

### ACL Tests
- [ ] GET `/acl/ping` - Test ACL service availability
- [ ] GET `/acl/accessible-memories` - List accessible memories
- [ ] POST `/acl/evaluate` - Test permission evaluation
- [ ] GET `/acl/stats` - Get ACL statistics

### Error Handling Tests
- [ ] Test with missing auth token (401)
- [ ] Test with invalid auth token (401)
- [ ] Test with non-existent resource IDs (404)
- [ ] Test with malformed JSON (400)

---

## 🐛 Debugging Tips

### Enable Verbose Output
```bash
curl -v http://localhost:13390/health
```

### Check Response Headers
```bash
curl -I http://localhost:13390/health
```

### Pretty Print JSON
```bash
curl -s http://localhost:13390/health | jq '.'
```

### Save Response to File
```bash
curl -s http://localhost:13390/openapi.json > core-api-spec.json
```

---

## ✅ Next Steps

1. **Run the test script above** to verify all endpoints work
2. **Document any issues** you find in Taiga comments
3. **Report success metrics**: Number of endpoints tested, pass/fail rate
4. **Create bug tickets** for any 500 errors or unexpected behavior

---

**Questions?** Ask in the team chat or update Task #39 in Taiga.
