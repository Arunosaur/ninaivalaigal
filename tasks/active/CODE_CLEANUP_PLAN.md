# Code Cleanup Plan - Based on SPECs and Stories

**Developer F**
**Date**: 2025-01-31
**Status**: 📋 Planning

---

## 🎯 Objective

Remove deprecated and unused code/folders based on SPECs and Taiga stories. Focus on verifying through SPECs rather than assumptions.

---

## 📊 Analysis Results

### ✅ Confirmed Deprecated (via SPECs)

#### 1. Next.js Frontend Folders (DEPRECATED)

**Evidence from SPECs:**
- **SPEC-103**: Next.js 15 Bootstrap - **DEPRECATED** (2025-11-02)
- **SPEC-116**: Internal Frontend Migration - Needs deprecation (Next.js split)
- **SPEC-122**: Customer Frontend Rollout - Next.js + Vercel (DEPRECATED)
- **SPEC-123**: Admin Frontend Rollout - Next.js admin app (DEPRECATED)
- **SPEC-121**: Frontend Shared Library - React components (DEPRECATED)

**Current Direction**: FastAPI + Jinja2 templates (per `docs/UI_SPEC_AUDIT_AND_UPDATE_PLAN.md`)

**Folders to Archive:**
- `frontend-nextjs/` - Next.js 15 bootstrap project
- `frontend-nextjs-customer/` - Customer Next.js app (has DEPRECATED.md)
- `frontend-nextjs-admin/` - Admin Next.js app (mostly empty)

**Size**: ~200+ files across 3 directories

---

#### 2. Deprecated SPEC Directories (Already Archived)

**Already in `.archive/deprecated/`:**
- SPEC-049: Memory Sharing & Collaboration → Superseded by SPEC-127
- SPEC-050: Cross-Organization Memory Sharing → Superseded by SPEC-127
- SPEC-066: Standalone Team Accounts → Duplicate of SPEC-026

**Action**: ✅ Already archived, no action needed

---

#### 3. Other Potential Cleanup (Need Verification)

**Need to verify:**
- `client/` - Check if used
- `frontend/` - Check if legacy or active
- `apps/customer/` vs `frontend-nextjs-customer/` - Which is active?
- `frontend-shared/` - Check if React components are needed

---

## 📋 Cleanup Plan

### Phase 1: Archive Next.js Folders (High Priority)

**Rationale**: Confirmed deprecated by SPEC-103, SPEC-116, SPEC-122, SPEC-123

#### 1.1 Archive `frontend-nextjs/`
```bash
# Create archive directory
mkdir -p .archive/deprecated/frontend-nextjs-2025-01-31

# Move with deprecation notice
mv frontend-nextjs .archive/deprecated/frontend-nextjs-2025-01-31/
```

**Reason**: SPEC-103 marked as DEPRECATED, replaced by FastAPI templating

#### 1.2 Archive `frontend-nextjs-customer/`
```bash
mkdir -p .archive/deprecated/frontend-nextjs-customer-2025-01-31
mv frontend-nextjs-customer .archive/deprecated/frontend-nextjs-customer-2025-01-31/
```

**Reason**: SPEC-122 deprecated (Next.js + Vercel), has DEPRECATED.md already

#### 1.3 Archive `frontend-nextjs-admin/`
```bash
mkdir -p .archive/deprecated/frontend-nextjs-admin-2025-01-31
mv frontend-nextjs-admin .archive/deprecated/frontend-nextjs-admin-2025-01-31/
```

**Reason**: SPEC-123 deprecated (Next.js admin app), mostly empty directory

---

### Phase 2: Verify Other Frontend Folders

#### 2.1 Check `frontend/` vs `apps/customer/`
- **Question**: Which is the active frontend?
- **Check**: SPECs, recent commits, CI/CD configs
- **Action**: Archive legacy one if duplicate

#### 2.2 Check `frontend-shared/`
- **Question**: Is this React components library still needed?
- **Check**: SPEC-121 status (marked as DEPRECATED)
- **Action**: Archive if React components not needed

#### 2.3 Check `client/`
- **Question**: What is this folder? Is it used?
- **Check**: References in codebase, SPECs
- **Action**: Archive if unused

---

### Phase 3: Update References

#### 3.1 Update CI/CD Workflows
- Remove Next.js deployment workflows
- Remove Next.js build steps
- Update documentation references

#### 3.2 Update Documentation
- Remove Next.js references from active docs
- Update architecture diagrams
- Update deployment guides

---

## 🔍 Verification Checklist

### Before Archiving

- [ ] Verify folder is not referenced in active SPECs
- [ ] Check if referenced in active Taiga stories
- [ ] Verify no active CI/CD pipelines use it
- [ ] Check if any production deployments use it
- [ ] Document what's being archived and why

### After Archiving

- [ ] Update SPEC_INDEX.md if needed
- [ ] Update any cross-references
- [ ] Update README files
- [ ] Create deprecation summary document

---

## 📊 Expected Cleanup Results

### Files/Folders to Archive

| Folder | Size | Reason | Priority |
|--------|------|--------|----------|
| `frontend-nextjs/` | ~74 files | SPEC-103 DEPRECATED | 🔴 HIGH |
| `frontend-nextjs-customer/` | ~88 files | SPEC-122 DEPRECATED | 🔴 HIGH |
| `frontend-nextjs-admin/` | ~2 files | SPEC-123 DEPRECATED | 🔴 HIGH |
| `frontend-shared/` | ~71 files | SPEC-121 DEPRECATED | 🟡 MEDIUM |
| `client/` | TBD | Needs verification | 🟡 MEDIUM |
| `frontend/` | TBD | Needs verification | 🟡 MEDIUM |

**Estimated Total**: ~235+ files to archive

---

## 🚀 Implementation Steps

### Step 1: Create Archive Structure
```bash
mkdir -p .archive/deprecated/frontend-nextjs-2025-01-31
mkdir -p .archive/deprecated/frontend-nextjs-customer-2025-01-31
mkdir -p .archive/deprecated/frontend-nextjs-admin-2025-01-31
```

### Step 2: Add Deprecation README
Create README in each archive explaining:
- Why it was deprecated
- When it was deprecated
- What replaced it
- Reference to SPEC

### Step 3: Move Folders
```bash
mv frontend-nextjs .archive/deprecated/frontend-nextjs-2025-01-31/
mv frontend-nextjs-customer .archive/deprecated/frontend-nextjs-customer-2025-01-31/
mv frontend-nextjs-admin .archive/deprecated/frontend-nextjs-admin-2025-01-31/
```

### Step 4: Update References
- Search codebase for references
- Update documentation
- Update CI/CD configs

---

## 📝 Archive Documentation Template

For each archived folder, create:

```markdown
# [Folder Name] - DEPRECATED

**Deprecated Date**: 2025-01-31
**Deprecated By**: Developer F
**Reason**: [SPEC-based reason]

## Deprecation Details

**Original Purpose**: [What it was for]
**Replaced By**: [What replaced it]

## SPEC References

- **SPEC-XXX**: [Relevant SPEC]
- **Status**: DEPRECATED

## Migration Path

[If applicable, how to migrate]

## Archive Location

This folder was moved from: `[original path]`
To: `.archive/deprecated/[folder-name]-[date]/`
```

---

## ⚠️ Risk Assessment

### Low Risk
- ✅ Next.js folders are confirmed deprecated by SPECs
- ✅ No active development on these folders
- ✅ Clear replacement path documented

### Medium Risk
- ⚠️ Need to verify `frontend-shared/` usage
- ⚠️ Need to verify `frontend/` vs `apps/customer/` relationship

### High Risk
- ❌ None identified

---

## 📋 Execution Checklist

### Pre-Cleanup
- [ ] Verify SPEC deprecation status
- [ ] Check for active references
- [ ] Backup important code (git already has it)
- [ ] Notify team (if needed)

### Cleanup
- [ ] Create archive directories
- [ ] Add deprecation READMEs
- [ ] Move folders to archive
- [ ] Update .gitignore if needed
- [ ] Update documentation

### Post-Cleanup
- [ ] Verify no broken references
- [ ] Update SPEC_INDEX.md
- [ ] Create cleanup summary
- [ ] Update project README

---

## 🔗 References

- **SPEC-103**: Next.js 15 Bootstrap (DEPRECATED)
- **SPEC-116**: Internal Frontend Migration
- **SPEC-121**: Frontend Shared Library (DEPRECATED)
- **SPEC-122**: Customer Frontend Rollout (DEPRECATED)
- **SPEC-123**: Admin Frontend Rollout (DEPRECATED)
- **UI SPEC Audit**: `docs/UI_SPEC_AUDIT_AND_UPDATE_PLAN.md`
- **Frontend Architecture Decision**: `docs/architecture/FRONTEND_ARCHITECTURE_DECISION.md`

---

**Status**: Ready to execute Phase 1 (Archive Next.js folders)
