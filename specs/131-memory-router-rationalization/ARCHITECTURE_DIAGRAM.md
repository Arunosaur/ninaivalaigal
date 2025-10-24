# Memory Router Rationalization - Architecture Diagrams

## 📊 Current State (After US #88)

```
┌────────────────────────────────────────────────────────────────────────┐
│                           CLIENT / FRONTEND                             │
│                    (Web UI, Mobile Apps, CLI Tools)                     │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP/REST
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY / NGINX                              │
│                   (Routing, TLS, Load Balancing)                        │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                     ▼                           ▼
        ┌────────────────────────┐   ┌──────────────────────────┐
        │   PYTHON CORE API      │   │   RUST SERVICES          │
        │   Port: 13390          │   │                          │
        │   (18 routers)         │   │                          │
        └────────────────────────┘   └──────────────────────────┘
                     │                           │
                     │                           │
        ┌────────────┴────────────┐             │
        │                         │             │
        ▼                         ▼             ▼
  ┌──────────┐            ┌──────────────┐  ┌─────────────┐
  │  Auth &  │            │   Memory     │  │   Memory    │
  │  Users   │            │   Advanced   │  │   Service   │
  │ (5 rt)   │            │   Features   │  │ (Rust 13393)│
  └──────────┘            │   (5 rt)     │  │             │
                          └──────────────┘  │ • CRUD      │
  ┌──────────┐                              │ • Cache     │
  │  Teams & │            ┌──────────────┐  │ • pgvector  │
  │  Orgs    │            │ Operations   │  └─────────────┘
  │ (4 rt)   │            │  (4 rt)      │
  └──────────┘            └──────────────┘  ┌─────────────┐
                                            │  GraphOps   │
                                            │ (Rust 13398)│
                                            │             │
                                            │ • Apache    │
                                            │   AGE       │
                                            │ • Cypher    │
                                            └─────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌────────────────────┐        ┌────────────────────┐
        │   PostgreSQL       │        │      Redis         │
        │   (Primary DB)     │        │   (Cache Layer)    │
        └────────────────────┘        └────────────────────┘
```

### Current Router Distribution

**Python Core API (18 routers):**
- 🔐 Auth & Users: 5 routers
- 👥 Teams & Orgs: 4 routers
- 🧠 Advanced Memory: 5 routers
  - ❌ `memory_acl_api` (RBAC)
  - ❌ `memory_drift_api` (Analytics)
  - 🔶 `memory_health_api` (Monitoring)
  - ✅ `memory_injection_api` (Bulk ops) ← **MIGRATE**
  - 🔶 `memory_suggestions_api` (AI/NLP)
- ⚙️ Operations: 4 routers
  - ✅ `queue_api` (Queue control) ← **MIGRATE**
  - ❌ `preload_api` (Templates)
  - ❌ `health` (Status)
  - 🔶 `metrics` (Aggregation)

**Rust Services:**
- ⚡ Memory Service: Basic CRUD
- 📊 GraphOps: Graph operations

---

## 🎯 Target State (After SPEC-131)

```
┌────────────────────────────────────────────────────────────────────────┐
│                           CLIENT / FRONTEND                             │
│                    (Web UI, Mobile Apps, CLI Tools)                     │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP/REST
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY / NGINX                              │
│                   (Routing, TLS, Load Balancing)                        │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                     ▼                           ▼
        ┌────────────────────────┐   ┌──────────────────────────────────┐
        │   PYTHON CORE API      │   │   RUST SERVICES                  │
        │   Port: 13390          │   │   (Performance-Critical)         │
        │   (14-16 routers)      │   │                                  │
        │                        │   │                                  │
        │   BUSINESS LOGIC       │   │   HIGH-PERFORMANCE OPERATIONS    │
        └────────────────────────┘   └──────────────────────────────────┘
                     │                               │
                     │                               │
        ┌────────────┴─────────┐      ┌─────────────┴─────────────┐
        │                      │      │                           │
        ▼                      ▼      ▼                           ▼
  ┌──────────────┐      ┌─────────────────┐         ┌──────────────────────┐
  │  Auth &      │      │  Advanced       │         │  Memory Service      │
  │  Users       │      │  Memory         │         │  (Rust 13393)        │
  │  (5 rt)      │      │  (3 rt)         │         │  ┌─────────────────┐ │
  │              │      │                 │         │  │ CORE FEATURES   │ │
  │ • signup     │      │ ❌ ACL          │         │  │ • CRUD          │ │
  │ • users      │      │    (RBAC)       │         │  │ • Redis cache   │ │
  │ • rbac       │      │                 │         │  │ • pgvector      │ │
  │ • tokens     │      │ ❌ Drift        │         │  └─────────────────┘ │
  │ • sessions   │      │    (Analytics)  │         │                      │
  └──────────────┘      │                 │         │  ┌─────────────────┐ │
                        │ 🔶 Suggestions  │         │  │ MIGRATED (NEW)  │ │
  ┌──────────────┐      │    (AI/NLP)     │         │  │ ✅ Injection    │ │
  │  Teams &     │      │                 │         │  │    (Bulk ops)   │ │
  │  Orgs        │      └─────────────────┘         │  │                 │ │
  │  (4 rt)      │                                  │  │ ✅ Queue        │ │
  │              │      ┌─────────────────┐         │  │    (Control)    │ │
  │ • teams      │      │  Operations     │         │  └─────────────────┘ │
  │ • orgs       │      │  (2 rt)         │         │                      │
  │ • invites    │      │                 │         │  ┌─────────────────┐ │
  │ • keys       │      │ ❌ Preload      │         │  │ CONDITIONAL     │ │
  └──────────────┘      │    (Templates)  │         │  │ 🔶 Health       │ │
                        │                 │         │  │    (If missing) │ │
                        │ ❌ Health       │         │  └─────────────────┘ │
                        │    (Core API)   │         └──────────────────────┘
                        │                 │
                        │ 🔶 Metrics      │         ┌──────────────────────┐
                        │    (Conditional)│         │  GraphOps            │
                        └─────────────────┘         │  (Rust 13398)        │
                                                    │                      │
                                                    │ • Apache AGE         │
                                                    │ • Cypher queries     │
                                                    │ • Graph traversal    │
                                                    └──────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌────────────────────┐        ┌────────────────────┐
        │   PostgreSQL       │        │      Redis         │
        │   (Primary DB)     │        │   (Cache Layer)    │
        └────────────────────┘        └────────────────────┘
```

### Target Router Distribution

**Python Core API (14-16 routers):**
- 🔐 Auth & Users: 5 routers ✅ (no change)
- 👥 Teams & Orgs: 4 routers ✅ (no change)
- 🧠 Advanced Memory: 3 routers ❌ (keep complex logic)
  - `memory_acl_api` - RBAC business logic
  - `memory_drift_api` - Schema analytics
  - `memory_suggestions_api` - AI/NLP (conditional)
- ⚙️ Operations: 2 routers ❌ (keep infrequent ops)
  - `preload_api` - Admin templates
  - `health` - Core API status
  - `metrics` - Aggregation (conditional)

**Rust Memory Service (Enhanced):**
- ✅ **Existing:** Basic CRUD, cache, pgvector
- ✅ **NEW:** Bulk injection API (migrated)
- ✅ **NEW:** Queue management API (migrated)
- 🔶 **Conditional:** Health API (if not present)

**Rust GraphOps:**
- ✅ Graph operations (no change)

---

## 🔄 Migration Flow

### Phase 1: Queue API Migration

```
┌─────────────────────────────────────────────────────────────────┐
│ BEFORE: Python handles queue operations                         │
└─────────────────────────────────────────────────────────────────┘

    Client Request
         │
         ▼
    [Python Core API]
         │
         ▼
    queue_api.py ───► Queue Logic (Python)
         │
         ▼
    Redis/DB


┌─────────────────────────────────────────────────────────────────┐
│ AFTER: Rust handles queue operations                            │
└─────────────────────────────────────────────────────────────────┘

    Client Request
         │
         ▼
    [API Gateway]
         │
         ▼
    [Rust Memory Service] ───► Queue Logic (Rust)
         │                         │
         ▼                         ▼
    Redis/DB              Tokio Channels (async)

BENEFITS:
✅ 80% latency reduction (50ms → 10ms)
✅ Better concurrency (Rust async)
✅ Lower resource usage
```

### Phase 2: Injection API Migration

```
┌─────────────────────────────────────────────────────────────────┐
│ BEFORE: Python handles bulk injection                           │
└─────────────────────────────────────────────────────────────────┘

    Client Bulk Request (1000 memories)
         │
         ▼
    [Python Core API]
         │
         ▼
    injection_api.py ───► Batch Processing (Python)
         │                   │
         │                   ▼
         │              Sequential/Limited Parallelism
         │
         ▼
    PostgreSQL + Redis


┌─────────────────────────────────────────────────────────────────┐
│ AFTER: Rust handles bulk injection                              │
└─────────────────────────────────────────────────────────────────┘

    Client Bulk Request (1000 memories)
         │
         ▼
    [API Gateway]
         │
         ▼
    [Rust Memory Service]
         │
         ▼
    Injection Logic (Rust) ───► Parallel Batching
         │                          │
         │                          ▼
         │                      Stream Processing
         │
         ▼
    PostgreSQL + Redis (concurrent writes)

BENEFITS:
✅ 5x throughput (200 → 1000 memories/sec)
✅ Streaming pipeline (memory efficient)
✅ Better error handling (Rust type safety)
```

---

## 🧠 Decision Framework Visualization

```
                    START: Analyze Router
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Is it on HOT PATH?   │
                  │ (High frequency)     │
                  └──────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼ YES               ▼ NO
          ┌─────────────────┐    ┌──────────────┐
          │ Bulk operations?│    │ Complex      │
          │ High throughput?│    │ business     │
          └─────────────────┘    │ logic?       │
                   │             └──────────────┘
         ┌─────────┴─────────┐           │
         │                   │           ▼ YES
         ▼ YES               ▼ NO    ┌──────────┐
    ┌─────────┐        ┌─────────┐  │ KEEP IN  │
    │ MIGRATE │        │ Profile │  │ PYTHON   │
    │ TO RUST │        │ First   │  └──────────┘
    │    ✅   │        │   🔶    │
    └─────────┘        └─────────┘

EXAMPLES:

✅ MIGRATE TO RUST:
   • injection_api (bulk ops, high throughput)
   • queue_api (hot path, real-time control)

🔶 CONDITIONAL (Profile First):
   • suggestions_api (depends on latency)
   • metrics (depends on volume)
   • health_api (check if already in Rust)

❌ KEEP IN PYTHON:
   • acl_api (complex RBAC logic)
   • drift_api (Python tooling dependency)
   • preload_api (infrequent admin ops)
```

---

## 📊 Performance Comparison

### Latency Expectations

```
                PYTHON                      RUST
                ------                      ----

Queue Ops       ~50ms                       ~10ms    (80% reduction)
Injection       ~200 mem/s                  ~1000/s  (5x throughput)
CRUD            ~30ms                       ~5ms     (already in Rust)
Health          ~5ms                        ~2ms     (minimal gain)


         Latency (ms)
         │
    50   │ ████████████ Python Queue
         │
    30   │ ████████ Python CRUD          ████████ Python Injection
         │
    10   │ ██ Rust Queue
         │
    5    │ █ Rust CRUD    ██ Python Health
         │
    2    │ █ Rust Health
         └───────────────────────────────────────────────────────▶
              Queue      CRUD      Health    Injection
```

### Resource Usage Comparison

```
                PYTHON                      RUST
                ------                      ----

Memory          200-300 MB                  50-100 MB   (60% reduction)
CPU (idle)      5-10%                       1-2%        (80% reduction)
CPU (load)      60-80%                      30-40%      (50% reduction)
Concurrency     Limited (GIL)               Excellent   (tokio async)


         Resource Usage
         │
   100%  │ ████████████ Python under load
         │
    80%  │ ████████████
         │
    60%  │ ████████       ██████ Rust under load
         │
    40%  │ ████████       ██████
         │
    20%  │ ██             ██
         │
     0%  │
         └──────────────────────────────────────────────────────▶
              Python          Rust
```

---

## 🎯 Router Categorization

### Visual Decision Map

```
                    ALL ROUTERS (9 analyzed)
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ADVANCED MEMORY (5)        OPERATIONS (4)
                │                         │
    ┌───────────┼──────────┐         ┌───┼────┐
    │           │          │         │   │    │
    ▼           ▼          ▼         ▼   ▼    ▼

┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────┐ ┌────────┐
│   ACL   │ │  Drift  │ │  Health  │ │ Queue │ │Preload │
│   ❌    │ │   ❌    │ │    🔶    │ │  ✅   │ │  ❌    │
│ Python  │ │ Python  │ │   Maybe  │ │ Rust  │ │ Python │
│         │ │         │ │          │ │       │ │        │
│ Complex │ │ Tooling │ │ Check if │ │  Hot  │ │ Admin  │
│  RBAC   │ │Alembic  │ │ in Rust  │ │ Path  │ │  Only  │
└─────────┘ └─────────┘ └──────────┘ └───────┘ └────────┘

┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│Injection │ │Suggest  │ │ Health │ │Metrics │
│   ✅     │ │   🔶    │ │  ❌    │ │  🔶    │
│  Rust    │ │  Maybe  │ │ Python │ │ Maybe  │
│          │ │         │ │        │ │        │
│   Bulk   │ │Profile  │ │  Core  │ │ If     │
│   Ops    │ │  First  │ │  API   │ │Streaming│
└──────────┘ └─────────┘ └────────┘ └────────┘

LEGEND:
✅ Migrate to Rust (2 routers)
🔶 Conditional (3 routers)
❌ Keep in Python (4 routers)
```

---

## 🏁 Final Architecture Summary

### Service Responsibilities

```
┌────────────────────────────────────────────────────────────────┐
│ PYTHON CORE API - "The Orchestrator"                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🎯 FOCUS: Complex Business Logic & Orchestration               │
│                                                                 │
│ ✅ Authentication & Authorization                               │
│    → Multi-factor auth, session management, token rotation     │
│                                                                 │
│ ✅ Team & Organization Management                               │
│    → Hierarchies, invitations, billing integration             │
│                                                                 │
│ ✅ Advanced Memory Features                                     │
│    → RBAC (complex rules), Drift detection (Alembic),          │
│      AI suggestions (NLP/graph heuristics)                     │
│                                                                 │
│ ✅ Admin Operations                                             │
│    → Preloading templates, configuration management            │
│                                                                 │
│ 🚫 NOT RESPONSIBLE FOR: High-throughput, hot path operations   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ RUST MEMORY SERVICE - "The Workhorse"                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ⚡ FOCUS: Performance-Critical & High-Throughput Operations    │
│                                                                 │
│ ✅ Basic CRUD (Existing)                                        │
│    → /remember, /recall, /memories - Fast, cached              │
│                                                                 │
│ ✅ Bulk Operations (NEW from SPEC-131)                          │
│    → Injection API - Stream processing, 1000+ memories/sec     │
│                                                                 │
│ ✅ Queue Management (NEW from SPEC-131)                         │
│    → Real-time control, low latency (<10ms), async primitives  │
│                                                                 │
│ ✅ Caching & Storage                                            │
│    → Redis integration, pgvector embeddings                    │
│                                                                 │
│ 🚫 NOT RESPONSIBLE FOR: Complex business logic, orchestration  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ RUST GRAPHOPS - "The Intelligence"                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 FOCUS: Graph Operations & Relationship Intelligence         │
│                                                                 │
│ ✅ Apache AGE Integration                                       │
│    → Cypher queries, graph traversal, relationship detection   │
│                                                                 │
│ 🚫 NOT RESPONSIBLE FOR: Memory CRUD, user management           │
└────────────────────────────────────────────────────────────────┘
```

---

**Status:** 📋 Architecture Defined
**Next Steps:** Implement Phase 1 (Queue + Injection migration)
**Timeline:** 5 weeks for immediate migrations
