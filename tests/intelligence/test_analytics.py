"""
Tests for Graph Analytics Engine
Testing real-time graph intelligence and insights generation
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.intelligence.analytics import GraphAnalyticsEngine
from server.intelligence.models import (FederationMetrics, GraphMLMetrics,
                                        KnowledgeGap, SuggestedConnection,
                                        TeamContext, TeamInsights,
                                        TrendingTopic)


class TestGraphAnalyticsEngine:
    """Test suite for Graph Analytics Engine"""

    @pytest.fixture
    def analytics_config(self):
        """Analytics engine configuration"""
        return {"cache_ttl": 300, "max_trends": 50, "min_confidence": 0.6}

    @pytest.fixture
    def analytics_engine(self, analytics_config):
        """Graph analytics engine instance"""
        return GraphAnalyticsEngine(analytics_config)

    @pytest.fixture
    def team_context(self):
        """Team context for analytics testing"""
        return TeamContext(
            team_id="engineering",
            team_name="Engineering Team",
            department="Technology",
            organization="Ninaivalaigal",
            access_level=4,
            specializations=["backend", "api", "debugging", "python"],
            collaboration_history={"support": 0.8, "product": 0.6},
        )

    @pytest.fixture
    def sample_knowledge_gaps(self):
        """Sample knowledge gaps for testing"""
        return [
            {
                "topic_area": "kubernetes_deployment",
                "confidence": 0.85,
                "urgency": 0.9,
                "related_queries": [
                    "How to deploy to k8s?",
                    "Kubernetes troubleshooting",
                ],
                "source": "query_analysis",
            },
            {
                "topic_area": "performance_optimization",
                "confidence": 0.75,
                "urgency": 0.7,
                "related_queries": ["API performance issues", "Database optimization"],
                "source": "collaboration_gaps",
            },
            {
                "topic_area": "security_best_practices",
                "confidence": 0.9,
                "urgency": 0.8,
                "related_queries": ["Security vulnerabilities", "Auth implementation"],
                "source": "standard_gaps",
            },
        ]

    @pytest.fixture
    def sample_trending_topics(self):
        """Sample trending topics data"""
        return {
            "kubernetes": {
                "memory_ids": ["mem_k8s_001", "mem_k8s_002", "mem_k8s_003"],
                "teams": ["engineering", "devops"],
                "total_activity": 150,
                "time_series": [10, 15, 25, 40, 60],  # Growing trend
            },
            "fastapi": {
                "memory_ids": ["mem_api_001", "mem_api_002"],
                "teams": ["engineering"],
                "total_activity": 80,
                "time_series": [20, 18, 22, 20, 19],  # Stable
            },
            "machine_learning": {
                "memory_ids": ["mem_ml_001", "mem_ml_002", "mem_ml_003", "mem_ml_004"],
                "teams": ["engineering", "data_science"],
                "total_activity": 200,
                "time_series": [5, 10, 30, 80, 75],  # High growth then plateau
            },
        }

    def test_analytics_engine_initialization(self, analytics_config):
        """Test analytics engine initializes correctly"""
        engine = GraphAnalyticsEngine(analytics_config)

        assert engine.config == analytics_config
        assert engine.analytics_cache == {}
        assert isinstance(engine.trend_history, defaultdict)
        assert engine.knowledge_graph == {}
        assert engine.team_analytics == {}

    @pytest.mark.asyncio
    async def test_detect_knowledge_gaps(
        self, analytics_engine, team_context, sample_knowledge_gaps
    ):
        """Test knowledge gap detection with confidence filtering"""

        analysis_window = timedelta(days=30)
        confidence_threshold = 0.7

        with (
            patch.object(
                analytics_engine, "_analyze_team_knowledge_coverage"
            ) as mock_coverage,
            patch.object(analytics_engine, "_analyze_query_patterns") as mock_queries,
            patch.object(
                analytics_engine, "_compare_with_knowledge_standards"
            ) as mock_standards,
            patch.object(
                analytics_engine, "_analyze_collaboration_gaps"
            ) as mock_collab,
            patch.object(analytics_engine, "_find_gap_sources") as mock_sources,
            patch.object(analytics_engine, "_identify_topic_experts") as mock_experts,
        ):

            # Setup mocks
            mock_coverage.return_value = {"kubernetes": 0.3, "security": 0.4}
            mock_queries.return_value = [sample_knowledge_gaps[0]]  # Kubernetes gap
            mock_standards.return_value = [sample_knowledge_gaps[2]]  # Security gap
            mock_collab.return_value = [sample_knowledge_gaps[1]]  # Performance gap

            mock_sources.return_value = ["internal_docs", "external_training"]
            mock_experts.return_value = ["expert_user_001", "expert_user_002"]

            knowledge_gaps = await analytics_engine.detect_knowledge_gaps(
                team_context=team_context,
                analysis_window=analysis_window,
                confidence_threshold=confidence_threshold,
            )

            # Verify gap detection
            assert len(knowledge_gaps) == 3  # All gaps above threshold
            assert all(isinstance(gap, KnowledgeGap) for gap in knowledge_gaps)

            # Should be sorted by urgency * confidence
            assert (
                knowledge_gaps[0].urgency_score * knowledge_gaps[0].confidence
                >= knowledge_gaps[1].urgency_score * knowledge_gaps[1].confidence
            )

            # Verify gap structure
            first_gap = knowledge_gaps[0]
            assert first_gap.team_id == team_context.team_id
            assert first_gap.confidence >= confidence_threshold
            assert len(first_gap.suggested_sources) > 0
            assert len(first_gap.potential_experts) > 0
            assert len(first_gap.related_queries) > 0

    @pytest.mark.asyncio
    async def test_identify_trending_topics(
        self, analytics_engine, sample_trending_topics
    ):
        """Test trending topic identification with growth rate filtering"""

        with (
            patch.object(analytics_engine, "_get_memory_access_data") as mock_access,
            patch.object(
                analytics_engine, "_get_memory_creation_data"
            ) as mock_creation,
            patch.object(analytics_engine, "_extract_topic_activity") as mock_activity,
            patch.object(
                analytics_engine, "_calculate_topic_growth_rate"
            ) as mock_growth,
            patch.object(analytics_engine, "_find_peak_activity_time") as mock_peak,
        ):

            # Setup mocks
            mock_access.return_value = {"access_data": "mock"}
            mock_creation.return_value = {"creation_data": "mock"}
            mock_activity.return_value = sample_trending_topics

            # Mock growth rates - only kubernetes and ML are trending
            mock_growth.side_effect = [
                0.8,
                0.1,
                0.6,
            ]  # k8s: high, fastapi: low, ml: medium
            mock_peak.return_value = datetime.utcnow()

            trending_topics = await analytics_engine.identify_trending_topics(
                scope="organization", time_window="24h", min_growth_rate=0.2
            )

            # Verify trending topics
            assert len(trending_topics) == 2  # Only k8s and ML above threshold
            assert all(isinstance(topic, TrendingTopic) for topic in trending_topics)

            # Should be sorted by trend score
            assert trending_topics[0].trend_score >= trending_topics[1].trend_score

            # Verify topic structure
            first_topic = trending_topics[0]
            assert first_topic.growth_rate >= 0.2
            assert len(first_topic.related_memories) > 0
            assert len(first_topic.teams_involved) > 0
            assert first_topic.time_window == "24h"

    @pytest.mark.asyncio
    async def test_suggest_memory_connections(self, analytics_engine):
        """Test memory connection suggestions"""

        memory_id = "mem_001"
        context = {"user_id": "user_123", "current_task": "debugging"}

        memory_data = {
            "id": memory_id,
            "title": "API Debugging Guide",
            "content": "Guide for debugging REST API issues",
            "tags": ["api", "debugging", "rest"],
        }

        candidates = [
            {
                "id": "mem_002",
                "title": "Database Connection Issues",
                "content": "Troubleshooting database connections",
                "tags": ["database", "debugging", "connection"],
            },
            {
                "id": "mem_003",
                "title": "Frontend React Guide",
                "content": "Building React components",
                "tags": ["react", "frontend", "ui"],
            },
        ]

        with (
            patch.object(
                analytics_engine, "_get_memory_data", return_value=memory_data
            ),
            patch.object(
                analytics_engine, "_get_existing_connections", return_value=[]
            ),
            patch.object(
                analytics_engine, "_find_connection_candidates", return_value=candidates
            ),
            patch.object(
                analytics_engine, "_analyze_potential_connection"
            ) as mock_analyze,
        ):

            # Mock connection analysis - first candidate is relevant, second is not
            mock_analyze.side_effect = [
                {
                    "confidence": 0.8,
                    "type": "complementary",
                    "reasoning": "Both related to debugging",
                    "value": 0.7,
                },
                {
                    "confidence": 0.3,  # Below threshold
                    "type": "weak",
                    "reasoning": "Different domains",
                    "value": 0.2,
                },
            ]

            suggestions = await analytics_engine.suggest_memory_connections(
                memory_id=memory_id, context=context, max_suggestions=10
            )

            # Verify suggestions
            assert len(suggestions) == 1  # Only one above confidence threshold
            assert isinstance(suggestions[0], SuggestedConnection)

            suggestion = suggestions[0]
            assert suggestion.source_memory == memory_id
            assert suggestion.target_memory == "mem_002"
            assert suggestion.confidence >= 0.6
            assert suggestion.potential_value > 0
            assert len(suggestion.reasoning) > 0

    @pytest.mark.asyncio
    async def test_generate_team_insights(self, analytics_engine, team_context):
        """Test comprehensive team insights generation"""

        team_id = team_context.team_id
        analysis_period = timedelta(days=30)

        # Mock all the analysis components
        with (
            patch.object(
                analytics_engine, "_get_team_context", return_value=team_context
            ),
            patch.object(
                analytics_engine, "_analyze_comprehensive_knowledge_coverage"
            ) as mock_coverage,
            patch.object(
                analytics_engine, "_analyze_team_collaboration_patterns"
            ) as mock_collab,
            patch.object(analytics_engine, "identify_trending_topics") as mock_trends,
            patch.object(analytics_engine, "detect_knowledge_gaps") as mock_gaps,
            patch.object(
                analytics_engine, "_calculate_team_productivity_metrics"
            ) as mock_metrics,
            patch.object(
                analytics_engine, "_generate_team_recommendations"
            ) as mock_recommendations,
        ):

            # Setup mock returns
            mock_coverage.return_value = {
                "backend": 0.8,
                "frontend": 0.4,
                "devops": 0.3,
                "security": 0.5,
            }

            mock_collab.return_value = {
                "internal_collaboration_score": 0.7,
                "external_collaboration_score": 0.4,
                "knowledge_sharing_frequency": 0.6,
            }

            mock_trends.return_value = [
                TrendingTopic(
                    topic="kubernetes",
                    trend_score=0.9,
                    growth_rate=0.8,
                    related_memories=["mem_k8s_001"],
                    teams_involved=["engineering"],
                    time_window="30d",
                    peak_timestamp=datetime.utcnow(),
                )
            ]

            mock_gaps.return_value = [
                KnowledgeGap(
                    gap_id="gap_001",
                    team_id=team_id,
                    topic_area="security",
                    confidence=0.8,
                    suggested_sources=["training"],
                    urgency_score=0.7,
                    related_queries=["security best practices"],
                    potential_experts=["security_expert"],
                )
            ]

            mock_metrics.return_value = {
                "knowledge_reuse_rate": 0.6,
                "avg_response_time": 2.5,
                "collaboration_frequency": 0.7,
            }

            mock_recommendations.return_value = [
                "Improve frontend knowledge coverage",
                "Increase external team collaboration",
                "Address security knowledge gap",
            ]

            insights = await analytics_engine.generate_team_insights(
                team_id=team_id, analysis_period=analysis_period
            )

            # Verify insights structure
            assert isinstance(insights, TeamInsights)
            assert insights.team_id == team_id
            assert len(insights.knowledge_coverage) > 0
            assert len(insights.collaboration_patterns) > 0
            assert len(insights.trending_topics) > 0
            assert len(insights.knowledge_gaps) > 0
            assert len(insights.productivity_metrics) > 0
            assert len(insights.recommendations) > 0

            # Verify insights are cached
            assert team_id in analytics_engine.team_analytics

    @pytest.mark.asyncio
    async def test_get_real_time_analytics_data(self, analytics_engine):
        """Test real-time analytics data retrieval for dashboard"""

        with (
            patch.object(analytics_engine, "_get_overview_analytics") as mock_overview,
            patch.object(analytics_engine, "_get_team_analytics") as mock_team,
            patch.object(analytics_engine, "_get_trending_analytics") as mock_trends,
            patch.object(analytics_engine, "_get_knowledge_gap_analytics") as mock_gaps,
        ):

            # Setup mock returns
            mock_overview.return_value = {
                "total_memories": 1000,
                "active_teams": 5,
                "trending_topics_count": 3,
            }

            mock_team.return_value = {
                "team_knowledge_score": 0.75,
                "collaboration_index": 0.6,
            }

            mock_trends.return_value = {
                "top_trends": ["kubernetes", "fastapi", "security"],
                "growth_rates": [0.8, 0.3, 0.5],
            }

            mock_gaps.return_value = {
                "critical_gaps": 2,
                "total_gaps": 5,
                "avg_confidence": 0.7,
            }

            # Test different dashboard types
            overview_data = await analytics_engine.get_real_time_analytics_data(
                "overview"
            )
            team_data = await analytics_engine.get_real_time_analytics_data(
                "team", filters={"team_id": "engineering"}
            )
            trends_data = await analytics_engine.get_real_time_analytics_data("trends")
            gaps_data = await analytics_engine.get_real_time_analytics_data("gaps")

            # Verify data structure
            assert "total_memories" in overview_data
            assert "team_knowledge_score" in team_data
            assert "top_trends" in trends_data
            assert "critical_gaps" in gaps_data

    def test_time_window_parsing(self, analytics_engine):
        """Test time window string parsing"""

        # Test various time window formats
        assert analytics_engine._parse_time_window("1h") == timedelta(hours=1)
        assert analytics_engine._parse_time_window("24h") == timedelta(hours=24)
        assert analytics_engine._parse_time_window("7d") == timedelta(days=7)
        assert analytics_engine._parse_time_window("2w") == timedelta(weeks=2)
        assert analytics_engine._parse_time_window("invalid") == timedelta(
            hours=24
        )  # Default

    def test_trend_score_calculation(self, analytics_engine):
        """Test trend score calculation algorithm"""

        activity_data = {"total_activity": 100, "teams": ["team1", "team2", "team3"]}

        growth_rate = 0.5
        window_delta = timedelta(hours=24)

        trend_score = analytics_engine._calculate_trend_score(
            activity_data, growth_rate, window_delta
        )

        # Verify score calculation
        assert 0.0 <= trend_score <= 1.0
        assert trend_score > growth_rate  # Should be boosted by activity and diversity

    @pytest.mark.asyncio
    async def test_team_recommendations_generation(
        self, analytics_engine, team_context
    ):
        """Test actionable team recommendations generation"""

        # Mock data for recommendations
        knowledge_coverage = {
            "backend": 0.8,
            "frontend": 0.3,  # Low coverage
            "security": 0.2,  # Very low coverage
        }

        collaboration_patterns = {
            "external_collaboration_score": 0.2  # Low collaboration
        }

        trending_topics = [
            TrendingTopic(
                topic="kubernetes",
                trend_score=0.9,
                growth_rate=0.8,
                related_memories=[],
                teams_involved=[],
                time_window="24h",
                peak_timestamp=datetime.utcnow(),
            )
        ]

        knowledge_gaps = [
            KnowledgeGap(
                gap_id="gap_001",
                team_id=team_context.team_id,
                topic_area="docker_deployment",
                confidence=0.9,
                suggested_sources=[],
                urgency_score=0.8,
                related_queries=[],
                potential_experts=[],
            )
        ]

        productivity_metrics = {"knowledge_reuse_rate": 0.3}  # Low reuse

        recommendations = await analytics_engine._generate_team_recommendations(
            team_context=team_context,
            knowledge_coverage=knowledge_coverage,
            collaboration_patterns=collaboration_patterns,
            trending_topics=trending_topics,
            knowledge_gaps=knowledge_gaps,
            productivity_metrics=productivity_metrics,
        )

        # Verify recommendations
        assert len(recommendations) > 0
        assert len(recommendations) <= 5  # Should be limited to top 5

        # Should include recommendations for low coverage areas
        assert any("frontend" in rec or "security" in rec for rec in recommendations)

        # Should include collaboration recommendation
        assert any("collaboration" in rec for rec in recommendations)

        # Should include knowledge gap recommendation
        assert any("docker_deployment" in rec for rec in recommendations)

        # Should include knowledge reuse recommendation
        assert any("reuse" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_analytics_performance_targets(self, analytics_engine, team_context):
        """Test analytics engine meets performance targets"""

        # Test knowledge gap detection performance
        start_time = datetime.utcnow()

        with (
            patch.object(
                analytics_engine, "_analyze_team_knowledge_coverage", return_value={}
            ),
            patch.object(analytics_engine, "_analyze_query_patterns", return_value=[]),
            patch.object(
                analytics_engine, "_compare_with_knowledge_standards", return_value=[]
            ),
            patch.object(
                analytics_engine, "_analyze_collaboration_gaps", return_value=[]
            ),
        ):

            await analytics_engine.detect_knowledge_gaps(
                team_context=team_context,
                analysis_window=timedelta(days=30),
                confidence_threshold=0.7,
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Should complete within reasonable time
        assert processing_time < 1.0  # Target: <1 second for gap detection

    @pytest.mark.asyncio
    async def test_analytics_error_handling(self, analytics_engine, team_context):
        """Test analytics handles errors gracefully"""

        # Mock an exception during analysis
        with patch.object(
            analytics_engine,
            "_analyze_team_knowledge_coverage",
            side_effect=Exception("Analysis error"),
        ):

            insights = await analytics_engine.generate_team_insights(
                team_id=team_context.team_id, analysis_period=timedelta(days=30)
            )

            # Should return error insights instead of crashing
            assert isinstance(insights, TeamInsights)
            assert insights.team_id == team_context.team_id
            assert len(insights.recommendations) > 0
            assert "Error generating insights" in insights.recommendations[0]

    @pytest.mark.asyncio
    async def test_knowledge_coverage_analysis(self, analytics_engine, team_context):
        """Test team knowledge coverage analysis"""

        analysis_window = timedelta(days=30)

        with patch.object(
            analytics_engine, "_calculate_domain_coverage"
        ) as mock_coverage:
            # Mock coverage scores for different domains
            mock_coverage.side_effect = [0.8, 0.6, 0.4, 0.7, 0.5, 0.3, 0.9]

            coverage = await analytics_engine._analyze_team_knowledge_coverage(
                team_context, analysis_window
            )

            # Verify coverage analysis
            assert len(coverage) > 0

            # Should include team specializations
            for specialization in team_context.specializations:
                assert specialization in coverage

            # Should include general areas
            general_areas = ["technical", "process", "business", "communication"]
            for area in general_areas:
                assert area in coverage

            # All scores should be between 0 and 1
            for score in coverage.values():
                assert 0.0 <= score <= 1.0
