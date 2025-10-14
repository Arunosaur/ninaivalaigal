---
{}
---




# SPEC-105: Backend Integration & Database Connectivity

**Status**: 📋 Proposed
**Phase**: Migration Trilogy v1 - Integration
**Priority**: HIGH (Critical Path)
**Estimated Effort**: 4 hours (2 sessions)
**Dependencies**: SPEC-103 (Next.js 15 Bootstrap)

---

## 🎯 Executive Summary

**Objective**: Replace mock data with live API calls connected to PostgreSQL/Redis, establishing full-stack Ninaivalaigal system operational end-to-end.

**Outcome**: Production-ready frontend ↔ backend ↔ database integration with authenticated API routes, environment security, and smoke test validation.

---

## 📋 Context

### Current State (Post SPEC-103)
- ✅ Modern Next.js 15 frontend with component library
- ✅ Storybook documentation for UI components
- ✅ Mock data powering dashboard and analytics views
- ❌ No real backend API connection
- ❌ Frontend isolated from Nina Intelligence Stack

### Target State (Post SPEC-105)
- ✅ FastAPI backend serving real data endpoints
- ✅ PostgreSQL + Redis connected and operational
- ✅ Frontend consuming live API data via Next.js API routes
- ✅ Environment variables and secrets secured
- ✅ Smoke tests validating end-to-end connectivity
- ✅ **Full stack Ninaivalaigal operational**

### Strategic Importance
This SPEC bridges the "frontend island" created in SPEC-103 with the proven Nina Intelligence Stack (nina-intelligence-db + nina-intelligence-cache + nv-api), achieving **true full-stack operational status**.

---

## 🏗️ Architecture Overview

### Integration Stack
```
┌─────────────────────────────────────────────────┐
│  Frontend (Next.js 15) - Port 3000              │
│  ├── app/api/                 [API Routes]      │
│  ├── components/              [UI Layer]        │
│  └── .env.local              [Frontend Config] │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/REST
                  ↓
┌─────────────────────────────────────────────────┐
│  Backend (FastAPI) - Port 13370                 │
│  ├── /health                  [Health Check]    │
│  ├── /api/v1/memories        [Memory API]       │
│  ├── /api/v1/analytics       [Analytics API]    │
│  └── /api/v1/auth            [Auth API]         │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
┌──────────────────┐  ┌─────────────────┐
│  PostgreSQL      │  │  Redis          │
│  Port 5432       │  │  Port 6379      │
│  (nina-intel-db) │  │  (nina-cache)   │
└──────────────────┘  └─────────────────┘
```

### Technology Decisions
- **Backend Framework**: FastAPI (existing Nina Intelligence Stack)
- **Database**: PostgreSQL 15 + Apache AGE + pgvector (existing)
- **Cache**: Redis 7.4.5 (existing)
- **API Communication**: RESTful HTTP with JSON
- **Environment Management**: .env.local (frontend) + .env (backend)
- **Secret Management**: Vault integration for CI/CD

---

## 📦 Phase Breakdown

### Phase 1: Backend API Layer (Session 1 - 2 hours)

#### 1.1 Initialize Backend Service
**Goal**: Ensure FastAPI backend is running and accessible

**Tasks**:
- [ ] Verify `make nina-stack-up` starts all services
- [ ] Confirm backend health at http://localhost:13370/health
- [ ] Document backend startup in integration guide
- [ ] Create backend troubleshooting section

**Acceptance Criteria**:
- FastAPI backend responds to health checks
- All required endpoints documented in OpenAPI schema
- Backend logs show successful PostgreSQL + Redis connections

#### 1.2 Connect Database Layer
**Goal**: Establish PostgreSQL and Redis connectivity

**Tasks**:
- [ ] Verify `nina-intelligence-db` container running (port 5432)
- [ ] Verify `nina-intelligence-cache` container running (port 6379)
- [ ] Test database connection with `psql -U nina -d ninaivalaigal`
- [ ] Test Redis connection with `redis-cli PING`
- [ ] Run existing database migrations if needed

**Acceptance Criteria**:
- PostgreSQL connection pool active (visible in logs)
- Redis cache responding to PING commands
- Database schema matches expected state
- Connection strings properly configured

#### 1.3 Secure Environment Variables
**Goal**: Implement secure secret management

**Tasks**:
- [ ] Create `.env.local` template for frontend
- [ ] Document required environment variables:
  - `NEXT_PUBLIC_API_URL=http://localhost:13370`
  - `NEXT_PUBLIC_WS_URL=ws://localhost:13370`
- [ ] Ensure `.env` files are gitignored
- [ ] Add `.env.example` files for both frontend and backend
- [ ] Document secret management strategy for CI/CD

**Acceptance Criteria**:
- `.env.local` and `.env` files never committed to Git
- Example files provide clear configuration templates
- CI/CD uses secure secret injection (GitHub Secrets / Vault)

**Deliverables**:
- ✅ Backend service operational and health-checked
- ✅ Database connectivity verified
- ✅ Environment variables secured
- ✅ Configuration documentation complete

---

### Phase 2: Frontend-Backend Integration (Session 2 - 2 hours)

#### 2.1 Next.js API Routes
**Goal**: Create API proxy layer in Next.js

**File Structure**:
```
frontend-nextjs/app/api/
├── health/
│   └── route.ts          # Proxy to backend /health
├── memories/
│   └── route.ts          # Proxy to backend /api/v1/memories
├── analytics/
│   └── route.ts          # Proxy to backend /api/v1/analytics
└── auth/
    └── route.ts          # Proxy to backend /api/v1/auth
```

**Tasks**:
- [ ] Create `app/api/health/route.ts` for health checks
- [ ] Create `app/api/memories/route.ts` for memory operations
- [ ] Create `app/api/analytics/route.ts` for dashboard data
- [ ] Implement error handling and logging
- [ ] Add request/response type validation

**Example Implementation**:
```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/health`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Backend unavailable' },
      { status: 503 }
    );
  }
}
```

**Acceptance Criteria**:
- All API routes return proper HTTP status codes
- Error responses include helpful messages
- TypeScript types defined for all responses
- Logging captures request/response metadata

#### 2.2 Replace Mock Data with Live API Calls
**Goal**: Update components to fetch real data

**Tasks**:
- [ ] Update `DashboardPage` to fetch from `/api/analytics`
- [ ] Update `MemoryBrowser` to fetch from `/api/memories`
- [ ] Replace mock authentication with `/api/auth`
- [ ] Add loading states during API calls
- [ ] Implement error boundaries for API failures

**Example**:
```typescript
// app/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { StatsCard } from '@/components/dashboard/StatsCard';

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/analytics')
      .then(res => res.json())
      .then(data => {
        setAnalytics(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="grid gap-4">
      <StatsCard title="Total Memories" value={analytics.totalMemories} />
      {/* More components with real data */}
    </div>
  );
}
```

**Acceptance Criteria**:
- No hardcoded mock data in production components
- All API calls use proper error handling
- Loading states provide user feedback
- Data types validated with TypeScript

#### 2.3 Smoke Tests for Integration
**Goal**: Automated validation of full-stack connectivity

**Test File**: `frontend-nextjs/tests/integration/api-connectivity.test.ts`

**Tasks**:
- [ ] Test backend health endpoint reachability
- [ ] Test database query execution via API
- [ ] Test Redis cache operations via API
- [ ] Test authentication flow end-to-end
- [ ] Add smoke test to CI/CD pipeline

**Example Test**:
```typescript
// tests/integration/api-connectivity.test.ts
describe('API Connectivity', () => {
  it('should connect to backend health endpoint', async () => {
    const response = await fetch('http://localhost:13370/health');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  it('should fetch memories from database', async () => {
    const response = await fetch('http://localhost:13370/api/v1/memories');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data.memories)).toBe(true);
  });
});
```

**Acceptance Criteria**:
- All smoke tests pass in local development
- Tests run automatically in CI/CD
- Test failures block deployment
- Coverage includes happy path and error scenarios

**Deliverables**:
- ✅ Next.js API routes proxying to backend
- ✅ Components consuming real API data
- ✅ Smoke tests validating integration
- ✅ CI/CD pipeline updated

---

## 🎯 Success Metrics

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Response Time** | <200ms P95 | Backend logs + Lighthouse |
| **Database Query Time** | <50ms average | PostgreSQL query logs |
| **Cache Hit Rate** | >80% | Redis INFO stats |
| **Integration Test Pass Rate** | 100% | CI/CD pipeline |
| **Error Rate** | <1% | Application logs |

### Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Type Safety** | 100% (no `any`) | TypeScript compiler |
| **Test Coverage** | 80%+ | Jest coverage report |
| **API Documentation** | Complete | OpenAPI schema |
| **Environment Config** | Secure | No secrets in Git |

### Functional Metrics
| Metric | Target | Validation |
|--------|--------|------------|
| **Dashboard Loads Real Data** | Yes | Manual verification |
| **Memory CRUD Operations** | All working | Smoke tests |
| **Authentication Flow** | End-to-end | Integration tests |
| **Health Checks Passing** | All green | `/health` endpoint |

---

## 📁 Deliverables

### Code Artifacts
1. **Next.js API Routes** (`frontend-nextjs/app/api/`)
   - `health/route.ts`
   - `memories/route.ts`
   - `analytics/route.ts`
   - `auth/route.ts`

2. **Environment Configuration**
   - `frontend-nextjs/.env.example`
   - `frontend-nextjs/.env.local` (local only, gitignored)
   - Environment setup documentation

3. **Integration Tests** (`frontend-nextjs/tests/integration/`)
   - `api-connectivity.test.ts`
   - `database-operations.test.ts`
   - `authentication-flow.test.ts`

4. **Updated Components**
   - Dashboard components using live data
   - Memory browser with real API calls
   - Loading and error states

### Documentation
1. **Integration Guide** (`specs/105-backend-database-integration/INTEGRATION_GUIDE.md`)
   - Backend startup instructions
   - Database connection verification
   - Troubleshooting common issues

2. **API Documentation** (`specs/105-backend-database-integration/API_REFERENCE.md`)
   - Endpoint definitions
   - Request/response schemas
   - Authentication requirements

3. **Environment Setup** (`specs/105-backend-database-integration/ENVIRONMENT_SETUP.md`)
   - Required environment variables
   - Secret management strategy
   - Local development vs production config

### Testing
1. **Smoke Test Suite**
   - Backend health verification
   - Database connectivity tests
   - Redis cache tests
   - End-to-end API tests

2. **CI/CD Integration**
   - GitHub Actions workflow updated
   - Integration tests run on PR
   - Deployment blocked on test failures

---

## 🚦 Acceptance Criteria

### Must Have (Blocking)
- [ ] Backend service starts successfully with `make nina-stack-up`
- [ ] PostgreSQL and Redis connections verified
- [ ] All Next.js API routes functional
- [ ] Dashboard displays real data from backend
- [ ] Smoke tests pass in CI/CD
- [ ] No secrets committed to Git

### Should Have (Important)
- [ ] Error handling for all API failures
- [ ] Loading states during data fetches
- [ ] API response times meet P95 target (<200ms)
- [ ] Integration guide complete and tested
- [ ] TypeScript types for all API responses

### Nice to Have (Optional)
- [ ] Request/response logging for debugging
- [ ] API request retries with exponential backoff
- [ ] Caching strategy for frequently accessed data
- [ ] Performance monitoring dashboard

---

## 🔗 Dependencies

### Prerequisite SPECs
- **SPEC-103**: Next.js 15 Bootstrap (COMPLETE) - Provides frontend foundation
- **Nina Intelligence Stack**: Backend infrastructure must be operational

### Dependent SPECs (Unblocked by SPEC-105)
- **SPEC-104**: Post-Migration Quality Verification (can validate full stack)
- **SPEC-106**: E2E Tests with Playwright (requires live backend)
- **SPEC-107**: Profile/Settings Pages (needs auth API)
- **SPEC-108**: Auth & Security Integration (builds on auth endpoints)
- **SPEC-109**: Real-Time Features (requires WebSocket layer)

---

## 🎓 Technical Approach

### Best Practices
1. **API Routes as Proxy Layer**: Next.js API routes act as secure proxy, not duplication of logic
2. **Environment-Based Configuration**: Different configs for dev/staging/prod
3. **Graceful Degradation**: Frontend shows cached/stale data if backend unavailable
4. **Type Safety End-to-End**: TypeScript interfaces shared between frontend and backend
5. **Security First**: API keys never exposed to client, all backend calls server-side

### Error Handling Strategy
```typescript
// Centralized error handling
export async function fetchWithRetry(url: string, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
}
```

### Performance Optimization
- **API Response Caching**: Use Redis to cache frequent queries
- **Database Connection Pooling**: FastAPI manages connection pool
- **Query Optimization**: Ensure database indexes exist for common queries
- **Frontend Caching**: Use Next.js ISR (Incremental Static Regeneration) where appropriate

---

## 🐛 Troubleshooting Guide

### Common Issues

**Issue**: Frontend can't reach backend API
```bash
# Verify backend is running
curl http://localhost:13370/health

# Check backend logs
make nina-stack-logs

# Verify NEXT_PUBLIC_API_URL is set correctly
cat frontend-nextjs/.env.local
```

**Issue**: Database connection failures
```bash
# Verify PostgreSQL container running
container list | grep nina-intelligence-db

# Test database connection
container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "SELECT 1"

# Check backend database config
grep DATABASE_URL .env
```

**Issue**: Redis cache not working
```bash
# Verify Redis container running
container list | grep nina-intelligence-cache

# Test Redis connection
container exec nina-intelligence-cache redis-cli PING

# Check Redis stats
container exec nina-intelligence-cache redis-cli INFO
```

---

## 📊 Risk Assessment

### High Risk
- **Database Schema Mismatch**: Mitigation - Run migrations before integration testing
- **Environment Variable Leakage**: Mitigation - Strict .gitignore, pre-commit hooks
- **API Authentication Failures**: Mitigation - Comprehensive auth flow testing

### Medium Risk
- **Performance Degradation**: Mitigation - Load testing before production
- **CORS Issues**: Mitigation - Proper CORS configuration in FastAPI
- **Type Mismatch**: Mitigation - Shared TypeScript types

### Low Risk
- **Port Conflicts**: Mitigation - Document required ports, provide alternatives
- **Cache Invalidation**: Mitigation - Conservative TTL settings initially

---

## 🚀 Getting Started (Post-Approval)

### Session 1 Checklist
```bash
# 1. Start Nina Intelligence Stack
make nina-stack-up
make nina-stack-status  # Verify all services healthy

# 2. Verify Backend Health
curl http://localhost:13370/health
curl http://localhost:13370/docs  # OpenAPI schema

# 3. Test Database Connection
container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "SELECT version()"

# 4. Test Redis Connection
container exec nina-intelligence-cache redis-cli PING

# 5. Configure Frontend Environment
cd frontend-nextjs
cp .env.example .env.local
# Edit .env.local with correct API URL
```

### Session 2 Checklist
```bash
# 1. Create API Routes
mkdir -p frontend-nextjs/app/api/{health,memories,analytics,auth}
# Implement route handlers

# 2. Update Components
# Replace mock data with fetch() calls

# 3. Run Integration Tests
npm run test:integration

# 4. Manual Smoke Test
npm run dev
# Visit http://localhost:3000/dashboard
# Verify real data loads
```

---

## 📈 Timeline

### Session 1 (2 hours): Backend & Database Layer
- **0:00-0:30**: Verify Nina Intelligence Stack operational
- **0:30-1:00**: Database and Redis connectivity validation
- **1:00-1:30**: Environment variable setup and security
- **1:30-2:00**: Backend API endpoint documentation and testing

### Session 2 (2 hours): Frontend Integration
- **0:00-0:45**: Create Next.js API routes (proxy layer)
- **0:45-1:30**: Update components to use live data
- **1:30-1:45**: Write integration smoke tests
- **1:45-2:00**: CI/CD pipeline updates and final validation

**Total Duration**: 4 hours over 2 sessions

---

## ✅ Definition of Done

### Technical Completion
- [ ] Backend API serving data on all required endpoints
- [ ] PostgreSQL and Redis connected and operational
- [ ] Next.js API routes implemented and tested
- [ ] Frontend components consuming real backend data
- [ ] Integration tests passing (100% pass rate)
- [ ] No hardcoded mock data in production code paths

### Documentation Completion
- [ ] Integration guide complete with troubleshooting
- [ ] API reference documentation updated
- [ ] Environment setup guide written
- [ ] README.md updated with integration instructions

### Quality Gates
- [ ] All smoke tests green in CI/CD
- [ ] TypeScript compilation with no errors
- [ ] ESLint passes with <20 issues
- [ ] Test coverage >80%
- [ ] Security scan clean (no exposed secrets)

### Deployment Readiness
- [ ] `.env.example` files in place
- [ ] CI/CD secrets configured
- [ ] Health checks responding
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

---

## 🎯 Strategic Impact

### Business Value
- **End-to-End Functionality**: Users can now perform real operations, not just view mock data
- **Production Readiness**: Full stack operational, ready for beta testing
- **Data Persistence**: User actions stored in database, providing genuine value
- **Performance Baseline**: Real metrics for optimization in SPEC-106+

### Technical Value
- **Integration Patterns Established**: Reusable approach for future API integrations
- **Type Safety**: Shared contracts between frontend and backend
- **Observability**: Health checks and smoke tests provide system visibility
- **Security Foundation**: Proper secret management from day one

### Team Value
- **Clear Ownership**: Frontend team owns API routes, backend team owns FastAPI
- **Parallel Development**: Teams can work independently with API contracts
- **Rapid Iteration**: Changes to backend immediately reflected in frontend
- **Quality Confidence**: Automated tests catch integration regressions

---

## 📞 Support & Resources

### Documentation
- **Nina Intelligence Stack Guide**: `docs/NINA_INTELLIGENCE_STACK_COMPLETE.md`
- **Backend API Docs**: http://localhost:13370/docs (FastAPI Swagger UI)
- **Frontend README**: `frontend-nextjs/README.md`

### Quick Commands
```bash
# Start full stack
make nina-stack-up

# Check status
make nina-stack-status

# View logs
make nina-stack-logs

# Run smoke tests
cd frontend-nextjs && npm run test:integration

# Build frontend
cd frontend-nextjs && npm run build
```

### Troubleshooting Resources
- **GitHub Issues**: Tag with `spec-105` and `integration`
- **Stack Overflow**: `ninaivalaigal` + `nextjs` + `fastapi`
- **Internal Wiki**: Integration troubleshooting guide

---

## 🏁 Next Steps After SPEC-105

Once SPEC-105 is complete, the following SPECs become unblocked:

1. **SPEC-104**: Post-Migration Quality Verification
   - Full-stack Lighthouse audits
   - End-to-end performance benchmarks
   - Complete migration trilogy report

2. **SPEC-106**: E2E Tests with Playwright
   - User journey testing with real data
   - Cross-browser compatibility validation

3. **SPEC-107**: Profile/Settings Pages
   - User preferences stored in database
   - Real-time updates via WebSocket

4. **SPEC-108**: Auth & Security Integration
   - JWT token management
   - Session persistence
   - Role-based access control

5. **SPEC-109**: Real-Time Features
   - WebSocket layer for live updates
   - Collaborative editing

---

## 📋 Appendix

### A. API Endpoint Reference

#### Health Check
```
GET /health
Response: { "status": "healthy", "database": "connected", "redis": "connected" }
```

#### Memories API
```
GET /api/v1/memories
Response: { "memories": [...], "total": 42 }

POST /api/v1/memories
Body: { "content": "...", "context": "..." }
Response: { "id": "uuid", "created_at": "..." }
```

#### Analytics API
```
GET /api/v1/analytics/dashboard
Response: {
  "totalMemories": 1234,
  "activeUsers": 56,
  "storageUsed": "1.2GB",
  "chartData": [...]
}
```

### B. Environment Variables Reference

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:13370
NEXT_PUBLIC_WS_URL=ws://localhost:13370
NEXT_PUBLIC_ENV=development
```

#### Backend (.env)
```bash
DATABASE_URL=postgresql://nina:password@localhost:5432/ninaivalaigal  # pragma: allowlist secret
REDIS_URL=redis://localhost:6379
SECRET_KEY=<generated-secret>
ENVIRONMENT=development
```

### C. Testing Strategy

#### Unit Tests
- Test individual API route handlers
- Mock fetch calls to backend
- Validate error handling

#### Integration Tests
- Test full request/response cycle
- Verify database operations
- Validate cache behavior

#### Smoke Tests
- Quick validation of critical paths
- Run before every deployment
- Block deployment on failure

---

**Document Version**: 1.0
**Created**: October 10, 2025
**Status**: Ready for Review
**Next Action**: Team review and approval for implementation
