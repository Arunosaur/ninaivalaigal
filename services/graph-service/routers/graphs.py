#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Graph management and CRUD endpoints for the Graph/AI service."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from graph.age_client import ApacheAGEClient, get_age_client
from pydantic import BaseModel, Field

from config import get_config

CONFIG = get_config()
router = APIRouter(prefix="/graphs", tags=["graph-management"])


async def _age_client() -> ApacheAGEClient:
    """Return the shared AGE client instance."""

    return await get_age_client()


class GraphCreateRequest(BaseModel):
    """Payload to create a new graph."""

    name: str = Field(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_]+$")
    if_not_exists: bool = Field(default=True, description="Skip creation if the graph already exists")


class GraphCreateResponse(BaseModel):
    """Response after attempting to create a graph."""

    name: str
    created: bool


class GraphListResponse(BaseModel):
    """List all graphs in the AGE catalog."""

    graphs: List[str]


class GraphDeleteResponse(BaseModel):
    """Response for graph deletion operations."""

    name: str
    deleted: bool


class CypherRequest(BaseModel):
    """Execute arbitrary Cypher against a named graph."""

    query: str = Field(..., description="Cypher query to execute")
    cache_key: Optional[str] = Field(default=None, description="Optional cache key for Redis reuse")
    cache_ttl: Optional[int] = Field(default=300, description="TTL for cached query results in seconds")


class CypherResponse(BaseModel):
    """Return value from a Cypher execution."""

    graph: str
    result_count: int
    results: List[Dict[str, Any]]


class NodeCreateRequest(BaseModel):
    """Create a node within a graph."""

    label: str = Field(..., min_length=1, max_length=64)
    properties: Dict[str, Any] = Field(default_factory=dict)
    node_id: Optional[str] = Field(default=None, description="Override the generated node identifier")


class RelationshipCreateRequest(BaseModel):
    """Create a relationship between two nodes."""

    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    relationship: str = Field(..., min_length=1, max_length=64)
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0)


class GraphStatsResponse(BaseModel):
    """Basic graph statistics."""

    graph: str
    nodes: int
    edges: int


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


@router.get("", response_model=GraphListResponse)
async def list_graphs() -> GraphListResponse:
    """Return all graphs registered in Apache AGE."""

    client = await _age_client()
    graphs = await client.list_graphs()

    return GraphListResponse(graphs=graphs)


@router.post("", response_model=GraphCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(payload: GraphCreateRequest) -> GraphCreateResponse:
    """Create a new graph if it does not exist."""

    client = await _age_client()
    try:
        created = await client.create_graph(payload.name, if_not_exists=payload.if_not_exists)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return GraphCreateResponse(name=payload.name, created=created)


@router.delete("/{graph_name}", response_model=GraphDeleteResponse)
async def delete_graph(graph_name: str, cascade: bool = True) -> GraphDeleteResponse:
    """Drop a graph from the catalog."""

    if graph_name == CONFIG.graph_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot drop the service's primary graph",
        )

    client = await _age_client()
    deleted = await client.drop_graph(graph_name, cascade=cascade, if_exists=True)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    return GraphDeleteResponse(name=graph_name, deleted=True)


@router.post("/{graph_name}/query", response_model=CypherResponse)
async def execute_cypher(graph_name: str, payload: CypherRequest) -> CypherResponse:
    """Run a Cypher query against a specific graph."""

    client = await _age_client()
    results = await client.execute_cypher(
        payload.query,
        cache_key=payload.cache_key,
        cache_ttl=payload.cache_ttl or 300,
        graph_name=graph_name,
    )

    return CypherResponse(graph=graph_name, result_count=len(results), results=results)


@router.post("/{graph_name}/nodes")
async def create_node(graph_name: str, payload: NodeCreateRequest) -> Dict[str, Any]:
    """Create a node within the specified graph."""

    client = await _age_client()
    node = await client.create_node(
        payload.label,
        payload.properties,
        payload.node_id,
        graph_name=graph_name,
    )

    data = asdict(node)
    data["created_at"] = _serialize_datetime(node.created_at)
    data["updated_at"] = _serialize_datetime(node.updated_at)
    return data


@router.post("/{graph_name}/relationships")
async def create_relationship(graph_name: str, payload: RelationshipCreateRequest) -> Dict[str, Any]:
    """Create a relationship between nodes in the specified graph."""

    client = await _age_client()
    edge = await client.create_edge(
        payload.source_id,
        payload.target_id,
        payload.relationship,
        payload.properties,
        payload.weight,
        graph_name=graph_name,
    )

    data = asdict(edge)
    data["created_at"] = _serialize_datetime(edge.created_at)
    return data


@router.get("/{graph_name}/stats", response_model=GraphStatsResponse)
async def graph_stats(graph_name: str) -> GraphStatsResponse:
    """Return node and edge counts for a graph."""

    client = await _age_client()
    try:
        stats = await client.graph_stats(graph_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return GraphStatsResponse(**stats)
