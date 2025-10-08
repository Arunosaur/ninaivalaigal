# Pre-Commit Hook Restoration - Phase 1 Implementation

**Date:** 2025-10-08
**Status:** 🚀 READY TO START
**Approach:** Incremental Restoration (Option B - Pragmatic)

## Overview

Based on the provided bundle and analysis, we're implementing a **2-phase incremental approach** that delivers real progress without disrupting ongoing work.

## Current Metrics (Baseline)

| Metric | Current | Target (Phase 1) | Target (Phase 2) |
|--------|---------|------------------|------------------|
| Files checked | 4% (28 files) | 50% (360+ files) | 85% (600+ files) |
| Undefined names | 107+ | < 10 | 0 |
| Line length issues | 157 | Resolved | Resolved |
| Hook bypass rate | 96% | < 50% | < 15% |
| Code health (CI) | Partial | ✅ Server enforced | ✅ Full enforcement |

## Phase 1: Core Restoration (Week 1-2)

### Target: `server/` Directory (304 files)

**Goals:**
1. Fix 107 undefined names (critical runtime issues)
2. Enforce strict flake8 (E9, F63, F7, F82)
3. Remove `server/.*\.py` exclusion from `.pre-commit-config.yaml`
4. Add CI step: `flake8 server/ --count --select=E9,F63,F7,F82`

### Step-by-Step Execution

#### Step 1: Baseline Assessment (5 minutes)
```bash
# Run verification script
./scripts/lint/verify-hooks.sh > docs/hooks/phase1-baseline.txt

# Count issues
echo "Current undefined names in server/:"
flake8 server/ --count --select=F821 --statistics
```

#### Step 2: Auto-Fix What We Can (10 minutes)
```bash
# Fix imports automatically
./scripts/lint/fix-imports.sh

# Run black formatter
black server/

# Run isort
isort server/
```

#### Step 3: Manual Fixes (1-2 hours)
Fix remaining issues by category:

**A. Undefined Names (F821) - Priority 1**
Common patterns found:
- Missing imports: `db`, `List`, `deploy_graph_intelligence`
- Typos in variable names
- Missing function definitions

**B. Syntax Errors (E9, F63, F7) - Priority 2**
- Indentation errors
- Invalid syntax
- Unclosed brackets

**C. Line Length (E501) - Lower Priority**
- Split long lines
- Use better variable names

#### Step 4: Update Hook Configuration (5 minutes)
```bash
# Backup current config
cp .pre-commit-config.yaml .pre-commit-config.yaml.backup

# Update exclusion pattern
# CHANGE: exclude: ^(server/.*\.py|tests/.*\.py|...)$
# TO:     exclude: ^(tests/.*\.py|scripts/.*\.py|...)$
# (Remove server/ from exclusion)
```

#### Step 5: Validate & Commit (10 minutes)
```bash
# Run hooks on server/ only
pre-commit run --files server/**/*.py

# If passing, commit
git add server/ .pre-commit-config.yaml
git commit -m "fix(hooks): restore pre-commit enforcement for server/ directory

- Fixed 107 undefined name errors (F821)
- Resolved syntax and import issues
- Enabled strict flake8 for server/ (E9,F63,F7,F82)
- Phase 1 of pre-commit restoration complete

Metrics:
- Files now checked: 360+ (up from 28)
- Critical errors: 0 (down from 107)
- Hook coverage: 50% (up from 4%)"
```

### Deliverables

- ✅ `PRE_COMMIT_HOOK_RESTORE_SERVER.md` summary
- ✅ All server/*.py validated
- ✅ New hook metrics report in CI
- ✅ Updated `.pre-commit-config.yaml` with server/ enforcement

## Phase 2: Tests + Scripts (Week 3-4)

### Target: `tests/`, `scripts/`, `utils/` (196 files)

**Goals:**
1. Clean imports + docstrings
2. Add pytest `--maxfail=3 --disable-warnings`
3. Re-enable these in `.pre-commit-config.yaml`
4. Achieve ≥ 80% flake8 coverage across repo

**Deliverables:**
- ✅ `PRE_COMMIT_HOOK_RESTORE_TESTS.md` summary
- ✅ CI "lint + test" job across all major directories

## Tools Provided in Bundle

### 1. `scripts/lint/verify-hooks.sh`
Runs per-directory lint stats:
```bash
./scripts/lint/verify-hooks.sh
```

### 2. `scripts/lint/fix-imports.sh`
Auto-fixes imports using `isort` + `autoflake`:
```bash
./scripts/lint/fix-imports.sh
```

### 3. Progressive `.pre-commit-config.yaml`
Uses strict error-only enforcement initially:
```yaml
args: ["--count", "--select=E9,F63,F7,F82"]
```

## Expected Outcome

**After Phase 1:**
- Files checked: **360+ files** (up from 28)
- Undefined names: **< 10** (down from 107+)
- Line length: **Resolved**
- Hook bypass: **< 50%** (down from 96%)
- Code health: **✅ Full enforcement on server/**

**After Phase 2:**
- Files checked: **600+ files** (85% coverage)
- All critical errors: **0**
- Hook bypass: **< 15%**
- CI enforcement: **✅ Full lint + test**

## Automation Scripts

### Quick Start Script

```bash
#!/usr/bin/env bash
# scripts/hooks/restore-phase1.sh

set -euo pipefail

echo "🚀 Pre-Commit Hook Restoration - Phase 1"
echo "=========================================="
echo ""

# Step 1: Baseline
echo "📊 Step 1: Baseline assessment..."
./scripts/lint/verify-hooks.sh | tee docs/hooks/phase1-baseline.txt

# Step 2: Auto-fix
echo ""
echo "🛠️  Step 2: Auto-fixing imports..."
./scripts/lint/fix-imports.sh

# Step 3: Format
echo ""
echo "✨ Step 3: Formatting code..."
black server/
isort server/

# Step 4: Check
echo ""
echo "🔍 Step 4: Checking for remaining issues..."
flake8 server/ --count --select=E9,F63,F7,F82 --show-source --statistics || true

echo ""
echo "✅ Phase 1 automation complete!"
echo ""
echo "Next steps:"
echo "  1. Fix remaining undefined names manually"
echo "  2. Update .pre-commit-config.yaml"
echo "  3. Run: pre-commit run --files server/**/*.py"
echo "  4. Commit changes"
```

## Risk Mitigation

1. **Backup Current Config:**
   - `.pre-commit-config.yaml.backup` saved
   - Can revert instantly if needed

2. **Incremental Commits:**
   - Commit after each major fix category
   - Easy to bisect if issues arise

3. **CI Safety Net:**
   - CI runs on PRs before merge
   - Can still manually override in emergencies

4. **Parallel Work:**
   - Phase 1 doesn't block API/container work
   - Other devs can continue in tests/scripts

## Success Criteria

**Phase 1 Complete When:**
- [ ] All F821 errors in `server/` resolved
- [ ] `server/.*\.py` removed from exclusions
- [ ] `pre-commit run --files server/**/*.py` passes
- [ ] CI has `flake8 server/` step passing
- [ ] Documentation updated

## Next Actions

**Ready to start Phase 1?**

1. Run: `./scripts/lint/verify-hooks.sh` (baseline)
2. Run: `./scripts/lint/fix-imports.sh` (auto-fix)
3. Fix remaining issues manually
4. Update `.pre-commit-config.yaml`
5. Commit and celebrate! 🎉

---

**Timeline:** 2-4 hours for Phase 1 (can be done today!)
**Impact:** Restores code quality on 304 core server files
**Risk:** Low (incremental, reversible)
