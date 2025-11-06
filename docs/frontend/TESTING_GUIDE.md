# Frontend Testing Guide

**Version:** 2.0 (FastAPI Templating)
**Last Updated:** January 2025
**Status:** Production
**References:** SPEC-016 (CI/CD), General Testing Guide

---

## Overview

This guide covers testing for the FastAPI-based frontend (customer and admin UIs). Since the frontend is server-rendered with Jinja2 templates, testing focuses on server-side tests rather than client-side JavaScript tests.

---

## Testing Strategy

### Testing Pyramid

```
        ┌─────────────────┐
        │  E2E Tests      │  ← Full user workflows
        │  (Playwright)   │
    ┌───┴─────────────────┴───┐
    │  Integration Tests       │  ← API + Template rendering
    │  (FastAPI TestClient)    │
┌───┴─────────────────────────┴───┐
│  Unit Tests                     │  ← Template macros, utilities
│  (Pytest + Jinja2)             │
└─────────────────────────────────┘
```

### Test Coverage Targets

- **Unit Tests**: 90% coverage
- **Integration Tests**: 80% coverage
- **E2E Tests**: Critical user workflows only
- **Overall Coverage**: 85% combined target

---

## Unit Tests

### Template Macro Tests

Test Jinja2 macros in isolation:

```python
# tests/frontend/test_template_macros.py
import pytest
from jinja2 import Environment, FileSystemLoader

def test_memory_card_macro():
    """Test memory_card macro renders correctly"""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('components/cards.html')

    memory = {
        'id': '123',
        'title': 'Test Memory',
        'content': 'Test content'
    }

    rendered = template.module.memory_card(memory, show_actions=True)

    assert 'Test Memory' in rendered
    assert 'Test content' in rendered
    assert 'View' in rendered
    assert 'Edit' in rendered
```

### Utility Function Tests

Test helper functions used in templates:

```python
# tests/frontend/test_utils.py
from lib.customer.utils import format_date, truncate_text

def test_format_date():
    """Test date formatting utility"""
    from datetime import datetime
    date = datetime(2025, 1, 15, 10, 30)
    assert format_date(date) == 'Jan 15, 2025'

def test_truncate_text():
    """Test text truncation utility"""
    text = 'A' * 200
    truncated = truncate_text(text, max_length=100)
    assert len(truncated) <= 103  # 100 + '...'
    assert truncated.endswith('...')
```

---

## Integration Tests

### Route Handler Tests

Test FastAPI routes with template rendering:

```python
# tests/frontend/test_customer_routes.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_customer_dashboard():
    """Test customer dashboard route"""
    # Login first
    response = client.post('/auth/login', json={
        'email': 'customer@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200

    # Get dashboard
    response = client.get('/customer/dashboard')
    assert response.status_code == 200
    assert 'Customer Dashboard' in response.text
    assert 'memories' in response.text.lower()
```

### Template Rendering Tests

Test template rendering with various data:

```python
# tests/frontend/test_template_rendering.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_memory_list_template():
    """Test memory list template renders correctly"""
    # Login and get memories page
    client.post('/auth/login', json={
        'email': 'customer@example.com',
        'password': 'password123'
    })

    response = client.get('/customer/memories')
    assert response.status_code == 200

    # Check template structure
    assert 'Memory Browser' in response.text
    assert 'Create Memory' in response.text

    # Check for memory cards (if memories exist)
    # This depends on test data setup
```

### Form Submission Tests

Test form submissions and validation:

```python
# tests/frontend/test_forms.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_memory_form():
    """Test memory creation form submission"""
    # Login
    client.post('/auth/login', json={
        'email': 'customer@example.com',
        'password': 'password123'
    })

    # Submit form
    response = client.post('/customer/memories', data={
        'title': 'Test Memory',
        'content': 'Test content'
    }, follow_redirects=False)

    assert response.status_code == 302  # Redirect after creation
    assert response.headers['location'] == '/customer/memories'

def test_form_validation():
    """Test form validation errors"""
    # Login
    client.post('/auth/login', json={
        'email': 'customer@example.com',
        'password': 'password123'
    })

    # Submit invalid form
    response = client.post('/customer/memories', data={
        'title': '',  # Empty title
        'content': 'Test content'
    })

    assert response.status_code == 200
    assert 'Title is required' in response.text
```

---

## End-to-End Tests

### Playwright Setup

Install Playwright:

```bash
pip install pytest-playwright
playwright install
```

### Basic E2E Test

```python
# tests/e2e/test_customer_workflow.py
import pytest
from playwright.sync_api import Page, expect

def test_customer_login_workflow(page: Page):
    """Test complete customer login workflow"""
    # Navigate to login page
    page.goto('http://localhost:13370/customer/login')

    # Fill login form
    page.fill('input[name="email"]', 'customer@example.com')
    page.fill('input[name="password"]', 'password123')

    # Submit form
    page.click('button[type="submit"]')

    # Wait for redirect to dashboard
    expect(page).to_have_url('http://localhost:13370/customer/dashboard')

    # Verify dashboard content
    expect(page.locator('h1')).to_contain_text('Dashboard')
```

### Memory Management E2E

```python
# tests/e2e/test_memory_management.py
import pytest
from playwright.sync_api import Page, expect

def test_create_memory_workflow(page: Page):
    """Test memory creation workflow"""
    # Login first
    page.goto('http://localhost:13370/customer/login')
    page.fill('input[name="email"]', 'customer@example.com')
    page.fill('input[name="password"]', 'password123')
    page.click('button[type="submit"]')

    # Navigate to create memory page
    page.goto('http://localhost:13370/customer/memories/new')

    # Fill memory form
    page.fill('input[name="title"]', 'E2E Test Memory')
    page.fill('textarea[name="content"]', 'This is a test memory created during E2E testing')

    # Submit form
    page.click('button[type="submit"]')

    # Verify redirect to memory list
    expect(page).to_have_url('http://localhost:13370/customer/memories')

    # Verify memory appears in list
    expect(page.locator('text=E2E Test Memory')).to_be_visible()
```

---

## Running Tests

### Run All Tests

```bash
# Run all frontend tests
pytest tests/frontend/

# Run with coverage
pytest tests/frontend/ --cov=lib/customer --cov=lib/admin --cov-report=html
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/frontend/test_template_macros.py tests/frontend/test_utils.py

# Integration tests only
pytest tests/frontend/test_customer_routes.py tests/frontend/test_template_rendering.py

# E2E tests only
pytest tests/e2e/
```

### Run Tests in CI/CD

See **SPEC-016** for CI/CD integration. Tests run automatically on:

- Pull requests
- Merges to main
- Tag releases

---

## Test Data Setup

### Database Fixtures

```python
# tests/conftest.py
import pytest
from app.database import get_db

@pytest.fixture
def test_db():
    """Create test database and clean up after"""
    # Setup test database
    db = get_db()
    yield db
    # Cleanup
    db.close()
```

### Test Users

```python
# tests/fixtures/test_users.py
@pytest.fixture
def test_customer():
    """Create test customer user"""
    return {
        'email': 'customer@example.com',
        'password': 'password123',
        'role': 'customer'
    }

@pytest.fixture
def test_admin():
    """Create test admin user"""
    return {
        'email': 'admin@example.com',
        'password': 'password123',
        'role': 'admin'
    }
```

---

## Accessibility Testing

### Basic Accessibility Checks

```python
# tests/frontend/test_accessibility.py
import pytest
from playwright.sync_api import Page

def test_page_has_title(page: Page):
    """Test page has title"""
    page.goto('http://localhost:13370/customer/dashboard')
    assert page.title() != ''

def test_forms_have_labels(page: Page):
    """Test forms have proper labels"""
    page.goto('http://localhost:13370/customer/login')

    email_input = page.locator('input[name="email"]')
    label = page.locator('label[for="email"]')

    assert label.is_visible()
    assert email_input.get_attribute('id') == 'email'
```

### Automated Accessibility Testing

```bash
# Install axe-core
npm install -g @axe-core/cli

# Run accessibility scan
axe http://localhost:13370/customer/dashboard
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dashboard_load_time():
    """Test dashboard loads within performance budget"""
    import time

    start = time.time()
    response = client.get('/customer/dashboard')
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5  # 500ms target
```

### Template Rendering Performance

```python
# tests/performance/test_template_performance.py
import pytest
from jinja2 import Environment, FileSystemLoader

def test_template_render_performance():
    """Test template rendering is fast"""
    import time

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('customer/dashboard.html')

    start = time.time()
    rendered = template.render(user={'name': 'Test'}, memories=[])
    duration = time.time() - start

    assert duration < 0.1  # 100ms target for template rendering
```

---

## Best Practices

### 1. Test Isolation

- Each test should be independent
- Use fixtures for setup/teardown
- Clean up test data after each test

### 2. Test Coverage

- Aim for 85% overall coverage
- Focus on critical paths
- Test edge cases and error conditions

### 3. Test Data

- Use realistic test data
- Create fixtures for common test data
- Clean up test data after tests

### 4. Performance

- Keep tests fast (< 1 second per test)
- Use mocks for slow operations
- Run E2E tests separately from unit tests

---

## References

- **SPEC-016**: CI/CD Pipeline Architecture
- **General Testing Guide**: `docs/TESTING_GUIDE.md`
- **Pytest Documentation**: https://docs.pytest.org/
- **Playwright Documentation**: https://playwright.dev/

---

**Status**: ✅ **Production-Ready**
**Last Updated**: January 2025
**Next Review**: After testing validation
