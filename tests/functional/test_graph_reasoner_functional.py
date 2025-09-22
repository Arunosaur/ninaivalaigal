"""
Functional tests for SPEC-061 Graph Reasoner with Apache AGE + Redis

Tests the GraphReasoner class with real Apache AGE and Redis connections.
Validates end-to-end functionality, performance, and integration behavior.
"""

import pytest
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from server.graph.graph_reasoner import GraphReasoner, create_graph_reasoner
from server.graph.age_client import ApacheAGEClient
from server.redis_client import RedisClient
from server.graph.models.node_models import (
    create_user_node,
    create_memory_node,
    MemoryType,
)
from server.graph.models.edge_models import create_created_edge, create_linked_to_edge


@pytest.fixture
async def redis_client():
    """Create Redis client for testing"""
    try:
        client = RedisClient()
        await client.initialize()
        yield client
        await client.close()
    except Exception:
        pytest.skip("Redis not available for functional testing")


@pytest.fixture
async def age_client():
    """Create Apache AGE client for testing"""
    try:
        client = ApacheAGEClient()
        await client.initialize()
        yield client
        await client.close()
    except Exception:
        pytest.skip("Apache AGE not available for functional testing")


@pytest.fixture
async def graph_reasoner(age_client, redis_client):
    """Create GraphReasoner with real dependencies"""
    return create_graph_reasoner(age_client, redis_client)


@pytest.fixture
async def test_graph_data(age_client):
    """Setup test graph data in Apache AGE"""
    # Create test nodes
    user_node = create_user_node(
        "test_user_001", "Test User", "test@medhasys.com", "developer"
    )
    memory_node1 = create_memory_node(
        "test_mem_001",
        "SPEC-061 Implementation",
        "Graph reasoner testing",
        MemoryType.ARCHITECTURE,
    )
    memory_node2 = create_memory_node(
        "test_mem_002",
        "Redis Integration",
        "Performance caching layer",
        MemoryType.CORE,
    )

    # Create nodes in graph
    await age_client.create_node(user_node)
    await age_client.create_node(memory_node1)
    await age_client.create_node(memory_node2)

    # Create test edges
    created_edge1 = create_created_edge(
        "test_user_001", "test_mem_001", confidence=0.95
    )
    created_edge2 = create_created_edge(
        "test_user_001", "test_mem_002", confidence=0.90
    )
    linked_edge = create_linked_to_edge(
        "test_mem_001", "test_mem_002", relevance="high", weight=0.85
    )

    await age_client.create_edge(created_edge1)
    await age_client.create_edge(created_edge2)
    await age_client.create_edge(linked_edge)

    yield {
        "user_id": "test_user_001",
        "memory_ids": ["test_mem_001", "test_mem_002"],
        "nodes": [user_node, memory_node1, memory_node2],
        "edges": [created_edge1, created_edge2, linked_edge],
    }

    # Cleanup test data
    cleanup_query = """
    MATCH (n) WHERE n.id STARTS WITH 'test_'
    DETACH DELETE n
    """
    await age_client.execute_cypher(cleanup_query)


class TestExplainContextFunctional:
    """Functional tests for explain_context with real graph data"""

    @pytest.mark.asyncio
    async def test_explain_context_direct_relationship(
        self, graph_reasoner, test_graph_data
    ):
        """Test explain_context finds direct user-memory relationship"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        explanation = await graph_reasoner.explain_context(memory_id, user_id)

        assert explanation.memory_id == memory_id
        assert len(explanation.paths) > 0
        assert explanation.relevance_score > 0
        assert explanation.confidence > 0

        # Should find direct CREATED relationship
        primary_path = explanation.paths[0]
        assert user_id in primary_path.nodes
        assert memory_id in primary_path.nodes
        assert "CREATED" in primary_path.edges

    @pytest.mark.asyncio
    async def test_explain_context_multi_hop_relationship(
        self, graph_reasoner, test_graph_data
    ):
        """Test explain_context finds multi-hop relationships"""
        user_id = test_graph_data["user_id"]
        memory_ids = test_graph_data["memory_ids"]

        # Test explanation from user to second memory (should find path through first memory)
        explanation = await graph_reasoner.explain_context(
            memory_ids[1], user_id, max_depth=3
        )

        assert explanation.memory_id == memory_ids[1]
        assert len(explanation.paths) > 0

        # Should find paths with different lengths
        path_lengths = [len(path.nodes) for path in explanation.paths]
        assert min(path_lengths) >= 2  # At least direct relationship

    @pytest.mark.asyncio
    async def test_explain_context_caching_behavior(
        self, graph_reasoner, test_graph_data, redis_client
    ):
        """Test that explain_context results are properly cached"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Clear any existing cache
        cache_pattern = f"context_explanation:{memory_id}:*"
        keys = await redis_client.keys(cache_pattern)
        if keys:
            await redis_client.delete(*keys)

        # First call should compute result
        start_time = datetime.now()
        explanation1 = await graph_reasoner.explain_context(memory_id, user_id)
        first_call_time = (datetime.now() - start_time).total_seconds()

        # Second call should use cache and be faster
        start_time = datetime.now()
        explanation2 = await graph_reasoner.explain_context(memory_id, user_id)
        second_call_time = (datetime.now() - start_time).total_seconds()

        # Results should be identical
        assert explanation1.memory_id == explanation2.memory_id
        assert explanation1.retrieval_reason == explanation2.retrieval_reason
        assert explanation1.relevance_score == explanation2.relevance_score

        # Second call should be significantly faster (cached)
        assert second_call_time < first_call_time * 0.5

    @pytest.mark.asyncio
    async def test_explain_context_different_context_types(
        self, graph_reasoner, test_graph_data
    ):
        """Test explain_context with different context types"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        context_types = ["retrieval", "suggestion", "inference"]
        explanations = {}

        for context_type in context_types:
            explanation = await graph_reasoner.explain_context(
                memory_id, user_id, context_type=context_type
            )
            explanations[context_type] = explanation

            assert explanation.memory_id == memory_id
            assert (
                context_type in explanation.retrieval_reason
                or "context" in explanation.retrieval_reason
            )

        # All explanations should have same basic structure but potentially different reasoning
        for explanation in explanations.values():
            assert len(explanation.paths) > 0
            assert explanation.relevance_score > 0


class TestInferRelevanceFunctional:
    """Functional tests for infer_relevance with real graph data"""

    @pytest.mark.asyncio
    async def test_infer_relevance_finds_connected_memories(
        self, graph_reasoner, test_graph_data
    ):
        """Test infer_relevance finds connected memories"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        inference = await graph_reasoner.infer_relevance(memory_id, user_id)

        assert isinstance(inference.suggested_memories, list)
        assert isinstance(inference.suggested_agents, list)
        assert isinstance(inference.reasoning_scores, dict)
        assert isinstance(inference.proximity_metrics, dict)
        assert 0 <= inference.confidence <= 1

        # Should find the connected memory
        connected_memory = test_graph_data["memory_ids"][1]
        if inference.suggested_memories:
            # If suggestions found, connected memory should be among them or have high proximity
            assert (
                connected_memory in inference.suggested_memories
                or inference.proximity_metrics.get(connected_memory, 0) > 0
            )

    @pytest.mark.asyncio
    async def test_infer_relevance_suggestion_count_limit(
        self, graph_reasoner, test_graph_data
    ):
        """Test infer_relevance respects suggestion count limit"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Test with different suggestion counts
        for count in [1, 3, 5]:
            inference = await graph_reasoner.infer_relevance(
                memory_id, user_id, suggestion_count=count
            )

            assert len(inference.suggested_memories) <= count
            assert len(inference.suggested_agents) <= min(
                count, 3
            )  # Agent limit is min(count, 3)

    @pytest.mark.asyncio
    async def test_infer_relevance_caching_behavior(
        self, graph_reasoner, test_graph_data, redis_client
    ):
        """Test that infer_relevance results are properly cached"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Clear any existing cache
        cache_pattern = f"relevance_inference:{memory_id}:*"
        keys = await redis_client.keys(cache_pattern)
        if keys:
            await redis_client.delete(*keys)

        # First call should compute result
        start_time = datetime.now()
        inference1 = await graph_reasoner.infer_relevance(memory_id, user_id)
        first_call_time = (datetime.now() - start_time).total_seconds()

        # Second call should use cache
        start_time = datetime.now()
        inference2 = await graph_reasoner.infer_relevance(memory_id, user_id)
        second_call_time = (datetime.now() - start_time).total_seconds()

        # Results should be identical
        assert inference1.suggested_memories == inference2.suggested_memories
        assert inference1.suggested_agents == inference2.suggested_agents
        assert inference1.confidence == inference2.confidence

        # Second call should be faster
        assert second_call_time < first_call_time * 0.5


class TestFeedbackLoopFunctional:
    """Functional tests for feedback_loop with real graph data"""

    @pytest.mark.asyncio
    async def test_feedback_loop_stores_feedback_edge(
        self, graph_reasoner, test_graph_data, age_client
    ):
        """Test feedback_loop creates feedback edge in graph"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Provide feedback
        result = await graph_reasoner.feedback_loop(
            user_id, memory_id, "relevance", 0.8, {"context": "test_feedback"}
        )

        assert result["feedback_stored"] is True
        assert "weight_updates" in result
        assert "traversal_updates" in result

        # Verify feedback edge was created
        feedback_query = f"""
        MATCH (u:User {{id: '{user_id}'}})-[r:FEEDBACK]->(m:Memory {{id: '{memory_id}'}})
        RETURN r.type as feedback_type, r.score as feedback_score
        """

        feedback_result = await age_client.execute_cypher(feedback_query)
        assert len(feedback_result) > 0
        assert feedback_result[0]["feedback_type"] == "relevance"
        assert feedback_result[0]["feedback_score"] == 0.8

    @pytest.mark.asyncio
    async def test_feedback_loop_updates_traversal_preferences(
        self, graph_reasoner, test_graph_data, redis_client
    ):
        """Test feedback_loop updates user traversal preferences in Redis"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Clear existing preferences
        prefs_key = f"traversal_prefs:{user_id}"
        await redis_client.delete(prefs_key)

        # Provide positive feedback
        await graph_reasoner.feedback_loop(user_id, memory_id, "relevance", 0.9)

        # Check that preferences were stored
        stored_prefs = await redis_client.get(prefs_key)
        assert stored_prefs is not None

        prefs = json.loads(stored_prefs)
        assert "depth_preference" in prefs
        assert "weight_threshold" in prefs
        assert "relevance_boost" in prefs

        # Relevance boost should be increased for high score
        assert prefs["relevance_boost"] > 1.0

    @pytest.mark.asyncio
    async def test_feedback_loop_invalidates_caches(
        self, graph_reasoner, test_graph_data, redis_client
    ):
        """Test feedback_loop invalidates related caches"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Create some cached data first
        await graph_reasoner.explain_context(memory_id, user_id)
        await graph_reasoner.infer_relevance(memory_id, user_id)
        await graph_reasoner.analyze_memory_network(user_id)

        # Verify caches exist
        cache_patterns = [
            f"context_explanation:{memory_id}:*",
            f"relevance_inference:{memory_id}:*",
            f"network_analysis:{user_id}:*",
        ]

        cache_keys_before = []
        for pattern in cache_patterns:
            keys = await redis_client.keys(pattern)
            cache_keys_before.extend(keys)

        assert len(cache_keys_before) > 0, "Should have cached data before feedback"

        # Provide feedback (should invalidate caches)
        await graph_reasoner.feedback_loop(user_id, memory_id, "relevance", 0.8)

        # Verify caches were invalidated
        cache_keys_after = []
        for pattern in cache_patterns:
            keys = await redis_client.keys(pattern)
            cache_keys_after.extend(keys)

        assert len(cache_keys_after) < len(
            cache_keys_before
        ), "Caches should be invalidated"


class TestAnalyzeMemoryNetworkFunctional:
    """Functional tests for analyze_memory_network with real graph data"""

    @pytest.mark.asyncio
    async def test_analyze_memory_network_comprehensive(
        self, graph_reasoner, test_graph_data
    ):
        """Test comprehensive memory network analysis"""
        user_id = test_graph_data["user_id"]

        analysis = await graph_reasoner.analyze_memory_network(user_id, "comprehensive")

        assert analysis["user_id"] == user_id
        assert analysis["analysis_type"] == "comprehensive"
        assert "network_structure" in analysis
        assert "patterns" in analysis
        assert "insights" in analysis
        assert "timestamp" in analysis

        # Verify network structure analysis
        structure = analysis["network_structure"]
        assert structure["node_count"] > 0
        assert structure["edge_count"] > 0
        assert "node_types" in structure
        assert "avg_connections" in structure

        # Verify patterns analysis
        patterns = analysis["patterns"]
        assert "hubs" in patterns
        assert "connection_distribution" in patterns

        # Verify insights are generated
        insights = analysis["insights"]
        assert isinstance(insights, list)
        assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_analyze_memory_network_caching(
        self, graph_reasoner, test_graph_data, redis_client
    ):
        """Test memory network analysis caching behavior"""
        user_id = test_graph_data["user_id"]

        # Clear any existing cache
        cache_pattern = f"network_analysis:{user_id}:*"
        keys = await redis_client.keys(cache_pattern)
        if keys:
            await redis_client.delete(*keys)

        # First call should compute result
        start_time = datetime.now()
        analysis1 = await graph_reasoner.analyze_memory_network(user_id)
        first_call_time = (datetime.now() - start_time).total_seconds()

        # Second call should use cache
        start_time = datetime.now()
        analysis2 = await graph_reasoner.analyze_memory_network(user_id)
        second_call_time = (datetime.now() - start_time).total_seconds()

        # Results should be identical
        assert analysis1["user_id"] == analysis2["user_id"]
        assert analysis1["network_structure"] == analysis2["network_structure"]
        assert analysis1["patterns"] == analysis2["patterns"]

        # Second call should be significantly faster
        assert second_call_time < first_call_time * 0.5

    @pytest.mark.asyncio
    async def test_analyze_memory_network_different_types(
        self, graph_reasoner, test_graph_data
    ):
        """Test memory network analysis with different analysis types"""
        user_id = test_graph_data["user_id"]

        analysis_types = ["comprehensive", "recent", "patterns"]

        for analysis_type in analysis_types:
            analysis = await graph_reasoner.analyze_memory_network(
                user_id, analysis_type
            )

            assert analysis["user_id"] == user_id
            assert analysis["analysis_type"] == analysis_type
            assert "network_structure" in analysis
            assert "patterns" in analysis
            assert "insights" in analysis


class TestIntegrationScenarios:
    """Test complete integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_reasoning_workflow(self, graph_reasoner, test_graph_data):
        """Test complete reasoning workflow: explain → infer → feedback → analyze"""
        user_id = test_graph_data["user_id"]
        memory_id = test_graph_data["memory_ids"][0]

        # Step 1: Explain context for memory retrieval
        explanation = await graph_reasoner.explain_context(memory_id, user_id)
        assert explanation.memory_id == memory_id
        assert len(explanation.paths) > 0

        # Step 2: Infer relevant memories and agents
        inference = await graph_reasoner.infer_relevance(memory_id, user_id)
        assert isinstance(inference.suggested_memories, list)
        assert isinstance(inference.suggested_agents, list)

        # Step 3: Provide feedback on the relevance
        feedback_result = await graph_reasoner.feedback_loop(
            user_id, memory_id, "relevance", 0.9, {"workflow": "complete_test"}
        )
        assert feedback_result["feedback_stored"] is True

        # Step 4: Analyze the updated memory network
        analysis = await graph_reasoner.analyze_memory_network(user_id)
        assert analysis["user_id"] == user_id
        assert len(analysis["insights"]) > 0

        # Verify the workflow created a coherent reasoning chain
        assert explanation.confidence > 0
        assert inference.confidence > 0
        assert len(analysis["network_structure"]) > 0

    @pytest.mark.asyncio
    async def test_performance_under_load(self, graph_reasoner, test_graph_data):
        """Test GraphReasoner performance under concurrent load"""
        user_id = test_graph_data["user_id"]
        memory_ids = test_graph_data["memory_ids"]

        # Create multiple concurrent operations
        tasks = []

        # Add explain_context tasks
        for memory_id in memory_ids:
            tasks.append(graph_reasoner.explain_context(memory_id, user_id))

        # Add infer_relevance tasks
        for memory_id in memory_ids:
            tasks.append(graph_reasoner.infer_relevance(memory_id, user_id))

        # Add feedback_loop tasks
        for i, memory_id in enumerate(memory_ids):
            tasks.append(
                graph_reasoner.feedback_loop(
                    user_id, memory_id, "relevance", 0.7 + i * 0.1
                )
            )

        # Add network analysis task
        tasks.append(graph_reasoner.analyze_memory_network(user_id))

        # Execute all tasks concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (datetime.now() - start_time).total_seconds()

        # Verify all operations completed successfully
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Task {i} failed: {result}"

        # Performance should be reasonable (less than 10 seconds for all operations)
        assert total_time < 10.0, f"Operations took too long: {total_time}s"

        # Verify results are of correct types
        explanation_results = [r for r in results if hasattr(r, "memory_id")]
        inference_results = [r for r in results if hasattr(r, "suggested_memories")]
        feedback_results = [
            r for r in results if isinstance(r, dict) and "feedback_stored" in r
        ]
        analysis_results = [
            r for r in results if isinstance(r, dict) and "network_structure" in r
        ]

        assert len(explanation_results) == len(memory_ids)
        assert len(inference_results) == len(memory_ids)
        assert len(feedback_results) == len(memory_ids)
        assert len(analysis_results) == 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, graph_reasoner, test_graph_data):
        """Test error handling and recovery scenarios"""
        user_id = test_graph_data["user_id"]

        # Test with non-existent memory ID
        try:
            explanation = await graph_reasoner.explain_context(
                "non_existent_memory", user_id
            )
            # Should not raise exception, but return explanation with low confidence
            assert explanation.memory_id == "non_existent_memory"
            assert explanation.confidence == 0.0 or len(explanation.paths) == 0
        except Exception as e:
            pytest.fail(f"Should handle non-existent memory gracefully: {e}")

        # Test with non-existent user ID
        try:
            inference = await graph_reasoner.infer_relevance(
                test_graph_data["memory_ids"][0], "non_existent_user"
            )
            # Should not raise exception, but return inference with low confidence
            assert inference.confidence >= 0.0
        except Exception as e:
            pytest.fail(f"Should handle non-existent user gracefully: {e}")

        # Test feedback with invalid scores
        try:
            result = await graph_reasoner.feedback_loop(
                user_id,
                test_graph_data["memory_ids"][0],
                "relevance",
                1.5,  # Invalid score > 1.0
            )
            # Should handle gracefully or normalize the score
            assert result["feedback_stored"] is True
        except Exception as e:
            pytest.fail(f"Should handle invalid feedback scores gracefully: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
