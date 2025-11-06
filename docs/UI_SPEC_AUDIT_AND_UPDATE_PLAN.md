# UI SPEC Audit and Update Plan

**Date:** 2025-11-02
**Developer:** Developer F
**Purpose:** Audit and update all UI-related SPECs and Taiga stories to reflect FastAPI templating direction (not Next.js)

---

## Executive Summary

After analysis, we've decided to use **FastAPI + Jinja2 templates** for both customer-facing and admin/internal UI instead of Next.js. This audit identifies all SPECs and Taiga stories that need updates to reflect this architectural decision.

---

## Key UI-Related SPECs Identified

### Critical SPECs (Need Major Updates)

1. **SPEC-005: Admin Dashboard** ⚠️
   - **Current:** Mentions React 18, React Router, React Query
   - **Update:** Change to FastAPI + Jinja2 templates
   - **File:** `specs/005-admin-dashboard/spec.md`

2. **SPEC-116: Internal Frontend Migration** ⚠️
   - **Current:** Entirely about Next.js split (frontend-nextjs-admin, frontend-nextjs-customer)
   - **Update:** Change to FastAPI templating approach
   - **File:** `specs/116-internal-frontend-migration/README.md`
   - **Status:** Mark as DEPRECATED or update to FastAPI

3. **SPEC-122: Customer Frontend Rollout** ⚠️
   - **Current:** Next.js 15 + Vercel deployment
   - **Update:** FastAPI templates + static hosting or FastAPI serving
   - **File:** `specs/122-customer-frontend-rollout/README.md`

4. **SPEC-123: Admin Frontend Rollout** ⚠️
   - **Current:** Next.js admin app + internal server deployment
   - **Update:** FastAPI templates + internal FastAPI routes
   - **File:** `specs/123-admin-frontend-rollout/README.md`

5. **SPEC-121: Frontend Shared Library** ⚠️
   - **Current:** React components library for Next.js
   - **Update:** Mark as DEPRECATED or change to Jinja2 macros/partials
   - **File:** `specs/121-frontend-shared-library/README.md`

6. **SPEC-103: Next.js 15 Bootstrap** ⚠️
   - **Current:** Next.js 15 setup and migration
   - **Update:** Add deprecation notice, redirect to FastAPI templating
   - **File:** `specs/103-nextjs-15-bootstrap/README.md`

### Secondary SPECs (May Need Updates)

7. **SPEC-068: Comprehensive UI Suite**
   - Check if it mentions Next.js
   - **File:** `specs/068-comprehensive-ui-suite/README.md`

8. **SPEC-102: Frontend Migration Preparation**
   - Check if it mentions Next.js migration
   - **File:** `specs/102-frontend-migration-preparation/README.md`

9. **SPEC-113: Profile Settings Pages**
   - Check if it assumes Next.js
   - **File:** `specs/113-profile-settings-pages/README.md`

10. **SPEC-075: Unified Frontend Architecture**
    - Check alignment with new direction
    - **File:** `specs/075-unified-frontend-architecture/README.md`

---

## Update Strategy

### For Each SPEC

1. **Add Deprecation Notice** (if Next.js-focused)
   ```markdown
   > **⚠️ DEPRECATED:** This SPEC described a Next.js implementation approach.
   > **Current Direction:** We use FastAPI + Jinja2 templates for all UI.
   > **See:** `docs/FRONTEND_ARCHITECTURE_DECISION.md` and `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`
   ```

2. **Update Technology Stack Sections**
   - Replace: React/Next.js/TypeScript
   - With: FastAPI + Jinja2 + TailwindCSS + Alpine.js

3. **Update Implementation Examples**
   - Replace React/Next.js code examples
   - With FastAPI router + Jinja2 template examples

4. **Update Architecture Diagrams**
   - Remove Next.js/Vercel deployment
   - Show FastAPI serving templates directly

5. **Update References**
   - Point to FastAPI templating docs
   - Remove references to Next.js bootstrap

---

## SPEC Update Checklist

### SPEC-005: Admin Dashboard
- [ ] Update "Frontend Implementation" section
- [ ] Change React/TypeScript to Jinja2 templates
- [ ] Update component examples to Jinja2 macros
- [ ] Update deployment from React SPA to FastAPI routes
- [ ] Add reference to `docs/ADMIN_UI_FASTAPI_ANALYSIS.md`

### SPEC-116: Internal Frontend Migration
- [ ] Add deprecation notice at top
- [ ] Update architecture diagram (remove Next.js apps)
- [ ] Change to FastAPI templating approach
- [ ] Update deployment strategy
- [ ] Mark as "Superseded by FastAPI templating approach"

### SPEC-122: Customer Frontend Rollout
- [ ] Change from Next.js + Vercel to FastAPI templates
- [ ] Update deployment configuration
- [ ] Remove NextAuth.js references
- [ ] Update to FastAPI JWT authentication

### SPEC-123: Admin Frontend Rollout
- [ ] Change from Next.js + PM2 to FastAPI routes
- [ ] Update nginx configuration (remove Next.js proxy)
- [ ] Update IP whitelist to FastAPI middleware
- [ ] Remove PM2 ecosystem config

### SPEC-121: Frontend Shared Library
- [ ] Add deprecation notice
- [ ] Change from React components to Jinja2 macros/partials
- [ ] Update package.json examples
- [ ] Mark as "Not needed with FastAPI templating"

### SPEC-103: Next.js 15 Bootstrap
- [ ] Add deprecation notice at top
- [ ] Redirect to FastAPI templating approach
- [ ] Keep as historical reference but mark deprecated

---

## Taiga Stories to Update

### Stories Mentioning Next.js

Need to search Taiga for stories that mention:
- Next.js
- NextJS
- frontend-nextjs
- React SPA
- Vercel deployment
- Customer app
- Admin app

### Update Pattern for Taiga Stories

1. **Add Comment/Note** to story description:
   ```
   ⚠️ ARCHITECTURE UPDATE (2025-11-02):
   This story originally described a Next.js implementation.
   Current direction: FastAPI + Jinja2 templates.
   See: docs/FRONTEND_ARCHITECTURE_DECISION.md
   ```

2. **Update Story Status** if needed (mark as "Needs Review")

3. **Update Acceptance Criteria** to reflect FastAPI templating

---

## Implementation Plan

### Phase 1: Documentation Updates (Today)
1. Update SPEC-005 (Admin Dashboard)
2. Update SPEC-116 (Internal Frontend Migration) - add deprecation
3. Update SPEC-122 (Customer Frontend Rollout)
4. Update SPEC-123 (Admin Frontend Rollout)
5. Update SPEC-121 (Shared Library) - deprecate
6. Update SPEC-103 (Next.js Bootstrap) - deprecate

### Phase 2: Secondary SPECs Review (Today)
1. Review SPEC-068, SPEC-102, SPEC-113, SPEC-075
2. Update if they mention Next.js
3. Add references to new architecture docs

### Phase 3: Taiga Stories Audit (Today)
1. Search Taiga for UI-related stories
2. Identify stories mentioning Next.js
3. Add comments/notes to relevant stories
4. Update story descriptions if critical

### Phase 4: Create Summary Document
1. Document all changes made
2. Create migration guide for developers
3. Update SPEC_INDEX.md if needed

---

## Files to Create/Update

### New Documentation
- ✅ `docs/ADMIN_UI_FASTAPI_ANALYSIS.md` (already created)
- `docs/UI_SPEC_MIGRATION_SUMMARY.md` (summary of all updates)

### SPECs to Update
- `specs/005-admin-dashboard/spec.md`
- `specs/116-internal-frontend-migration/README.md`
- `specs/122-customer-frontend-rollout/README.md`
- `specs/123-admin-frontend-rollout/README.md`
- `specs/121-frontend-shared-library/README.md`
- `specs/103-nextjs-15-bootstrap/README.md`
- `specs/068-comprehensive-ui-suite/README.md` (if needed)
- `specs/102-frontend-migration-preparation/README.md` (if needed)
- `specs/113-profile-settings-pages/README.md` (if needed)
- `specs/075-unified-frontend-architecture/README.md` (if needed)

---

## Success Criteria

- [ ] All UI-related SPECs updated or deprecated
- [ ] No misleading Next.js references in active SPECs
- [ ] All Taiga stories updated with architecture notes
- [ ] Clear migration path documented
- [ ] Developers know to use FastAPI templating

---

**Status:** 🔄 In Progress
**Next Steps:** Begin updating SPECs systematically
