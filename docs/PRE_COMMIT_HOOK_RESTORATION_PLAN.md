# Pre-Commit Hook Restoration Plan

**Date:** 2025-10-08
**Status:** CRITICAL - Currently Bypassing 96% of Codebase

## Current Situation Analysis

### Codebase Statistics
- **Total Files:** 5,615 files (112.35 MB)
- **Python Files:** 708 files (6.82 MB) ← PRIMARY CONCERN
- **Shell Scripts:** 176 files (0.74 MB)
- **JavaScript:** 30 files (1.03 MB)
- **HTML:** 54 files (0.83 MB)
- **Markdown:** 825 files (6.53 MB)

### Current Exclusions (PROBLEM!)

**Flake8 Excludes (Line 50):**
```regex
^(server/.*\.py|tests/.*\.py|test_.*\.py|alembic/.*\.py|
  specs/.*/tests/.*\.py|coverage/.*\.py|scripts/.*\.py|
  run_server\.py|run_server_minimal\.py|mem0|
  ninaivalaigal_ci_rbac_pack/.*|client-tools/vendor/.*|
  .*debug.*\.py|benchmarks/.*\.py|mcp_server/.*\.py|
  examples/.*\.py|health-monitor.*\.py|utils/.*\.py)$
```

**Result:** ~680 of 708 Python files EXCLUDED (96%)

### Files Actually Being Checked
- ✅ `eM.py` (root level)
- ✅ `client-tools/eM`
- ✅ `client-tools/mem0`
- ✅ `sidecar/main.py`
- ✅ `specs/033-redis-integration/scripts/redis_test.py`
- **Total:** ~20-30 files out of 708

## Why This Violates Best Practices

Per Memory [b996f051-ab89-4cfc-a7b4-d7bcefdf8002]:
> "User emphasized the importance of not bypassing pre-commit hooks with --no-verify.
> We need to fix the actual issues flagged by the hooks rather than bypassing them."

**Current state defeats the entire purpose of code quality enforcement.**

## Restoration Strategy

### Phase 1: Assess the Damage (15 min)
Run hooks on excluded directories and catalog issues:

```bash
# Test flake8 on server/
flake8 server/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Test flake8 on tests/
flake8 tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Test flake8 on scripts/
flake8 scripts/*.py --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Phase 2: Critical Errors First (1-2 hours)
Fix only blocking errors:
- **E9**: Runtime errors (syntax, indentation)
- **F63**: Invalid syntax
- **F7**: Syntax errors
- **F82**: Undefined names

### Phase 3: Incremental Restoration (Iterative)

#### Week 1: Core Server (200+ files)
- Remove `server/.*\.py` exclusion
- Fix issues directory by directory:
  - `server/database/` (30 files)
  - `server/security/` (20 files)
  - `server/graph/` (15 files)
  - `server/agent/` (10 files)
  - `server/*.py` root APIs (150 files)

#### Week 2: Tests (150+ files)
- Remove `tests/.*\.py` exclusion
- Add proper test fixtures
- Fix test docstrings

#### Week 3: Scripts & Utilities (50+ files)
- Remove `scripts/.*\.py` exclusion
- Fix shell scripts with shellcheck
- Add proper documentation

#### Week 4: Specialized Modules
- Remove remaining exclusions
- Polish remaining files

### Phase 4: Lock It Down
- Update `.pre-commit-config.yaml` with minimal exclusions
- Only exclude true third-party code: `client-tools/vendor/.*`
- Add CI enforcement

## Top SPECs Affected

Based on analysis, these SPECs have the most Python files:

| SPEC | Files | Python Files | Priority |
|------|-------|--------------|----------|
| SPEC-040 | 80 | 16 | HIGH |
| SPEC-031 | 73 | 13 | HIGH |
| SPEC-033 | 56 | 11 | HIGH |
| SPEC-061 | 32 | 13 | HIGH |
| SPEC-060 | 32 | 8 | MEDIUM |
| SPEC-052 | 34 | 8 | MEDIUM |
| SPEC-049 | 29 | 10 | MEDIUM |

## Estimated Effort

**Conservative Estimate:**
- Phase 1 (Assessment): 15 minutes
- Phase 2 (Critical): 2 hours
- Phase 3 (Incremental): 20-30 hours over 4 weeks
- Phase 4 (Lock down): 1 hour

**Total:** ~25-35 hours for complete restoration

## Alternative: Aggressive Approach

If time is critical, we can:
1. Fix critical errors only (Phase 1-2)
2. Gradually expand coverage over time
3. Add files back as they're cleaned up

## Decision Point

**Option A: Full Restoration (Recommended)**
- Proper code quality across entire codebase
- Takes 4 weeks
- Establishes professional discipline

**Option B: Incremental Restoration**
- Fix critical paths first (server/ core)
- Add tests/scripts gradually
- 2 weeks for core, ongoing for rest

**Option C: Status Quo (NOT RECOMMENDED)**
- Keep bypassing 96% of code
- Defeats purpose of hooks
- Violates user's stated preference

## Next Steps

1. **User Decision:** Choose Option A, B, or C
2. **If A or B:** Run Phase 1 assessment
3. **Create Issues:** Track restoration progress
4. **Update Memory:** Document approach for future

## Memory Update

If proceeding, create memory:
```
Pre-commit hook restoration initiated. Currently excluding 680/708 Python files.
Incremental restoration plan: Phase 1 (assessment), Phase 2 (critical errors),
Phase 3 (directory-by-directory cleanup), Phase 4 (lock down). Estimated 25-35
hours total effort. Top affected SPECs: 040, 031, 033, 061, 060.
```
