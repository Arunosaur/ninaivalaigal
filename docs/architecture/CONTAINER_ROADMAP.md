# Container Roadmap: Current, Planned & Future

**Last Updated:** October 30, 2025
**Status:** Strategic Planning Document
**References:** SPEC-099, SPEC-100, SPEC-101

---

## 🎯 Executive Summary

**Current State:** 16 containers operational
**Containers Being Rewritten:** **NONE** ✅
**New Containers Planned:** 7 (Observability + Infrastructure)
**Language Strategy:** Stable hybrid architecture (Rust/Python/Go/TypeScript)

**Key Insight:** The hybrid compute-cognitive architecture is **stable and validated**. No existing services are being rewritten to different languages. New containers focus on **observability** and **infrastructure tooling**.

---

## ✅ Current Production Containers (16)

### Application Services (7)
| Container | Language | Status | Notes |
|-----------|----------|--------|-------|
| ui-customer | TypeScript | ✅ Stable | React UI, staying TypeScript |
| core-api | Python | ✅ Stable | Routing layer, staying Python |
| business-service | Python | ✅ Stable | Billing/Analytics, staying Python |
| admin-vendor | Python | ✅ Stable | Admin dashboards, staying Python |
| **memory-service** | **Rust** | ✅ **Complete** | Migrated from Python (SPEC-099 Phase 2A) |
| graph-service | Python | ✅ Stable | Intelligence hub, staying Python |
| **gateway** | **Rust** | ✅ **Complete** | New service (SPEC-099) |

### Infrastructure (9)
| Container | Language | Status | Notes |
|-----------|----------|--------|-------|
| **graphops** | **Rust** | ✅ **Complete** | Migrated (SPEC-099 Phase 1) |
| grpc-gateway | Go | 🟡 Partial | REST ↔ gRPC translation |
| load-tester | Go | ✅ Complete | Load testing tool |
| em | Go/Python | 🟡 TBD | Entity Manager (language TBD) |
| db | SQL | ✅ Stable | PostgreSQL + AGE + pgvector |
| pgbouncer-tx | C | ✅ Stable | Transaction pooling |
| pgbouncer-sess | C | ✅ Stable | Session pooling |
| redis | C | ✅ Stable | Caching/sessions |
| jaeger | Go | ✅ Stable | Distributed tracing |

---

## 🆕 New Containers - Coming Soon

### Phase 1: Observability Stack (SPEC-101)

**Timeline:** Q1 2026
**Purpose:** Unified observability and performance governance

| Container | Language | Port | Purpose | Priority |
|-----------|----------|------|---------|----------|
| **prometheus** | Go | 9090 | Metrics collection & alerting | P0 |
| **grafana** | Go/TypeScript | 3000 | Unified dashboards | P0 |
| **loki** | Go | 3100 | Log aggregation | P0 |
| **promtail** | Go | N/A | Log shipping agent | P0 |

**Rationale:**
- Complete the observability triad: Metrics (Prometheus), Traces (Jaeger ✅), Logs (Loki)
- Enable SPEC-099 ROI validation with real metrics
- Provide unified dashboards for all services

---

### Phase 2: Infrastructure Tooling (SPEC-099 Phases 4-6)

**Timeline:** Q2-Q3 2026
**Purpose:** Enhanced infrastructure and developer tooling

| Container | Language | Purpose | Priority | Status |
|-----------|----------|---------|----------|--------|
| **telemetry-daemon** | Rust | Real-time metrics streaming | P1 | 🔄 Planned |
| **cli-tools** | Go | Operational CLI utilities | P2 | 🔄 Planned |
| **agent-orchestrator** | Go | Agent coordination layer | P2 | 🔄 Planned |
| **security-middleware** | Rust | JWT/HMAC/token validation | P3 | 🟡 Optional |

**Rationale:**
- **Telemetry Daemon (Rust):** Low-latency metrics collection, independent of Python services
- **CLI Tools (Go):** Single binary deployment, cross-platform operations
- **Agent Orchestrator (Go):** Coordinate Taiga ↔ Windsurf ↔ services
- **Security Middleware (Rust):** Optional performance optimization for auth operations

---

## 🚫 Containers NOT Being Rewritten

### Cognitive Layer - Staying Python ✅

These services are **explicitly staying in Python** because they are intelligence-oriented, model-rich, and SDK-dependent:

| Service | Reason to Keep Python |
|---------|----------------------|
| **core-api** | FastAPI routing, session intelligence, rapid iteration |
| **graph-service** | Apache AGE driver, ML models, NLP, graph reasoning (SPEC-031, 040, 041) |
| **business-service** | Stripe SDK, billing logic, relational analytics |
| **admin-vendor** | Admin dashboards, vendor management, reporting |

**From SPEC-099 Zone 3 (Keep in Python):**
> "Preserve the productivity layer. Guard against re-writing glue just for syntactic consistency."

---

### UI Layer - Staying TypeScript ✅

| Service | Reason to Keep TypeScript |
|---------|---------------------------|
| **ui-customer** | React ecosystem, type safety, modern tooling |

---

### Infrastructure - Staying as-is ✅

| Service | Technology | Status |
|---------|-----------|--------|
| PostgreSQL | SQL + Extensions | Mature, no alternative |
| PgBouncer | C | Industry standard |
| Redis | C | Industry standard |
| Jaeger | Go | Official Jaeger image |

---

## 📊 Language Distribution Evolution

### Current (October 2025)
```
Python:      4 services (25%)
Rust:        3 services (19%)
Go:          3 services (19%)
TypeScript:  1 service  (6%)
Infrastructure: 5 services (31%)
```

### After Phase 1 (Q1 2026) - Observability Added
```
Python:      4 services (20%)
Rust:        3 services (15%)
Go:          7 services (35%) ← Observability stack
TypeScript:  1 service  (5%)
Infrastructure: 5 services (25%)
```

### After Phase 2 (Q3 2026) - Full Infrastructure
```
Python:      4 services (17%)
Rust:        5 services (22%) ← Telemetry + Security
Go:          9 services (39%) ← CLI + Agent Orchestrator
TypeScript:  1 service  (4%)
Infrastructure: 5 services (22%)
```

**Trend:** Go becomes dominant for infrastructure tooling, Rust grows for performance-critical services, Python stable for intelligence.

---

## 🔄 Migration Status by Phase

### ✅ Phase 1: Complete (Oct 2025)
- ✅ **GraphOps (Rust):** Cypher query engine migrated
- **Result:** 10x throughput, <25ms p99 latency

### ⚙️ Phase 2A: Complete (Oct 2025)
- ✅ **Memory Service (Rust):** CRUD + Redis caching migrated
- **Result:** <5ms p99 latency, 100x faster

### ⚙️ Phase 2B: In Progress (Nov 2025)
- 🟡 **GraphOps Integration:** Connect Rust GraphOps to Python Graph Service
- **Note:** NOT rewriting Graph Service—integrating Rust engine with Python intelligence

### 🌿 Phase 3A: Planned (Q1 2026)
- 🔄 **gRPC Gateway Enhancement (Go):** Complete REST ↔ gRPC translation

### 🌿 Phase 3B: Planned (Q1 2026)
- ✅ **Load Tester (Go):** Already complete

### 🔄 Phase 4-6: Future (Q2-Q3 2026)
- 🔄 Telemetry Daemon (Rust)
- 🔄 CLI Tools (Go)
- 🔄 Agent Orchestrator (Go)
- 🟡 Security Middleware (Rust) - Optional

---

## 🎯 Decision Matrix: Rewrite vs New Container

### When to Rewrite Existing Container ❌
**Criteria:**
- Proven 10x+ performance bottleneck
- Simple, well-defined interface
- No SDK dependencies
- Throughput-critical hot path

**Status:** All eligible containers already migrated (Memory Service, GraphOps, Gateway)

### When to Add New Container ✅
**Criteria:**
- New functionality needed (observability, tooling)
- Independent lifecycle
- Clear service boundary
- Doesn't overlap with existing cognitive services

**Status:** All planned containers are NEW, not rewrites

---

## 📋 Service Stability Guarantee

### Python Services: STABLE ✅
- **core-api:** No rewrite planned
- **graph-service:** No rewrite planned (intelligence hub)
- **business-service:** No rewrite planned (Stripe SDK)
- **admin-vendor:** No rewrite planned (dashboards)

**Guarantee:** Python services are part of the validated hybrid architecture and will NOT be rewritten to Rust/Go unless ROI significantly changes.

### Rust Services: STABLE ✅
- **memory-service:** Recently migrated, stable
- **gateway:** Recently built, stable
- **graphops:** Recently migrated, stable

### Go Services: EXPANDING ✅
- **grpc-gateway:** Enhancing existing
- **load-tester:** Complete
- **NEW:** Observability stack (4 containers)
- **NEW:** CLI + orchestration (2 containers)

---

## 🚀 What This Means for Development

### For Python Developers
- ✅ **Job Security:** All cognitive layer services staying Python
- ✅ **Skills Relevant:** ML/AI, FastAPI, Apache AGE remain critical
- 🎓 **Optional Learning:** Understanding Rust/Go contracts helpful but not required

### For Rust Developers
- ⚡ **Focus Area:** Performance-critical compute layer
- 🔄 **Growth:** 2 new services planned (telemetry, security)
- 🎯 **Stable:** No rewrites of existing Rust services

### For Go Developers
- 📈 **High Growth:** 6 new services planned (observability + tooling)
- 🛠️ **Infrastructure Focus:** gRPC, CLI tools, observability
- 🎯 **Domain:** Infrastructure and developer tooling

### For TypeScript Developers
- ✅ **Stable:** UI layer not changing
- 🎨 **Focus:** React, Tailwind, shadcn/ui, user experience
- 🔄 **Integration:** Work with Python/Rust APIs via REST

---

## 📚 References

- **SPEC-099:** Rust Migration Strategy & ROI Analysis
- **SPEC-100:** API Container Modularization & Runtime-Agnostic Federation
- **SPEC-101:** Unified Observability and Performance Governance
- **SPEC-020 Addendum:** Hybrid Compute-Cognitive Architecture
- **CONTAINER_LANGUAGE_REFERENCE.md:** Current language breakdown

---

## 🏆 Conclusion

### No Containers Being Rewritten ✅
The hybrid architecture is **validated and stable**. All eligible performance-critical services have been migrated to Rust. Python cognitive services are staying Python.

### 7 New Containers Planned ✅
- **4 Observability containers (Go):** Prometheus, Grafana, Loki, Promtail
- **3 Infrastructure containers:** Telemetry Daemon (Rust), CLI Tools (Go), Agent Orchestrator (Go)
- **1 Optional container:** Security Middleware (Rust)

### Language Strategy: Polyglot by Design ✅
- **Rust:** Compute layer (memory, gateway, telemetry)
- **Python:** Cognitive layer (intelligence, ML, business logic)
- **Go:** Infrastructure tooling (observability, CLI, orchestration)
- **TypeScript:** UI layer (React, modern web)

**The architecture is production-ready and future-proof.**

---

**Prepared By:** Engineering Team
**Date:** October 30, 2025
**Next Review:** Q1 2026 (after observability stack deployment)
