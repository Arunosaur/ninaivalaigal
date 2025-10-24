# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for memory contracts."""

import pytest
from ninaivalaigal_contracts.memory.v1 import (
    CreateMemoryRequest,
    ListMemoriesRequest,
    Memory,
    MemoryList,
    UpdateMemoryRequest,
)
from pydantic import ValidationError


class TestCreateMemoryRequest:
    """Test CreateMemoryRequest contract."""

    def test_valid_create_request(self):
        """Test valid memory creation request."""
        request = CreateMemoryRequest(
            user_id="user123", content="This is a memory", metadata={"key": "value"}, tags=["important", "work"]
        )
        assert request.user_id == "user123"
        assert request.content == "This is a memory"
        assert len(request.tags) == 2

    def test_empty_content_rejected(self):
        """Test empty content is rejected."""
        with pytest.raises(ValidationError):
            CreateMemoryRequest(user_id="user123", content="")

    def test_optional_fields(self):
        """Test optional metadata and tags."""
        request = CreateMemoryRequest(user_id="user123", content="Simple memory")
        assert request.metadata is None
        assert request.tags == []


class TestListMemoriesRequest:
    """Test ListMemoriesRequest contract."""

    def test_valid_list_request(self):
        """Test valid list request with pagination."""
        request = ListMemoriesRequest(user_id="user123", page=2, page_size=50)
        assert request.page == 2
        assert request.page_size == 50

    def test_default_pagination(self):
        """Test default pagination values."""
        request = ListMemoriesRequest(user_id="user123")
        assert request.page == 1
        assert request.page_size == 20

    def test_page_validation(self):
        """Test page number must be >= 1."""
        with pytest.raises(ValidationError):
            ListMemoriesRequest(user_id="user123", page=0)

    def test_page_size_limits(self):
        """Test page size limits."""
        # Too large
        with pytest.raises(ValidationError):
            ListMemoriesRequest(user_id="user123", page_size=101)
        # Too small
        with pytest.raises(ValidationError):
            ListMemoriesRequest(user_id="user123", page_size=0)


class TestMemoryList:
    """Test MemoryList contract."""

    def test_valid_memory_list(self):
        """Test valid memory list response."""
        memories = [
            Memory(id="mem1", user_id="user123", content="Memory 1", tags=[], created_at="2025-01-01T00:00:00Z"),
            Memory(id="mem2", user_id="user123", content="Memory 2", tags=["tag1"], created_at="2025-01-02T00:00:00Z"),
        ]
        memory_list = MemoryList(memories=memories, total=100, page=1, page_size=20)
        assert len(memory_list.memories) == 2
        assert memory_list.total == 100

    def test_empty_memory_list(self):
        """Test empty memory list."""
        memory_list = MemoryList(memories=[], total=0, page=1, page_size=20)
        assert len(memory_list.memories) == 0


class TestSerialization:
    """Test JSON serialization for memory contracts."""

    def test_create_request_roundtrip(self):
        """Test serialization roundtrip."""
        original = CreateMemoryRequest(user_id="user123", content="Test memory", tags=["test"])
        json_str = original.model_dump_json()
        restored = CreateMemoryRequest.model_validate_json(json_str)
        assert restored.user_id == original.user_id
        assert restored.content == original.content
        assert restored.tags == original.tags
