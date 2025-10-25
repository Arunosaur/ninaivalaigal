#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Integration coverage for Apache AGE connectivity in the graph service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Ensure the graph service modules are importable when running from repo root
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
async def age_client():
    """Provide an initialized Apache AGE client or skip if unavailable."""

    try:
        config = get_config()
    except RuntimeError as exc:  # pragma: no cover - depends on env configuration
        pytest.skip(f"Graph service config unavailable: {exc}")
    client = ApacheAGEClient(
        config.database_url,
        graph_name=config.graph_name,
        db_name=config.db_name,
        use_cache=False,
    )

    try:
        await client.initialize()
    except Exception as exc:  # pragma: no cover - depends on local services
        pytest.skip(f"Apache AGE unavailable for integration test: {exc}")

    try:
        yield client
    finally:
        await client.close()


async def test_age_health_check_reports_status(age_client):
    """AGE health check returns structured status information."""

    health = await age_client.health_check()

    assert health["type"] == "postgresql+age"
    assert health["database"] == (age_client.db_name or "unknown")
    assert health["status"] in {"healthy", "unhealthy"}

    if health["status"] == "healthy":
        assert isinstance(health.get("graphs"), list)
        assert age_client.graph_name in health["graphs"]


async def test_age_graph_list_contains_configured_graph(age_client):
    """Configured graph is present in the AGE catalog after initialization."""

    graphs = await age_client.list_graphs()
    assert isinstance(graphs, list)
    assert age_client.graph_name in graphs
