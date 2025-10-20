# Taiga Task Tracking - Gap Analysis Items

**Date:** October 20, 2025
**Status:** All Critical Items Tracked ✅
**Source:** SPEC_099_100_GAP_ANALYSIS_OCT20.md

---

## 🔴 P0 - Critical Blockers

### Task #85: Fix PgBouncer Bypass in Memory Service
**Status:** New (In Progress)
**Effort:** 2-3 weeks
**Priority:** P0 - Do this FIRST

**Problem:** Memory Service bypasses PgBouncer, breaking connection pooling model

**Solution:** Switch PgBouncer to session mode to support prepared statements

**Action Items:**
- Update config/pgbouncer/pgbouncer.ini: `pool_mode = session`
- Change Memory Service DATABASE_URL to port 6432 (PgBouncer)
- Test prepared statements work through PgBouncer
- Verify connection pooling operational

**Reference:** docs/TASK_85_PGBOUNCER_PREPARED_STATEMENTS.md

---

### Task #79: Shared Contracts Layer (SPEC-100 Phase 0)
**Status:** Done → **NEEDS REOPENING** (incorrectly marked complete)
**Effort:** 2-3 weeks
**Priority:** P0 - BLOCKER

**Problem:** Without `shared/contracts/`, service decomposition is blocked

**Current State:**
- ❌ No centralized OpenAPI models
- ❌ No JSON schema validation
- ❌ No automated contract diff checking

**Action Items:**
- Create `shared/contracts/` directory structure
- Extract Pydantic models from Core API
- Generate OpenAPI specs from FastAPI
- Set up CI validation for contract drift
- Add pre-commit hooks

**Blocks:** Task #83 (API Gateway), Task #88 (Core API decomposition)

**Reference:** SPEC-100: API Container Modularization (Phase 0)

---

### Task #83: Deploy API Gateway with Path Routing
**Status:** Done → **NEEDS REOPENING** (incorrectly marked complete)
**Effort:** 2 weeks
**Priority:** P0

**Problem:** Services exist but no proper ingress routing

**Current State:**
- ✅ gRPC Gateway exists (Task #71) - different purpose
- ❌ No HTTP path-based routing (`/auth` → Core API, `/memory` → Memory Service)
- ❌ No single entry point

**Action Items:**
- Deploy Traefik or FastAPI Gateway
- Configure path-based routing for all services
- Add JWT authentication middleware
- Add rate limiting and CORS
- Test end-to-end routing

**Depends On:** Task #79 (should have contracts first)

**Reference:** SPEC-100 Section 4.1 (Gateway Layer)

---

## 🟡 P1 - High Priority

### Task #86: Performance Benchmarking CI
**Status:** New (Created Oct 20, 2025)
**Effort:** 2-3 weeks
**Priority:** P1

**Problem:** SPEC-099 ROI claims (50-90% latency reduction) are unvalidated

**Current State:**
- ✅ Load testing tool built (Task #72)
- ❌ No comprehensive benchmarks run
- ❌ No Python vs Rust comparison
- ❌ No cost analysis

**Action Items:**
- Use load tester for comprehensive benchmarks
- Benchmark top 3 GraphOps queries:
  - User memory graph traversal
  - Context similarity search
  - Team collaboration graph
- Compare Python vs Rust metrics
- Measure throughput improvements
- Generate ROI validation report

**Success Criteria:**
- Validate latency reduction (target: 50-90%)
- Validate throughput improvement (target: 6-10x)
- Estimate infrastructure cost savings (target: 30-60%)

**Reference:** SPEC-099 Section 1 (ROI Matrix)

---

### Task #87: Schema Drift Prevention CI
**Status:** New (Created Oct 20, 2025)
**Effort:** 1 week
**Priority:** P1

**Problem:** No automated validation prevents API contract breaking changes

**Action Items:**
- Create `scripts/check-contract-drift.py`
- Add GitHub workflow for OpenAPI validation
- Detect breaking changes (removed endpoints, schema changes)
- Add pre-commit hook for local validation
- Document contract evolution process

**Depends On:** Task #79 (contracts must exist first)

**Reference:** SPEC-099 Section 6 (Risk Mitigation #1)

---

### Task #88: Core API Decomposition
**Status:** New (Created Oct 20, 2025)
**Effort:** 4-6 weeks
**Priority:** P1

**Problem:** Monolithic API (49K lines, 54 routers) creates coupling and deployment risks

**Target Decomposition:**
1. **Core API Service** - Auth, Users, Teams, RBAC
2. **Memory Service** - Context, Recording (already exists in Rust)
3. **Graph/AI Service** - Intelligence, Feedback (GraphOps exists)
4. **Business Service** - Billing, Usage, Analytics
5. **Admin/Vendor Service** - Admin + Vendor portals

**Action Items:**
- Extract auth_api, users_api, teams_api, rbac_api into Core API service
- Set up independent CI/CD workflows
- Configure API Gateway routing
- Migrate to independent containers

**Depends On:** Task #79 (contracts), Task #83 (gateway)

**Reference:** SPEC-100: API Container Modularization

---

## 🟢 P2 - Future Work (Q2-Q3 2026)

### Event Bus Integration
**Status:** Not Yet Tracked
**Effort:** 2-3 weeks
**Priority:** P2 (Q2 2026)

**Description:** Redis Streams or NATS for async service communication

**Action:** Create task when Q1 2026 decomposition complete

---

### Service Mesh Deployment
**Status:** Not Yet Tracked
**Effort:** 4-6 weeks
**Priority:** P2 (Q3 2026)

**Description:** Linkerd or Istio for mTLS and intelligent routing

**Action:** Create task when contract testing and CI resilience proven

---

## ✅ Completed Foundation Work

### Task #77: CLI Tools Distribution
**Status:** Complete ✅
**Date:** October 20, 2025

Unified CLI tools ready for distribution with:
- Multi-platform support (Linux, macOS, Windows)
- Health check commands
- GraphOps gRPC-only documentation
- Complete checksums and validation

**Reference:** docs/TASK_77_DISTRIBUTION_CHECKLIST.md

---

### Task #84: OpenTelemetry Distributed Tracing
**Status:** Complete ✅
**Date:** October 20, 2025

Full distributed tracing operational:
- 6 services instrumented (Python, Rust, Go)
- Jaeger v1.51 on Apple Container CLI
- W3C Trace Context propagation
- OTLP gRPC endpoint: localhost:4317

**Reference:** docs/TASK_84_COMPLETE.md

---

### Task #71: gRPC Gateway
**Status:** Complete ✅

REST ↔ gRPC translation operational (different from Task #83 HTTP path routing)

---

### Task #72: Load Testing Tools
**Status:** Complete ✅

Concurrent load testing tool ready for Task #86 benchmarking

---

## 📊 Summary Dashboard

### By Priority

| Priority | Tasks | Complete | In Progress | Not Started |
|----------|-------|----------|-------------|-------------|
| 🔴 P0 | 3 | 0 | 1 (#85) | 2 (#79, #83) |
| 🟡 P1 | 3 | 0 | 0 | 3 (#86, #87, #88) |
| 🟢 P2 | 2 | 0 | 0 | 2 (future) |

### By Status

| Status | Count | Tasks |
|--------|-------|-------|
| ✅ Complete | 4 | #71, #72, #77, #84 |
| 🔄 In Progress | 1 | #85 |
| 📋 Ready to Start | 5 | #79, #83, #86, #87, #88 |
| 🔮 Future | 2 | Event Bus, Service Mesh |

---

## 🎯 Recommended Execution Order

### Q4 2025 (Now - Dec 2025)

1. **Task #85** - Fix PgBouncer (P0, 2-3 weeks)
   - Architectural blocker, do this FIRST

2. **Task #77** - Distribute CLI Tools (P0, 1 day)
   - Upload to distribution, notify Ops/Developer B

3. **Task #86** - Performance Benchmarks (P1, 2-3 weeks)
   - Validate ROI claims while services are fresh

### Q1 2026 (Jan - Mar 2026)

4. **Task #79** - Shared Contracts Layer (P0, 2-3 weeks)
   - Prerequisite for everything else

5. **Task #87** - Schema Drift CI (P1, 1 week)
   - Implement immediately after #79

6. **Task #83** - API Gateway (P0, 2 weeks)
   - Deploy Traefik with contracts in place

7. **Task #88** - Core API Decomposition (P1, 4-6 weeks)
   - Break monolith with gateway ready

### Q2 2026 (Apr - Jun 2026)

8. **Event Bus** - Redis Streams/NATS (P2, 2-3 weeks)
   - Add after decomposition proven

### Q3 2026 (Jul - Sep 2026)

9. **Service Mesh** - Linkerd/Istio (P2, 4-6 weeks)
   - Add when contract testing mature

---

## 📝 Notes

### Tasks Needing Attention

**Task #79 & #83:** Incorrectly marked "Done" in Taiga. These need to be reopened and reprioritized as P0. Got 403 errors trying to update them programmatically - may need manual update.

**Task #85:** Successfully updated with full description. This is the most critical blocker.

**New Tasks Created:** #86 (Performance), #87 (Schema Drift), #88 (Core API Decomp) all properly documented and tracked.

---

## 🔗 References

### Key Documents
- **Gap Analysis:** docs/SPEC_099_100_GAP_ANALYSIS_OCT20.md
- **SPEC-099:** specs/099-rust-migration-strategy/README.md
- **SPEC-100:** specs/100-api-container-modularization/README.md
- **Task #77 Distribution:** docs/TASK_77_DISTRIBUTION_CHECKLIST.md
- **Task #84 Complete:** docs/TASK_84_COMPLETE.md

### Task URLs
- Taiga: http://localhost:9000 (or your Taiga URL)
- GitHub: Repository task tracking board

---

**Last Updated:** October 20, 2025
**Next Review:** Weekly during Q4 2025, then bi-weekly during Q1 2026
**Owner:** Architecture Team
