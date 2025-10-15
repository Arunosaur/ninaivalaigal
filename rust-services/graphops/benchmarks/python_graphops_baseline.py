# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Baseline GraphOps performance probe in Python.

This script mirrors the Cypher queries executed by the Rust benchmark so we can
collect apples-to-apples latency metrics.
"""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path
from typing import Callable, List

import psycopg2

# Load .env file if present (from project root)
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use existing env vars

DATABASE_URL = os.getenv("DATABASE_URL")
GRAPH_NAME = os.getenv("GRAPHOPS_GRAPH", "graph")
ITERATIONS = int(os.getenv("GRAPHOPS_PY_ITERATIONS", "10"))


def run_query(cursor, query: str) -> List[str]:
    # AGE requires graph name and query as literals (not parameters)
    sql = f"SELECT * FROM cypher('{GRAPH_NAME}', $${query}$$) AS (result agtype);"
    cursor.execute(sql)
    rows = cursor.fetchall()

    parsed: List[str] = []
    for (raw,) in rows:
        fragment = raw.split("::", 1)[0]
        parsed.append(fragment)
    return parsed


def measure(label: str, func: Callable[[], None]) -> None:
    timings: List[float] = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        func()
        timings.append(time.perf_counter() - start)

    print(f"{label}: min={min(timings):.6f}s median={statistics.median(timings):.6f}s max={max(timings):.6f}s")


def main() -> None:
    if not DATABASE_URL:
        print("DATABASE_URL not set – skipping Python baseline.")
        return

    with psycopg2.connect(DATABASE_URL) as conn:
        # Initialize Apache AGE extension
        with conn.cursor() as init_cursor:
            init_cursor.execute("LOAD 'age';")
            init_cursor.execute('SET search_path = ag_catalog, "$user", public;')
        conn.commit()

        # Reuse cursor across measurements (mirrors Rust connection reuse)
        cursor = conn.cursor()

        # Warmup phase (300 iterations to match Rust)
        for _ in range(300):
            run_query(cursor, "MATCH (n) RETURN n LIMIT 1")

        print("Python GraphOps Baseline (after warmup):")
        measure("python_cypher_simple_match", lambda: run_query(cursor, "MATCH (n) RETURN n LIMIT 10"))
        measure(
            "python_cypher_graph_traversal",
            lambda: run_query(
                cursor,
                "MATCH (a)-[r*1..3]->(b) RETURN {start: a, hops: r, end: b} LIMIT 10",
            ),
        )

        cursor.close()


if __name__ == "__main__":
    main()
