# Container Language Reference

**Last Updated:** October 30, 2025
**Status:** Production
**Purpose:** Quick reference for the core programming language of each container

---

## 🚀 Application Services

| Container | Port | Language | Layer | SPEC | Rationale | Protocol |
|-----------|------|----------|-------|------|-----------|----------|
| **ui-customer** | 8101 | **TypeScript** | UI | SPEC-067 | Modern React ecosystem with type safety | HTTP/JSON |
| **core-api** | 13390 | **Python** | Routing | SPEC-020 | Pythonic orchestration between compute/cognitive layers | REST (FastAPI) |
| **business-service** | 13391 | **Python** | Cognitive | SPEC-026-030 | Stripe SDK + relational billing analytics | REST (internal) |
| **admin-vendor** | 13392 | **Python** | Cognitive | SPEC-025 | Dashboard rendering + vendor management | REST (internal) |
| **memory-service** | 13393 | **Rust** | Compute ⚡ | SPEC-005/006/011 | Deterministic performance and safe parallelism | REST (HTTP/JSON) |
| **graph-service** | 13394 | **Python** | Cognitive 🧠 | SPEC-040/041 | Leverages ML/graph libraries (NetworkX, scikit, AGE driver) | REST (FastAPI) |
| **gateway** | 13395 | **Rust** | Compute ⚡ | SPEC-063 | gRPC bridge with minimal latency | gRPC |

---

## 🔧 Infrastructure Services

| Container | Port | Language | Layer | Rationale | Protocol |
|-----------|------|----------|-------|-----------|----------|
| **db** | 5432 | **SQL** | Infra | Dual relational + graph store | SQL + AGE |
| **pgbouncer-tx** | 6432 | **C** | Infra | Standard lightweight pooler | PostgreSQL wire |
| **pgbouncer-sess** | 6433 | **C** | Infra | Standard lightweight pooler | PostgreSQL wire |
| **redis** | 6379 | **C** | Infra | Core cache daemon | RESP |

---

## 🧪 Development & Monitoring

| Container | Port | Language | Layer | SPEC | Rationale | Protocol |
|-----------|------|----------|-------|------|-----------|----------|
| **graphops** | N/A | **Rust** | Compute ⚡ | SPEC-062 | Graph traversal + Cypher parsing performance | gRPC → PostgreSQL |
| **Go Gateway** | 8080 | **Go** | Infra | N/A | Mature tooling for proto translation | gRPC ↔ REST |
| **load-tester** | N/A | **Go** | Infra | N/A | Native concurrency for stress tests | HTTP/gRPC clients |
| **EM CLI (Go)** | N/A | **Go** | Infra | SPEC-073/079 | Memory CLI for operations | gRPC client |
| **jaeger** | 16686 | **Go** | Infra | SPEC-101 | OpenTelemetry native collector | OTLP |

---

## 📊 Language Distribution

### By Layer

**Compute Layer (High-Performance):**
- **Rust:** Memory Service, Gateway, GraphOps
- **Characteristics:** <5ms p99, memory-safe, concurrent I/O

**Cognitive Layer (Intelligence):**
- **Python:** Core API, Graph Service, Business Service, Admin/Vendor
- **Characteristics:** <50-100ms p99, ML/AI, SDK-rich

**Infrastructure Layer:**
- **Go:** gRPC Gateway, Load Tester, Jaeger
- **C:** PgBouncer, Redis
- **SQL:** PostgreSQL

**UI Layer:**
- **TypeScript:** Customer UI (React)

### By Count

```
Python:      4 services (Core API, Business, Admin, Graph)
Rust:        3 services (Memory, Gateway, GraphOps)
Go:          3 services (Go Gateway, Load Tester, EM CLI)
TypeScript:  1 service  (Customer UI)
C:           2 services (PgBouncer x2, Redis)
SQL:         1 service  (PostgreSQL)
```

**Note:** "gRPC Gateway" renamed to "Go Gateway" for clarity (Gateway = Rust gRPC service on 13395)

---

## 🔍 Language Selection Rationale

### Why Rust? ⚡
**Use Case:** Throughput-critical, CPU-bound, concurrent I/O
**Services:** Memory CRUD, Gateway, GraphOps
**Benefits:**
- 10-100x faster than Python on compute operations
- Memory safety (zero-cost abstractions)
- Excellent async/await with Tokio
- <5ms p99 latency

**Future:** WASM integration for Relevance Core (SPEC-031 inner loop) if relevance_engine crate or other WASM modules exist.

### Why Python?
**Use Case:** Intelligence-oriented, model-rich, SDK-dependent
**Services:** Core API, Graph Service, Business Service, Admin/Vendor
**Benefits:**
- Rich ML/AI ecosystem (NumPy, scikit-learn, transformers)
- FastAPI for rapid API development
- Apache AGE driver, Stripe SDK, OpenAI SDK
- Easy integration with AI/ML models

### Why Go?
**Use Case:** Infrastructure tooling, gRPC ecosystems, concurrent I/O
**Services:** gRPC Gateway, Load Tester
**Benefits:**
- Best gRPC ecosystem (auto-generated stubs)
- Simple concurrency (goroutines)
- Single binary deployment
- Fast compilation

### Why TypeScript?
**Use Case:** Modern web UI with type safety
**Services:** Customer UI
**Benefits:**
- Type-safe React development
- Rich ecosystem (Tailwind, shadcn/ui)
- Vite for fast builds
- Modern tooling

---

## 🔗 Technology Stacks

### Python Services
```yaml
Language: Python 3.11+
Web Framework: FastAPI
ORM: SQLAlchemy 2.0
Database Driver: psycopg3 (async)
Validation: Pydantic v2
Testing: pytest + pytest-asyncio
Linting: ruff + mypy
```

### Rust Services
```yaml
Language: Rust 2021 edition
Web Framework: Axum (HTTP), Tonic (gRPC)
Database: sqlx (PostgreSQL)
Cache: redis-rs with dashmap
Serialization: serde + serde_json
Testing: cargo test
```

### Go Services
```yaml
Language: Go 1.21+
gRPC: google.golang.org/grpc
HTTP: net/http (stdlib)
Concurrency: goroutines + channels
Testing: go test
```

### TypeScript UI
```yaml
Language: TypeScript 5.x
Framework: React 18
Build Tool: Vite
Styling: Tailwind CSS
Components: shadcn/ui
State: React Query
HTTP: Axios
```

---

## 📋 Container Image Sources

### Custom Built (In-Repo)
- `nina-core-api:arm64` - Python service
- `nina-business-service:arm64` - Python service
- `nina-admin-vendor:arm64` - Python service
- `nina-graph-service:arm64` - Python service
- `nina-memory-service:arm64` - Rust service
- `ninaivalaigal-gateway:arm64` - Rust service
- `ninaivalaigal-graphops:arm64` - Rust service
- `ninaivalaigal-grpc-gateway:arm64` - Go service
- `nina-load-tester:arm64` - Go service
- `nina-customer-ui:arm64` - TypeScript/React
- `nina-intelligence-db:arm64` - PostgreSQL + AGE + pgvector
- `nina-pgbouncer:latest` - Custom PgBouncer

### Third-Party Images
- `redis:7-alpine` - Official Redis
- `jaegertracing/all-in-one:1.51` - Official Jaeger

---

## 🎯 Finding Container Source Code

### Python Services
```bash
# Core API
services/core-api/

# Business Service
services/business-service/

# Admin/Vendor
services/admin-vendor-service/

# Graph Service
services/graph-service/
```

### Rust Services
```bash
# Memory Service
rust-services/memory-service/

# Gateway
rust-services/gateway/

# GraphOps
rust-services/graphops/
```

### Go Services
```bash
# gRPC Gateway
go-services/grpc-gateway/

# Load Tester
go-services/load-tools/
```

### TypeScript UI
```bash
# Customer UI
apps/customer/
```

---

## 🔄 Inter-Service Communication

### Python ↔ Rust
- **Protocol:** HTTP/REST (JSON)
- **Pattern:** Core API routes to Memory Service via HTTP
- **Example:** `http://localhost:13393/memory/remember`

### Python ↔ Python
- **Protocol:** HTTP/REST (JSON)
- **Pattern:** Core API routes to Graph/Business services
- **Example:** `http://localhost:13394/api/v1/graph/explain-context`

### Python ↔ Go
- **Protocol:** gRPC (planned)
- **Pattern:** Services call Go gRPC Gateway
- **Future:** REST → gRPC translation

### All ↔ Database
- **Protocol:** PostgreSQL wire protocol
- **Via:** PgBouncer (transaction/session pooling)
- **Driver:** Python (psycopg3), Rust (sqlx), Go (pgx)

---

## 📚 References

- **SPEC-020:** Memory Provider Architecture (Hybrid Compute-Cognitive)
- **SPEC-099:** Rust Migration Strategy & ROI Analysis
- **SPEC-100:** API Container Modularization & Runtime-Agnostic Federation
- **ARCHITECTURE_OVERVIEW.md:** Complete system architecture
- **SPEC_CROSS_VALIDATION_REPORT.md:** Architecture validation

---

## 🏷️ Quick Reference Tags

**For docker-compose.yml labeling (US#144 P1):**

```yaml
services:
  core-api:
    labels:
      - "ninaivalaigal.language=python"
      - "ninaivalaigal.layer=routing"

  memory-service:
    labels:
      - "ninaivalaigal.language=rust"
      - "ninaivalaigal.layer=compute"

  graph-service:
    labels:
      - "ninaivalaigal.language=python"
      - "ninaivalaigal.layer=cognitive"
```

---

## 🔮 Future Direction

These language assignments are stable for the current architecture, with potential expansion areas:

- **Rust (Compute Layer Expansion)** - Potential migration of Relevance Core (SPEC-031 inner loop) to WASM/Rust crate for 10x performance gain
- **Go (System Tools)** - Telemetry, CLI, and orchestration daemons for infrastructure management
- **Python (Cognitive Layer)** - Retained for ML and dynamic reasoning pipelines; no rewrites planned
- **TypeScript (UI Layer)** - Maintained for front-end interactivity and agent visualization

*This prevents confusion six months later when another engineer revisits "why we didn't rewrite everything in Rust."*

---

**Last Updated:** October 30, 2025
**Maintained By:** Engineering Team
**Related US:** #144 (Architecture Documentation)
**Review Feedback:** Incorporated recommendations from architecture review (Oct 30, 2025)
