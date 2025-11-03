# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Pydantic data models for GraphOps client."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CypherRequest(BaseModel):
    """Request model for Cypher query execution"""

    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    timeout_ms: int = Field(default=5000, description="Query timeout in milliseconds")


class GraphNode(BaseModel):
    """Represents a graph node"""

    id: str
    labels: List[str]
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """Represents a graph edge"""

    id: str
    type: str
    source: str
    target: str
    properties: Dict[str, Any]


class QueryMetrics(BaseModel):
    """Query execution metrics"""

    execution_time_ms: float
    nodes_returned: int
    edges_returned: int
    cache_hit: bool = False


class GraphResult(BaseModel):
    """Response model for graph query results"""

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metrics: Optional[QueryMetrics] = None
    error: Optional[str] = None


class HealthStatus(BaseModel):
    """Service health check response"""

    status: str  # "healthy", "degraded", "unhealthy"
    uptime_seconds: int
    version: str
    database_connected: bool
