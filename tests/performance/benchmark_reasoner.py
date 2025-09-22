"""
Performance benchmarks for SPEC-061 Graph Reasoner

Benchmarks the GraphReasoner class performance with pytest-benchmark.
Validates SLO compliance and performance regression detection.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from server.graph.graph_reasoner import create_graph_reasoner


@pytest.fixture
def mock_age_client():
    """Mock Apache AGE client with realistic response times"""
    client = AsyncMock()

    # Mock typical Cypher query responses
    client.execute_cypher.return_value = [
        {
            "path": {
                "nodes": [{"id": "user_001"}, {"id": "mem_001"}],
                "relationships": [{"type": "CREATED"}],
            },
            "weights": [0.9],
            "depth": 1,
        }
    ]

    client.get_memory_network.return_value = {
        "nodes": [
            {"id": "user_001", "label": "User"},
            {"id": "mem_001", "label": "Memory"},
            {"id": "mem_002", "label": "Memory"},
        ],
        "edges": [
            {"source": "user_001", "target": "mem_001", "type": "CREATED"},
            {"source": "user_001", "target": "mem_002", "type": "CREATED"},
        ],
    }

    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client with realistic response times"""
    client = AsyncMock()
    client.get.return_value = None  # No cache by default
    client.setex.return_value = True
    client.keys.return_value = []
    client.delete.return_value = 1
    return client


@pytest.fixture
def graph_reasoner(mock_age_client, mock_redis_client):
    """Create GraphReasoner with mocked dependencies"""
    return create_graph_reasoner(mock_age_client, mock_redis_client)


class TestExplainContextPerformance:
    """Performance benchmarks for explain_context"""

    @pytest.mark.benchmark(group="explain_context")
    def test_explain_context_performance_cold_cache(self, benchmark, graph_reasoner):
        """Benchmark explain_context with cold cache (no Redis cache hit)"""

        async def explain_context_cold():
            return await graph_reasoner.explain_context("mem_001", "user_001")

        def run_explain_context():
            return asyncio.run(explain_context_cold())

        result = benchmark(run_explain_context)

        # Validate result structure
        assert result.memory_id == "mem_001"
        assert len(result.paths) > 0
        assert result.confidence >= 0.0

    @pytest.mark.benchmark(group="explain_context")
    def test_explain_context_performance_warm_cache(
        self, benchmark, graph_reasoner, mock_redis_client
    ):
        """Benchmark explain_context with warm cache (Redis cache hit)"""
        # Setup cache hit
        cached_data = {
            "memory_id": "mem_001",
            "retrieval_reason": "Cached reason",
            "paths": [],
            "relevance_score": 0.8,
            "confidence": 0.7,
            "supporting_evidence": ["Cached evidence"],
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)

        async def explain_context_warm():
            return await graph_reasoner.explain_context("mem_001", "user_001")

        def run_explain_context():
            return asyncio.run(explain_context_warm())

        result = benchmark(run_explain_context)

        # Validate cached result
        assert result.memory_id == "mem_001"
        assert result.retrieval_reason == "Cached reason"

    @pytest.mark.benchmark(group="explain_context")
    def test_explain_context_performance_deep_traversal(
        self, benchmark, graph_reasoner
    ):
        """Benchmark explain_context with deep graph traversal"""

        async def explain_context_deep():
            return await graph_reasoner.explain_context(
                "mem_001", "user_001", max_depth=5
            )

        def run_explain_context():
            return asyncio.run(explain_context_deep())

        result = benchmark(run_explain_context)

        # Should handle deep traversal efficiently
        assert result.memory_id == "mem_001"

    @pytest.mark.benchmark(group="explain_context", min_rounds=10)
    def test_explain_context_performance_bulk_operations(
        self, benchmark, graph_reasoner
    ):
        """Benchmark explain_context with multiple concurrent operations"""

        async def explain_context_bulk():
            tasks = []
            for i in range(10):
                tasks.append(graph_reasoner.explain_context(f"mem_{i:03d}", "user_001"))

            results = await asyncio.gather(*tasks)
            return results

        def run_explain_context_bulk():
            return asyncio.run(explain_context_bulk())

        results = benchmark(run_explain_context_bulk)

        # Validate bulk results
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.memory_id == f"mem_{i:03d}"


class TestInferRelevancePerformance:
    """Performance benchmarks for infer_relevance"""

    @pytest.mark.benchmark(group="infer_relevance")
    def test_infer_relevance_performance_cold_cache(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark infer_relevance with cold cache"""
        # Setup multiple query responses for connected memories and agents
        mock_age_client.execute_cypher.side_effect = [
            # Connected memories
            [{"memory_id": f"mem_{i:03d}", "distance": i + 1} for i in range(5)],
            # Relevant agents
            [{"agent_id": f"agent_{i:03d}"} for i in range(3)],
            # Proximity metrics (one per target)
            *[[{"distance": i + 1}] for i in range(8)],
            # Memory scoring
            *[[{"base_score": 0.8, "connection_count": 5}] for _ in range(5)],
            # Agent scoring
            *[[{"activity_count": 10, "capabilities": "test"}] for _ in range(3)],
        ]

        async def infer_relevance_cold():
            return await graph_reasoner.infer_relevance("mem_001", "user_001")

        def run_infer_relevance():
            return asyncio.run(infer_relevance_cold())

        result = benchmark(run_infer_relevance)

        # Validate result structure
        assert isinstance(result.suggested_memories, list)
        assert isinstance(result.suggested_agents, list)
        assert 0 <= result.confidence <= 1

    @pytest.mark.benchmark(group="infer_relevance")
    def test_infer_relevance_performance_warm_cache(
        self, benchmark, graph_reasoner, mock_redis_client
    ):
        """Benchmark infer_relevance with warm cache"""
        # Setup cache hit
        cached_data = {
            "suggested_memories": ["mem_002", "mem_003"],
            "suggested_agents": ["agent_001"],
            "reasoning_scores": {"mem_002": 0.8, "mem_003": 0.7},
            "proximity_metrics": {"mem_002": 0.9},
            "confidence": 0.75,
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)

        async def infer_relevance_warm():
            return await graph_reasoner.infer_relevance("mem_001", "user_001")

        def run_infer_relevance():
            return asyncio.run(infer_relevance_warm())

        result = benchmark(run_infer_relevance)

        # Validate cached result
        assert result.suggested_memories == ["mem_002", "mem_003"]
        assert result.confidence == 0.75

    @pytest.mark.benchmark(group="infer_relevance")
    def test_infer_relevance_performance_large_suggestion_count(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark infer_relevance with large suggestion count"""
        # Setup responses for many connected items
        mock_age_client.execute_cypher.side_effect = [
            # Connected memories (20 items)
            [{"memory_id": f"mem_{i:03d}", "distance": i + 1} for i in range(20)],
            # Relevant agents (10 items)
            [{"agent_id": f"agent_{i:03d}"} for i in range(10)],
            # Proximity metrics
            *[[{"distance": i + 1}] for i in range(30)],
            # Memory scoring
            *[[{"base_score": 0.8, "connection_count": 5}] for _ in range(20)],
            # Agent scoring
            *[[{"activity_count": 10, "capabilities": "test"}] for _ in range(10)],
        ]

        async def infer_relevance_large():
            return await graph_reasoner.infer_relevance(
                "mem_001", "user_001", suggestion_count=15
            )

        def run_infer_relevance():
            return asyncio.run(infer_relevance_large())

        result = benchmark(run_infer_relevance)

        # Should handle large suggestion counts efficiently
        assert len(result.suggested_memories) <= 15
        assert len(result.suggested_agents) <= 3  # Agent limit


class TestFeedbackLoopPerformance:
    """Performance benchmarks for feedback_loop"""

    @pytest.mark.benchmark(group="feedback_loop")
    def test_feedback_loop_performance_single_feedback(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark single feedback_loop operation"""
        # Setup query responses
        mock_age_client.execute_cypher.side_effect = [
            [{"r": {"type": "relevance", "score": 0.8}}],  # Store feedback
            [{"updated_edges": 3}],  # Update weights
        ]

        async def feedback_loop_single():
            return await graph_reasoner.feedback_loop(
                "user_001", "mem_001", "relevance", 0.8, {"context": "benchmark"}
            )

        def run_feedback_loop():
            return asyncio.run(feedback_loop_single())

        result = benchmark(run_feedback_loop)

        # Validate result
        assert result["feedback_stored"] is True
        assert "weight_updates" in result

    @pytest.mark.benchmark(group="feedback_loop", min_rounds=5)
    def test_feedback_loop_performance_batch_feedback(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark batch feedback_loop operations"""
        # Setup query responses for multiple feedbacks
        mock_age_client.execute_cypher.side_effect = [
            [{"r": {"type": "relevance", "score": 0.8}}],
            [{"updated_edges": 3}],
        ] * 5  # 5 feedback operations

        async def feedback_loop_batch():
            tasks = []
            for i in range(5):
                tasks.append(
                    graph_reasoner.feedback_loop(
                        "user_001", f"mem_{i:03d}", "relevance", 0.7 + i * 0.05
                    )
                )

            results = await asyncio.gather(*tasks)
            return results

        def run_feedback_loop_batch():
            return asyncio.run(feedback_loop_batch())

        results = benchmark(run_feedback_loop_batch)

        # Validate batch results
        assert len(results) == 5
        for result in results:
            assert result["feedback_stored"] is True


class TestAnalyzeMemoryNetworkPerformance:
    """Performance benchmarks for analyze_memory_network"""

    @pytest.mark.benchmark(group="analyze_network")
    def test_analyze_network_performance_small_network(self, benchmark, graph_reasoner):
        """Benchmark network analysis with small network"""

        async def analyze_network_small():
            return await graph_reasoner.analyze_memory_network(
                "user_001", "comprehensive"
            )

        def run_analyze_network():
            return asyncio.run(analyze_network_small())

        result = benchmark(run_analyze_network)

        # Validate analysis result
        assert result["user_id"] == "user_001"
        assert "network_structure" in result
        assert "patterns" in result
        assert "insights" in result

    @pytest.mark.benchmark(group="analyze_network")
    def test_analyze_network_performance_large_network(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark network analysis with large network"""
        # Setup large network data
        large_network = {
            "nodes": [{"id": f"node_{i:03d}", "label": "Memory"} for i in range(100)],
            "edges": [
                {
                    "source": f"node_{i:03d}",
                    "target": f"node_{(i + 1) % 100:03d}",
                    "type": "LINKED_TO",
                }
                for i in range(100)
            ],
        }
        mock_age_client.get_memory_network.return_value = large_network

        async def analyze_network_large():
            return await graph_reasoner.analyze_memory_network(
                "user_001", "comprehensive"
            )

        def run_analyze_network():
            return asyncio.run(analyze_network_large())

        result = benchmark(run_analyze_network)

        # Should handle large networks efficiently
        assert result["network_structure"]["node_count"] == 100
        assert result["network_structure"]["edge_count"] == 100

    @pytest.mark.benchmark(group="analyze_network")
    def test_analyze_network_performance_cached(
        self, benchmark, graph_reasoner, mock_redis_client
    ):
        """Benchmark network analysis with cache hit"""
        # Setup cache hit
        cached_analysis = {
            "user_id": "user_001",
            "analysis_type": "comprehensive",
            "network_structure": {"node_count": 10, "edge_count": 15},
            "patterns": {"hubs": []},
            "insights": ["Cached insight"],
            "timestamp": datetime.now().isoformat(),
        }
        mock_redis_client.get.return_value = json.dumps(cached_analysis)

        async def analyze_network_cached():
            return await graph_reasoner.analyze_memory_network(
                "user_001", "comprehensive"
            )

        def run_analyze_network():
            return asyncio.run(analyze_network_cached())

        result = benchmark(run_analyze_network)

        # Validate cached result
        assert result["user_id"] == "user_001"
        assert result["network_structure"]["node_count"] == 10


class TestConcurrentOperationsPerformance:
    """Performance benchmarks for concurrent operations"""

    @pytest.mark.benchmark(group="concurrent", min_rounds=3)
    def test_concurrent_mixed_operations_performance(
        self, benchmark, graph_reasoner, mock_age_client, mock_redis_client
    ):
        """Benchmark mixed concurrent operations"""
        # Setup responses for all operation types
        mock_age_client.execute_cypher.side_effect = [
            # explain_context responses
            [
                {
                    "path": {
                        "nodes": [{"id": "user_001"}, {"id": "mem_001"}],
                        "relationships": [{"type": "CREATED"}],
                    },
                    "weights": [0.9],
                    "depth": 1,
                }
            ],
            [
                {
                    "related.id": "macro_001",
                    "timestamp": "2024-09-21T20:00:00Z",
                    "rel_type": "LINKED_TO",
                }
            ],
            # infer_relevance responses
            [{"memory_id": "mem_002", "distance": 1}],
            [{"agent_id": "agent_001"}],
            [{"distance": 1}],
            [{"distance": 2}],  # proximity
            [{"base_score": 0.8, "connection_count": 5}],  # memory scoring
            [{"activity_count": 10, "capabilities": "test"}],  # agent scoring
            # feedback_loop responses
            [{"r": {"type": "relevance", "score": 0.8}}],
            [{"updated_edges": 3}],
        ]

        # No cache hits for this benchmark
        mock_redis_client.get.return_value = None

        async def concurrent_mixed_operations():
            tasks = [
                # Explanation tasks
                graph_reasoner.explain_context("mem_001", "user_001"),
                # Inference tasks
                graph_reasoner.infer_relevance("mem_001", "user_001"),
                # Feedback tasks
                graph_reasoner.feedback_loop("user_001", "mem_001", "relevance", 0.8),
                # Analysis tasks
                graph_reasoner.analyze_memory_network("user_001"),
            ]

            results = await asyncio.gather(*tasks)
            return results

        def run_concurrent_operations():
            return asyncio.run(concurrent_mixed_operations())

        results = benchmark(run_concurrent_operations)

        # Validate all operations completed
        assert len(results) == 4

        # Validate result types
        explanation_result = results[0]
        inference_result = results[1]
        feedback_result = results[2]
        analysis_result = results[3]

        assert hasattr(explanation_result, "memory_id")
        assert hasattr(inference_result, "suggested_memories")
        assert feedback_result["feedback_stored"] is True
        assert analysis_result["user_id"] == "user_001"

    @pytest.mark.benchmark(group="concurrent")
    def test_high_concurrency_performance(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark high concurrency scenario"""
        # Setup responses for many operations
        mock_age_client.execute_cypher.side_effect = [
            [
                {
                    "path": {
                        "nodes": [{"id": "user_001"}, {"id": f"mem_{i:03d}"}],
                        "relationships": [{"type": "CREATED"}],
                    },
                    "weights": [0.9],
                    "depth": 1,
                }
            ]
            for i in range(20)
        ] + [
            [
                {
                    "related.id": "macro_001",
                    "timestamp": "2024-09-21T20:00:00Z",
                    "rel_type": "LINKED_TO",
                }
            ]
            for _ in range(20)
        ]

        async def high_concurrency_operations():
            tasks = []

            # Create 20 concurrent explain_context operations
            for i in range(20):
                tasks.append(graph_reasoner.explain_context(f"mem_{i:03d}", "user_001"))

            results = await asyncio.gather(*tasks)
            return results

        def run_high_concurrency():
            return asyncio.run(high_concurrency_operations())

        results = benchmark(run_high_concurrency())

        # Validate high concurrency results
        assert len(results) == 20
        for i, result in enumerate(results):
            assert result.memory_id == f"mem_{i:03d}"


class TestMemoryAndResourceUsage:
    """Benchmarks for memory and resource usage"""

    @pytest.mark.benchmark(group="memory_usage")
    def test_memory_usage_large_dataset(
        self, benchmark, graph_reasoner, mock_age_client
    ):
        """Benchmark memory usage with large dataset"""
        # Setup large dataset responses
        large_memories = [
            {"memory_id": f"mem_{i:05d}", "distance": i + 1} for i in range(1000)
        ]
        large_agents = [{"agent_id": f"agent_{i:03d}"} for i in range(100)]

        mock_age_client.execute_cypher.side_effect = [
            large_memories,  # Connected memories
            large_agents,  # Relevant agents
            # Proximity metrics
            *[[{"distance": i + 1}] for i in range(1100)],
            # Memory scoring
            *[[{"base_score": 0.8, "connection_count": 5}] for _ in range(1000)],
            # Agent scoring
            *[[{"activity_count": 10, "capabilities": "test"}] for _ in range(100)],
        ]

        async def large_dataset_operation():
            return await graph_reasoner.infer_relevance(
                "mem_001", "user_001", suggestion_count=50
            )

        def run_large_dataset():
            return asyncio.run(large_dataset_operation())

        result = benchmark(run_large_dataset)

        # Should handle large datasets efficiently
        assert len(result.suggested_memories) <= 50
        assert len(result.reasoning_scores) > 0

    @pytest.mark.benchmark(group="cache_performance")
    def test_cache_hit_ratio_performance(
        self, benchmark, graph_reasoner, mock_redis_client
    ):
        """Benchmark cache hit ratio and performance"""
        # Setup alternating cache hits and misses
        cache_responses = [None, "cached_data", None, "cached_data"] * 5
        mock_redis_client.get.side_effect = cache_responses

        async def cache_hit_ratio_test():
            results = []
            for i in range(20):
                if i % 2 == 1:  # Cache hit
                    mock_redis_client.get.return_value = json.dumps(
                        {
                            "memory_id": f"mem_{i:03d}",
                            "retrieval_reason": "Cached",
                            "paths": [],
                            "relevance_score": 0.8,
                            "confidence": 0.7,
                            "supporting_evidence": [],
                        }
                    )
                else:  # Cache miss
                    mock_redis_client.get.return_value = None

                result = await graph_reasoner.explain_context(
                    f"mem_{i:03d}", "user_001"
                )
                results.append(result)

            return results

        def run_cache_test():
            return asyncio.run(cache_hit_ratio_test())

        results = benchmark(run_cache_test)

        # Validate cache behavior
        assert len(results) == 20
        for i, result in enumerate(results):
            assert result.memory_id == f"mem_{i:03d}"


# Performance SLO validation
class TestPerformanceSLOs:
    """Validate Service Level Objectives (SLOs) for performance"""

    def test_explain_context_slo_compliance(self, graph_reasoner):
        """Validate explain_context meets SLO requirements"""

        async def slo_test():
            start_time = datetime.now()
            result = await graph_reasoner.explain_context("mem_001", "user_001")
            end_time = datetime.now()

            duration_ms = (end_time - start_time).total_seconds() * 1000
            return duration_ms, result

        duration_ms, result = asyncio.run(slo_test())

        # SLO: explain_context should complete within 100ms for cold cache
        assert (
            duration_ms < 100
        ), f"explain_context took {duration_ms}ms, exceeds 100ms SLO"
        assert result.memory_id == "mem_001"

    def test_infer_relevance_slo_compliance(self, graph_reasoner, mock_age_client):
        """Validate infer_relevance meets SLO requirements"""
        # Setup minimal responses for fast execution
        mock_age_client.execute_cypher.side_effect = [
            [{"memory_id": "mem_002", "distance": 1}],  # Connected memories
            [{"agent_id": "agent_001"}],  # Relevant agents
            [{"distance": 1}],
            [{"distance": 1}],  # Proximity
            [{"base_score": 0.8, "connection_count": 5}],  # Memory scoring
            [{"activity_count": 10, "capabilities": "test"}],  # Agent scoring
        ]

        async def slo_test():
            start_time = datetime.now()
            result = await graph_reasoner.infer_relevance("mem_001", "user_001")
            end_time = datetime.now()

            duration_ms = (end_time - start_time).total_seconds() * 1000
            return duration_ms, result

        duration_ms, result = asyncio.run(slo_test())

        # SLO: infer_relevance should complete within 150ms for cold cache
        assert (
            duration_ms < 150
        ), f"infer_relevance took {duration_ms}ms, exceeds 150ms SLO"
        assert isinstance(result.suggested_memories, list)

    def test_feedback_loop_slo_compliance(self, graph_reasoner, mock_age_client):
        """Validate feedback_loop meets SLO requirements"""
        mock_age_client.execute_cypher.side_effect = [
            [{"r": {"type": "relevance", "score": 0.8}}],
            [{"updated_edges": 3}],
        ]

        async def slo_test():
            start_time = datetime.now()
            result = await graph_reasoner.feedback_loop(
                "user_001", "mem_001", "relevance", 0.8
            )
            end_time = datetime.now()

            duration_ms = (end_time - start_time).total_seconds() * 1000
            return duration_ms, result

        duration_ms, result = asyncio.run(slo_test())

        # SLO: feedback_loop should complete within 50ms
        assert duration_ms < 50, f"feedback_loop took {duration_ms}ms, exceeds 50ms SLO"
        assert result["feedback_stored"] is True


if __name__ == "__main__":
    pytest.main([__file__, "--benchmark-only", "-v"])
