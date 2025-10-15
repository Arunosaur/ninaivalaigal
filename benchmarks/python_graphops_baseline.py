# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Python GraphOps Performance Baseline
Measures current Python implementation for comparison with Rust
"""

import asyncio
import time
from typing import List

from server.graph.age_client import ApacheAGEClient, get_age_client


async def benchmark_simple_match(client: ApacheAGEClient, iterations: int = 100):
    """Benchmark simple MATCH query"""
    query = "MATCH (n) RETURN n LIMIT 10"

    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await client.execute_cypher(cypher_query=query)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    avg_time = sum(times) / len(times)
    p50 = sorted(times)[len(times) // 2]
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]

    print(f"Simple MATCH Query (n={iterations}):")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")

    return {"avg": avg_time, "p50": p50, "p95": p95, "p99": p99}


async def benchmark_graph_traversal(client: ApacheAGEClient, iterations: int = 50):
    """Benchmark graph traversal query"""
    query = "MATCH (a)-[r*1..3]->(b) RETURN {a: a, r: r, b: b} LIMIT 10"

    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await client.execute_cypher(cypher_query=query)
        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"\nGraph Traversal Query (n={iterations}):")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P95: {p95:.2f}ms")

    return {"avg": avg_time, "p95": p95}


async def main():
    print("=== Python GraphOps Baseline Benchmarks ===\n")
    client = await get_age_client(use_cache=False)
    await benchmark_simple_match(client)
    await benchmark_graph_traversal(client)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
