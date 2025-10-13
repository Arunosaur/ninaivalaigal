# Testing Strategy: ninaivalaigal Platform

**Last Updated:** October 12, 2025
**Owner:** QA & Platform Engineering

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Types](#test-types)
4. [Test Pyramid](#test-pyramid)
5. [Test Infrastructure](#test-infrastructure)
6. [Running Tests](#running-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Coverage Goals](#coverage-goals)
9. [Best Practices](#best-practices)

---

## 1. Overview

ninaivalaigal uses a comprehensive, multi-layer testing strategy:

| Test Type | Purpose | Speed | Coverage |
|-----------|---------|-------|----------|
| Unit Tests | Individual functions | Fast | 80% target |
| Integration Tests | API endpoints | Medium | Key flows |
| Agentic Tests | UI user flows | Slow | Critical paths |
| E2E Tests | Full stack | Slowest | Happy paths |

**Total Tests:** 100+ test cases
**Coverage:** 11% (growing to 80%)
**Frameworks:** pytest, Playwright, Ollama/OpenAI

---

## 2. Testing Philosophy

### Our Principles

✅ **Test What Matters**
- Focus on business-critical paths
- Don't test framework code
- Test behavior, not implementation

✅ **Fast Feedback**
- Unit tests run in seconds
- Integration tests in minutes
- Agentic tests nightly

✅ **Reliable Tests**
- No flaky tests tolerated
- Deterministic outcomes
- Proper mocking

✅ **Maintainable Tests**
- Clear test names
- Well-documented
- DRY principles

### Test-Driven Development

We encourage TDD:
1. Write failing test
2. Implement feature
3. Test passes
4. Refactor

---

## 3. Test Types

### Unit Tests

**What:** Test individual functions in isolation

**Example:**
```python
def test_hash_password():
    password = "SecurePass123!"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert verify_password(password, hashed)
```

**When to use:**
- Testing pure functions
- Business logic
- Utility functions
- Edge cases

**Tools:** pytest, unittest.mock

### Integration Tests

**What:** Test API endpoints with real database

**Example:**
```python
def test_login_endpoint(client, test_user):
    response = client.post('/auth/login', json={
        'email': test_user.email,
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'jwt_token' in response.json()['user']
```

**When to use:**
- Testing API endpoints
- Database interactions
- Authentication flows

**Tools:** pytest, TestClient, fixtures

### Agentic Tests (UI)

**What:** LLM-powered tests that navigate UI like a human

**Example:**
```python
async def test_signup_flow_agentic(page, llm_agent):
    await llm_agent.navigate_to('http://localhost:3000')
    await llm_agent.complete_task('Sign up with email test@example.com')

    # LLM figures out how to click buttons, fill forms
    assert await llm_agent.verify('User is logged in')
```

**When to use:**
- Critical user journeys
- UI regression testing
- Cross-browser testing

**Tools:** Playwright, OpenAI/Ollama

### End-to-End Tests

**What:** Complete user flows across entire stack

**Example:**
```python
def test_complete_memory_lifecycle(client, authenticated_user):
    # Create context
    context = create_context(client, 'test-context')

    # Store memory
    memory = store_memory(client, context.id, 'Test data')

    # Recall memory
    results = recall_memories(client, 'Test')
    assert memory.id in [r.id for r in results]

    # Delete memory
    delete_memory(client, memory.id)

    # Verify deleted
    results = recall_memories(client, 'Test')
    assert memory.id not in [r.id for r in results]
```

---

## 4. Test Pyramid

```
        /\\\
       /  \\\
      / UI \\\\        Agentic Tests (Slow, Few)
     /------\\\
    /        \\\
   / Integra \\\\     API Tests (Medium, More)
  / tion      \\\
 /------------\\\
/              \\\
/  Unit Tests  \\\\   Function Tests (Fast, Many)
/________________\\\
```

**Ratio:** 70% Unit, 20% Integration, 10% UI

---

## 5. Test Infrastructure

### pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    agentic: Agentic UI tests
    slow: Slow tests
```

### Test Fixtures

**File:** `conftest.py`

Common fixtures:
- `client`: TestClient for API tests
- `db_session`: Database session
- `test_user`: Sample user for auth
- `authenticated_client`: Pre-authenticated client

### Test Commands

**Makefile targets:**

```bash
make test                 # All tests
make test-unit           # Unit tests only
make test-integration    # Integration tests
make test-agentic        # Agentic tests (hybrid)
make test-agentic-openai # Force OpenAI
make test-agentic-ollama # Force Ollama (free)
make test-coverage       # With coverage report
```

---

## 6. Running Tests

### Local Development

```bash
# Quick test (unit tests only)
make test-unit

# Before commit (unit + integration)
make test

# Full suite (all tests)
make test-all
```

### With Coverage

```bash
# Generate coverage report
make test-coverage

# View HTML report
open htmlcov/index.html
```

### Specific Test File

```bash
# Run one file
pytest tests/test_signup.py -v

# Run one test
pytest tests/test_signup.py::test_login_success -v

# With debugging
pytest tests/test_signup.py -vv -s
```

---

## 7. CI/CD Integration

### GitHub Actions Workflows

**On Every Push:**
- Unit tests
- Integration tests
- Code coverage
- Linting

**Nightly:**
- Agentic tests (with Ollama)
- Performance tests
- Database migrations

**On Release:**
- Full test suite
- Security scans
- E2E tests

### Workflow Files

1. **test-auth.yml**: Auth tests with coverage
2. **agentic-nightly.yml**: UI tests with Ollama
3. **ci.yml**: Main CI pipeline (if exists)

### Test Services

CI provides:
- PostgreSQL 15
- Redis 7
- Ollama (for agentic tests)

---

## 8. Coverage Goals

### Current Status

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| auth.py | 45% | 100% | Critical |
| memory_api.py | 30% | 90% | High |
| database/ | 60% | 80% | Medium |
| Overall | 11% | 80% | - |

### Critical Modules (100% target)

- Authentication
- Authorization (RBAC)
- Payment processing
- Security middleware

### High Priority (90% target)

- Memory operations
- Context management
- User management

### Medium Priority (80% target)

- Database operations
- Caching (Redis)
- Background jobs

---

## 9. Best Practices

### Writing Good Tests

✅ **DO:**
```python
def test_user_can_login_with_valid_credentials():
    # Arrange
    user = create_test_user(email='test@example.com')

    # Act
    response = login(email='test@example.com', password='password123')

    # Assert
    assert response.success is True
    assert response.jwt_token is not None
```

❌ **DON'T:**
```python
def test_stuff():  # Vague name
    # No arrange/act/assert structure
    u = User()  # Unclear
    assert u  # Tests nothing meaningful
```

### Test Naming

✅ **Good:** `test_user_cannot_login_with_invalid_password`
❌ **Bad:** `test_login_2`

Pattern: `test_[unit]_[scenario]_[expected_result]`

### Test Independence

✅ **DO:**
- Each test creates its own data
- Tests can run in any order
- Clean up after tests

❌ **DON'T:**
- Rely on test execution order
- Share state between tests
- Leave test data in database

### Mocking

✅ **When to mock:**
- External APIs
- Slow operations
- Non-deterministic code (random, time)

❌ **When NOT to mock:**
- Your own business logic
- Database in integration tests
- Simple functions

---

## 10. Troubleshooting

### Common Issues

**Issue:** Tests fail locally but pass in CI
```bash
# Solution: Check environment variables
env | grep TEST_

# Ensure database is clean
make db-reset-test
```

**Issue:** Flaky tests
```bash
# Solution: Add explicit waits
await page.wait_for_selector('#element')

# Or increase timeouts
pytest tests/ --timeout=60
```

**Issue:** Slow tests
```bash
# Solution: Profile tests
pytest tests/ --durations=10

# Parallelize
pytest tests/ -n auto
```

---

## Appendix: Test Categories

### Security Tests
- Authentication bypass attempts
- Authorization violations
- SQL injection prevention
- XSS prevention

### Performance Tests
- Response time < 200ms
- Concurrent user handling
- Database query optimization

### Regression Tests
- Known bug fixes
- Critical user flows
- Edge cases

---

**Document Version:** 1.0
**Last Updated:** October 12, 2025
**Maintained By:** QA Team + Developer C
