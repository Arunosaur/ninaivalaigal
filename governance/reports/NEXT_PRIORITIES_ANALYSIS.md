# Next Priorities Analysis

**Date**: November 1, 2025
**Status**: Analysis of Next Pressing Work

---

## 📊 Summary

Completed US#237-242 (SPEC-027/028 Refactoring). Analysis of next most pressing stories based on codebase and governance reports.

---

## 🔴 Critical Priorities (P0)

### 1. US#117: ORM Guardrails & Multi-Tenant Isolation
**Priority**: P0 - CRITICAL SECURITY
**Risk**: HIGH - Potential cross-org data leaks
**Impact**: Multi-tenant SaaS security requirement
**Status**: Needs to be created in Taiga or assigned if exists

**Description**:
- Database-level access controls
- Automatic query filtering by organization
- Prevent cross-org data leaks
- **HIGHEST PRIORITY - START IMMEDIATELY**

**Effort**: 4 days

---

### 2. US#20: User Signup with bcrypt
**Priority**: P0 - BLOCKING PRODUCTION
**Status**: Needs to be created/assigned in Taiga

**Description**:
- Complete user signup flow
- Password hashing with bcrypt
- **BLOCKS EVERYTHING** - Users cannot sign up without this

**Effort**: 4-6 hours

---

### 3. US#21: User Login with Password Verification
**Priority**: P0 - BLOCKING PRODUCTION
**Status**: Needs to be created/assigned in Taiga

**Description**:
- User login flow
- Password verification
- JWT token generation
- **BLOCKS EVERYTHING** - Users cannot log in without this

**Effort**: 4-6 hours

---

### 4. Rate Limiting Implementation
**Priority**: P0 - SECURITY
**Status**: Needs to be created in Taiga

**Description**:
- API rate limiting
- Security hardening
- Prevents abuse

**Effort**: 2 days

---

## 🟡 High Priorities (P1)

### 5. US#243: Remove Legacy Code (After Refactoring Validation)
**Priority**: P1 - TECHNICAL DEBT
**Status**: Next step after US#237-242 validation

**Description**:
- Remove deprecated functions (generate_invoice_pdf, create_pdf_invoice)
- Remove legacy tax calculation code
- Remove feature flag code after migration
- Clean up codebase

**Effort**: 2-3 hours
**Dependencies**: US#241 (PDF validation) must pass first

---

### 6. US#291-293: Governance Quick-Wins (If Not Done)
**Priority**: P1 - GOVERNANCE
**Status**: May already be completed (US#291-293 created in previous session)

**Description**:
- US#291: Deprecate SPEC-049 & SPEC-050
- US#292: Verify SPEC-014 vs SPEC-006 boundaries
- US#293: Standardize status terms

**Effort**: 2.5 hours total

---

## 📋 Recommended Action Plan

### Immediate Next Steps (This Week)

1. **Check if critical stories exist in Taiga**:
   - US#117 (ORM Guardrails)
   - US#20 (User Signup)
   - US#21 (User Login)
   - Rate Limiting story

2. **Create missing stories** if they don't exist

3. **Assign and start**:
   - Start with US#117 (Security) or US#20/21 (Production blockers)
   - Depends on current production readiness status

4. **After validation**:
   - Complete US#243 (Remove legacy code)
   - Only after US#241 validation passes

---

## 🎯 Priority Ranking

| Priority | Story | Effort | Impact | Blocking |
|----------|-------|--------|--------|----------|
| 🔴 P0 | US#117: ORM Guardrails | 4d | Critical | Security |
| 🔴 P0 | US#20: User Signup | 4-6h | Critical | Production |
| 🔴 P0 | US#21: User Login | 4-6h | Critical | Production |
| 🔴 P0 | Rate Limiting | 2d | High | Security |
| 🟡 P1 | US#243: Remove Legacy Code | 2-3h | Medium | After validation |
| 🟡 P1 | US#291-293: Governance | 2.5h | Low | Documentation |

---

## ✅ Completed Work (US#237-242)

All SPEC-027/028 refactoring stories are complete:
- ✅ US#237: Shared InvoicingService created
- ✅ US#238: Shared TaxCalculator created
- ✅ US#239: SPEC-027 refactored
- ✅ US#240: SPEC-028 refactored
- ✅ US#241: PDF comparison script created
- ✅ US#242: Test suite complete (90+ tests)

**Next**: Run validation (US#241) before removing legacy code (US#243)

---

## 📝 Notes

- Many critical stories may need to be created in Taiga
- Production blockers (US#20, US#21) should be verified against current auth implementation
- Security stories (US#117, Rate Limiting) are highest priority for multi-tenant SaaS
- Refactoring work (US#237-242) is complete and ready for validation
