# SPEC-100: API Container Modularization & Runtime-Agnostic Federation

**Status:** 🟢 Approved for Design & Documentation
**Priority:** CRITICAL
**Category:** Core Architecture Evolution
**Phase:** Architecture Foundation
**Author:** Architecture Team
**Date:** October 2025

**📋 Implementation Tracking:**
- **Taiga Tasks:** #79 (Contracts - Phase 0), #83 (Gateway), #87 (Schema Drift), #88 (Core API Decomp)
- **Blocks:** #85 (PgBouncer - infrastructure prerequisite)
- **3-Month Plan:** docs/3_MONTH_EXECUTION_PLAN.md
- **Gap Analysis:** docs/SPEC_099_100_GAP_ANALYSIS_OCT20.md
- **Timeline:** Oct 2025 - Jan 2026 (12 weeks)
- **Team:** Developer C (contracts, gateway), Developer A (decomposition)

---

## Purpose

Define the transition of the current monolithic API into a **modular, runtime-agnostic federation** of independently deployable service containers.

All services communicate through **shared API contracts** and an **asynchronous message bus**, enabling seamless substitution of runtimes or service implementations in the future.

---

## 1. 🎯 Objective

Transition the monolithic Ninaivalaigal API (≈ 49K lines, 54 routers) into a **runtime-agnostic microservice federation**, allowing:
- **Independent builds** - faster CI/CD pipelines
- **Faster deployments** - deploy only changed services
- **Improved fault isolation** - service failures don't cascade
- **Contract-driven evolution** - runtime changes don't break clients

---

## 2. 📊 Current Challenges

| Area | Problem |
|------|---------|
| **Build Time** | &gt; 30 min monolithic container build |
| **Coupling** | 54 routers in one image, shared dependency graph |
| **Reliability** | Single point of failure across ML + Core logic |
| **Scalability** | Can't scale individual functional domains |
| **Maintenance** | Difficult to test or redeploy partial modules |

---

## 3. 🏗️ Target Architecture

### Service Decomposition

| Service | Role | Characteristics |
|---------|------|-----------------|
| **Core API** | Authentication, Users, Teams, RBAC | Lightweight + stateless |
| **Memory Service** | Context, Recording, State persistence | Manages memory substrate |
| **Graph/AI Service** | Intelligence & feedback processing | Isolated heavy compute |
| **Business Service** | Billing, Usage, Analytics | Independently scalable |
| **Admin/Vendor Service** | Admin + Vendor portals | Restricted internal access |

Each service runs in its own container and CI/CD workflow, exposing a **contract-compliant interface** (OpenAPI + JSON Schema).

---

## 4. 🔄 Orchestration & Communication Model

### 4.1 Gateway Layer

**Purpose:** Single ingress routing by path or tag

**Implementation:** Traefik or FastAPI Gateway

```yaml
# Gateway routing configuration
http:
  routers:
    auth-router:
      rule: "PathPrefix(`/auth`, `/users`, `/teams`)"
      service: core-api
    memory-router:
      rule: "PathPrefix(`/memory`, `/context`, `/recording`)"
      service: memory-service
    graph-router:
      rule: "PathPrefix(`/graph`, `/insights`, `/ai`)"
      service: graph-ai-service
    business-router:
      rule: "PathPrefix(`/billing`, `/usage`, `/analytics`)"
      service: business-service
    admin-router:
      rule: "PathPrefix(`/admin`, `/vendor`)"
      service: admin-vendor-service
```

**Benefits:**
- Centralized routing and load balancing
- TLS termination at gateway
- Rate limiting and authentication middleware
- Unified access logs

---

### 4.2 Shared Contracts

**Purpose:** Language-neutral API definitions

**Format:** OpenAPI 3.0 + JSON Schema + Protocol Buffers

**Location:** `shared/contracts/`

```
shared/contracts/
├── auth/
│   ├── v1/
│   │   ├── auth.proto          # gRPC contracts
│   │   ├── models.py           # Pydantic models
│   │   └── openapi.yaml        # REST contracts
├── memory/
│   └── v1/
│       ├── memory.proto
│       ├── models.py
│       └── openapi.yaml
├── graph/
│   └── v1/
│       └── ...
└── common/
    ├── errors.proto
    ├── pagination.proto
    └── types.py
```

**Contract Validation:**
- Pre-commit hook validates all `.proto` and `.yaml` files
- CI fails on breaking changes (using buf or protolock)
- Versioned schemas (v1, v2) for backward compatibility

---

### 4.3 Event Bus

**Purpose:** Decoupled async messaging

**Implementation:** Redis Streams or NATS

**Use Cases:**
- `user:created` → Business Service initializes billing
- `memory:created` → Graph/AI Service triggers analysis
- `insight:generated` → Admin Service updates dashboards

```python
# Example: Publishing event
await redis.xadd(
    "memory:events",
    {
        "event_type": "memory:created",
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-10-15T00:00:00Z"
    }
)

# Example: Consuming event
async for message in redis.xread({"memory:events": "$"}):
    event = parse_event(message)
    await handle_memory_created(event)
```

**Benefits:**
- Loose coupling between services
- Async "fire-and-forget" workflows
- Event replay for debugging
- Horizontal scaling of consumers

---

### 4.4 Aggregator Layer

**Purpose:** Merges responses from multiple services

**Pattern:** Backend-for-Frontend (BFF) or API Composition

```python
# Example: Aggregated endpoint
@router.get("/context/{context_id}/analyze")
async def analyze_context(context_id: str):
    """
    Aggregates data from Memory + Graph/AI services
    Executes calls in parallel, returns unified response
    """
    # Parallel execution (contracted parallelism)
    memory_task = memory_service.get_context(context_id)
    insights_task = graph_service.analyze_context(context_id)

    memory_data, insights = await asyncio.gather(
        memory_task,
        insights_task
    )

    # Merge results
    return {
        "context": memory_data,
        "insights": insights,
        "aggregated_at": datetime.now()
    }
```

**Benefits:**
- Single API call for frontend
- Reduces client complexity
- Handles service failures gracefully
- Optimizes with parallel execution

---

### 4.5 Contracted Parallelism

**Principle:** Services execute in parallel; gateway aggregates results—no chained calls.

**Before (Sequential):**
```
Client → CoreAPI → MemoryService → GraphService → Response (slow)
```

**After (Parallel):**
```
Client → Gateway → [CoreAPI, MemoryService, GraphService] → Aggregator → Response (fast)
```

**Implementation:**
```python
# Contracted merge with timeout and fallback
async def contracted_merge(context_id: str):
    tasks = {
        "auth": core_api.validate_auth(context_id),
        "memory": memory_service.get_context(context_id),
        "insights": graph_service.compute_insights(context_id)
    }

    # Execute with timeout
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True
    )

    # Handle partial failures
    response = {}
    for key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            response[key] = {"error": str(result)}
        else:
            response[key] = result

    return response
```

---

## 5. 📦 Deployment Pattern

### 5.1 Independent CI Pipelines

Each service has its own GitHub Actions workflow:

```
.github/workflows/
├── build-core-api.yml
├── build-memory-service.yml
├── build-graph-ai-service.yml
├── build-business-service.yml
└── build-admin-vendor-service.yml
```

**Benefits:**
- Parallel builds (&lt; 10 minutes aggregate)
- Deploy only changed services
- Independent rollback per service

---

### 5.2 Parallel Container Builds

**Using docker buildx bake:**

```hcl
# docker-bake.hcl
group "all" {
  targets = [
    "core-api",
    "memory-service",
    "graph-ai-service",
    "business-service",
    "admin-vendor-service"
  ]
}

target "core-api" {
  dockerfile = "containers/core-api/Dockerfile"
  tags = ["ghcr.io/arunosaur/ninaivalaigal-core-api:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "memory-service" {
  dockerfile = "containers/memory-service/Dockerfile"
  tags = ["ghcr.io/arunosaur/ninaivalaigal-memory-service:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}

# ... etc
```

**Build command:**
```bash
docker buildx bake --push
# Builds all services in parallel (~70% time reduction)
```

---

### 5.3 Standardized Health Endpoints

All services implement standard health checks:

```
GET /health      → 200 OK (basic liveness)
GET /ready       → 200 OK (readiness with dependencies)
GET /metrics     → Prometheus metrics
```

**Example:**
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "memory-service",
        "version": "1.0.0",
        "uptime_seconds": get_uptime()
    }

@router.get("/ready")
async def readiness_check():
    """Check dependencies (DB, Redis, etc.)"""
    try:
        await db.execute("SELECT 1")
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

---

### 5.4 Unified Environment Contract

All services use consistent environment variables:

```bash
# Unified contract
SERVICE_ROLE=memory-service
PORT=8000
DB_URI=postgresql://user:pass@host:5432/db  # pragma: allowlist secret
REDIS_URI=redis://host:6379
LOG_LEVEL=info
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

**Benefits:**
- Drop-in container replacement
- Consistent configuration across services
- Easy local development (docker-compose)

---

### 5.5 Drop-in Container Replacement

**Goal:** Replace service runtime without downstream changes

**Example:** Replace Python GraphOps with Rust GraphOps
```bash
# Before (Python)
container stop ninaivalaigal-dev-graph-ai-service
container rm ninaivalaigal-dev-graph-ai-service

# After (Rust - same contract)
container run -d \
  --name ninaivalaigal-dev-graph-ai-service \
  -p 8002:8000 \
  -e SERVICE_ROLE=graph-ai-service \
  -e DB_URI=$DB_URI \
  graphops-rust:arm64

# Gateway routing unchanged
# Clients experience zero downtime
```

---

## 6. 🧩 Additional Enhancements

### 6.1 Shared Contracts Layer

**Implementation:**
```bash
shared/contracts/
├── setup.py              # Python package
├── Cargo.toml            # Rust crate
├── scripts/
│   ├── generate-proto.sh
│   └── validate-contracts.py
└── [service contracts...]
```

**Usage:**
```bash
# Publish as private PyPI package
cd shared/contracts
python setup.py sdist bdist_wheel
twine upload --repository-url <private-pypi> dist/*

# Install in services
pip install ninaivalaigal-contracts==1.0.0
```

**Benefits:**
- Centralized schema definitions
- Automated contract validation in CI
- Version-controlled schema evolution

---

### 6.2 Internal Service Mesh (Optional)

**Purpose:** Lightweight mesh for mTLS, retry logic, and distributed tracing

**Implementation:** Linkerd or Istio-minimal

**Configuration:**
```yaml
# linkerd-values.yaml
proxy:
  resources:
    cpu:
      request: 10m
    memory:
      request: 20Mi

controlPlane:
  resources:
    cpu:
      request: 100m
    memory:
      request: 50Mi

enablePodSecurityPolicy: true
```

**Benefits:**
- Zero-trust mTLS between services
- Automatic retries and circuit breakers
- Service-to-service tracing
- Policy-based traffic management

---

### 6.3 Event Bus or Async Broker

**Purpose:** Decouple Core ↔ Graph ↔ Memory interactions

**Implementation Options:**
1. **Redis Streams** (lightweight, already deployed)
2. **NATS** (scalable pub/sub)
3. **RabbitMQ** (complex workflows)

**Redis Streams Topology:**
```yaml
# redis-streams-topology.md
streams:
  - name: user:events
    consumers:
      - business-service  # Initialize billing
      - admin-service     # Update dashboards

  - name: memory:events
    consumers:
      - graph-ai-service  # Trigger analysis
      - telemetry-service # Log metrics

  - name: insight:events
    consumers:
      - memory-service    # Store insights
      - notification-service # Alert users
```

**Benefits:**
- Async "fire-and-forget" workflows
- Event replay for debugging
- Horizontal scaling of consumers
- Decoupled service evolution

---

### 6.4 Deployment Optimization

**Parallel Docker Builds:**
```bash
# Build all services in parallel
docker buildx bake --no-cache

# Push with provenance for supply chain security
docker buildx bake --push --provenance=true --sbom=true
```

**Independent CI Workflows:**
- Each service triggers only on relevant file changes
- Avoids cross-service rebuild cascades
- Reduces CI time from 30+ min to &lt; 10 min aggregate

---

### 6.5 Database Strategy (Phased)

| Phase | Approach | Purpose |
|-------|----------|---------|
| **Phase 1** | Shared DB Schema | Fast migration, minimal changes |
| **Phase 2** | Separate Schemas | Isolation + resilience |
| **Phase 3** | Federated DB/API Composition | Cross-service analytics |

### Phase 1: Shared Database Schema
```
PostgreSQL (ninaivalaigal-graph-db)
├── public.users
├── public.teams
├── public.memories
├── public.contexts
├── public.graph_nodes
└── public.graph_edges
```

**Implementation:**
- All services connect to same PostgreSQL instance
- Namespace isolation via schema permissions
- Fast migration path (no data movement)

---

### Phase 2: Service-Specific Schemas
```
PostgreSQL (ninaivalaigal-graph-db)
├── core_api.users
├── core_api.teams
├── memory_service.memories
├── memory_service.contexts
├── graph_ai.nodes
└── graph_ai.edges
```

**Implementation:**
- Each service owns its schema
- Cross-service queries via API calls
- Better fault isolation

---

### Phase 3: Federated API/DB Composition
```
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
   ┌───┴────┬────────┬────────┐
   │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌───▼───┐ ┌──▼──┐
│ Core│ │ Mem │ │ Graph │ │ Biz │
│ API │ │ Svc │ │  AI   │ │ Svc │
└──┬──┘ └──┬──┘ └───┬───┘ └──┬──┘
   │       │        │        │
┌──▼───────▼────────▼────────▼──┐
│  Federated Query Aggregator   │
└───────────────────────────────┘
```

**Implementation:**
- Optional: Separate databases per service
- Cross-service analytics via federated queries
- GraphQL composition layer (Hasura or Apollo Federation)

---

## 7. 🔮 Optional Enhancements & Future Layer

These capabilities can be added **after** core federation is stable:

### 7.1 API Gateway (Kong/Traefik/FastAPI)

**Purpose:** Unified routing + caching + rate limiting

**When to add:** If we have 5+ microservices or need advanced traffic management

**Future SPEC:** Reserve as SPEC-102 (API Gateway Layer)

---

### 7.2 OpenTelemetry Tracing

**Purpose:** Distributed tracing across Python and Rust services

**Implementation:** OTEL SDKs + Jaeger collector

**When to add:** Once federation is implemented (SPEC-101)

**Future SPEC:** Part of SPEC-101 (Unified Observability)

---

### 7.3 Polyglot Extension Readiness

**Purpose:** Plug-in micro-executors via shared contracts (no code change)

**Example:** Run Rust GraphOps inside Python process via PyO3/FFI

**When to add:** Phase 4 (if microservice overhead too high)

**Future SPEC:** Reserve as SPEC-103 (Polyglot Executors)

---

### 7.4 GraphOps Federation

**Purpose:** Optional future layer combining cross-service graph queries

**When to add:** If graph queries span multiple services

**Future SPEC:** Reserve as SPEC-104 (GraphOps Federation)

---

### 7.5 Unified Observability

**Purpose:** Centralized metrics + logs with service tags

**Implementation:** Prometheus + Loki + Grafana

**When to add:** Part of SPEC-101 (after federation implemented)

---

## 8. 📁 Proposed Directory Structure

```
ninaivalaigal/
├── services/
│   ├── core-api/
│   ├── memory-service/
│   ├── graph-ai-service/
│   ├── business-service/
│   └── admin-vendor-service/
├── shared/
│   ├── contracts/
│   ├── utils/
│   └── telemetry/
├── docker/
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
├── ci/
│   ├── workflows/
│   └── templates/
├── docs/
│   └── architecture/
```

---

## 9. 🗺️ Migration Roadmap

| Stage | Action | Deliverable |
|-------|--------|-------------|
| **1** | Refactor router boundaries | Service stubs created |
| **2** | Establish shared contracts repo | Schema validation CI hook |
| **3** | Split containers & workflows | Parallel builds active |
| **4** | Introduce gateway & bus | Parallel orchestration working |
| **5** | Add telemetry + autoscaling | Full federated observability |

### Stage 1: Refactor Router Boundaries (Days 1-2)
- Map 54 routers to 5 services
- Create service stub directories
- Document router → service mapping

### Stage 2: Establish Shared Contracts (Days 2-3)
- Create `shared/contracts/` directory
- Move Pydantic models to shared
- Generate OpenAPI schemas
- Add contract validation CI hook

### Stage 3: Split Containers & Workflows (Days 4-5)
- Create separate Dockerfiles per service
- Split requirements.txt by service
- Create docker-compose.dev.yml
- Set up parallel build configuration
- Create independent CI workflows

### Stage 4: Introduce Gateway & Event Bus (Days 6-7)
- Deploy API Gateway (Traefik)
- Configure routing by path/tag
- Deploy Redis Streams for event bus
- Implement event producers/consumers
- Add aggregator layer

### Stage 5: Add Telemetry & Autoscaling (Day 7+)
- Add OpenTelemetry to all services
- Configure distributed tracing (Jaeger)
- Add service-specific metrics
- Create unified observability dashboard
- Implement autoscaling rules (K8s HPA)

---

## 10. ✅ Success Criteria

- ⏱️ **Aggregate build time &lt; 10 minutes**
- 🚀 **Independent deployments per service**
- 🔒 **Fault isolation verified in test clusters**
- 📝 **Strict contract validation in CI**
- 🔄 **Drop-in container replacement successful**

---

## 11. 📊 Impact

| Area | Result |
|------|--------|
| **Performance** | Parallel CI/CD reduces build time by ~70% |
| **Reliability** | Service failures contained within domain |
| **Scalability** | Horizontal scaling per service |
| **Maintainability** | Reduced code ownership overlap |
| **Future-Proofing** | Runtime-agnostic contracts enable evolution |

### Quantified Impact (Cross-reference SPEC-099)

**Build Time Reduction:**
- Before: 30+ minutes monolithic build
- After: &lt; 10 minutes aggregate (parallel builds)
- Improvement: **~70% faster CI/CD**

**Deployment Speed:**
- Before: Deploy entire monolith for any change
- After: Deploy only changed service
- Improvement: **Per-service rollouts in &lt;5 minutes**

**Infrastructure Efficiency:**
- Reference SPEC-099 ROI matrix for runtime optimizations
- GraphOps (Rust): -90% latency, +10x throughput
- Memory Service (Rust): -83% latency, +5-6x throughput
- Combined: **30-60% infrastructure cost reduction**

---

## 12. 🎯 Conclusion

**SPEC-100 establishes the architectural foundation for runtime-agnostic modularization of Ninaivalaigal's API layer.**

It decouples functional domains, accelerates delivery, and introduces **contract-driven interoperability** across all future runtimes and services—while remaining fully compatible with existing clients and infrastructure.

### Integration with Other SPECs

- **SPEC-099 (Rust Migration):** Provides runtime optimization within SPEC-100 architecture
- **SPEC-040/062 (Memory/Graph):** First services to adopt federated architecture
- **SPEC-101 (Observability):** Next-phase spec for unified telemetry across federation

### Why This Matters

- **099 = Runtime specialization** (Rust for performance)
- **100 = Runtime-agnostic modular framework** (Python + Rust + future)
- **101 = Visibility & governance layer** tying it all together

This way:
- SPEC-099 remains lean and focused on ROI, not architecture
- SPEC-100 becomes the full architectural north star
- SPEC-101 (optional next step) covers unified metrics, observability, and performance validation once the split stack stabilizes

---

## Acceptance Criteria

- [ ] 5 service boundaries defined and documented
- [ ] Shared contracts repository created with validation
- [ ] Parallel build configuration working
- [ ] Gateway routing operational
- [ ] Event bus implemented (Redis Streams)
- [ ] Aggregator layer handling multi-service calls
- [ ] Independent CI workflows per service
- [ ] Health endpoints standardized across services
- [ ] Drop-in container replacement verified
- [ ] Documentation complete

---

## References

- [SPEC-099: Rust Migration Strategy & ROI Analysis](../099-rust-migration-strategy/)
- [SPEC-040: Memory Service Core Engine](../040-memory-service-core-engine/)
- [SPEC-062: GraphOps Stack Deployment](../062-graphops-stack-deployment/)
- [Microservices Patterns](https://microservices.io/patterns/)
- [Twelve-Factor App](https://12factor.net/)
- [Protocol Buffers](https://protobuf.dev/)

---

## Validation Status

✅ **Service Boundaries Validated:** October 30, 2025
- See: [Cross-Validation Report](/docs/architecture/SPEC_CROSS_VALIDATION_REPORT.md)
- Contract-first integration working correctly
- Runtime-agnostic boundaries confirmed
- Service isolation validated (5 independent services)
- Port allocation documented and operational

### Implementation Status
- ✅ **Service Separation:** Core API, Memory, Graph, Business, Admin/Vendor
- ✅ **Port Allocation:** 13390-13395 (SPEC-086 compliant)
- ✅ **Layer Classification:** Compute (Rust), Cognitive (Python), Routing
- 🌿 **Gateway Layer:** Planned (unified API gateway)
- 🌿 **Event Bus:** Planned (Redis Streams)

---

## Related Documentation

### Architecture Documents
- [Container Language Reference](/docs/architecture/CONTAINER_LANGUAGE_REFERENCE.md) - Language rationale per service
- [Architecture Overview](/docs/architecture/ARCHITECTURE_OVERVIEW.md#service-topology) - Complete service topology
- [Container Roadmap](/docs/architecture/CONTAINER_ROADMAP.md) - Future service plans

### Related SPECs
- **SPEC-020:** Memory Provider Architecture (Provider registry pattern)
- **SPEC-099:** Rust Migration Strategy (Runtime specialization)
- **SPEC-101:** Unified Observability (Service monitoring)

### Taiga Tasks
- **US#144:** Architecture Documentation: Hybrid Compute-Cognitive Architecture

---

**Last Updated:** October 30, 2025 (Validation Complete + Cross-References Added)
**Next Review:** Q1 2026 (after observability stack deployment)
**Status:** Implemented ✅ + Validated ✅
