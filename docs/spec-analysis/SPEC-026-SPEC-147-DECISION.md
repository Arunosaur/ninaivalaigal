# SPEC-026 vs SPEC-147: Decision & Implementation Plan

**Date**: January 2025
**Decision Maker**: Developer D
**Status**: ✅ **DECISION FINALIZED**

---

## 🎯 Decision Summary

**SPEC-026**: Partially deprecated - billing schema portions deprecated, unique features preserved
**SPEC-147**: Primary billing architecture - use for all billing infrastructure

### Key Decisions

1. ✅ **Use SPEC-147's unified billing schema** for all billing infrastructure
2. ✅ **Preserve SPEC-026's unique features** (standalone teams, non-profit apps)
3. ✅ **Integrate SPEC-026 features** into SPEC-147 implementation
4. ✅ **Update documentation** to reflect deprecation

---

## 📋 Implementation Actions

### ✅ Completed

- [x] Created comparison document (SPEC-026-vs-SPEC-147-COMPARISON.md)
- [x] Updated SPEC-026 spec.md with deprecation notice
- [x] Updated SPEC_INDEX.md with deprecation note
- [x] Added SPEC-147 to SPEC_INDEX.md

### 🔄 In Progress

- [ ] Review and consolidate Taiga stories
- [ ] Assign SPEC-147 stories to Developer D
- [ ] Begin SPEC-147 implementation

### ⏳ Pending

- [ ] Add non-profit application tables to SPEC-147 schema
- [ ] Update SPEC-147 to support standalone teams
- [ ] Close duplicate SPEC-026 billing stories
- [ ] Create SPEC-026-specific feature stories

---

## 📊 Taiga Story Status

### SPEC-026 Stories (17 stories: #156-#172)
**Status**: ⚠️ **NEEDS REVIEW**

**Billing Infrastructure Stories** (Should use SPEC-147):
- #156: Team Billing Schema Design → **Close/Deprecate** (use SPEC-147)
- #160: Team Billing APIs → **Update** to use SPEC-147 infrastructure
- #163: Stripe Customer Management → **Update** to use SPEC-147
- #164: Stripe Subscription Handling → **Update** to use SPEC-147

**Unique Feature Stories** (Preserve):
- #158: Non-Profit Application System Schema → **Keep**
- #159: Standalone Team CRUD APIs → **Keep**
- #161: Discount & Credit APIs → **Update** to use SPEC-147 billing_accounts

### SPEC-147 Stories (15 stories: BILL-001 to BILL-015)
**Status**: ✅ **DEFINED** - Ready for implementation

**All stories** should be assigned to **Developer D** and implemented using SPEC-147 architecture.

---

## 🚀 Next Steps

### Immediate (This Week)
1. **Review Taiga Stories**
   - Review SPEC-026 stories #156-#172
   - Identify duplicates with SPEC-147
   - Close/update duplicate stories
   - Preserve unique SPEC-026 features

2. **Assign SPEC-147 Stories**
   - Assign BILL-001 to BILL-015 to Developer D
   - Set priority levels
   - Create sprint plan

3. **Begin Implementation**
   - Start with BILL-001: Core Billing Data Models
   - Follow SPEC-147 architecture
   - Integrate SPEC-026 unique features

### Short-Term (Next 2 Weeks)
1. **Schema Integration**
   - Add non-profit application tables
   - Ensure standalone teams work with billing_accounts
   - Test polymorphic billing

2. **Feature Integration**
   - Preserve standalone team creation
   - Integrate non-profit workflow
   - Implement team upgrade path

---

## ✅ Approval

- [x] Analysis Complete
- [x] Decision Documented
- [x] Documentation Updated
- [ ] Taiga Stories Reviewed
- [ ] Developer D Assigned
- [ ] Implementation Started

---

**Status**: ✅ **DECISION COMPLETE** - Ready for Implementation
**Next Step**: Review Taiga stories and assign to Developer D
**Timeline**: Begin implementation immediately
