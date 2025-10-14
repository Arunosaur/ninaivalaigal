# SPEC-105: Backend Integration - Quick Start

**Duration**: 4 hours (2 sessions)
**Objective**: Replace mock data with live API calls to Nina Intelligence Stack
**Outcome**: Full-stack Ninaivalaigal operational end-to-end

---

## 🎯 What This SPEC Does

Bridges the frontend baseline (SPEC-103) with the Nina Intelligence Stack:

```
Frontend (Next.js 15) → API Routes → Backend (FastAPI) → Database (PostgreSQL + Redis)
```

**Before**: Dashboard shows mock data, no persistence
**After**: Dashboard shows real data, full CRUD operations, authentication working

---

## 📋 Phase Breakdown

### Session 1: Backend & Database Layer (2 hours)

**Checklist**:
```bash
✅ Start Nina Intelligence Stack
   make nina-stack-up

✅ Verify backend health
   curl http://localhost:13370/health

✅ Test database connection
   container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "SELECT 1"

✅ Test Redis cache
   container exec nina-intelligence-cache redis-cli PING

✅ Configure environment variables
   cd frontend-nextjs
   cp .env.example .env.local
   # Edit NEXT_PUBLIC_API_URL=http://localhost:13370
```

**Deliverables**:
- Backend operational and health-checked
- Database connectivity verified
- Environment variables secured
- Configuration docs complete

---

### Session 2: Frontend Integration (2 hours)

**Checklist**:
```bash
✅ Create Next.js API routes
   mkdir -p frontend-nextjs/app/api/{health,memories,analytics,auth}
   # Implement proxy handlers

✅ Update components with live data
   # Replace mock data in DashboardPage
   # Replace mock data in MemoryBrowser

✅ Write integration tests
   # Create tests/integration/api-connectivity.test.ts

✅ Run smoke tests
   npm run test:integration

✅ Manual validation
   npm run dev
   # Visit http://localhost:3000/dashboard
   # Verify real data loads
```

**Deliverables**:
- Next.js API routes implemented
- Components consuming real data
- Integration tests passing
- CI/CD pipeline updated

---

## 🚀 Key Files to Create

### 1. Next.js API Routes

**`frontend-nextjs/app/api/health/route.ts`**
```typescript
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

### 2. Environment Configuration

**`frontend-nextjs/.env.example`**
```bash
NEXT_PUBLIC_API_URL=http://localhost:13370
NEXT_PUBLIC_WS_URL=ws://localhost:13370
NEXT_PUBLIC_ENV=development
```

### 3. Integration Test

**`frontend-nextjs/tests/integration/api-connectivity.test.ts`**
```typescript
describe('API Connectivity', () => {
  it('should connect to backend health endpoint', async () => {
    const response = await fetch('http://localhost:13370/health');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
});
```

---

## ✅ Success Criteria

### Must Have
- [ ] Backend service starts with `make nina-stack-up`
- [ ] PostgreSQL and Redis connected
- [ ] All Next.js API routes functional
- [ ] Dashboard displays real backend data
- [ ] Smoke tests pass in CI/CD
- [ ] No secrets in Git

### Quality Gates
- [ ] API response times &lt;200ms P95
- [ ] Integration tests 100% pass rate
- [ ] TypeScript compiles with no errors
- [ ] ESLint passes with &lt;20 issues

---

## 🐛 Troubleshooting

### Backend Not Reachable
```bash
# Check backend is running
curl http://localhost:13370/health

# View backend logs
make nina-stack-logs

# Restart stack
make nina-stack-down
make nina-stack-up
```

### Database Connection Failed
```bash
# Verify database container
container list | grep nina-intelligence-db

# Test direct connection
container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "SELECT version()"
```

### Redis Not Responding
```bash
# Verify Redis container
container list | grep nina-intelligence-cache

# Test Redis
container exec nina-intelligence-cache redis-cli PING
```

---

## 📊 Expected Outcomes

### Technical
- ✅ Full-stack integration operational
- ✅ Real data flowing frontend ↔ backend ↔ database
- ✅ API response times meeting targets
- ✅ Integration tests providing confidence

### Business
- ✅ Users can perform real operations (not just view mock data)
- ✅ Data persists across sessions
- ✅ Authentication fully functional
- ✅ Ready for beta testing

---

## 🎯 What's Next (After SPEC-105)

Once integrated, these SPECs become unblocked:

1. **SPEC-104**: Quality verification with full-stack metrics
2. **SPEC-106**: E2E tests with Playwright using real data
3. **SPEC-107**: Profile/settings pages with database persistence
4. **SPEC-108**: Auth & security with JWT tokens
5. **SPEC-109**: Real-time features with WebSocket

---

## 📞 Quick Commands

```bash
# Start everything
make nina-stack-up

# Check status
make nina-stack-status

# Run frontend
cd frontend-nextjs && npm run dev

# Run tests
cd frontend-nextjs && npm run test:integration

# View logs
make nina-stack-logs

# Stop everything
make nina-stack-down
```

---

**Ready to Start?** Review the full SPEC at `specs/105-backend-database-integration/README.md`

**Questions?** Check the troubleshooting guide or create a GitHub issue tagged with `spec-105`
