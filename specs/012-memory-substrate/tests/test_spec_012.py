"""
SPEC-012: Memory Substrate Tests

Tests for pluggable memory providers (native PostgreSQL and HTTP mem0).
"""

import os
import time
import pytest
from unittest.mock import AsyncMock, patch

# Set up test environment
os.environ["MEMORY_PROVIDER"] = "native"
os.environ["NINAIVALAIGAL_DATABASE_URL"] = "postgresql://nina:change_me_securely@localhost:5433/nina"

from server.memory import get_memory_provider, MemoryProvider, MemoryItem
from server.memory.factory import reset_memory_provider
from server.memory.providers.postgres import PostgresMemoryProvider
from server.memory.providers.mem0_http import Mem0HttpMemoryProvider

class TestMemoryProviderFactory:
    """Test memory provider factory"""
    
    def test_get_native_provider(self):
        """Test getting native PostgreSQL provider"""
        reset_memory_provider()
        provider = get_memory_provider("native")
        assert isinstance(provider, PostgresMemoryProvider)
    
    def test_get_http_provider(self):
        """Test getting HTTP mem0 provider"""
        reset_memory_provider()
        provider = get_memory_provider("http", base_url="http://localhost:7070")
        assert isinstance(provider, Mem0HttpMemoryProvider)
    
    def test_get_provider_from_env(self):
        """Test getting provider from environment variable"""
        reset_memory_provider()
        with patch.dict(os.environ, {"MEMORY_PROVIDER": "native"}):
            provider = get_memory_provider()
            assert isinstance(provider, PostgresMemoryProvider)
    
    def test_invalid_provider_type(self):
        """Test error handling for invalid provider type"""
        reset_memory_provider()
        with pytest.raises(ValueError, match="Unknown memory provider type"):
            get_memory_provider("invalid")

class TestPostgresMemoryProvider:
    """Test PostgreSQL memory provider"""
    
    @pytest.fixture
    def provider(self):
        """Create a PostgreSQL provider for testing"""
        database_url = os.environ.get("NINAIVALAIGAL_DATABASE_URL")
        if not database_url:
            pytest.skip("No database URL configured")
        return PostgresMemoryProvider(database_url)
    
    @pytest.mark.asyncio
    async def test_remember_and_recall(self, provider):
        """Test storing and retrieving memories"""
        # Store a memory
        memory = await provider.remember(
            text="Test memory for SPEC-012",
            meta={"test": True, "timestamp": time.time()},
            user_id=1,
            context_id="test-context"
        )
        
        assert memory["text"] == "Test memory for SPEC-012"
        assert memory["meta"]["test"] is True
        assert memory["user_id"] == 1
        assert memory["context_id"] == "test-context"
        assert "id" in memory
        
        # Recall the memory
        results = await provider.recall(
            query="SPEC-012",
            k=5,
            user_id=1,
            context_id="test-context"
        )
        
        assert len(results) > 0
        found = any(r["id"] == memory["id"] for r in results)
        assert found, "Stored memory should be found in recall results"
    
    @pytest.mark.asyncio
    async def test_list_memories(self, provider):
        """Test listing memories with pagination"""
        # Store a few memories
        for i in range(3):
            await provider.remember(
                text=f"List test memory {i}",
                meta={"index": i},
                user_id=2,
                context_id="list-test"
            )
        
        # List memories
        memories = await provider.list_memories(
            user_id=2,
            context_id="list-test",
            limit=10,
            offset=0
        )
        
        assert len(memories) >= 3
        # Should be ordered by created_at DESC
        assert all("List test memory" in m["text"] for m in memories[:3])
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, provider):
        """Test deleting a memory"""
        # Store a memory
        memory = await provider.remember(
            text="Memory to delete",
            user_id=3
        )
        
        # Delete it
        deleted = await provider.delete(id=memory["id"], user_id=3)
        assert deleted is True
        
        # Try to delete again (should return False)
        deleted_again = await provider.delete(id=memory["id"], user_id=3)
        assert deleted_again is False
    
    @pytest.mark.asyncio
    async def test_health_check(self, provider):
        """Test provider health check"""
        healthy = await provider.health_check()
        assert healthy is True

class TestMem0HttpMemoryProvider:
    """Test HTTP mem0 memory provider"""
    
    @pytest.fixture
    def provider(self):
        """Create an HTTP provider for testing"""
        return Mem0HttpMemoryProvider(
            base_url="http://localhost:7070",
            auth_secret="test-secret"
        )
    
    @pytest.mark.asyncio
    async def test_remember_mock(self, provider):
        """Test storing memory with mocked HTTP response"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": "test-123", "status": "success"}
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(provider.client, 'post', return_value=mock_response):
            memory = await provider.remember(
                text="Test HTTP memory",
                meta={"source": "http"},
                user_id=1
            )
            
            assert memory["text"] == "Test HTTP memory"
            assert memory["meta"]["source"] == "http"
            assert memory["user_id"] == 1
    
    @pytest.mark.asyncio
    async def test_recall_mock(self, provider):
        """Test recalling memories with mocked HTTP response"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "mem-1",
                    "text": "Found memory 1",
                    "metadata": {"score": 0.9}
                },
                {
                    "id": "mem-2", 
                    "text": "Found memory 2",
                    "metadata": {"score": 0.8}
                }
            ]
        }
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(provider.client, 'post', return_value=mock_response):
            results = await provider.recall(query="test", k=5, user_id=1)
            
            assert len(results) == 2
            assert results[0]["text"] == "Found memory 1"
            assert results[1]["text"] == "Found memory 2"
    
    @pytest.mark.asyncio
    async def test_health_check_mock(self, provider):
        """Test health check with mocked response"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch.object(provider.client, 'get', return_value=mock_response):
            healthy = await provider.health_check()
            assert healthy is True

class TestMemoryProviderIntegration:
    """Integration tests for memory providers"""
    
    @pytest.mark.asyncio
    async def test_provider_switching(self):
        """Test switching between providers"""
        reset_memory_provider()
        
        # Test native provider
        native_provider = get_memory_provider("native")
        assert isinstance(native_provider, PostgresMemoryProvider)
        
        # Test HTTP provider  
        http_provider = get_memory_provider("http")
        assert isinstance(http_provider, Mem0HttpMemoryProvider)
        
        # Both should implement the same interface
        assert hasattr(native_provider, 'remember')
        assert hasattr(native_provider, 'recall')
        assert hasattr(native_provider, 'delete')
        assert hasattr(native_provider, 'health_check')
        
        assert hasattr(http_provider, 'remember')
        assert hasattr(http_provider, 'recall')
        assert hasattr(http_provider, 'delete')
        assert hasattr(http_provider, 'health_check')
