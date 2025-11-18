# frontend-nextjs/ - DEPRECATED

**Deprecated Date**: 2025-01-31
**Deprecated By**: Developer F
**Reason**: SPEC-103 (Next.js 15 Bootstrap) is DEPRECATED

---

## Deprecation Details

**Original Purpose**: Next.js 15 bootstrap project for component library and Storybook setup

**Replaced By**: FastAPI + Jinja2 templates (server-side rendering)

**Current Direction**: FastAPI + Jinja2 + TailwindCSS + Alpine.js (per `docs/UI_SPEC_AUDIT_AND_UPDATE_PLAN.md`)

---

## SPEC References

- **SPEC-103**: Next.js 15 Bootstrap
  - **Status**: 🔴 DEPRECATED (2025-11-02)
  - **File**: `specs/103-nextjs-15-bootstrap/README.md`
  - **Reason**: Next.js no longer the direction, replaced by FastAPI templating

---

## Migration Path

**If you need component functionality:**
- Use Jinja2 macros in `templates/_partials/`
- Use Alpine.js for client-side interactivity
- Use TailwindCSS for styling

**If you need Storybook:**
- Consider Jinja2 template examples instead
- Or use Storybook for React micro-widgets only (if needed)

---

## Archive Location

This folder was moved from: `frontend-nextjs/`
To: `.archive/deprecated/frontend-nextjs-2025-01-31/`

**Original Size**: ~74 files

---

**Status**: ✅ Archived - Do not use for new development




