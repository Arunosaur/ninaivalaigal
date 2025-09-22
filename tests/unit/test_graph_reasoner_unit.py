"""
Unit tests for SPEC-061 Graph Reasoner

Tests the GraphReasoner class functionality with mocked dependencies.
Validates reasoning paths, context explanations, relevance inference, and feedback loops.
"""

import pytest
import json
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from server.graph.graph_reasoner import (
    GraphReasoner, 
    ReasoningPath, 
    ContextExplanation, 
    RelevanceInference,
    create_graph_reasoner
)


@pytest.fixture
def mock_age_client():
    """Mock Apache AGE client"""
    client = AsyncMock()
    client.execute_cypher = AsyncMock()
    client.get_memory_network = AsyncMock()
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)  # No cache by default
    client.setex = AsyncMock()
    client.keys = AsyncMock(return_value=[])
    client.delete = AsyncMock()
    return client


@pytest.fixture
def graph_reasoner(mock_age_client, mock_redis_client):
    """Create GraphReasoner instance with mocked dependencies"""
    return GraphReasoner(mock_age_client, mock_redis_client)


class TestGraphReasonerCreation:
    """Test GraphReasoner creation and initialization"""
    
    def test_create_graph_reasoner_factory(self, mock_age_client, mock_redis_client):
        """Test factory function creates GraphReasoner correctly"""
        reasoner = create_graph_reasoner(mock_age_client, mock_redis_client)
        
        assert isinstance(reasoner, GraphReasoner)
        assert reasoner.age_client == mock_age_client
        assert reasoner.redis_client == mock_redis_client
        assert reasoner.cache_ttl == 300
    
    def test_graph_reasoner_initialization(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test GraphReasoner initializes with correct dependencies"""
        assert graph_reasoner.age_client == mock_age_client
        assert graph_reasoner.redis_client == mock_redis_client
        assert graph_reasoner.cache_ttl == 300


class TestReasoningPath:
    """Test ReasoningPath dataclass"""
    
    def test_reasoning_path_creation(self):
        """Test ReasoningPath creation with default values"""
        path = ReasoningPath()
        
        assert path.nodes == []
        assert path.edges == []
        assert path.weights == []
        assert path.total_weight == 0.0
        assert path.confidence == 0.0
        assert path.reasoning == ""
    
    def test_reasoning_path_with_data(self):
        """Test ReasoningPath creation with actual data"""
        path = ReasoningPath(
            nodes=['user1', 'memory1'],
            edges=['CREATED'],
            weights=[0.9],
            total_weight=0.9,
            confidence=0.8,
            reasoning="Direct creation relationship"
        )
        
        assert path.nodes == ['user1', 'memory1']
        assert path.edges == ['CREATED']
        assert path.weights == [0.9]
        assert path.total_weight == 0.9
        assert path.confidence == 0.8
        assert path.reasoning == "Direct creation relationship"


class TestContextExplanation:
    """Test ContextExplanation dataclass"""
    
    def test_context_explanation_creation(self):
        """Test ContextExplanation creation with default values"""
        explanation = ContextExplanation(
            memory_id="mem_001",
            retrieval_reason="Test reason"
        )
        
        assert explanation.memory_id == "mem_001"
        assert explanation.retrieval_reason == "Test reason"
        assert explanation.paths == []
        assert explanation.relevance_score == 0.0
        assert explanation.confidence == 0.0
        assert explanation.supporting_evidence == []
    
    def test_context_explanation_with_paths(self):
        """Test ContextExplanation with reasoning paths"""
        path = ReasoningPath(
            nodes=['user1', 'memory1'],
            edges=['CREATED'],
            confidence=0.8
        )
        
        explanation = ContextExplanation(
            memory_id="mem_001",
            retrieval_reason="Direct creation",
            paths=[path],
            relevance_score=0.9,
            confidence=0.8,
            supporting_evidence=["Strong creation relationship"]
        )
        
        assert len(explanation.paths) == 1
        assert explanation.paths[0] == path
        assert explanation.relevance_score == 0.9
        assert explanation.confidence == 0.8
        assert "Strong creation relationship" in explanation.supporting_evidence


class TestRelevanceInference:
    """Test RelevanceInference dataclass"""
    
    def test_relevance_inference_creation(self):
        """Test RelevanceInference creation with default values"""
        inference = RelevanceInference()
        
        assert inference.suggested_memories == []
        assert inference.suggested_agents == []
        assert inference.reasoning_scores == {}
        assert inference.proximity_metrics == {}
        assert inference.confidence == 0.0
    
    def test_relevance_inference_with_suggestions(self):
        """Test RelevanceInference with actual suggestions"""
        inference = RelevanceInference(
            suggested_memories=['mem_002', 'mem_003'],
            suggested_agents=['agent_001'],
            reasoning_scores={'mem_002': 0.8, 'mem_003': 0.7, 'agent_001': 0.6},
            proximity_metrics={'mem_002': 0.9, 'mem_003': 0.8},
            confidence=0.75
        )
        
        assert inference.suggested_memories == ['mem_002', 'mem_003']
        assert inference.suggested_agents == ['agent_001']
        assert inference.reasoning_scores['mem_002'] == 0.8
        assert inference.proximity_metrics['mem_002'] == 0.9
        assert inference.confidence == 0.75


class TestExplainContext:
    """Test explain_context functionality"""
    
    @pytest.mark.asyncio
    async def test_explain_context_cache_hit(self, graph_reasoner, mock_redis_client):
        """Test explain_context returns cached result when available"""
        # Setup cache hit
        cached_data = {
            "memory_id": "mem_001",
            "retrieval_reason": "Cached reason",
            "paths": [],
            "relevance_score": 0.8,
            "confidence": 0.7,
            "supporting_evidence": ["Cached evidence"]
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await graph_reasoner.explain_context("mem_001", "user_001")
        
        assert isinstance(result, ContextExplanation)
        assert result.memory_id == "mem_001"
        assert result.retrieval_reason == "Cached reason"
        assert result.relevance_score == 0.8
        assert result.confidence == 0.7
        
        # Verify cache was checked
        mock_redis_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_explain_context_cache_miss(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test explain_context computes result when cache miss"""
        # Setup cache miss
        mock_redis_client.get.return_value = None
        
        # Mock Cypher query results
        mock_age_client.execute_cypher.side_effect = [
            # Reasoning paths query
            [
                {
                    'path': {
                        'nodes': [{'id': 'user_001'}, {'id': 'mem_001'}],
                        'relationships': [{'type': 'CREATED'}]
                    },
                    'weights': [0.9],
                    'depth': 1
                }
            ],
            # Supporting evidence query
            [
                {
                    'related.id': 'macro_001',
                    'timestamp': '2024-09-21T20:00:00Z',
                    'rel_type': 'LINKED_TO'
                }
            ]
        ]
        
        result = await graph_reasoner.explain_context("mem_001", "user_001")
        
        assert isinstance(result, ContextExplanation)
        assert result.memory_id == "mem_001"
        assert len(result.paths) == 1
        assert result.paths[0].nodes == ['user_001', 'mem_001']
        assert result.paths[0].edges == ['CREATED']
        
        # Verify result was cached
        mock_redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_explain_context_with_max_depth(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test explain_context respects max_depth parameter"""
        mock_redis_client.get.return_value = None
        mock_age_client.execute_cypher.return_value = []
        
        await graph_reasoner.explain_context("mem_001", "user_001", max_depth=5)
        
        # Verify Cypher query included correct max depth
        call_args = mock_age_client.execute_cypher.call_args_list[0][0][0]
        assert "*1..5" in call_args
    
    @pytest.mark.asyncio
    async def test_explain_context_different_context_types(self, graph_reasoner, mock_redis_client):
        """Test explain_context handles different context types"""
        mock_redis_client.get.return_value = None
        
        # Test different context types
        context_types = ["retrieval", "suggestion", "inference"]
        
        for context_type in context_types:
            await graph_reasoner.explain_context("mem_001", "user_001", context_type=context_type)
            
            # Verify cache key includes context type
            cache_key = mock_redis_client.get.call_args[0][0]
            assert context_type in cache_key


class TestInferRelevance:
    """Test infer_relevance functionality"""
    
    @pytest.mark.asyncio
    async def test_infer_relevance_cache_hit(self, graph_reasoner, mock_redis_client):
        """Test infer_relevance returns cached result when available"""
        # Setup cache hit
        cached_data = {
            "suggested_memories": ["mem_002", "mem_003"],
            "suggested_agents": ["agent_001"],
            "reasoning_scores": {"mem_002": 0.8, "mem_003": 0.7},
            "proximity_metrics": {"mem_002": 0.9},
            "confidence": 0.75
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await graph_reasoner.infer_relevance("mem_001", "user_001")
        
        assert isinstance(result, RelevanceInference)
        assert result.suggested_memories == ["mem_002", "mem_003"]
        assert result.suggested_agents == ["agent_001"]
        assert result.confidence == 0.75
    
    @pytest.mark.asyncio
    async def test_infer_relevance_cache_miss(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test infer_relevance computes result when cache miss"""
        mock_redis_client.get.return_value = None
        
        # Mock Cypher query results
        mock_age_client.execute_cypher.side_effect = [
            # Connected memories query
            [
                {"memory_id": "mem_002", "distance": 1},
                {"memory_id": "mem_003", "distance": 2}
            ],
            # Relevant agents query
            [
                {"agent_id": "agent_001"},
                {"agent_id": "agent_002"}
            ],
            # Proximity metrics queries (one per target)
            [{"distance": 1}],  # mem_002
            [{"distance": 2}],  # mem_003
            [{"distance": 1}],  # agent_001
            [{"distance": 3}],  # agent_002
            # Memory scoring queries
            [{"base_score": 0.8, "connection_count": 5, "created_at": "2024-09-21"}],  # mem_002
            [{"base_score": 0.7, "connection_count": 3, "created_at": "2024-09-20"}],  # mem_003
            # Agent scoring queries
            [{"activity_count": 10, "capabilities": "memory_management"}],  # agent_001
            [{"activity_count": 5, "capabilities": "automation"}]  # agent_002
        ]
        
        result = await graph_reasoner.infer_relevance("mem_001", "user_001")
        
        assert isinstance(result, RelevanceInference)
        assert len(result.suggested_memories) > 0
        assert len(result.suggested_agents) > 0
        assert result.confidence > 0
        
        # Verify result was cached
        mock_redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_infer_relevance_suggestion_count(self, graph_reasoner, mock_redis_client):
        """Test infer_relevance respects suggestion_count parameter"""
        mock_redis_client.get.return_value = None
        
        await graph_reasoner.infer_relevance("mem_001", "user_001", suggestion_count=10)
        
        # Verify cache key includes suggestion count
        cache_key = mock_redis_client.get.call_args[0][0]
        assert ":10" in cache_key


class TestFeedbackLoop:
    """Test feedback_loop functionality"""
    
    @pytest.mark.asyncio
    async def test_feedback_loop_stores_feedback(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test feedback_loop stores feedback in graph"""
        mock_age_client.execute_cypher.side_effect = [
            # Store feedback edge
            [{"r": {"type": "relevance", "score": 0.8}}],
            # Update graph weights
            [{"updated_edges": 3}]
        ]
        
        result = await graph_reasoner.feedback_loop(
            "user_001", "mem_001", "relevance", 0.8, {"context": "test"}
        )
        
        assert result["feedback_stored"] is True
        assert result["weight_updates"]["updated_edges"] == 3
        assert "traversal_updates" in result
        assert "cache_invalidations" in result
        
        # Verify feedback was stored
        store_call = mock_age_client.execute_cypher.call_args_list[0][0][0]
        assert "MERGE (u)-[r:FEEDBACK]->(m)" in store_call
        assert "relevance" in store_call
        assert "0.8" in store_call
    
    @pytest.mark.asyncio
    async def test_feedback_loop_updates_traversal_preferences(self, graph_reasoner, mock_redis_client):
        """Test feedback_loop updates user traversal preferences"""
        # Mock existing preferences
        existing_prefs = {
            "depth_preference": 2.0,
            "weight_threshold": 0.5,
            "relevance_boost": 1.0
        }
        mock_redis_client.get.return_value = json.dumps(existing_prefs)
        
        await graph_reasoner.feedback_loop("user_001", "mem_001", "relevance", 0.9)
        
        # Verify preferences were updated and stored
        setex_calls = [call for call in mock_redis_client.setex.call_args_list 
                      if "traversal_prefs" in call[0][0]]
        assert len(setex_calls) > 0
        
        # Check that relevance_boost was increased for high score
        stored_prefs = json.loads(setex_calls[0][0][2])
        assert stored_prefs["relevance_boost"] > 1.0
    
    @pytest.mark.asyncio
    async def test_feedback_loop_invalidates_caches(self, graph_reasoner, mock_redis_client):
        """Test feedback_loop invalidates related caches"""
        mock_redis_client.keys.side_effect = [
            ["context_explanation:mem_001:user_001:retrieval:3"],
            ["relevance_inference:mem_001:user_001:5"],
            ["network_analysis:user_001:comprehensive"]
        ]
        
        await graph_reasoner.feedback_loop("user_001", "mem_001", "relevance", 0.8)
        
        # Verify cache patterns were checked
        assert mock_redis_client.keys.call_count == 3
        
        # Verify caches were deleted
        assert mock_redis_client.delete.call_count == 3


class TestAnalyzeMemoryNetwork:
    """Test analyze_memory_network functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_memory_network_cache_hit(self, graph_reasoner, mock_redis_client):
        """Test analyze_memory_network returns cached result when available"""
        cached_data = {
            "user_id": "user_001",
            "analysis_type": "comprehensive",
            "network_structure": {"node_count": 10, "edge_count": 15},
            "patterns": {"hubs": []},
            "insights": ["Test insight"],
            "timestamp": "2024-09-21T20:00:00Z"
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await graph_reasoner.analyze_memory_network("user_001")
        
        assert result["user_id"] == "user_001"
        assert result["analysis_type"] == "comprehensive"
        assert result["network_structure"]["node_count"] == 10
        assert "Test insight" in result["insights"]
    
    @pytest.mark.asyncio
    async def test_analyze_memory_network_cache_miss(self, graph_reasoner, mock_age_client, mock_redis_client):
        """Test analyze_memory_network computes result when cache miss"""
        mock_redis_client.get.return_value = None
        
        # Mock network data
        network_data = {
            "nodes": [
                {"id": "user_001", "label": "User"},
                {"id": "mem_001", "label": "Memory"},
                {"id": "mem_002", "label": "Memory"}
            ],
            "edges": [
                {"source": "user_001", "target": "mem_001", "type": "CREATED"},
                {"source": "user_001", "target": "mem_002", "type": "CREATED"},
                {"source": "mem_001", "target": "mem_002", "type": "LINKED_TO"}
            ]
        }
        mock_age_client.get_memory_network.return_value = network_data
        
        result = await graph_reasoner.analyze_memory_network("user_001")
        
        assert result["user_id"] == "user_001"
        assert result["analysis_type"] == "comprehensive"
        assert "network_structure" in result
        assert "patterns" in result
        assert "insights" in result
        assert "timestamp" in result
        
        # Verify network structure analysis
        structure = result["network_structure"]
        assert structure["node_count"] == 3
        assert structure["edge_count"] == 3
        assert structure["density"] > 0
        
        # Verify result was cached with longer TTL
        mock_redis_client.setex.assert_called_once()
        cache_call = mock_redis_client.setex.call_args
        assert cache_call[0][1] == 600  # 2 * cache_ttl


class TestHelperMethods:
    """Test private helper methods"""
    
    def test_select_primary_path_empty_list(self, graph_reasoner):
        """Test _select_primary_path with empty list"""
        result = graph_reasoner._select_primary_path([])
        assert result is None
    
    def test_select_primary_path_single_path(self, graph_reasoner):
        """Test _select_primary_path with single path"""
        path = ReasoningPath(total_weight=0.8, confidence=0.9)
        result = graph_reasoner._select_primary_path([path])
        assert result == path
    
    def test_select_primary_path_multiple_paths(self, graph_reasoner):
        """Test _select_primary_path selects highest scoring path"""
        path1 = ReasoningPath(total_weight=0.6, confidence=0.8)  # Score: 0.48
        path2 = ReasoningPath(total_weight=0.9, confidence=0.7)  # Score: 0.63
        path3 = ReasoningPath(total_weight=0.7, confidence=0.9)  # Score: 0.63
        
        result = graph_reasoner._select_primary_path([path1, path2, path3])
        # Should return path2 or path3 (both have same score, max returns first)
        assert result in [path2, path3]
    
    def test_generate_retrieval_reason_no_path(self, graph_reasoner):
        """Test _generate_retrieval_reason with no path"""
        result = graph_reasoner._generate_retrieval_reason(None, "test_context")
        assert result == "Memory retrieved through test_context context"
    
    def test_generate_retrieval_reason_direct_relationship(self, graph_reasoner):
        """Test _generate_retrieval_reason with direct relationship"""
        path = ReasoningPath(nodes=['user1', 'mem1'], edges=['CREATED'])
        result = graph_reasoner._generate_retrieval_reason(path, "retrieval")
        assert result == "Direct CREATED relationship"
    
    def test_generate_retrieval_reason_two_hop(self, graph_reasoner):
        """Test _generate_retrieval_reason with two-hop connection"""
        path = ReasoningPath(
            nodes=['user1', 'macro1', 'mem1'], 
            edges=['CREATED', 'LINKED_TO']
        )
        result = graph_reasoner._generate_retrieval_reason(path, "retrieval")
        assert result == "Connected via CREATED → LINKED_TO"
    
    def test_generate_retrieval_reason_multi_hop(self, graph_reasoner):
        """Test _generate_retrieval_reason with multi-hop connection"""
        path = ReasoningPath(
            nodes=['user1', 'macro1', 'agent1', 'mem1'], 
            edges=['CREATED', 'TRIGGERED_BY', 'LINKED_TO']
        )
        result = graph_reasoner._generate_retrieval_reason(path, "retrieval")
        assert result == "Multi-hop connection through 3 relationships"
    
    def test_calculate_explanation_confidence_empty_paths(self, graph_reasoner):
        """Test _calculate_explanation_confidence with empty paths"""
        result = graph_reasoner._calculate_explanation_confidence([])
        assert result == 0.0
    
    def test_calculate_explanation_confidence_single_path(self, graph_reasoner):
        """Test _calculate_explanation_confidence with single path"""
        path = ReasoningPath(confidence=0.8)
        result = graph_reasoner._calculate_explanation_confidence([path])
        assert result == 0.8
    
    def test_calculate_explanation_confidence_multiple_strong_paths(self, graph_reasoner):
        """Test _calculate_explanation_confidence with multiple strong paths"""
        paths = [
            ReasoningPath(confidence=0.8),
            ReasoningPath(confidence=0.9),
            ReasoningPath(confidence=0.7)  # Not strong enough for boost
        ]
        result = graph_reasoner._calculate_explanation_confidence(paths)
        
        # Average: (0.8 + 0.9 + 0.7) / 3 = 0.8
        # Strong paths: 2 (>0.7), boost: 2 * 0.1 = 0.2
        # Final: min(0.8 + 0.2, 1.0) = 1.0
        assert result == 1.0
    
    def test_select_top_suggestions_empty_scores(self, graph_reasoner):
        """Test _select_top_suggestions with empty scores"""
        result = graph_reasoner._select_top_suggestions({}, 5)
        assert result == []
    
    def test_select_top_suggestions_normal_case(self, graph_reasoner):
        """Test _select_top_suggestions with normal scores"""
        scores = {
            "item1": 0.9,
            "item2": 0.7,
            "item3": 0.8,
            "item4": 0.6
        }
        result = graph_reasoner._select_top_suggestions(scores, 3)
        
        assert result == ["item1", "item3", "item2"]  # Sorted by score descending
        assert len(result) == 3
    
    def test_calculate_inference_confidence_empty_scores(self, graph_reasoner):
        """Test _calculate_inference_confidence with empty scores"""
        result = graph_reasoner._calculate_inference_confidence({}, {})
        assert result == 0.0
    
    def test_calculate_inference_confidence_good_suggestions(self, graph_reasoner):
        """Test _calculate_inference_confidence with good suggestions"""
        memory_scores = {"mem1": 0.8, "mem2": 0.7, "mem3": 0.6}
        agent_scores = {"agent1": 0.9}
        
        result = graph_reasoner._calculate_inference_confidence(memory_scores, agent_scores)
        
        # Should have high confidence due to good scores and multiple suggestions
        assert result > 0.7
        assert result <= 1.0
    
    def test_generate_path_reasoning_direct_access(self, graph_reasoner):
        """Test _generate_path_reasoning with single node"""
        result = graph_reasoner._generate_path_reasoning(["node1"], [])
        assert result == "Direct access"
    
    def test_generate_path_reasoning_direct_connection(self, graph_reasoner):
        """Test _generate_path_reasoning with two nodes"""
        result = graph_reasoner._generate_path_reasoning(["node1", "node2"], ["CREATED"])
        assert result == "Direct CREATED connection"
    
    def test_generate_path_reasoning_multi_hop(self, graph_reasoner):
        """Test _generate_path_reasoning with multiple hops"""
        result = graph_reasoner._generate_path_reasoning(
            ["node1", "node2", "node3"], 
            ["CREATED", "LINKED_TO"]
        )
        assert result == "Path through CREATED → LINKED_TO"


class TestPerformanceAndCaching:
    """Test performance and caching behavior"""
    
    @pytest.mark.asyncio
    async def test_cache_key_generation_consistency(self, graph_reasoner, mock_redis_client):
        """Test that cache keys are generated consistently"""
        mock_redis_client.get.return_value = None
        
        # Call same method twice with same parameters
        await graph_reasoner.explain_context("mem_001", "user_001")
        await graph_reasoner.explain_context("mem_001", "user_001")
        
        # Verify same cache key was used both times
        get_calls = mock_redis_client.get.call_args_list
        assert len(get_calls) == 2
        assert get_calls[0][0][0] == get_calls[1][0][0]
    
    @pytest.mark.asyncio
    async def test_cache_ttl_settings(self, graph_reasoner, mock_redis_client):
        """Test that cache TTL is set correctly for different operations"""
        mock_redis_client.get.return_value = None
        
        # Test explain_context caching
        await graph_reasoner.explain_context("mem_001", "user_001")
        setex_call = mock_redis_client.setex.call_args
        assert setex_call[0][1] == 300  # Standard cache_ttl
        
        mock_redis_client.reset_mock()
        
        # Test analyze_memory_network caching (should use longer TTL)
        await graph_reasoner.analyze_memory_network("user_001")
        setex_call = mock_redis_client.setex.call_args
        assert setex_call[0][1] == 600  # 2 * cache_ttl
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, graph_reasoner, mock_redis_client):
        """Test that concurrent operations work correctly"""
        mock_redis_client.get.return_value = None
        
        # Run multiple operations concurrently
        tasks = [
            graph_reasoner.explain_context("mem_001", "user_001"),
            graph_reasoner.infer_relevance("mem_002", "user_001"),
            graph_reasoner.analyze_memory_network("user_001")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed without exceptions
        for result in results:
            assert not isinstance(result, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
