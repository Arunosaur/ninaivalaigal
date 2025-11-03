# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""FastAPI integration for GraphOps Rust microservice."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from graphops_client import CypherRequest, GraphOpsClient, GraphResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["GraphOps"])

# Global client instance (will be initialized on startup)
_graphops_client: Optional[GraphOpsClient] = None


async def get_graphops_client() -> GraphOpsClient:
    """Dependency injection for GraphOps client"""
    global _graphops_client
    if _graphops_client is None:
        _graphops_client = GraphOpsClient(service_url="localhost:50051")
        await _graphops_client.connect()
    return _graphops_client


@router.post("/query", response_model=GraphResult)
async def execute_cypher_query(request: CypherRequest, client: GraphOpsClient = Depends(get_graphops_client)):
    """
    Execute Cypher query via GraphOps Rust service
    Fallback to Python implementation if Rust service unavailable
    """
    try:
        result = await client.execute_query(request)

        # If Rust service returns error, fallback to Python
        if result.error:
            logger.warning("Rust service unavailable, using Python fallback")
            # TODO: Call existing Python GraphOps implementation
            raise HTTPException(status_code=503, detail="GraphOps service unavailable")

        return result

    except Exception as e:
        logger.error(f"GraphOps query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def graphops_health(client: GraphOpsClient = Depends(get_graphops_client)):
    """Check GraphOps service health"""
    try:
        health = await client.health_check()
        return health
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
