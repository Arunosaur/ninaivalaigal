# Graph/AI Service - SPEC-100 Modularization

**Task #30:** Graph/AI Service - Architecture & Setup (EARLY START)
**Status:** 🟡 In Progress
**SPEC:** SPEC-100 (API Container Modularization), SPEC-062 (GraphOps), SPEC-064 (Graph Intelligence)

---

## 📋 Overview

The Graph/AI Service is part of SPEC-100's API modularization strategy, responsible for:

- **Graph Intelligence:** Apache AGE-powered graph reasoning
- **AI Suggestions:** ML-based relevance inference
- **Heavy Compute:** Isolated graph algorithms and analytics
- **Memory Graph:** Relationship analysis and path discovery

This service extracts graph logic from the monolithic `server/` directory into an independently deployable microservice with GraphOps integration.

---

## 🎯 SPEC Compliance

### SPEC-100: API Container Modularization
> **Graph/AI Service:** Intelligence & feedback processing - Isolated heavy compute

### SPEC-062: GraphOps Stack Deployment
- **Apache AGE:** Graph database on port 5433
- **Graph Redis:** Cache on port 6380
- **Independent Infrastructure:** Separate from main database

### SPEC-064: Graph Intelligence Architecture
- **HTTP Integration:** RESTful APIs for graph reasoning
- **Optional Dependency:** Graceful degradation if unavailable
- **Microservice-Ready:** Independent scaling and deployment

---

## 🏗️ Architecture

### Directory Structure
```
services/graph-service/
├── main.py                    # FastAPI application
├── routers/
│   ├── health.py              # SPEC-100 health endpoints
│   ├── metrics.py             # SPEC-100 metrics endpoint
│   └── graph.py               # Graph intelligence APIs
├── graph/                     # Graph reasoner logic (future)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
└── README.md                  # This file
```

### Extracted from `server/`
- `server/graph_intelligence_api.py` → `routers/graph.py`
- `server/graph/graph_reasoner.py` → `graph/` (future)
- `server/graph_rank.py` → Graph algorithms (future)

---

## 🔌 API Endpoints

### Health & Monitoring (SPEC-100)
- ✅ `GET /health` - Basic liveness check
- ✅ `GET /ready` - Readiness with GraphOps validation
- ✅ `GET /metrics` - Prometheus-format metrics

### Graph Intelligence
- ✅ `POST /graph/explain-context` - Explain memory retrieval reasoning
- ✅ `POST /graph/infer-relevance` - AI-powered suggestions
- ✅ `POST /graph/analytics` - Graph analytics and insights
- ✅ `GET /graph/status` - GraphOps infrastructure status

---

## 🧪 GraphOps Integration (SPEC-062)

### Infrastructure Components
- **Apache AGE:** PostgreSQL 15 + Apache AGE v1.5.0-rc0
  - Port: `5433`
  - Container: `ninaivalaigal-graph-db`

- **Graph Redis:** Redis 7-alpine cache
  - Port: `6380`
  - Container: `ninaivalaigal-graph-redis`

### Environment Variables
```bash
GRAPH_DB_HOST=localhost
GRAPH_DB_PORT=5433
GRAPH_DB_NAME=graph_db
GRAPH_DB_USER=graphops
GRAPH_DB_PASSWORD=graphops_password
GRAPH_REDIS_HOST=localhost
GRAPH_REDIS_PORT=6380
```

---

## 🚀 Quick Start

### Local Development
```bash
cd services/graph-service

# Install dependencies
pip install -r requirements.txt

# Start GraphOps infrastructure (SPEC-062)
make start-graph-infrastructure

# Run the service
python main.py
```

Service will be available at: `http://localhost:8001`

### Docker
```bash
# Build image
docker build -t ninaivalaigal-graph-service:latest .

# Run container
docker run -d \
  --name ninaivalaigal-dev-graph-service \
  -p 8001:8001 \
  -e GRAPH_DB_HOST=192.168.65.124 \  # pragma: allowlist secret
  -e GRAPH_DB_PORT=5433 \
  -e GRAPH_REDIS_HOST=192.168.65.122 \
  -e GRAPH_REDIS_PORT=6380 \
  ninaivalaigal-graph-service:latest
```

---

## 🧪 Testing Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Readiness Check (GraphOps)
```bash
curl http://localhost:8001/ready
```

### Graph Status
```bash
curl http://localhost:8001/graph/status
```

### Explain Context
```bash
curl -X POST http://localhost:8001/graph/explain-context \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "abc123",
    "context_type": "retrieval",
    "max_depth": 3
  }'
```

### Infer Relevance
```bash
curl -X POST http://localhost:8001/graph/infer-relevance \
  -H "Content-Type: application/json" \
  -d '{
    "current_memory_id": "abc123",
    "suggestion_count": 5
  }'
```

---

## 📊 Task #30 Progress

### Completed ✅
1. **Directory Structure** - SPEC-100 compliant layout
2. **Health Endpoints** - `/health`, `/ready`, `/metrics` with GraphOps checks
3. **Graph Router** - Placeholder endpoints for graph intelligence
4. **Requirements** - Python dependencies defined
5. **Dockerfile** - Container build definition with GraphOps env vars
6. **Documentation** - This README

### Pending ⏳
1. **GraphOps Connection** - Connect to Apache AGE (port 5433)
2. **Graph Redis Integration** - Connect to Graph Redis (port 6380)
3. **GraphReasoner Migration** - Move graph_reasoner.py logic
4. **Apache AGE Queries** - Cypher query execution
5. **Caching Layer** - Redis-based graph query caching
6. **Authentication** - JWT validation and RBAC
7. **Testing** - Unit and integration tests

---

## 🔗 Integration with Existing Infrastructure

### Port Assignment
- **Graph/AI Service:** `8001`
- **Core API:** `8000`
- **Business Service:** `8002`

### GraphOps Dependencies (SPEC-062)
- **Graph DB:** `ninaivalaigal-graph-db` (Apache AGE on port 5433)
- **Graph Redis:** `ninaivalaigal-graph-redis` (Redis on port 6380)

### Main Stack (Separate)
- **Main DB:** `ninaivalaigal-dev-db` (PostgreSQL on port 5432)
- **Main Redis:** `ninaivalaigal-dev-redis` (Redis on port 6379)
- **PgBouncer:** `ninaivalaigal-dev-pgbouncer` (port 6432)

### Naming Convention
- Container: `ninaivalaigal-dev-graph-service`
- Follows standard: `ninaivalaigal-{env}-{service}`

---

## 📈 Next Steps (Task #30+)

### Phase 1: GraphOps Connection (Current)
- Connect to Apache AGE database
- Initialize Graph Redis client
- Implement GraphReasoner integration
- Test Cypher query execution

### Phase 2: Graph Intelligence
- Migrate graph_reasoner.py logic
- Implement explain-context with real graph traversal
- Implement infer-relevance with GraphReasoner
- Add caching layer for graph queries

### Phase 3: Production
- Add comprehensive error handling
- Implement proper authentication
- Add rate limiting and caching
- Create integration tests
- Set up CI/CD pipeline
- Configure monitoring and alerting

---

## 🔍 SPEC References

### SPEC-100: API Container Modularization
- **Section 3:** Target Architecture - Graph/AI Service role
- **Section 4:** Orchestration & Communication Model
- **Section 5.3:** Standardized Health Endpoints
- **Section 5.4:** Unified Environment Contract

### SPEC-062: GraphOps Stack Deployment
- **Apache AGE:** PostgreSQL + Apache AGE on port 5433
- **Graph Redis:** Dedicated cache on port 6380
- **Dual Architecture:** ARM64 + x86_64 support
- **Makefile Commands:** start-graph-infrastructure, check-graph-health

### SPEC-064: Graph Intelligence Architecture
- **HTTP Integration:** RESTful APIs for graph reasoning
- **Optional Dependency:** Graceful degradation
- **Microservice-Ready:** Independent scaling

---

## 📚 Related Documentation

- **SPEC-100:** `/specs/100-api-container-modularization/README.md`
- **SPEC-062:** `/specs/062-graphops-deployment/README.md`
- **SPEC-064:** `/specs/064-graph-intelligence-architecture/README.md`
- **Core API:** `/services/core-api/SPEC_100_IMPLEMENTATION.md`
- **Business Service:** `/services/business-service/README.md`

---

## 📝 Notes

### Why "EARLY START"?
Task #30 is marked as "EARLY START" because it initiates the Graph/AI Service extraction before full GraphOps integration. This establishes the structure and API contracts while GraphOps connection is pending.

### Placeholder Endpoints
Current endpoints return placeholder data to demonstrate the API contract. Full implementation will:
- Execute real Cypher queries via Apache AGE
- Use GraphReasoner for AI-powered suggestions
- Implement Redis caching for graph queries
- Add proper authentication and authorization

### GraphOps Architecture
The service is designed to work with SPEC-062 GraphOps infrastructure:
- **Separate graph database** (port 5433) from main database (port 5432)
- **Dedicated graph cache** (port 6380) from main cache (port 6379)
- **Independent scaling** of graph intelligence workloads
- **Experimental freedom** without affecting main stack

---

**Created:** October 18, 2025
**Status:** Phase 1 - Structure Complete
**Next:** GraphOps connection and full graph intelligence integration
