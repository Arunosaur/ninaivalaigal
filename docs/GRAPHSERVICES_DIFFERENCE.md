# Graph Services Comparison

**Date**: 2025-11-04
**Related SPECs**: SPEC-062, SPEC-064, SPEC-100, SPEC-145

---

## 📋 Service Overview

### 1. **graph-service** (Python)
- **Port**: 13394 (Apple dev runtime)
- **Language**: Python/FastAPI
- **Purpose**: Graph Intelligence and AI features
- **Responsibilities**:
  - ML-based relevance inference
  - Graph reasoning algorithms
  - Memory graph analysis
  - Relationship discovery
- **SPEC**: SPEC-100 (API Container Modularization)

### 2. **graphops** (Rust)
- **Port**: 13398 (Apple dev runtime)
- **Language**: Rust/Tokio + gRPC
- **Purpose**: High-performance Apache AGE query execution
- **Responsibilities**:
  - Cypher query execution via AGE SQL interface
  - Query result caching
  - Performance optimization
  - gRPC API for graph operations
- **SPEC**: SPEC-062 (GraphOps Stack Deployment)

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core API      │    │  graph-service  │    │    graphops     │
│   (Python)      │    │   (Python)      │    │    (Rust)       │
│   Port: 13390   │    │   Port: 13394   │    │   Port: 13398   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Apache AGE     │
                    │  (PostgreSQL)   │
                    │   Port: 5452    │
                    └─────────────────┘
```

---

## 📊 SPEC-145 Compliance

Both services are built according to SPEC-145 multi-runtime, multi-architecture standards:

### Container Images
- **graph-service**: `nina-graph-service:arm64`
- **graphops**: `nina-graphops:arm64`

### Port Allocation (from `config/ports.nv.yaml`)
```yaml
apple:
  dev:
    graph_service: 13394  # Python Graph/AI Service
    graphops: 13398       # Rust GraphOps Service
```

---

## 🔄 Integration Pattern

1. **Core API** → **graph-service** for AI-powered graph features
2. **Core API** → **graphops** for high-performance Cypher queries
3. **graph-service** can optionally use **graphops** for complex queries

---

## 🚀 Deployment Status

- ✅ **graph-service**: Running on port 13394
- ✅ **graphops**: Built and ready (container startup script fixed)
- ✅ Both services documented in ports.nv.yaml
- ✅ SPEC-145 compliant container images available

---

## 📝 Notes

- These are **distinct services** with different purposes
- Both can run simultaneously without conflicts
- graphops provides the low-level query execution engine
- graph-service provides high-level AI and intelligence features
- Both services connect to the same Apache AGE database
