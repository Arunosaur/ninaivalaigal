# SPEC-099 & SPEC-100 Action Plan
**To Close Both SPECs: 78% → 95%+**

**Date:** October 20, 2025
**Timeline:** 2-3 weeks to 95% completion

---

## 🎯 **IMMEDIATE ACTIONS (Next 24-48 Hours)**

### 1. ✅ Task #77: Deploy CLI Tools (Go)
**Status:** In Progress
**Blocker:** REMOVED (Task #49 complete)
**Priority:** 🔥 HIGH
**Time:** 2-4 hours

**Action Items:**
```bash
# Apply GraphOps deployment pattern
cd go-services/cli-tools

# 1. Build image with Docker
docker build --no-cache --platform linux/arm64 \
  -t ninaivalaigal-cli-tools:arm64 .

# 2. Save and transfer to Apple Container CLI
docker save ninaivalaigal-cli-tools:arm64 -o /tmp/cli-tools.tar
container image load -i /tmp/cli-tools.tar

# 3. Create management scripts
# - scripts/nv-cli-tools-start.sh (port 13397)
# - scripts/nv-cli-tools-stop.sh
# - scripts/nv-cli-tools-status.sh

# 4. Start container
./scripts/nv-cli-tools-start.sh

# 5. Test
./scripts/nv-cli-tools-status.sh
```

**Success Criteria:**
- [ ] Container running on port 13397
- [ ] Health check passing
- [ ] Management scripts working
- [ ] Documentation updated

---

### 2. 🔗 Integrate GraphOps with API Gateway
**Status:** New
**Priority:** 🔥 HIGH
**Time:** 2-3 hours

**Action Items:**
```yaml
# Update deployment/traefik/dynamic.yml
http:
  routers:
    graphops-router:
      rule: "PathPrefix(`/graphops`)"
      service: graphops-service
      middlewares:
        - stripprefix-graphops
        - ratelimit

  services:
    graphops-service:
      loadBalancer:
        servers:
          - url: "http://192.168.66.115:13398"
        healthCheck:
          path: "/health"
          interval: "10s"

  middlewares:
    stripprefix-graphops:
      stripPrefix:
        prefixes:
          - "/graphops"
```

**Test:**
```bash
# Restart gateway
./scripts/gateway-stop.sh
./scripts/gateway-start.sh

# Test routing
curl http://localhost/graphops/health
curl http://localhost/graphops/metrics

# Test via gateway test script
./scripts/gateway-test.sh
```

**Success Criteria:**
- [ ] GraphOps accessible via gateway
- [ ] Health checks working through gateway
- [ ] Metrics accessible
- [ ] Gateway tests passing

---

### 3. 📝 Task #81: gRPC Gateway Integration Testing
**Status:** New
**Priority:** HIGH
**Time:** 4-6 hours

**Action Items:**
```python
# Create tests/integration/test_grpc_integration.py

import grpc
import requests

def test_grpc_gateway_to_memory_service():
    """Test REST → gRPC → Memory Service"""
    # Via gateway
    response = requests.get("http://localhost:13395/api/v1/memory/123")
    assert response.status_code == 200

def test_grpc_gateway_to_graphops():
    """Test REST → gRPC → GraphOps"""
    response = requests.post(
        "http://localhost:13395/api/v1/graph/query",
        json={"query": "MATCH (n) RETURN n LIMIT 1"}
    )
    assert response.status_code == 200

def test_end_to_end_flow():
    """Test Client → API Gateway → gRPC Gateway → Services"""
    # Via Traefik gateway
    response = requests.get("http://localhost/graphops/health")
    assert response.status_code == 200
```

**Success Criteria:**
- [ ] All integration tests passing
- [ ] End-to-end flow validated
- [ ] Error handling tested
- [ ] Performance acceptable

---

## 🎯 **THIS WEEK (Oct 21-25)**

### Goal: SPEC-099 → 90%, SPEC-100 → 85%

**Day 1-2 (Mon-Tue):**
- ✅ Task #77: CLI Tools deployment
- ✅ GraphOps gateway integration
- ✅ Basic integration testing

**Day 3-4 (Wed-Thu):**
- ✅ Task #81: Comprehensive gRPC testing
- ✅ Load testing with tools (port 13396)
- ✅ Performance baseline

**Day 5 (Fri):**
- ✅ Documentation updates
- ✅ Code quality fixes (Task #78)
- ✅ Week review

---

## 🎯 **NEXT WEEK (Oct 28 - Nov 1)**

### Goal: SPEC-099 → 95%, SPEC-100 → 90%

### 4. 📊 Task #84: OpenTelemetry Distributed Tracing
**Priority:** MEDIUM
**Time:** 3-5 days

**Action Items:**
```python
# 1. Add OpenTelemetry to all services
pip install opentelemetry-api opentelemetry-sdk

# 2. Configure tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

# 3. Instrument FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# 4. Deploy Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest
```

**Success Criteria:**
- [ ] Tracing across all services
- [ ] Jaeger UI accessible
- [ ] Request correlation working
- [ ] Performance impact minimal

---

### 5. 🧪 Comprehensive Load Testing
**Priority:** MEDIUM
**Time:** 2-3 days

**Action Items:**
```bash
# Use deployed load testing tools (port 13396)
container exec ninaivalaigal-dev-load-tester \
  /usr/local/bin/load-tester \
  --url http://192.168.66.115:13390/health \
  --requests 10000 \
  --concurrency 100

# Test each service
- Core API (13390)
- Business Service (13391)
- Memory Service (13393)
- GraphOps (13398)

# Measure P50/P95/P99 latencies
# Identify bottlenecks
# Optimize hot paths
```

**Success Criteria:**
- [ ] All services tested under load
- [ ] Performance baseline established
- [ ] Bottlenecks identified
- [ ] Optimization plan created

---

### 6. 📝 Documentation & Polish
**Priority:** MEDIUM
**Time:** 2 days

**Action Items:**
- [ ] Update all service READMEs
- [ ] Create deployment runbooks
- [ ] Document API contracts
- [ ] Update architecture diagrams
- [ ] Create troubleshooting guides

---

## 🎯 **WEEKS 3-4 (Nov 4-15)**

### Goal: SPEC-099 → 100%, SPEC-100 → 95%

### 7. Extract Graph/AI Service to Rust
**Priority:** MEDIUM
**Time:** 1-2 weeks

**Scope:**
- Extract graph intelligence logic
- Implement in Rust for performance
- Integrate with AGE database
- Migrate endpoints from Python

**Port:** 13399 (next in sequence)

---

### 8. Implement Feedback Loop (Rust)
**Priority:** MEDIUM
**Time:** 1 week

**Scope:**
- Event-driven architecture
- Redis Streams integration
- Async message processing
- Performance monitoring

**Port:** 13400

---

## 📊 **COMPLETION FORECAST**

| Week | SPEC-099 | SPEC-100 | Combined | Key Milestone |
|------|----------|----------|----------|---------------|
| **Current** | 80% | 75% | 78% | GraphOps deployed |
| **Week 1** | 90% | 85% | 88% | All services deployed + tested |
| **Week 2** | 95% | 90% | 93% | Observability + optimization |
| **Week 3-4** | 100% | 95% | 98% | Graph/AI extracted, polish complete |

---

## 🔥 **CRITICAL PATH**

```
Day 1-2: CLI Tools (Task #77) → Integration Testing (Task #81)
         ↓
Day 3-4: GraphOps Gateway Integration → Load Testing
         ↓
Week 2:  OpenTelemetry (Task #84) → Performance Optimization
         ↓
Week 3:  Graph/AI Extraction → Feedback Loop
         ↓
Week 4:  Final Polish → 95%+ Complete
```

---

## ✅ **SUCCESS METRICS**

### Technical Metrics
- [ ] All 7 services deployed and healthy
- [ ] All integration tests passing
- [ ] API Gateway routing all services
- [ ] Distributed tracing working
- [ ] P95 latency <100ms for all services
- [ ] Load test: 10,000+ req/s sustained

### Documentation Metrics
- [ ] All services documented
- [ ] Deployment runbooks complete
- [ ] Architecture diagrams updated
- [ ] Troubleshooting guides created

### Process Metrics
- [ ] All Taiga tasks closed
- [ ] Code quality gates passing
- [ ] CI/CD pipeline working
- [ ] Monitoring dashboards live

---

## 📋 **TASK TRACKING**

### SPEC-099 Tasks
- [x] #71: gRPC Gateway (Done)
- [x] #72: Load Testing Tools (Done)
- [x] #73: CLI Tools Code (Done)
- [x] #76: Fix Load Testing (Done)
- [x] #49: GraphOps gRPC (Done)
- [ ] #77: Deploy CLI Tools (In Progress)
- [ ] #81: Integration Testing (New)
- [ ] Extract Graph/AI to Rust (Future)
- [ ] Implement Feedback Loop (Future)

### SPEC-100 Tasks
- [x] #30-37: Service Decomposition (Done)
- [x] #79: Shared Contracts (Done)
- [x] #80: Protocol Buffers (Done)
- [x] #82: Event Bus (Done)
- [x] #83: API Gateway (Done)
- [ ] GraphOps Gateway Integration (New)
- [ ] #81: Integration Testing (New)
- [ ] #84: OpenTelemetry Tracing (New)

---

## 💡 **RECOMMENDATIONS**

### This Week Priority
1. **Task #77** - Deploy CLI Tools (blocks nothing else)
2. **Gateway Integration** - Connect GraphOps to Traefik
3. **Task #81** - Integration testing (validates everything)

### Next Week Priority
4. **Task #84** - OpenTelemetry (observability)
5. **Load Testing** - Performance baseline
6. **Documentation** - Knowledge capture

### Future Priority
7. **Graph/AI Extraction** - Performance gain
8. **Feedback Loop** - Event-driven architecture
9. **Service Mesh** - Production hardening

---

## 🎯 **FINAL GOAL**

**Target:** 95%+ completion in 2-3 weeks
**Path:** Clear and achievable
**Risk:** LOW - Foundation is solid
**Confidence:** HIGH - All pieces in place

**Next Action:** Start Task #77 (CLI Tools deployment) - 2-4 hours

---

**Created:** October 20, 2025
**Owner:** Development Team
**Status:** ✅ READY TO EXECUTE
