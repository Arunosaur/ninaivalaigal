# SPEC-100: API Container Modularization - Implementation Checklist

**Status:** 🟢 Approved for Implementation
**Start Date:** October 15, 2025
**Target Completion:** October 22, 2025 (1 week)
**Owner:** Architecture Team

> **📖 Full Specification:** See [specs/100-api-container-modularization/README.md](../specs/100-api-container-modularization/README.md)

---

## 📋 Overview

Transform monolithic API (49K lines, 54 routers, 30+ min build) into 5 independent microservices with <10 min aggregate build time.

This checklist tracks the **implementation tasks** for SPEC-100. For the complete architectural specification including orchestration, communication model, and future enhancements, refer to the main README.

**Success Criteria:**
- ⏱ Aggregate build time < 10 minutes
- 🚀 Independent deployments per service
- 🔒 Fault isolation verified in test clusters
- 📝 Strict contract validation in CI
- 🔄 Drop-in container replacement successful

---

## 🎯 5-Stage Migration Roadmap

### **Stage 1: Refactor Router Boundaries** (Day 1-2)
**Goal:** Create service stubs and clear boundaries
**Deliverable:** Service stubs created

- [ ] **Map 54 routers to 5 services**
  ```bash
  services/
  ├── core-api/          # Auth, Users, Teams, RBAC (lightweight)
  ├── memory-service/    # Memory, Context, Recording (substrate)
  ├── graph-ai-service/  # Graph Intelligence, AI Feedback (heavy ML)
  ├── business-service/  # Billing, Usage, Analytics
  └── admin-vendor-service/  # Admin Console, Vendor Portal
  ```

- [ ] **Document router → service mapping**
  ```bash
  # Create mapping document
  touch specs/100-api-container-modularization/router-service-mapping.md
  ```

- [ ] **Create service stub directories**
  ```bash
  mkdir -p services/{core-api,memory-service,graph-ai-service,business-service,admin-vendor-service}
  ```

- [ ] **Define service boundaries (no implementation yet)**
  - Core API: auth.py, signup_api.py, routers/users.py, routers/teams.py, rbac_*.py
  - Memory: memory_*.py, context_*.py, recording_*.py
  - Graph/AI: graph_*.py, ai_*.py, insights_api.py, discussion_api.py
  - Business: billing_*.py, usage_*.py, analytics_*.py, invoice_*.py
  - Admin/Vendor: vendor_*.py, admin_*.py

**Estimated Time:** 6-8 hours

---

### **Stage 2: Establish Shared Contracts** (Day 2-3)
**Goal:** Create schema validation CI hook
**Deliverable:** Schema validation CI hook

- [ ] **Create shared contracts directory**
  ```bash
  mkdir -p shared/contracts/{auth,memory,graph,business,admin}
  ```

- [ ] **Move Pydantic models to shared/**
  - [ ] Extract auth models → `shared/contracts/auth/`
  - [ ] Extract memory models → `shared/contracts/memory/`
  - [ ] Extract graph models → `shared/contracts/graph/`
  - [ ] Extract business models → `shared/contracts/business/`
  - [ ] Extract admin models → `shared/contracts/admin/`

- [ ] **Generate OpenAPI schemas from Pydantic models**
  ```bash
  python3 scripts/generate_openapi_schemas.py
  ```

- [ ] **Create schema validation script**
  ```bash
  touch ci/validate-api-contracts.py
  chmod +x ci/validate-api-contracts.py
  ```

- [ ] **Add to pre-commit hooks**
  ```yaml
  # .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: validate-api-contracts
        name: Validate API Contracts
        entry: python3 ci/validate-api-contracts.py
        language: system
        pass_filenames: false
  ```

- [ ] **Publish as private PyPI package**
  ```bash
  cd shared/contracts/
  python3 setup.py sdist bdist_wheel
  twine upload --repository-url <private-pypi> dist/*
  ```

**Estimated Time:** 8-10 hours

---

### **Stage 3: Split Containers & Workflows** (Day 4-5)
**Goal:** Parallel builds active
**Deliverable:** Parallel builds active

- [ ] **Create separate Dockerfiles**
  ```bash
  containers/
  ├── core-api/Dockerfile
  ├── memory-service/Dockerfile
  ├── graph-ai-service/Dockerfile
  ├── business-service/Dockerfile
  └── admin-vendor-service/Dockerfile
  ```

- [ ] **Split requirements.txt by service**
  - [ ] `core-api/requirements.txt` (minimal: fastapi, uvicorn, jwt, redis)
  - [ ] `memory-service/requirements.txt` (sqlalchemy, psycopg2, redis)
  - [ ] `graph-ai-service/requirements.txt` (scikit-learn, numpy, pandas, torch)
  - [ ] `business-service/requirements.txt` (stripe, reportlab, pandas)
  - [ ] `admin-vendor-service/requirements.txt` (minimal)

- [ ] **Create docker-compose.dev.yml**
  ```yaml
  # docker-compose.dev.yml
  version: '3.8'
  services:
    core-api:
      build: ./services/core-api
      ports: ["13390:8000"]
    memory-service:
      build: ./services/memory-service
      ports: ["13391:8000"]
    # ... etc
  ```

- [ ] **Create parallel build configuration**
  ```bash
  # docker-bake.hcl
  group "all" {
    targets = ["core-api", "memory-service", "graph-ai-service", "business-service", "admin-vendor-service"]
  }

  target "core-api" {
    dockerfile = "containers/core-api/Dockerfile"
    tags = ["nina-core-api:arm64"]
  }
  # ... etc
  ```

- [ ] **Create independent CI workflows**
  ```bash
  .github/workflows/
  ├── build-core-api.yml
  ├── build-memory-service.yml
  ├── build-graph-ai-service.yml
  ├── build-business-service.yml
  └── build-admin-vendor-service.yml
  ```

- [ ] **Test parallel builds**
  ```bash
  docker buildx bake --no-cache
  ```

- [ ] **Measure build times**
  ```bash
  time docker buildx bake --no-cache
  # Target: < 10 minutes aggregate
  ```

- [ ] **Verify container sizes**
  ```bash
  docker images | grep nina-
  # Core API should be <500MB
  # Graph/AI can be 1-2GB (ML dependencies)
  ```

**Estimated Time:** 12-14 hours

---

### **Stage 4: Introduce Gateway & Event Bus** (Day 6-7)
**Goal:** Parallel orchestration working
**Deliverable:** Parallel orchestration working

- [ ] **Deploy API Gateway (Traefik or Envoy)**
  ```yaml
  # docker-compose.dev.yml
  gateway:
    image: traefik:v2.10
    ports: ["13370:80", "13371:8080"]
    volumes:
      - ./traefik.yml:/etc/traefik/traefik.yml
  ```

- [ ] **Configure routing by path/tag**
  ```yaml
  # traefik.yml
  http:
    routers:
      auth-router:
        rule: "PathPrefix(`/auth`)"
        service: core-api
      memory-router:
        rule: "PathPrefix(`/memory`, `/context`, `/recording`)"
        service: memory-service
  ```

- [ ] **Deploy Redis Streams for event bus**
  ```bash
  # Already have Redis, just configure streams
  redis-cli XADD memory:events * action created memory_id 123
  ```

- [ ] **Implement event producers**
  - [ ] Core API publishes `user:created` events
  - [ ] Memory Service publishes `memory:created` events
  - [ ] Graph/AI Service publishes `insight:generated` events

- [ ] **Implement event consumers**
  - [ ] Graph/AI listens to `memory:created` → triggers analysis
  - [ ] Business Service listens to `user:created` → initializes billing
  - [ ] Admin Service listens to all events → updates dashboards

- [ ] **Add aggregator layer**
  ```python
  # services/gateway/aggregator.py
  async def aggregate_context_analysis(context_id: str):
      memory_data = await memory_service.get_context(context_id)
      insights = await graph_service.analyze_context(context_id)
      return {"context": memory_data, "insights": insights}
  ```

- [ ] **Test parallel orchestration**
  ```bash
  # POST /context/analyze should call Memory + Graph in parallel
  curl -X POST http://localhost:13370/context/123/analyze
  # Verify: both services called, results aggregated, no chained calls
  ```

**Estimated Time:** 10-12 hours

---

### **Stage 5: Add Telemetry & Autoscaling** (Day 7+)
**Goal:** Full federated observability
**Deliverable:** Full federated observability

- [ ] **Add OpenTelemetry to all services**
  ```python
  # shared/telemetry.py
  from opentelemetry import trace
  from opentelemetry.sdk.trace import TracerProvider
  from opentelemetry.sdk.trace.export import BatchSpanProcessor
  from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

  tracer_provider = TracerProvider()
  tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
  trace.set_tracer_provider(tracer_provider)
  ```

- [ ] **Configure distributed tracing**
  ```yaml
  # docker-compose.dev.yml
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports: ["16686:16686", "4317:4317"]
  ```

- [ ] **Add service-specific metrics**
  ```python
  # Each service exposes /metrics
  from prometheus_client import Counter, Histogram

  request_count = Counter('service_requests_total', 'Total requests', ['service', 'endpoint'])
  request_duration = Histogram('service_request_duration_seconds', 'Request duration')
  ```

- [ ] **Create unified observability dashboard**
  - Grafana dashboard showing all 5 services
  - Service health, throughput, latency, error rate
  - Cross-service trace visualization

- [ ] **Implement autoscaling rules**
  ```yaml
  # k8s/core-api-hpa.yml (future)
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: core-api
  spec:
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  ```

**Estimated Time:** 8-10 hours

---

## 📊 Progress Tracking

| Stage | Status | Start | End | Duration | Blockers |
|-------|--------|-------|-----|----------|----------|
| 1. Refactor Boundaries | ⏳ Pending | - | - | - | - |
| 2. Shared Contracts | ⏳ Pending | - | - | - | - |
| 3. Split Containers | ⏳ Pending | - | - | - | - |
| 4. Gateway & Bus | ⏳ Pending | - | - | - | - |
| 5. Telemetry | ⏳ Pending | - | - | - | - |

---

## 🎯 Daily Standup Template

**Date:** [Date]
**Developer:** [Name]

**Yesterday:**
- [x] Completed task
- [ ] In-progress task

**Today:**
- [ ] Planned task
- [ ] Planned task

**Blockers:**
- None / [Blocker description]

**Build Time Measurement:**
- Monolith: [X] minutes
- Service 1: [X] minutes
- Service 2: [X] minutes
- Aggregate: [X] minutes

---

## 🔍 Testing Checklist

### Per-Service Tests
- [ ] **Core API**
  - [ ] Auth flow (signup, login, token refresh)
  - [ ] User management CRUD
  - [ ] Team management CRUD
  - [ ] RBAC permissions

- [ ] **Memory Service**
  - [ ] Memory CRUD
  - [ ] Context operations
  - [ ] Recording ingestion
  - [ ] State persistence

- [ ] **Graph/AI Service**
  - [ ] Graph query execution
  - [ ] Insight generation
  - [ ] AI feedback processing
  - [ ] ML model inference

- [ ] **Business Service**
  - [ ] Billing operations
  - [ ] Usage tracking
  - [ ] Analytics queries
  - [ ] Invoice generation

- [ ] **Admin/Vendor Service**
  - [ ] Admin console access
  - [ ] Vendor portal operations
  - [ ] Internal-only endpoints

### Integration Tests
- [ ] **Gateway routing**
  - [ ] Requests route to correct service
  - [ ] Load balancing works
  - [ ] Health checks propagate

- [ ] **Event bus**
  - [ ] Events publish successfully
  - [ ] Consumers receive events
  - [ ] No message loss

- [ ] **Cross-service calls**
  - [ ] Aggregator returns unified responses
  - [ ] Parallel execution works
  - [ ] No circular dependencies

### Performance Tests
- [ ] **Build times**
  - [ ] Each service builds < 5 minutes
  - [ ] Parallel build < 10 minutes aggregate
  - [ ] No cache invalidation issues

- [ ] **Runtime performance**
  - [ ] Response times unchanged
  - [ ] Throughput maintained
  - [ ] No N+1 query problems

### Deployment Tests
- [ ] **Container replacement**
  - [ ] Drop-in replacement successful
  - [ ] No client changes required
  - [ ] Gateway handles routing

- [ ] **Fault isolation**
  - [ ] Graph/AI failure doesn't affect Core API
  - [ ] Memory Service failure isolated
  - [ ] Circuit breakers work

---

## 📝 Documentation Requirements

- [ ] **Architecture documentation**
  - [ ] Update SPEC-100 with final architecture
  - [ ] Create service interaction diagrams
  - [ ] Document gateway routing rules

- [ ] **API documentation**
  - [ ] Generate OpenAPI specs per service
  - [ ] Update external API docs
  - [ ] Document event schemas

- [ ] **Deployment documentation**
  - [ ] Update container build instructions
  - [ ] Document docker-compose usage
  - [ ] Create rollback procedures

- [ ] **Developer guides**
  - [ ] How to add a new service
  - [ ] How to add a new endpoint
  - [ ] How to debug cross-service issues

---

## 🚨 Rollback Plan

**If any stage fails:**

1. **Immediate rollback** to monolithic container
   ```bash
   # Use existing nina-api:arm64 image
   container stop ninaivalaigal-dev-core-api
   container stop ninaivalaigal-dev-memory-service
   # ... stop all new services

   # Start monolith
   ./scripts/restart-api-with-latest-code.sh
   ```

2. **Preserve work**
   ```bash
   git branch spec-100-wip-$(date +%Y%m%d)
   git checkout main
   ```

3. **Document issues**
   - What failed?
   - Why did it fail?
   - What's the fix?
   - Timeline to retry?

---

## 🎉 Success Metrics

**When all stages complete:**

| Metric | Before | Target | Actual |
|--------|--------|--------|--------|
| Build Time | 30+ min | <10 min | - |
| Container Count | 1 | 5 | - |
| Lines per Container | 49K | <10K avg | - |
| Deployment Independence | No | Yes | - |
| Fault Isolation | No | Yes | - |
| Horizontal Scaling | No | Yes | - |

**Final Validation:**
```bash
# All services healthy
curl http://localhost:13370/health

# Parallel builds complete
time docker buildx bake --no-cache
# Should show < 10 minutes

# Independent deployment works
docker stop ninaivalaigal-dev-graph-ai-service
docker start ninaivalaigal-dev-graph-ai-service
# Other services unaffected

# Contract validation passes
python3 ci/validate-api-contracts.py
echo $?  # Should be 0
```

---

**Status:** Ready to start Stage 1 on October 15, 2025
**Next Review:** End of Stage 1 (October 16, 2025)
