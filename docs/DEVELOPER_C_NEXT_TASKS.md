# Developer C - Next Tasks (SPEC-099/100 GAP)

**Date:** October 19, 2025
**Status:** Ready to start
**Taiga Board:** http://localhost:9000/project/ninaivalaigal/backlog

---

## 🎯 Your Mission

Close the remaining **35% gap** in SPEC-100 (API Modularization & Federation) by implementing the contracts layer, event bus, and observability infrastructure.

**Current Status:** Service decomposition 100% complete (286 endpoints across 6 services)
**Your Focus:** Build the connective tissue between services

---

## 📋 Your Tasks (5 assigned)

You have **5 critical tasks** that build the foundation for production-ready microservices:

### **Task #79: Implement Shared Contracts Layer** ⚠️ PRIORITY 1 - FOUNDATIONAL
**Status:** New
**Epic:** SPEC-100: API Modularization & Federation
**Location:** Create `shared/contracts/`

**Current Status:** ❌ NOT STARTED (CRITICAL BLOCKER)

**Objective:** Create centralized contract repository for all services to prevent drift and enable automated validation.

**Directory Structure to Create:**
```
shared/contracts/
├── auth/v1/
│   ├── auth.proto           # gRPC definitions
│   ├── models.py            # Pydantic models
│   └── openapi.yaml         # REST API spec
├── memory/v1/
│   ├── memory.proto
│   ├── models.py
│   └── openapi.yaml
├── graph/v1/
│   ├── graph.proto
│   ├── models.py
│   └── openapi.yaml
├── business/v1/
│   ├── billing.proto
│   ├── analytics.proto
│   ├── models.py
│   └── openapi.yaml
├── admin/v1/
│   ├── admin.proto
│   ├── models.py
│   └── openapi.yaml
└── common/
    ├── errors.proto         # Standard error types
    ├── pagination.proto     # Pagination patterns
    └── types.py             # Shared types
```

**Tasks:**
1. Create directory structure
2. Move existing .proto files from `go-services/grpc-gateway/proto/` to contracts
3. Extract Pydantic models from each service into contracts
4. Generate OpenAPI schemas for each service
5. Add contract validation to pre-commit hooks
6. Add CI contract validation (breaking change detection)

**Acceptance Criteria:**
- ✅ All services reference centralized contracts
- ✅ CI fails on contract breaking changes
- ✅ Documentation auto-generated from contracts
- ✅ Versioning strategy documented (v1, v2)
- ✅ Each service has comprehensive contract coverage

**Estimated Time:** 8-10 hours (Week 1 priority)

**Why This is Critical:**
Without shared contracts, services will drift apart and integration will break. This is the foundation for all other tasks.

---

### **Task #80: Generate Protocol Buffers for All Services**
**Status:** New
**Epic:** SPEC-100: API Modularization & Federation
**Location:** `shared/contracts/*/v1/*.proto`

**Current Status:** Only gRPC Gateway has .proto files

**Dependencies:** Task #79 (Shared Contracts Layer must exist first)

**Services Needing Protocol Buffers:**

1. **Memory Service (Rust):**
   ```protobuf
   service MemoryService {
     rpc CreateMemory(CreateMemoryRequest) returns (Memory);
     rpc GetMemory(GetMemoryRequest) returns (Memory);
     rpc UpdateMemory(UpdateMemoryRequest) returns (Memory);
     rpc DeleteMemory(DeleteMemoryRequest) returns (Empty);
     rpc ListMemories(ListMemoriesRequest) returns (MemoryList);
     rpc SearchMemories(SearchRequest) returns (MemoryList);
   }
   ```

2. **Graph/AI Service:**
   ```protobuf
   service GraphIntelligenceService {
     rpc AnalyzeMemory(MemoryAnalysisRequest) returns (AnalysisResult);
     rpc GetSimilarMemories(SimilarityRequest) returns (MemoryList);
     rpc GenerateInsights(InsightRequest) returns (Insight);
     rpc ProcessFeedback(FeedbackRequest) returns (FeedbackResult);
   }
   ```

3. **Core API (Auth):**
   ```protobuf
   service AuthService {
     rpc Register(RegisterRequest) returns (AuthResponse);
     rpc Login(LoginRequest) returns (AuthResponse);
     rpc RefreshToken(RefreshRequest) returns (AuthResponse);
     rpc ValidateToken(TokenRequest) returns (ValidateResponse);
   }
   ```

4. **Business Service:**
   ```protobuf
   service BillingService {
     rpc CreateSubscription(SubscriptionRequest) returns (Subscription);
     rpc UpdateSubscription(UpdateRequest) returns (Subscription);
     rpc CancelSubscription(CancelRequest) returns (Empty);
     rpc GetUsage(UsageRequest) returns (UsageReport);
   }
   ```

5. **Common Types:**
   ```protobuf
   // errors.proto
   message Error {
     string code = 1;
     string message = 2;
     map<string, string> details = 3;
   }

   // pagination.proto
   message PageRequest {
     int32 page = 1;
     int32 page_size = 2;
   }

   message PageInfo {
     int32 total = 1;
     int32 pages = 2;
     int32 current_page = 3;
   }
   ```

**Tools Needed:**
- `protoc` (Protocol Buffer Compiler)
- `protoc-gen-go` (Go plugins)
- `protoc-gen-python` (Python plugins)
- `protoc-gen-rust` (Rust plugins via tonic)

**Tasks:**
1. Design .proto files for each service
2. Generate bindings for all languages (Go, Python, Rust)
3. Update services to use generated code
4. Add proto generation to CI/CD
5. Document proto best practices

**Acceptance Criteria:**
- ✅ All services have complete .proto definitions
- ✅ Bindings generated for Python, Go, Rust
- ✅ Proto files in `shared/contracts/`
- ✅ CI auto-generates on proto changes
- ✅ Services updated to use generated code

**Estimated Time:** 10-12 hours (Week 1-2)

---

### **Task #82: Deploy Event Bus (Redis Streams or NATS)**
**Status:** New
**Epic:** SPEC-100: API Modularization & Federation

**Current Status:** Services tightly coupled via direct HTTP calls

**Objective:** Implement async messaging for loose coupling and event-driven architecture

**Implementation Options:**

**Option 1: Redis Streams (Recommended)**
- ✅ Already have Redis infrastructure
- ✅ Simple to integrate
- ✅ Consumer groups for scaling
- ✅ Event replay capability
- ⚠️ Not as feature-rich as dedicated message broker

**Option 2: NATS**
- ✅ Dedicated message broker
- ✅ Better for high-throughput
- ✅ Built-in clustering
- ⚠️ Additional infrastructure

**Recommended: Redis Streams** (leverage existing Redis)

**Architecture:**
```
Publisher (Memory Service)
    ↓ publish event
Redis Stream: "events:memory"
    ↓ consume
Consumer (Graph/AI Service)
    ↓ process
    ↓ emit new event
Redis Stream: "events:insights"
    ↓ consume
Consumer (Admin Dashboard)
```

**Events to Implement:**

| Event | Producer | Consumers | Purpose |
|-------|----------|-----------|---------|
| `user.created` | Core API | Business Service | Initialize billing |
| `memory.created` | Memory Service | Graph/AI Service | Trigger analysis |
| `insight.generated` | Graph/AI Service | Admin Dashboard | Update dashboards |
| `team.updated` | Core API | All Services | Sync state |
| `subscription.changed` | Business Service | Core API | Update access |

**Event Schema:**
```json
{
  "event_id": "uuid",
  "event_type": "memory.created",
  "timestamp": "ISO8601",
  "version": "1.0",
  "source": "memory-service",
  "data": {
    "memory_id": "uuid",
    "user_id": "uuid",
    "content": "..."
  },
  "metadata": {
    "correlation_id": "uuid",
    "causation_id": "uuid"
  }
}
```

**Tasks:**
1. Choose Redis Streams vs NATS (recommend Redis)
2. Design event schema and catalog
3. Create Python event publishing library
4. Create Python event consumer framework
5. Implement event handlers for each service
6. Add monitoring dashboard (Redis Insights or custom)
7. Document event catalog

**Acceptance Criteria:**
- ✅ All services can publish events
- ✅ Multiple consumers can subscribe
- ✅ Event replay works for debugging
- ✅ Monitoring shows event flow
- ✅ At-least-once delivery guaranteed
- ✅ Event catalog documented

**Estimated Time:** 12-15 hours (Week 2-3)

---

### **Task #83: Deploy API Gateway (Traefik or Kong)**
**Status:** New
**Epic:** SPEC-100: API Modularization & Federation

**Current Status:** Direct service access, no centralized routing

**Objective:** Single ingress point with routing, rate limiting, TLS, and observability

**Implementation Options:**

**Option 1: Traefik (Recommended)**
- ✅ Simple YAML configuration
- ✅ Auto-discovery (Docker/K8s labels)
- ✅ Let's Encrypt integration
- ✅ Good middleware ecosystem
- ✅ Prometheus metrics built-in

**Option 2: Kong**
- ✅ Powerful plugin ecosystem
- ✅ Admin UI
- ✅ More enterprise features
- ⚠️ Steeper learning curve
- ⚠️ Heavier resource usage

**Recommended: Traefik** (simpler for our needs)

**Features to Implement:**

**1. Path-Based Routing:**
```yaml
# traefik.yml
http:
  routers:
    auth:
      rule: "PathPrefix(`/auth`)"
      service: core-api
    memory:
      rule: "PathPrefix(`/memory`)"
      service: memory-service
    graph:
      rule: "PathPrefix(`/graph`)"
      service: graph-service
    billing:
      rule: "PathPrefix(`/billing`)"
      service: business-service
    admin:
      rule: "PathPrefix(`/admin`)"
      service: admin-service
    grpc:
      rule: "PathPrefix(`/grpc`)"
      service: grpc-gateway
```

**2. Rate Limiting:**
```yaml
http:
  middlewares:
    rate-limit:
      rateLimit:
        average: 100  # req/min
        burst: 50
        period: 1m

    premium-rate-limit:
      rateLimit:
        average: 1000
        burst: 200
        period: 1m
```

**3. TLS Termination:**
```yaml
entryPoints:
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt
```

**4. Authentication Middleware:**
```yaml
http:
  middlewares:
    jwt-auth:
      forwardAuth:
        address: "http://core-api:13390/auth/validate"
        authResponseHeaders:
          - "X-User-Id"
          - "X-User-Role"
```

**Deployment:**
```bash
# Apple Container CLI
container run -d --name ninaivalaigal-dev-gateway \
  -p 80:80 \
  -p 443:443 \
  -v /Users/swami/WorkSpace/ninaivalaigal/traefik:/etc/traefik \
  traefik:v2.10
```

**Tasks:**
1. Choose Traefik vs Kong
2. Create Traefik configuration files
3. Deploy gateway container
4. Configure routing rules for all services
5. Add rate limiting middleware
6. Setup TLS certificates (Let's Encrypt)
7. Add authentication middleware
8. Load testing (<10ms gateway overhead target)
9. Create monitoring dashboard

**Acceptance Criteria:**
- ✅ All services accessible via gateway
- ✅ Rate limiting enforced per user/tier
- ✅ TLS working with auto-renewal
- ✅ <10ms gateway overhead
- ✅ JWT validation at gateway
- ✅ Prometheus metrics exposed
- ✅ Access logs structured

**Estimated Time:** 10-12 hours (Week 3)

---

### **Task #84: Implement OpenTelemetry Distributed Tracing**
**Status:** New
**Epic:** SPEC-100: API Modularization & Federation

**Current Status:** Limited visibility across services

**Objective:** End-to-end request tracing across all services for debugging and performance analysis

**Architecture:**
```
Services (Python/Go/Rust)
  ↓ emit traces/spans
OTEL Collector (buffer & batch)
  ↓ export
Jaeger Backend (storage & UI)
  ↓ query
Grafana Dashboard (visualization)
```

**Components:**

**1. OpenTelemetry SDKs:**

Python (FastAPI):
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

tracer = trace.get_tracer(__name__)
FastAPIInstrumentor.instrument_app(app)
```

Rust:
```rust
use tracing::{info, instrument};
use opentelemetry::global;

#[instrument]
async fn process_memory(id: Uuid) -> Result<Memory> {
    info!("Processing memory: {}", id);
    // ...
}
```

Go:
```go
import "go.opentelemetry.io/otel"

tracer := otel.Tracer("grpc-gateway")
ctx, span := tracer.Start(ctx, "translate-request")
defer span.End()
```

**2. OTEL Collector:**
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
```

**3. Jaeger Deployment:**
```bash
container run -d --name ninaivalaigal-dev-jaeger \
  -p 16686:16686 \
  -p 14250:14250 \
  jaegertracing/all-in-one:latest
```

**4. Instrumentation Points:**
- HTTP requests (ingress/egress)
- gRPC calls
- Database queries (PostgreSQL)
- Redis operations
- Custom business logic spans

**Example Trace:**
```
GET /memory/123
  ├─ API Gateway (2ms)
  ├─ Core API: JWT Validation (5ms)
  │   ├─ Redis: Token Cache Check (0.5ms)
  │   └─ Database: User Lookup (3ms)
  ├─ Memory Service (15ms)
  │   ├─ Redis: Memory Cache Hit (0.5ms)
  │   └─ PostgreSQL: Fetch Memory (10ms)
  │   └─ Rust: Serialize (2ms)
  └─ Graph Service: Enrich Metadata (20ms)
      └─ GraphOps gRPC Call (18ms)

Total: 42ms
```

**Tasks:**
1. Deploy OTEL Collector container
2. Deploy Jaeger backend container
3. Add OpenTelemetry SDK to all Python services
4. Add tracing to Rust services
5. Add tracing to Go services
6. Instrument critical paths (auth, memory CRUD, graph queries)
7. Add custom spans for business logic
8. Create Jaeger dashboards
9. Setup Grafana integration
10. Document trace analysis workflow

**Acceptance Criteria:**
- ✅ All services emit traces
- ✅ End-to-end request visibility
- ✅ <1% performance overhead
- ✅ Trace retention 7 days
- ✅ Jaeger UI accessible
- ✅ Grafana dashboards created
- ✅ Service dependency map visible
- ✅ P50/P95/P99 latencies tracked

**Estimated Time:** 12-15 hours (Week 3-4)

---

## 🎯 Recommended Workflow

### **Week 1 (Critical Foundation):**
**Day 1-2:** Task #79 - Shared Contracts Layer
- Create directory structure
- Move existing contracts
- Add validation to CI

**Day 3-4:** Task #80 - Protocol Buffers
- Design .proto files
- Generate bindings
- Update services

### **Week 2 (Event-Driven Architecture):**
**Day 5-7:** Task #82 - Event Bus
- Deploy Redis Streams
- Implement publishing/consuming
- Add monitoring

### **Week 3-4 (Production Infrastructure):**
**Day 8-10:** Task #83 - API Gateway
- Deploy Traefik
- Configure routing
- Add rate limiting

**Day 11-13:** Task #84 - OpenTelemetry
- Deploy OTEL stack
- Instrument services
- Create dashboards

---

## 🔧 Development Environment

**All services currently running (Apple/Dev):**
```
Infrastructure:
  PostgreSQL:  port 5452 ✅
  Redis:       port 6399 ✅
  PgBouncer:   port 6452 ✅

Python Services:
  core-api:         port 13390 ✅
  business-service: port 13391 ✅
  admin-vendor:     port 13392 ✅
  graph-service:    port 13394 ✅
  em:               port 8301 ✅

Go Services:
  grpc-gateway:     port 13395 ✅

Rust Services:
  memory-service:   port 13393 ✅
```

All services healthy and ready for integration work!

---

## 📚 Reference Documents

1. **GAP Analysis:** `/docs/SPEC_099_100_GAP_ANALYSIS.md`
2. **SPEC-100 Original:** `/specs/spec-100-api-modularization.md`
3. **Port Matrix:** `/config/ports.nv.yaml`
4. **Service Architecture:** `/docs/architecture/`
5. **API Documentation:** Each service has OpenAPI docs at `/docs`

---

## 🚀 Getting Started

1. **Access Taiga:**
   ```bash
   open http://localhost:9000/project/ninaivalaigal/backlog
   ```

2. **Check your tasks:**
   - Filter by "Assigned to: Developer C"
   - You should see tasks #79, #80, #82, #83, #84

3. **Start with Task #79 (Shared Contracts):**
   ```bash
   cd /Users/swami/WorkSpace/ninaivalaigal

   # Create contracts directory
   mkdir -p shared/contracts/{auth,memory,graph,business,admin,common}/v1

   # Review existing proto files
   ls go-services/grpc-gateway/proto/

   # Plan migration
   ```

4. **Move task to "In Progress" in Taiga** when you start

---

## 💬 Communication

- **Questions?** Post in Taiga task comments
- **Blockers?** Tag @admin in task
- **Updates?** Move task status in Taiga
- **Done?** Mark complete and move to next

---

## 🎯 Success Criteria

By end of Week 4, you should have:

**Week 1:**
- ✅ Shared contracts layer operational
- ✅ Protocol buffers for all services
- ✅ CI contract validation working

**Week 2:**
- ✅ Event bus deployed and tested
- ✅ Services publishing/consuming events
- ✅ Event monitoring dashboard

**Week 3:**
- ✅ API Gateway routing all traffic
- ✅ Rate limiting enforced
- ✅ TLS configured

**Week 4:**
- ✅ OpenTelemetry tracing end-to-end
- ✅ Jaeger UI showing service maps
- ✅ Performance baselines established

**This completes SPEC-100 implementation and moves us to 95%+ completion!** 🚀

---

**Your work will establish the production-ready microservices foundation. These are critical architectural pieces that enable scale and observability.** 🎯
