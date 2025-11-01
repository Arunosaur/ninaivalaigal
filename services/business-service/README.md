# Business Service - SPEC-100 Modularization

**Task #34:** Business Service - Code Extraction (START)
**Status:** 🟡 In Progress
**SPEC:** SPEC-100 (API Container Modularization & Runtime-Agnostic Federation)

---

## 📋 Overview

The Business Service is part of SPEC-100's API modularization strategy, responsible for:

- **Billing Management:** Stripe integration, subscription handling
- **Usage Analytics:** Team growth, user engagement, conversion metrics
- **Admin Intelligence:** Revenue analytics, churn analysis, business insights

This service extracts business logic from the monolithic `server/` directory into an independently deployable microservice.

---

## 🎯 SPEC-100 Compliance

### Service Role (SPEC-100 Section 3)
> **Business Service:** Billing, Usage, Analytics - Independently scalable

### Standardized Endpoints (SPEC-100 Section 5.3)
- ✅ `GET /health` - Basic liveness check
- ✅ `GET /ready` - Readiness with dependency validation
- ✅ `GET /metrics` - Prometheus-format metrics

### Business Endpoints
- `GET /billing/plans` - Available subscription plans
- `GET /billing/subscription/{team_id}` - Team subscription info
- `POST /billing/subscription/create` - Create subscription
- `POST /billing/subscription/cancel/{team_id}` - Cancel subscription
- `GET /analytics/team-growth` - Team growth metrics
- `GET /analytics/usage/{team_id}` - Team usage metrics
- `GET /analytics/revenue` - Revenue and monetization metrics
- `GET /analytics/admin/overview` - Admin dashboard overview

---

## 🏗️ Architecture

### Directory Structure
```
services/business-service/
├── main.py                    # FastAPI application
├── routers/
│   ├── health.py              # SPEC-100 health endpoints
│   ├── metrics.py             # SPEC-100 metrics endpoint
│   ├── billing.py             # Billing management
│   └── analytics.py           # Analytics and BI
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
└── README.md                  # This file
```

### Extracted from `server/`
- `server/billing_console_api.py` → `routers/billing.py`
- `server/team_billing_portal_api.py` → `routers/billing.py`
- `server/usage_analytics_api.py` → `routers/analytics.py`
- `server/admin_analytics_api.py` → `routers/analytics.py`

---

## 🚀 Quick Start

### Local Development
```bash
cd services/business-service

# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

Service will be available at: `http://localhost:13391`

### Docker
```bash
# Build image
docker build -t ninaivalaigal-business-service:latest .

# Run container
docker run -d \
  --name ninaivalaigal-dev-business-service \
  -p 13391:13391 \
  -e DB_URI=postgresql://user:pass@host:5432/db \  # pragma: allowlist secret
  -e REDIS_URI=redis://host:6379 \
  -e STRIPE_SECRET_KEY=sk_test_... \
  ninaivalaigal-business-service:latest
```

---

## 🧪 Testing Endpoints

### Health Check
```bash
curl http://localhost:13391/health
```

### Readiness Check
```bash
curl http://localhost:13391/ready
```

### Metrics
```bash
curl http://localhost:13391/metrics
```

### Billing Plans
```bash
curl http://localhost:13391/billing/plans
```

### Analytics
```bash
curl http://localhost:13391/analytics/team-growth?days=30
curl http://localhost:13391/analytics/revenue?period=month
```

---

## 📊 Task #34 Progress

### Completed ✅
1. **Directory Structure** - SPEC-100 compliant layout
2. **Health Endpoints** - `/health`, `/ready`, `/metrics`
3. **Billing Router** - Placeholder endpoints with plan data
4. **Analytics Router** - Placeholder endpoints with metrics
5. **Requirements** - Python dependencies defined
6. **Dockerfile** - Container build definition
7. **Documentation** - This README

### Pending ⏳
1. **Full Code Migration** - Move complete logic from `server/`
2. **Database Integration** - Connect to existing ninaivalaigal-dev-db
3. **Stripe Integration** - Real payment processing
4. **Authentication** - JWT validation and RBAC
5. **Testing** - Unit and integration tests
6. **Container Deployment** - Build and run in existing stack

---

## 🔗 Integration with Existing Infrastructure

### Dependencies
- **Database:** `ninaivalaigal-dev-db` (PostgreSQL + pgvector)
- **Redis:** `ninaivalaigal-dev-redis` (Caching)
- **PgBouncer:** `ninaivalaigal-dev-pgbouncer` (Connection pooling)

### Port Assignment
- **Business Service:** `13391`
- **Core API:** `8000`
- **Memory Service:** `8001`

### Naming Convention
- Container: `ninaivalaigal-dev-business-service`
- Follows standard: `ninaivalaigal-{env}-{service}`

---

## 📈 Next Steps (Task #35+)

### Phase 1: Full Extraction
- Migrate complete billing logic from `server/billing_*.py`
- Migrate complete analytics logic from `server/*_analytics_api.py`
- Integrate with existing database schemas

### Phase 2: Enhancement
- Add comprehensive error handling
- Implement proper authentication
- Add rate limiting and caching
- Create integration tests

### Phase 3: Production
- Set up CI/CD pipeline
- Configure monitoring and alerting
- Add observability hooks
- Deploy to production infrastructure

---

## 🔍 SPEC-100 References

- **Section 3:** Target Architecture - Business Service role
- **Section 4:** Orchestration & Communication Model
- **Section 5.3:** Standardized Health Endpoints
- **Section 5.4:** Unified Environment Contract
- **Section 9:** Migration Roadmap (Stage 1-2)

---

## 📚 Related Documentation

- **SPEC-100:** `/specs/100-api-container-modularization/README.md`
- **Core API:** `/services/core-api/SPEC_100_IMPLEMENTATION.md`
- **Billing SPECs:** `/specs/026-standalone-teams-billing/`, `/specs/027-billing-engine-integration/`

---

## 📝 Notes

### Why "START"?
Task #34 is marked as "START" because it initiates the Business Service extraction. This is a foundational step in SPEC-100's modularization roadmap, creating the structure and placeholder endpoints before full migration.

### Placeholder Endpoints
Current endpoints return placeholder data to demonstrate the API contract. Full implementation will:
- Query actual database for real metrics
- Integrate with Stripe for live billing
- Implement proper authentication and authorization
- Add caching and performance optimizations

### Development Status
- **Foundation:** ✅ Complete
- **Placeholders:** ✅ Complete
- **Full Migration:** ⏳ Pending (Task #35+)

---

**Created:** October 18, 2025
**Status:** Phase 1 - Structure Complete
**Next:** Full code extraction and integration
