# SPEC-132: Gateway Protocol Architecture

**Status:** 🟡 Under Review
**Created:** October 22, 2025
**Implementation:** US #93

---

## 📋 QUICK SUMMARY

This specification addresses the architectural question: **How should the Ninaivalaigal Gateway handle mixed-protocol service backends (gRPC + REST)?**

**Discovered During:** US #77 validation
**Decision Required:** Protocol support strategy
**Recommended:** Hybrid gateway with grpc-gateway translation

---

## 📚 DOCUMENTS

### **Core Specification**
- **[SPEC-132-GATEWAY-PROTOCOL-ARCHITECTURE.md](./SPEC-132-GATEWAY-PROTOCOL-ARCHITECTURE.md)**
  - Complete architecture specification
  - Problem statement and context
  - Four architecture options analyzed
  - Recommended approach (Option 2: Hybrid)
  - Detailed design and configuration
  - Testing strategy and success criteria
  - Implementation phases

### **Visual Diagrams**
- **[DIAGRAMS.md](./DIAGRAMS.md)**
  - Current state architecture
  - All four options visualized
  - Protocol flow diagrams
  - Migration path
  - Routing architecture
  - Testing flow
  - Performance expectations

### **Configuration Example**
- **[gateway.yaml.example](./gateway.yaml.example)**
  - Complete hybrid gateway configuration
  - Backend definitions (Memory, GraphOps, Core API)
  - Protocol-specific settings
  - Middleware configuration
  - Observability settings
  - Translation rules
  - Ready to use as template

---

## 🎯 KEY QUESTION

**Should the Gateway support:**
1. **gRPC-only** (current state - blocks REST services)
2. **Hybrid gRPC + REST** (recommended - supports all services)
3. **Dual gateways** (separate for each protocol)
4. **Envoy proxy** (enterprise solution)

---

## 💡 RECOMMENDATION

**Option 2: Hybrid Gateway with grpc-gateway Translation**

**Why:**
- ✅ Single unified endpoint for all clients
- ✅ Supports gradual migration (REST → gRPC)
- ✅ No client disruption during transitions
- ✅ Aligns with SPEC-131 (Memory Service Rust migration)
- ✅ Medium complexity (acceptable tradeoff)

**Implementation:** 3 phases over 6 weeks
1. REST proxy support (unblock immediate needs)
2. Protocol translation (full hybrid mode)
3. Advanced features (auth, rate limiting)

---

## 🔍 CONTEXT

### **The Discovery**

During US #77 validation, we found:
- Gateway configured for gRPC-only
- Memory Service and Core API are REST services
- GraphOps is native gRPC ✅
- Routing to REST backends fails (404)
- Gateway remains operational (graceful degradation)

**This is NOT a bug** - it's an **architectural design question**.

### **Service Landscape**

| Service | Protocol | Port | Language | Status |
|---------|----------|------|----------|--------|
| GraphOps | gRPC | 13398 | Rust | Native gRPC ✅ |
| Memory Service | REST | 13393 | Rust | Migrating to gRPC (SPEC-131) |
| Core API | REST | 13390 | Python | Legacy, must remain REST |
| Gateway | gRPC-only | 13395 | Go | Needs hybrid support |

---

## 📊 ARCHITECTURE OPTIONS

### **Option 1: gRPC-Only** (Current)
- ✅ Simple implementation
- ❌ Clients must access REST services directly
- ❌ No unified API surface

### **Option 2: Hybrid Gateway** ⭐ (Recommended)
- ✅ Single endpoint for all services
- ✅ Supports both protocols
- ✅ Gradual migration path
- ⚠️ Medium complexity

### **Option 3: Dual Gateways**
- ✅ Protocol-specific optimizations
- ❌ Two services to maintain
- ❌ More deployment complexity

### **Option 4: Envoy Proxy**
- ✅ Enterprise features
- ✅ Protocol agnostic
- ❌ Complex configuration
- ❌ Overkill for current scale

**See [SPEC document](./SPEC-132-GATEWAY-PROTOCOL-ARCHITECTURE.md) for detailed analysis.**

---

## 🚀 IMPLEMENTATION

### **Phase 1: REST Proxy** (2 weeks)
- Add HTTP reverse proxy for REST backends
- Path-based routing
- Health check improvements
- **Deliverable:** Memory and Core API accessible via gateway

### **Phase 2: Protocol Translation** (2 weeks)
- Integrate grpc-gateway library
- REST→gRPC translation
- Protocol detection logic
- **Deliverable:** Full hybrid mode operational

### **Phase 3: Advanced Features** (2 weeks)
- Authentication/authorization
- Rate limiting
- Circuit breaking
- **Deliverable:** Production-ready gateway

---

## 🧪 VALIDATION

**Test Matrix:**
- ✅ gRPC → gRPC (native, no translation)
- ✅ REST → REST (HTTP proxy)
- ✅ REST → gRPC (translation)
- ✅ gRPC → REST (translation)
- ✅ Health checks (mixed protocols)
- ✅ Failure handling (graceful degradation)

**Success Criteria:**
- All routing paths work
- <10ms overhead for proxying
- <15ms overhead for translation
- Clear error messages
- No breaking changes to existing clients

---

## 🔗 RELATED WORK

### **Specifications**
- **SPEC-131:** Memory Router Rationalization (Rust migration)
  - Memory Service transitioning from REST to gRPC
  - Gateway must support during transition

### **User Stories**
- **US #77:** gRPC Gateway Integration
  - Validation that discovered this architectural question
  - Gateway infrastructure proven production-ready
  - 5 of 7 tests passed, routing blocked by this decision

- **US #93:** Gateway Protocol Support Review
  - Implementation ticket for this SPEC
  - Will implement recommended Option 2 (Hybrid)

---

## 📝 DECISION TIMELINE

| Date | Milestone |
|------|-----------|
| Oct 22, 2025 | SPEC created, under review |
| Oct 29, 2025 | Architecture team decision (target) |
| Nov 5, 2025 | Phase 1 implementation start (if approved) |
| Nov 19, 2025 | Phase 2 implementation |
| Dec 3, 2025 | Phase 3 implementation |
| Dec 10, 2025 | Production deployment |

---

## ✅ APPROVAL CHECKLIST

- [ ] Architecture team review
- [ ] Backend team review (Rust/Python)
- [ ] DevOps review (deployment)
- [ ] Security review (auth patterns)
- [ ] CLI team review (client impact)

---

## 📚 REFERENCES

**Technical Resources:**
- [grpc-gateway](https://grpc-ecosystem.github.io/grpc-gateway/) - REST-to-gRPC translation
- [gRPC Go](https://grpc.io/docs/languages/go/) - gRPC implementation
- [Envoy Proxy](https://www.envoyproxy.io/) - Alternative solution

**Industry Examples:**
- Google Cloud API Gateway (hybrid REST/gRPC)
- AWS API Gateway (protocol agnostic)
- Kong Gateway (multi-protocol support)

---

## 🎯 NEXT STEPS

**For Decision Makers:**
1. Review [main specification](./SPEC-132-GATEWAY-PROTOCOL-ARCHITECTURE.md)
2. Review [diagrams](./DIAGRAMS.md) for visual understanding
3. Consider [configuration example](./gateway.yaml.example)
4. Approve or request modifications
5. If approved → US #93 begins implementation

**For Implementers:**
1. Wait for architecture decision
2. Review implementation phases
3. Prepare development environment
4. Begin Phase 1 upon approval

---

## 📧 CONTACTS

**Architecture Team:** architecture@ninaivalaigal.dev
**SPEC Author:** Cascade AI / Architecture Team
**Implementation Lead:** TBD (pending approval)

---

## 📊 IMPACT ASSESSMENT

**Services Affected:**
- Gateway (implementation changes)
- Memory Service (routing enabled)
- Core API (routing enabled)
- GraphOps (no changes, already working)

**Client Impact:**
- CLI tools: Can use unified endpoint
- gRPC clients: No changes (backward compatible)
- REST clients: Can access via gateway (new capability)

**Operations Impact:**
- Single endpoint to monitor
- Unified observability
- Simplified deployment

**Development Impact:**
- Medium: 6 weeks of focused work
- Low risk: Incremental rollout
- High value: Unifies architecture

---

**This SPEC is ready for architecture team review and decision.**

**Status:** 🟡 Awaiting Decision
**Next Review:** Architecture Team Meeting (Oct 29, 2025)
