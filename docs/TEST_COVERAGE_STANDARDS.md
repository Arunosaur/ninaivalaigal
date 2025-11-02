# Test Coverage Standards (US#410, SPEC-052)

**Status**: ✅ **STANDARDIZED**
**Last Updated**: November 1, 2025
**SPEC**: SPEC-052 (Comprehensive Test Coverage)

---

## 📋 Coverage Thresholds

### Standard Thresholds (Enforced in CI/CD)

| Test Type | Threshold | Enforcement | Purpose |
|-----------|-----------|-------------|---------|
| **Unit Tests** | **90%** | ✅ Blocking | Critical for foundation components and core logic |
| **Integration Tests** | **80%** | ✅ Blocking | Cross-component interactions and service integration |
| **Functional Tests** | **70%** | ✅ Blocking | End-to-end workflows and user scenarios |
| **Overall Coverage** | **85%** | ✅ Blocking | Platform-wide combined coverage target |
| **Changed Files** | **80%** | ⚠️ Recommended | New or modified code should meet threshold |

### Threshold Rationale

- **Unit Tests (90%)**: High threshold ensures critical business logic is well-tested
- **Integration Tests (80%)**: Lower threshold reflects complexity of integration scenarios
- **Functional Tests (70%)**: Lower threshold reflects end-to-end test complexity
- **Overall (85%)**: Balances comprehensive coverage with practical constraints

---

## 🔧 Configuration Files

### 1. `pytest.ini`

**Location**: Project root
**Purpose**: Pytest configuration for test discovery and execution

**Standard Configuration:**
```ini
[pytest]
pythonpath = .
testpaths = tests server/tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    unit: Unit tests - fast, isolated, no external dependencies
    integration: Integration tests - require live services or external infrastructure
    functional: Functional tests - end-to-end workflows and user scenarios
    performance: Performance and benchmark tests
    slow: Tests that take more than 1 second to run
    security: Security-focused tests
    chaos: Chaos engineering and failure simulation tests
```

### 2. `.coveragerc`

**Location**: Project root
**Purpose**: Coverage.py configuration for coverage measurement

**Standard Configuration:**
```ini
[run]
source = server, rbac
omit =
    */tests/*
    */venv/*
    */env/*
    */__pycache__/*
    */migrations/*
    */node_modules/*
    setup.py
    conftest.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
    @abstractmethod
    @property
    @.*\.setter

precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
title = ninaivalaigal Code Coverage Report

[xml]
output = coverage.xml
```

### 3. Coverage Threshold Constants

**Location**: `.github/workflows/.coverage-thresholds` (if using centralized config)
**Or**: Defined in each workflow file

**Standard Values:**
```bash
COVERAGE_THRESHOLD_UNIT=90
COVERAGE_THRESHOLD_INTEGRATION=80
COVERAGE_THRESHOLD_FUNCTIONAL=70
COVERAGE_THRESHOLD_OVERALL=85
COVERAGE_THRESHOLD_CHANGED_FILES=80
```

---

## 📂 Test Directory Structure

### Standard Organization

```
tests/
├── unit/                  # Unit tests (90% threshold)
│   ├── test_*.py
│   └── modules/
├── integration/          # Integration tests (80% threshold)
│   ├── test_*.py
│   └── services/
├── functional/           # Functional tests (70% threshold)
│   ├── test_*.py
│   └── workflows/
└── performance/          # Performance tests
    └── test_*.py

server/tests/             # Server-specific tests
├── unit/
├── integration/
├── services/
└── security/
```

### Test File Naming Convention

- **Unit Tests**: `test_<module_name>.py` or `tests/unit/test_<module_name>.py`
- **Integration Tests**: `test_<service>_integration.py` or `tests/integration/test_<service>.py`
- **Functional Tests**: `test_<feature>_workflow.py` or `tests/functional/test_<feature>.py`

---

## 🎯 Coverage Measurement

### Running Coverage Locally

```bash
# Unit tests with coverage
pytest tests/unit/ --cov=server --cov-report=html --cov-report=term

# Integration tests with coverage
pytest tests/integration/ --cov=server --cov-report=html --cov-report=term

# All tests with coverage
pytest tests/ --cov=server --cov-report=html --cov-report=term --cov-report=xml

# With threshold enforcement
pytest tests/unit/ --cov=server --cov-report=term --cov-fail-under=90
```

### Coverage Reports

- **HTML Report**: `htmlcov/index.html` - Visual coverage report
- **XML Report**: `coverage.xml` - For CI/CD integration (Codecov)
- **Terminal Report**: Standard output with missing lines

---

## 🔄 CI/CD Integration

### GitHub Actions Workflows

All workflows should use standardized thresholds:

```yaml
env:
  COVERAGE_THRESHOLD_UNIT: 90
  COVERAGE_THRESHOLD_INTEGRATION: 80
  COVERAGE_THRESHOLD_FUNCTIONAL: 70
  COVERAGE_THRESHOLD_OVERALL: 85
```

### Quality Gates

Coverage thresholds are enforced as quality gates:
- **Blocking**: Merges blocked if threshold not met
- **Reporting**: Coverage reports generated and uploaded as artifacts
- **Comments**: PR comments with coverage status

---

## 📊 Coverage Exclusions

### Files/Folders Excluded from Coverage

- Test files (`*/tests/*`)
- Virtual environments (`*/venv/*`, `*/env/*`)
- Cache directories (`*/__pycache__/*`)
- Migration files (`*/migrations/*`)
- Setup/configuration files (`setup.py`, `conftest.py`)
- Abstract base classes and protocols
- Debug-only code paths

### Code Patterns Excluded

- `pragma: no cover` - Explicitly excluded code
- `__repr__` methods - Usually trivial
- Debug conditionals - Not executed in production
- Abstract methods - Cannot be directly tested
- Protocol definitions - Type hints only

---

## ✅ Best Practices

### For Developers

1. **Write Tests First** (TDD when possible)
2. **Achieve Threshold**: New code should meet 80%+ coverage
3. **Update Tests**: Modify tests when modifying code
4. **Use Markers**: Properly mark tests (unit, integration, functional)
5. **Check Coverage Locally**: Run coverage before committing

### For CI/CD

1. **Enforce Thresholds**: Block merges if thresholds not met
2. **Generate Reports**: Create HTML and XML reports for review
3. **Post PR Comments**: Provide coverage feedback in PRs
4. **Track Trends**: Monitor coverage over time

---

## 📈 Reporting

### Coverage Reports Available

1. **HTML Report** (`htmlcov/index.html`): Visual coverage with line-by-line highlighting
2. **XML Report** (`coverage.xml`): For CI/CD integration (Codecov)
3. **Terminal Output**: Quick overview with missing lines
4. **CI Artifacts**: Uploaded to GitHub Actions for download

### Coverage Metrics Tracked

- **Line Coverage**: Percentage of lines executed
- **Branch Coverage**: Percentage of branches taken
- **Function Coverage**: Percentage of functions called
- **Class Coverage**: Percentage of classes instantiated

---

## 🔗 Related Documentation

- [SPEC-052: Comprehensive Test Coverage](../specs/052-comprehensive-test-coverage/README.md)
- [Testing Guide](../docs/TESTING_GUIDE.md)
- [Test Automation Summary](../docs/TEST_AUTOMATION_SUMMARY.md)
- [Multi-Language Test Coverage Guide](../docs/MULTI_LANGUAGE_TEST_COVERAGE_GUIDE.md)

---

**Status**: ✅ **STANDARDIZED** - All coverage configuration is now consistent across the project.
