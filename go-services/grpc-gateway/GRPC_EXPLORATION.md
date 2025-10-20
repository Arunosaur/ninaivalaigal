# gRPC Gateway - API Exploration Guide

The gRPC Gateway uses gRPC protocol (not REST), so it doesn't have traditional Swagger documentation. Instead, use **gRPC reflection** to explore and interact with the API.

---

## 📦 Prerequisites

Install `grpcurl` for gRPC API exploration:

```bash
# macOS
brew install grpcurl

# Linux
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest

# Or download from: https://github.com/fullstorydev/grpcurl/releases
```

---

## 🔍 Exploring the API

### List All Available Services

```bash
grpcurl -plaintext localhost:13395 list
```

**Expected Output:**
```
grpc.health.v1.Health
grpc.reflection.v1alpha.ServerReflection
memory.v1.MemoryService
graphops.v1.GraphOpsService
```

---

### Describe a Specific Service

```bash
# Describe Memory Service
grpcurl -plaintext localhost:13395 describe memory.v1.MemoryService

# Describe GraphOps Service
grpcurl -plaintext localhost:13395 describe graphops.v1.GraphOpsService
```

---

### Describe a Specific Method

```bash
# Describe the Remember method
grpcurl -plaintext localhost:13395 describe memory.v1.MemoryService.Remember

# Describe the Recall method
grpcurl -plaintext localhost:13395 describe memory.v1.MemoryService.Recall
```

---

### View Message Schemas

```bash
# View CreateMemoryRequest schema
grpcurl -plaintext localhost:13395 describe memory.v1.CreateMemoryRequest

# View Memory schema
grpcurl -plaintext localhost:13395 describe memory.v1.Memory
```

---

## 🚀 Calling gRPC Methods

### Health Check

```bash
grpcurl -plaintext localhost:13395 grpc.health.v1.Health/Check
```

---

### Create a Memory (Remember)

```bash
grpcurl -plaintext \
  -d '{
    "content": "Test memory from grpcurl",
    "metadata": {"source": "cli"}
  }' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  localhost:13395 \
  memory.v1.MemoryService/Remember
```

---

### Recall Memories (Search)

```bash
grpcurl -plaintext \
  -d '{
    "query": "test",
    "limit": 10
  }' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  localhost:13395 \
  memory.v1.MemoryService/Recall
```

---

### List All Memories

```bash
grpcurl -plaintext \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  localhost:13395 \
  memory.v1.MemoryService/ListMemories
```

---

### Delete a Memory

```bash
grpcurl -plaintext \
  -d '{"id": "550e8400-e29b-41d4-a716-446655440000"}' \
  -H 'authorization: Bearer YOUR_JWT_TOKEN' \
  localhost:13395 \
  memory.v1.MemoryService/DeleteMemory
```

---

## 🔐 Authentication

All memory operations require JWT authentication. Add your token to requests:

```bash
-H 'authorization: Bearer eyJhbGciOiJIUzI1NiIs...'
```

**Get a JWT token:**
1. Login via Core API: `POST http://localhost:13390/api/v1/auth/login`
2. Use the returned `access_token`

---

## 📝 Protocol Buffer Definitions

Proto files are located in: `/shared/contracts/`

- `memory/v1/memory.proto` - Memory service definitions
- `graphops/v1/graphops.proto` - GraphOps service definitions
- `common/v1/*.proto` - Common message types

---

## 🆚 gRPC vs REST

| Feature | gRPC Gateway | REST APIs |
|---------|--------------|-----------|
| **Protocol** | gRPC (HTTP/2) | HTTP/1.1 |
| **Format** | Protocol Buffers | JSON |
| **Docs** | grpcurl + reflection | Swagger UI |
| **Performance** | ~2-10x faster | Standard |
| **Browser** | Requires proxy | Native |

---

## 🔧 Advanced Usage

### Save Service Definition to File

```bash
grpcurl -plaintext localhost:13395 describe memory.v1.MemoryService > memory-service-api.txt
```

### Format JSON Response

```bash
grpcurl -plaintext localhost:13395 list | jq .
```

### Debug Mode (Verbose)

```bash
grpcurl -v -plaintext localhost:13395 grpc.health.v1.Health/Check
```

---

## 🌐 Alternative: REST Gateway (Future)

To enable REST access to gRPC services, we can add `grpc-gateway`:

```go
// This would allow REST → gRPC translation
// GET  /api/v1/memories -> memory.v1.MemoryService/ListMemories
// POST /api/v1/memories/recall -> memory.v1.MemoryService/Recall
```

This is a future enhancement (not yet implemented).

---

## 📚 Resources

- **grpcurl GitHub:** https://github.com/fullstorydev/grpcurl
- **gRPC Reflection:** https://github.com/grpc/grpc/blob/master/doc/server-reflection.md
- **Protocol Buffers:** https://protobuf.dev/

---

## ✅ Quick Test

Verify the gateway is working:

```bash
# Test health check (no auth required)
grpcurl -plaintext localhost:13395 grpc.health.v1.Health/Check

# List available services
grpcurl -plaintext localhost:13395 list

# Expected: Should see memory and graphops services
```

If you see services listed, the gRPC Gateway is working correctly! 🎉
