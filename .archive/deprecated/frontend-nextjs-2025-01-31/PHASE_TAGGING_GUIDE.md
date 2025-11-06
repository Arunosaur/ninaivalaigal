# Phase Tagging Guide

**SPEC-103**: Migration Trilogy v1 - Phase Tagging Schema

## Overview

Phase tags provide traceable rollout and rollback points throughout the migration process. Each phase gets a semantic Git tag for production-grade version control.

---

## Tagging Schema

### **Format**
```
spec-{NUMBER}-phase-{PHASE}[-{VARIANT}]
```

### **Examples**
```bash
# SPEC-102: Migration Preparation
spec-102-migration-ready         # Legacy freeze complete

# SPEC-103: Next.js Bootstrap
spec-103-phase-1                 # Project bootstrap
spec-103-phase-2                 # Configurations ported
spec-103-phase-3                 # Components ported
spec-103-phase-4                 # Storybook setup
spec-103-phase-5                 # Pages created
spec-103-phase-6                 # CI/CD configured
spec-103-complete                # Full Next.js migration

# SPEC-104: Quality Verification
spec-104-phase-1                 # Lighthouse audit
spec-104-phase-2                 # Accessibility audit
spec-104-complete                # Migration verified
```

---

## Tag Creation Commands

### **Phase 1: Bootstrap (COMPLETED)**
```bash
git tag -a spec-103-phase-1 -m "SPEC-103 Phase 1: Next.js 15 Bootstrap Complete

- Next.js 15.5.4 with App Router
- React 19.1.0, TypeScript 5.9.3, Tailwind 4.1.14
- All dependencies installed
- Configurations ready
- Makefile convenience targets
- ESLint dual-mode (local + CI)

Ready for Phase 2: Configuration port"

git push origin spec-103-phase-1
```

### **Phase 2: Configurations (PENDING)**
```bash
git tag -a spec-103-phase-2 -m "SPEC-103 Phase 2: Configurations Ported

- Tailwind config with design tokens
- Jest test framework setup
- Storybook configuration
- tsconfig paths configured

Ready for Phase 3: Component port"

git push origin spec-103-phase-2
```

### **Phase 3: Components (PENDING)**
```bash
git tag -a spec-103-phase-3 -m "SPEC-103 Phase 3: Keeper Components Ported

- 17 components successfully migrated
- Import paths updated for Next.js
- ESLint issues resolved (< 20 remaining)
- Storybook stories created

Ready for Phase 4: Storybook setup"

git push origin spec-103-phase-3
```

---

## Rollback Strategy

### **Rollback to Previous Phase**
```bash
# View available phase tags
git tag -l "spec-103-*"

# Rollback to Phase 1
git checkout spec-103-phase-1

# Create recovery branch
git checkout -b recovery-from-phase-1

# Continue work from stable checkpoint
```

### **Compare Phases**
```bash
# See changes between Phase 1 and Phase 2
git diff spec-103-phase-1..spec-103-phase-2

# See file changes
git diff --stat spec-103-phase-1..spec-103-phase-2
```

---

## Quality Gates per Phase

### **Phase 1: Bootstrap**
- ✅ Project created with correct dependencies
- ✅ All configurations operational
- ✅ `make dev` starts without errors
- ✅ Pre-commit hooks working
- ✅ TypeScript compiles clean

### **Phase 2: Configurations**
- ✅ Tailwind build successful
- ✅ Jest runs without errors
- ✅ Storybook starts on port 6006
- ✅ Path aliases resolve correctly

### **Phase 3: Components**
- ✅ All 17 components ported
- ✅ ESLint < 20 issues
- ✅ Zero TypeScript errors
- ✅ Storybook stories working
- ✅ Accessibility checks passing

### **Phase 4: Storybook**
- ✅ All components have stories
- ✅ Storybook builds for production
- ✅ Visual regression tests setup
- ✅ Docs pages generated

### **Phase 5: Pages**
- ✅ Dashboard page functional
- ✅ Signup page functional
- ✅ Routing working correctly
- ✅ API calls successful

### **Phase 6: CI/CD**
- ✅ GitHub Actions workflow passing
- ✅ Lighthouse CI configured
- ✅ Automated deploys working
- ✅ E2E tests passing

---

## Tag Validation

### **Before Creating Tag**
```bash
# 1. Run all checks
make ci

# 2. Verify quality gates
npm run lint
npm run type-check
npm run build

# 3. Check git status
git status

# 4. Review changes
git log --oneline -5
```

### **After Creating Tag**
```bash
# Verify tag exists
git tag -l "spec-103-phase-*"

# View tag details
git show spec-103-phase-1

# Verify pushed to remote
git ls-remote --tags origin | grep spec-103
```

---

## Documentation Updates

Each phase tag should be accompanied by:

1. **Commit Message**: Detailed phase summary
2. **Documentation Update**: README or checklist
3. **Migration Log**: Entry in MIGRATION_LOG.md
4. **Metrics Update**: ESLint counts, test coverage, etc.

---

## Recommended Workflow

```bash
# Start Phase 2
git checkout main
git pull origin main

# Work on Phase 2
# ... make changes ...

# Validate before tagging
make ci

# Commit Phase 2 work
git add -A
git commit -m "feat(SPEC-103): Phase 2 - Configurations ported"

# Create Phase 2 tag
git tag -a spec-103-phase-2 -m "Phase 2 complete"

# Push everything
git push origin main --tags
```

---

## Emergency Rollback

If a phase introduces breaking changes:

```bash
# 1. Identify last good tag
git tag -l "spec-103-*"

# 2. Revert to last good state
git reset --hard spec-103-phase-1

# 3. Force push (ONLY if not yet deployed)
git push --force origin main

# 4. Re-tag current state
git tag -a spec-103-phase-1-recovery -m "Rolled back from Phase 2"
git push origin spec-103-phase-1-recovery
```

---

## Best Practices

1. **Tag at Logical Boundaries**: End of each phase, not mid-work
2. **Descriptive Messages**: Include metrics and readiness statement
3. **Quality Gates**: Never tag without passing all checks
4. **Push Immediately**: Don't leave tags local-only
5. **Document Dependencies**: Note what each phase requires
6. **Test Rollback**: Periodically verify rollback works
7. **Archive Tags**: Keep old tags for audit trail

---

**Current Status**: Phase 1 tagged and ready for Phase 2

**Next Tag**: `spec-103-phase-2` (after Tailwind/Jest/Storybook port)
