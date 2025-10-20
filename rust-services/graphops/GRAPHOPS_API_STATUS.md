# GraphOps Service - API Status

**Service Type:** Pure gRPC (not REST)
**Port:** 50051 (gRPC) / 9090 (Metrics HTTP)
**Status:** ✅ Running & Healthy

---

## Why No Swagger Documentation?

GraphOps is a **pure gRPC service** - it does not expose REST endpoints. Swagger/OpenAPI is designed for REST APIs and does not apply here.

### Architecture:

```
gRPC Protocol (Port 50051):
├── GraphOpsService (Protocol Buffers)
│   ├── ExecuteQuery
│   ├── CreateNode
│   ├── CreateEdge
│   └── ... (other gRPC methods)
│
HTTP Metrics (Port 9090):
├── /health   - Health check (JSON)
└── /metrics  - Prometheus metrics (text)
```

---

## API Documentation

### For gRPC Methods:

Use **gRPC reflection** to explore the API:

```bash
# List all gRPC services
grpcurl -plaintext localhost:50051 list

# Describe GraphOps service
grpcurl -plaintext localhost:50051 describe graphops.v1.GraphOpsService

# Describe a specific method
grpcurl -plaintext localhost:50051 describe graphops.v1.GraphOpsService.ExecuteQuery
```

**Protocol Buffer Definitions:**
- Located in: `/shared/contracts/graphops/v1/graphops.proto`
- Auto-generated stubs available for Go and Python

---

### For HTTP Endpoints:

Only 2 HTTP endpoints exist (metrics/health):

#### Health Check
```bash
GET http://localhost:9090/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "graphops"
}
```

#### Prometheus Metrics
```bash
GET http://localhost:9090/metrics
```

**Response:** Text-based Prometheus format
```
# HELP graphops_queries_total Total number of graph queries executed
# TYPE graphops_queries_total counter
graphops_queries_total 1234
...
```

---

## Usage Examples

### From Go gRPC Gateway:

The gRPC Gateway translates REST calls to gRPC:

```go
// REST endpoint internally calls GraphOps gRPC
GET /api/v1/graph/query → GraphOpsService.ExecuteQuery (gRPC)
```

### Direct gRPC Call:

```bash
grpcurl -plaintext \
  -d '{"query": "MATCH (n) RETURN n LIMIT 10"}' \
  localhost:50051 \
  graphops.v1.GraphOpsService/ExecuteQuery
```

---

## Why gRPC Instead of REST?

**Benefits:**
- **Performance:** 2-10x faster than REST (binary protocol)
- **Streaming:** Bidirectional streaming support
- **Type Safety:** Protocol Buffers enforce strict schemas
- **Code Generation:** Auto-generate clients in any language

**Trade-offs:**
- No browser access (requires gRPC-web proxy)
- No Swagger UI (use grpcurl instead)
- Steeper learning curve

---

## Adding REST Wrapper (Future Enhancement)

If REST access is needed, we can add grpc-gateway transcoding:

```proto
service GraphOpsService {
  rpc ExecuteQuery(QueryRequest) returns (QueryResponse) {
    option (google.api.http) = {
      post: "/v1/graph/query"
      body: "*"
    };
  }
}
```

This would:
- ✅ Enable REST access alongside gRPC
- ✅ Auto-generate OpenAPI/Swagger
- ✅ Maintain gRPC performance for internal calls

**Status:** Not yet implemented (low priority)

---

## Monitoring & Observability

### Metrics (Prometheus):
```bash
curl http://localhost:9090/metrics
```

**Available Metrics:**
- `graphops_queries_total` - Total queries executed
- `graphops_query_duration_seconds` - Query latency histogram
- `graphops_connections_active` - Active DB connections
- `process_*` - Process-level metrics (CPU, memory)

### Health Check:
```bash
curl http://localhost:9090/health
```

### Logs:
```bash
# View container logs
container logs ninaivalaigal-dev-graphops-service

# Follow logs
container logs -f ninaivalaigal-dev-graphops-service
```

---

## Comparison with Other Services

| Service | Protocol | Swagger UI | Docs Method |
|---------|----------|------------|-------------|
| Core API | REST | ✅ /docs | FastAPI auto-gen |
| Business | REST | ✅ /docs | FastAPI auto-gen |
| Memory (Rust) | REST | ✅ /docs | utoipa |
| Graph Service | REST | ✅ /docs | FastAPI auto-gen |
| **GraphOps** | **gRPC** | **❌ N/A** | **grpcurl + proto** |
| gRPC Gateway | gRPC | ❌ N/A | grpcurl + proto |

---

## Summary

✅ **GraphOps is correctly implemented as pure gRPC**
✅ **Swagger/OpenAPI does not apply (by design)**
✅ **Use grpcurl for API exploration**
✅ **HTTP endpoints (/health, /metrics) working**
✅ **Protocol Buffers provide type-safe schema**

**No changes needed** - service is working as designed.

For REST API access, use the Graph Service (Python FastAPI) which wraps GraphOps functionality with REST endpoints.
