# SPEC-131: Memory Router Rationalization

## 📌 Overview
Strategic selective migration of Python memory routers to Rust based on **performance profiles and business logic complexity**, not blanket decomposition. This SPEC defines the decision framework, migration priorities, and target architecture for the Rust/Python split.

---

## 🎯 Goals
- **Rationalize** memory router placement: Rust for performance, Python for complexity
- **Eliminate redundancy** while preserving unique features
- **Maximize performance** on hot paths (bulk ops, queues)
- **Maintain flexibility** for complex business logic in Python
- **Establish clear migration criteria** for future decisions

**Core Principle:**
> "Only migrate to Rust when the performance/throughput justifies the complexity."

---

## 🏗️ Current State Analysis

### Python Memory Routers (Post US #88)
After removing the redundant `memory_api.py`, we have **5 Advanced Memory + 4 Operations routers**:

**Advanced Memory Routers (5):**
| Router | LOC | Complexity | Performance Profile | SPEC |
|--------|-----|------------|---------------------|------|
| `memory_acl_api.py` | ~250 | High (RBAC logic) | Low-frequency | SPEC-043 |
| `memory_drift_api.py` | ~200 | High (analytics) | Low-frequency | N/A |
| `memory_health_api.py` | ~150 | Medium | Medium-frequency | SPEC-071 |
| `memory_injection_api.py` | ~300 | Medium (bulk ops) | **HIGH-frequency** | SPEC-036 |
| `memory_suggestions_api.py` | ~250 | High (NLP/graph) | Medium-frequency | SPEC-041 |

**Operations Routers (4):**
| Router | LOC | Complexity | Performance Profile | SPEC |
|--------|-----|------------|---------------------|------|
| `queue_api.py` | ~200 | Medium | **HIGH-frequency** | N/A |
| `preload_api.py` | ~150 | Low | Infrequent batch | SPEC-038 |
| `health` (core API) | ~100 | Low | Status ping | N/A |
| `metrics` | ~180 | Medium | Depends on volume | N/A |

### Rust Services (Existing)
- **Memory Service** (port 13393) - Basic CRUD, Redis caching, pgvector
- **GraphOps** (port 13398) - Graph operations, Apache AGE

---

## 🧠 Decision Framework

### Strategic Migration Rule
```
Migrate to Rust when:
✅ The route is on the HOT PATH (high-frequency, critical latency)
✅ It processes HIGH-FREQUENCY or BULK OPERATIONS
✅ You can REUSE INTERNAL RUST LOGIC (e.g., shared gRPC models)
✅ You need PRECISE MEMORY or CONCURRENCY CONTROL

Keep in Python when:
❌ Logic is CONDITIONAL/ORCHESTRATED (not compute-intensive)
❌ It's ADMIN-ONLY or USED INFREQUENTLY
❌ It's HIGHLY COUPLED to Python-only tooling (Alembic, Pydantic)
❌ The complexity doesn't justify the Rust investment
```

---

## 🎯 Router Analysis & Decisions

### ✅ **IMMEDIATE MIGRATION (High Priority)**

#### **Priority 1: `injection_api.py` → Rust**
**Decision:** ✅ **MIGRATE**

**Rationale:**
- **Performance:** HIGH-throughput bulk memory injection (procedural pipeline)
- **Use Case:** Bulk processing of memories in pipelines
- **Hot Path:** Yes - memory ingestion critical path
- **Complexity:** Medium (batching, pipeline operations)
- **Reuse:** Can leverage existing Rust Memory Service gRPC models
- **Impact:** Significant performance gain for bulk operations

**Timeline:** 2-3 weeks
**Dependencies:** Rust Memory Service gRPC proto definitions
**Risk:** Low (well-defined batch operations)

---

#### **Priority 2: `queue_api.py` → Rust**
**Decision:** ✅ **MIGRATE**

**Rationale:**
- **Performance:** HIGH - controls memory ingestion throughput
- **Use Case:** Queue management, throughput control, real-time processing
- **Hot Path:** Yes - on the memory ingestion critical path
- **Complexity:** Medium (queue control, async operations)
- **Reuse:** Can leverage Rust async primitives (tokio channels)
- **Impact:** Improved queue control, real-time responsiveness

**Timeline:** 2 weeks
**Dependencies:** None (standalone queue logic)
**Risk:** Low (clear queue management semantics)

---

### 🔶 **CONDITIONAL MIGRATION (Evaluate First)**

#### **`health_api.py` - Memory Health Monitoring**
**Decision:** 🔶 **CONDITIONAL** - Check Rust Memory Service first

**Rationale:**
- **Performance:** Could be high-frequency in production monitoring
- **Current Status:** ⚠️ Likely already exposed in Rust Memory Service
- **Decision:** Migrate ONLY IF not already part of Rust service
- **Best Practice:** Health endpoints should be per-service, not centralized

**Action:**
1. First check Rust Memory Service for `/health` endpoint
2. If missing, add to Rust service
3. If exists, deprecate Python version

**Timeline:** 1 week (if needed)
**Dependencies:** Rust Memory Service
**Risk:** Low (simple health check logic)

---

#### **`suggestions_api.py` - AI/Heuristic Suggestions**
**Decision:** 🔶 **CONDITIONAL** - Profile first, migrate only if bottleneck

**Rationale:**
- **Performance:** Depends on algorithm complexity (NLP, graph heuristics)
- **Current Status:** Using Python NLP libraries (spaCy, etc.)
- **Complexity:** HIGH - complex algorithms, NLP integration
- **Python Advantage:** Superior NLP ecosystem
- **Decision:** Migrate ONLY IF latency becomes critical bottleneck

**Action:**
1. Profile performance in production
2. Identify if NLP computation is bottleneck
3. Consider partial migration (keep Python for NLP, Rust for serving)

**Timeline:** 3 weeks (complex logic, NLP integration)
**Dependencies:** Rust NLP libraries (if available)
**Risk:** High (complex logic, potential accuracy issues)

---

#### **`metrics` - Metrics Aggregation**
**Decision:** 🔶 **CONDITIONAL** - Depends on metrics volume

**Rationale:**
- **Performance:** Depends on volume (streaming dashboards vs batch reports)
- **Use Case:** Aggregates and reports service metrics
- **Complexity:** Medium (aggregation logic)
- **Decision:** Migrate IF metrics volume is high (e.g., real-time streaming)

**Action:**
1. Monitor metrics query patterns
2. Identify if high-volume streaming is needed
3. Migrate if dashboard refresh rate < 1s required

**Timeline:** 2 weeks
**Dependencies:** Rust metrics aggregation library
**Risk:** Medium (aggregation logic complexity)

---

### ❌ **KEEP IN PYTHON (No Migration)**

#### **`acl_api.py` - Access Control (SPEC-043)**
**Decision:** ❌ **KEEP IN PYTHON**

**Rationale:**
- **Complexity:** HIGH - RBAC logic, role hierarchy, permission checks
- **Performance:** Mostly business logic, NOT compute-intensive
- **Dependencies:** Heavy integration with auth system, Pydantic validations
- **Python Advantage:** Readability for complex conditional logic
- **Decision:** Pure orchestration logic - Python is appropriate

**Why Not Rust:**
- Complex conditional logic better suited for Python readability
- Auth integration tightly coupled to Python ecosystem
- Not on hot path (infrequent permission checks)

---

#### **`drift_api.py` - Schema Drift Detection**
**Decision:** ❌ **KEEP IN PYTHON**

**Rationale:**
- **Complexity:** HIGH - schema analysis, diff computation, internal API calls
- **Performance:** Infrequent (analysis + internal API, not compute-bound)
- **Dependencies:** Python schema inspection tools, Alembic integration
- **Python Advantage:** Leverages Python ecosystem (Alembic, Pydantic)
- **Decision:** Keep in Python for tooling integration

**Why Not Rust:**
- Heavily dependent on Python tooling (Alembic)
- Infrequent use (drift detection is periodic, not real-time)
- No performance benefit from Rust

---

#### **`preload_api.py` - Template/Token Preloading (SPEC-038)**
**Decision:** ❌ **KEEP IN PYTHON**

**Rationale:**
- **Complexity:** LOW - load templates/tokens into memory
- **Performance:** Infrequent batch operation (admin-only)
- **Use Case:** Admin configuration, not user-facing
- **Decision:** Not worth migration effort

**Why Not Rust:**
- Admin-only, infrequent use
- Simple logic, no performance gain
- Low ROI for migration

---

#### **`health` (Core API General) - Status Ping**
**Decision:** ❌ **KEEP IN PYTHON**

**Rationale:**
- **Complexity:** LOW - just a status endpoint
- **Performance:** Low impact (simple ping)
- **Best Practice:** Every service should have its own health endpoint
- **Decision:** Keep per-service health in Python Core API

**Why Not Rust:**
- Simple endpoint, no performance benefit
- Part of Core API service boundaries

---

## 🏛️ Target Architecture

### Post-Rationalization Service Split

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT / UI                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / NGINX                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   PYTHON CORE API         │   │   RUST SERVICES               │
│   (Business Logic)        │   │   (Performance-Critical)      │
│   Port: 13390             │   │                               │
├───────────────────────────┤   ├───────────────────────────────┤
│                           │   │                               │
│ 🔐 Auth & Users (5)       │   │ ⚡ Memory Service (13393)     │
│   • signup, users, rbac   │   │   • CRUD (remember/recall)    │
│   • tokens, sessions      │   │   • Redis caching             │
│                           │   │   • pgvector embeddings       │
│ 👥 Teams & Orgs (4)       │   │   • ✅ NEW: Injection API     │
│   • teams, organizations  │   │   • ✅ NEW: Queue API         │
│   • invitations, keys     │   │                               │
│                           │   │ 📊 GraphOps (13398)           │
│ 🧠 Advanced Memory (3)    │   │   • Graph operations          │
│   • ✅ ACL (RBAC)         │   │   • Apache AGE                │
│   • ✅ Drift Detection    │   │   • Cypher queries            │
│   • 🔶 Suggestions (AI)   │   │                               │
│                           │   │ 🔄 Health & Metrics (Future)  │
│ ⚙️  Operations (2)        │   │   • 🔶 Health API (if not     │
│   • ✅ Preload            │   │       in Memory Service)      │
│   • ✅ Health (Core API)  │   │   • 🔶 Metrics (if streaming) │
│                           │   │                               │
└───────────────────────────┘   └───────────────────────────────┘
                │                               │
                │                               │
                └───────────┬───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   PostgreSQL + Redis  │
                │   (Shared Data Layer) │
                └───────────────────────┘
```

### Service Boundaries After Rationalization

**Python Core API (Business Logic):**
- ✅ Authentication & Authorization (5 routers)
- ✅ Team & Organization Management (4 routers)
- ✅ Advanced Memory Features (3 routers):
  - `memory_acl_api` - RBAC for memories
  - `memory_drift_api` - Schema drift detection
  - `memory_suggestions_api` - AI-powered suggestions
- ✅ Operations (2 routers):
  - `preload_api` - Admin template loading
  - `health` - Core API health check

**Rust Memory Service (Performance-Critical):**
- ✅ Basic CRUD (`/remember`, `/recall`, `/memories`)
- ✅ Redis caching layer
- ✅ pgvector embeddings
- ✅ **NEW:** Bulk injection API (migrated from Python)
- ✅ **NEW:** Queue management API (migrated from Python)
- 🔶 **CONDITIONAL:** Health API (if not already present)

**Rust GraphOps (Graph Intelligence):**
- ✅ Graph operations (AGE)
- ✅ Cypher queries
- ✅ Relationship traversal

**Future Rust Services (Conditional):**
- 🔶 Metrics Service (if high-volume streaming)
- 🔶 Suggestions Service (if AI latency critical)

---

## 📋 Migration Plan

### Phase 1: Immediate Migrations (3-5 weeks)

**Week 1-2: Queue API → Rust**
- [ ] Design Rust queue management API
- [ ] Implement queue control logic in Rust Memory Service
- [ ] Add gRPC endpoints for queue operations
- [ ] Create HTTP gateway endpoints
- [ ] Test throughput and latency
- [ ] Migrate Python clients to Rust endpoints
- [ ] Deprecate Python `queue_api.py`

**Week 3-5: Injection API → Rust**
- [ ] Design bulk injection API in Rust
- [ ] Implement batch processing logic
- [ ] Add pipeline support (streaming ingestion)
- [ ] Create gRPC + HTTP endpoints
- [ ] Performance test bulk operations
- [ ] Migrate Python clients
- [ ] Deprecate Python `injection_api.py`

### Phase 2: Conditional Evaluations (2-4 weeks)

**Week 1: Health API Audit**
- [ ] Check if Rust Memory Service has `/health` endpoint
- [ ] If missing, add to Rust service (1 day)
- [ ] If exists, deprecate Python version
- [ ] Update monitoring to use Rust health endpoint

**Week 2: Suggestions API Profiling**
- [ ] Profile `suggestions_api` in production
- [ ] Identify NLP computation bottlenecks
- [ ] Measure current P50/P99 latency
- [ ] Decision: Migrate if P99 > 200ms

**Week 3: Metrics API Evaluation**
- [ ] Monitor metrics query patterns
- [ ] Identify dashboard refresh requirements
- [ ] Measure current aggregation performance
- [ ] Decision: Migrate if real-time streaming needed

**Week 4: Final Decisions**
- [ ] Document conditional migration decisions
- [ ] Update architecture diagram
- [ ] Create follow-up tasks if migrations needed

### Phase 3: Cleanup & Documentation (1 week)

- [ ] Archive deprecated Python routers
- [ ] Update API documentation
- [ ] Update architecture diagrams
- [ ] Create performance benchmarks
- [ ] Document Rust/Python split rationale

---

## ✅ Acceptance Criteria

### Performance Criteria
- [ ] Queue API latency: P99 < 10ms (Rust)
- [ ] Injection API throughput: >1000 memories/sec (Rust)
- [ ] No regression on existing Python routers
- [ ] Memory service uptime: >99.9%

### Functional Criteria
- [ ] All existing Python clients work seamlessly
- [ ] No breaking changes to API contracts
- [ ] Backward compatibility maintained
- [ ] Health checks pass for all services

### Quality Criteria
- [ ] Unit test coverage >80% for new Rust code
- [ ] Integration tests for migrated endpoints
- [ ] Performance benchmarks documented
- [ ] Architecture diagrams updated

---

## 🔗 Dependencies

**Existing SPECs:**
- SPEC-043 (Memory ACL) - ✅ Complete
- SPEC-038 (Memory Preloading) - ✅ Complete
- SPEC-041 (Intelligent Related Memory) - ✅ Complete
- SPEC-071 (Auto-healing Health System) - ✅ Complete
- SPEC-036 (Memory Injection Rules) - 🔄 Migrating to Rust

**Infrastructure:**
- Rust Memory Service (port 13393) - ✅ Operational
- GraphOps (port 13398) - ✅ Operational
- PostgreSQL + Redis - ✅ Operational
- gRPC Gateway - ✅ Operational

---

## 🧪 Testing Plan

### Unit Tests
- Rust queue management logic
- Rust bulk injection logic
- Python router deprecation (no regressions)

### Integration Tests
- End-to-end memory ingestion (Python → Rust → DB)
- Queue control operations (enqueue, dequeue, pause, resume)
- Bulk injection pipeline (batch processing)

### Performance Tests
- Queue API: latency, throughput
- Injection API: bulk operation performance
- Load testing: concurrent operations

### Regression Tests
- Existing Python routers still work
- No breaking changes to API contracts

---

## 📈 Success Metrics

**Performance Gains:**
- Queue API latency: 80% reduction (Python ~50ms → Rust ~10ms)
- Injection API throughput: 5x improvement (200 → 1000 memories/sec)
- Memory service resource usage: 30% reduction (Rust efficiency)

**Code Quality:**
- LOC reduction: ~500 lines (deprecate Python routers)
- Service separation: Clear Rust/Python boundaries
- Maintainability: Easier to reason about service responsibilities

**Business Impact:**
- Improved user experience (faster memory operations)
- Reduced infrastructure costs (more efficient Rust services)
- Better scalability (Rust concurrency model)

---

## 🗓️ Implementation Timeline

| Phase | Task | Duration | Owner |
|-------|------|----------|-------|
| **Phase 1** | Queue API → Rust | 2 weeks | Rust Team |
| **Phase 1** | Injection API → Rust | 3 weeks | Rust Team |
| **Phase 2** | Health API Audit | 1 week | DevOps |
| **Phase 2** | Suggestions API Profiling | 1 week | Performance |
| **Phase 2** | Metrics API Evaluation | 1 week | Platform |
| **Phase 2** | Final Decisions | 1 week | Architecture |
| **Phase 3** | Cleanup & Documentation | 1 week | All Teams |

**Total Estimated Timeline:** 6-8 weeks

---

## 📂 Files to Create/Modify

### Rust Memory Service
**New files:**
- `src/api/queue.rs` - Queue management API
- `src/api/injection.rs` - Bulk injection API
- `src/services/queue_service.rs` - Queue control logic
- `src/services/injection_service.rs` - Batch processing logic

**Modified files:**
- `src/main.rs` - Register new API routes
- `proto/memory_service.proto` - Add queue and injection messages
- `Cargo.toml` - Add dependencies (tokio channels, async-stream)

### Python Core API
**Deprecated files:**
- `routers/queue_api.py` → Archive after migration
- `routers/memory_injection_api.py` → Archive after migration
- `routers/memory_health_api.py` → Archive if Rust has it

**Modified files:**
- `main.py` - Remove deprecated router registrations
- `requirements.txt` - Remove unused dependencies

### Documentation
**New files:**
- `docs/MEMORY_ROUTER_RATIONALIZATION.md` - Decision log
- `docs/RUST_PYTHON_SPLIT_ARCHITECTURE.md` - Architecture guide
- `docs/MIGRATION_GUIDE.md` - Client migration guide

**Modified files:**
- `README.md` - Update architecture section
- `docs/API.md` - Update endpoint documentation

---

## 🏁 Outcome

> Transforms the monolithic Python memory API into a strategically optimized **Rust/Python hybrid architecture**:
> - **Rust handles performance-critical paths** (CRUD, bulk ops, queues)
> - **Python handles complex business logic** (ACL, drift, suggestions)
> - **Clear decision framework** for future migrations
> - **Improved performance** without sacrificing flexibility
> - **Maintainable codebase** with well-defined service boundaries

**Key Insight:**
> "Migration is not about moving everything to Rust; it's about putting the **right logic in the right language** for the right reasons."

---

## 📊 Decision Matrix Summary

| Router | Migrate? | Reason | Timeline |
|--------|----------|--------|----------|
| `injection_api` | ✅ Yes | High-throughput bulk ops | 3 weeks |
| `queue_api` | ✅ Yes | Critical path throughput | 2 weeks |
| `health_api` | 🔶 Maybe | Check if in Rust service | 1 week |
| `suggestions_api` | 🔶 Maybe | Only if latency critical | 3 weeks |
| `metrics` | 🔶 Maybe | Only if streaming needed | 2 weeks |
| `acl_api` | ❌ No | Complex business logic | - |
| `drift_api` | ❌ No | Python tooling dependency | - |
| `preload_api` | ❌ No | Infrequent admin operation | - |
| `health` (core) | ❌ No | Per-service boundary | - |

**Total Immediate Work:** 5 weeks (queue + injection)
**Conditional Work:** 2-6 weeks (if profiling indicates need)
**Maximum Timeline:** 8-10 weeks (all conditional migrations)

---

**Status:** 📋 Ready for Implementation
**Priority:** High (performance optimization)
**Risk Level:** Low (well-defined scope, clear criteria)
