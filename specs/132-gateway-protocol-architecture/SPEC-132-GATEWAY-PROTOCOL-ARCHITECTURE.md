# SPEC-132: Gateway Protocol Architecture

**Status:** 🟡 Under Review
**Created:** October 22, 2025
**Author:** Architecture Team
**Related:** US #77 (Integration Validation), US #93 (Implementation)

---

## 📋 EXECUTIVE SUMMARY

This specification defines the protocol support strategy, routing responsibilities, and configuration architecture for the Ninaivalaigal Gateway service. It addresses a critical architectural decision point discovered during US #77 validation: **how should the Gateway handle mixed-protocol service backends (gRPC + REST)?**

**Key Question:** Should the Gateway be gRPC-only, or support hybrid protocol routing?

**Impact:** Affects all future service integration, CLI tooling, API contracts, and deployment patterns.

---

## 🎯 PROBLEM STATEMENT

### **Discovery Context**

During US #77 validation (gRPC Gateway integration testing), we discovered:

**Current Service Landscape:**
- ✅ **GraphOps:** Native gRPC service (Rust) - Port 13398
- ✅ **Memory Service:** Native gRPC planned, currently REST (Rust) - Port 13393
- ✅ **Core API:** REST/JSON service (Python/FastAPI) - Port 13390

**Gateway Implementation:**
- Currently configured for **gRPC-only** connections
- Attempts to establish gRPC connections to all backends
- Health checks fail for REST backends (Memory, Core API)
- Gateway remains operational despite warnings

**Test Results:**
- Gateway starts successfully ✅
- Gateway health endpoint works ✅
- Routing to REST backends returns 404 ❌
- GraphOps connectivity works ✅ (gRPC native)

### **The Architectural Question**

**What protocol support should the Gateway provide?**

This is not a bug—it's a **foundational architecture decision** that affects:
1. Service integration patterns
2. Client tooling design
3. API surface contracts
4. Migration strategy for existing REST services
5. Long-term maintenance complexity

---

## 🏗️ CURRENT ARCHITECTURE

### **Service Protocol Matrix**

| Service | Current Protocol | Port | Language | Notes |
|---------|-----------------|------|----------|-------|
| **GraphOps** | gRPC | 13398 | Rust | Native gRPC, production-ready |
| **Memory Service** | REST | 13393 | Rust | Planned gRPC migration (SPEC-131) |
| **Core API** | REST | 13390 | Python | FastAPI, legacy compatibility required |
| **Gateway** | gRPC | 13395 | Go | Current: gRPC-only routing |

### **Current Gateway Behavior**

```
┌─────────────┐
│   Gateway   │  (gRPC-only)
│  Port 13395 │
└──────┬──────┘
       │
       ├─── gRPC ──→ GraphOps ✅ (Works)
       │
       ├─── gRPC ──X Memory Service ❌ (REST backend, fails)
       │
       └─── gRPC ──X Core API ❌ (REST backend, fails)
```

**Logs Show:**
```
⚠️  Memory Service health check failed: rpc error: code = Unavailable
⚠️  GraphOps Service health check failed: grpc: failed to unmarshal
✅ All gRPC connections established successfully
```

**Gateway continues running** - graceful degradation working, but routing unavailable.

---

## 🔧 ARCHITECTURE OPTIONS

### **Option 1: gRPC-Only Gateway (Current State)**

**Description:** Gateway only routes gRPC traffic. REST services must be accessed directly or through separate proxy.

**Architecture:**
```
┌──────────┐
│  Clients │
└────┬─────┘
     │
     ├─── gRPC ──→ Gateway (13395) ──→ GraphOps ✅
     │
     └─── REST ──→ Direct Access ──→ Memory/Core API
```

**Pros:**
- ✅ Simple, focused implementation
- ✅ No protocol translation overhead
- ✅ Clear separation of concerns
- ✅ Current code works as-is

**Cons:**
- ❌ Clients must know about multiple endpoints
- ❌ No unified API surface
- ❌ Harder to apply cross-cutting concerns (auth, logging, rate limiting)
- ❌ CLI tools must handle both protocols

**Best For:**
- Pure gRPC microservice architectures
- When REST services will be fully migrated to gRPC

---

### **Option 2: Hybrid Gateway with grpc-gateway Translation**

**Description:** Gateway accepts both gRPC and REST/JSON, translates REST to gRPC for backends.

**Architecture:**
```
┌──────────┐
│  Clients │
└────┬─────┘
     │
     ├─── gRPC ──→ ┌─────────────────┐
     │            │  Gateway (13395) │
     └─── REST ──→ │  - gRPC native  │
                  │  - REST→gRPC     │
                  │  - Translation   │
                  └────────┬─────────┘
                           │
                           ├──→ GraphOps (gRPC) ✅
                           ├──→ Memory (REST, proxied) ✅
                           └──→ Core API (REST, proxied) ✅
```

**Implementation:** Use [grpc-gateway](https://github.com/grpc-ecosystem/grpc-gateway) library

**Pros:**
- ✅ Single unified endpoint for clients
- ✅ Supports both gRPC and REST clients
- ✅ Gradual migration path (REST → gRPC over time)
- ✅ Easier to apply middleware (auth, logging, metrics)

**Cons:**
- ⚠️ Translation overhead (small)
- ⚠️ More complex configuration
- ⚠️ Requires protobuf definitions for all REST endpoints
- ⚠️ Additional testing surface

**Best For:**
- Mixed service architectures (gRPC + REST)
- When gradual migration is needed
- When unified API surface is important

---

### **Option 3: Dual Gateway Pattern**

**Description:** Separate gateways for gRPC and REST traffic, with service mesh coordination.

**Architecture:**
```
┌──────────┐
│  Clients │
└────┬─────┘
     │
     ├─── gRPC ──→ gRPC Gateway (13395) ──→ GraphOps
     │
     └─── REST ──→ REST Gateway (13396) ──→ Memory/Core API
```

**Pros:**
- ✅ Protocol-specific optimizations
- ✅ Clear separation
- ✅ Independent scaling

**Cons:**
- ❌ Two services to maintain
- ❌ Clients must know about both endpoints
- ❌ More deployment complexity

**Best For:**
- Large-scale architectures
- When protocol-specific optimizations matter

---

### **Option 4: Envoy Proxy with Advanced Routing**

**Description:** Use Envoy as universal proxy with protocol translation, advanced routing, and service mesh features.

**Architecture:**
```
┌──────────┐
│  Clients │
└────┬─────┘
     │
     └──→ ┌─────────────────┐
          │  Envoy Proxy    │
          │  - gRPC         │
          │  - REST         │
          │  - WebSocket    │
          │  - HTTP/2       │
          │  - Service Mesh │
          └────────┬─────────┘
                   │
                   ├──→ All Services (any protocol)
```

**Pros:**
- ✅ Enterprise-grade features
- ✅ Protocol agnostic
- ✅ Advanced routing (A/B, canary, circuit breaking)
- ✅ Built-in observability

**Cons:**
- ❌ Complex configuration
- ❌ Steeper learning curve
- ❌ Overkill for current scale

**Best For:**
- Enterprise deployments
- Service mesh architectures
- When advanced routing is required

---

## 🎯 RECOMMENDED APPROACH

### **Recommendation: Option 2 (Hybrid Gateway with grpc-gateway)**

**Rationale:**

1. **Current State Alignment:**
   - Memory Service planned for gRPC migration (SPEC-131)
   - Core API must remain REST (legacy compatibility)
   - Gateway already Go-based, grpc-gateway is Go-native

2. **Migration Path:**
   - Support REST backends today
   - Gradual transition to gRPC as services migrate
   - No client disruption during transitions

3. **Developer Experience:**
   - CLI tools can use REST (simpler) or gRPC (performance)
   - Single endpoint for all services
   - Consistent authentication/authorization

4. **Strategic Fit:**
   - Aligns with SPEC-131 (Memory Router Rationalization)
   - Provides bridge during Rust migration
   - Future-proof for full gRPC architecture

**Implementation Complexity:** Medium (acceptable tradeoff)

---

## 📐 DETAILED DESIGN

### **Protocol Support Matrix**

| Client Protocol | Backend Protocol | Gateway Action | Status |
|----------------|------------------|----------------|--------|
| gRPC | gRPC | Direct proxy | ✅ Current |
| gRPC | REST | gRPC→REST translation | 🟡 New |
| REST | gRPC | REST→gRPC translation | 🟡 New |
| REST | REST | HTTP proxy | 🟡 New |

### **Routing Strategy**

**Path-Based Routing:**
```
/api/v1/memory/*    → Memory Service (13393)
/api/v1/graph/*     → GraphOps (13398)
/api/v1/core/*      → Core API (13390)
/health             → Gateway health
/metrics            → Gateway metrics
```

**Protocol Detection:**
- `Content-Type: application/grpc` → gRPC handler
- `Content-Type: application/json` → REST handler
- Header-based routing for ambiguous cases

### **Configuration Architecture**

**Environment Variables:**
```bash
# Backend Service Addresses
MEMORY_SERVICE_ADDR=192.168.68.66:13393
MEMORY_SERVICE_PROTOCOL=rest  # or 'grpc'

GRAPHOPS_SERVICE_ADDR=192.168.68.66:13398
GRAPHOPS_SERVICE_PROTOCOL=grpc

CORE_API_ADDR=192.168.68.66:13390
CORE_API_PROTOCOL=rest

# Gateway Settings
GATEWAY_PORT=13395
GATEWAY_MODE=hybrid  # 'grpc-only', 'rest-only', 'hybrid'
```

**Configuration File (gateway.yaml):**
```yaml
gateway:
  listen:
    port: 13395
    host: 0.0.0.0

  mode: hybrid  # grpc-only | rest-only | hybrid

  backends:
    memory:
      address: "192.168.68.66:13393"
      protocol: rest
      routes:
        - path: /api/v1/memory/*
        - path: /api/v1/memories/*
      health_check:
        enabled: true
        path: /health
        interval: 10s

    graphops:
      address: "192.168.68.66:13398"
      protocol: grpc
      routes:
        - path: /api/v1/graph/*
        - path: /api/v1/graphops/*
      health_check:
        enabled: true
        interval: 10s

    core_api:
      address: "192.168.68.66:13390"
      protocol: rest
      routes:
        - path: /api/v1/core/*
      health_check:
        enabled: true
        path: /health
        interval: 10s

  middleware:
    - logging
    - metrics
    - cors
    - auth  # future

  observability:
    logging:
      level: info
      format: json  # or 'text'
    metrics:
      enabled: true
      port: 9090
      path: /metrics
```

### **Implementation Phases**

**Phase 1: REST Proxy Support** (2 weeks)
- Add HTTP reverse proxy for REST backends
- Path-based routing configuration
- Health check improvements
- Documentation

**Phase 2: Protocol Translation** (2 weeks)
- Integrate grpc-gateway library
- REST→gRPC translation for Memory Service
- Protocol detection logic
- Testing and validation

**Phase 3: Advanced Features** (2 weeks)
- Authentication/authorization middleware
- Rate limiting
- Circuit breaking
- Advanced routing rules

**Phase 4: Migration Support** (ongoing)
- Support Memory Service transition to gRPC
- Gradual cutover with no client changes
- Monitoring and observability

---

## 🧪 TESTING STRATEGY

### **Test Matrix**

| Test Case | Client | Backend | Expected |
|-----------|--------|---------|----------|
| gRPC→gRPC native | gRPC client | GraphOps | Direct proxy, no translation |
| REST→REST proxy | curl/HTTP | Memory | HTTP reverse proxy |
| REST→gRPC translation | curl/HTTP | GraphOps | REST→gRPC translation |
| gRPC→REST translation | gRPC client | Memory | gRPC→REST translation |
| Health checks | Any | All | Gateway aggregates health |
| Protocol errors | Mixed | Mixed | Clear error messages |

### **Validation Tests**

**Test 1: REST Backend Routing**
```bash
curl http://localhost:13395/api/v1/memory/health
# Expected: 200 OK with Memory Service response
```

**Test 2: gRPC Backend Routing**
```bash
grpcurl -plaintext localhost:13395 graphops.v1.GraphOpsService/GetGraph
# Expected: gRPC response from GraphOps
```

**Test 3: Mixed Protocol**
```bash
# REST client accessing gRPC service
curl http://localhost:13395/api/v1/graph/status
# Expected: Translation to gRPC, JSON response
```

**Test 4: Failure Handling**
```bash
# Stop Memory Service
curl http://localhost:13395/api/v1/memory/health
# Expected: 503 Service Unavailable (not 500 or crash)
```

---

## 📊 SUCCESS CRITERIA

**Must Have:**
- ✅ Gateway routes REST requests to REST backends
- ✅ Gateway maintains gRPC routing to gRPC backends
- ✅ Health checks work for mixed protocols
- ✅ Error handling is graceful and informative
- ✅ Configuration is clear and documented
- ✅ No breaking changes to existing gRPC clients

**Should Have:**
- ✅ REST→gRPC translation for at least one service
- ✅ Metrics and observability for both protocols
- ✅ Performance within 10ms overhead for routing
- ✅ Configuration validation and helpful errors

**Nice to Have:**
- ⚠️ Hot-reload configuration without restart
- ⚠️ Advanced routing rules (header-based, etc.)
- ⚠️ A/B testing support

---

## 🔗 RELATED SPECIFICATIONS

- **SPEC-131:** Memory Router Rationalization (Rust migration)
- **US #77:** gRPC Gateway Integration (validation that discovered this issue)
- **US #93:** Gateway Protocol Support Review (implementation ticket)

---

## 📚 REFERENCES

**Technical Resources:**
- [grpc-gateway Documentation](https://grpc-ecosystem.github.io/grpc-gateway/)
- [gRPC Go Tutorial](https://grpc.io/docs/languages/go/)
- [Envoy Proxy](https://www.envoyproxy.io/) (for future consideration)

**Industry Patterns:**
- Google API Gateway (hybrid REST/gRPC)
- AWS API Gateway (protocol agnostic)
- Kong Gateway (multi-protocol)

---

## 🎯 DECISION LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-22 | Recommended Option 2 (Hybrid) | Balances current needs with future migration path |
| 2025-10-22 | YAML configuration preferred | Better for complex routing rules |
| 2025-10-22 | Phase 1 priority: REST proxy | Unblocks immediate CLI tools and testing |

---

## ✅ APPROVAL CHECKLIST

- [ ] Architecture team review
- [ ] Backend team review (Rust/Python)
- [ ] DevOps review (deployment implications)
- [ ] Security review (auth/authz patterns)
- [ ] Documentation team notified

---

## 📝 NEXT STEPS

1. ✅ Create US #93 for implementation
2. ✅ Present to architecture team for decision
3. ✅ Update US #77 with closure note referencing this SPEC
4. ⏳ Begin Phase 1 implementation upon approval
5. ⏳ Create developer guide for hybrid gateway usage

---

**Status:** 🟡 **Awaiting Architecture Team Decision**
**Target Decision Date:** October 29, 2025
**Implementation Start:** TBD (upon approval)

---

**Document Version:** 1.0
**Last Updated:** October 22, 2025
**Next Review:** Upon architecture decision
