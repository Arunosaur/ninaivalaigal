#!/usr/bin/env python3
"""
Comprehensive test coverage for server/memory_api.py
Target: Increase from 0% to 80% coverage
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Set test environment
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("NINAIVALAIGAL_ENV", "test")

# Import after setting environment
from server.memory_api import (
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    list_memories,
    search_memories,
    get_memory_context,
    add_memory_tag,
    remove_memory_tag,
    get_memory_attachments
)


class TestMemoryCreation:
    """Test memory creation functionality."""
    
    @patch('server.memory_api.database.execute_query')
    @patch('server.memory_api.redis_client.set')
    def test_create_memory_with_valid_data(self, mock_redis, mock_db):
        """Test creating memory with valid data."""
        mock_db.return_value = [{"id": "mem_123", "content": "Test memory"}]
        
        memory_data = {
            "content": "Test memory content",
            "title": "Test Memory",
            "tags": ["test", "memory"],
            "user_id": "user_123"
        }
        
        result = create_memory(memory_data)
        
        assert result is not None
        assert result["id"] == "mem_123"
        assert result["content"] == "Test memory"
        mock_db.assert_called_once()
        mock_redis.assert_called()
    
    @patch('server.memory_api.database.execute_query')
    def test_create_memory_with_missing_content(self, mock_db):
        """Test creating memory with missing required content."""
        memory_data = {
            "title": "Test Memory",
            "user_id": "user_123"
            # Missing content
        }
        
        with pytest.raises(HTTPException) as exc_info:
            create_memory(memory_data)
        
        assert exc_info.value.status_code == 400
        assert "Content is required" in str(exc_info.value.detail)
    
    @patch('server.memory_api.database.execute_query')
    def test_create_memory_with_invalid_user(self, mock_db):
        """Test creating memory with invalid user ID."""
        from psycopg2 import IntegrityError
        mock_db.side_effect = IntegrityError("Invalid user")
        
        memory_data = {
            "content": "Test memory content",
            "title": "Test Memory",
            "user_id": "invalid_user"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            create_memory(memory_data)
        
        assert exc_info.value.status_code == 400
        assert "Invalid user" in str(exc_info.value.detail)


class TestMemoryRetrieval:
    """Test memory retrieval functionality."""
    
    @patch('server.memory_api.redis_client.get')
    @patch('server.memory_api.database.execute_query')
    def test_get_memory_from_cache(self, mock_db, mock_redis):
        """Test retrieving memory from Redis cache."""
        import json
        
        cached_memory = {
            "id": "mem_123",
            "content": "Cached memory content",
            "title": "Cached Memory"
        }
        mock_redis.return_value = json.dumps(cached_memory)
        
        result = get_memory("mem_123", "user_123")
        
        assert result is not None
        assert result["id"] == "mem_123"
        assert result["content"] == "Cached memory content"
        mock_redis.assert_called_once()
        mock_db.assert_not_called()  # Should not hit database
    
    @patch('server.memory_api.redis_client.get')
    @patch('server.memory_api.redis_client.set')
    @patch('server.memory_api.database.execute_query')
    def test_get_memory_from_database(self, mock_db, mock_redis_set, mock_redis_get):
        """Test retrieving memory from database when not in cache."""
        mock_redis_get.return_value = None  # Not in cache
        
        db_memory = {
            "id": "mem_123",
            "content": "Database memory content",
            "title": "Database Memory",
            "user_id": "user_123"
        }
        mock_db.return_value = [db_memory]
        
        result = get_memory("mem_123", "user_123")
        
        assert result is not None
        assert result["id"] == "mem_123"
        assert result["content"] == "Database memory content"
        mock_db.assert_called_once()
        mock_redis_set.assert_called_once()  # Should cache the result
    
    @patch('server.memory_api.redis_client.get')
    @patch('server.memory_api.database.execute_query')
    def test_get_nonexistent_memory(self, mock_db, mock_redis):
        """Test retrieving nonexistent memory."""
        mock_redis.return_value = None
        mock_db.return_value = []
        
        with pytest.raises(HTTPException) as exc_info:
            get_memory("nonexistent_id", "user_123")
        
        assert exc_info.value.status_code == 404
        assert "Memory not found" in str(exc_info.value.detail)
    
    @patch('server.memory_api.redis_client.get')
    @patch('server.memory_api.database.execute_query')
    def test_get_memory_unauthorized_user(self, mock_db, mock_redis):
        """Test retrieving memory with unauthorized user."""
        mock_redis.return_value = None
        
        db_memory = {
            "id": "mem_123",
            "content": "Private memory content",
            "title": "Private Memory",
            "user_id": "other_user"  # Different user
        }
        mock_db.return_value = [db_memory]
        
        with pytest.raises(HTTPException) as exc_info:
            get_memory("mem_123", "user_123")
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)


class TestMemoryUpdate:
    """Test memory update functionality."""
    
    @patch('server.memory_api.get_memory')
    @patch('server.memory_api.database.execute_query')
    @patch('server.memory_api.redis_client.delete')
    def test_update_memory_with_valid_data(self, mock_redis_del, mock_db, mock_get):
        """Test updating memory with valid data."""
        # Mock existing memory
        existing_memory = {
            "id": "mem_123",
            "content": "Original content",
            "title": "Original Title",
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        
        # Mock update result
        updated_memory = {
            "id": "mem_123",
            "content": "Updated content",
            "title": "Updated Title",
            "user_id": "user_123"
        }
        mock_db.return_value = [updated_memory]
        
        update_data = {
            "content": "Updated content",
            "title": "Updated Title"
        }
        
        result = update_memory("mem_123", update_data, "user_123")
        
        assert result is not None
        assert result["content"] == "Updated content"
        assert result["title"] == "Updated Title"
        mock_db.assert_called_once()
        mock_redis_del.assert_called_once()  # Should invalidate cache
    
    @patch('server.memory_api.get_memory')
    def test_update_nonexistent_memory(self, mock_get):
        """Test updating nonexistent memory."""
        mock_get.side_effect = HTTPException(status_code=404, detail="Memory not found")
        
        update_data = {"content": "Updated content"}
        
        with pytest.raises(HTTPException) as exc_info:
            update_memory("nonexistent_id", update_data, "user_123")
        
        assert exc_info.value.status_code == 404
    
    @patch('server.memory_api.get_memory')
    def test_update_memory_unauthorized(self, mock_get):
        """Test updating memory with unauthorized user."""
        mock_get.side_effect = HTTPException(status_code=403, detail="Access denied")
        
        update_data = {"content": "Updated content"}
        
        with pytest.raises(HTTPException) as exc_info:
            update_memory("mem_123", update_data, "user_123")
        
        assert exc_info.value.status_code == 403


class TestMemoryDeletion:
    """Test memory deletion functionality."""
    
    @patch('server.memory_api.get_memory')
    @patch('server.memory_api.database.execute_query')
    @patch('server.memory_api.redis_client.delete')
    def test_delete_memory_success(self, mock_redis_del, mock_db, mock_get):
        """Test successful memory deletion."""
        # Mock existing memory
        existing_memory = {
            "id": "mem_123",
            "content": "Memory to delete",
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        mock_db.return_value = []  # Successful deletion
        
        result = delete_memory("mem_123", "user_123")
        
        assert result is True
        mock_db.assert_called_once()
        mock_redis_del.assert_called_once()
    
    @patch('server.memory_api.get_memory')
    def test_delete_nonexistent_memory(self, mock_get):
        """Test deleting nonexistent memory."""
        mock_get.side_effect = HTTPException(status_code=404, detail="Memory not found")
        
        with pytest.raises(HTTPException) as exc_info:
            delete_memory("nonexistent_id", "user_123")
        
        assert exc_info.value.status_code == 404


class TestMemoryListing:
    """Test memory listing functionality."""
    
    @patch('server.memory_api.database.execute_query')
    def test_list_memories_with_pagination(self, mock_db):
        """Test listing memories with pagination."""
        mock_memories = [
            {"id": "mem_1", "title": "Memory 1", "user_id": "user_123"},
            {"id": "mem_2", "title": "Memory 2", "user_id": "user_123"},
            {"id": "mem_3", "title": "Memory 3", "user_id": "user_123"}
        ]
        mock_db.return_value = mock_memories
        
        result = list_memories("user_123", limit=10, offset=0)
        
        assert result is not None
        assert len(result) == 3
        assert result[0]["id"] == "mem_1"
        mock_db.assert_called_once()
    
    @patch('server.memory_api.database.execute_query')
    def test_list_memories_empty_result(self, mock_db):
        """Test listing memories with no results."""
        mock_db.return_value = []
        
        result = list_memories("user_123", limit=10, offset=0)
        
        assert result == []
        mock_db.assert_called_once()
    
    @patch('server.memory_api.database.execute_query')
    def test_list_memories_with_filters(self, mock_db):
        """Test listing memories with tag filters."""
        mock_memories = [
            {"id": "mem_1", "title": "Tagged Memory", "tags": ["work"], "user_id": "user_123"}
        ]
        mock_db.return_value = mock_memories
        
        result = list_memories("user_123", tags=["work"], limit=10, offset=0)
        
        assert result is not None
        assert len(result) == 1
        assert "work" in result[0]["tags"]


class TestMemorySearch:
    """Test memory search functionality."""
    
    @patch('server.memory_api.database.execute_query')
    def test_search_memories_by_content(self, mock_db):
        """Test searching memories by content."""
        mock_results = [
            {"id": "mem_1", "content": "Python programming tips", "user_id": "user_123"},
            {"id": "mem_2", "content": "Advanced Python concepts", "user_id": "user_123"}
        ]
        mock_db.return_value = mock_results
        
        result = search_memories("user_123", query="Python", limit=10, offset=0)
        
        assert result is not None
        assert len(result) == 2
        assert "Python" in result[0]["content"]
        mock_db.assert_called_once()
    
    @patch('server.memory_api.database.execute_query')
    def test_search_memories_no_results(self, mock_db):
        """Test searching memories with no results."""
        mock_db.return_value = []
        
        result = search_memories("user_123", query="nonexistent", limit=10, offset=0)
        
        assert result == []
    
    @patch('server.memory_api.database.execute_query')
    def test_search_memories_with_empty_query(self, mock_db):
        """Test searching memories with empty query."""
        with pytest.raises(HTTPException) as exc_info:
            search_memories("user_123", query="", limit=10, offset=0)
        
        assert exc_info.value.status_code == 400
        assert "Query cannot be empty" in str(exc_info.value.detail)


class TestMemoryTags:
    """Test memory tagging functionality."""
    
    @patch('server.memory_api.get_memory')
    @patch('server.memory_api.database.execute_query')
    @patch('server.memory_api.redis_client.delete')
    def test_add_memory_tag_success(self, mock_redis_del, mock_db, mock_get):
        """Test successfully adding tag to memory."""
        existing_memory = {
            "id": "mem_123",
            "tags": ["existing_tag"],
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        mock_db.return_value = []  # Successful update
        
        result = add_memory_tag("mem_123", "new_tag", "user_123")
        
        assert result is True
        mock_db.assert_called_once()
        mock_redis_del.assert_called_once()
    
    @patch('server.memory_api.get_memory')
    def test_add_duplicate_tag(self, mock_get):
        """Test adding duplicate tag to memory."""
        existing_memory = {
            "id": "mem_123",
            "tags": ["existing_tag"],
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        
        with pytest.raises(HTTPException) as exc_info:
            add_memory_tag("mem_123", "existing_tag", "user_123")
        
        assert exc_info.value.status_code == 400
        assert "Tag already exists" in str(exc_info.value.detail)
    
    @patch('server.memory_api.get_memory')
    @patch('server.memory_api.database.execute_query')
    @patch('server.memory_api.redis_client.delete')
    def test_remove_memory_tag_success(self, mock_redis_del, mock_db, mock_get):
        """Test successfully removing tag from memory."""
        existing_memory = {
            "id": "mem_123",
            "tags": ["tag_to_remove", "keep_tag"],
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        mock_db.return_value = []  # Successful update
        
        result = remove_memory_tag("mem_123", "tag_to_remove", "user_123")
        
        assert result is True
        mock_db.assert_called_once()
        mock_redis_del.assert_called_once()
    
    @patch('server.memory_api.get_memory')
    def test_remove_nonexistent_tag(self, mock_get):
        """Test removing nonexistent tag from memory."""
        existing_memory = {
            "id": "mem_123",
            "tags": ["existing_tag"],
            "user_id": "user_123"
        }
        mock_get.return_value = existing_memory
        
        with pytest.raises(HTTPException) as exc_info:
            remove_memory_tag("mem_123", "nonexistent_tag", "user_123")
        
        assert exc_info.value.status_code == 400
        assert "Tag not found" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
