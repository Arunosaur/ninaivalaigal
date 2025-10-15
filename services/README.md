# Ninaivalaigal Services

**SPEC-100: API Container Modularization & Runtime-Agnostic Federation**

This directory contains the modularized microservices architecture for Ninaivalaigal, decomposed from the monolithic API.

---

## 📁 Service Structure

```
services/
├── core-api/               # Authentication, Users, Teams, RBAC
├── memory-service/         # Context, Recording, State Persistence
├── graph-ai-service/       # Intelligence & Feedback Processing
├── business-service/       # Billing, Usage, Analytics
└── admin-vendor-service/   # Admin + Vendor Portals
```

---

## 🎯 Service Boundaries

### Core API
**Responsibility**: Authentication and user management
- User authentication and authorization
- Team management
- Organization management
- Role-based access control (RBAC)
- Token management
- API key management

**Port**: 8000
**Health**: `/health`
**Metrics**: `/metrics`

---

### Memory Service
**Responsibility**: Memory substrate and context management
- Memory CRUD operations
- Context management and scoping
- Recording sessions
- Memory substrate
- Timeline views
- Memory access control (ACL)
- Drift detection
- Memory health monitoring

**Port**: 8001
**Health**: `/health`
**Metrics**: `/metrics`

---

### Graph/AI Service
**Responsibility**: Graph intelligence and AI integrations
- Graph intelligence and analytics
- AI integrations (Copilot, Universal AI)
- Insights generation
- Feedback processing
- Suggestions and recommendations
- Agentic workflows
- Relevance scoring

**Port**: 8002
**Health**: `/health`
**Metrics**: `/metrics`

---

### Business Service
**Responsibility**: Billing and business operations
- Billing console and invoices
- Usage analytics and tracking
- Performance monitoring
- Gamification
- Partner ecosystem
- Early adopter programs
- Provider management

**Port**: 8003
**Health**: `/health`
**Metrics**: `/metrics`

---

### Admin/Vendor Service
**Responsibility**: Internal admin and vendor portals
- Admin analytics and dashboards
- Vendor management
- Discussion forums
- Approval workflows
- Spec management
- Demo endpoints

**Port**: 8004
**Health**: `/health`
**Metrics**: `/metrics`

---

## 🔗 Inter-Service Communication

### Synchronous (REST/gRPC)
- Authentication: All services call Core API for auth validation
- Data queries: Services expose REST/gRPC APIs for data access

### Asynchronous (Event Bus)
- Redis Streams for event-driven communication
- Events: `user:created`, `memory:created`, `insight:generated`
- Each service subscribes to relevant event streams

---

## 📦 Deployment

### Local Development
```bash
# Start all services with docker-compose
docker-compose -f docker/docker-compose.dev.yml up

# Or start individual services
cd services/core-api
uvicorn main:app --reload --port 8000
```

### Production
Each service has independent CI/CD pipeline in `.github/workflows/`

---

## 🧪 Testing

Each service has its own test suite:
```bash
# Test individual service
cd services/core-api
pytest tests/

# Test all services
pytest services/*/tests/
```

---

## 📊 Monitoring

All services expose:
- **Health check**: `GET /health`
- **Readiness check**: `GET /ready`
- **Prometheus metrics**: `GET /metrics`

Unified dashboard: `monitoring/grafana-dashboards/services-overview.json`

---

## 🔄 Migration Status

| Service | Status | Progress |
|---------|--------|----------|
| Core API | 🟡 Planned | 0% |
| Memory Service | 🟡 Planned | 0% |
| Graph/AI Service | 🟡 Planned | 0% |
| Business Service | 🟡 Planned | 0% |
| Admin/Vendor Service | 🟡 Planned | 0% |

**Overall Progress**: Stage 1 (Router Analysis) - 75% complete

---

## 📚 Documentation

- **Architecture Overview**: `docs/architecture/spec-100-router-mapping.md`
- **Migration Guide**: `docs/architecture/spec-100-migration-guide.md` (coming soon)
- **API Contracts**: `shared/contracts/`
- **Deployment Guide**: `docs/deployment/services-deployment.md` (coming soon)

---

## 🚀 Next Steps

### Stage 1: Refactor Router Boundaries (In Progress)
- [x] Router inventory and analysis
- [x] Service directory structure
- [x] Service stubs initialized
- [ ] Shared components extracted
- [ ] Documentation complete

### Stage 2: Establish Shared Contracts (Next)
- [ ] OpenAPI schemas per service
- [ ] JSON Schema validation
- [ ] Contract validation CI
- [ ] Contracts package

### Stage 3: Split Containers & Workflows
- [ ] Separate Dockerfiles
- [ ] docker-compose.dev.yml
- [ ] Independent CI workflows
- [ ] Parallel builds

---

**Last Updated**: 2025-10-15
**Status**: Active Development
**Lead**: Developer C
