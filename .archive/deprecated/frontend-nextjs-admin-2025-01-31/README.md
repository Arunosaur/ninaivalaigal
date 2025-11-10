# frontend-nextjs-admin/ - DEPRECATED

**Deprecated Date**: 2025-01-31
**Deprecated By**: Developer F
**Reason**: SPEC-123 (Admin Frontend Rollout) is DEPRECATED

---

## Deprecation Details

**Original Purpose**: Next.js admin application for internal use

**Replaced By**: FastAPI + Jinja2 templates (admin UI served from FastAPI)

**Current Direction**: FastAPI templating for all UI (customer and admin)

---

## SPEC References

- **SPEC-123**: Admin Frontend Rollout
  - **Status**: 🔴 DEPRECATED (Next.js admin app)
  - **File**: `specs/123-admin-frontend-rollout/README.md`
  - **Replaced By**: FastAPI templates + internal FastAPI routes

- **SPEC-116**: Internal Frontend Migration
  - **Status**: 🔴 DEPRECATED (Next.js split architecture)
  - **File**: `specs/116-internal-frontend-migration/README.md`

---

## Migration Path

**Admin UI should use**:
- FastAPI routes serving Jinja2 templates
- Same design system as customer UI
- Internal IP whitelist via FastAPI middleware (not nginx)

---

## Archive Location

This folder was moved from: `frontend-nextjs-admin/`
To: `.archive/deprecated/frontend-nextjs-admin-2025-01-31/`

**Original Size**: ~2 files (mostly empty, placeholder)

---

**Status**: ✅ Archived - Admin UI to be served from FastAPI
