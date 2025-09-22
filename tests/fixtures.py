# SPEC-056: Dependency & Testing Improvements
# Comprehensive test fixtures and mocks for ninaivalaigal

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Dict, Any, Optional
import tempfile
import os
from datetime import datetime, timedelta

# Test data factories
class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_user(
        id: int = 1,
        email: str = "test@example.com",
        username: str = "testuser",
        is_active: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test user object"""
        return {
            "id": id,
            "email": email,
            "username": username,
            "is_active": is_active,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **kwargs
        }
    
    @staticmethod
    def create_memory(
        id: int = 1,
        user_id: int = 1,
        content: str = "Test memory content",
        context: str = "test_context",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test memory object"""
        return {
            "id": id,
            "user_id": user_id,
            "content": content,
            "context": context,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {},
            **kwargs
        }
    
    @staticmethod
    def create_team(
        id: int = 1,
        name: str = "Test Team",
        organization_id: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test team object"""
        return {
            "id": id,
            "name": name,
            "organization_id": organization_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **kwargs
        }

# Database mocks
class MockDatabaseManager:
    """Mock database manager for testing"""
    
    def __init__(self):
        self.users = {}
        self.memories = {}
        self.teams = {}
        self.sessions = {}
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get next available ID"""
        current_id = self._next_id
        self._next_id += 1
        return current_id
    
    async def create_user(self, email: str, username: str, **kwargs) -> Dict[str, Any]:
        """Mock user creation"""
        user_id = self._get_next_id()
        user = TestDataFactory.create_user(
            id=user_id, email=email, username=username, **kwargs
        )
        self.users[user_id] = user
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Mock user lookup by email"""
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None
    
    async def create_memory(self, user_id: int, content: str, **kwargs) -> Dict[str, Any]:
        """Mock memory creation"""
        memory_id = self._get_next_id()
        memory = TestDataFactory.create_memory(
            id=memory_id, user_id=user_id, content=content, **kwargs
        )
        self.memories[memory_id] = memory
        return memory
    
    async def get_user_memories(self, user_id: int) -> list[Dict[str, Any]]:
        """Mock memory retrieval for user"""
        return [m for m in self.memories.values() if m["user_id"] == user_id]

# Redis mocks
class MockRedisClient:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {}
        self.expirations = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Mock Redis GET"""
        if key in self.expirations:
            if datetime.utcnow() > self.expirations[key]:
                del self.data[key]
                del self.expirations[key]
                return None
        return self.data.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Mock Redis SET"""
        self.data[key] = value
        if ex:
            self.expirations[key] = datetime.utcnow() + timedelta(seconds=ex)
        return True
    
    async def delete(self, key: str) -> int:
        """Mock Redis DELETE"""
        if key in self.data:
            del self.data[key]
            if key in self.expirations:
                del self.expirations[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        """Mock Redis EXISTS"""
        return 1 if key in self.data else 0

# HTTP client mocks
class MockHttpClient:
    """Mock HTTP client for testing external API calls"""
    
    def __init__(self):
        self.responses = {}
        self.call_history = []
    
    def set_response(self, url: str, response: Dict[str, Any]):
        """Set mock response for URL"""
        self.responses[url] = response
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock HTTP GET"""
        self.call_history.append(("GET", url, kwargs))
        return self.responses.get(url, {"status_code": 404})
    
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock HTTP POST"""
        self.call_history.append(("POST", url, kwargs))
        return self.responses.get(url, {"status_code": 404})

# Pytest fixtures
@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory()

@pytest.fixture
def mock_db():
    """Provide mock database manager"""
    return MockDatabaseManager()

@pytest.fixture
def mock_redis():
    """Provide mock Redis client"""
    return MockRedisClient()

@pytest.fixture
def mock_http_client():
    """Provide mock HTTP client"""
    return MockHttpClient()

@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def test_env_vars():
    """Provide test environment variables"""
    test_vars = {
        "NINAIVALAIGAL_JWT_SECRET": "test-secret-key",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "TESTING": "true"
    }
    
    # Set test environment variables
    original_vars = {}
    for key, value in test_vars.items():
        original_vars[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original environment variables
    for key, original_value in original_vars.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest_asyncio.fixture
async def mock_database_session():
    """Provide mock database session"""
    with patch('server.database.DatabaseManager') as mock_db_class:
        mock_db = MockDatabaseManager()
        mock_db_class.return_value = mock_db
        yield mock_db

@pytest_asyncio.fixture
async def mock_redis_session():
    """Provide mock Redis session"""
    with patch('server.redis_client.redis_client') as mock_redis:
        mock_redis_instance = MockRedisClient()
        mock_redis.return_value = mock_redis_instance
        yield mock_redis_instance

# Context managers for mocking
class MockContext:
    """Context manager for comprehensive mocking"""
    
    def __init__(self):
        self.patches = []
        self.mock_db = MockDatabaseManager()
        self.mock_redis = MockRedisClient()
        self.mock_http = MockHttpClient()
    
    def __enter__(self):
        # Mock database
        db_patch = patch('server.database.DatabaseManager')
        mock_db_class = db_patch.start()
        mock_db_class.return_value = self.mock_db
        self.patches.append(db_patch)
        
        # Mock Redis
        redis_patch = patch('server.redis_client.redis_client')
        mock_redis_client = redis_patch.start()
        mock_redis_client.return_value = self.mock_redis
        self.patches.append(redis_patch)
        
        # Mock HTTP client
        http_patch = patch('httpx.AsyncClient')
        mock_http_client = http_patch.start()
        mock_http_client.return_value = self.mock_http
        self.patches.append(http_patch)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in reversed(self.patches):
            patch_obj.stop()

@pytest.fixture
def mock_context():
    """Provide comprehensive mock context"""
    return MockContext()

# Performance testing utilities
@pytest.fixture
def benchmark_config():
    """Configure pytest-benchmark for performance tests"""
    return {
        "min_rounds": 5,
        "max_time": 1.0,
        "warmup": True,
        "warmup_iterations": 2
    }

# Async test utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Test markers
pytest_plugins = ["pytest_asyncio"]

# Custom assertions
def assert_memory_valid(memory: Dict[str, Any]):
    """Assert that a memory object is valid"""
    required_fields = ["id", "user_id", "content", "created_at"]
    for field in required_fields:
        assert field in memory, f"Memory missing required field: {field}"
    
    assert isinstance(memory["id"], int), "Memory ID must be integer"
    assert isinstance(memory["user_id"], int), "User ID must be integer"
    assert isinstance(memory["content"], str), "Content must be string"
    assert len(memory["content"]) > 0, "Content must not be empty"

def assert_user_valid(user: Dict[str, Any]):
    """Assert that a user object is valid"""
    required_fields = ["id", "email", "username", "is_active"]
    for field in required_fields:
        assert field in user, f"User missing required field: {field}"
    
    assert isinstance(user["id"], int), "User ID must be integer"
    assert "@" in user["email"], "Email must be valid format"
    assert isinstance(user["is_active"], bool), "is_active must be boolean"
