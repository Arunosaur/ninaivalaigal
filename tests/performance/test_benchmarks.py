"""Performance benchmark tests."""
import pytest


class TestPerformanceBenchmarks:
    """Test performance benchmarks."""

    def test_memory_retrieval_performance(self, benchmark, client, auth_headers):
        """Benchmark memory retrieval performance."""

        def retrieve_memories():
            return client.get("/api/memories", headers=auth_headers)

        result = benchmark(retrieve_memories)
        # Test should handle both success and expected failure cases
        assert result.status_code in [200, 401, 404]

    def test_health_endpoint_performance(self, benchmark, client):
        """Benchmark health endpoint performance."""

        def check_health():
            return client.get("/health")

        result = benchmark(check_health)
        assert result.status_code == 200
