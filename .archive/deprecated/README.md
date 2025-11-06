# Deprecated Code Archive

**Last Updated**: 2025-01-31  
**Purpose**: Archive deprecated code and folders based on SPEC decisions

---

## Archive Structure

This directory contains deprecated code that has been superseded by new implementations or architectural decisions.

---

## Archived Items

### Frontend Next.js Folders (2025-01-31)

**Reason**: Next.js deprecated in favor of FastAPI + Jinja2 templates (per SPEC-103, SPEC-116, SPEC-122, SPEC-123)

- `frontend-nextjs/` - Next.js 15 bootstrap project (SPEC-103)
- `frontend-nextjs-customer/` - Customer Next.js app (SPEC-122)
- `frontend-nextjs-admin/` - Admin Next.js app (SPEC-123)

**Replaced By**: FastAPI + Jinja2 templates (server-side rendering)

**SPEC References**:
- SPEC-103: Next.js 15 Bootstrap (DEPRECATED)
- SPEC-116: Internal Frontend Migration (DEPRECATED)
- SPEC-122: Customer Frontend Rollout (DEPRECATED)
- SPEC-123: Admin Frontend Rollout (DEPRECATED)

**Active Frontend**: `apps/customer/` (Vite + React Router)

---

## Archive Guidelines

### When to Archive

1. **SPEC Deprecation**: Code related to deprecated SPECs
2. **Architecture Change**: Code replaced by new architecture
3. **Migration Complete**: Code successfully migrated to new location
4. **No Active Use**: Code not referenced in active SPECs or stories

### Archive Process

1. Create dated archive directory: `.archive/deprecated/[name]-[date]/`
2. Move code to archive
3. Add README explaining deprecation
4. Update references in active code
5. Update documentation

### Retrieval

Archived code can be retrieved if needed:
```bash
# Restore from archive
cp -r .archive/deprecated/[name]-[date]/ [original-location]/
```

---

## Maintenance

- Review archive quarterly
- Remove archives older than 1 year if no longer needed
- Keep archives for legal/compliance requirements

---

**Archive Location**: `.archive/deprecated/`

