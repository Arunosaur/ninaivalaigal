# Ninaivalaigal Architecture Overview

**Version**: 3.0 (Hybrid Compute-Cognitive Architecture)
**Last Updated**: October 30, 2025
**Status**: Production
**References**: SPEC-020 (Addendum), SPEC-099 (Rust Migration), SPEC-100 (API Modularization)

---

## 🎯 **Executive Summary: Hybrid Architecture**

Ninaivalaigal implements a **hybrid compute-cognitive architecture** that separates concerns between:
- **Compute Layer (Rust/Go):** Fast, deterministic, throughput-bound operations
- **Cognitive Layer (Python):** Intelligence, ML models, adaptive reasoning

**This architecture delivers:**
- ⚡ **10-100x performance improvement** on compute-bound operations (Rust)
- 🧠 **Full intelligence preservation** in Python microservices
- 🔄 **Runtime-agnostic contracts** enabling future evolution
- 💰 **30-60% infrastructure cost reduction**

---

## 🏗️ **System Architecture**

Ninaivalaigal is an enterprise-grade AI memory management platform built on a modern, scalable, hybrid architecture.

### **Core Architecture Principles**

- **Hybrid Compute-Cognitive Architecture**: Rust for performance, Python for intelligence
- **Microservices Architecture**: Modular components with clear separation of concerns
- **Event-Driven Design**: Asynchronous processing with comprehensive audit trails
- **Multi-Provider Support**: Pluggable memory providers with intelligent failover
- **Enterprise Security**: RBAC, API key management, and comprehensive audit logging
- **High Availability**: Auto-healing systems with chaos-tested resilience
- **Contract-First Integration**: Runtime-agnostic service boundaries (SPEC-100)

---

## 🌐 **Service Topology**

### **Port Allocation (SPEC-086)**

| Service | Port | Language | Layer | Purpose |
|---------|------|----------|-------|---------|
| **Frontend** | 8101 | React/TypeScript | UI | Customer UI |
| **Core API** | 13390 | Python/FastAPI | Routing | Auth, Users, Teams, Routing |
| **Business Service** | 13391 | Python/FastAPI | Cognitive | Billing, Usage, Analytics |
| **Admin/Vendor Service** | 13392 | Python/FastAPI | Cognitive | Admin dashboards, vendor management |
| **Memory Service** | 13393 | **Rust/Axum** | **Compute** | **Memory CRUD, Redis caching** |
| **Graph Service** | 13394 | Python/FastAPI | Cognitive | Graph Intelligence, AI Feedback, Relevance Ranking |
| **Gateway** | 13395 | Rust/gRPC | Compute | API Gateway (planned) |

---

## ⚡ **Compute Layer (Rust/Go)**

**Characteristics:** Throughput-bound, predictable latency, memory-safe, concurrent I/O

### **Memory Service (Rust - Port 13393)**
```rust
// High-performance memory CRUD
- Create/Read/Update/Delete operations
- PostgreSQL + pgvector integration
- Redis caching (1-hour TTL)
- <5ms p99 latency
- Memory-safe concurrency
```

**Technology Stack:**
- **Language:** Rust (2021 edition)
- **Web Framework:** Axum
- **Database:** PostgreSQL + pgvector
- **Cache:** Redis with `dashmap`/`moka`
- **Performance:** 10-100x faster than Python equivalent

**API Endpoints:**
- `POST /memory/remember` - Create memory
- `POST /memory/recall` - Search memories
- `GET /memory/memories` - List all memories
- `GET /health` - Health check

---

## 🧠 **Cognitive Layer (Python)**

**Characteristics:** Intelligence-oriented, model-rich, SDK-dependent, adaptive reasoning

### **Graph Service (Python - Port 13394)**
```python
# Intelligence Hub
- Relevance Ranking (SPEC-031)
- Graph Intelligence (SPEC-040, SPEC-062)
- AI Feedback System (SPEC-041)
- Memory Federation (cross-tenant)
- Performance Analytics
```

**Technology Stack:**
- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Graph DB:** Apache AGE (PostgreSQL extension)
- **ML/AI:** NumPy, scikit-learn, transformers
- **Async:** Redis Streams for event bus

**Key Modules:**
- `lib/relevance_engine.py` (59 matches - SPEC-031)
- `lib/graph_intelligence_api.py` (Graph reasoning)
- `lib/ai_feedback_system.py` (ML feedback loops)
- `lib/memory_federation.py` (Multi-tenant search)

**API Endpoints:**
- `POST /api/v1/graph/explain-context` - Context analysis
- `POST /api/v1/graph/infer-relevance` - Relevance scoring
- `POST /api/v1/graph/feedback-loop` - AI feedback
- `POST /api/v1/graph/analyze-network` - Graph analytics

---

### **Core API (Python - Port 13390)**
```python
# Routing & Orchestration Hub
- Authentication & Authorization
- User/Team/Organization management
- Memory Preloading (SPEC-038)
- Session Intelligence (SPEC-039)
- Request routing to Compute/Cognitive layers
```

**Key Modules:**
- `lib/memory/factory.py` - Memory provider registry
- `lib/memory/hybrid_providers.py` - Compute-Cognitive integration
- `lib/intelligent_session.py` - Session context modeling
- `lib/preloading_engine.py` - Predictive memory warming

---

### **Business Service (Python - Port 13391)**
```python
# Business Logic & Analytics
- Billing & Subscriptions (Stripe SDK)
- Invoice Management (SPEC-027)
- Usage Analytics (SPEC-030)
- Customer Success tracking
```

---

## 🔄 **Hybrid Integration Pattern**

### **Intelligent Memory Creation Flow**

```python
async def remember_intelligent(text, user_id, context_id):
    """
    Hybrid flow: Rust for speed, Python for intelligence
    """
    # 1. Compute Layer: Fast CRUD (Rust)
    memory = await rust_memory_service.create(
        text=text,
        user_id=user_id,
        context_id=context_id
    )  # <5ms p99

    # 2. Cognitive Layer: Relevance Ranking (Python)
    relevance_score = await graph_service.calculate_relevance(
        memory_id=memory.id,
        user_id=user_id
    )  # <50ms p99

    # 3. Cognitive Layer: Graph Linking (Python)
    await graph_service.link_memory_to_graph(
        memory_id=memory.id,
        context_id=context_id
    )  # <100ms p99

    return memory
```

### **Provider Registry (SPEC-020)**

```python
# services/core-api/lib/memory/hybrid_providers.py

PROVIDERS = {
    "memory": RustProvider(base_url="http://localhost:13393"),
    "graph": GraphProvider(base_url="http://localhost:13394"),
    "ranker": RelevanceProvider(base_url="http://localhost:13394"),
}
```

---

## 📊 **Performance Characteristics**

| Operation | Python Baseline | Rust Compute | Improvement |
|-----------|----------------|--------------|-------------|
| **Memory CRUD** | 50-500ms | 1-5ms | **10-100x** |
| **Vector Search** | 180ms | 30ms | **6x** |
| **Concurrent Throughput** | 50 req/sec | 500+ req/sec | **10x** |
| **Memory Usage** | 500MB | 200MB | **60% reduction** |

| Operation | Python Cognitive | Target | Status |
|-----------|-----------------|--------|--------|
| **Relevance Ranking** | 30-50ms | <50ms p99 | ✅ Validated |
| **Graph Intelligence** | 80-100ms | <100ms p99 | ✅ Validated |
| **AI Feedback** | 100-150ms | <200ms p99 | ✅ Validated |

---

## 🎯 **What Stays in Python**

These domains are **knowledge-dense rather than throughput-dense**—Rust adds little value:

| Domain | Service | Port | Reason |
|--------|---------|------|--------|
| **Relevance Ranking** | Graph Service | 13394 | Algorithmic, model-driven, Redis + decay scoring |
| **Graph Intelligence** | Graph Service | 13394 | Apache AGE driver + async orchestration |
| **AI Feedback** | Graph Service | 13394 | ML models, NLP heuristics |
| **Memory Preloading** | Core API | 13390 | Behavior learning, cache heuristics |
| **Session Intelligence** | Core API | 13390 | User-context modeling |
| **Memory Federation** | Graph Service | 13394 | Multi-tenant cross-team reasoning |
| **Business Analytics** | Business Service | 13391 | Relational joins + billing logic |

---

## 🚀 **Future Enhancements (Optional)**

### **P1: Relevance Engine WASM Optimization**
- Port inner mathematical loop (exponential decay + frequency scoring) to Rust WASM
- Call from Python via PyO3 or WASM runtime
- **Expected gain:** 10x faster relevance calculation
- **Effort:** 2-3 days

### **P2: Graph Query Adapter (Go)**
- Wrap Apache AGE/PostgreSQL driver in Go for connection pooling
- Keeps Python async I/O thin
- **Expected gain:** Better connection management
- **Effort:** 1 week

### **P3: Performance Analytics Daemon (Go)**
- Metrics collector streaming to Prometheus
- Low-latency, low-memory footprint
- **Expected gain:** Independent telemetry service
- **Effort:** 3-5 days

---

## 📊 **Foundation Architecture (6 Complete SPECs)**

### **SPEC-007: Unified Context Scope System**
```
┌─────────────────────────────────────────────────────────────┐
│                    Context Scope Hierarchy                  │
├─────────────────────────────────────────────────────────────┤
│  Organization Scope                                         │
│  ├── Team Scope A                                          │
│  │   ├── User Scope 1                                      │
│  │   └── User Scope 2                                      │
│  └── Team Scope B                                          │
│      ├── User Scope 3                                      │
│      └── Agent Scope 1                                     │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Scope Management**: Hierarchical organization, team, and user scopes
- **Permission Inheritance**: Cascading permissions with override capabilities
- **Context Isolation**: Secure separation between different scope levels
- **Cross-Scope Operations**: Controlled sharing and collaboration workflows

### **SPEC-012: Memory Substrate**
```
┌─────────────────────────────────────────────────────────────┐
│                     Memory Substrate                        │
├─────────────────────────────────────────────────────────────┤
│  Memory Operations Layer                                    │
│  ├── Create/Read/Update/Delete                             │
│  ├── Search & Retrieval                                    │
│  ├── Relevance Ranking                                     │
│  └── Context Injection                                     │
├─────────────────────────────────────────────────────────────┤
│  Provider Abstraction Layer                                │
│  ├── PostgreSQL Provider                                   │
│  ├── HTTP/External Providers                               │
│  └── Future Providers (Redis, Vector DBs)                  │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                             │
│  ├── PostgreSQL + pgvector                                 │
│  ├── Redis Cache                                           │
│  └── Apache AGE Graph                                      │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Multi-Provider Architecture**: Pluggable memory providers with consistent API
- **Intelligent Caching**: Redis-backed performance optimization
- **Vector Search**: pgvector integration for similarity search
- **Graph Intelligence**: Apache AGE for relationship modeling

### **SPEC-016: CI/CD Pipeline Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                   CI/CD Pipeline Architecture               │
├─────────────────────────────────────────────────────────────┤
│  GitHub Actions Workflows (28 total)                       │
│  ├── Foundation Validation                                 │
│  │   ├── Memory Provider Tests                             │
│  │   ├── Sharing Collaboration Tests                       │
│  │   └── Comprehensive Coverage Tests                      │
│  ├── Multi-Architecture Builds                             │
│  │   ├── ARM64 (Apple Container CLI)                       │
│  │   └── x86_64 (Docker/Production)                        │
│  └── Quality Gates                                         │
│      ├── Coverage Thresholds (90%/80%/70%)                 │
│      ├── Security Scanning                                 │
│      └── Performance Validation                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Dual Architecture Strategy**: ARM64 development + x86_64 production
- **Comprehensive Testing**: Unit, integration, functional, and chaos testing
- **Quality Enforcement**: Automated coverage thresholds with merge blocking
- **Multi-Environment Support**: Local, staging, and production deployments

### **SPEC-020: Memory Provider Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                Memory Provider Architecture                 │
├─────────────────────────────────────────────────────────────┤
│  Provider Management Layer                                  │
│  ├── Provider Registry (Auto-discovery)                    │
│  ├── Health Monitor (Real-time status)                     │
│  ├── Failover Manager (5 strategies)                       │
│  └── Security Manager (RBAC + API keys)                    │
├─────────────────────────────────────────────────────────────┤
│  Provider Implementations                                   │
│  ├── PostgreSQL Provider                                   │
│  │   ├── Connection pooling                                │
│  │   ├── Query optimization                                │
│  │   └── Health monitoring                                 │
│  └── HTTP Provider (mem0, external APIs)                   │
│      ├── Authentication                                    │
│      ├── Rate limiting                                     │
│      └── Circuit breakers                                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Auto-Discovery**: Environment-based provider detection and registration
- **Intelligent Failover**: Priority, health, round-robin, performance, and hybrid strategies
- **Security Integration**: RBAC permissions with API key management
- **Health Monitoring**: Real-time status tracking with SLO validation

### **SPEC-049: Memory Sharing Collaboration**
```
┌─────────────────────────────────────────────────────────────┐
│              Memory Sharing Collaboration                   │
├─────────────────────────────────────────────────────────────┤
│  Sharing Contract Layer                                     │
│  ├── Cross-Scope Contracts                                 │
│  │   ├── User ↔ User                                       │
│  │   ├── User ↔ Team                                       │
│  │   ├── Team ↔ Organization                               │
│  │   └── Agent ↔ Any Scope                                 │
│  └── Permission Management                                  │
│      ├── VIEW, COMMENT, EDIT, SHARE, ADMIN                 │
│      └── Granular visibility controls                      │
├─────────────────────────────────────────────────────────────┤
│  Consent & Temporal Access                                 │
│  ├── Consent Management                                     │
│  │   ├── Explicit/Implicit/Delegated                      │
│  │   └── Visibility profiles                               │
│  └── Temporal Access                                       │
│      ├── Time-limited access                               │
│      ├── Session-based access                              │
│      ├── Usage-limited access                              │
│      └── Conditional access                                │
├─────────────────────────────────────────────────────────────┤
│  Audit & Compliance                                        │
│  ├── Comprehensive Audit Logging                           │
│  ├── Transfer Record Tracking                              │
│  ├── Compliance Reporting                                  │
│  └── Security Pattern Detection                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Cross-Scope Sharing**: Secure memory sharing between users, teams, organizations, and agents
- **Granular Permissions**: Fine-grained access control with visibility management
- **Temporal Access**: Time-limited, session-based, and conditional access controls
- **Comprehensive Auditing**: Complete audit trails with compliance reporting

### **SPEC-052: Comprehensive Test Coverage**
```
┌─────────────────────────────────────────────────────────────┐
│               Comprehensive Test Coverage                   │
├─────────────────────────────────────────────────────────────┤
│  E2E Test Matrix                                           │
│  ├── Foundation SPEC Testing                               │
│  │   ├── Memory Provider Matrix                            │
│  │   ├── Sharing Collaboration Matrix                      │
│  │   ├── RBAC Integration Matrix                           │
│  │   └── API Endpoint Matrix                               │
│  └── Cross-Component Integration                            │
│      ├── Provider ↔ Sharing Integration                     │
│      ├── RBAC ↔ All Components                             │
│      └── Health ↔ Monitoring Integration                    │
├─────────────────────────────────────────────────────────────┤
│  Chaos Testing Suite                                       │
│  ├── Database Failure Scenarios                            │
│  ├── Redis Failure Scenarios                               │
│  ├── Concurrent Load Testing                               │
│  └── Resource Exhaustion Testing                           │
├─────────────────────────────────────────────────────────────┤
│  Coverage Validation & CI Enforcement                      │
│  ├── Unit Tests (90% threshold)                            │
│  ├── Integration Tests (80% threshold)                     │
│  ├── Functional Tests (70% threshold)                      │
│  └── Quality Gate Enforcement                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **E2E Test Matrix**: Comprehensive testing across all foundation SPECs
- **Chaos Testing**: Resilience validation through failure simulation
- **Coverage Validation**: Automated coverage analysis with quality gates
- **CI Enforcement**: Merge blocking and automated quality assurance

## 🔄 **Data Flow Architecture**

### **Memory Operation Flow**
```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Client │───▶│   FastAPI   │───▶│  Provider   │───▶│  Storage    │
│         │    │   Router    │    │  Manager    │    │   Layer     │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                       │                   │                   │
                       ▼                   ▼                   ▼
               ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
               │    RBAC     │    │   Health    │    │    Redis    │
               │ Validation  │    │  Monitor    │    │    Cache    │
               └─────────────┘    └─────────────┘    └─────────────┘
```

### **Sharing Workflow**
```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Sharer  │───▶│   Contract  │───▶│   Consent   │───▶│   Access    │
│         │    │   Manager   │    │   Manager   │    │   Grant     │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                       │                   │                   │
                       ▼                   ▼                   ▼
               ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
               │    Audit    │    │  Temporal   │    │ Visibility  │
               │   Logger    │    │   Access    │    │  Manager    │
               └─────────────┘    └─────────────┘    └─────────────┘
```

## 🛡️ **Security Architecture**

### **Multi-Layer Security Model**
```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  Authentication Layer                                       │
│  ├── JWT Token Management                                   │
│  ├── API Key Authentication                                 │
│  └── Session Management                                     │
├─────────────────────────────────────────────────────────────┤
│  Authorization Layer (RBAC)                                │
│  ├── Role-Based Access Control                             │
│  ├── Scope-Based Permissions                               │
│  └── Resource-Level Authorization                           │
├─────────────────────────────────────────────────────────────┤
│  Provider Security                                          │
│  ├── Secure Provider Registration                          │
│  ├── API Key Management                                     │
│  └── Security Audit Logging                                │
├─────────────────────────────────────────────────────────────┤
│  Sharing Security                                           │
│  ├── Consent Management                                     │
│  ├── Temporal Access Controls                              │
│  └── Comprehensive Audit Trails                            │
└─────────────────────────────────────────────────────────────┘
```

## 📈 **Performance Architecture**

### **Performance Optimization Stack**
```
┌─────────────────────────────────────────────────────────────┐
│                 Performance Optimization                    │
├─────────────────────────────────────────────────────────────┤
│  Caching Layer (Redis)                                     │
│  ├── Memory Token Cache (1-hour TTL)                       │
│  ├── Relevance Score Cache (15-min TTL)                    │
│  ├── Session Cache (30-min TTL)                            │
│  └── Query Result Cache (configurable TTL)                 │
├─────────────────────────────────────────────────────────────┤
│  Provider Optimization                                      │
│  ├── Connection Pooling (PgBouncer)                        │
│  ├── Intelligent Failover                                  │
│  ├── Health-Based Routing                                  │
│  └── Performance Monitoring                                │
├─────────────────────────────────────────────────────────────┤
│  Database Optimization                                      │
│  ├── pgvector Similarity Search                            │
│  ├── Apache AGE Graph Queries                              │
│  ├── Optimized Indexing                                    │
│  └── Query Performance Monitoring                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Deployment Architecture**

### **Multi-Environment Strategy**
```
┌─────────────────────────────────────────────────────────────┐
│                  Deployment Environments                    │
├─────────────────────────────────────────────────────────────┤
│  Local Development                                          │
│  ├── Apple Container CLI (ARM64)                           │
│  ├── Native performance                                     │
│  └── Hot reload development                                 │
├─────────────────────────────────────────────────────────────┤
│  CI/CD Validation                                          │
│  ├── GitHub Actions (x86_64)                               │
│  ├── Multi-architecture testing                            │
│  └── Quality gate enforcement                              │
├─────────────────────────────────────────────────────────────┤
│  Production Deployment                                      │
│  ├── Kubernetes orchestration                              │
│  ├── Auto-scaling capabilities                             │
│  ├── High availability setup                               │
│  └── Monitoring & observability                            │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 **Enterprise Readiness**

### **Production-Grade Capabilities**
- **High Availability**: Auto-healing systems with intelligent failover
- **Scalability**: Horizontal scaling with provider-based architecture
- **Security**: Enterprise-grade RBAC with comprehensive audit trails
- **Monitoring**: Real-time health monitoring with SLO validation
- **Testing**: Comprehensive test coverage with chaos testing validation
- **Documentation**: Complete developer and user documentation

### **Compliance & Governance**
- **Audit Trails**: Comprehensive logging of all operations
- **Data Governance**: Scope-based data isolation and access controls
- **Security Compliance**: RBAC, API key management, and security monitoring
- **Quality Assurance**: Automated testing with enforced coverage thresholds

## 🚀 **Next Phase Architecture**

With foundation complete, the architecture is ready for:
- **Advanced AI Features**: Graph-based intelligence and reasoning
- **Enterprise Integrations**: SSO, directory services, and enterprise APIs
- **Multi-Tenant SaaS**: Isolated tenant environments with shared infrastructure
- **Advanced Analytics**: Business intelligence and usage analytics
- **Monetization Features**: API billing, usage tracking, and subscription management

---

**This architecture provides the foundation for a world-class AI memory management platform with enterprise-grade capabilities, comprehensive security, and production-ready reliability.**
