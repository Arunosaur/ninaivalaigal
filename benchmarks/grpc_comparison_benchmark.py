# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

# gRPC Client Comparison Benchmark

import asyncio
import time
from typing import List

from python_clients.graphops.graphops_client.client import GraphOpsClient as MockClient

from server.graph.age_client import get_age_client


async def benchmark_client(client, query: str, iterations: int) -> List[float]:
    """Benchmark a client with a given query."""
    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        if isinstance(client, MockClient):
            await client.execute_query(request=query)
        else:
            await client.execute_cypher(cypher_query=query)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    return times


def print_results(client_name: str, times: List[float]):
    """Print benchmark results."""
    avg_time = sum(times) / len(times)
    p50 = sorted(times)[len(times) // 2]
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]

    print(f"\n--- {client_name} ---")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")


async def main():
    """Run the benchmark comparison."""
    print("=== gRPC Client Benchmark Comparison ===")

    # Queries to test
    simple_query = "MATCH (n) RETURN n LIMIT 10"
    traversal_query = "MATCH (a)-[r*1..3]->(b) RETURN {a: a, r: r, b: b} LIMIT 10"

    # Initialize clients
    mock_client = MockClient()
    real_client = await get_age_client(use_cache=False)

    # Run benchmarks
    print("\n--- Simple Query ---")
    mock_times = await benchmark_client(mock_client, simple_query, 100)
    real_times = await benchmark_client(real_client, simple_query, 100)
    print_results("Mock Client", mock_times)
    print_results("Real gRPC Client", real_times)

    print("\n--- Traversal Query ---")
    mock_times = await benchmark_client(mock_client, traversal_query, 50)
    real_times = await benchmark_client(real_client, traversal_query, 50)
    print_results("Mock Client", mock_times)
    print_results("Real gRPC Client", real_times)

    await real_client.close()


if __name__ == "__main__":
    asyncio.run(main())
