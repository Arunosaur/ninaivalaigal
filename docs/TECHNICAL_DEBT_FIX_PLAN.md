# Technical Debt Fix Plan - Incremental Remediation

**Created:** October 7, 2025, 20:11 CST
**Status:** IN PROGRESS
**Goal:** Remove all pre-commit bypasses with incremental testing

---

## 🎯 EXECUTION STRATEGY

### Principles:
1. **Quick Wins First** - Start with 30-minute fixes to build momentum
2. **Test After Each Fix** - Run pre-commit hooks after every change
3. **Incremental Commits** - Commit each phase separately
4. **No Regressions** - Run smoke tests before each commit
5. **Document Everything** - Update TECHNICAL_DEBT.md as we fix items

---

## 📋 STASH REVIEW

### Stash Analysis:
- **stash@{0}**: Profile-based service separation (517 insertions, 147 deletions)
  - Status: Review for conflicts with recent commit
  - Action: Check if changes are still needed

- **stash@{1}**: Minor redaction middleware changes (pyc files only)
  - Status: Discard (compiled files, not source changes)

- **stash@{2}**: Major docs cleanup (20,931 insertions, 63,073 deletions)
  - Status: Old cleanup work, already incorporated
  - Action: Discard

- **stash@{3}**: node_modules whitespace (732 insertions, 753 deletions)
  - Status: Noise, vendor code
  - Action: Discard

### Stash Decision:
- Review stash@{0} for useful changes
- Discard stash@{1}, @{2}, @{3}

---

## 🚀 PHASE 1: QUICK WINS (Est: 1 hour)

### ✅ Task 1.1: Fix Duplicate Python Module Names (30 min)

**Problem:** `test_auth_enhanced.py` exists in both `tests/unit/` and `tests/functional/`

**Fix:**
```bash
# Rename functional version to be more specific
mv tests/functional/test_auth_enhanced.py tests/functional/test_auth_functional.py

# Update any imports if needed
grep -r "test_auth_enhanced" tests/
```

**Test:**
```bash
git add tests/
pre-commit run mypy --files tests/functional/test_auth_functional.py
pytest tests/functional/test_auth_functional.py -v
```

**Commit:**
```bash
git commit -m "fix: rename duplicate test module test_auth_enhanced -> test_auth_functional

Resolves mypy duplicate module error.
Part of Technical Debt Item #2 remediation.

Refs: docs/TECHNICAL_DEBT.md"
```

---

### ✅ Task 1.2: Fix Empty Shell Scripts (15 min)

**Problem:** Two empty shell scripts causing shellcheck to fail
- `scripts/apple-stack-up.sh`
- `scripts/ninaivalaigal-dev-pgbouncer-start.sh`

**Fix:**
```bash
# Check if they're actually empty
[ -s scripts/apple-stack-up.sh ] || echo "Empty"
[ -s scripts/ninaivalaigal-dev-pgbouncer-start.sh ] || echo "Empty"

# Either add proper shebang and content, or remove them
git rm scripts/apple-stack-up.sh scripts/ninaivalaigal-dev-pgbouncer-start.sh
```

**Test:**
```bash
pre-commit run shellcheck --all-files
```

**Commit:**
```bash
git commit -m "fix: remove empty shell script stubs

Removed apple-stack-up.sh and ninaivalaigal-dev-pgbouncer-start.sh which
were empty placeholders causing shellcheck failures.

Part of Technical Debt Item #1 remediation.

Refs: docs/TECHNICAL_DEBT.md"
```

---

## 🔧 PHASE 2: SHELLCHECK CRITICAL FIXES (Est: 2 hours)

### ✅ Task 2.1: Fix Parsing Errors in Python-Embedded Scripts

**Files:**
1. `scripts/update-agent-context.sh` - SC1073, SC1072, SC1009
2. `scripts/nina-intelligence-stack-start.sh` - SC1089

**Strategy:**
- Extract Python code to separate .py files
- Call Python scripts from shell scripts
- Keeps separation of concerns clean

**Example for update-agent-context.sh:**
```bash
# Instead of embedded Python:
# python << EOF
# ...
# EOF

# Create scripts/update_agent_context.py and call it:
python scripts/update_agent_context.py "$@"
```

---

### ✅ Task 2.2: Fix Common Anti-Patterns

**SC2012 - Use find instead of ls:**
```bash
# Before:
backup_file=$(ls -t "${BACKUP_DIR}"/nv-db-relational-backup-*.sql | head -1)

# After:
backup_file=$(find "${BACKUP_DIR}" -name 'nv-db-relational-backup-*.sql' -type f -print0 | \
              xargs -0 ls -t | head -1)
```

**SC2001 - Use parameter expansion instead of sed:**
```bash
# Before:
IMAGE_NAME=$(echo "$IMAGE" | sed 's/:.*//')

# After:
IMAGE_NAME="${IMAGE%%:*}"
```

**SC2009 - Use pgrep instead of ps | grep:**
```bash
# Before:
ps aux | grep -E "(container|docker|podman)" | grep -v grep

# After:
pgrep -f "container|docker|podman" || echo "No container processes running"
```

---

## 📝 PHASE 3: PYTHON TEST QUALITY (Est: 4 hours)

### ✅ Task 3.1: Add Module Docstrings (1h)

**Strategy:** Add brief module docstrings to all test files

**Template:**
```python
"""
Test module for [component name].

This module contains [unit/functional/integration] tests for [what it tests].
"""
```

**Automation:**
```bash
# Script to add docstrings
for file in tests/**/*.py; do
  if ! head -1 "$file" | grep -q '"""'; then
    # Add docstring at top
    echo 'Needs docstring: '$file
  fi
done
```

---

### ✅ Task 3.2: Fix Line Length Issues (1h)

**Strategy:** Use black and manual formatting

**Commands:**
```bash
# Let black handle most of it
black tests/ --line-length 100

# Manual review for docstrings and comments
flake8 tests/ | grep E501
```

---

### ✅ Task 3.3: Fix Bare Except Statements (1h)

**Pattern:**
```python
# Before:
try:
    something()
except:
    pass

# After:
try:
    something()
except Exception as e:
    logger.warning(f"Operation failed: {e}")
```

---

### ✅ Task 3.4: Add Type Hints to Fixtures (1h)

**Pattern:**
```python
# Before:
@pytest.fixture
def test_client():
    return TestClient(app)

# After:
@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
```

---

## 🎨 PHASE 4: SERVER MODULE TYPE COVERAGE (Est: 8 hours)

### Prioritization:
1. **Critical (2h):** `server/main.py`, `server/auth.py`
2. **High (3h):** `server/database/operations/`, `server/graph/`
3. **Medium (3h):** `server/performance/`, `server/middleware/`

### Strategy:
- Add type hints incrementally
- Use mypy to validate
- Focus on public APIs first

---

## 📊 SUCCESS METRICS

### Phase Completion Criteria:
- ✅ All pre-commit hooks pass without exclusions
- ✅ No shellcheck warnings (except documented exceptions)
- ✅ Test files have 100% docstring coverage
- ✅ Server modules have 70%+ type hint coverage
- ✅ All smoke tests pass
- ✅ TECHNICAL_DEBT.md updated to RESOLVED status

---

## 🔄 TESTING PROTOCOL

### After Each Fix:
```bash
# 1. Run specific hook
pre-commit run [hook-name] --files [changed-files]

# 2. Run all hooks on changed files
pre-commit run --files [changed-files]

# 3. Run smoke tests
pytest tests/smoke/ -v

# 4. If all pass, commit
git add [files]
git commit -m "[conventional-commit-format]"
```

### Before Push:
```bash
# Full validation
pre-commit run --all-files
pytest tests/smoke/ -v
make test-critical
```

---

## 📅 TIMELINE

| Phase | Tasks | Est. Time | Target Completion |
|-------|-------|-----------|-------------------|
| Stash Review | 4 stashes | 30 min | Oct 7, 20:30 |
| Phase 1 | Quick Wins | 1 hour | Oct 7, 21:30 |
| Phase 2 | ShellCheck | 2 hours | Oct 7, 23:30 |
| Phase 3 | Test Quality | 4 hours | Oct 8, 03:30 |
| Phase 4 | Type Coverage | 8 hours | Oct 8, 11:30 |

**Total:** ~15.5 hours (can be spread over multiple sessions)

---

## 🚨 ROLLBACK PLAN

If any fix causes issues:
```bash
# Revert last commit
git reset --soft HEAD~1

# Or revert specific commit
git revert [commit-hash]

# Re-add exclusion temporarily
# (document in TECHNICAL_DEBT.md)
```

---

**Next Step:** Start with Phase 1, Task 1.1 (duplicate module fix)
