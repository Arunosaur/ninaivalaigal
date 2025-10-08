"""
Tests for Graph ML Engine
Testing graph-aware machine learning for memory ranking and relationship prediction
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from server.intelligence.graph_ml import GraphMLEngine
from server.intelligence.models import (
    EmbeddingUpdate,
    GraphContext,
    GraphMLMetrics,
    RelationshipPrediction,
    ScoredMemory,
    TeamContext,
    UserFeedback,
    WeightUpdate,
)


class TestGraphMLEngine:
    """Test suite for Graph ML Engine"""

    @pytest.fixture
    def ml_config(self):
        """Graph ML engine configuration"""
        return {
            "model_cache_size": 100,
            "prediction_threshold": 0.7,
            "learning_rate": 0.01,
        }

    @pytest.fixture
    def ml_engine(self, ml_config):
        """Graph ML engine instance"""
        return GraphMLEngine(ml_config)

    @pytest.fixture
    def graph_context(self):
        """Graph context for ML operations"""
        team_context = TeamContext(
            team_id="engineering",
            team_name="Engineering Team",
            department="Technology",
            organization="Ninaivalaigal",
            access_level=4,
            specializations=["backend", "ai", "ml"],
            collaboration_history={"support": 0.8},
        )

        return GraphContext(
            user_id="user_123",
            team_context=team_context,
            current_task="debugging_api_issue",
            recent_memories=["mem_001", "mem_002"],
            collaboration_network={"user_456": 0.7, "user_789": 0.5},
            expertise_areas=["python", "fastapi", "debugging"],
        )

    @pytest.fixture
    def candidate_memories(self):
        """Candidate memories for ML ranking"""
        return [
            {
                "id": "mem_001",
                "title": "FastAPI Debugging Guide",
                "content": "Comprehensive guide for debugging FastAPI applications with common issues and solutions",
                "tags": ["fastapi", "debugging", "python", "api"],
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "quality_score": 0.9,
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
            },
            {
                "id": "mem_002",
                "title": "Database Connection Issues",
                "content": "Solutions for common database connection problems in web applications",
                "tags": ["database", "connection", "troubleshooting"],
                "created_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "last_accessed": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "quality_score": 0.8,
                "embedding": [0.2, 0.3, 0.1, 0.5, 0.4],
            },
            {
                "id": "mem_003",
                "title": "Frontend React Components",
                "content": "Reusable React components for building user interfaces",
                "tags": ["react", "frontend", "components", "ui"],
                "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                "last_accessed": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "quality_score": 0.7,
                "embedding": [0.5, 0.1, 0.4, 0.2, 0.3],
            },
        ]

    @pytest.fixture
    def user_feedback_batch(self):
        """Batch of user feedback for learning"""
        return [
            UserFeedback(
                feedback_id="fb_001",
                user_id="user_123",
                memory_id="mem_001",
                query="fastapi debugging",
                relevance_rating=5,
                usefulness_rating=5,
                context_accuracy=4,
                feedback_text="Very helpful for solving API issues",
            ),
            UserFeedback(
                feedback_id="fb_002",
                user_id="user_123",
                memory_id="mem_002",
                query="database connection",
                relevance_rating=4,
                usefulness_rating=4,
                context_accuracy=4,
                feedback_text="Good troubleshooting steps",
            ),
            UserFeedback(
                feedback_id="fb_003",
                user_id="user_123",
                memory_id="mem_003",
                query="api debugging",
                relevance_rating=2,
                usefulness_rating=2,
                context_accuracy=2,
                feedback_text="Not relevant for backend debugging",
            ),
        ]

    def test_ml_engine_initialization(self, ml_config):
        """Test ML engine initializes correctly"""
        engine = GraphMLEngine(ml_config)

        assert engine.config == ml_config
        assert engine.model_cache == {}
        assert "content_similarity" in engine.feature_weights
        assert "graph_centrality" in engine.feature_weights
        assert engine.metrics.model_accuracy == 0.0
        assert engine.metrics.model_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_predict_memory_relevance(
        self, ml_engine, graph_context, candidate_memories
    ):
        """Test memory relevance prediction with graph ML"""

        query = "fastapi debugging issues"

        # Mock graph feature extraction
        with (
            patch.object(ml_engine, "_extract_graph_features") as mock_features,
            patch.object(ml_engine, "_calculate_content_similarity") as mock_content,
            patch.object(ml_engine, "_get_feedback_score") as mock_feedback,
            patch.object(ml_engine, "_get_memory_connections") as mock_connections,
        ):

            # Setup mocks
            mock_features.return_value = {
                "centrality": 0.8,
                "collaboration_strength": 0.7,
                "graph_similarity": 0.6,
                "expertise_alignment": 0.9,
            }

            mock_content.side_effect = [0.9, 0.6, 0.2]  # High, medium, low relevance
            mock_feedback.side_effect = [0.8, 0.7, 0.3]
            mock_connections.return_value = ["mem_004", "mem_005"]

            scored_memories = await ml_engine.predict_memory_relevance(
                query=query,
                context=graph_context,
                candidate_memories=candidate_memories,
                limit=10,
            )

            # Verify results
            assert len(scored_memories) == 3
            assert all(isinstance(m, ScoredMemory) for m in scored_memories)

            # Should be sorted by relevance score (highest first)
            assert (
                scored_memories[0].relevance_score >= scored_memories[1].relevance_score
            )
            assert (
                scored_memories[1].relevance_score >= scored_memories[2].relevance_score
            )

            # First memory should have highest score (FastAPI debugging)
            assert scored_memories[0].memory_id == "mem_001"
            assert scored_memories[0].relevance_score > 0.7
            assert scored_memories[0].confidence > 0.0
            assert len(scored_memories[0].reasoning) > 0

    @pytest.mark.asyncio
    async def test_predict_relationships(self, ml_engine, graph_context):
        """Test relationship prediction between memories"""

        memory_id = "mem_001"
        candidate_memories = ["mem_002", "mem_003", "mem_004"]

        # Mock trained model in cache
        mock_model = Mock()
        ml_engine.model_cache["relationship_predictor"] = mock_model

        with (
            patch.object(ml_engine, "_extract_pair_features") as mock_features,
            patch.object(ml_engine, "_predict_with_model") as mock_predict,
            patch.object(ml_engine, "_generate_relationship_evidence") as mock_evidence,
            patch.object(ml_engine, "_find_graph_path") as mock_path,
        ):

            # Setup mocks
            mock_features.return_value = {"similarity": 0.8, "co_occurrence": 0.6}
            mock_predict.side_effect = [
                {"confidence": 0.9, "relationship_type": "related_topic"},
                {
                    "confidence": 0.5,
                    "relationship_type": "weak_connection",
                },  # Below threshold
                {"confidence": 0.8, "relationship_type": "complementary"},
            ]
            mock_evidence.return_value = ["Similar tags", "Common usage patterns"]
            mock_path.return_value = ["mem_001", "intermediate", "mem_002"]

            predictions = await ml_engine.predict_relationships(
                memory_id=memory_id,
                candidate_memories=candidate_memories,
                context=graph_context,
                threshold=0.7,
            )

            # Verify predictions
            assert len(predictions) == 2  # Only 2 above threshold
            assert all(isinstance(p, RelationshipPrediction) for p in predictions)

            # Should be sorted by confidence
            assert predictions[0].confidence >= predictions[1].confidence
            assert predictions[0].confidence >= 0.7

            # Verify prediction structure
            assert predictions[0].memory_a == memory_id
            assert predictions[0].memory_b in candidate_memories
            assert len(predictions[0].supporting_evidence) > 0
            assert len(predictions[0].graph_path) > 0

    @pytest.mark.asyncio
    async def test_optimize_embeddings(self, ml_engine):
        """Test embedding optimization with graph features"""

        memories = [
            {
                "id": "mem_001",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "title": "Test Memory",
                "content": "Test content",
            }
        ]

        graph_data = {
            "nodes": ["mem_001", "mem_002"],
            "edges": [("mem_001", "mem_002", 0.8)],
            "centrality": {"mem_001": 0.7},
        }

        with (
            patch.object(ml_engine, "_extract_memory_graph_features") as mock_features,
            patch.object(ml_engine, "_enhance_embedding_with_graph") as mock_enhance,
            patch.object(
                ml_engine, "_calculate_embedding_improvement"
            ) as mock_improvement,
        ):

            mock_features.return_value = {"centrality": 0.7, "clustering": 0.6}
            mock_enhance.return_value = [
                0.15,
                0.25,
                0.35,
                0.45,
                0.55,
            ]  # Enhanced embedding
            mock_improvement.return_value = 0.1  # 10% improvement

            updates = await ml_engine.optimize_embeddings(
                memories=memories,
                graph_data=graph_data,
                optimization_target="relevance",
            )

            # Verify updates
            assert len(updates) == 1
            assert isinstance(updates[0], EmbeddingUpdate)
            assert updates[0].memory_id == "mem_001"
            assert updates[0].improvement_score == 0.1
            assert len(updates[0].enhanced_embedding) == 5
            assert updates[0].enhanced_embedding != updates[0].original_embedding

    @pytest.mark.asyncio
    async def test_adapt_ranking_weights(self, ml_engine, user_feedback_batch):
        """Test adaptive learning from user feedback"""

        initial_weights = ml_engine.feature_weights.copy()

        with (
            patch.object(ml_engine, "_analyze_feedback_patterns") as mock_analyze,
            patch.object(ml_engine, "_calculate_weight_gradients") as mock_gradients,
            patch.object(ml_engine, "_evaluate_current_performance") as mock_current,
            patch.object(ml_engine, "_evaluate_updated_performance") as mock_updated,
        ):

            # Setup mocks
            mock_analyze.return_value = {
                "high_relevance_features": ["content_similarity", "graph_centrality"],
                "low_relevance_features": ["temporal_relevance"],
            }

            mock_gradients.return_value = {
                "content_similarity": 0.05,
                "graph_centrality": 0.03,
                "temporal_relevance": -0.02,
            }

            mock_current.return_value = 0.75  # Current performance
            mock_updated.return_value = 0.78  # Improved performance

            weight_update = await ml_engine.adapt_ranking_weights(
                feedback_batch=user_feedback_batch, learning_rate=0.01
            )

            # Verify weight update
            assert isinstance(weight_update, WeightUpdate)
            assert weight_update.performance_improvement > 0
            assert "Improved based on" in weight_update.update_reason

            # Verify weights were updated
            assert ml_engine.feature_weights != initial_weights

            # Verify weights still sum to approximately 1.0
            total_weight = sum(ml_engine.feature_weights.values())
            assert abs(total_weight - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_content_similarity_calculation(self, ml_engine):
        """Test content similarity calculation"""

        query = "fastapi debugging python"
        memory = {
            "content": "This is a comprehensive guide for debugging FastAPI applications in Python",
            "title": "FastAPI Debugging Guide",
        }

        similarity = await ml_engine._calculate_content_similarity(query, memory)

        # Should have high similarity due to matching keywords
        assert similarity > 0.5
        assert similarity <= 1.0

    def test_temporal_relevance_calculation(self, ml_engine, graph_context):
        """Test temporal relevance scoring"""

        # Recent memory
        recent_memory = {
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }

        # Old memory
        old_memory = {
            "created_at": (datetime.utcnow() - timedelta(days=200)).isoformat(),
            "last_accessed": (datetime.utcnow() - timedelta(days=100)).isoformat(),
        }

        recent_score = ml_engine._calculate_temporal_relevance(
            recent_memory, graph_context
        )
        old_score = ml_engine._calculate_temporal_relevance(old_memory, graph_context)

        # Recent memory should score higher
        assert recent_score > old_score
        assert recent_score > 0.8
        assert old_score < 0.5

    def test_prediction_confidence_calculation(self, ml_engine):
        """Test prediction confidence calculation"""

        # High agreement between features
        high_agreement_scores = [0.8, 0.85, 0.82, 0.78, 0.83, 0.81]
        high_confidence = ml_engine._calculate_prediction_confidence(
            high_agreement_scores
        )

        # Low agreement between features
        low_agreement_scores = [0.9, 0.2, 0.8, 0.1, 0.7, 0.3]
        low_confidence = ml_engine._calculate_prediction_confidence(
            low_agreement_scores
        )

        # High agreement should have higher confidence
        assert high_confidence > low_confidence
        assert high_confidence > 0.7
        assert low_confidence < 0.5

    def test_reasoning_generation(self, ml_engine):
        """Test reasoning generation for transparency"""

        # High scores across features
        reasoning = ml_engine._generate_reasoning(0.9, 0.8, 0.7, 0.85, 0.6, 0.75)

        assert len(reasoning) > 0
        assert any("High content similarity" in r for r in reasoning)
        assert any("connected in knowledge graph" in r for r in reasoning)
        assert any("alignment with team context" in r for r in reasoning)

    @pytest.mark.asyncio
    async def test_ml_metrics_tracking(self, ml_engine):
        """Test ML performance metrics tracking"""

        initial_metrics = await ml_engine.get_ml_metrics()
        assert initial_metrics.processing_latency_ms == 0.0
        assert initial_metrics.throughput_qps == 0.0

        # Simulate processing
        ml_engine._update_ml_metrics(processed_count=10, processing_time=50.0)

        updated_metrics = await ml_engine.get_ml_metrics()

        # Verify metrics were updated
        assert updated_metrics.processing_latency_ms > 0
        assert updated_metrics.throughput_qps > 0

    @pytest.mark.asyncio
    async def test_relationship_training_workflow(self, ml_engine):
        """Test relationship predictor training workflow"""

        training_data = [
            {
                "memory_a": "mem_001",
                "memory_b": "mem_002",
                "relationship": "related",
                "features": [0.8, 0.6, 0.7],
            }
        ]

        with (
            patch.object(ml_engine, "_prepare_training_data") as mock_prepare,
            patch.object(ml_engine, "_train_gnn_model") as mock_train,
        ):

            mock_prepare.return_value = (np.array([[0.8, 0.6, 0.7]]), np.array([1]))
            mock_train.return_value = {"model": Mock(), "accuracy": 0.85, "loss": 0.15}

            results = await ml_engine.train_relationship_predictor(training_data)

            # Verify training results
            assert results["accuracy"] == 0.85
            assert "relationship_predictor" in ml_engine.model_cache
            assert ml_engine.metrics.model_accuracy == 0.85

    def test_ml_performance_targets(self, ml_engine):
        """Test ML engine meets performance targets"""

        # Simulate processing batch
        ml_engine._update_ml_metrics(processed_count=20, processing_time=80.0)  # 80ms

        metrics = asyncio.run(ml_engine.get_ml_metrics())

        # Verify performance targets
        assert metrics.processing_latency_ms <= 100  # Target: <100ms
        assert metrics.throughput_qps > 0

        # Test prediction confidence targets
        feature_scores = [0.8, 0.82, 0.78, 0.85, 0.79, 0.83]
        confidence = ml_engine._calculate_prediction_confidence(feature_scores)
        assert confidence >= 0.7  # Target: >70% confidence for consistent features

    @pytest.mark.asyncio
    async def test_weight_adaptation_performance_protection(
        self, ml_engine, user_feedback_batch
    ):
        """Test weight adaptation reverts if performance decreases"""

        initial_weights = ml_engine.feature_weights.copy()

        with (
            patch.object(ml_engine, "_analyze_feedback_patterns") as mock_analyze,
            patch.object(ml_engine, "_calculate_weight_gradients") as mock_gradients,
            patch.object(ml_engine, "_evaluate_current_performance") as mock_current,
            patch.object(ml_engine, "_evaluate_updated_performance") as mock_updated,
        ):

            mock_analyze.return_value = {"patterns": "test"}
            mock_gradients.return_value = {
                "content_similarity": -0.5
            }  # Large negative gradient
            mock_current.return_value = 0.80
            mock_updated.return_value = 0.70  # Performance decreased significantly

            weight_update = await ml_engine.adapt_ranking_weights(
                feedback_batch=user_feedback_batch, learning_rate=0.01
            )

            # Verify weights were reverted
            assert ml_engine.feature_weights == initial_weights
            assert weight_update.performance_improvement == 0.0
            assert "Reverted due to performance decrease" in weight_update.update_reason
