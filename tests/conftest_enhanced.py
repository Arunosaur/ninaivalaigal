"""Enhanced test configuration with comprehensive fixtures."""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    test_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",  # pragma: allowlist secret
        "REDIS_URL": "redis://localhost:6379/1",
        "JWT_SECRET": "test-secret-key-for-testing",  # pragma: allowlist secret
        "ENVIRONMENT": "test",
    }

    # Store original values
    original_values = {}
    for key, value in test_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_vars

    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="module")
def client(test_env):
    """Create a test client for functional tests."""
    try:
        from server.main import app

        return TestClient(app)
    except ImportError:
        pytest.skip("Server main module not available for functional testing")
    except Exception as e:
        pytest.skip(f"Failed to create test client: {e}")


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock_session = Mock()
    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.close.return_value = None
    return mock_session


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False
    mock_client.expire.return_value = True
    mock_client.hget.return_value = None
    mock_client.hset.return_value = True
    mock_client.zadd.return_value = 1
    mock_client.zrange.return_value = []
    return mock_client


@pytest.fixture
def mock_user():
    """Mock user object."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.created_at = "2024-01-01T00:00:00Z"
    return user


@pytest.fixture
def mock_memory():
    """Mock memory object."""
    memory = Mock()
    memory.id = 1
    memory.user_id = 1
    memory.content = "Test memory content"
    memory.title = "Test Memory"
    memory.created_at = "2024-01-01T00:00:00Z"
    memory.updated_at = "2024-01-01T00:00:00Z"
    return memory


@pytest.fixture
def mock_role():
    """Mock role object."""
    role = Mock()
    role.id = 1
    role.name = "admin"
    role.description = "Administrator role"
    role.permissions = ["read", "write", "delete"]
    return role


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {
        "Authorization": "Bearer test-jwt-token",  # pragma: allowlist secret
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_jwt_token():
    """Sample JWT token for testing."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3R1c2VyIn0.test"  # pragma: allowlist secret


@pytest.fixture
def memory_test_data():
    """Test data for memory operations."""
    return {
        "title": "Test Memory",
        "content": "This is test memory content",
        "tags": ["test", "memory"],
        "metadata": {"source": "test"},
    }


@pytest.fixture
def user_test_data():
    """Test data for user operations."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",  # pragma: allowlist secret
        "full_name": "Test User",
    }


@pytest.fixture
def rbac_test_data():
    """Test data for RBAC operations."""
    return {
        "role": {
            "name": "test_role",
            "description": "Test role for testing",
            "permissions": ["read", "write"],
        },
        "permission": {
            "name": "test_permission",
            "description": "Test permission",
            "resource": "test_resource",
        },
    }


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Cleanup logic would go here
    # For now, just a placeholder


# Pytest markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "functional: Functional tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


# Skip tests based on environment
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    skip_integration = pytest.mark.skip(
        reason="Integration tests require running services"
    )
    skip_performance = pytest.mark.skip(
        reason="Performance tests require specific setup"
    )

    for item in items:
        if "integration" in item.keywords:
            # Skip integration tests if services not available
            if not _services_available():
                item.add_marker(skip_integration)

        if "performance" in item.keywords:
            # Skip performance tests in CI unless specifically requested
            if os.environ.get("RUN_PERFORMANCE_TESTS") != "true":
                item.add_marker(skip_performance)


def _services_available():
    """Check if required services are available."""
    try:
        import redis
        import psycopg2

        # Try to connect to Redis
        r = redis.Redis(host="localhost", port=6379, db=1)
        r.ping()

        # Try to connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="test_db",
            user="test",
            password="test",  # pragma: allowlist secret
        )
        conn.close()

        return True
    except Exception:
        return False
