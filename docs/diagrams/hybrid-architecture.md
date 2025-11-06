# Hybrid Compute-Cognitive Architecture Diagram

**Version**: 3.0
**Date**: November 4, 2025
**Related**: US#144, SPEC-020 Addendum, SPEC-099, SPEC-100

---

## 🏗️ Architecture Overview

Ninaivalaigal implements a **hybrid compute-cognitive architecture** that separates:
- **Compute Layer (Rust/Go)**: Fast, deterministic, throughput-bound operations
- **Cognitive Layer (Python)**: Intelligence, ML models, adaptive reasoning
- **Routing Layer (Python)**: API gateway and orchestration

---

## 📊 Service Topology Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[🌐 Customer UI<br/>Port: 8101<br/>TypeScript/React]
        AdminUI[👔 Admin Console<br/>Port: 8201<br/>TypeScript/React]
    end

    subgraph "Routing Layer"
        CoreAPI[⚡ Core API<br/>Port: 13390<br/>Python/FastAPI<br/>🔀 Routing & Orchestration]
    end

    subgraph "Compute Layer ⚡"
        MemoryService[💾 Memory Service<br/>Port: 13393<br/>Rust/Axum<br/>⚡ CRUD Operations]
        Gateway[🚪 gRPC Gateway<br/>Port: 13395<br/>Rust/gRPC<br/>⚡ API Gateway]
    end

    subgraph "Cognitive Layer 🧠"
        GraphService[🧠 Graph Service<br/>Port: 13394<br/>Python/FastAPI<br/>🧠 AI & Intelligence]
        BusinessService[💼 Business Service<br/>Port: 13391<br/>Python/FastAPI<br/>🧠 Billing & Analytics]
        AdminVendor[👥 Admin Vendor<br/>Port: 13392<br/>Python/FastAPI<br/>🧠 Admin Dashboards]
    end

    subgraph "Data Layer"
        PgBouncer[🔄 PgBouncer<br/>Port: 6432<br/>Connection Pooling]
        Postgres[(🐘 PostgreSQL 15<br/>Port: 5432<br/>pgvector + Apache AGE)]
        Redis[💾 Redis 7<br/>Port: 6379<br/>Cache & Sessions]
    end

    UI --> CoreAPI
    AdminUI --> CoreAPI

    CoreAPI --> MemoryService
    CoreAPI --> GraphService
    CoreAPI --> BusinessService
    CoreAPI --> AdminVendor
    CoreAPI --> Gateway

    MemoryService --> PgBouncer
    MemoryService --> Redis
    GraphService --> PgBouncer
    GraphService --> Redis
    BusinessService --> PgBouncer
    AdminVendor --> PgBouncer

    PgBouncer --> Postgres

    style CoreAPI fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style MemoryService fill:#ffe1e1,stroke:#cc0000,stroke-width:2px
    style Gateway fill:#ffe1e1,stroke:#cc0000,stroke-width:2px
    style GraphService fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
    style BusinessService fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
    style AdminVendor fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
```

---

## 🔄 Request Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant CoreAPI as Core API<br/>(Routing)
    participant MemoryService as Memory Service<br/>(Compute ⚡)
    participant GraphService as Graph Service<br/>(Cognitive 🧠)
    participant DB as PostgreSQL

    User->>CoreAPI: GET /api/v1/memory/memories
    CoreAPI->>MemoryService: Fast CRUD Operation
    MemoryService->>DB: Query memories
    DB-->>MemoryService: Memory data
    MemoryService-->>CoreAPI: Memory list
    CoreAPI->>GraphService: Get relevance scores
    GraphService->>DB: Graph intelligence query
    DB-->>GraphService: Relevance data
    GraphService-->>CoreAPI: Relevance scores
    CoreAPI-->>User: Combined response
```

---

## 📋 Layer Classification

### Compute Layer ⚡ (Rust/Go)
**Purpose**: Fast, deterministic, throughput-bound operations

| Service | Port | Language | Rationale |
|---------|------|----------|-----------|
| Memory Service | 13393 | Rust | CRUD operations, vector search, Redis caching |
| gRPC Gateway | 13395 | Rust | Low-latency API gateway |

### Cognitive Layer 🧠 (Python)
**Purpose**: Intelligence, ML models, adaptive reasoning

| Service | Port | Language | Rationale |
|---------|------|----------|-----------|
| Graph Service | 13394 | Python | AI feedback, relevance ranking, graph intelligence |
| Business Service | 13391 | Python | Billing analytics, Stripe integration |
| Admin Vendor | 13392 | Python | Admin dashboards, vendor management |

### Routing Layer 🔀 (Python)
**Purpose**: API gateway and orchestration

| Service | Port | Language | Rationale |
|---------|------|----------|-----------|
| Core API | 13390 | Python | Auth, users, teams, routing between layers |

---

## 🎯 Architecture Benefits

### Performance
- ⚡ **10-100x faster** on compute-bound operations (Rust)
- 🧠 **Full intelligence** preserved in Python
- 🔄 **Optimal routing** between layers

### Cost
- 💰 **30-60% infrastructure cost reduction**
- 🚀 **Better resource utilization**
- 📊 **Scalable per layer**

### Maintainability
- 🔧 **Clear separation of concerns**
- 📚 **Language-appropriate tools**
- 🧪 **Easier testing and debugging**

---

## 📚 Related Documentation

- **SPEC-020 Addendum**: `/specs/020-memory-provider-architecture/ADDENDUM_HYBRID_ARCHITECTURE.md`
- **Architecture Overview**: `/docs/architecture/ARCHITECTURE_OVERVIEW.md`
- **Container Language Reference**: `/docs/architecture/CONTAINER_LANGUAGE_REFERENCE.md`
- **Validation Summary**: `/docs/architecture/HYBRID_ARCHITECTURE_VALIDATION_SUMMARY.md`

---

**Last Updated**: November 4, 2025
**Maintained By**: Developer G
**Related US**: #144
