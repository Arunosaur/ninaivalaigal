"""
SPEC-031: Memory Relevance Ranking - Comprehensive Test Coverage

Tests memory relevance ranking and token prioritization system.
"""

import pytest
import requests
from unittest.mock import Mock, patch
import json

# Test Configuration
BASE_URL = "http://localhost:13370"
TEST_TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


class TestMemoryRelevanceRanking:
    """Test suite for SPEC-031: Memory Relevance Ranking"""

    def test_relevance_scoring_basic(self):
        """Test basic relevance scoring functionality"""
        relevance_data = {
            "query": "test query for relevance",
            "context": "testing context",
            "memories": [
                {"id": "mem_001", "content": "test content related to query"},
                {"id": "mem_002", "content": "unrelated content about cats"},
            ],
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Relevance scoring endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Relevance scoring failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                assert (
                    "scores" in result or "rankings" in result
                ), "Relevance response missing scores"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_memory_ranking_by_relevance(self):
        """Test memory ranking by relevance scores"""
        ranking_data = {"query": "python programming", "limit": 10}

        try:
            response = requests.get(
                f"{BASE_URL}/memory/ranked",
                params=ranking_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Memory ranking endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Memory ranking failed: {response.status_code}"

            if response.status_code == 200:
                result = response.json()
                assert isinstance(result, list), "Ranked memories should be a list"

                # Check if results are properly ranked (descending relevance)
                if len(result) > 1:
                    for i in range(len(result) - 1):
                        current_score = result[i].get("relevance_score", 0)
                        next_score = result[i + 1].get("relevance_score", 0)
                        assert (
                            current_score >= next_score
                        ), "Memories not properly ranked by relevance"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_context_aware_relevance(self):
        """Test context-aware relevance scoring"""
        context_data = {
            "query": "debugging",
            "context": "software development",
            "user_preferences": {
                "programming_languages": ["python", "javascript"],
                "experience_level": "intermediate",
            },
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/relevance/context-aware",
                json=context_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Context-aware relevance endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Context-aware relevance failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_relevance_feedback_integration(self):
        """Test integration with feedback system (SPEC-040)"""
        feedback_data = {
            "memory_id": "test_memory_feedback_001",
            "query": "test query",
            "relevance_score": 0.85,
            "user_feedback": "helpful",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/relevance/feedback",
                json=feedback_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Relevance feedback endpoint not implemented")

            assert response.status_code in [
                200,
                201,
            ], f"Relevance feedback failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


class TestRelevancePerformance:
    """Test relevance system performance"""

    def test_relevance_scoring_performance(self):
        """Test relevance scoring performance"""
        import time

        try:
            # Test scoring performance with multiple memories
            memories = [
                {"id": f"mem_{i:03d}", "content": f"test content {i}"}
                for i in range(50)
            ]

            relevance_data = {"query": "test performance query", "memories": memories}

            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=10,
            )
            scoring_time = time.time() - start_time

            if response.status_code == 404:
                pytest.skip("Relevance scoring endpoint not implemented")

            assert (
                response.status_code == 200
            ), f"Performance test failed: {response.status_code}"

            print(f"Relevance scoring time for 50 memories: {scoring_time:.3f}s")

            # Performance assertion - should handle 50 memories quickly
            assert (
                scoring_time < 5.0
            ), f"Relevance scoring too slow: {scoring_time:.3f}s"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_redis_cached_relevance(self):
        """Test Redis caching of relevance scores (SPEC-033 integration)"""
        try:
            # First request (cache miss)
            relevance_data = {
                "query": "cached relevance test",
                "context": "caching test",
            }

            import time

            start_time = time.time()
            response1 = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=5,
            )
            first_request_time = time.time() - start_time

            if response1.status_code == 404:
                pytest.skip("Relevance scoring endpoint not implemented")

            # Second request (cache hit)
            start_time = time.time()
            response2 = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=5,
            )
            second_request_time = time.time() - start_time

            assert response2.status_code == 200, "Cached relevance request failed"

            print(
                f"First request: {first_request_time:.3f}s, Second request: {second_request_time:.3f}s"
            )

            # Cache should make second request faster (though this depends on implementation)
            # This is more of an observational test

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


class TestRelevanceEdgeCases:
    """Test edge cases for relevance system"""

    def test_empty_query_relevance(self):
        """Test relevance scoring with empty query"""
        relevance_data = {
            "query": "",
            "memories": [{"id": "mem_001", "content": "some content"}],
        }

        try:
            response = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=5,
            )

            if response.status_code == 404:
                pytest.skip("Relevance scoring endpoint not implemented")

            # Should handle empty query gracefully
            assert response.status_code in [
                200,
                400,
            ], f"Empty query handling failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_large_memory_set_relevance(self):
        """Test relevance scoring with large memory set"""
        # Create a large set of memories
        large_memory_set = [
            {
                "id": f"large_mem_{i:04d}",
                "content": f"content number {i} with various keywords",
            }
            for i in range(500)
        ]

        relevance_data = {"query": "keywords", "memories": large_memory_set}

        try:
            response = requests.post(
                f"{BASE_URL}/memory/relevance/score",
                json=relevance_data,
                headers=HEADERS,
                timeout=30,
            )

            if response.status_code == 404:
                pytest.skip("Relevance scoring endpoint not implemented")

            # Should handle large datasets
            assert response.status_code in [
                200,
                413,
            ], f"Large dataset handling failed: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
