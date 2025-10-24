# SPEC-131: Memory Router Rationalization

**Status:** 📋 Ready for Implementation
**Taiga:** US #95
**Created:** October 22, 2025
**Owner:** Rust Team + Architecture Team

---

## 📚 Documentation Index

This directory contains all documentation for SPEC-131: Memory Router Rationalization, a strategic initiative to selectively migrate Python memory routers to Rust based on performance profiles.

### Core Documents

1. **[SPEC-131-memory-router-rationalization.md](./SPEC-131-memory-router-rationalization.md)**
   - Complete specification document
   - Decision framework and criteria
   - Detailed router analysis
   - Success criteria and timeline

2. **[ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)**
   - Visual architecture diagrams
   - Current state vs target state
   - Service boundaries and responsibilities
   - Performance comparison charts
   - Migration flow diagrams

3. **[MIGRATION_PLAN.md](./MIGRATION_PLAN.md)**
   - Detailed router decision matrix
   - Phase-by-phase implementation plan
   - Timeline and milestones
   - Success criteria and outcomes

---

## 🎯 Quick Summary

### Strategic Principle
> "Only migrate to Rust when the performance/throughput justifies the complexity."

### Router Decisions

**✅ Migrate to Rust (2 routers):**
- `injection_api.py` - High-throughput bulk operations (3 weeks)
- `queue_api.py` - Critical path queue control (2 weeks)

**🔶 Conditional (3 routers):**
- `health_api.py` - Check if in Rust service first (1 week)
- `suggestions_api.py` - Only if latency critical (3 weeks)
- `metrics` - Only if streaming needed (2 weeks)

**❌ Keep in Python (4 routers):**
- `acl_api.py` - Complex RBAC logic
- `drift_api.py` - Python tooling dependency
- `preload_api.py` - Admin-only, infrequent
- `health` (Core API) - Service boundary

### Timeline

**Total:** 6-10 weeks
- **Phase 1:** 5 weeks (immediate migrations)
- **Phase 2:** 4 weeks (conditional evaluations)
- **Phase 3:** 1 week (cleanup)

### Expected Outcomes

**Performance:**
- Queue API: 80% latency reduction
- Injection API: 5x throughput improvement
- Resource usage: 30% reduction

**Code Quality:**
- ~500 lines removed (deprecated routers)
- Clear Rust/Python boundaries
- Better maintainability

---

## 📊 Router Analysis Summary

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

---

## 🚀 Getting Started

### For Implementation Team

1. **Read the SPEC:** Start with `SPEC-131-memory-router-rationalization.md`
2. **Review Architecture:** Check `ARCHITECTURE_DIAGRAM.md` for visual overview
3. **Follow Migration Plan:** Use `MIGRATION_PLAN.md` for step-by-step guidance
4. **Track Progress:** Update Taiga US #95 with progress

### For Stakeholders

- **Executive Summary:** See "Quick Summary" section above
- **Business Impact:** See "Expected Outcomes" in SPEC-131
- **Timeline:** See "Implementation Timeline" in SPEC-131
- **Risk Assessment:** Low risk - well-defined scope, clear criteria

---

## 🔗 Related Work

**Previous:**
- US #88: Core API Smart Cleanup (removed redundant `memory_api.py`)

**Dependencies:**
- SPEC-043: Memory ACL (staying in Python)
- SPEC-038: Memory Preloading (staying in Python)
- SPEC-036: Memory Injection Rules (migrating to Rust)
- Rust Memory Service (port 13393)

**Follow-up:**
- Performance benchmarks (after Phase 1)
- Conditional migration decisions (after Phase 2)

---

## 📈 Success Metrics

**Performance Targets:**
- Queue API: P99 < 10ms
- Injection API: >1000 memories/sec
- No regression on Python routers

**Quality Targets:**
- Unit test coverage >80% (Rust)
- Integration tests passing
- Documentation complete

**Business Targets:**
- Faster memory operations
- Reduced infrastructure costs
- Better scalability

---

## 🎯 Key Insights

### Strategic Engineering
This SPEC demonstrates **strategic software engineering**:
- ✅ Data-driven decisions (profile before migrating)
- ✅ Clear migration criteria (performance justifies complexity)
- ✅ Rust for speed, Python for flexibility
- ✅ No over-engineering (4 routers stay in Python)

### Decision Framework
The decision framework from this SPEC can be reused for future migration decisions across the codebase.

---

## 📞 Contact

**Questions?** Ask in #architecture channel
**Updates?** Track in Taiga US #95
**Issues?** Create ticket with tag `spec-131`

---

**Status:** 📋 Ready for Implementation
**Priority:** High (performance optimization)
**Risk:** Low (well-defined scope)
**Next Action:** Begin Phase 1 - Queue API migration
