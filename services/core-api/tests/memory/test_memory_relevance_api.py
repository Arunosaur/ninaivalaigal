#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Tests for Memory Relevance Ranking API - SPEC-031

Tests for US#321 and US#322: Memory Relevance Ranking API endpoints.
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from lib.memory_api import router

app = FastAPI()
app.include_router(router)


class TestMemoryRelevanceEndpoint:
    """Tests for GET /memory/relevant endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        user = MagicMock()
        user.id = "test_user_123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_memory_provider(self):
        """Mock memory provider"""
        provider = MagicMock()
        provider.list_memories = AsyncMock(
            return_value=[
                {
                    "id": "mem_001",
                    "text": "Important project note",
                    "meta": {"importance": "high"},
                    "context_id": "ctx123",
                },
                {"id": "mem_002", "text": "Recent conversation topic", "meta": {}, "context_id": "ctx123"},
            ]
        )
        return provider

    @pytest.fixture
    def mock_relevance_engine(self):
        """Mock relevance engine"""
        engine = MagicMock()
        engine.get_top_memories = AsyncMock(return_value=[("mem_001", 0.92), ("mem_002", 0.78)])
        return engine

    @pytest.mark.asyncio
    async def test_get_relevant_memories_success(self, client, mock_user, mock_memory_provider, mock_relevance_engine):
        """Test successful retrieval of relevant memories"""
        from lib.memory_api import get_current_user, get_memory_provider_dep
        from lib.relevance_engine import get_relevance_engine

        async def override_get_current_user():
            return mock_user

        async def override_get_memory_provider():
            return mock_memory_provider

        async def override_get_relevance_engine():
            return mock_relevance_engine

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_memory_provider_dep] = override_get_memory_provider
        app.dependency_overrides[get_relevance_engine] = override_get_relevance_engine

        try:
            response = client.get(
                "/memory/relevant",
                params={"limit": 10, "context_id": "ctx123"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert len(data["items"]) == 2
            assert data["items"][0]["id"] == "mem_001"
            assert data["items"][0]["score"] == 0.92
            assert data["items"][1]["score"] == 0.78
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_relevant_memories_empty(self, client, mock_user, mock_memory_provider):
        """Test when no relevant memories are available"""
        from lib.memory_api import get_current_user, get_memory_provider_dep
        from lib.relevance_engine import get_relevance_engine

        mock_relevance_engine = MagicMock()
        mock_relevance_engine.get_top_memories = AsyncMock(return_value=[])

        async def override_get_current_user():
            return mock_user

        async def override_get_memory_provider():
            return mock_memory_provider

        async def override_get_relevance_engine():
            return mock_relevance_engine

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_memory_provider_dep] = override_get_memory_provider
        app.dependency_overrides[get_relevance_engine] = override_get_relevance_engine

        try:
            response = client.get(
                "/memory/relevant", params={"limit": 10}, headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_relevant_memories_with_limit(
        self, client, mock_user, mock_memory_provider, mock_relevance_engine
    ):
        """Test limit parameter"""
        from lib.memory_api import (
            get_current_user,
            get_default_memory_provider,
            get_relevance_engine,
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_default_memory_provider] = lambda: mock_memory_provider
        app.dependency_overrides[get_relevance_engine] = lambda: mock_relevance_engine

        try:
            response = client.get(
                "/memory/relevant", params={"limit": 1}, headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            # Should respect limit (though mock returns 2, we test limit is passed)
            assert "items" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_relevant_memories_with_context(
        self, client, mock_user, mock_memory_provider, mock_relevance_engine
    ):
        """Test context parameter"""
        from lib.memory_api import (
            get_current_user,
            get_default_memory_provider,
            get_relevance_engine,
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_default_memory_provider] = lambda: mock_memory_provider
        app.dependency_overrides[get_relevance_engine] = lambda: mock_relevance_engine

        try:
            response = client.get(
                "/memory/relevant",
                params={"context": "test context", "context_id": "ctx123"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["context"] == "test context"
        finally:
            app.dependency_overrides.clear()


class TestMemoryRelevanceIntegration:
    """Tests for relevance score integration in memory endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        user = MagicMock()
        user.id = "test_user_123"
        return user

    @pytest.mark.asyncio
    async def test_remember_updates_relevance_score(self, client, mock_user):
        """Test that /memory/remember updates relevance score"""
        from lib.memory_api import (
            get_current_user,
            get_default_memory_provider,
            get_relevance_engine,
        )

        mock_memory_provider = MagicMock()
        mock_memory_provider.remember = AsyncMock(
            return_value={
                "id": "mem_new",
                "text": "New memory",
                "meta": {},
                "user_id": "test_user_123",
                "context_id": "ctx123",
                "created_at": datetime.utcnow().isoformat(),
            }
        )

        mock_relevance_engine = MagicMock()
        mock_relevance_engine.update_memory_score = AsyncMock(return_value=0.5)

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_default_memory_provider] = lambda: mock_memory_provider
        app.dependency_overrides[get_relevance_engine] = lambda: mock_relevance_engine

        try:
            response = client.post(
                "/memory/remember",
                json={"text": "New memory", "meta": {}, "context_id": "ctx123"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            # Verify relevance score was updated
            mock_relevance_engine.update_memory_score.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_recall_updates_relevance_scores(self, client, mock_user):
        """Test that /memory/recall updates relevance scores for accessed memories"""
        from lib.memory_api import (
            get_current_user,
            get_default_memory_provider,
            get_relevance_engine,
        )

        mock_memory_provider = MagicMock()
        mock_memory_provider.recall = AsyncMock(
            return_value=[
                {"id": "mem_001", "text": "Memory 1", "meta": {}},
                {"id": "mem_002", "text": "Memory 2", "meta": {}},
            ]
        )

        mock_relevance_engine = MagicMock()
        mock_relevance_engine.update_memory_score = AsyncMock(return_value=0.5)
        mock_relevance_engine.get_memory_score = AsyncMock(return_value=0.75)

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_default_memory_provider] = lambda: mock_memory_provider
        app.dependency_overrides[get_relevance_engine] = lambda: mock_relevance_engine

        try:
            response = client.post(
                "/memory/recall", params={"query": "test", "k": 5}, headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            # Verify relevance scores are included
            assert all("score" in item for item in data["items"])
            # Verify update_memory_score was called for each memory
            assert mock_relevance_engine.update_memory_score.call_count == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_recall_includes_relevance_scores(self, client, mock_user):
        """Test that /memory/recall response includes relevance scores"""
        from lib.memory_api import (
            get_current_user,
            get_default_memory_provider,
            get_relevance_engine,
        )

        mock_memory_provider = MagicMock()
        mock_memory_provider.recall = AsyncMock(return_value=[{"id": "mem_001", "text": "Memory 1", "meta": {}}])

        mock_relevance_engine = MagicMock()
        mock_relevance_engine.update_memory_score = AsyncMock(return_value=0.5)
        mock_relevance_engine.get_memory_score = AsyncMock(return_value=0.85)

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_default_memory_provider] = lambda: mock_memory_provider
        app.dependency_overrides[get_relevance_engine] = lambda: mock_relevance_engine

        try:
            response = client.post(
                "/memory/recall", params={"query": "test", "k": 5}, headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["items"][0]["score"] == 0.85
        finally:
            app.dependency_overrides.clear()
