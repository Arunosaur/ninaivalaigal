# Test Automation and Enforcement Guide

**Date**: January 2025
**Purpose**: Comprehensive guide for ensuring tests run automatically and new tests are required for code changes

---

## 🎯 Current State

### ✅ **What's Already Working**

#### 1. **CI/CD Automated Test Execution**

**GitHub Actions Workflows**:
- `.github/workflows/comprehensive-test-validation.yml` - Runs on every PR/push
- `.github/workflows/pr-quality-gates.yml` - Quality gates including tests
- `.github/workflows/test-coverage.yml` - Coverage validation (85% threshold)
- `.github/workflows/foundation-tests.yml` - Foundation SPEC tests
- `.github/workflows/comprehensive-api-test-suite.yml` - API test suite

**Triggers**:
- ✅ **Pull Requests**: All PRs trigger test execution
- ✅ **Pushes to main/master**: All pushes trigger test execution
- ✅ **Manual dispatch**: Can trigger specific test suites

**Coverage Enforcement**:
- ✅ **Unit Tests**: 90% threshold enforced
- ✅ **Integration Tests**: 80% threshold enforced
- ✅ **Functional Tests**: 70% threshold enforced
- ✅ **Overall Coverage**: 85% threshold enforced
- ✅ **Quality Gates**: Block merges if coverage drops below thresholds

#### 2. **Pre-Commit Hooks** (Linting/Formatting Only)

**Current Hooks** (`.pre-commit-config.yaml`):
- ✅ Code formatting (black, isort)
- ✅ Linting (flake8)
- ✅ Security scanning (bandit, detect-secrets)
- ✅ Shell script validation (shellcheck)
- ❌ **Tests are NOT run in pre-commit** (intentional - too slow for commit-time)

#### 3. **Quality Gates**

**PR Quality Gates** (`.github/workflows/pr-quality-gates.yml`):
- ✅ Foundation SPEC tests must pass
- ✅ Coverage threshold must be met (85%)
- ✅ Performance regression check
- ✅ Security scan must pass
- ✅ Code quality checks must pass
- ✅ **All gates must pass before merge**

---

## ⚠️ **Gaps & Missing Mechanisms**

### 1. **No Pre-Commit Test Execution**
- Tests are not run before commit (too slow)
- Developers may commit broken code if tests aren't run locally
- **Mitigation**: CI runs tests on PR, but developer feedback is delayed

### 2. **No Automatic Detection of New Code Without Tests**
- No mechanism to detect when new Python files are added without corresponding test files
- No enforcement that new code must have tests before merge
- **Mitigation**: Coverage thresholds catch overall drops, but not specific new files

### 3. **Limited PR-Agent Test Requirements**
- PR-Agent has `require_tests=true` but only runs with `ai-review` label
- Not enforced for all PRs automatically
- **Mitigation**: Quality gates catch coverage issues, but not test file existence

---

## 🚀 **Recommended Enhancements**

### **Enhancement 1: Pre-Commit Fast Test Runner**

Add a fast test subset to pre-commit hooks for critical paths only:

**Add to `.pre-commit-config.yaml`**:
```yaml
  - repo: local
    hooks:
      - id: run-fast-tests
        name: Run Fast Test Subset
        entry: bash -c 'cd server && pytest tests/unit/test_*_critical.py -v --tb=short || exit 1'
        language: system
        types: [python]
        pass_filenames: false
        stages: [commit]
```

**Benefits**:
- Catches critical test failures before commit
- Fast execution (<30 seconds)
- Prevents broken commits

**Trade-offs**:
- Only runs critical tests (not comprehensive)
- May add 10-30 seconds to commit time

---

### **Enhancement 2: New File Test Detection**

Create a hook that detects new Python files without corresponding test files:

**Add to `.pre-commit-config.yaml`**:
```yaml
  - repo: local
    hooks:
      - id: check-new-files-have-tests
        name: Check New Files Have Tests
        entry: python scripts/check_test_coverage.py --check-new-files
        language: system
        types: [python]
        pass_filenames: true
        stages: [pre-commit]
```

**Implementation** (`scripts/check_test_coverage.py`):
```python
#!/usr/bin/env python3
"""
Check that new Python files have corresponding test files.
Run as pre-commit hook to enforce test coverage for new code.
"""

import sys
import os
from pathlib import Path

def find_test_file(source_file: Path) -> Path | None:
    """Find corresponding test file for a source file."""
    # Convert server/file.py -> tests/test_file.py
    # Or server/module/file.py -> tests/module/test_file.py

    if 'server/' in str(source_file):
        relative = source_file.relative_to('server/')
        test_path = Path('tests') / f"test_{relative.name}"
        if test_path.exists():
            return test_path

        # Try module-specific test
        if relative.parent != Path('.'):
            test_path = Path('tests') / relative.parent / f"test_{relative.name}"
            if test_path.exists():
                return test_path

    return None

def check_new_files():
    """Check if newly added Python files have test files."""
    # Get staged files from git
    import subprocess
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=A'],
        capture_output=True,
        text=True
    )

    new_files = [Path(f) for f in result.stdout.strip().split('\n') if f.endswith('.py')]

    missing_tests = []
    for new_file in new_files:
        if 'server/' in str(new_file) or 'services/' in str(new_file):
            test_file = find_test_file(new_file)
            if not test_file:
                missing_tests.append((new_file, test_file))

    if missing_tests:
        print("❌ New Python files found without corresponding test files:")
        for source, test in missing_tests:
            print(f"  - {source}")
            print(f"    Expected test: {test or 'tests/test_...py'}")
        print("\n⚠️  Please add test files before committing.")
        return False

    return True

if __name__ == '__main__':
    if not check_new_files():
        sys.exit(1)
```

**Benefits**:
- Automatically detects new files without tests
- Prevents committing untested code
- Provides clear guidance on expected test file locations

---

### **Enhancement 3: Enhanced Coverage Validation for Changed Files**

Add coverage validation that checks coverage for only changed files:

**Add to `.github/workflows/pr-quality-gates.yml`**:
```yaml
      - name: Quality Gate 6 - Changed Files Coverage Check
        id: changed_files_coverage
        run: |
          echo "📊 Checking coverage for changed files..."

          # Get changed Python files in this PR
          changed_files=$(git diff --name-only origin/main...HEAD | grep '\.py$' | grep -E '^(server|services)/' || true)

          if [ -z "$changed_files" ]; then
            echo "ℹ️ No Python files changed"
            echo "changed_files_coverage_passed=true" >> $GITHUB_OUTPUT
            exit 0
          fi

          # Run coverage for changed files
          coverage run -m pytest tests/ -v
          coverage report --include="$changed_files" --fail-under=80

          if [ $? -eq 0 ]; then
            echo "✅ Changed files meet coverage threshold"
            echo "changed_files_coverage_passed=true" >> $GITHUB_OUTPUT
          else
            echo "❌ Changed files below coverage threshold (80%)"
            echo "changed_files_coverage_passed=false" >> $GITHUB_OUTPUT
            exit 1
          fi
```

**Benefits**:
- Focuses on files actually changed in PR
- Ensures new/modified code has adequate tests
- Prevents coverage drops on specific files

---

### **Enhancement 4: PR-Agent Test Requirements for All PRs**

Update PR-Agent to always require tests (not just with label):

**Update `.github/workflows/pr-agent.yml`**:
```yaml
    - name: PR-Agent Review
      uses: Codium-ai/pr-agent@main
      if: github.event_name == 'pull_request'  # Run on all PRs
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        command: /review
        args: |
          --pr_reviewer.require_tests=true
          --pr_reviewer.require_security_review=true
          --pr_reviewer.focus_on_rbac=true
          --pr_reviewer.check_performance=true
          --pr_reviewer.check_coverage=true
          --pr_reviewer.test_inference=true  # Automatically detect missing tests
```

**Benefits**:
- AI-powered test detection
- Automatic review comments on missing tests
- Works for all PRs, not just labeled ones

---

## 📋 **Complete Test Execution Flow**

### **Current Flow**:

```
Developer commits code
    ↓
Pre-commit hooks (linting/formatting only)
    ↓
Code pushed to branch
    ↓
GitHub Actions triggers on PR
    ↓
Comprehensive test validation runs
    ↓
Quality gates check coverage (85% threshold)
    ↓
All tests must pass before merge
```

### **Recommended Enhanced Flow**:

```
Developer commits code
    ↓
Pre-commit hooks:
  - Linting/formatting (fast)
  - Fast test subset (critical tests only, <30s)
  - New file test detection (check for test files)
    ↓
If all pass → Commit succeeds
If tests fail → Commit blocked, developer fixes locally
    ↓
Code pushed to branch
    ↓
GitHub Actions triggers on PR
    ↓
Comprehensive test validation runs:
  - All unit tests (90% threshold)
  - All integration tests (80% threshold)
  - All functional tests (70% threshold)
  - Changed files coverage check (80% threshold)
  - Overall coverage (85% threshold)
    ↓
PR-Agent reviews:
  - Requires tests flag
  - Test inference (detects missing tests)
  - Coverage analysis
    ↓
Quality gates check:
  - Foundation SPEC tests pass
  - Coverage thresholds met
  - Performance acceptable
  - Security scan passes
    ↓
If all pass → PR can be merged
If any fail → PR blocked, developer must fix
```

---

## 🛠️ **Implementation Steps**

### **Step 1: Add Pre-Commit Fast Tests** (Optional - Recommended)

1. Create critical test subset: `tests/unit/test_*_critical.py`
2. Add pre-commit hook for fast tests
3. Test locally to ensure <30 second execution time

**Trade-off**: Adds commit time but catches issues early

### **Step 2: Implement New File Test Detection** (High Priority)

1. Create `scripts/check_test_coverage.py`
2. Add to `.pre-commit-config.yaml`
3. Test with new Python files

**Benefits**: Prevents untested code from being committed

### **Step 3: Enhance Coverage Validation** (High Priority)

1. Add changed files coverage check to quality gates
2. Set threshold (recommended: 80% for changed files)
3. Test with PR containing new/modified files

**Benefits**: Ensures changed code has tests

### **Step 4: Enable PR-Agent for All PRs** (Medium Priority)

1. Update `.github/workflows/pr-agent.yml` to run on all PRs
2. Enable test inference and coverage checks
3. Monitor PR-Agent reviews for effectiveness

**Benefits**: AI-powered test detection and review

---

## 📊 **Monitoring & Metrics**

### **Track These Metrics**:

1. **Test Execution Rate**:
   - Percentage of commits with tests run
   - Percentage of PRs with tests passing
   - Test execution time trends

2. **Coverage Trends**:
   - Overall coverage percentage over time
   - Coverage by file/component
   - Coverage for new vs existing code

3. **Test Quality**:
   - Number of test files per code file
   - Test-to-code ratio
   - Edge case coverage

4. **Developer Experience**:
   - Pre-commit hook execution time
   - PR review time (test failures)
   - Developer satisfaction with test requirements

---

## ✅ **Best Practices**

### **For Developers**:

1. **Run Tests Locally Before Committing**:
   ```bash
   make test-unit          # Fast unit tests
   make test-coverage      # Full coverage check
   ```

2. **Add Tests for New Code**:
   - Create test file alongside new Python files
   - Follow naming convention: `test_<original_name>.py`
   - Ensure 80%+ coverage for new code

3. **Update Tests for Modified Code**:
   - Update existing tests when modifying code
   - Add tests for new functionality
   - Remove/update obsolete tests

4. **Use Make Targets**:
   ```bash
   make test-all           # All tests with coverage
   make test-critical      # Critical path tests
   make validate-coverage  # Coverage validation
   ```

### **For CI/CD**:

1. **Maintain Coverage Thresholds**:
   - Unit: 90% (critical components)
   - Integration: 80% (cross-component)
   - Functional: 70% (end-to-end)
   - Overall: 85% (platform-wide)

2. **Block Merges on Failures**:
   - Tests must pass
   - Coverage must meet thresholds
   - Quality gates must pass

3. **Provide Clear Feedback**:
   - Detailed test failure reports
   - Coverage reports with missing lines highlighted
   - Actionable recommendations

---

## 🎯 **Summary**

### **Current Mechanisms**:
- ✅ CI/CD runs tests on every PR/push
- ✅ Quality gates block merges if tests fail
- ✅ Coverage thresholds enforced (85% overall)
- ✅ PR-Agent can review tests (with label)

### **Recommended Enhancements**:
- 🔧 Add pre-commit fast test subset (optional)
- 🔧 Add new file test detection hook (high priority)
- 🔧 Add changed files coverage validation (high priority)
- 🔧 Enable PR-Agent for all PRs (medium priority)

### **Expected Outcomes**:
- 🎯 100% of commits have tests run (via CI)
- 🎯 New code automatically requires tests
- 🎯 Changed files must have 80%+ coverage
- 🎯 Quality gates prevent untested code merges
- 🎯 Continuous improvement in test coverage

---

**Last Updated**: January 2025
**Status**: Current mechanisms work well, enhancements recommended for stronger enforcement




