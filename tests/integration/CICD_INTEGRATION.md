# CI/CD Integration for Comprehensive API Test Suite

**Story**: US-92 - Comprehensive API Test Suite
**SPEC**: SPEC-086 (Multi-Runtime Port Allocation)
**Status**: ✅ Ready for CI/CD

## Overview

The comprehensive API test suite is fully integrated into the CI/CD pipeline and ready for ongoing validation. This document describes how the tests are integrated and how to use them.

## GitHub Actions Integration

### 1. Dedicated Workflow

**File**: `.github/workflows/comprehensive-api-test-suite.yml`

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch via GitHub Actions UI
- Path-based triggers (only runs when relevant files change)

**Test Suites**:
- Comprehensive API Suite (39 tests)
- Authentication Flows (6 tests)
- CRUD Operations (12 tests)
- Port Allocation (SPEC-086, 6 tests)

**Features**:
- Automatic API server startup
- Test result artifacts (JUnit XML, HTML reports)
- PR comments with test results
- Test summary in GitHub Actions summary

### 2. PR Quality Gates Integration

**File**: `.github/workflows/pr-quality-gates.yml`

The comprehensive API test suite is integrated as **Quality Gate 5** in the PR quality gates workflow:

- Runs automatically on pull requests
- Only runs when API code (`server/`) is modified
- Blocks merge if tests fail
- Provides test results in PR comments

**Quality Gates**:
1. Foundation SPEC Tests
2. Coverage Threshold Check
3. Performance Regression Check
4. Security Scan
5. **Comprehensive API Test Suite** ⭐
6. Code Quality Check

## Local Testing

### Using Makefile Commands

```bash
# Run all comprehensive API tests
make test-api-comprehensive

# Run with coverage
make test-api-comprehensive-coverage

# Run specific test suites
make test-api-suite      # Comprehensive suite (39 tests)
make test-api-auth       # Authentication flows (6 tests)
make test-api-crud       # CRUD operations (12 tests)
make test-api-ports      # Port allocation (SPEC-086, 6 tests)

# Run all API integration tests
make test-api-all
```

### Using pytest Directly

```bash
# Activate conda environment
conda activate nina

# Run all comprehensive tests
pytest tests/integration/test_comprehensive_api_suite.py \
       tests/integration/test_api_authentication_flows.py \
       tests/integration/test_api_crud_operations.py \
       tests/integration/test_port_allocation.py \
       -v

# Run with coverage
pytest tests/integration/test_comprehensive_api_suite.py \
       tests/integration/test_api_authentication_flows.py \
       tests/integration/test_api_crud_operations.py \
       tests/integration/test_port_allocation.py \
       --cov=server --cov-report=html --cov-report=term -v

# Run specific test class
pytest tests/integration/test_comprehensive_api_suite.py::TestHealthEndpoints -v

# Run with HTML report
pytest tests/integration/test_comprehensive_api_suite.py \
       --html=test-report.html --self-contained-html -v
```

## CI/CD Configuration

### Environment Variables

The tests use the following environment variables (configured in CI):

```bash
TEST_API_BASE_URL=http://localhost:13390  # API base URL
TEST_API_TIMEOUT=30                        # Request timeout in seconds
NINA_RUNTIME=docker                        # Runtime type (docker/colima/apple)
NINA_ENV=dev                              # Environment (dev/test/prod)
API_PORT=13390                            # API port for port allocation tests
PGBOUNCER_PORT=6432                       # PgBouncer port
DATABASE_URL=postgresql://...             # Database connection string
REDIS_URL=redis://localhost:6379/0        # Redis connection string
JWT_SECRET=test-jwt-secret-for-ci         # JWT secret for testing
```

### Services Required in CI

The GitHub Actions workflow automatically sets up:

- **PostgreSQL** (pgvector/pgvector:pg15)
  - Port: 5432
  - Database: ninaivalaigal_test
  - Extensions: vector, age

- **Redis** (redis:7-alpine)
  - Port: 6379

- **API Server** (started automatically)
  - Port: 13390
  - Started via `uvicorn main:app`

## Test Results and Reporting

### Artifacts Generated

The CI/CD pipeline generates:

1. **JUnit XML Reports**: `test-results-*.xml`
   - Compatible with most CI/CD systems
   - Can be uploaded to test reporting tools

2. **HTML Reports**: `test-report.html`
   - Self-contained HTML report
   - Viewable in browser
   - Includes test results and timing

3. **Coverage Reports**: `htmlcov/` (if coverage enabled)
   - HTML coverage report
   - Line-by-line coverage details

### PR Comments

When tests run in a pull request, the workflow automatically:

1. Posts a comment with test results summary
2. Shows total tests, passed, failed, errors
3. Indicates if all tests passed
4. Provides links to test artifacts

### GitHub Actions Summary

The workflow adds a summary to the GitHub Actions run:

- Test execution summary with statistics
- Pass/fail indicators
- Quick status overview

## Monitoring and Maintenance

### Test Coverage Tracking

Monitor test coverage trends:

```bash
# Generate coverage report
make test-api-comprehensive-coverage

# View in browser
open htmlcov/index.html
```

### Updating Tests

When adding new API endpoints:

1. Add tests to appropriate test file:
   - `test_comprehensive_api_suite.py` for general endpoints
   - `test_api_authentication_flows.py` for auth flows
   - `test_api_crud_operations.py` for CRUD operations
   - `test_port_allocation.py` for infrastructure tests

2. Ensure tests follow existing patterns
3. Run tests locally before pushing
4. Check CI results in PR

### Troubleshooting CI Failures

Common issues and solutions:

**Issue**: API server not starting
- Check PostgreSQL/Redis are ready
- Verify environment variables are set
- Check API server logs in artifacts

**Issue**: Tests timing out
- Increase `TEST_API_TIMEOUT` environment variable
- Check if API server is responding at `/health`
- Review test execution logs

**Issue**: Authentication failures
- Verify `JWT_SECRET` is set correctly
- Check if test user exists in database
- Review authentication flow tests

## Best Practices

1. **Run Tests Locally First**
   ```bash
   make test-api-comprehensive
   ```

2. **Check PR Quality Gates**
   - All quality gates must pass before merge
   - Review test results in PR comments

3. **Keep Tests Updated**
   - Update tests when API changes
   - Add tests for new endpoints
   - Remove obsolete tests

4. **Monitor Coverage**
   - Aim for 80%+ coverage on API endpoints
   - Review coverage reports regularly

5. **Use Appropriate Test Levels**
   - Integration tests for API endpoints
   - Unit tests for business logic
   - E2E tests for complete workflows

## Continuous Validation

The comprehensive API test suite runs:

- **On Every Push** to main/develop
- **On Every PR** to main/develop
- **On Manual Dispatch** via GitHub Actions UI
- **In PR Quality Gates** (when API code changes)

## Related Documentation

- [Test Suite README](README_API_TEST_SUITE.md)
- [Testing Strategy](../docs/TESTING_STRATEGY.md)
- [CI/CD Pipeline Architecture](../../specs/016-cicd-pipeline-architecture/)

## Support

For issues or questions:

1. Check test logs in GitHub Actions artifacts
2. Review PR comments for test results
3. Run tests locally to reproduce issues
4. Consult test documentation

---

**Last Updated**: 2025-01-XX
**Status**: ✅ Production Ready
