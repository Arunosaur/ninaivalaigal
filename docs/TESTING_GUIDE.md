# Testing & CI Documentation

**Version**: 2.0
**Last Updated**: September 27, 2024
**Audience**: Developers, QA Engineers, DevOps Teams

## 🧪 **Testing Strategy Overview**

Ninaivalaigal employs a comprehensive testing strategy with multiple layers of validation to ensure enterprise-grade reliability and performance. Our testing approach covers unit tests, integration tests, functional tests, chaos testing, and comprehensive coverage validation.

## 🏗️ **Testing Architecture**

### **Testing Pyramid**
```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Comprehensive workflows
                    │   (Functional)  │
                ┌───┴─────────────────┴───┐
                │   Integration Tests     │  ← Component interactions
                │   (API + Database)      │
            ┌───┴─────────────────────────┴───┐
            │      Unit Tests                 │  ← Individual components
            │   (Functions + Classes)         │
        ┌───┴─────────────────────────────────┴───┐
        │         Static Analysis                 │  ← Code quality & security
        │    (Linting + Type Checking)            │
    └─────────────────────────────────────────────┘
```

### **Coverage Targets**
- **Unit Tests**: 90% coverage threshold
- **Integration Tests**: 80% coverage threshold
- **Functional Tests**: 70% coverage threshold
- **Overall Coverage**: 85% combined target
- **Critical Modules**: 95% coverage requirement (auth, memory, RBAC)

## 🔧 **Local Development Testing**

### **1. Setting Up Test Environment**

#### **Prerequisites**
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-mock coverage[toml]

# Install development tools
pip install black flake8 mypy pre-commit

# Setup pre-commit hooks
pre-commit install
```

#### **Environment Configuration**
```bash
# Copy test environment template
cp .env.test.example .env.test

# Configure test database
export DATABASE_URL="postgresql://postgres:test_password@localhost:5432/ninaivalaigal_test"  # pragma: allowlist secret
export REDIS_URL="redis://localhost:6379/1"
export ENVIRONMENT="test"
```

### **2. Running Local Stack**

#### **Start Test Infrastructure**
```bash
# Start complete test stack
make test-stack-up

# Or start individual components
make test-db-start      # PostgreSQL + pgvector
make test-redis-start   # Redis cache
make test-api-start     # FastAPI server
```

#### **Verify Stack Health**
```bash
# Check all services
make test-stack-status

# Individual health checks
curl http://localhost:13370/health
curl http://localhost:13370/health/detailed
curl http://localhost:13370/memory/health
```

### **3. Running Tests Locally**

#### **Unit Tests**
```bash
# Run all unit tests
make test-unit

# Run specific test modules
pytest tests/unit/test_memory_providers.py -v
pytest tests/unit/test_sharing_contracts.py -v
pytest tests/unit/test_rbac_integration.py -v

# Run with coverage
pytest tests/unit/ --cov=server --cov-report=html --cov-report=term
```

#### **Integration Tests**
```bash
# Run all integration tests
make test-integration

# Run specific integration suites
pytest tests/integration/test_provider_integration.py -v
pytest tests/integration/test_sharing_integration.py -v
pytest tests/integration/test_api_integration.py -v

# Run with database
pytest tests/integration/ --cov=server --cov-report=xml
```

#### **Functional Tests**
```bash
# Run all functional tests
make test-functional

# Run E2E test matrix
python tests/e2e/test_foundation_matrix.py

# Run specific functional scenarios
pytest tests/functional/test_memory_workflows.py -v
pytest tests/functional/test_sharing_workflows.py -v
```

#### **Chaos Testing**
```bash
# Run chaos testing suite
make test-chaos

# Run specific chaos scenarios
python tests/chaos/chaos_testing_suite.py

# Run individual chaos tests
pytest tests/chaos/test_database_failures.py -v
pytest tests/chaos/test_redis_failures.py -v
pytest tests/chaos/test_concurrent_load.py -v
```

## 📊 **Coverage Validation**

### **1. Running Coverage Analysis**

#### **Comprehensive Coverage Validation**
```bash
# Run complete coverage validation
make test-coverage-validation

# Generate coverage reports
python tests/coverage/coverage_validator.py

# View HTML coverage report
open htmlcov/index.html
```

#### **Coverage by Test Type**
```bash
# Unit test coverage
pytest tests/unit/ --cov=server --cov-report=html:htmlcov-unit

# Integration test coverage
pytest tests/integration/ --cov=server --cov-report=html:htmlcov-integration

# Functional test coverage
pytest tests/functional/ --cov=server --cov-report=html:htmlcov-functional

# Combined coverage
pytest tests/ --cov=server --cov-report=html:htmlcov-combined
```

### **2. Coverage Quality Gates**

#### **Enforcing Coverage Thresholds**
```bash
# Enforce unit test threshold (90%)
pytest tests/unit/ --cov=server --cov-fail-under=90

# Enforce integration test threshold (80%)
pytest tests/integration/ --cov=server --cov-fail-under=80

# Enforce functional test threshold (70%)
pytest tests/functional/ --cov=server --cov-fail-under=70

# Enforce overall threshold (85%)
pytest tests/ --cov=server --cov-fail-under=85
```

#### **Coverage Report Generation**
```python
# Generate detailed coverage report
from tests.coverage.coverage_validator import CoverageValidator

validator = CoverageValidator()
results = await validator.run_comprehensive_coverage_validation()

print(f"Overall Coverage: {results['overall_assessment']['overall_coverage_percentage']:.1f}%")
print(f"Quality Gates Passed: {results['overall_assessment']['quality_gates_passed']}")
```

## 🚀 **CI/CD Testing Pipeline**

### **1. GitHub Actions Workflow**

#### **Comprehensive Test Validation Workflow**
```yaml
# .github/workflows/comprehensive-test-validation.yml
name: SPEC-052 Comprehensive Test Validation

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

env:
  COVERAGE_THRESHOLD_UNIT: 90
  COVERAGE_THRESHOLD_INTEGRATION: 80
  COVERAGE_THRESHOLD_FUNCTIONAL: 70
  COVERAGE_THRESHOLD_OVERALL: 85

jobs:
  foundation-validation:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password_123
          POSTGRES_DB: ninaivalaigal_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-mock coverage[toml]

      - name: Unit Test Coverage Validation
        run: |
          pytest tests/unit/ \
            --cov=server \
            --cov-report=xml:coverage-unit.xml \
            --cov-report=html:htmlcov-unit \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD_UNIT }} \
            -v

      - name: Integration Test Coverage Validation
        run: |
          pytest tests/integration/ \
            --cov=server \
            --cov-report=xml:coverage-integration.xml \
            --cov-report=html:htmlcov-integration \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD_INTEGRATION }} \
            -v

      - name: Functional Test Coverage Validation
        run: |
          pytest tests/functional/ \
            --cov=server \
            --cov-report=xml:coverage-functional.xml \
            --cov-report=html:htmlcov-functional \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD_FUNCTIONAL }} \
            -v

      - name: E2E Foundation Matrix Validation
        run: |
          python tests/e2e/test_foundation_matrix.py

      - name: Chaos Testing Validation
        run: |
          python tests/chaos/chaos_testing_suite.py

      - name: Quality Gate Enforcement
        run: |
          # Comprehensive quality gate validation
          python tests/coverage/coverage_validator.py
```

### **2. Test Execution Strategies**

#### **Parallel Test Execution**
```bash
# Run tests in parallel for faster execution
pytest tests/unit/ -n auto --dist=loadscope
pytest tests/integration/ -n 4 --dist=loadfile
pytest tests/functional/ -n 2 --dist=loadgroup
```

#### **Test Selection & Filtering**
```bash
# Run tests by markers
pytest -m "unit" tests/
pytest -m "integration" tests/
pytest -m "functional" tests/
pytest -m "chaos" tests/

# Run tests by pattern
pytest -k "test_memory" tests/
pytest -k "test_sharing" tests/
pytest -k "test_provider" tests/

# Run failed tests only
pytest --lf tests/
pytest --ff tests/
```

#### **Test Environment Matrix**
```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
    postgres-version: ['15', '16']
    redis-version: ['7', '7-alpine']
    test-type: ['unit', 'integration', 'functional']
```

## 🔥 **Chaos Testing Guide**

### **1. Chaos Testing Scenarios**

#### **Database Failure Scenarios**
```python
# Test database connection loss
async def test_database_connection_loss():
    """Test API behavior when database connection is lost"""

    # Baseline functionality test
    response = await client.get("/health")
    assert response.status_code == 200

    # Simulate database connection issues
    # (In real scenario, temporarily block database connections)

    # Test API graceful degradation
    for i in range(10):
        try:
            response = await client.get("/health/detailed")
            # Should handle gracefully or return appropriate error
        except Exception as e:
            # Expected during database issues
            pass

    # Test recovery
    # (Restore database connection)

    # Verify recovery
    response = await client.get("/health")
    assert response.status_code == 200
```

#### **Redis Failure Scenarios**
```python
# Test Redis connection loss
async def test_redis_failure_graceful_degradation():
    """Test system behavior when Redis is unavailable"""

    # Test Redis connectivity
    await redis_client.ping()

    # Simulate Redis failure
    # (Block Redis connections or stop Redis service)

    # Test API functionality without Redis (should degrade gracefully)
    response = await client.get("/memory/recall", json={"query": "test"})
    # Should work but may be slower without cache

    # Test cache fallback mechanisms
    # Verify database queries work without Redis cache
```

#### **Concurrent Load Scenarios**
```python
# Test concurrent API requests
async def test_concurrent_api_load():
    """Test API behavior under concurrent load"""

    async def make_request(request_id: int):
        try:
            response = await client.get("/health")
            return {"id": request_id, "status": response.status_code}
        except Exception as e:
            return {"id": request_id, "error": str(e)}

    # Launch 50 concurrent requests
    tasks = [make_request(i) for i in range(50)]
    results = await asyncio.gather(*tasks)

    # Analyze results
    successful = sum(1 for r in results if r.get("status") == 200)
    failed = len(results) - successful

    assert successful >= 45  # Allow some failures under load
    assert failed <= 5
```

### **2. Chaos Testing Execution**

#### **Running Chaos Tests**
```bash
# Run all chaos tests
make test-chaos

# Run specific chaos scenarios
python tests/chaos/test_database_failures.py
python tests/chaos/test_redis_failures.py
python tests/chaos/test_concurrent_load.py
python tests/chaos/test_resource_exhaustion.py

# Run chaos tests with reporting
python tests/chaos/chaos_testing_suite.py --generate-report
```

#### **Chaos Test Configuration**
```yaml
# chaos_config.yml
chaos_testing:
  database_scenarios:
    connection_loss_duration: 30  # seconds
    performance_degradation_factor: 5  # 5x slower
    recovery_timeout: 60  # seconds

  redis_scenarios:
    memory_pressure_mb: 100
    connection_timeout: 5  # seconds
    failover_timeout: 10  # seconds

  load_scenarios:
    concurrent_requests: 50
    sustained_duration: 60  # seconds
    ramp_up_time: 10  # seconds
```

## 📋 **Test Organization & Structure**

### **1. Test Directory Structure**
```
tests/
├── unit/                          # Unit tests (90% coverage target)
│   ├── test_memory_providers.py   # Memory provider unit tests
│   ├── test_sharing_contracts.py  # Sharing contract unit tests
│   ├── test_consent_manager.py    # Consent management unit tests
│   ├── test_temporal_access.py    # Temporal access unit tests
│   ├── test_audit_logger.py       # Audit logging unit tests
│   └── test_rbac_integration.py   # RBAC integration unit tests
├── integration/                   # Integration tests (80% coverage target)
│   ├── test_provider_integration.py    # Provider integration tests
│   ├── test_sharing_integration.py     # Sharing workflow integration
│   ├── test_api_integration.py         # API endpoint integration
│   └── test_database_integration.py    # Database integration tests
├── functional/                    # Functional tests (70% coverage target)
│   ├── test_memory_workflows.py        # End-to-end memory workflows
│   ├── test_sharing_workflows.py       # End-to-end sharing workflows
│   ├── test_user_workflows.py          # User journey testing
│   └── test_admin_workflows.py         # Admin workflow testing
├── e2e/                          # End-to-end test matrix
│   ├── test_foundation_matrix.py       # Foundation SPEC validation
│   └── test_cross_component.py         # Cross-component integration
├── chaos/                        # Chaos testing suite
│   ├── chaos_testing_suite.py          # Main chaos testing framework
│   ├── test_database_failures.py       # Database failure scenarios
│   ├── test_redis_failures.py          # Redis failure scenarios
│   ├── test_concurrent_load.py         # Load testing scenarios
│   └── test_resource_exhaustion.py     # Resource exhaustion tests
├── coverage/                     # Coverage validation
│   ├── coverage_validator.py           # Coverage analysis tool
│   └── test_coverage_reports.py        # Coverage reporting tests
├── fixtures/                     # Test fixtures and data
│   ├── memory_fixtures.py              # Memory test data
│   ├── user_fixtures.py                # User test data
│   └── sharing_fixtures.py             # Sharing test data
└── conftest.py                   # Pytest configuration and fixtures
```

### **2. Test Naming Conventions**

#### **Test File Naming**
- Unit tests: `test_{module_name}.py`
- Integration tests: `test_{component}_integration.py`
- Functional tests: `test_{workflow}_workflows.py`
- Chaos tests: `test_{scenario}_failures.py`

#### **Test Function Naming**
```python
# Unit test naming
def test_memory_provider_creation_success():
def test_memory_provider_creation_invalid_config():
def test_memory_provider_health_check_healthy():
def test_memory_provider_health_check_unhealthy():

# Integration test naming
def test_provider_registry_integration_with_health_monitor():
def test_sharing_contract_integration_with_audit_logger():

# Functional test naming
def test_complete_memory_sharing_workflow():
def test_temporal_access_expiration_workflow():

# Chaos test naming
def test_database_connection_loss_recovery():
def test_redis_memory_pressure_graceful_degradation():
```

### **3. Test Fixtures & Utilities**

#### **Common Test Fixtures**
```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

@pytest.fixture
async def mock_database():
    """Mock database connection for unit tests"""
    mock_db = AsyncMock()
    mock_db.execute.return_value = Mock()
    mock_db.fetch.return_value = []
    return mock_db

@pytest.fixture
async def mock_redis():
    """Mock Redis client for unit tests"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.ping.return_value = True
    return mock_redis

@pytest.fixture
async def test_memory():
    """Sample memory for testing"""
    return {
        "memory_id": "test-memory-123",
        "content": "Test memory content",
        "context": "test/context",
        "metadata": {"importance": "high", "tags": ["test"]}
    }

@pytest.fixture
async def test_user():
    """Sample user for testing"""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
```

#### **Test Utilities**
```python
# tests/utils/test_helpers.py
import asyncio
from typing import Any, Dict, List

class TestDataFactory:
    """Factory for generating test data"""

    @staticmethod
    def create_memory(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        base_memory = {
            "memory_id": "test-memory-123",
            "content": "Test memory content",
            "context": "test/context",
            "metadata": {"importance": "medium"}
        }
        if overrides:
            base_memory.update(overrides)
        return base_memory

    @staticmethod
    def create_sharing_contract(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        base_contract = {
            "contract_id": "test-contract-123",
            "memory_id": "test-memory-123",
            "permissions": ["view", "comment"],
            "status": "active"
        }
        if overrides:
            base_contract.update(overrides)
        return base_contract

async def wait_for_condition(condition_func, timeout: int = 10, interval: float = 0.1):
    """Wait for a condition to become true"""
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)

    return False

def assert_memory_equal(actual: Dict, expected: Dict, ignore_fields: List[str] = None):
    """Assert two memories are equal, ignoring specified fields"""
    ignore_fields = ignore_fields or ["created_at", "updated_at"]

    for key, value in expected.items():
        if key not in ignore_fields:
            assert actual.get(key) == value, f"Field {key} mismatch: {actual.get(key)} != {value}"
```

## 🎯 **Foundation SPEC Testing**

### **1. SPEC-Specific Test Validation**

#### **SPEC-007: Unified Context Scope System**
```python
# tests/unit/test_spec_007_context_scope.py
class TestUnifiedContextScope:
    async def test_scope_hierarchy_validation(self):
        """Test context scope hierarchy validation"""
        # Test user scope creation
        # Test team scope creation with user members
        # Test organization scope with team hierarchy
        # Test permission inheritance

    async def test_cross_scope_permissions(self):
        """Test permissions across different scopes"""
        # Test user-to-user permissions
        # Test user-to-team permissions
        # Test team-to-organization permissions

    async def test_scope_isolation(self):
        """Test scope isolation and security"""
        # Test data isolation between scopes
        # Test unauthorized cross-scope access prevention
```

#### **SPEC-020: Memory Provider Architecture**
```python
# tests/integration/test_spec_020_provider_architecture.py
class TestMemoryProviderArchitecture:
    async def test_provider_auto_discovery(self):
        """Test automatic provider discovery"""
        # Test PostgreSQL provider discovery
        # Test HTTP provider discovery
        # Test provider registration

    async def test_intelligent_failover(self):
        """Test provider failover scenarios"""
        # Test priority-based failover
        # Test health-based failover
        # Test performance-based failover

    async def test_security_integration(self):
        """Test provider security features"""
        # Test RBAC integration
        # Test API key management
        # Test audit logging
```

#### **SPEC-049: Memory Sharing Collaboration**
```python
# tests/functional/test_spec_049_sharing_collaboration.py
class TestMemorySharingCollaboration:
    async def test_cross_scope_sharing_workflow(self):
        """Test complete cross-scope sharing workflow"""
        # Test contract creation
        # Test consent management
        # Test temporal access
        # Test audit trail

    async def test_permission_granularity(self):
        """Test granular permission system"""
        # Test VIEW permission
        # Test COMMENT permission
        # Test EDIT permission
        # Test SHARE permission
        # Test ADMIN permission
```

#### **SPEC-052: Comprehensive Test Coverage**
```python
# tests/e2e/test_spec_052_test_coverage.py
class TestComprehensiveTestCoverage:
    async def test_coverage_validation(self):
        """Test coverage validation system"""
        # Test unit test coverage calculation
        # Test integration test coverage
        # Test functional test coverage
        # Test quality gate enforcement

    async def test_chaos_testing_framework(self):
        """Test chaos testing capabilities"""
        # Test database failure simulation
        # Test Redis failure simulation
        # Test concurrent load testing
        # Test resource exhaustion testing
```

### **2. Cross-Component Integration Testing**

#### **Provider + Sharing Integration**
```python
async def test_provider_sharing_integration():
    """Test integration between provider architecture and sharing system"""

    # Create memory using provider system
    memory = await provider_registry.create_memory(content, context, metadata)

    # Share memory using sharing system
    contract = await sharing_manager.create_contract(memory.id, target_scope, permissions)

    # Access shared memory through provider system
    shared_memory = await provider_registry.recall_memory(memory.id, target_user_id)

    # Verify audit trail
    audit_events = await audit_logger.get_events(memory.id)
    assert len(audit_events) >= 3  # create, share, access
```

#### **RBAC + All Components Integration**
```python
async def test_rbac_comprehensive_integration():
    """Test RBAC integration across all foundation components"""

    # Test RBAC with provider management
    assert await rbac.check_permission(user_id, "provider:register")

    # Test RBAC with sharing contracts
    assert await rbac.check_permission(user_id, "memory:share")

    # Test RBAC with temporal access
    assert await rbac.check_permission(user_id, "access:grant")

    # Test RBAC with audit access
    assert await rbac.check_permission(admin_id, "audit:view")
```

## 📊 **Test Reporting & Analytics**

### **1. Test Result Reporting**

#### **Automated Test Reports**
```python
# Generate comprehensive test report
class TestReportGenerator:
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        return {
            "execution_summary": {
                "total_tests": self.count_total_tests(),
                "passed_tests": self.count_passed_tests(),
                "failed_tests": self.count_failed_tests(),
                "skipped_tests": self.count_skipped_tests(),
                "execution_time": self.get_execution_time()
            },
            "coverage_analysis": {
                "unit_coverage": self.get_unit_coverage(),
                "integration_coverage": self.get_integration_coverage(),
                "functional_coverage": self.get_functional_coverage(),
                "overall_coverage": self.get_overall_coverage()
            },
            "quality_gates": {
                "coverage_gates_passed": self.check_coverage_gates(),
                "performance_gates_passed": self.check_performance_gates(),
                "security_gates_passed": self.check_security_gates()
            },
            "foundation_spec_validation": {
                "spec_007_status": self.validate_spec_007(),
                "spec_020_status": self.validate_spec_020(),
                "spec_049_status": self.validate_spec_049(),
                "spec_052_status": self.validate_spec_052()
            }
        }
```

#### **CI/CD Integration Reports**
```bash
# Generate reports for CI/CD
pytest tests/ --junitxml=test-results.xml --cov=server --cov-report=xml

# Upload to coverage services
codecov -f coverage.xml

# Generate badges
coverage-badge -o coverage.svg
```

### **2. Performance & Trend Analysis**

#### **Test Performance Monitoring**
```python
# Monitor test execution performance
class TestPerformanceMonitor:
    def track_test_performance(self, test_name: str, execution_time: float):
        """Track individual test performance"""
        self.performance_data[test_name].append({
            "timestamp": datetime.now(),
            "execution_time": execution_time,
            "status": "passed" if execution_time < self.thresholds[test_name] else "slow"
        })

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate test performance analysis"""
        return {
            "slowest_tests": self.get_slowest_tests(10),
            "performance_trends": self.analyze_trends(),
            "threshold_violations": self.get_threshold_violations()
        }
```

---

**This comprehensive testing guide ensures that all team members can effectively contribute to maintaining the high-quality, enterprise-grade testing standards that make Ninaivalaigal production-ready.**
