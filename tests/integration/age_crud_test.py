#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Integration tests covering Apache AGE graph CRUD operations."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import AsyncIterator

import pytest
import pytest_asyncio

# Allow importing graph service modules when tests run from repo root
SERVICE_DIR = Path(__file__).resolve().parents[2] / "services" / "graph-service"
LIB_DIR = SERVICE_DIR / "lib"
for candidate in (LIB_DIR, SERVICE_DIR):
    candidate_path = str(candidate)
    if candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

from graph.age_client import ApacheAGEClient  # noqa: E402

from config import get_config  # noqa: E402

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def age_client() -> AsyncIterator[ApacheAGEClient]:
    """Provide an initialized AGE client or skip if unavailable."""

    try:
        config = get_config()
    except RuntimeError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Graph service config unavailable: {exc}")

    client = ApacheAGEClient(
        config.database_url,
        graph_name=config.graph_name,
        db_name=config.db_name,
        use_cache=False,
    )

    try:
        await client.initialize()
    except Exception as exc:  # pragma: no cover - depends on external services
        pytest.skip(f"Apache AGE unavailable: {exc}")

    try:
        yield client
    finally:
        await client.close()


def _unique_graph_name(prefix: str = "test_graph") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def test_graph_creation_listing_and_deletion(age_client: ApacheAGEClient) -> None:
    """Graphs can be created, enumerated, and dropped cleanly."""

    graph_name = _unique_graph_name()

    try:
        created = await age_client.create_graph(graph_name, if_not_exists=False)
        assert created is True

        graphs = await age_client.list_graphs()
        assert graph_name in graphs

        stats = await age_client.graph_stats(graph_name)
        assert stats["graph"] == graph_name
        assert stats["nodes"] == 0
        assert stats["edges"] == 0
    finally:
        await age_client.drop_graph(graph_name, if_exists=True)

    graphs_after = await age_client.list_graphs()
    assert graph_name not in graphs_after


async def test_node_and_relationship_creation(age_client: ApacheAGEClient) -> None:
    """Nodes and relationships can be added to a dedicated graph."""

    graph_name = _unique_graph_name("crud_graph")

    try:
        await age_client.create_graph(graph_name, if_not_exists=False)

        node_a = await age_client.create_node(
            "Person",
            {"name": "Alice"},
            graph_name=graph_name,
        )
        node_b = await age_client.create_node(
            "Person",
            {"name": "Bob"},
            graph_name=graph_name,
        )

        assert node_a.id != node_b.id
        assert node_a.properties["name"] == "Alice"
        assert node_b.properties["name"] == "Bob"

        edge = await age_client.create_edge(
            node_a.id,
            node_b.id,
            "KNOWS",
            {"since": 2024},
            weight=0.9,
            graph_name=graph_name,
        )

        assert edge.source_id == node_a.id
        assert edge.target_id == node_b.id
        assert edge.properties["since"] == 2024
        assert pytest.approx(edge.properties["weight"], rel=1e-6) == 0.9

        stats = await age_client.graph_stats(graph_name)
        assert stats == {"graph": graph_name, "nodes": 2, "edges": 1}

        results = await age_client.execute_cypher(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) RETURN a.id as src, r as rel, b.id as tgt",
            graph_name=graph_name,
            column_defs=["src", "rel", "tgt"],
        )
        assert len(results) == 1
        result = results[0]
        assert result["src"] == node_a.id
        assert result["tgt"] == node_b.id
        assert "rel" in result
    finally:
        await age_client.drop_graph(graph_name, if_exists=True)
