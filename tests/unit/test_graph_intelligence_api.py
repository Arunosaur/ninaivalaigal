"""
Unit tests for Graph Intelligence API - SPEC-061

Tests the FastAPI endpoints for graph reasoning functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add project root to path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from server.graph_intelligence_api import router
from server.graph.graph_reasoner import (
    ContextExplanation,
    RelevanceInference,
    ReasoningPath,
)


@pytest.fixture
def app():
    """Create FastAPI app with graph intelligence router"""
    app = FastAPI()

    # Override dependencies for testing
    def mock_get_current_user():
        return {"user_id": "test_user_123", "email": "test@example.com"}

    def mock_get_graph_reasoner():
        reasoner = AsyncMock()
        reasoner.cache_ttl = 300
        return reasoner

    def mock_get_age_client():
        return AsyncMock()

    def mock_get_redis_client():
        return AsyncMock()

    app.dependency_overrides = {
        "server.graph_intelligence_api.get_current_user": mock_get_current_user,
        "server.graph_intelligence_api.get_graph_reasoner": mock_get_graph_reasoner,
        "server.graph_intelligence_api.get_age_client": mock_get_age_client,
        "server.graph_intelligence_api.get_redis_client": mock_get_redis_client,
    }

    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return {"user_id": "test_user_123", "email": "test@example.com"}


@pytest.fixture
def mock_graph_reasoner():
    """Mock GraphReasoner instance"""
    reasoner = AsyncMock()
    reasoner.cache_ttl = 300
    return reasoner


@pytest.fixture
def sample_explanation():
    """Sample context explanation"""
    reasoning_path = ReasoningPath(
        nodes=["user_001", "memory_001"],
        edges=["CREATED"],
        weights=[0.9],
        total_weight=0.9,
        confidence=0.8,
        reasoning="Direct creation relationship",
    )

    return ContextExplanation(
        memory_id="mem_001",
        retrieval_reason="Direct user creation",
        paths=[reasoning_path],
        relevance_score=0.85,
        confidence=0.8,
        supporting_evidence=["Strong creation relationship"],
    )


@pytest.fixture
def sample_inference():
    """Sample relevance inference"""
    return RelevanceInference(
        suggested_memories=["mem_002", "mem_003"],
        suggested_agents=["agent_001"],
        reasoning_scores={"mem_002": 0.8, "agent_001": 0.7},
        proximity_metrics={"mem_002": 0.9},
        confidence=0.75,
    )


class TestExplainContext:
    """Test explain context endpoint"""

    def test_explain_context_success(self, client, sample_explanation):
        """Test successful context explanation"""
        # Mock the graph reasoner response
        with patch(
            "server.graph_intelligence_api.get_graph_reasoner"
        ) as mock_get_reasoner:
            mock_reasoner = AsyncMock()
            mock_reasoner.explain_context.return_value = sample_explanation
            mock_get_reasoner.return_value = mock_reasoner

        request_data = {
            "memory_id": "mem_001",
            "context_type": "retrieval",
            "max_depth": 3,
        }

        response = client.post("/graph/explain-context", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "mem_001"
        assert data["retrieval_reason"] == "Direct user creation"
        assert data["confidence"] == 0.8
        assert len(data["paths"]) == 1
        assert len(data["supporting_evidence"]) == 1

        mock_graph_reasoner.explain_context.assert_called_once_with(
            memory_id="mem_001",
            user_id="test_user_123",
            context_type="retrieval",
            max_depth=3,
        )

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_explain_context_with_defaults(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
        sample_explanation,
    ):
        """Test context explanation with default parameters"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.explain_context.return_value = sample_explanation

        request_data = {"memory_id": "mem_001"}

        response = client.post("/graph/explain-context", json=request_data)

        assert response.status_code == 200
        mock_graph_reasoner.explain_context.assert_called_once_with(
            memory_id="mem_001",
            user_id="test_user_123",
            context_type="retrieval",
            max_depth=3,
        )

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_explain_context_error(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
    ):
        """Test context explanation error handling"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.explain_context.side_effect = Exception("Graph error")

        request_data = {"memory_id": "mem_001"}

        response = client.post("/graph/explain-context", json=request_data)

        assert response.status_code == 500
        assert "Context explanation failed" in response.json()["detail"]


class TestInferRelevance:
    """Test infer relevance endpoint"""

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_infer_relevance_success(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
        sample_inference,
    ):
        """Test successful relevance inference"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.infer_relevance.return_value = sample_inference

        request_data = {
            "current_memory_id": "mem_001",
            "suggestion_count": 5,
            "context_memories": ["mem_000"],
        }

        response = client.post("/graph/infer-relevance", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["suggested_memories"]) == 2
        assert len(data["suggested_agents"]) == 1
        assert data["confidence"] == 0.75
        assert "mem_002" in data["reasoning_scores"]

        mock_graph_reasoner.infer_relevance.assert_called_once_with(
            current_memory_id="mem_001",
            user_id="test_user_123",
            suggestion_count=5,
            context_memories=["mem_000"],
        )

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_infer_relevance_validation(
        self, mock_get_reasoner, mock_get_user, client, mock_current_user
    ):
        """Test relevance inference request validation"""
        mock_get_user.return_value = mock_current_user

        # Test invalid suggestion count
        request_data = {
            "current_memory_id": "mem_001",
            "suggestion_count": 25,  # Exceeds maximum of 20
        }

        response = client.post("/graph/infer-relevance", json=request_data)
        assert response.status_code == 422


class TestFeedbackLoop:
    """Test feedback loop endpoint"""

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_feedback_loop_success(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
    ):
        """Test successful feedback processing"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.feedback_loop.return_value = {
            "feedback_stored": True,
            "weight_updates": {"updated_edges": 3},
            "cache_invalidated": True,
        }

        request_data = {
            "memory_id": "mem_001",
            "feedback_type": "relevance",
            "feedback_score": 0.8,
            "context_data": {"source": "user_rating"},
        }

        response = client.post("/graph/feedback-loop", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["feedback_stored"] is True
        assert data["weight_updates"]["updated_edges"] == 3

        mock_graph_reasoner.feedback_loop.assert_called_once_with(
            user_id="test_user_123",
            memory_id="mem_001",
            feedback_type="relevance",
            feedback_score=0.8,
            context_data={"source": "user_rating"},
        )

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_feedback_loop_validation(
        self, mock_get_reasoner, mock_get_user, client, mock_current_user
    ):
        """Test feedback loop request validation"""
        mock_get_user.return_value = mock_current_user

        # Test invalid feedback score
        request_data = {
            "memory_id": "mem_001",
            "feedback_type": "relevance",
            "feedback_score": 1.5,  # Exceeds maximum of 1.0
        }

        response = client.post("/graph/feedback-loop", json=request_data)
        assert response.status_code == 422


class TestAnalyzeNetwork:
    """Test analyze network endpoint"""

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_analyze_network_success(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
    ):
        """Test successful network analysis"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.analyze_memory_network.return_value = {
            "structure": {"node_count": 10, "edge_count": 15, "density": 0.3},
            "patterns": {"hubs": [{"node_id": "mem_001", "connections": 5}]},
            "insights": ["Well-connected memory system"],
            "recommendations": ["Consider adding more relationships"],
        }

        request_data = {"analysis_type": "comprehensive", "time_window": "30d"}

        response = client.post("/graph/analyze-network", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["structure"]["node_count"] == 10
        assert len(data["insights"]) == 1
        assert len(data["recommendations"]) == 1

        mock_graph_reasoner.analyze_memory_network.assert_called_once_with(
            user_id="test_user_123", analysis_type="comprehensive", time_window="30d"
        )


class TestHealthAndStats:
    """Test health and stats endpoints"""

    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_health_endpoint(self, mock_get_reasoner, client, mock_graph_reasoner):
        """Test health check endpoint"""
        mock_get_reasoner.return_value = mock_graph_reasoner

        response = client.get("/graph/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "graph-intelligence"
        assert data["cache_ttl"] == 300
        assert "components" in data

    @patch("server.graph_intelligence_api.get_current_user")
    @patch("server.graph_intelligence_api.get_graph_reasoner")
    def test_stats_endpoint(
        self,
        mock_get_reasoner,
        mock_get_user,
        client,
        mock_current_user,
        mock_graph_reasoner,
    ):
        """Test stats endpoint"""
        mock_get_user.return_value = mock_current_user
        mock_get_reasoner.return_value = mock_graph_reasoner
        mock_graph_reasoner.redis_client.keys.return_value = [
            "graph:explain:test_user_123:mem_001",
            "graph:infer:test_user_123:mem_002",
        ]

        response = client.get("/graph/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert data["total_cache_entries"] == 2
        assert data["cache_ttl_seconds"] == 300


class TestRequestValidation:
    """Test request validation"""

    def test_explain_context_missing_memory_id(self, client):
        """Test explain context with missing memory_id"""
        request_data = {"context_type": "retrieval"}

        response = client.post("/graph/explain-context", json=request_data)
        assert response.status_code == 422

    def test_infer_relevance_missing_current_memory_id(self, client):
        """Test infer relevance with missing current_memory_id"""
        request_data = {"suggestion_count": 5}

        response = client.post("/graph/infer-relevance", json=request_data)
        assert response.status_code == 422

    def test_feedback_loop_missing_required_fields(self, client):
        """Test feedback loop with missing required fields"""
        request_data = {"memory_id": "mem_001"}

        response = client.post("/graph/feedback-loop", json=request_data)
        assert response.status_code == 422
