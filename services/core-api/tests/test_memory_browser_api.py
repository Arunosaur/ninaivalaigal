#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Unit tests for Memory Browser API CRUD endpoints
Tests the implementation of US#13 - Implement CRUD endpoints
"""

import json
import os
import sys
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_service import get_current_user
from database import DatabaseManager, get_db
from database.models import Memory, User

# Create test app
from fastapi import FastAPI
from routers.memory_browser_api import (
    MemoryCreate,
    MemoryUpdate,
    _serialize_memory,
    router,
)

app = FastAPI()
app.include_router(router, prefix="/api/v1/memory")


# Mock dependencies for testing
@pytest.fixture
def mock_db():
    """Mock database manager"""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def mock_session():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    return user


@pytest.fixture
def mock_memory():
    """Mock memory record"""
    memory = Mock(spec=Memory)
    memory.id = uuid.uuid4()
    memory.user_id = uuid.uuid4()
    memory.context = "test"
    memory.type = "user_created"
    memory.source = "web_ui"
    memory.data = json.dumps(
        {
            "content": "Test memory content",
            "tags": ["test", "unit"],
            "pinned": False,
            "archived": False,
            "relevance_score": 1.0,
        }
    )
    memory.created_at = datetime.utcnow()
    memory.updated_at = datetime.utcnow()
    return memory


@pytest.fixture
def client(mock_db, mock_session, mock_user):
    """Test client with mocked dependencies"""

    def override_get_db():
        return mock_db

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    mock_db.get_session.return_value = mock_session

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


class TestMemorySerialization:
    """Test memory serialization function"""

    def test_serialize_memory_with_dict_data(self, mock_memory):
        """Test serialization with dict data"""
        mock_memory.data = {"content": "Test content", "tags": ["test"], "pinned": True}

        result = _serialize_memory(mock_memory)

        assert result["id"] == str(mock_memory.id)
        assert result["content"] == "Test content"
        assert result["context"] == mock_memory.context
        assert result["tags"] == ["test"]
        assert result["pinned"] is True
        assert "created_at" in result
        assert "updated_at" in result

    def test_serialize_memory_with_string_data(self, mock_memory):
        """Test serialization with string data (from VIEW)"""
        mock_memory.data = json.dumps({"content": "Test content", "tags": ["test"], "pinned": True})

        result = _serialize_memory(mock_memory)

        assert result["id"] == str(mock_memory.id)
        assert result["content"] == "Test content"
        assert result["tags"] == ["test"]
        assert result["pinned"] is True

    def test_serialize_memory_with_invalid_json(self, mock_memory):
        """Test serialization with invalid JSON string"""
        mock_memory.data = "invalid json string"

        result = _serialize_memory(mock_memory)

        assert result["content"] == "invalid json string"
        assert result["tags"] == []

    def test_serialize_memory_fallback_content(self, mock_memory):
        """Test content fallback to other fields"""
        mock_memory.data = {"text": "Fallback content"}

        result = _serialize_memory(mock_memory)

        assert result["content"] == "Fallback content"


class TestCreateMemory:
    """Test memory creation endpoint"""

    def test_create_memory_success(self, client, mock_session, mock_user):
        """Test successful memory creation"""
        memory_data = {"content": "New test memory", "context": "test", "tags": ["test", "new"], "pinned": True}

        # Mock the database operations
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        response = client.post("/api/v1/memory/memories", json=memory_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "memory" in data
        assert data["memory"]["content"] == "New test memory"
        assert data["memory"]["context"] == "test"
        assert data["memory"]["tags"] == ["test", "new"]
        assert data["memory"]["pinned"] is True

        # Verify database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_memory_minimal_data(self, client, mock_session, mock_user):
        """Test memory creation with minimal data"""
        memory_data = {"content": "Minimal memory"}

        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        response = client.post("/api/v1/memory/memories", json=memory_data)

        assert response.status_code == 201
        data = response.json()
        assert data["memory"]["content"] == "Minimal memory"
        assert data["memory"]["context"] == "general"  # default
        assert data["memory"]["tags"] == []  # default
        assert data["memory"]["pinned"] is False  # default


class TestListMemories:
    """Test memory listing endpoint"""

    def test_list_memories_success(self, client, mock_session, mock_user, mock_memory):
        """Test successful memory listing"""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_memory]

        mock_session.query.return_value = mock_query
        mock_session.query.return_value.count.return_value = 1

        response = client.get("/api/v1/memory/memories")

        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert "count" in data
        assert data["count"] == 1
        assert len(data["memories"]) == 1
        assert data["memories"][0]["content"] == "Test memory content"

    def test_list_memories_with_pagination(self, client, mock_session, mock_user):
        """Test memory listing with pagination parameters"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.count.return_value = 0

        response = client.get("/api/v1/memory/memories?limit=50&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 10


class TestGetMemory:
    """Test individual memory retrieval endpoint"""

    def test_get_memory_success(self, client, mock_session, mock_user, mock_memory):
        """Test successful memory retrieval"""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_memory
        mock_session.query.return_value = mock_query

        memory_id = str(mock_memory.id)
        response = client.get(f"/api/v1/memory/memories/{memory_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory" in data
        assert data["memory"]["id"] == memory_id
        assert data["memory"]["content"] == "Test memory content"

    def test_get_memory_not_found(self, client, mock_session, mock_user):
        """Test memory retrieval when memory doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query

        memory_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/memory/memories/{memory_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Memory not found" in data["detail"]

    def test_get_memory_invalid_uuid(self, client, mock_user):
        """Test memory retrieval with invalid UUID"""
        response = client.get("/api/v1/memory/memories/invalid-uuid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid memory ID format" in data["detail"]


class TestUpdateMemory:
    """Test memory update endpoint"""

    def test_update_memory_success(self, client, mock_session, mock_user, mock_memory):
        """Test successful memory update"""
        # Mock query to get memory
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_memory
        mock_session.query.return_value = mock_query

        update_data = {"content": "Updated content", "tags": ["updated"], "pinned": True}

        memory_id = str(mock_memory.id)
        response = client.put(f"/api/v1/memory/memories/{memory_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory" in data
        assert data["memory"]["content"] == "Updated content"
        assert data["memory"]["tags"] == ["updated"]
        assert data["memory"]["pinned"] is True

        # Verify database operations
        mock_session.commit.assert_called()
        mock_session.refresh.assert_called()

    def test_update_memory_partial(self, client, mock_session, mock_user, mock_memory):
        """Test partial memory update"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_memory
        mock_session.query.return_value = mock_query

        update_data = {"pinned": True}

        memory_id = str(mock_memory.id)
        response = client.put(f"/api/v1/memory/memories/{memory_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Only pinned should be updated, other fields preserved
        assert data["memory"]["pinned"] is True

    def test_update_memory_not_found(self, client, mock_session, mock_user):
        """Test memory update when memory doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query

        update_data = {"content": "Updated"}
        memory_id = str(uuid.uuid4())

        response = client.put(f"/api/v1/memory/memories/{memory_id}", json=update_data)

        assert response.status_code == 404
        data = response.json()
        assert "Memory not found" in data["detail"]


class TestDeleteMemory:
    """Test memory deletion endpoint"""

    def test_delete_memory_success(self, client, mock_session, mock_user, mock_memory):
        """Test successful memory deletion"""
        # Mock query to get memory
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_memory
        mock_session.query.return_value = mock_query

        memory_id = str(mock_memory.id)
        response = client.delete(f"/api/v1/memory/memories/{memory_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Memory deleted successfully" in data["message"]

        # Verify database operations
        mock_session.delete.assert_called_once_with(mock_memory)
        mock_session.commit.assert_called_once()

    def test_delete_memory_not_found(self, client, mock_session, mock_user):
        """Test memory deletion when memory doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query

        memory_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/memory/memories/{memory_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Memory not found" in data["detail"]

    def test_delete_memory_invalid_uuid(self, client, mock_user):
        """Test memory deletion with invalid UUID"""
        response = client.delete("/api/v1/memory/memories/invalid-uuid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid memory ID format" in data["detail"]


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_database_error_handling(self, client, mock_session, mock_user):
        """Test proper handling of database errors"""
        mock_session.query.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/memory/memories")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to load memories" in data["detail"]

    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        # Create client without auth override
        test_client = TestClient(app)

        response = test_client.get("/api/v1/memory/memories")
        assert response.status_code == 401

        response = test_client.post("/api/v1/memory/memories", json={"content": "test"})
        assert response.status_code == 401

        memory_id = str(uuid.uuid4())
        response = test_client.get(f"/api/v1/memory/memories/{memory_id}")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
