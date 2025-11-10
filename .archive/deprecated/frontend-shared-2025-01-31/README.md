# frontend-shared/ - DEPRECATED

**Deprecated Date**: 2025-01-31
**Deprecated By**: Developer F
**Reason**: SPEC-121 (Frontend Shared Library) is DEPRECATED, only used by archived Next.js apps

---

## Deprecation Details

**Original Purpose**: React component library (`@ninaivalaigal/ui-components`) for Next.js apps

**Replaced By**: Jinja2 macros and partials (FastAPI templating approach)

**Current Direction**: FastAPI + Jinja2 templates. Shared components are Jinja2 macros/partials, not React components.

---

## SPEC References

- **SPEC-121**: Frontend Shared Library
  - **Status**: 🔴 DEPRECATED (2025-11-02)
  - **File**: `specs/121-frontend-shared-library/README.md`
  - **Reason**: React component library no longer needed with FastAPI templating

**Replacement SPECs**:
- **SPEC-005**: Admin Dashboard (FastAPI templating)
- **SPEC-146**: Customer UI (FastAPI templating)

---

## Migration Path

**If you need shared components:**
- Use Jinja2 macros in `templates/_partials/`
- Use Alpine.js for client-side interactivity
- Use TailwindCSS for styling

**If you need component library:**
- Create Jinja2 template macros instead of React components
- Use template inheritance for shared patterns

---

## Usage Status

**Was Used By**: `frontend-nextjs-customer/` (now archived)
**Not Used By**: `apps/customer/` (active Vite app doesn't use it)

**Status**: ✅ Safe to archive - no active dependencies

---

## Archive Location

This folder was moved from: `frontend-shared/`
To: `.archive/deprecated/frontend-shared-2025-01-31/`

**Original Size**: ~71 files

---

**Status**: ✅ Archived - Do not use for new development
