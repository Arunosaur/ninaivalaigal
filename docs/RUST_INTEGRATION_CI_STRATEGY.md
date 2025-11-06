# Rust Integration CI Strategy

**Status**: ✅ **IMPLEMENTED**
**Date**: November 5, 2025
**SPEC**: SPEC-139 (Audit Reconciliation & Rust Integration Readiness)
**Related Story**: US#820 (CI Markers and Rust Integration Test Setup)

---

## Overview

The Rust Memory Service integration tests are **gated** in the CI pipeline to prevent them from running by default. This ensures:

1. ✅ Default CI pipelines run quickly without Rust service dependencies
2. ✅ Rust integration tests only run when explicitly enabled
3. ✅ Optional nightly/on-demand CI job for comprehensive Rust testing
4. ✅ Clear separation between standard tests and Rust-specific tests

---

## Gating Mechanism

### Test Marker

All Rust integration tests are marked with `@pytest.mark.rust_integration`:

**Test Files**:
- `tests/integration/test_memory_service_rust.py`
- `tests/integration/test_memory_service_rust_standalone.py`
- `services/core-api/tests/test_rust_memory_provider.py`

### Gating Logic

The gating logic is implemented in `tests/conftest.py`:

```python
def pytest_collection_modifyitems(config, items):
    """Skip Rust integration tests unless explicitly enabled."""

    env_enabled = _bool_from_env(os.getenv("PYTEST_RUN_RUST_INTEGRATION"))
    flag_enabled = _bool_from_env(os.getenv("USE_RUST_MEMORY"))
    cli_enabled = config.getoption("--run-rust-integration")

    if env_enabled or flag_enabled or cli_enabled:
        return  # Tests are enabled, don't skip

    # Otherwise, skip rust_integration tests
    skip_reason = (
        "Rust integration suite gated. Set PYTEST_RUN_RUST_INTEGRATION=1, "
        "USE_RUST_MEMORY=1, or pass --run-rust-integration to execute it."
    )
    # ... skip logic
```

### Opt-In Methods

Rust integration tests can be enabled using one of three methods:

1. **Environment Variable**: `PYTEST_RUN_RUST_INTEGRATION=1`
2. **Feature Flag**: `USE_RUST_MEMORY=1`
3. **CLI Flag**: `pytest --run-rust-integration`

---

## CI Workflow Strategy

### Default CI Workflows

**All standard CI workflows exclude Rust integration tests by default**:

- ✅ `comprehensive-api-test-suite.yml` - Runs standard API tests (no Rust)
- ✅ `pr-quality-gates.yml` - Runs quality gates (no Rust)
- ✅ `ci-lint.yml` - Runs linting and standard tests (no Rust)
- ✅ `foundation-tests.yml` - Runs foundation SPEC tests (no Rust)

**How it works**: The `pytest_collection_modifyitems` hook in `tests/conftest.py` automatically deselects `rust_integration` tests unless explicitly enabled. No workflow changes needed.

### Dedicated Rust Integration Workflow

**New Workflow**: `.github/workflows/rust-integration-tests.yml`

**Triggers**:
- ⏰ **Nightly**: Runs at 3 AM UTC daily
- 🔄 **On-Demand**: Manual trigger via GitHub Actions UI
- 📝 **Push**: Runs when Rust-related files change (memory service, tests)

**Features**:
- ✅ Builds Rust Memory Service from source
- ✅ Starts Rust service and Core API server
- ✅ Runs all Rust integration tests with `PYTEST_RUN_RUST_INTEGRATION=1`
- ✅ Generates test reports (JUnit XML, HTML)
- ✅ Uploads artifacts and comments on PRs
- ✅ Creates GitHub issues on failure

**Services Required**:
- PostgreSQL (via pgvector/pgvector:pg15)
- Redis (redis:7-alpine)
- Rust Memory Service (built from source)
- Core API Server (for JWT token generation)

---

## Local Development

### Running Rust Integration Tests Locally

**Option 1: CLI Flag**
```bash
pytest tests/integration/test_memory_service_rust.py --run-rust-integration
```

**Option 2: Environment Variable**
```bash
PYTEST_RUN_RUST_INTEGRATION=1 pytest tests/integration/test_memory_service_rust.py
```

**Option 3: Feature Flag**
```bash
USE_RUST_MEMORY=1 pytest tests/integration/test_memory_service_rust.py
```

### Prerequisites

1. **Rust Memory Service Running**
   ```bash
   # Start Rust Memory Service
   ./scripts/nv-memory-service-start.sh

   # Verify health
   curl http://localhost:13393/health
   ```

2. **Core API Server Running** (for JWT tokens)
   ```bash
   # Start Core API
   cd server && python -m uvicorn main:app --host 0.0.0.0 --port 13390

   # Verify health
   curl http://localhost:13390/health
   ```

3. **Database and Redis**
   - PostgreSQL accessible at `localhost:5432`
   - Redis accessible at `localhost:6379`

---

## Verification

### Verify Gating Works

**Test 1: Default pytest run (should skip Rust tests)**
```bash
pytest tests/integration/test_memory_service_rust.py --collect-only
# Expected: "collected X items / X deselected / 0 selected"
```

**Test 2: With flag enabled (should collect tests)**
```bash
pytest tests/integration/test_memory_service_rust.py --collect-only --run-rust-integration
# Expected: "collected X items / 0 deselected / X selected"
```

### Verify CI Workflows

1. **Standard workflows** should complete quickly without Rust service
2. **Rust integration workflow** should run only when:
   - Scheduled (nightly)
   - Manually triggered
   - Rust-related files change

---

## Integration with SPEC-139

This CI strategy fulfills the following SPEC-139 requirements:

### ✅ Test & CI Requirements

- [x] Pytest marker `rust_integration` applied to Rust-dependent tests
- [x] Default CI pipelines exclude the marker until flag enabled
- [x] Optional CI job runs full suite with Rust service (nightly or on-demand)

### Remaining Work

- [ ] Load test baseline captured (Rust vs Postgres provider)
- [ ] Observability dashboards include Rust metrics + alerts
- [ ] Stakeholder sign-off

---

## Troubleshooting

### Tests Still Running When They Shouldn't

**Check**: Ensure `tests/conftest.py` is being loaded. Verify pytest configuration:
```bash
pytest --collect-only -v | grep rust_integration
```

### Tests Not Running When They Should

**Check**: Verify environment variables or flags are set:
```bash
echo $PYTEST_RUN_RUST_INTEGRATION
echo $USE_RUST_MEMORY
```

**Check**: Verify Rust service is running:
```bash
curl http://localhost:13393/health
```

### CI Workflow Fails

**Common Issues**:
1. Rust service fails to start → Check logs in workflow artifacts
2. Database connection fails → Verify PostgreSQL service is healthy
3. JWT token generation fails → Verify Core API is running

**Debug**: Check workflow logs and artifacts for detailed error messages.

---

## Related Documentation

- **SPEC-139**: `specs/139-audit-reconciliation-rust-readiness/README.md`
- **Rust Integration Gate**: `specs/139-audit-reconciliation-rust-readiness/RUST_INTEGRATION_GATE.md`
- **Rust Memory Runbook**: `specs/139-audit-reconciliation-rust-readiness/RUST_MEMORY_RUNBOOK.md`
- **US#820 Documentation**: `docs/US820_CI_MARKERS_RUST_INTEGRATION.md`

---

**Last Updated**: November 5, 2025
**Maintained By**: Developer H
