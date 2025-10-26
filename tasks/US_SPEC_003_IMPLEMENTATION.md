# SPEC-003 Implementation Guide (Supporting Documentation)

**Date:** October 26, 2025
**Parent SPEC:** SPEC-003 - Core API Architecture
**Source of Truth:** Taiga Project Management System
**Purpose:** Detailed implementation guide to support Taiga user stories

> **Note:** All user stories and tasks are tracked in Taiga. This document provides additional technical details, code examples, and acceptance criteria to support implementation.

---

## 📋 User Story Summary

| US # | Title | Status | Priority | SPEC | Assignee | Effort |
|------|-------|--------|----------|------|----------|--------|
| US-89 | Customer UI Auth Integration | In Progress | P0 | SPEC-122, SPEC-003 | Developer A | 4-6h |
| US-90 | Grafana Monitoring Dashboards | New | P1 | SPEC-070, SPEC-101 | TBD | 3-4d |
| US-91 | API Rate Limiting & Throttling | New | P0 | SPEC-065, SPEC-003 | TBD | 2d |
| US-92 | Comprehensive API Test Suite | New | P1 | SPEC-052, SPEC-112 | TBD | 3d |
| #86 | Performance Benchmarking CI | New | P1 | SPEC-069, SPEC-099 | TBD | 3w |
| #87 | Schema Drift Prevention CI | New | P1 | SPEC-087, SPEC-088 | TBD | 1w |
| #88 | Core API Decomposition | New | P1 | SPEC-100 | TBD | 4-6w |

---

## US-89: Customer UI Auth Integration ⚡ IN PROGRESS

**Priority:** 🔴 P0 - Critical
**Status:** In Progress (Developer A)
**Effort:** 4-6 hours
**Sprint:** Current

### Description
Connect the customer UI signup/login forms to the backend authentication API, enabling full user registration and authentication flow.

### Related SPECs
- **SPEC-122**: Customer Frontend Rollout (Primary)
- **SPEC-003**: Core API Architecture
- **SPEC-006**: User Management, Authentication & Signup
- **SPEC-114**: Auth Security Integration

### Current State
```
✅ Backend API operational at 192.168.66.163:8000
✅ Customer UI running at localhost:8101
✅ Beautiful signup/login forms with Tailwind CSS
❌ No API integration - forms are UI-only placeholders
❌ No JWT token management
❌ No protected routes
```

### Acceptance Criteria
- [ ] **AC1**: Axios/fetch API client configured with base URL
- [ ] **AC2**: Signup form submits to `POST /auth/signup`
- [ ] **AC3**: Login form submits to `POST /auth/login`
- [ ] **AC4**: JWT tokens stored securely (localStorage/httpOnly cookies)
- [ ] **AC5**: Protected routes redirect unauthenticated users to /login
- [ ] **AC6**: Auth context provider available throughout app
- [ ] **AC7**: Error handling for failed auth attempts
- [ ] **AC8**: Loading states during API calls
- [ ] **AC9**: Successful login redirects to /dashboard
- [ ] **AC10**: Logout functionality clears tokens and redirects to /

### Technical Requirements

**1. API Client Setup**
```typescript
// apps/customer/src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://192.168.66.163:8000', // or use env variable
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

**2. Auth Context Provider**
```typescript
// apps/customer/src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);
export const useAuth = () => useContext(AuthContext);
```

**3. Form Handlers**
```typescript
// apps/customer/src/pages/Signup.tsx
const [formData, setFormData] = useState({ name: '', email: '', password: '' });
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setError('');

  try {
    await signup(formData.name, formData.email, formData.password);
    navigate('/dashboard');
  } catch (err) {
    setError(err.message || 'Signup failed');
  } finally {
    setLoading(false);
  }
};
```

**4. Protected Route Component**
```typescript
// apps/customer/src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return children;
};
```

### API Endpoints to Integrate

**Signup:**
```http
POST /auth/signup
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"  # pragma: allowlist secret
}

Response 201:
{
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Login:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePassword123!"  # pragma: allowlist secret
}

Response 200:
{
  "user": { ... },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Refresh Token:**
```http
POST /auth/refresh
Authorization: Bearer {old_token}

Response 200:
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Testing Requirements
- [ ] Manual testing: Signup → Login → Dashboard → Logout
- [ ] Error handling: Invalid credentials, network errors, expired tokens
- [ ] Token persistence: Refresh page maintains login state
- [ ] Token expiry: Automatic refresh or logout after expiry

### Dependencies
- None - API backend already complete

### Risks & Mitigation
- **Risk**: CORS issues between localhost:8101 and 192.168.66.163:8000
- **Mitigation**: Configure CORS in backend API to allow customer UI origin

### Definition of Done
- All acceptance criteria met
- Manual testing completed
- Code reviewed and approved
- Deployed to dev environment
- Documentation updated

### Resources
- API Documentation: http://192.168.66.163:8000/docs
- SPEC-122: specs/122-customer-frontend-rollout/
- Auth patterns: apps/internal/src/auth/ (reference)

---

## US-90: Grafana Monitoring Dashboards

**Priority:** 🟡 P1 - High
**Status:** New
**Effort:** 3-4 days
**Sprint:** Next

### Description
Set up Grafana dashboards for real-time API monitoring, performance metrics, and SLO tracking to complete the observability stack.

### Related SPECs
- **SPEC-070**: Real-time Monitoring Dashboard (Primary)
- **SPEC-101**: Unified Observability Performance
- **SPEC-118**: Observability Performance Budgets
- **SPEC-119**: Automated SLO Enforcement

### Current State
```
✅ OpenTelemetry tracing operational (Task #84)
✅ Jaeger running at localhost:16686
✅ Prometheus metrics collection active
✅ Health endpoints operational
❌ No Grafana instance deployed
❌ No real-time dashboards configured
❌ No SLO violation alerting
```

### Acceptance Criteria
- [ ] **AC1**: Grafana deployed via Apple Container CLI
- [ ] **AC2**: Connected to Prometheus data source
- [ ] **AC3**: Dashboard: API Performance Overview (RPS, latency, errors)
- [ ] **AC4**: Dashboard: Service Health (CPU, memory, connections)
- [ ] **AC5**: Dashboard: Business Metrics (users, memories, teams)
- [ ] **AC6**: Dashboard: SLO Compliance (P95 latency, uptime, error rate)
- [ ] **AC7**: Alerting rules configured for SLO violations
- [ ] **AC8**: Slack/email notifications set up
- [ ] **AC9**: Grafana accessible at localhost:3001
- [ ] **AC10**: Dashboards exported as JSON in /config/grafana/

### Technical Requirements

**1. Grafana Deployment**
```bash
# Container deployment
container run -d \
  --name ninaivalaigal-dev-grafana \
  -p 3001:3000 \
  -v grafana-data:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_SERVER_ROOT_URL=http://localhost:3001 \
  grafana/grafana:10.2.0
```

**2. Prometheus Data Source**
```yaml
# config/grafana/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**3. Dashboard: API Performance**
- Request rate (RPS) by endpoint
- P50, P95, P99 latency
- Error rate percentage
- Active connections
- Request/response sizes

**4. Dashboard: Service Health**
- CPU usage per service
- Memory usage per service
- Database connection pool status
- Redis cache hit rate
- Container health status

**5. Dashboard: SLO Compliance**
- API latency SLO: P95 < 200ms
- Uptime SLO: 99.9% availability
- Error rate SLO: < 0.1%
- Time to first byte: < 50ms

**6. Alerting Rules**
```yaml
# SLO Violation: High Latency
- alert: HighAPILatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "API P95 latency exceeds 200ms"

# SLO Violation: High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.001
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Error rate exceeds 0.1%"
```

### Dependencies
- SPEC-010: Observability and Telemetry (Complete ✅)
- Task #84: OpenTelemetry Tracing (Complete ✅)

### Definition of Done
- Grafana deployed and accessible
- All 4 dashboards configured and working
- Alerting rules active with notifications
- Documentation updated with dashboard access

### Resources
- Grafana Docs: https://grafana.com/docs/
- Prometheus Metrics: http://localhost:9090
- Jaeger Traces: http://localhost:16686

---

## US-91: API Rate Limiting & Throttling

**Priority:** 🔴 P0 - Critical (Security)
**Status:** New
**Effort:** 2 days
**Sprint:** Current

### Description
Implement rate limiting and request throttling to prevent API abuse, DDoS attacks, and ensure fair resource allocation across users.

### Related SPECs
- **SPEC-065**: Advanced Security Compliance (Primary)
- **SPEC-003**: Core API Architecture
- **SPEC-111**: CI/CD Security Baseline

### Current State
```
✅ JWT authentication working
✅ RBAC authorization in place
✅ Security headers configured
❌ No rate limiting
❌ No request throttling
❌ No IP-based blocking
❌ No user-based quotas
```

### Acceptance Criteria
- [ ] **AC1**: Rate limiting middleware implemented
- [ ] **AC2**: Per-IP limit: 100 requests/minute
- [ ] **AC3**: Per-user limit: 1000 requests/hour
- [ ] **AC4**: Per-endpoint custom limits (e.g., /auth/login: 5/min)
- [ ] **AC5**: HTTP 429 responses with Retry-After header
- [ ] **AC6**: Redis-backed rate limit storage
- [ ] **AC7**: Admin endpoints to view/reset rate limits
- [ ] **AC8**: Rate limit headers in all responses (X-RateLimit-*)
- [ ] **AC9**: Whitelist for internal services
- [ ] **AC10**: Load testing validates rate limits work

### Technical Requirements

**1. FastAPI Rate Limiting Middleware**
```python
# server/middleware/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**2. Route-Specific Limits**
```python
# Per-IP limits
@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    ...

# Per-user limits (after auth)
@app.get("/memories/")
@limiter.limit("100/minute")
@require_auth
async def get_memories(request: Request, user: User = Depends(get_current_user)):
    ...
```

**3. Custom Rate Limit Headers**
```python
# Add rate limit info to responses
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)

    # Add headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "95"
    response.headers["X-RateLimit-Reset"] = "1635724800"

    return response
```

**4. Admin Endpoints**
```python
@app.get("/admin/rate-limits/{user_id}")
@require_permission("admin.rate_limits.read")
async def get_user_rate_limit(user_id: str):
    """View user's current rate limit status"""
    ...

@app.post("/admin/rate-limits/{user_id}/reset")
@require_permission("admin.rate_limits.write")
async def reset_user_rate_limit(user_id: str):
    """Reset user's rate limit counter"""
    ...
```

**5. Rate Limit Configuration**
```yaml
# config/rate_limits.yml
global:
  per_ip: 100/minute
  per_user: 1000/hour

endpoints:
  /auth/login:
    per_ip: 5/minute
  /auth/signup:
    per_ip: 3/minute
  /memories/:
    per_user: 100/minute
  /search:
    per_user: 50/minute

whitelist:
  - 192.168.66.0/24  # Internal services
  - 127.0.0.1        # Localhost
```

### Testing Requirements
- [ ] Load testing: Verify 429 responses after limit exceeded
- [ ] Unit tests: Rate limit logic and storage
- [ ] Integration tests: End-to-end API rate limiting
- [ ] Security tests: Attempt to bypass rate limits

### Dependencies
- Redis operational (Complete ✅)

### Definition of Done
- Rate limiting middleware active on all endpoints
- Load tests confirm limits are enforced
- Documentation updated with rate limit policies
- Admin can view/manage rate limits

### Resources
- slowapi: https://github.com/laurents/slowapi
- Redis: localhost:6379

---

## US-92: Comprehensive API Test Suite

**Priority:** 🟡 P1 - High
**Status:** New
**Effort:** 3 days
**Sprint:** Next

### Description
Create a comprehensive test suite covering all API endpoints with unit tests, integration tests, and contract tests to ensure API reliability.

### Related SPECs
- **SPEC-052**: Comprehensive Test Coverage (Primary)
- **SPEC-112**: E2E Tests Playwright
- **SPEC-104**: Post-Migration Quality Verification

### Current State
```
✅ Load testing tool ready (Task #72)
✅ Test fixtures available (SPEC-056)
✅ OpenTelemetry tracing for debugging
❌ No comprehensive endpoint test suite
❌ No contract testing
❌ No regression testing in CI
❌ Coverage < 40%
```

### Acceptance Criteria
- [ ] **AC1**: Unit tests for all 277 API endpoints
- [ ] **AC2**: Integration tests for critical user flows
- [ ] **AC3**: Contract tests for service boundaries
- [ ] **AC4**: Test coverage > 80% for API routers
- [ ] **AC5**: All tests pass in CI pipeline
- [ ] **AC6**: Performance regression tests
- [ ] **AC7**: Security tests (SQL injection, XSS, auth bypass)
- [ ] **AC8**: Error handling tests (4xx, 5xx responses)
- [ ] **AC9**: Test execution time < 5 minutes
- [ ] **AC10**: Test reports generated and published

### Technical Requirements

**1. Test Structure**
```
tests/
├── unit/
│   ├── test_auth_api.py           # Auth endpoints
│   ├── test_memory_api.py         # Memory endpoints
│   ├── test_team_api.py           # Team endpoints
│   └── test_business_api.py       # Business endpoints
├── integration/
│   ├── test_user_flows.py         # End-to-end user journeys
│   ├── test_auth_flow.py          # Signup → Login → Refresh
│   └── test_memory_workflow.py    # Create → Update → Delete
├── contract/
│   ├── test_openapi_schema.py     # Schema validation
│   └── test_service_boundaries.py # Inter-service contracts
└── security/
    ├── test_auth_bypass.py        # Security vulnerabilities
    └── test_injection.py          # SQL injection, XSS
```

**2. Example Unit Test**
```python
# tests/unit/test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_signup_success():
    """Test successful user signup"""
    response = client.post("/auth/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "SecurePassword123!"  # pragma: allowlist secret
    })

    assert response.status_code == 201
    assert "token" in response.json()
    assert response.json()["user"]["email"] == "test@example.com"

def test_signup_duplicate_email():
    """Test signup with existing email returns 400"""
    # First signup
    client.post("/auth/signup", json={...})

    # Duplicate signup
    response = client.post("/auth/signup", json={...})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
```

**3. Example Integration Test**
```python
# tests/integration/test_auth_flow.py
def test_complete_auth_flow():
    """Test signup → login → access protected resource → logout"""
    # 1. Signup
    signup_response = client.post("/auth/signup", json={...})
    assert signup_response.status_code == 201
    token = signup_response.json()["token"]

    # 2. Access protected resource
    headers = {"Authorization": f"Bearer {token}"}
    memories_response = client.get("/memories/", headers=headers)
    assert memories_response.status_code == 200

    # 3. Refresh token
    refresh_response = client.post("/auth/refresh", headers=headers)
    assert refresh_response.status_code == 200
    new_token = refresh_response.json()["token"]

    # 4. Logout
    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    # 5. Verify token invalid after logout
    headers = {"Authorization": f"Bearer {token}"}
    invalid_response = client.get("/memories/", headers=headers)
    assert invalid_response.status_code == 401
```

**4. Contract Testing**
```python
# tests/contract/test_openapi_schema.py
def test_openapi_schema_valid():
    """Validate OpenAPI schema is valid and matches implementation"""
    response = client.get("/openapi.json")
    schema = response.json()

    # Validate schema structure
    assert "openapi" in schema
    assert "paths" in schema
    assert len(schema["paths"]) == 277  # All endpoints documented

    # Validate required fields
    for path, methods in schema["paths"].items():
        for method, spec in methods.items():
            assert "responses" in spec
            assert "200" in spec["responses"] or "201" in spec["responses"]
```

**5. Security Testing**
```python
# tests/security/test_auth_bypass.py
def test_auth_bypass_attempts():
    """Test various auth bypass attack vectors"""

    # No token
    response = client.get("/memories/")
    assert response.status_code == 401

    # Invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/memories/", headers=headers)
    assert response.status_code == 401

    # Expired token
    expired_token = generate_expired_token()
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/memories/", headers=headers)
    assert response.status_code == 401

    # SQL injection in query params
    response = client.get("/memories/?search=' OR '1'='1")
    assert response.status_code != 500  # Should handle gracefully
```

**6. CI Integration**
```yaml
# .github/workflows/api-tests.yml
name: API Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Run tests
        run: |
          pytest tests/ \
            --cov=server \
            --cov-report=html \
            --cov-report=term \
            --junit-xml=test-results.xml \
            --maxfail=5

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Testing Targets

**Coverage Goals:**
- Overall: > 80%
- Auth API: > 95%
- Memory API: > 90%
- Business API: > 85%
- Critical paths: 100%

**Performance Targets:**
- Test execution: < 5 minutes
- No flaky tests (> 99% pass rate)
- Parallel execution enabled

### Dependencies
- SPEC-056: Dependency & Testing Improvements (Complete ✅)
- Test fixtures available

### Definition of Done
- All 277 endpoints have unit tests
- Integration tests cover critical flows
- Security tests prevent vulnerabilities
- CI pipeline runs all tests automatically
- Coverage > 80%

### Resources
- pytest: https://docs.pytest.org/
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- Test fixtures: tests/fixtures/

---

## Existing Tasks (Update References)

### Task #86: Performance Benchmarking CI

**Status:** Update with SPEC references
**Related SPECs:**
- SPEC-069: Performance Optimization Suite ✅
- SPEC-099: Rust Migration Strategy
- SPEC-003: Core API Architecture

**Add to Description:**
```
This task validates SPEC-003 Core API Architecture performance targets:
- API response times: Sub-second for 95% of requests
- Memory retrieval: < 50ms target (achieved: 0.15ms)
- Concurrent throughput: > 1000 req/sec

See: tasks/SPEC_003_COVERAGE_ANALYSIS.md
```

---

### Task #87: Schema Drift Prevention CI

**Status:** Update with SPEC references
**Related SPECs:**
- SPEC-087: API Surface Contracts
- SPEC-088: API Versioning Strategy
- SPEC-003: Core API Architecture

**Add to Description:**
```
This task ensures SPEC-003 OpenAPI documentation remains accurate:
- 277 endpoints documented
- Contract validation in CI
- Breaking change detection

See: tasks/SPEC_003_COVERAGE_ANALYSIS.md
```

---

### Task #88: Core API Decomposition

**Status:** Update with SPEC references
**Related SPECs:**
- SPEC-100: API Container Modularization (Primary)
- SPEC-003: Core API Architecture

**Add to Description:**
```
This task decomposes SPEC-003 monolithic API into microservices:
- Current: 49K lines, 54 routers, single deployment
- Target: 5 independent services with API gateway

See: tasks/SPEC_003_COVERAGE_ANALYSIS.md
```

---

## 🔗 Cross-Reference Updates

### Update SPEC-003 README
Add to `/specs/003-core-api-architecture/README.md`:

```markdown
## Related Taiga User Stories

- **US-89**: Customer UI Auth Integration (P0)
- **US-90**: Grafana Monitoring Dashboards (P1)
- **US-91**: API Rate Limiting & Throttling (P0)
- **US-92**: Comprehensive API Test Suite (P1)
- **Task #86**: Performance Benchmarking CI (P1)
- **Task #87**: Schema Drift Prevention CI (P1)
- **Task #88**: Core API Decomposition (P1)

See: `/tasks/US_SPEC_003_IMPLEMENTATION.md`
```

### Update SPEC-122 README
Add to `/specs/122-customer-frontend-rollout/README.md`:

```markdown
## Related Taiga User Stories

- **US-89**: Customer UI Auth Integration (In Progress - Developer A)

Implementation guide: `/tasks/US_SPEC_003_IMPLEMENTATION.md`
```

---

## 📊 Implementation Priority

### Sprint 1 (Current) - 2 weeks
1. **US-89**: Customer UI Auth Integration (Developer A) - 6h
2. **US-91**: API Rate Limiting - 2d

### Sprint 2 (Next) - 2 weeks
3. **US-92**: Comprehensive API Test Suite - 3d
4. **US-90**: Grafana Monitoring Dashboards - 4d
5. **Task #87**: Schema Drift Prevention - 1w

### Sprint 3 (Future) - 3 weeks
6. **Task #86**: Performance Benchmarking CI - 3w
7. **Task #88**: Core API Decomposition - 4-6w (parallel work)

---

## 🎯 Success Metrics

**SPEC-003 Implementation Completion:**
- Authentication Flow: 95% → 100% (US-89)
- Performance Benchmarking: 80% → 100% (Task #86)
- Monitoring Dashboard: 70% → 100% (US-90)
- OpenAPI Documentation: 60% → 100% (Task #87)
- Security Hardening: 50% → 100% (US-91)
- API Testing: 40% → 100% (US-92)
- Customer UI Integration: 0% → 100% (US-89)

**Overall Target:** 100% SPEC-003 implementation by end of Sprint 3

---

**Generated:** October 26, 2025
**Next Review:** Weekly during Sprint 1
**Owner:** Engineering Team
