# US#79 MVP Scope – Simplified Contracts Layer

**Date:** October 24, 2025
**Approach:** Hybrid - MVP First, Enterprise Later
**Status:** Scope reduction complete

---

## MVP (Phase 1) - Immediate Delivery

### Goal
Achieve the **original US#79 objective**: Share contract definitions between services to reduce duplication and improve type safety.

### What's Included
- ✅ **Shared Contracts Layer**
  - Centralized Pydantic models for auth, user, team
  - Type-safe contract sharing across Python services
  - Proper import structure and validation

- ✅ **Minimal Relationship Fixes**
  - Basic User-Team-Organization relationships
  - Simple foreign key constraints only
  - No complex propagation logic

- ✅ **Simple Migrations**
  - 1-2 Alembic migration files maximum
  - Straightforward schema additions
  - Easy rollback path

- ✅ **Feature Flag Scaffolding**
  - Infrastructure for future enterprise features
  - All flags disabled by default
  - No runtime impact on MVP

### What's Excluded
- ❌ No database triggers (was 4 → now 0)
- ❌ No provenance tracking
- ❌ No hierarchy arrays
- ❌ No M&A lineage tracking
- ❌ No complex CHECK constraints
- ❌ No enterprise intelligence features
- ❌ No governance/legal tracking

### Complexity Comparison

| Metric | Phase 1 Submission | MVP (Phase 1) | Reduction |
|--------|-------------------|---------------|-----------|
| Migrations | 6 | 1-2 | 70-83% |
| New Columns | 50+ | ~10 | 80% |
| Triggers | 4 | 0 | 100% |
| CHECK Constraints | 18 | 3-5 | 72-83% |
| New Features | Enterprise Intelligence | Contract Sharing | 90% |

---

## Deferred (Phase 2) - Enterprise Enablement

### When
After MVP is merged and SPEC-099/100 are unblocked.

### Requirements for Phase 2
1. **Product Validation** ✅
   - Customer demand verification
   - Roadmap approval
   - Feature prioritization

2. **Feature Flags** ✅
   - `ENTERPRISE_INTELLIGENCE_ENABLED=false` by default
   - Runtime toggles for all enterprise features
   - Per-tenant control (future)

3. **Performance Testing** ✅
   - 10K+ entity datasets
   - Trigger vs recursive CTE benchmarks
   - EXPLAIN ANALYZE validation
   - Deadlock scenario testing

4. **Operational Readiness** ✅
   - Monitoring dashboards
   - Runbook procedures
   - Rollback scripts
   - Backfill automation

5. **Full Documentation** ✅
   - ADR updates
   - Verification checklist evidence
   - Performance test results
   - Architect re-review

### Phase 2 Features (Disabled in MVP)
- 🔒 Provenance tracking and M&A lineage
- 🔒 Hierarchy array propagation
- 🔒 Governance triggers and constraints
- 🔒 Legal/compliance tracking
- 🔒 Intelligence event streaming

---

## Result

### MVP Benefits
- ✅ Achieves original US#79 goal (contract sharing)
- ✅ Unblocks SPEC-099/100 immediately
- ✅ Low risk, simple implementation
- ✅ Fast delivery (2-3 days)
- ✅ Proven pattern, no unknowns

### Enterprise Benefits (Phase 2)
- ✅ Proper product validation
- ✅ Adequate performance testing
- ✅ Feature-flagged rollout
- ✅ Production-ready monitoring
- ✅ Safe, incremental approach

### Risk Mitigation
- 🟢 MVP risk: LOW (minimal scope)
- 🟡 Enterprise risk: MEDIUM (but properly managed)
- ✅ Two-phase approach prevents overcommitment
- ✅ Each phase independently validated
- ✅ Clear decision gates between phases

---

## Migration Strategy

### MVP Migrations (1-2 files)
```python
# Example: 0122_shared_contracts_base.py
def upgrade():
    # Add minimal contract-related columns
    # Basic User-Team-Org relationships
    # Simple foreign keys only
    pass

def downgrade():
    # Clean rollback (tested locally)
    pass
```

### Phase 2 Migrations (4-5 files, future)
```python
# Only created AFTER product validation
# Behind ENTERPRISE_INTELLIGENCE_ENABLED flag
# Full testing and validation required
```

---

## Comparison to Architect Feedback

| Architect Requested | MVP Delivers |
|---------------------|--------------|
| **Simplify scope** | ✅ 70-90% reduction |
| **Stage rollout** | ✅ MVP → Enterprise phases |
| **Validate product demand** | ✅ Required for Phase 2 |
| **Feature flags** | ✅ Scaffolded, disabled |
| **Performance testing** | ✅ Phase 2 only (appropriate) |
| **Rollback safety** | ✅ Simple migrations, tested |

---

## Success Criteria

### MVP Success (Phase 1):
- [ ] Contracts shared across services
- [ ] 1-2 migrations applied successfully
- [ ] No runtime performance impact
- [ ] Feature flags present but disabled
- [ ] Integration tests passing
- [ ] Architect approval received
- [ ] SPEC-099/100 unblocked

### Enterprise Success (Phase 2):
- [ ] Product validation complete
- [ ] Performance tests pass (<25ms latency)
- [ ] 10K+ entity load tests successful
- [ ] Monitoring dashboards operational
- [ ] Rollback rehearsal successful
- [ ] Architect re-approval received
- [ ] Enterprise features enabled

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| **MVP (Phase 1)** | 2-3 days | Architect review only |
| **Phase 2 Planning** | 1-2 days | Product meeting |
| **Phase 2 Implementation** | 2-3 days | Product approval |
| **Phase 2 Testing** | 3-5 days | Implementation complete |
| **Phase 2 Review** | 1-2 days | Testing complete |
| **Total (if enterprise needed)** | 9-15 days | Properly sequenced |

**But SPEC-099/100 unblocked after Phase 1 (2-3 days)** ✅

---

**Document Owner:** Developer C
**Last Updated:** October 24, 2025
**Status:** MVP scope finalized
