# SPEC-124 Deprecation Decision

**Date:** January 2025
**Decision:** **DEPRECATED** - Option A
**Rationale:** Superseded by SPEC-016

---

## Decision Summary

| Decision | Result |
|----------|--------|
| **Framework** | FastAPI only (no Next.js) |
| **Monorepo Orchestration** | Covered by SPEC-016 |
| **SPEC-124 Status** | **DEPRECATED** |
| **Follow-ups** | Archive analysis, update index, close stories |

---

## Rationale

1. **Original purpose obsolete**: Frontend orchestration (Turborepo for Next.js) is no longer relevant
2. **Core pipeline logic covered**: Monorepo build/test/deploy is already handled by SPEC-016
3. **New FastAPI orchestration**: Should fall under SPEC-016 extensions or future SPECs (e.g., SPEC-150 "Service Build Matrix"), rather than reviving SPEC-124
4. **Maintaining obsolete SPECs**: Creates confusion in the index and audit trail

---

## Architectural Context

### Old Assumption (SPEC-124, now obsolete):
- **Frontend stack**: Next.js (customer/admin)
- **Workspace orchestration**: via Turborepo (turbo.json, caching, parallel pipelines)
- **Directory structure**:
  ```
  frontend-shared/
  frontend-nextjs-customer/
  frontend-nextjs-admin/
  ```
- **Tight coupling**: with SPEC-121/122/123 (all deprecated)

### New Reality:
- **Frontend strategy dropped**: No active Next.js layer
- **Unified FastAPI**: Handles both frontend rendering (templating/UI) and backend APIs
- **CI/CD handled entirely under SPEC-016**, which already:
  - Manages multi-service builds (nv-api, nv-redis, nv-db, rust memory provider, etc.)
  - Has 28 validated workflows
  - Provides caching, parallelization, lint/test/build stages
  - Works with Apple Container CLI + GitHub Actions instead of Turborepo

**Conclusion**: The purpose of SPEC-124 (Turborepo orchestration) has been fully absorbed into SPEC-016 and is functionally redundant.

---

## Proposed SPEC Entry Update

| SPEC | Title | Status | Notes |
|------|-------|--------|-------|
| **124** | Unified Workspace / Turborepo CI/CD | **DEPRECATED** | Superseded by SPEC-016 (CI/CD Pipeline Architecture). Next.js stack discontinued; FastAPI now primary. |

**Replaced By**: SPEC-016 - All CI/CD, caching, and workflow automation covered there.

---

## Follow-up Actions Completed

✅ **1. Mark SPEC-124 as Deprecated**
   - Updated `specs/124-unified-workspace-cicd/README.md` header with deprecation notice
   - Added deprecation rationale section

✅ **2. Tag SPEC_INDEX.md entry**
   - Updated SPEC-124 entry to `Deprecated` (not `Not Implemented`)

✅ **3. Archive analysis files**
   - Moved to `docs/spec-archive/124/`:
     - `SPEC_124_COMPREHENSIVE_ANALYSIS.md`
     - `SPEC_124_REVIEW_SUMMARY.md`
     - `DEPRECATION_DECISION.md` (this file)

⏳ **4. Close dependent stories (if exist)**
   - US#79 and US#596 should be marked as "Obsolete — superseded by SPEC-016"
   - **Note**: Stories need verification in Taiga

✅ **5. Link forward**
   - Added historical note to SPEC-016: "Historical note: SPEC-124 (Turborepo) deprecated after FastAPI migration, November 2025."

---

## Decision Options Considered

### Option A - Deprecate SPEC-124 ✅ **SELECTED**
- **Description**: Officially mark as deprecated; rely entirely on SPEC-016 for CI/CD
- **Pros**:
  - ✔ Removes redundancy
  - ✔ Reflects current FastAPI architecture
  - ✔ Simplifies SPEC index
- **Cons**:
  - ❌ Loses "monorepo workspace orchestration" documentation unless extracted elsewhere

### Option B - Revise SPEC-124 ❌ **REJECTED**
- **Description**: Repurpose SPEC-124 to describe "Unified FastAPI Workspace Build & Release Orchestration"
- **Pros**:
  - ✔ Preserves numbering and continuity
  - ✔ Could define how multiple FastAPI modules are built and versioned
- **Cons**:
  - ⚠ Requires rewriting entire spec!
  - ⚠ May overlap with SPEC-016 again

---

## Status

**Decision**: ✅ **DEPRECATED**
**Date**: January 2025
**Replaced By**: SPEC-016 (CI/CD Pipeline Architecture)
