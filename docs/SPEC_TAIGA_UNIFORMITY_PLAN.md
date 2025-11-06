# SPEC & Taiga Uniformity Plan
## Ensuring Cohesive UI Architecture Across All Documentation

**Date:** 2025-11-02
**Status:** 🔴 **IN PROGRESS** - Comprehensive audit and update plan
**Goal:** Ensure all SPECs and Taiga stories reflect the unified FastAPI + Jinja2 architecture decision

---

## Executive Summary

**Problem:** Despite clear architectural decisions (FastAPI + Jinja2 with optional React micro-widgets), there are inconsistencies across:
- SPEC documentation (some updated, some not)
- Taiga stories (may reference deprecated Next.js approach)
- SPEC_INDEX.md (deprecation status unclear)
- Cross-references between SPECs

**Solution:** Systematic audit and update of all UI-related SPECs and Taiga stories to reflect the current architecture.

**Decision Baseline (from images provided):**
- **Primary Stack:** FastAPI + Jinja2 (server-rendered templates)
- **Optional Enhancement:** React micro-widgets (Vite-built) for complex visualizations only
- **No standalone SPAs:** No Next.js, no separate React apps
- **Uniformity:** Single design system, single interaction contract, single API shape

---

## My Assessment: Stack Shifting

### The Honest Truth

**You're right to be concerned.** Constant stack shifting is problematic for several reasons:

#### 1. **Technical Debt Accumulation**
- Each shift leaves legacy code that needs maintenance or migration
- Developers waste time on deprecated code paths
- Documentation becomes inconsistent and confusing

#### 2. **Team Confusion**
- New developers don't know which stack to use
- Existing developers waste time on the wrong approach
- Inconsistent patterns across the codebase

#### 3. **Velocity Impact**
- Repeated rework instead of building features
- Time spent on migration instead of value delivery
- Context switching costs

#### 4. **But... The Decision is Sound**

**However**, the **current decision (FastAPI + Jinja2)** appears to be the right choice for your context:

✅ **Aligns with your team:** Backend-heavy Python/FastAPI expertise
✅ **Simplifies ops:** Single deployment, no Node.js build pipeline
✅ **Reduces complexity:** No CORS, no separate frontend hosting
✅ **Future-proof escape hatch:** React widgets when truly needed
✅ **SPEC-005 compliance:** Already documented and authoritative

**The problem isn't the decision—it's the inconsistent execution.**

---

## Comprehensive Audit Results

### SPECs Requiring Updates

#### ✅ Already Updated (4 SPECs)
1. **SPEC-005** - Admin Dashboard
   - ✅ Updated to FastAPI + Jinja2 (2025-11-02)
   - ✅ Status: Complete
   - ⚠️ **Action:** Verify Taiga stories align

2. **SPEC-103** - Next.js 15 Bootstrap
   - ✅ Deprecated notice added (2025-11-02)
   - ✅ Status: Deprecated (in SPEC_INDEX.md)
   - ⚠️ **Action:** Verify Taiga stories marked deprecated

3. **SPEC-102** - Frontend Migration Preparation
   - ✅ Deprecated notice added (2025-11-02)
   - ✅ Status: Deprecated (in SPEC_INDEX.md)
   - ⚠️ **Action:** Verify Taiga stories marked deprecated

4. **SPEC-124** - Unified Workspace & CI/CD
   - ✅ Deprecated notice added (November 2025)
   - ✅ Status: Deprecated (in SPEC_INDEX.md)
   - ✅ Replaced by: SPEC-016

#### ⚠️ Needs Update (4 SPECs)
5. **SPEC-116** - Internal Frontend Migration
   - ⚠️ **Status:** Deprecated notice exists but needs verification
   - ⚠️ **Issue:** Still references Next.js split architecture
   - **Action Required:**
     - [ ] Verify deprecation notice is prominent
     - [ ] Update cross-references
     - [ ] Check Taiga stories

6. **SPEC-121** - Frontend Shared Library
   - ⚠️ **Status:** Deprecated notice exists (2025-11-02)
   - ⚠️ **Issue:** Still describes React component library
   - **Action Required:**
     - [ ] Verify deprecation notice clarity
     - [ ] Update to reference Jinja2 macros/partials
     - [ ] Check Taiga stories

7. **SPEC-122** - Customer Frontend Rollout
   - ⚠️ **Status:** Deprecated notice exists (2025-11-02)
   - ⚠️ **Issue:** Still describes Vercel/Next.js deployment
   - **Action Required:**
     - [ ] Verify deprecation notice clarity
     - [ ] Update to reference SPEC-146 (Customer UI)
     - [ ] Check Taiga stories (US#101 mentioned)

8. **SPEC-123** - Admin Frontend Rollout
   - ⚠️ **Status:** Deprecated notice exists (2025-11-02)
   - ⚠️ **Issue:** Still describes Next.js admin app
   - **Action Required:**
     - [ ] Verify deprecation notice clarity
     - [ ] Update to reference SPEC-005 (Admin Dashboard)
     - [ ] Check Taiga stories

#### 🔍 Needs Verification (5 SPECs)
9. **SPEC-068** - Comprehensive UI Suite
   - ⚠️ **Status:** Unknown - needs verification
   - **Action Required:**
     - [ ] Read SPEC-068 README
     - [ ] Check for Next.js references
     - [ ] Update if needed

10. **SPEC-075** - Unified Frontend Architecture
    - ⚠️ **Status:** Unknown - needs verification
    - **Action Required:**
      - [ ] Read SPEC-075 README
      - [ ] Verify alignment with FastAPI + Jinja2
      - [ ] Update if needed

11. **SPEC-113** - Profile & Settings Pages
    - ⚠️ **Status:** Complete (per SPEC_INDEX.md)
    - **Action Required:**
      - [ ] Verify implementation uses FastAPI + Jinja2
      - [ ] Update if it references Next.js

12. **SPEC-114** - Auth & Security Integration
    - ⚠️ **Status:** Complete (per SPEC_INDEX.md)
    - **Action Required:**
      - [ ] Verify auth patterns work with FastAPI templates
      - [ ] Update if it references Next.js auth

13. **SPEC-115** - Real-Time Features (WebSocket/SSE)
    - ⚠️ **Status:** In Progress (40%)
    - **Action Required:**
      - [ ] Verify implementation uses FastAPI SSE
      - [ ] Update if it references Next.js real-time

---

## SPEC_INDEX.md Updates Required

### Current Status in SPEC_INDEX.md

| SPEC | Index Status | Actual Status | Action |
|------|--------------|----------------|--------|
| 005 | Complete | ✅ Updated | Verify |
| 102 | (not listed) | Deprecated | Add deprecation note |
| 103 | Complete | Deprecated | Update to Deprecated |
| 116 | Deprecated | Deprecated | ✅ Correct |
| 121 | Deprecated | Deprecated | ✅ Correct |
| 122 | Deprecated | Deprecated | ✅ Correct |
| 123 | Deprecated | Deprecated | ✅ Correct |
| 124 | Deprecated | Deprecated | ✅ Correct |

**Action Required:**
- [ ] Update SPEC-103 status in SPEC_INDEX.md to "Deprecated"
- [ ] Add SPEC-102 to SPEC_INDEX.md with "Deprecated" status
- [ ] Verify all deprecation notices point to replacement SPECs

---

## Taiga Stories Audit

### Stories Requiring Updates

#### SPEC-005 Stories (5 stories)
- **US#110**: US-98 - Admin User Management API (P0)
- **US#111**: US-99 - Admin UI Integration & Polish (P0)
- **US#112**: US-100 - Admin Activity Logging System (P0)
- **US#113**: US-101 - Context Admin Management API (P1)
- **US#114**: US-102 - System Dashboard & Monitoring (P1)

**Action Required:**
- [ ] Verify all stories reference FastAPI + Jinja2 (not React)
- [ ] Update story descriptions if they mention Next.js/React
- [ ] Add tags: `fastapi`, `jinja2`, `templates`

#### SPEC-116 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-116
  - [ ] Mark as deprecated or update to FastAPI approach
  - [ ] Add deprecation notice to story descriptions

#### SPEC-121 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-121
  - [ ] Mark as deprecated or update to Jinja2 macros
  - [ ] Add deprecation notice to story descriptions

#### SPEC-122 Stories
- **US#101**: US-89 - Customer UI Auth Integration (P0)
  - **Action Required:**
    - [ ] Update to reference FastAPI templating
    - [ ] Remove Next.js/Vercel references
    - [ ] Update to reference SPEC-146 if applicable

#### SPEC-123 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-123
  - [ ] Mark as deprecated or update to FastAPI approach
  - [ ] Point to SPEC-005 replacement

#### SPEC-103 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-103
  - [ ] Mark as deprecated
  - [ ] Add deprecation notice

#### SPEC-102 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-102
  - [ ] Mark as deprecated
  - [ ] Add deprecation notice

#### SPEC-124 Stories (if any)
- **Action Required:**
  - [ ] Find all stories linked to SPEC-124
  - [ ] Mark as deprecated
  - [ ] Point to SPEC-016 replacement

---

## Implementation Plan

### Phase 1: SPEC Audit & Update (Day 1-2)

#### Task 1.1: Verify SPEC-116, 121, 122, 123
- [ ] Read each SPEC README fully
- [ ] Verify deprecation notices are prominent
- [ ] Update cross-references to replacement SPECs
- [ ] Ensure consistency with SPEC-005 approach

#### Task 1.2: Verify SPEC-068, 075, 113, 114, 115
- [ ] Read each SPEC README
- [ ] Check for Next.js/React references
- [ ] Update to FastAPI + Jinja2 if needed
- [ ] Add deprecation notices if applicable

#### Task 1.3: Update SPEC_INDEX.md
- [ ] Update SPEC-103 status to "Deprecated"
- [ ] Add SPEC-102 entry with "Deprecated" status
- [ ] Verify all deprecation notices include replacement SPEC
- [ ] Add notes column for deprecated SPECs

### Phase 2: Taiga Stories Audit (Day 2-3)

#### Task 2.1: Query Taiga API
- [ ] Get all stories with tags: `spec-005`, `spec-116`, `spec-121`, `spec-122`, `spec-123`, `spec-103`, `spec-102`, `spec-124`
- [ ] Export story list with descriptions
- [ ] Identify stories needing updates

#### Task 2.2: Update Story Descriptions
- [ ] Update SPEC-005 stories (US#110-114) to reference FastAPI + Jinja2
- [ ] Add deprecation notices to SPEC-116, 121, 122, 123, 103, 102, 124 stories
- [ ] Update tags (remove `nextjs`, add `fastapi`, `jinja2`, `deprecated`)
- [ ] Link deprecated stories to replacement SPECs

#### Task 2.3: Create New Stories (if needed)
- [ ] Create stories for SPEC-146 (Customer UI) if it exists
- [ ] Ensure new stories follow FastAPI + Jinja2 pattern

### Phase 3: Cross-Reference Verification (Day 3-4)

#### Task 3.1: Check All SPEC Cross-References
- [ ] Search for references to SPEC-116, 121, 122, 123, 103, 102, 124 in other SPECs
- [ ] Update cross-references to point to replacement SPECs
- [ ] Add deprecation warnings where appropriate

#### Task 3.2: Update Documentation Indexes
- [ ] Update `docs/UI_SPEC_AUDIT_AND_UPDATE_PLAN.md` (this document)
- [ ] Update `docs/FRONTEND_ARCHITECTURE_DECISION.md` if it exists
- [ ] Update `docs/ADMIN_UI_FASTAPI_ANALYSIS.md` if it exists
- [ ] Ensure all docs reference the same architecture

### Phase 4: Verification & Closure (Day 4-5)

#### Task 4.1: Final Verification
- [ ] Verify all SPECs have consistent messaging
- [ ] Verify all Taiga stories align with current architecture
- [ ] Verify SPEC_INDEX.md is accurate
- [ ] Verify cross-references are correct

#### Task 4.2: Create Summary Report
- [ ] Document all changes made
- [ ] List SPECs updated
- [ ] List Taiga stories updated
- [ ] Create verification checklist

---

## Uniformity Standards

### SPEC Documentation Standards

#### For Deprecated SPECs
```markdown
> **⚠️ DEPRECATED (YYYY-MM-DD):**
> **This SPEC is DEPRECATED** - [Brief reason].
> **Current Direction:** [Current approach].
> **See:** `docs/[relevant-doc].md` for current architecture.
>
> **Replacement:** SPEC-XXX [Title]
```

#### For Active SPECs
- Must reference FastAPI + Jinja2 as primary stack
- Optional React widgets must be clearly marked as "exception"
- Must reference SPEC-005 for admin UI patterns
- Must reference SPEC-146 (or equivalent) for customer UI patterns

### Taiga Story Standards

#### For Deprecated Stories
- **Subject:** `SPEC-XXX: [Title] (DEPRECATED)`
- **Tags:** `spec-XXX`, `deprecated`, `fastapi`, `jinja2`
- **Description:** Include deprecation notice and replacement reference
- **Status:** Mark as "Done" or "Archived" if work completed, "Cancelled" if not started

#### For Active Stories
- **Subject:** `SPEC-XXX: [Title]`
- **Tags:** `spec-XXX`, `fastapi`, `jinja2`, `templates` (or `react-widget` if applicable)
- **Description:** Must reference FastAPI + Jinja2 approach
- **Status:** Active status (New, Ready, In Progress)

---

## Success Criteria

### SPEC Uniformity
- ✅ All UI-related SPECs reference FastAPI + Jinja2
- ✅ All deprecated SPECs have prominent deprecation notices
- ✅ All cross-references point to current SPECs
- ✅ SPEC_INDEX.md accurately reflects all statuses

### Taiga Story Uniformity
- ✅ All active UI stories reference FastAPI + Jinja2
- ✅ All deprecated stories have deprecation notices
- ✅ All stories have correct tags
- ✅ All stories link to correct SPECs

### Documentation Consistency
- ✅ All docs reference the same architecture
- ✅ No conflicting information between SPECs
- ✅ Clear migration path from deprecated to current approach

---

## Risk Mitigation

### Risk 1: Incomplete Update
**Mitigation:**
- Systematic checklist approach
- Verification step for each phase
- Final audit before closure

### Risk 2: Breaking Existing Work
**Mitigation:**
- Only update documentation, not code
- Mark deprecated items clearly
- Preserve historical context

### Risk 3: Team Confusion During Update
**Mitigation:**
- Communicate changes clearly
- Update all references simultaneously
- Create summary document

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Begin SPEC audit and updates
3. **Execute systematically** - Follow checklist methodically
4. **Verify completion** - Ensure all items addressed
5. **Document results** - Create summary report

---

## Related Documents

- `docs/FRONTEND_ARCHITECTURE_DECISION.md` - Customer UI decision
- `docs/ADMIN_UI_FASTAPI_ANALYSIS.md` - Admin UI analysis
- `specs/005-admin-dashboard/spec.md` - Authoritative SPEC-005
- `specs/SPEC_INDEX.md` - Master SPEC index

---

**Status:** Ready for execution
**Priority:** P0 - Blocks architectural clarity
**Estimated Effort:** 4-5 days
