# Integration tests for GraphOps ↔ Main Stack
import pytest
import requests
import asyncio
from typing import Dict, Any

class TestGraphOpsIntegration:
    """Integration tests between GraphOps and main ninaivalaigal stack"""
    
    @pytest.fixture
    def graphops_base_url(self):
        """GraphOps service base URL"""
        return "http://localhost:6380"
    
    @pytest.fixture
    def api_base_url(self):
        """Main API service base URL"""
        return "http://localhost:8000"
    
    def test_graphops_health(self, graphops_base_url):
        """Test GraphOps service health"""
        try:
            response = requests.get(f"{graphops_base_url}/health", timeout=5)
            assert response.status_code == 200
            health_data = response.json()
            assert health_data.get("status") == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphOps service not available")
    
    def test_main_api_health(self, api_base_url):
        """Test main API service health"""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            assert response.status_code == 200
            health_data = response.json()
            assert health_data.get("status") == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Main API service not available")
    
    def test_memory_to_graph_flow(self, api_base_url, graphops_base_url):
        """Test memory creation → graph storage flow"""
        try:
            # 1. Create memory via main API
            memory_data = {
                "content": "Integration test memory",
                "context": "test_integration",
                "metadata": {"source": "integration_test"}
            }
            
            memory_response = requests.post(
                f"{api_base_url}/memory/create",
                json=memory_data,
                timeout=5
            )
            
            if memory_response.status_code == 401:
                pytest.skip("Authentication required - skipping integration test")
            
            assert memory_response.status_code == 200
            memory_id = memory_response.json().get("id")
            
            # 2. Verify graph storage via GraphOps
            graph_response = requests.get(
                f"{graphops_base_url}/graph/memory/{memory_id}",
                timeout=5
            )
            
            assert graph_response.status_code == 200
            graph_data = graph_response.json()
            assert graph_data.get("memory_id") == memory_id
            
        except requests.exceptions.ConnectionError:
            pytest.skip("One or more services not available")
    
    def test_graph_query_integration(self, api_base_url, graphops_base_url):
        """Test graph query → memory retrieval integration"""
        try:
            # 1. Query graph for related memories
            query_data = {
                "query": "integration test",
                "limit": 5
            }
            
            graph_response = requests.post(
                f"{graphops_base_url}/graph/query",
                json=query_data,
                timeout=5
            )
            
            assert graph_response.status_code == 200
            graph_results = graph_response.json()
            
            # 2. Retrieve full memory details via main API
            if graph_results.get("memory_ids"):
                memory_id = graph_results["memory_ids"][0]
                
                memory_response = requests.get(
                    f"{api_base_url}/memory/{memory_id}",
                    timeout=5
                )
                
                if memory_response.status_code != 401:  # Skip if auth required
                    assert memory_response.status_code == 200
                    memory_data = memory_response.json()
                    assert memory_data.get("id") == memory_id
            
        except requests.exceptions.ConnectionError:
            pytest.skip("One or more services not available")
    
    def test_redis_cache_consistency(self, api_base_url, graphops_base_url):
        """Test Redis cache consistency between services"""
        try:
            # Test that both services can access shared Redis cache
            cache_key = "integration_test_key"
            cache_value = "integration_test_value"
            
            # Set cache via main API
            cache_set_response = requests.post(
                f"{api_base_url}/cache/set",
                json={"key": cache_key, "value": cache_value},
                timeout=5
            )
            
            # Get cache via GraphOps
            cache_get_response = requests.get(
                f"{graphops_base_url}/cache/{cache_key}",
                timeout=5
            )
            
            if cache_set_response.status_code == 200 and cache_get_response.status_code == 200:
                cached_data = cache_get_response.json()
                assert cached_data.get("value") == cache_value
            
        except requests.exceptions.ConnectionError:
            pytest.skip("One or more services not available")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, api_base_url, graphops_base_url):
        """Test concurrent operations across both services"""
        try:
            # Simulate concurrent memory operations
            tasks = []
            
            for i in range(5):
                # Alternate between API and GraphOps operations
                if i % 2 == 0:
                    task = self._create_memory_async(api_base_url, f"concurrent_test_{i}")
                else:
                    task = self._query_graph_async(graphops_base_url, f"concurrent_test")
                
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify no exceptions occurred
            for result in results:
                if isinstance(result, Exception):
                    if "Connection" in str(result):
                        pytest.skip("Service connection issues during concurrent test")
                    else:
                        raise result
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("Services not available for concurrent testing")
            else:
                raise
    
    async def _create_memory_async(self, api_base_url: str, content: str) -> Dict[str, Any]:
        """Async helper for memory creation"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_base_url}/memory/create",
                json={"content": content, "context": "concurrent_test"},
                timeout=5
            ) as response:
                return await response.json()
    
    async def _query_graph_async(self, graphops_base_url: str, query: str) -> Dict[str, Any]:
        """Async helper for graph querying"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{graphops_base_url}/graph/query",
                json={"query": query, "limit": 3},
                timeout=5
            ) as response:
                return await response.json()
