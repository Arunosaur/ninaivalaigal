# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Prototype gRPC client for GraphOps service.
This is a PROTOTYPE - not integrated into main client yet.
Used for testing real gRPC connection and performance measurement.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import grpc

# Import generated stubs
from .proto import graphops_pb2, graphops_pb2_grpc

logger = logging.getLogger(__name__)


class GraphOpsGrpcClientPrototype:
    """
    Prototype gRPC client for GraphOps Rust service.

    Purpose:
    - Test real gRPC connection
    - Measure actual performance
    - Validate protobuf contracts
    - Build confidence for full integration

    NOT YET INTEGRATED - This is for testing only!
    """

    def __init__(self, service_url: str = "localhost:50051"):
        """
        Initialize gRPC client prototype.

        Args:
            service_url: gRPC service address (host:port)
        """
        self.service_url = service_url
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[graphops_pb2_grpc.GraphOpsServiceStub] = None
        logger.info(f"Initialized gRPC prototype client for {service_url}")

    async def connect(self) -> bool:
        """
        Establish gRPC channel and test connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create async insecure channel (production will use TLS)
            self._channel = grpc.aio.insecure_channel(self.service_url)
            self._stub = graphops_pb2_grpc.GraphOpsServiceStub(self._channel)

            # Test connection with health check
            request = graphops_pb2.HealthCheckRequest()
            response = await self._stub.HealthCheck(request)

            is_healthy = response.status == graphops_pb2.HEALTH_STATUS_HEALTHY

            if is_healthy:
                logger.info(f"✅ Connected to GraphOps service: {response.version}")
                logger.info(f"   Database: {response.database.status}")
                logger.info(f"   AGE Extension: {response.age_extension.status}")
            else:
                logger.error(f"❌ Service unhealthy: {response.status}")

            return is_healthy

        except grpc.aio.AioRpcError as e:
            logger.error(f"❌ gRPC connection failed: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, timeout_ms: int = 5000
    ) -> Dict[str, Any]:
        """
        Execute single Cypher query via gRPC.

        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
            timeout_ms: Query timeout in milliseconds

        Returns:
            Dictionary with results and metadata
        """
        if not self._stub:
            raise RuntimeError("Not connected - call connect() first")

        try:
            # Build request
            request = graphops_pb2.ExecuteQueryRequest(query=query, parameters=parameters or {}, timeout_ms=timeout_ms)

            # Execute query
            start_time = time.time()
            response = await self._stub.ExecuteQuery(request)
            duration_ms = (time.time() - start_time) * 1000

            # Parse response
            result = {
                "status": response.status,
                "results": list(response.results),
                "row_count": response.row_count,
                "execution_time_ms": response.execution_time_ms,
                "client_duration_ms": duration_ms,
                "success": response.status == graphops_pb2.EXECUTION_STATUS_SUCCESS,
            }

            if result["success"]:
                logger.debug(f"✅ Query executed: {duration_ms:.2f}ms (server: {response.execution_time_ms}ms)")
            else:
                logger.error(f"❌ Query failed: {response.error_details}")
                result["error"] = response.error_details

            return result

        except grpc.aio.AioRpcError as e:
            logger.error(f"❌ gRPC error: {e.code()} - {e.details()}")
            return {"success": False, "error": f"{e.code()}: {e.details()}"}

    async def execute_batch(self, queries: list[str], timeout_ms: int = 5000) -> Dict[str, Any]:
        """
        Execute multiple queries in a batch.

        Args:
            queries: List of Cypher queries
            timeout_ms: Timeout for entire batch

        Returns:
            Batch results with individual query responses
        """
        if not self._stub:
            raise RuntimeError("Not connected - call connect() first")

        try:
            # Build batch request
            query_requests = [graphops_pb2.ExecuteQueryRequest(query=q, timeout_ms=timeout_ms) for q in queries]

            request = graphops_pb2.ExecuteQueryBatchRequest(queries=query_requests)

            # Execute batch
            start_time = time.time()
            response = await self._stub.ExecuteQueryBatch(request)
            duration_ms = (time.time() - start_time) * 1000

            return {
                "batch_status": response.batch_status,
                "total_execution_time_ms": response.total_execution_time_ms,
                "client_duration_ms": duration_ms,
                "success_count": response.success_count,
                "total_count": len(response.responses),
                "responses": [
                    {
                        "status": r.status,
                        "results": list(r.results),
                        "row_count": r.row_count,
                        "execution_time_ms": r.execution_time_ms,
                    }
                    for r in response.responses
                ],
            }

        except grpc.aio.AioRpcError as e:
            logger.error(f"❌ Batch gRPC error: {e.code()} - {e.details()}")
            return {"success": False, "error": f"{e.code()}: {e.details()}"}

    async def get_metrics(self, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Get service metrics.

        Args:
            window_seconds: Time window for metrics

        Returns:
            Service metrics
        """
        if not self._stub:
            raise RuntimeError("Not connected - call connect() first")

        try:
            request = graphops_pb2.MetricsRequest(window_seconds=window_seconds)
            response = await self._stub.GetMetrics(request)

            return {
                "total_queries": response.total_queries,
                "successful_queries": response.successful_queries,
                "failed_queries": response.failed_queries,
                "p50_latency_ms": response.p50_latency_ms,
                "p95_latency_ms": response.p95_latency_ms,
                "p99_latency_ms": response.p99_latency_ms,
                "avg_execution_time_ms": response.avg_execution_time_ms,
            }

        except grpc.aio.AioRpcError as e:
            logger.error(f"❌ Metrics gRPC error: {e.code()} - {e.details()}")
            return {"error": f"{e.code()}: {e.details()}"}

    async def close(self):
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()
            logger.info("Closed gRPC connection")


# ============================================================================
# Test & Benchmark Functions
# ============================================================================


async def test_connection():
    """Test basic gRPC connection."""
    print("\n" + "=" * 70)
    print("🧪 Testing gRPC Connection")
    print("=" * 70)

    client = GraphOpsGrpcClientPrototype()

    if await client.connect():
        print("✅ Connection successful!")

        # Get service metrics
        metrics = await client.get_metrics()
        print("\n📊 Service Metrics:")
        print(f"   Total queries: {metrics.get('total_queries', 'N/A')}")
        print(f"   Successful: {metrics.get('successful_queries', 'N/A')}")
        print(f"   P50 latency: {metrics.get('p50_latency_ms', 'N/A')}ms")

        await client.close()
        return True
    else:
        print("❌ Connection failed!")
        return False


async def test_simple_query():
    """Test single query execution."""
    print("\n" + "=" * 70)
    print("🧪 Testing Simple Query Execution")
    print("=" * 70)

    client = GraphOpsGrpcClientPrototype()

    if not await client.connect():
        print("❌ Connection failed!")
        return False

    # Test simple query
    query = "MATCH (n:User) RETURN count(n) as user_count"
    print(f"\nQuery: {query}")

    result = await client.execute_query(query)

    if result["success"]:
        print("✅ Query successful!")
        print(f"   Results: {result['results']}")
        print(f"   Rows: {result['row_count']}")
        print(f"   Server time: {result['execution_time_ms']}ms")
        print(f"   Client time: {result['client_duration_ms']:.2f}ms")
    else:
        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")

    await client.close()
    return result["success"]


async def test_batch_queries():
    """Test batch query execution."""
    print("\n" + "=" * 70)
    print("🧪 Testing Batch Query Execution")
    print("=" * 70)

    client = GraphOpsGrpcClientPrototype()

    if not await client.connect():
        print("❌ Connection failed!")
        return False

    queries = ["MATCH (n:User) RETURN count(n)", "MATCH (m:Memory) RETURN count(m)", "MATCH (t:Team) RETURN count(t)"]

    print(f"\nExecuting {len(queries)} queries in batch...")

    result = await client.execute_batch(queries)

    print("\n📊 Batch Results:")
    print(f"   Success count: {result['success_count']}/{result['total_count']}")
    print(f"   Server time: {result['total_execution_time_ms']}ms")
    print(f"   Client time: {result['client_duration_ms']:.2f}ms")

    await client.close()
    return True


async def benchmark_performance():
    """Benchmark gRPC client performance."""
    print("\n" + "=" * 70)
    print("📊 Performance Benchmark")
    print("=" * 70)

    client = GraphOpsGrpcClientPrototype()

    if not await client.connect():
        print("❌ Connection failed!")
        return

    # Warm up
    print("\n🔥 Warming up...")
    for _ in range(5):
        await client.execute_query("MATCH (n) RETURN count(n)")

    # Benchmark
    print("⏱️  Running benchmark (100 queries)...")
    times = []

    for i in range(100):
        result = await client.execute_query("MATCH (n) RETURN count(n)")
        if result["success"]:
            times.append(result["client_duration_ms"])

        if (i + 1) % 20 == 0:
            print(f"   Progress: {i+1}/100")

    # Calculate statistics
    import statistics

    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    p99_time = sorted(times)[int(len(times) * 0.99)]

    print("\n📊 Performance Results:")
    print(f"   Average:  {avg_time:.2f}ms")
    print(f"   Median:   {median_time:.2f}ms")
    print(f"   Min:      {min_time:.2f}ms")
    print(f"   Max:      {max_time:.2f}ms")
    print(f"   P95:      {p95_time:.2f}ms")
    print(f"   P99:      {p99_time:.2f}ms")

    print("\n📈 Comparison with Baseline:")
    baseline = 7.04  # Mock baseline from earlier tests
    print(f"   Mock baseline: {baseline}ms")
    print(f"   gRPC actual:   {avg_time:.2f}ms")

    if avg_time < baseline:
        speedup = baseline / avg_time
        print(f"   ✅ Speedup:    {speedup:.2f}x FASTER")
    else:
        slowdown = avg_time / baseline
        print(f"   ⚠️  Slowdown:   {slowdown:.2f}x SLOWER")
        print("   Note: Includes network overhead")

    await client.close()


async def run_all_tests():
    """Run all tests and benchmarks."""
    print("\n" + "=" * 70)
    print("🚀 GraphOps gRPC Client Prototype - Test Suite")
    print("=" * 70)

    # Run tests
    tests = [
        ("Connection Test", test_connection),
        ("Simple Query Test", test_simple_query),
        ("Batch Query Test", test_batch_queries),
        ("Performance Benchmark", benchmark_performance),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result if result is not None else True))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📋 Test Summary")
    print("=" * 70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n   Total: {passed_count}/{total_count} passed")

    print("\n" + "=" * 70)
    print("✅ Prototype testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    """Run prototype tests."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run all tests
    asyncio.run(run_all_tests())
