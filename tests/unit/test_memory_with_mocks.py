# SPEC-056: Example of improved testing with mocks and fixtures
# This demonstrates the new testing approach with comprehensive mocking

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from tests.fixtures import MockContext, assert_memory_valid, assert_user_valid


class TestMemoryWithMocks:
    """Test memory operations using comprehensive mocks"""
    
    @pytest_asyncio.fixture
    async def setup_test_data(self, mock_context):
        """Setup test data using mock context"""
        with mock_context:
            # Create test user
            user = await mock_context.mock_db.create_user(
                email="test@example.com",
                username="testuser"
            )
            
            # Create test memories
            memory1 = await mock_context.mock_db.create_memory(
                user_id=user["id"],
                content="First test memory",
                context="work"
            )
            
            memory2 = await mock_context.mock_db.create_memory(
                user_id=user["id"],
                content="Second test memory",
                context="personal"
            )
            
            yield {
                "user": user,
                "memories": [memory1, memory2],
                "mock_context": mock_context
            }
    
    @pytest.mark.asyncio
    async def test_create_memory_with_mocks(self, setup_test_data):
        """Test memory creation using mocks"""
        data = await setup_test_data
        user = data["user"]
        mock_context = data["mock_context"]
        
        with mock_context:
            # Test memory creation
            new_memory = await mock_context.mock_db.create_memory(
                user_id=user["id"],
                content="New memory content",
                context="test"
            )
            
            # Validate memory structure
            assert_memory_valid(new_memory)
            assert new_memory["content"] == "New memory content"
            assert new_memory["context"] == "test"
            assert new_memory["user_id"] == user["id"]
    
    @pytest.mark.asyncio
    async def test_retrieve_user_memories_with_mocks(self, setup_test_data):
        """Test memory retrieval using mocks"""
        data = await setup_test_data
        user = data["user"]
        mock_context = data["mock_context"]
        
        with mock_context:
            # Retrieve user memories
            memories = await mock_context.mock_db.get_user_memories(user["id"])
            
            # Validate results
            assert len(memories) == 2
            for memory in memories:
                assert_memory_valid(memory)
                assert memory["user_id"] == user["id"]
    
    @pytest.mark.asyncio
    async def test_redis_caching_with_mocks(self, mock_redis):
        """Test Redis caching using mocks"""
        # Test Redis operations
        await mock_redis.set("test_key", "test_value", ex=300)
        
        # Verify value was stored
        value = await mock_redis.get("test_key")
        assert value == "test_value"
        
        # Test key existence
        exists = await mock_redis.exists("test_key")
        assert exists == 1
        
        # Test deletion
        deleted = await mock_redis.delete("test_key")
        assert deleted == 1
        
        # Verify key is gone
        value = await mock_redis.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_http_client_mocking(self, mock_http_client):
        """Test HTTP client mocking"""
        # Setup mock response
        mock_http_client.set_response(
            "https://api.example.com/data",
            {"status_code": 200, "data": {"result": "success"}}
        )
        
        # Make request
        response = await mock_http_client.get("https://api.example.com/data")
        
        # Verify response
        assert response["status_code"] == 200
        assert response["data"]["result"] == "success"
        
        # Verify call was recorded
        assert len(mock_http_client.call_history) == 1
        assert mock_http_client.call_history[0][0] == "GET"
        assert mock_http_client.call_history[0][1] == "https://api.example.com/data"
    
    def test_user_validation_with_factory(self, test_data_factory):
        """Test user validation using data factory"""
        # Create test user using factory
        user = test_data_factory.create_user(
            email="factory@example.com",
            username="factoryuser"
        )
        
        # Validate user structure
        assert_user_valid(user)
        assert user["email"] == "factory@example.com"
        assert user["username"] == "factoryuser"
        assert user["is_active"] is True
    
    def test_memory_validation_with_factory(self, test_data_factory):
        """Test memory validation using data factory"""
        # Create test memory using factory
        memory = test_data_factory.create_memory(
            content="Factory memory content",
            context="factory_test"
        )
        
        # Validate memory structure
        assert_memory_valid(memory)
        assert memory["content"] == "Factory memory content"
        assert memory["context"] == "factory_test"
    
    @pytest.mark.asyncio
    async def test_comprehensive_mocking_scenario(self, mock_context):
        """Test comprehensive scenario with all mocks"""
        with mock_context:
            # Create user
            user = await mock_context.mock_db.create_user(
                email="comprehensive@example.com",
                username="compuser"
            )
            
            # Create memory
            memory = await mock_context.mock_db.create_memory(
                user_id=user["id"],
                content="Comprehensive test memory"
            )
            
            # Cache memory in Redis
            cache_key = f"memory:{memory['id']}"
            await mock_context.mock_redis.set(
                cache_key, 
                f"cached_content_{memory['id']}", 
                ex=3600
            )
            
            # Setup HTTP mock for external API
            mock_context.mock_http.set_response(
                "https://api.memory.com/analyze",
                {"status_code": 200, "analysis": "positive"}
            )
            
            # Simulate external API call
            response = await mock_context.mock_http.post(
                "https://api.memory.com/analyze",
                json={"content": memory["content"]}
            )
            
            # Verify all operations
            assert_user_valid(user)
            assert_memory_valid(memory)
            
            cached_value = await mock_context.mock_redis.get(cache_key)
            assert cached_value == f"cached_content_{memory['id']}"
            
            assert response["status_code"] == 200
            assert response["analysis"] == "positive"


class TestPerformanceWithMocks:
    """Test performance scenarios using mocks"""
    
    @pytest.mark.asyncio
    async def test_bulk_memory_operations(self, mock_context, benchmark_config):
        """Test bulk operations performance"""
        with mock_context:
            # Create user
            user = await mock_context.mock_db.create_user(
                email="bulk@example.com",
                username="bulkuser"
            )
            
            # Create multiple memories
            memories = []
            for i in range(100):
                memory = await mock_context.mock_db.create_memory(
                    user_id=user["id"],
                    content=f"Bulk memory {i}",
                    context=f"bulk_context_{i % 10}"
                )
                memories.append(memory)
            
            # Verify all memories were created
            user_memories = await mock_context.mock_db.get_user_memories(user["id"])
            assert len(user_memories) == 100
            
            # Verify memory structure
            for memory in user_memories:
                assert_memory_valid(memory)
    
    @pytest.mark.asyncio
    async def test_redis_performance_simulation(self, mock_redis):
        """Test Redis performance using mocks"""
        # Simulate high-frequency operations
        for i in range(1000):
            await mock_redis.set(f"key_{i}", f"value_{i}", ex=300)
        
        # Verify all keys exist
        for i in range(1000):
            value = await mock_redis.get(f"key_{i}")
            assert value == f"value_{i}"
        
        # Cleanup
        for i in range(1000):
            deleted = await mock_redis.delete(f"key_{i}")
            assert deleted == 1
