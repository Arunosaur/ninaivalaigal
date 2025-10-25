# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Graph service configuration helpers for the Graph/AI service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class GraphServiceConfig:
    """Materialized configuration for the Graph/AI service."""

    database_url: str
    graph_name: str
    db_name: str
    service_port: int
    service_name: str
    redis_url: str | None

    @classmethod
    def from_env(cls) -> "GraphServiceConfig":
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL is required for the graph service. \n"
                "Set it in .env.dev (already exported by the project) or pass it via the environment."
            )

        graph_name = os.getenv("GRAPHOPS_GRAPH", "intelligence_graph")
        db_name = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB", "ninaivalaigal_dev")
        service_port = int(os.getenv("GRAPHOPS_PORT", "13398"))
        service_name = os.getenv("GRAPHOPS_SERVICE_NAME", "graphops")
        redis_url = os.getenv("REDIS_URL") or os.getenv("NINAIVALAIGAL_REDIS_URL")

        return cls(
            database_url=database_url,
            graph_name=graph_name,
            db_name=db_name,
            service_port=service_port,
            service_name=service_name,
            redis_url=redis_url,
        )


@lru_cache(maxsize=1)
def get_config() -> GraphServiceConfig:
    """Return the memoized configuration instance."""

    return GraphServiceConfig.from_env()
