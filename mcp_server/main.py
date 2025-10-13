#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
MCP Server for Ninaivalaigal Memory Management
Exposes memory operations via Model Context Protocol
"""

import os
from typing import Dict, List, Optional

import httpx
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ninaivalaigal MCP Server",
    description="Model Context Protocol server for memory management",
    version="1.0.0",
)

# Configure CORS for Copilot access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your security needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "secure_nina_password")

# Initialize Redis client
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

# Initialize HTTP client
http_client = httpx.AsyncClient(base_url=API_URL, timeout=30.0)


# Request/Response Models
class MemoryStoreRequest(BaseModel):
    """Request to store a memory"""

    content: str
    context: str = "default"
    tags: List[str] = []
    metadata: Optional[Dict] = None


class MemoryRecallRequest(BaseModel):
    """Request to recall memories"""

    query: str
    context: str = "default"
    limit: int = 10


class MemoryResponse(BaseModel):
    """Memory response"""

    id: Optional[str]
    content: str
    context: str
    tags: List[str]
    metadata: Optional[Dict]
    relevance_score: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    api_connected: bool
    redis_connected: bool
    version: str


# Health Check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """MCP server health check"""
    try:
        # Check API connectivity
        api_response = await http_client.get("/health")
        api_connected = api_response.status_code == 200
    except Exception as e:
        logger.warning(f"API health check failed: {e}")
        api_connected = False

    # Check Redis connectivity
    try:
        redis_client.ping()
        redis_connected = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_connected = False

    return HealthResponse(
        status="healthy" if (api_connected and redis_connected) else "degraded",
        api_connected=api_connected,
        redis_connected=redis_connected,
        version="1.0.0",
    )


# MCP Endpoints
@app.post("/mcp/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """
    Store a memory via MCP

    This endpoint is called by Copilot to store context/memories
    """
    try:
        logger.info("Storing memory via MCP", context=request.context)

        # Forward to API
        response = await http_client.post(
            "/memory",
            json={
                "type": "mcp_context",
                "source": "copilot",
                "data": {
                    "content": request.content,
                    "context": request.context,
                    "tags": request.tags,
                    "metadata": request.metadata or {},
                },
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API error: {response.text}")

        result = response.json()
        logger.info("Memory stored successfully", memory_id=result.get("id"))

        return {
            "success": True,
            "memory_id": result.get("id"),
            "message": "Memory stored successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/memory/recall", response_model=List[MemoryResponse])
async def recall_memories(request: MemoryRecallRequest):
    """
    Recall memories via MCP

    This endpoint is called by Copilot to retrieve relevant context
    """
    try:
        logger.info("Recalling memories via MCP", query=request.query, context=request.context)

        # Forward to API
        response = await http_client.get(
            "/memory/recall",
            params={
                "query": request.query,
                "context": request.context,
                "limit": request.limit,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API error: {response.text}")

        result = response.json()
        memories = result.get("memories", [])

        logger.info("Memories recalled successfully", count=len(memories))

        # Convert to MCP format
        return [
            MemoryResponse(
                id=mem.get("id"),
                content=mem.get("data", {}).get("content", ""),
                context=mem.get("context", request.context),
                tags=mem.get("data", {}).get("tags", []),
                metadata=mem.get("data", {}).get("metadata"),
                relevance_score=mem.get("relevance_score"),
            )
            for mem in memories
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recall memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/contexts")
async def list_contexts():
    """
    List available contexts

    This endpoint is called by Copilot to discover available contexts
    """
    try:
        logger.info("Listing contexts via MCP")

        # Forward to API
        response = await http_client.get("/contexts")

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API error: {response.text}")

        result = response.json()
        logger.info("Contexts listed successfully", count=len(result))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/memory/tokenize")
async def tokenize_text(text: str):
    """
    Tokenize text for context injection

    This endpoint is called by Copilot to prepare text for memory storage
    """
    try:
        logger.info("Tokenizing text via MCP", length=len(text))

        # Forward to API
        response = await http_client.post("/memory/tokenize", json={"text": text})

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API error: {response.text}")

        result = response.json()
        logger.info("Text tokenized successfully", token_count=result.get("count"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to tokenize text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize MCP server"""
    logger.info("MCP server starting up")

    # Test connections
    try:
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    try:
        response = await http_client.get("/health")
        if response.status_code == 200:
            logger.info("API connection established")
        else:
            logger.warning(f"API health check returned {response.status_code}")
    except Exception as e:
        logger.warning(f"API connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("MCP server shutting down")
    await http_client.aclose()
    redis_client.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_PORT", "3000"))
    logger.info(f"Starting MCP server on port {port}")

    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info", access_log=True)
