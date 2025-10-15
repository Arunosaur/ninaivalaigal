# SPEC-100 Stage 3: Split Containers & Workflows - PLANNING

**Date**: October 15, 2025
**Stage**: Stage 3 - Split Containers & Workflows
**Status**: 📋 Planning (Ready to Start)
**Lead**: Developer C
**Prerequisites**: ✅ Stage 1 Complete (90%), ✅ Stage 2 Complete (100%)

---

## 🎯 Stage 3 Objectives

**Goal**: Create independent containerized services with separate CI/CD workflows

**Deliverables**:
1. Dockerfiles for each of the 5 services
2. Docker Compose configurations (dev + production)
3. Service-specific requirements.txt files
4. Independent GitHub Actions CI workflows
5. Service health checks and monitoring
6. Local development orchestration

**Success Criteria**:
- ✅ Each service runs independently in its own container
- ✅ Services communicate via defined contracts (REST/gRPC)
- ✅ Each service has its own CI/CD pipeline
- ✅ Local development workflow with docker-compose
- ✅ Health checks operational for all services
- ✅ Zero dependencies between service builds

---

## 📦 Service Architecture

### Service 1: Core API Service
**Container**: `ninaivalaigal-dev-core-api`
**Port**: 8000
**Responsibilities**:
- Authentication (login, signup, token refresh)
- User management (CRUD)
- Team management (CRUD)
- Organization management
- RBAC (role-based access control)
- Token management

**Dependencies**:
- PostgreSQL (database)
- Redis (session cache, rate limiting)

**Dockerfile**: `Dockerfile.core-api`

---

### Service 2: Memory Service
**Container**: `ninaivalaigal-dev-memory`
**Port**: 8001
**Responsibilities**:
- Memory CRUD operations
- Context management
- Recording sessions
- Timeline views
- Memory ACL

**Dependencies**:
- PostgreSQL (database)
- Redis (caching)
- Core API (for auth validation)

**Dockerfile**: `Dockerfile.memory-service`

---

### Service 3: Graph/AI Service
**Container**: `ninaivalaigal-dev-graph-ai`
**Port**: 8002
**Responsibilities**:
- AI intelligence operations
- Insight generation
- Feedback processing
- Suggestions and recommendations
- Graph query execution (via GraphOps gRPC)

**Dependencies**:
- PostgreSQL (database)
- Redis (caching)
- GraphOps service (gRPC on port 50051)
- Core API (for auth validation)

**Dockerfile**: `Dockerfile.graph-ai-service`

---

### Service 4: Business Service
**Container**: `ninaivalaigal-dev-business`
**Port**: 8003
**Responsibilities**:
- Billing and subscriptions
- Invoice management
- Usage analytics
- Provider management
- Revenue analytics

**Dependencies**:
- PostgreSQL (database)
- Redis (caching)
- Stripe API (external)
- Core API (for auth validation)

**Dockerfile**: `Dockerfile.business-service`

---

### Service 5: Admin/Vendor Service
**Container**: `ninaivalaigal-dev-admin`
**Port**: 8004
**Responsibilities**:
- Admin analytics and dashboards
- Vendor management
- Discussion forums
- Approval workflows
- System configuration

**Dependencies**:
- PostgreSQL (database)
- Redis (caching)
- Core API (for auth validation)

**Dockerfile**: `Dockerfile.admin-vendor-service`

---

## 🏗️ Infrastructure Components

### Shared Infrastructure
Already running (no changes needed):
- **Database**: `ninaivalaigal-dev-db` (PostgreSQL + pgvector, port 5432)
- **Redis**: `ninaivalaigal-dev-redis` (Redis cache, port 6379)
- **PgBouncer**: `ninaivalaigal-dev-pgbouncer` (Connection pooler, port 6432)
- **GraphOps**: Rust gRPC service (port 50051) - Developer A

### New Services (Stage 3)
- **Core API**: `ninaivalaigal-dev-core-api` (port 8000)
- **Memory**: `ninaivalaigal-dev-memory` (port 8001)
- **Graph/AI**: `ninaivalaigal-dev-graph-ai` (port 8002)
- **Business**: `ninaivalaigal-dev-business` (port 8003)
- **Admin/Vendor**: `ninaivalaigal-dev-admin` (port 8004)

---

## 📋 Implementation Tasks

### Phase 3A: Dockerfile Creation (Week 1)

**Task 3.1: Create Base Dockerfile Template** (2 hours)
- [ ] Create shared base image with common dependencies
- [ ] Python 3.11-slim base
- [ ] Common system packages (gcc, libpq-dev)
- [ ] Security hardening

**Task 3.2: Core API Dockerfile** (3 hours)
- [ ] Create `Dockerfile.core-api`
- [ ] Copy only core API code
- [ ] Service-specific requirements.txt
- [ ] Health check endpoint
- [ ] Build and test locally

**Task 3.3: Memory Service Dockerfile** (3 hours)
- [ ] Create `Dockerfile.memory-service`
- [ ] Copy only memory service code
- [ ] Service-specific dependencies
- [ ] Health check endpoint
- [ ] Build and test locally

**Task 3.4: Graph/AI Service Dockerfile** (3 hours)
- [ ] Create `Dockerfile.graph-ai-service`
- [ ] Copy only graph/AI code
- [ ] gRPC client dependencies
- [ ] Health check endpoint
- [ ] Build and test locally

**Task 3.5: Business Service Dockerfile** (3 hours)
- [ ] Create `Dockerfile.business-service`
- [ ] Copy only business logic code
- [ ] Stripe SDK dependencies
- [ ] Health check endpoint
- [ ] Build and test locally

**Task 3.6: Admin/Vendor Service Dockerfile** (3 hours)
- [ ] Create `Dockerfile.admin-vendor-service`
- [ ] Copy only admin/vendor code
- [ ] Service-specific dependencies
- [ ] Health check endpoint
- [ ] Build and test locally

**Task 3.7: Create Apple Container CLI How-To Guides** (4 hours)
- [ ] `how-to/container-builds/apple/08-core-api.md`
- [ ] `how-to/container-builds/apple/09-memory-service.md`
- [ ] `how-to/container-builds/apple/10-graph-ai-service.md`
- [ ] `how-to/container-builds/apple/11-business-service.md`
- [ ] `how-to/container-builds/apple/12-admin-vendor-service.md`
- [ ] Follow existing standards from `STANDARDS.md`
- [ ] Include both build methods (direct + Docker workaround)
- [ ] Document container networking and IP discovery

---

### Phase 3B: Dependency Splitting (Week 1-2)

**Task 3.8: Analyze Current Dependencies** (2 hours)
- [ ] Read current `server/requirements.txt`
- [ ] Map each dependency to service(s) that need it
- [ ] Identify shared vs service-specific dependencies

**Task 3.9: Create Service-Specific Requirements** (4 hours)
- [ ] `services/core-api/requirements.txt`
- [ ] `services/memory-service/requirements.txt`
- [ ] `services/graph-ai-service/requirements.txt`
- [ ] `services/business-service/requirements.txt`
- [ ] `services/admin-vendor-service/requirements.txt`
- [ ] `shared/requirements.txt` (common dependencies)

**Task 3.10: Validate Dependencies** (2 hours)
- [ ] Build each service independently
- [ ] Verify no missing dependencies
- [ ] Check for dependency conflicts
- [ ] Document version constraints

---

### Phase 3C: Docker Compose Configuration (Week 2)

**Task 3.11: Development Compose File** (4 hours)
- [ ] Create `docker-compose.dev.yml`
- [ ] Define all 5 services
- [ ] Service networking configuration
- [ ] Volume mounts for development
- [ ] Environment variable configuration
- [ ] Health checks for all services

**Task 3.12: Production Compose File** (3 hours)
- [ ] Create `docker-compose.prod.yml`
- [ ] Production-ready configurations
- [ ] Resource limits (CPU, memory)
- [ ] Logging configuration
- [ ] Restart policies
- [ ] Security hardening

**Task 3.13: Test Orchestration** (3 hours)
- [ ] Start all services with compose
- [ ] Verify service-to-service communication
- [ ] Test auth flow across services
- [ ] Validate health checks
- [ ] Check logs and metrics

---

### Phase 3D: CI/CD Workflows (Week 2-3)

**Task 3.14: Core API CI Workflow** (3 hours)
- [ ] Create `.github/workflows/core-api-ci.yml`
- [ ] Build and test on push
- [ ] Run service-specific tests
- [ ] Build Docker image
- [ ] Push to container registry
- [ ] Deploy to staging (optional)

**Task 3.15: Memory Service CI Workflow** (2 hours)
- [ ] Create `.github/workflows/memory-service-ci.yml`
- [ ] Mirror core API workflow structure
- [ ] Service-specific test execution
- [ ] Independent deployment

**Task 3.16: Graph/AI Service CI Workflow** (2 hours)
- [ ] Create `.github/workflows/graph-ai-service-ci.yml`
- [ ] Include gRPC client tests
- [ ] GraphOps integration validation

**Task 3.17: Business Service CI Workflow** (2 hours)
- [ ] Create `.github/workflows/business-service-ci.yml`
- [ ] Stripe integration tests (mocked)
- [ ] Invoice generation tests

**Task 3.18: Admin/Vendor Service CI Workflow** (2 hours)
- [ ] Create `.github/workflows/admin-vendor-service-ci.yml`
- [ ] Analytics validation tests
- [ ] Dashboard widget tests

**Task 3.19: Contract Validation in CI** (3 hours)
- [ ] Add OpenAPI schema validation to workflows
- [ ] Verify service implements contract
- [ ] Breaking change detection
- [ ] Contract compatibility matrix

---

### Phase 3E: Service Migration (Week 3)

**Task 3.20: Extract Core API Code** (4 hours)
- [ ] Move routers to `services/core-api/routers/`
- [ ] Move models to `services/core-api/models/`
- [ ] Create `services/core-api/main.py`
- [ ] Update import paths
- [ ] Test service independently

**Task 3.21: Extract Memory Service Code** (4 hours)
- [ ] Move memory routers to `services/memory-service/routers/`
- [ ] Move memory models to `services/memory-service/models/`
- [ ] Create `services/memory-service/main.py`
- [ ] Update import paths
- [ ] Test service independently

**Task 3.22: Extract Graph/AI Service Code** (4 hours)
- [ ] Move graph/AI routers to `services/graph-ai-service/routers/`
- [ ] Add GraphOps gRPC client
- [ ] Create `services/graph-ai-service/main.py`
- [ ] Update import paths
- [ ] Test service independently

**Task 3.23: Extract Business Service Code** (4 hours)
- [ ] Move business routers to `services/business-service/routers/`
- [ ] Move billing logic to service
- [ ] Create `services/business-service/main.py`
- [ ] Update import paths
- [ ] Test service independently

**Task 3.24: Extract Admin/Vendor Service Code** (4 hours)
- [ ] Move admin routers to `services/admin-vendor-service/routers/`
- [ ] Move vendor logic to service
- [ ] Create `services/admin-vendor-service/main.py`
- [ ] Update import paths
- [ ] Test service independently

---

## 🔧 Technical Specifications

### Container Build Strategy: Apple Container CLI First

**Primary Runtime**: Apple Container CLI
**Build Workaround**: Docker (for DNS issues) → Transfer to Apple CLI

**Build Process**:
```bash
# Method 1: Direct Apple Container CLI (preferred when DNS works)
container build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .

# Method 2: Docker build + transfer (DNS workaround)
docker build --no-cache -t nina-[service]:arm64 -f Dockerfile.[service] .
docker save nina-[service]:arm64 -o /tmp/nina-[service].tar
container image load --input /tmp/nina-[service].tar
rm /tmp/nina-[service].tar
```

**Runtime**: Always use Apple Container CLI
```bash
container run -d --name ninaivalaigal-dev-[service] \
  -p [PORT]:[PORT] \
  [ENV_VARS] \
  nina-[service]:arm64
```

---

### Dockerfile Template Structure

```dockerfile
# Base image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Ninaivalaigal Team"
LABEL service="[SERVICE_NAME]"
LABEL version="1.0.0"
LABEL runtime="apple-container-cli"

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY services/[SERVICE_NAME]/requirements.txt .
COPY shared/requirements.txt ./shared-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r shared-requirements.txt

# Application code
COPY shared/ ./shared/
COPY services/[SERVICE_NAME]/ ./

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Template

```yaml
version: '3.8'

services:
  core-api:
    build:
      context: .
      dockerfile: Dockerfile.core-api
    container_name: ninaivalaigal-dev-core-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://nina:${DB_PASSWORD}@db:5432/ninaivalaigal_dev
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - NINA_ENV=dev
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Additional services...
```

---

## 📊 Progress Tracking

### Stage 3 Milestones

| Milestone | Tasks | Status | ETA |
|-----------|-------|--------|-----|
| 3A: Dockerfiles + How-To | 3.1-3.7 | ⏳ Pending | Week 1 |
| 3B: Dependencies | 3.8-3.10 | ⏳ Pending | Week 1-2 |
| 3C: Docker Compose | 3.11-3.13 | ⏳ Pending | Week 2 |
| 3D: CI/CD Workflows | 3.14-3.19 | ⏳ Pending | Week 2-3 |
| 3E: Service Migration | 3.20-3.24 | ⏳ Pending | Week 3 |

### Time Estimates

- **Phase 3A**: 21 hours (Dockerfiles + How-To Guides)
  - Dockerfiles: 17 hours
  - How-To Guides: 4 hours
- **Phase 3B**: 8 hours (Dependencies)
- **Phase 3C**: 10 hours (Docker Compose)
- **Phase 3D**: 14 hours (CI/CD)
- **Phase 3E**: 20 hours (Migration)

**Total Stage 3**: ~74 hours (~2-3 weeks)

---

## 🎯 Success Metrics

### Build Metrics
- ✅ All 5 services build without errors
- ✅ Build time <5 minutes per service
- ✅ Image size <500MB per service
- ✅ No shared dependencies between services

### Runtime Metrics
- ✅ Service startup time <10 seconds
- ✅ Health check response <100ms
- ✅ Inter-service latency <50ms
- ✅ Memory usage <512MB per service

### CI/CD Metrics
- ✅ CI pipeline execution <5 minutes
- ✅ Test coverage >80% per service
- ✅ Zero breaking changes in contracts
- ✅ Automated deployment on merge

---

## 🚧 Risks & Mitigations

### Risk 1: Circular Dependencies Between Services
**Mitigation**: Enforce strict contract-based communication, no direct code sharing

### Risk 2: Database Schema Conflicts
**Mitigation**: Each service owns specific tables, use migration namespacing

### Risk 3: Authentication Across Services
**Mitigation**: Core API issues JWT tokens, other services validate tokens

### Risk 4: Development Environment Complexity
**Mitigation**: One-command startup with docker-compose, clear documentation

### Risk 5: CI/CD Pipeline Failures
**Mitigation**: Comprehensive testing, gradual rollout, rollback procedures

---

## 📚 Documentation Deliverables

1. **Service README files** (5 files)
   - `services/core-api/README.md`
   - `services/memory-service/README.md`
   - `services/graph-ai-service/README.md`
   - `services/business-service/README.md`
   - `services/admin-vendor-service/README.md`

2. **Deployment guides**
   - `docs/deployment/docker-compose-guide.md`
   - `docs/deployment/service-architecture.md`

3. **Development guides**
   - `docs/development/local-setup.md`
   - `docs/development/adding-new-service.md`

4. **CI/CD documentation**
   - `docs/cicd/workflow-overview.md`
   - `docs/cicd/testing-strategy.md`

---

## 🔗 Dependencies

**Prerequisites (Already Complete)**:
- ✅ Stage 1: Service boundaries defined
- ✅ Stage 2: Contracts established

**Parallel Work**:
- 🔄 Developer A: GraphOps service validation
- 🔄 Developer B: Python client for GraphOps

**Blockers**: None

---

## 👥 Team Coordination

**Developer C (Lead)**:
- Create Dockerfiles and docker-compose configurations
- Set up CI/CD workflows
- Migrate code to service directories
- Documentation

**Developer A**:
- GraphOps integration validation
- gRPC client guidance for Graph/AI service
- Performance testing

**Developer B**:
- Python client implementation
- Service testing
- API integration validation

---

## 📅 Next Actions

**Immediate (Today)**:
1. Review and approve Stage 3 plan
2. Create task tracking board
3. Set up service directory structure

**Week 1 (Starting Tomorrow)**:
1. Create all 5 Dockerfiles
2. Split requirements.txt files
3. Test individual service builds

**Week 2**:
1. Create docker-compose configurations
2. Set up CI/CD workflows
3. Begin code migration

**Week 3**:
1. Complete code migration
2. End-to-end testing
3. Documentation
4. Stage 3 completion report

---

**Last Updated**: 2025-10-15 11:45 AM
**Created By**: Developer C
**Status**: Ready for Implementation
**Estimated Completion**: 2-3 weeks
